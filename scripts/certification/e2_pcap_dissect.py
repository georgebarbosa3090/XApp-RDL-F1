#!/usr/bin/env python3
"""
Dissecação E2AP de um PCAP de execução NORI (PCAP -> SCTP -> E2AP-PDU).

Separa o tráfego E2 capturado por ``tcpdump`` em mensagens individuais, classifica
cada uma pelo papel no protocolo (E2 Setup, Subscription, Indication, Control, ...)
e identifica a cadeia KPM_t0 -> RC Control -> ACK -> KPM_t1 quando ela existe.

Dois decodificadores, de origens distintas:

1. Este módulo (só biblioteca padrão): lê o PCAP, remonta os fragmentos SCTP e
   decodifica o cabeçalho APER do E2AP-PDU e os IEs de identificação (RICrequestID,
   RANfunctionID, TransactionID, lista de RAN functions). Não usa o codec E2 da xApp.
2. ``tshark`` (Wireshark), implementação independente gerada do ASN.1 oficial. Quando
   disponível, a sequência de mensagens dele é comparada com a deste módulo, mensagem
   a mensagem. Só a concordância das duas é tratada como confirmação independente.

O diretório da execução não é alterado (a evidência bruta e seu ``hashes.sha256``
continuam imutáveis). A saída vai para ``experiments/e2_dissection/<run_id>/``:

    e2_messages.json     mensagens, papéis da cadeia e resultado do tshark
    messages/NNN_<papel>.aper   bytes de cada E2AP-PDU
    tshark_fields.tsv    saída bruta do tshark (quando disponível)
    hashes.sha256

Uso:
    python scripts/certification/e2_pcap_dissect.py --run nori_rc_demo_seed1
    python scripts/certification/e2_pcap_dissect.py --pcap caminho.pcap --out dir/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "xapp-rdl/e2-dissection/v1"
E2AP_PPID = 70
DEFAULT_RIC_PORTS = (36421, 36422)

PDU_KINDS = ("initiatingMessage", "successfulOutcome", "unsuccessfulOutcome")

# E2AP v3.01, seção 9.3.6 (códigos de procedimento)
PROCEDURES = {
    1: "e2_setup", 2: "error_indication", 3: "reset", 4: "control", 5: "indication",
    6: "service_query", 7: "service_update", 8: "subscription", 9: "subscription_delete",
    10: "node_configuration_update", 11: "connection_update", 12: "subscription_delete_required",
    13: "e2_removal", 14: "subscription_modification", 15: "subscription_modification_required",
    16: "query",
}
# Sufixo do papel por tipo de PDU. Indication e Error Indication não têm resposta.
ROLE_SUFFIX = {"initiatingMessage": "request", "successfulOutcome": "response", "unsuccessfulOutcome": "failure"}
ROLE_OVERRIDES = {(4, "successfulOutcome"): "control_ack", (5, "initiatingMessage"): "indication",
                  (2, "initiatingMessage"): "error_indication"}

# IDs de IE usados (E2AP v3.01, seção 9.3.7)
IE_RAN_FUNCTION_ID = 5
IE_RAN_FUNCTIONS_ACCEPTED = 9
IE_RAN_FUNCTIONS_ADDED = 10
IE_RIC_ACTION_ID = 15
IE_RIC_INDICATION_HEADER = 25
IE_RIC_INDICATION_MESSAGE = 26
IE_RIC_INDICATION_SN = 27
IE_RIC_INDICATION_TYPE = 28
IE_RIC_REQUEST_ID = 29
IE_RIC_CONTROL_HEADER = 22
IE_RIC_CONTROL_MESSAGE = 23
IE_RIC_CONTROL_OUTCOME = 32
IE_TRANSACTION_ID = 49
IE_NAMES = {
    3: "GlobalE2node_ID", 5: "RANfunctionID", 9: "RANfunctionsAccepted", 10: "RANfunctionsAdded",
    15: "RICactionID", 17: "RICactions_Admitted", 18: "RICactions_NotAdmitted", 20: "RICcallProcessID",
    21: "RICcontrolAckRequest", 22: "RICcontrolHeader", 23: "RICcontrolMessage", 25: "RICindicationHeader",
    26: "RICindicationMessage", 27: "RICindicationSN", 28: "RICindicationType", 29: "RICrequestID",
    30: "RICsubscriptionDetails", 32: "RICcontrolOutcome", 49: "TransactionID", 50: "E2nodeComponentConfigAddition",
    4: "GlobalRIC_ID",
}
OCTET_STRING_IES = {IE_RIC_INDICATION_HEADER, IE_RIC_INDICATION_MESSAGE, IE_RIC_CONTROL_HEADER,
                    IE_RIC_CONTROL_MESSAGE, IE_RIC_CONTROL_OUTCOME}

# Papéis da cadeia closed-loop esperados pelo certificador (E2_RAW_ROLES)
CHAIN_ROLES = ("e2_setup", "subscription", "kpm_t0", "control_request", "control_ack", "kpm_t1")
MESSAGE_TSV_COLUMNS = ("index", "frame", "time_epoch", "direction", "role", "procedure_code", "pdu_type",
                       "length", "sha256", "ric_requestor_id", "ric_instance_id", "ran_function_id",
                       "received_by_xapp")


class DissectError(ValueError):
    pass


# ---------------------------------------------------------------------------
# PCAP -> IP -> SCTP
# ---------------------------------------------------------------------------

def read_pcap(data: bytes) -> Tuple[int, List[Tuple[float, bytes]]]:
    """Lê PCAP clássico (micro ou nanossegundos, qualquer endianness)."""
    if len(data) < 24:
        raise DissectError("arquivo menor que o cabeçalho PCAP")
    magic = data[:4]
    formats = {b"\xd4\xc3\xb2\xa1": ("<", 1e-6), b"\xa1\xb2\xc3\xd4": (">", 1e-6),
               b"\x4d\x3c\xb2\xa1": ("<", 1e-9), b"\xa1\xb2\x3c\x4d": (">", 1e-9)}
    if magic not in formats:
        if magic == b"\x0a\x0d\x0d\x0a":
            raise DissectError("pcapng não suportado; capture com tcpdump -w (PCAP clássico)")
        raise DissectError(f"assinatura PCAP desconhecida: {magic.hex()}")
    endian, scale = formats[magic]
    linktype = struct.unpack(endian + "I", data[20:24])[0]
    packets, offset = [], 24
    while offset + 16 <= len(data):
        sec, frac, caplen, _ = struct.unpack(endian + "IIII", data[offset:offset + 16])
        offset += 16
        if offset + caplen > len(data):
            raise DissectError(f"pacote {len(packets) + 1} truncado")
        packets.append((sec + frac * scale, data[offset:offset + caplen]))
        offset += caplen
    return linktype, packets


def network_payload(linktype: int, frame: bytes) -> Tuple[Optional[int], bytes]:
    """Retorna (ethertype, payload L3) para os tipos de enlace usados pelo tcpdump."""
    if linktype == 1:  # Ethernet, com VLANs empilhadas
        ethertype, off = struct.unpack("!H", frame[12:14])[0], 14
        while ethertype in (0x8100, 0x88A8) and len(frame) >= off + 4:
            ethertype, off = struct.unpack("!H", frame[off + 2:off + 4])[0], off + 4
        return ethertype, frame[off:]
    if linktype == 113:  # Linux cooked (SLL), usado por tcpdump -i any
        return struct.unpack("!H", frame[14:16])[0], frame[16:]
    if linktype == 276:  # SLL2
        return struct.unpack("!H", frame[0:2])[0], frame[20:]
    if linktype in (101, 12, 228, 229):  # IP bruto
        version = frame[0] >> 4 if frame else 0
        return {4: 0x0800, 6: 0x86DD}.get(version), frame
    if linktype == 0:  # loopback BSD
        family = struct.unpack("<I", frame[:4])[0]
        return {2: 0x0800, 24: 0x86DD, 28: 0x86DD, 30: 0x86DD}.get(family), frame[4:]
    raise DissectError(f"tipo de enlace PCAP {linktype} não suportado")


def sctp_segment(ethertype: Optional[int], packet: bytes) -> Optional[Tuple[str, str, bytes]]:
    if ethertype == 0x0800 and len(packet) >= 20:
        ihl = (packet[0] & 0x0F) * 4
        flags_frag = struct.unpack("!H", packet[6:8])[0]
        if packet[9] != 132:
            return None
        if flags_frag & 0x3FFF:
            raise DissectError("datagrama IPv4 fragmentado: remontagem IP não implementada")
        total = struct.unpack("!H", packet[2:4])[0]
        src = ".".join(str(b) for b in packet[12:16])
        dst = ".".join(str(b) for b in packet[16:20])
        return src, dst, packet[ihl:total]
    if ethertype == 0x86DD and len(packet) >= 40:
        if packet[6] != 132:
            return None
        plen = struct.unpack("!H", packet[4:6])[0]
        src = ":".join(packet[8:24][i:i + 2].hex() for i in range(0, 16, 2))
        dst = ":".join(packet[24:40][i:i + 2].hex() for i in range(0, 16, 2))
        return src, dst, packet[40:40 + plen]
    return None


def sctp_data_chunks(segment: bytes) -> Tuple[int, int, List[Dict[str, Any]]]:
    if len(segment) < 12:
        raise DissectError("segmento SCTP menor que o cabeçalho comum")
    sport, dport = struct.unpack("!HH", segment[:4])
    chunks, off = [], 12
    while off + 4 <= len(segment):
        ctype, flags, length = segment[off], segment[off + 1], struct.unpack("!H", segment[off + 2:off + 4])[0]
        if length < 4:
            raise DissectError(f"chunk SCTP com comprimento inválido ({length})")
        if ctype == 0:  # DATA
            tsn, sid, ssn, ppid = struct.unpack("!IHHI", segment[off + 4:off + 16])
            chunks.append({"tsn": tsn, "sid": sid, "ssn": ssn, "ppid": ppid,
                           "begin": bool(flags & 0x02), "end": bool(flags & 0x01),
                           "data": segment[off + 16:off + length]})
        off += (length + 3) & ~3
    return sport, dport, chunks


# ---------------------------------------------------------------------------
# APER (subconjunto usado pelo cabeçalho E2AP)
# ---------------------------------------------------------------------------

class AperReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.bit = 0

    def bits(self, n: int) -> int:
        value = 0
        for _ in range(n):
            byte = self.bit >> 3
            if byte >= len(self.data):
                raise DissectError("fim inesperado do PDU")
            value = (value << 1) | ((self.data[byte] >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return value

    def align(self) -> None:
        self.bit = (self.bit + 7) & ~7

    def octets(self, n: int) -> bytes:
        self.align()
        start = self.bit >> 3
        if start + n > len(self.data):
            raise DissectError("fim inesperado do PDU")
        self.bit += 8 * n
        return self.data[start:start + n]

    def length(self) -> int:
        first = self.octets(1)[0]
        if first & 0x80 == 0:
            return first
        if first & 0xC0 == 0x80:
            return ((first & 0x3F) << 8) | self.octets(1)[0]
        raise DissectError("determinante de comprimento fragmentado (>16K) não suportado")

    def constrained(self, lo: int, hi: int) -> int:
        rng = hi - lo + 1
        if rng == 1:
            return lo
        if rng <= 255:
            return lo + self.bits((rng - 1).bit_length())
        if rng == 256:
            return lo + self.octets(1)[0]
        if rng <= 65536:
            return lo + int.from_bytes(self.octets(2), "big")
        raise DissectError("inteiro com faixa > 65536 não suportado")

    def open_type(self) -> bytes:
        return self.octets(self.length())


def _ext_int(r: AperReader, lo: int, hi: int) -> int:
    if r.bits(1):
        raise DissectError("valor fora da raiz de extensão")
    return r.constrained(lo, hi)


def _protocol_ies(value: bytes) -> List[Tuple[int, int, bytes]]:
    """SEQUENCE { protocolIEs ProtocolIE-Container, ... } -> [(id, criticality, valor)]."""
    r = AperReader(value)
    if r.bits(1):
        raise DissectError("extensões no SEQUENCE da mensagem não suportadas")
    count = r.constrained(0, 65535)
    ies = []
    for _ in range(count):
        ie_id = r.constrained(0, 65535)
        crit = r.bits(2)
        ies.append((ie_id, crit, r.open_type()))
    return ies


def _ran_function_list(raw: bytes, with_definition: bool) -> List[Dict[str, Any]]:
    """RANfunctions-List / RANfunctionsID-List: SEQUENCE (SIZE(1..256)) OF ProtocolIE-SingleContainer."""
    r = AperReader(raw)
    count = r.constrained(1, 256)
    items = []
    for _ in range(count):
        r.constrained(0, 65535)  # id do item
        r.bits(2)
        item = AperReader(r.open_type())
        item.bits(1)  # extensão do RANfunction-Item
        entry: Dict[str, Any] = {"ran_function_id": item.constrained(0, 4095)}
        if with_definition:
            definition = item.octets(item.length())
            entry["definition_len"] = len(definition)
            entry["revision"] = item.constrained(0, 4095)
            if item.bits(1):
                raise DissectError("OID de RAN function fora da raiz")
            size = item.constrained(1, 1000)
            entry["oid"] = item.octets(size).decode("ascii", "replace")
        else:
            entry["revision"] = item.constrained(0, 4095)
        items.append(entry)
    return items


def decode_ie(ie_id: int, raw: bytes) -> Any:
    if ie_id == IE_RIC_REQUEST_ID:
        r = AperReader(raw)
        r.bits(1)
        return {"requestor": r.constrained(0, 65535), "instance": r.constrained(0, 65535)}
    if ie_id == IE_RAN_FUNCTION_ID:
        return AperReader(raw).constrained(0, 4095)
    if ie_id == IE_TRANSACTION_ID:
        return _ext_int(AperReader(raw), 0, 255)
    if ie_id == IE_RIC_ACTION_ID:
        return AperReader(raw).constrained(0, 255)
    if ie_id == IE_RIC_INDICATION_SN:
        return AperReader(raw).constrained(0, 65535)
    if ie_id == IE_RIC_INDICATION_TYPE:
        r = AperReader(raw)
        return {0: "report", 1: "insert"}.get(_ext_int(r, 0, 1))
    if ie_id in OCTET_STRING_IES:
        r = AperReader(raw)
        body = r.octets(r.length())
        return {"len": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    if ie_id == IE_RAN_FUNCTIONS_ADDED:
        return _ran_function_list(raw, with_definition=True)
    if ie_id == IE_RAN_FUNCTIONS_ACCEPTED:
        return _ran_function_list(raw, with_definition=False)
    return None


def decode_e2ap_header(pdu: bytes) -> Dict[str, Any]:
    r = AperReader(pdu)
    if r.bits(1):
        raise DissectError("alternativa de extensão do E2AP-PDU não suportada")
    kind_index = r.bits(2)
    if kind_index > 2:
        raise DissectError(f"índice de E2AP-PDU inválido: {kind_index}")
    kind = PDU_KINDS[kind_index]
    code = r.constrained(0, 255)
    criticality = r.bits(2)
    value = r.open_type()
    end = (r.bit + 7) >> 3
    if end != len(pdu):
        raise DissectError(f"{len(pdu) - end} byte(s) além do fim do E2AP-PDU")
    proc = PROCEDURES.get(code, f"procedure_{code}")
    role = ROLE_OVERRIDES.get((code, kind)) or f"{proc}_{ROLE_SUFFIX[kind]}"
    message: Dict[str, Any] = {"pdu_type": kind, "procedure_code": code, "procedure": proc, "role": role,
                               "criticality": criticality, "ies": []}
    for ie_id, _, raw in _protocol_ies(value):
        entry: Dict[str, Any] = {"id": ie_id, "name": IE_NAMES.get(ie_id, f"ie_{ie_id}"), "len": len(raw)}
        try:
            decoded = decode_ie(ie_id, raw)
        except DissectError as exc:
            entry["decode_error"] = str(exc)
            decoded = None
        if decoded is not None:
            entry["value"] = decoded
        message["ies"].append(entry)
    return message


def ie_value(message: Dict[str, Any], ie_id: int) -> Any:
    for ie in message.get("ies", []):
        if ie["id"] == ie_id:
            return ie.get("value")
    return None


# ---------------------------------------------------------------------------
# Extração das mensagens
# ---------------------------------------------------------------------------

def extract_messages(pcap: bytes, ric_ports: Tuple[int, ...] = DEFAULT_RIC_PORTS) -> Dict[str, Any]:
    linktype, packets = read_pcap(pcap)
    seen_tsn = set()
    partial: Dict[Tuple, List[bytes]] = {}
    messages: List[Dict[str, Any]] = []
    errors: List[str] = []
    stats = {"frames": len(packets), "sctp_frames": 0, "data_chunks": 0, "retransmissions": 0, "fragments": 0}

    for frame_no, (ts, frame) in enumerate(packets, start=1):
        try:
            seg = sctp_segment(*network_payload(linktype, frame))
            if seg is None:
                continue
            src, dst, payload = seg
            sport, dport, chunks = sctp_data_chunks(payload)
        except DissectError as exc:
            errors.append(f"quadro {frame_no}: {exc}")
            continue
        stats["sctp_frames"] += 1
        if dport in ric_ports:
            direction = "E2_NODE->RIC"
        elif sport in ric_ports:
            direction = "RIC->E2_NODE"
        else:
            continue
        for chunk in chunks:
            stats["data_chunks"] += 1
            flow = (src, sport, dst, dport)
            if (flow, chunk["tsn"]) in seen_tsn:
                stats["retransmissions"] += 1
                continue
            seen_tsn.add((flow, chunk["tsn"]))
            key = (flow, chunk["sid"], chunk["ssn"])
            if chunk["begin"] and chunk["end"]:
                data = chunk["data"]
            else:
                stats["fragments"] += 1
                if chunk["begin"]:
                    partial[key] = [chunk["data"]]
                    continue
                if key not in partial:
                    errors.append(f"quadro {frame_no}: fragmento SCTP sem início (TSN {chunk['tsn']})")
                    continue
                partial[key].append(chunk["data"])
                if not chunk["end"]:
                    continue
                data = b"".join(partial.pop(key))
            entry: Dict[str, Any] = {
                "index": len(messages) + 1, "frame": frame_no, "time_epoch": round(ts, 6),
                "direction": direction, "src": f"{src}:{sport}", "dst": f"{dst}:{dport}",
                "sctp_stream": chunk["sid"], "sctp_ppid": chunk["ppid"], "length": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            try:
                entry.update(decode_e2ap_header(data))
            except DissectError as exc:
                entry["role"] = "undecoded"
                entry["decode_error"] = str(exc)
                errors.append(f"mensagem {entry['index']} (quadro {frame_no}): {exc}")
            entry["_bytes"] = data
            messages.append(entry)
    for key in partial:
        errors.append(f"mensagem SCTP incompleta no fim da captura (stream {key[1]}, SSN {key[2]})")
    return {"linktype": linktype, "stats": stats, "messages": messages, "errors": errors}


def ran_function_kinds(messages: List[Dict[str, Any]]) -> Dict[int, str]:
    """Classifica as RAN functions anunciadas no E2 Setup pelo OID do service model."""
    kinds: Dict[int, str] = {}
    for m in messages:
        if m.get("role") != "e2_setup_request":
            continue
        for item in ie_value(m, IE_RAN_FUNCTIONS_ADDED) or []:
            oid = str(item.get("oid", ""))
            # 1.3.6.1.4.1.53148.1.<versão>.2.<sm>: 2 = KPM, 3 = RC, 4 = CCC
            sm = oid.rsplit(".", 1)[-1] if oid.startswith("1.3.6.1.4.1.53148.1.") else ""
            kinds[item["ran_function_id"]] = {"2": "KPM", "3": "RC", "4": "CCC"}.get(sm, "OUTRO")
    return kinds


def _req_key(m: Dict[str, Any]) -> Optional[Tuple[int, int, int]]:
    rid, fn = ie_value(m, IE_RIC_REQUEST_ID), ie_value(m, IE_RAN_FUNCTION_ID)
    if not isinstance(rid, dict) or fn is None:
        return None
    return rid["requestor"], rid["instance"], fn


def assign_chain_roles(messages: List[Dict[str, Any]], kinds: Dict[int, str]) -> Dict[str, Optional[int]]:
    """Identifica as mensagens da cadeia KPM_t0 -> Control -> ACK -> KPM_t1, em ordem temporal."""
    roles: Dict[str, Optional[int]] = {r: None for r in CHAIN_ROLES}

    def first(pred, after: int = 0) -> Optional[Dict[str, Any]]:
        return next((m for m in messages if m["index"] > after and pred(m)), None)

    setup_req = first(lambda m: m.get("role") == "e2_setup_request" and m["direction"] == "E2_NODE->RIC")
    if setup_req:
        tx = ie_value(setup_req, IE_TRANSACTION_ID)
        resp = first(lambda m: m.get("role") == "e2_setup_response" and ie_value(m, IE_TRANSACTION_ID) == tx,
                     setup_req["index"])
        if resp:
            roles["e2_setup"] = resp["index"]

    sub_resp = None
    for sub_req in (m for m in messages if m.get("role") == "subscription_request" and m["direction"] == "RIC->E2_NODE"):
        key = _req_key(sub_req)
        if key is None or kinds.get(key[2]) not in (None, "KPM"):
            continue
        sub_resp = first(lambda m, k=key: m.get("role") == "subscription_response" and _req_key(m) == k,
                         sub_req["index"])
        if sub_resp:
            roles["subscription"] = sub_resp["index"]
            break
    if not sub_resp:
        return roles
    sub_key = _req_key(sub_resp)

    def kpm_indication(m: Dict[str, Any]) -> bool:
        return m.get("role") == "indication" and m["direction"] == "E2_NODE->RIC" and _req_key(m) == sub_key

    t0 = first(kpm_indication, sub_resp["index"])
    if not t0:
        return roles
    roles["kpm_t0"] = t0["index"]
    ctrl = first(lambda m: m.get("role") == "control_request" and m["direction"] == "RIC->E2_NODE"
                 and kinds.get((_req_key(m) or (0, 0, -1))[2]) in (None, "RC"), t0["index"])
    if not ctrl:
        return roles
    roles["control_request"] = ctrl["index"]
    ack = first(lambda m: m.get("role") == "control_ack" and _req_key(m) == _req_key(ctrl), ctrl["index"])
    if not ack:
        return roles
    roles["control_ack"] = ack["index"]
    t1 = first(kpm_indication, ack["index"])
    if t1:
        roles["kpm_t1"] = t1["index"]
    return roles


# ---------------------------------------------------------------------------
# Confirmação independente com tshark
# ---------------------------------------------------------------------------

TSHARK_FIELDS = ("frame.number", "e2ap.E2AP_PDU", "e2ap.procedureCode", "e2ap.ricRequestorID",
                 "e2ap.ricInstanceID", "e2ap.RANfunctionID")


def run_tshark(pcap_path: Path, ric_ports: Tuple[int, ...], tshark: Optional[str] = None) -> Dict[str, Any]:
    exe = tshark or shutil.which("tshark")
    if not exe:
        return {"available": False, "reason": "tshark não encontrado no PATH"}
    version = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.splitlines()[:1]
    cmd = [exe, "-n", "-r", str(pcap_path), "-o", "sctp.reassembly:TRUE"]
    for port in ric_ports:
        cmd += ["-d", f"sctp.port=={port},e2ap"]
    cmd += ["-Y", "e2ap", "-T", "fields", "-E", "separator=\t", "-E", "occurrence=a", "-E", "aggregator=,"]
    for f in TSHARK_FIELDS:
        cmd += ["-e", f]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result: Dict[str, Any] = {"available": True, "version": version[0] if version else "",
                              "command": " ".join(cmd), "exit_code": proc.returncode,
                              "stderr": proc.stderr.strip()[-2000:], "tsv": proc.stdout}
    if proc.returncode != 0:
        result["error"] = f"tshark terminou com código {proc.returncode}"
        return result
    rows, frame_ids = [], {}
    for line in proc.stdout.splitlines():
        cols = (line.split("\t") + [""] * len(TSHARK_FIELDS))[:len(TSHARK_FIELDS)]
        split = [[c for c in col.split(",") if c != ""] for col in cols]
        frame = int(cols[0])
        for i, kind in enumerate(split[1]):
            rows.append({"frame": frame, "pdu_type_index": int(kind),
                         "procedure_code": int(split[2][i]) if i < len(split[2]) else None})
        # IDs de nível superior por quadro (vários PDUs agrupados num quadro somam as listas)
        frame_ids[frame] = {"requestor": sorted(int(v) for v in split[3]),
                            "instance": sorted(int(v) for v in split[4]),
                            "ran_function": sorted(int(v) for v in split[5])}
    result["messages"] = rows
    result["frame_ids"] = frame_ids
    return result


def _frame_ids(messages: List[Dict[str, Any]]) -> Dict[int, Dict[str, List[int]]]:
    out: Dict[int, Dict[str, List[int]]] = {}
    for m in messages:
        ids = out.setdefault(m["frame"], {"requestor": [], "instance": [], "ran_function": []})
        rid, fn = ie_value(m, IE_RIC_REQUEST_ID), ie_value(m, IE_RAN_FUNCTION_ID)
        if isinstance(rid, dict):
            ids["requestor"].append(rid["requestor"])
            ids["instance"].append(rid["instance"])
        if fn is not None:
            ids["ran_function"].append(fn)
    return {f: {k: sorted(v) for k, v in ids.items()} for f, ids in out.items()}


def compare_with_tshark(messages: List[Dict[str, Any]], tshark: Dict[str, Any]) -> Dict[str, Any]:
    if not tshark.get("available") or "messages" not in tshark:
        return {"checked": False, "agreement": None, "mismatches": []}
    ours = [(m["frame"], PDU_KINDS.index(m["pdu_type"]) if m.get("pdu_type") in PDU_KINDS else None,
             m.get("procedure_code")) for m in messages]
    theirs = [(t["frame"], t["pdu_type_index"], t["procedure_code"]) for t in tshark["messages"]]
    mismatches = []
    for i in range(max(len(ours), len(theirs))):
        a = ours[i] if i < len(ours) else None
        b = theirs[i] if i < len(theirs) else None
        if a != b:
            mismatches.append({"position": i + 1, "dissector": a, "tshark": b})
    id_mismatches = []
    if "frame_ids" in tshark:
        mine = _frame_ids(messages)
        theirs_ids = {int(k): v for k, v in tshark["frame_ids"].items()}
        for frame in sorted(set(mine) | set(theirs_ids)):
            if mine.get(frame) != theirs_ids.get(frame):
                id_mismatches.append({"frame": frame, "dissector": mine.get(frame), "tshark": theirs_ids.get(frame)})
    return {"checked": True, "agreement": not mismatches and not id_mismatches and bool(ours),
            "messages_dissector": len(ours), "messages_tshark": len(theirs),
            "fields_compared": ["frame", "pdu_type", "procedure_code"]
                               + (["ricRequestorID", "ricInstanceID", "RANfunctionID"] if "frame_ids" in tshark else []),
            "mismatches": mismatches[:20], "id_mismatches": id_mismatches[:20],
            "id_mismatch_count": len(id_mismatches)}


# ---------------------------------------------------------------------------
# Cruzamento com a xApp (eventos RMR registrados pela kpm-probe)
# ---------------------------------------------------------------------------

def xapp_crosscheck(messages: List[Dict[str, Any]], roles: Dict[str, Optional[int]],
                    events_path: Path) -> Dict[str, Any]:
    """Casa cada RIC Indication do PCAP com as recebidas pela xApp via RMR (sha256 do payload)."""
    raw = events_path.read_bytes()
    received: Dict[str, int] = {}
    subscriptions = []
    for line in raw.decode("utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("event") == "rmr_message" and ev.get("mtype") == 12050:
            received[ev["sha256"]] = received.get(ev["sha256"], 0) + 1
        elif ev.get("event") in ("subscription_request", "submgr_notification"):
            subscriptions.append({k: ev.get(k) for k in ("t_utc", "event", "status", "response", "body") if k in ev})
    pcap_ind = [m for m in messages if m.get("role") == "indication" and m.get("direction") == "E2_NODE->RIC"]
    remaining = dict(received)
    matched = 0
    for m in pcap_ind:
        if remaining.get(m["sha256"], 0) > 0:
            remaining[m["sha256"]] -= 1
            matched += 1
            m["received_by_xapp"] = True
        else:
            m["received_by_xapp"] = False
    by_index = {m["index"]: m for m in messages}
    return {
        "events_file": events_path.name,
        "events_sha256": hashlib.sha256(raw).hexdigest(),
        "xapp_indications": sum(received.values()),
        "pcap_indications": len(pcap_ind),
        "pcap_indications_received_by_xapp": matched,
        "xapp_indications_not_in_pcap": sum(remaining.values()),
        "chain_roles_received_by_xapp": {r: by_index[i].get("received_by_xapp") for r, i in roles.items()
                                         if i and r in ("kpm_t0", "kpm_t1")},
        "subscription_events": subscriptions[:10],
    }


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dissect(pcap_path: Path, out_dir: Path, run_id: str, ric_ports: Tuple[int, ...] = DEFAULT_RIC_PORTS,
            use_tshark: bool = True, tshark: Optional[str] = None,
            xapp_events: Optional[Path] = None) -> Dict[str, Any]:
    raw = pcap_path.read_bytes()
    extracted = extract_messages(raw, ric_ports)
    messages = extracted["messages"]
    kinds = ran_function_kinds(messages)
    roles = assign_chain_roles(messages, kinds)
    ts = run_tshark(pcap_path, ric_ports, tshark) if use_tshark else {"available": False, "reason": "desativado (--no-tshark)"}
    comparison = compare_with_tshark(messages, ts)
    xapp = xapp_crosscheck(messages, roles, xapp_events) if xapp_events else None

    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "messages").mkdir(parents=True)

    # Lista completa em TSV (uma linha por mensagem); detalhe e bytes só das mensagens notáveis:
    # tudo que não é Indication, os papéis da cadeia e a primeira e a última Indication. Os
    # bytes das demais continuam no PCAP de origem (versionado e com hash na execução).
    indications = [m for m in messages if m.get("role") == "indication"]
    notable = {m["index"] for m in messages if m.get("role") != "indication"}
    notable |= {i for i in roles.values() if i}
    if indications:
        notable |= {indications[0]["index"], indications[-1]["index"]}
    rows = ["\t".join(MESSAGE_TSV_COLUMNS)]
    role_counts: Dict[str, int] = {}
    for m in messages:
        role_counts[m.get("role", "?")] = role_counts.get(m.get("role", "?"), 0) + 1
        rid, fn = ie_value(m, IE_RIC_REQUEST_ID), ie_value(m, IE_RAN_FUNCTION_ID)
        rows.append("\t".join(str(v) for v in (
            m["index"], m["frame"], m["time_epoch"], m["direction"], m.get("role"), m.get("procedure_code", ""),
            m.get("pdu_type", ""), m["length"], m["sha256"],
            rid["requestor"] if isinstance(rid, dict) else "", rid["instance"] if isinstance(rid, dict) else "",
            "" if fn is None else fn, {True: "1", False: "0"}.get(m.get("received_by_xapp"), ""))))
        data = m.pop("_bytes")
        if m["index"] in notable:
            name = f"{m['index']:05d}_{m['role']}.aper"
            (out_dir / "messages" / name).write_bytes(data)
            m["file"] = f"messages/{name}"
    tsv = ("\n".join(rows) + "\n").encode("utf-8")
    (out_dir / "messages.tsv").write_bytes(tsv)
    if ts.get("tsv") is not None:
        (out_dir / "tshark_fields.tsv").write_bytes(("\t".join(TSHARK_FIELDS) + "\n" + ts["tsv"]).encode("utf-8"))
    ts_summary = {k: v for k, v in ts.items() if k not in ("tsv", "messages", "frame_ids")}

    try:
        source = pcap_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source = str(pcap_path)
    summary = {
        "schema": SCHEMA,
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/certification/e2_pcap_dissect.py",
        "source_pcap": source,
        "source_pcap_sha256": hashlib.sha256(raw).hexdigest(),
        "pcap_linktype": extracted["linktype"],
        "ric_ports": list(ric_ports),
        "stats": extracted["stats"],
        "errors": extracted["errors"],
        "ran_functions": {str(k): v for k, v in sorted(kinds.items())},
        "message_count": len(messages),
        "role_counts": dict(sorted(role_counts.items())),
        "undecoded_count": role_counts.get("undecoded", 0),
        "messages_tsv": "messages.tsv",
        "messages_tsv_sha256": hashlib.sha256(tsv).hexdigest(),
        "messages": [m for m in messages if m["index"] in notable],
        "chain_roles": roles,
        "tshark": ts_summary,
        "tshark_comparison": comparison,
        "independent_confirmation": bool(comparison.get("agreement")) and not extracted["errors"],
        "xapp_crosscheck": xapp,
    }
    # write_bytes: mesmo conteúdo (e hashes) no Windows e no Linux, sem conversão de fim de linha
    (out_dir / "e2_messages.json").write_bytes((json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    files = sorted(p for p in out_dir.rglob("*") if p.is_file() and p.name != "hashes.sha256")
    (out_dir / "hashes.sha256").write_bytes(
        "".join(f"{sha256_file(p)}  {p.relative_to(out_dir).as_posix()}\n" for p in files).encode("utf-8"))
    summary["_all_messages"] = messages  # só para quem chama em processo (CLI e testes); não vai ao JSON
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--run", help="execução em experiments/runs/<run>/ (lê raw/e2_sctp.pcap)")
    src.add_argument("--pcap", help="PCAP avulso")
    parser.add_argument("--out", help="diretório de saída (padrão: experiments/e2_dissection/<run>)")
    parser.add_argument("--ric-port", type=int, action="append", help="porta SCTP do E2Term (padrão: 36421 e 36422)")
    parser.add_argument("--no-tshark", action="store_true", help="não executar a confirmação com tshark")
    parser.add_argument("--tshark", help="caminho do executável tshark")
    parser.add_argument("--xapp-events", help="JSON Lines da xApp kpm-probe (padrão: experiments/xapp_logs/<run>/kpm_probe_events.jsonl, se existir)")
    args = parser.parse_args(argv)

    if args.run:
        run_dir = ROOT / "experiments" / "runs" / args.run
        pcaps = sorted(run_dir.rglob("*.pcap"))
        if not pcaps:
            print(f"nenhum PCAP em {run_dir}", file=sys.stderr)
            return 2
        pcap_path, run_id = pcaps[0], args.run
    else:
        pcap_path, run_id = Path(args.pcap), Path(args.pcap).stem
    out_dir = Path(args.out) if args.out else ROOT / "experiments" / "e2_dissection" / run_id
    ports = tuple(args.ric_port) if args.ric_port else DEFAULT_RIC_PORTS
    events = Path(args.xapp_events) if args.xapp_events else ROOT / "experiments" / "xapp_logs" / run_id / "kpm_probe_events.jsonl"

    s = dissect(pcap_path, out_dir, run_id, ports, use_tshark=not args.no_tshark, tshark=args.tshark,
                xapp_events=events if events.exists() else None)
    print(f"PCAP: {s['source_pcap']} ({s['stats']['frames']} quadros, {s['stats']['data_chunks']} chunks DATA)")
    for m in s["messages"]:
        rid = ie_value(m, IE_RIC_REQUEST_ID)
        fn = ie_value(m, IE_RAN_FUNCTION_ID)
        extra = f" req={rid['requestor']}/{rid['instance']}" if isinstance(rid, dict) else ""
        extra += f" fn={fn}" if fn is not None else ""
        print(f"  #{m['index']:03d} quadro {m['frame']:>4} {m['direction']:<13} {m['role']:<28} {m['length']:>5} B{extra}")
    print(f"{s['message_count']} mensagens E2AP (listadas acima só as notáveis): "
          + ", ".join(f"{k}={v}" for k, v in s["role_counts"].items()))
    if s["ran_functions"]:
        print("RAN functions: " + ", ".join(f"{k}={v}" for k, v in s["ran_functions"].items()))
    print("Cadeia: " + ", ".join(f"{r}={'#%03d' % i if i else '—'}" for r, i in s["chain_roles"].items()))
    cmp_ = s["tshark_comparison"]
    if cmp_["checked"]:
        print(f"tshark ({s['tshark'].get('version', '')}): {cmp_['messages_tshark']} mensagens; "
              f"concordância {'SIM' if cmp_['agreement'] else 'NÃO'}")
        for mm in cmp_["mismatches"]:
            print(f"  divergência na posição {mm['position']}: dissecador={mm['dissector']} tshark={mm['tshark']}")
        for mm in cmp_.get("id_mismatches", []):
            print(f"  IDs divergentes no quadro {mm['frame']}: dissecador={mm['dissector']} tshark={mm['tshark']}")
    else:
        print(f"tshark: não executado ({s['tshark'].get('reason') or s['tshark'].get('error')})")
    x = s.get("xapp_crosscheck")
    if x:
        print(f"xApp: {x['xapp_indications']} Indications recebidas por RMR; "
              f"{x['pcap_indications_received_by_xapp']}/{x['pcap_indications']} do PCAP casadas por sha256; "
              f"{x['xapp_indications_not_in_pcap']} recebidas sem par no PCAP")
    for e in s["errors"]:
        print(f"ERRO: {e}")
    print(f"Saída: {out_dir}")
    return 0 if not s["errors"] and s["messages"] else 1


if __name__ == "__main__":
    sys.exit(main())
