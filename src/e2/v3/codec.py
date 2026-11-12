"""
Codec E2AP v03.01 / E2SM-KPM v03.00 / E2SM-RC v03.01 — as versões do NORI e da Release I.

Arquivo único e autocontido (biblioteca padrão + ``asn1tools`` só para o E2SM), para ser usado
tanto pela xApp RDL quanto pela xApp ``kpm-probe`` no cluster (o chart recebe o ``src/`` de um
commit por ``scripts/deploy_kpm_probe.sh``), sem cópias divergentes.

- E2AP: codificação APER escrita à mão para o subconjunto usado (RIC Control Request e leitura
  de Acknowledge/Failure). O E2AP usa classes de objetos de informação que o ``asn1tools`` não
  trata; a validação independente é feita pelo tshark sobre o PCAP da execução.
- E2SM-KPM e E2SM-RC: ``asn1tools`` compilando o ASN.1 do próprio NORI (commit fixado), baixado
  e conferido por sha256 (``ensure_asn1``).

Controle de fatia (E2SM-RC, estilo 2 "Radio Resource Allocation Control", ação 6 "Slice-level PRB
quota"), no formato que o NORI decodifica (``model/ric-control-message.cc``): Control Message
Format 1 com o RAN Parameter 1 (RRM Policy Ratio List) como lista de estruturas, cada uma com
3 = SST, 4 = Max PRB ratio, 5 = Min PRB ratio, 6 = Dedicated PRB ratio.
"""

from __future__ import annotations

import hashlib
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

NORI_COMMIT = "8a30867c8105d328aa50a7daaab3bcb2b4603763"
NORI_ASN1_BASE_URL = f"https://raw.githubusercontent.com/lasseufpa/nori/{NORI_COMMIT}/asn/v03"
NORI_ASN1_FILES = {
    "e2sm-v03.01.asn": "2e3a0ec42bafec8a8084ada1e92a968004cfa199d2ec86d8356f0ee42a2b202e",
    "e2sm-kpm-v03.00.asn": "9f13a077601f701685296fb777d57891d0c9691af3711b6b234fdef135fd84b6",
    "e2sm-rc-v03.01.asn": "ec0a8d603301854199ce86e85d7c19576aa82d3757540ee1bdec9e6b003f211b",
}

# E2AP v03.01
PDU_INITIATING, PDU_SUCCESSFUL, PDU_UNSUCCESSFUL = 0, 1, 2
PDU_KINDS = ("initiatingMessage", "successfulOutcome", "unsuccessfulOutcome")
CRIT_REJECT, CRIT_IGNORE, CRIT_NOTIFY = 0, 1, 2
PROC_RIC_CONTROL = 4
PROC_RIC_INDICATION = 5
IE_CAUSE = 1
IE_RAN_FUNCTION_ID = 5
IE_RIC_CALL_PROCESS_ID = 20
IE_RIC_CONTROL_ACK_REQUEST = 21
IE_RIC_CONTROL_HEADER = 22
IE_RIC_CONTROL_MESSAGE = 23
IE_RIC_INDICATION_HEADER = 25
IE_RIC_INDICATION_MESSAGE = 26
IE_RIC_REQUEST_ID = 29
IE_RIC_CONTROL_OUTCOME = 32

# E2SM-RC v03.01: estilo de controle 2, ação 6 (cota de PRB por fatia)
RC_STYLE_RADIO_RESOURCE_ALLOCATION = 2
RC_ACTION_SLICE_PRB_QUOTA = 6
RC_PARAM_RRM_POLICY_RATIO_LIST = 1
RC_PARAM_SST, RC_PARAM_MAX_PRB, RC_PARAM_MIN_PRB, RC_PARAM_DEDICATED_PRB = 3, 4, 5, 6
# IDs dos RAN Parameters da cota de PRB por fatia no leiaute plano do NORI; outro E2 Agent (srsRAN, OAI)
# pode usar outros IDs: o perfil do backend os sobrepõe (src/e2/backends/testbed_profiles.py)
NORI_RC_SLICE_IDS = {"list": RC_PARAM_RRM_POLICY_RATIO_LIST, "sst": RC_PARAM_SST, "max": RC_PARAM_MAX_PRB,
                     "min": RC_PARAM_MIN_PRB, "dedicated": RC_PARAM_DEDICATED_PRB}


class CodecError(ValueError):
    pass


# ---------------------------------------------------------------------------
# ASN.1 do NORI (download fixado por sha256)
# ---------------------------------------------------------------------------

def default_asn1_dir() -> Path:
    env = os.environ.get("XAPP_RDL_ASN1_DIR")
    if env:
        return Path(env)
    return Path.home() / ".cache" / "xapp-rdl" / f"nori-asn1-{NORI_COMMIT[:7]}"


def ensure_asn1(directory: Optional[Path] = None, download: bool = True) -> Path:
    """Garante os arquivos ASN.1 E2SM do NORI em ``directory``, conferindo o sha256 de cada um."""
    d = Path(directory) if directory else default_asn1_dir()
    d.mkdir(parents=True, exist_ok=True)
    for name, expected in NORI_ASN1_FILES.items():
        path = d / name
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            continue
        if not download:
            raise CodecError(f"ASN.1 {name} ausente ou com sha256 divergente em {d}")
        data = urllib.request.urlopen(f"{NORI_ASN1_BASE_URL}/{name}", timeout=60).read()
        got = hashlib.sha256(data).hexdigest()
        if got != expected:
            raise CodecError(f"sha256 divergente para {name}: {got} != {expected}")
        path.write_bytes(data)
    return d


# ---------------------------------------------------------------------------
# APER (subconjunto)
# ---------------------------------------------------------------------------

class AperWriter:
    def __init__(self) -> None:
        self._bits: List[int] = []

    def bits(self, value: int, n: int) -> "AperWriter":
        for i in range(n - 1, -1, -1):
            self._bits.append((value >> i) & 1)
        return self

    def align(self) -> "AperWriter":
        while len(self._bits) % 8:
            self._bits.append(0)
        return self

    def octets(self, data: bytes) -> "AperWriter":
        self.align()
        for byte in data:
            self.bits(byte, 8)
        return self

    def length(self, n: int) -> "AperWriter":
        if n < 128:
            return self.octets(bytes([n]))
        if n < 16384:
            return self.octets(bytes([0x80 | (n >> 8), n & 0xFF]))
        raise CodecError("comprimento >= 16K (fragmentação APER) não suportado")

    def constrained(self, value: int, lo: int, hi: int) -> "AperWriter":
        if not lo <= value <= hi:
            raise CodecError(f"valor {value} fora de [{lo}, {hi}]")
        rng, v = hi - lo + 1, value - lo
        if rng == 1:
            return self
        if rng <= 255:
            return self.bits(v, (rng - 1).bit_length())
        if rng == 256:
            return self.octets(bytes([v]))
        if rng <= 65536:
            return self.octets(v.to_bytes(2, "big"))
        raise CodecError("faixa > 65536 não suportada")

    def open_type(self, data: bytes) -> "AperWriter":
        return self.length(len(data)).octets(data)

    def to_bytes(self) -> bytes:
        self.align()
        return bytes(int("".join(map(str, self._bits[i:i + 8])), 2) for i in range(0, len(self._bits), 8))


class AperReader:
    def __init__(self, data: bytes) -> None:
        self.data, self.bit = data, 0

    def bits(self, n: int) -> int:
        value = 0
        for _ in range(n):
            byte = self.bit >> 3
            if byte >= len(self.data):
                raise CodecError("fim inesperado do PDU")
            value = (value << 1) | ((self.data[byte] >> (7 - (self.bit & 7))) & 1)
            self.bit += 1
        return value

    def align(self) -> None:
        self.bit = (self.bit + 7) & ~7

    def octets(self, n: int) -> bytes:
        self.align()
        start = self.bit >> 3
        if start + n > len(self.data):
            raise CodecError("fim inesperado do PDU")
        self.bit += 8 * n
        return self.data[start:start + n]

    def length(self) -> int:
        first = self.octets(1)[0]
        if first & 0x80 == 0:
            return first
        if first & 0xC0 == 0x80:
            return ((first & 0x3F) << 8) | self.octets(1)[0]
        raise CodecError("comprimento fragmentado não suportado")

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
        raise CodecError("faixa > 65536 não suportada")

    def open_type(self) -> bytes:
        return self.octets(self.length())


# ---------------------------------------------------------------------------
# E2AP v03.01
# ---------------------------------------------------------------------------

def encode_e2ap_pdu(kind: int, procedure_code: int, criticality: int,
                    ies: Sequence[Tuple[int, int, bytes]]) -> bytes:
    """E2AP-PDU com SEQUENCE { protocolIEs, ... } sem extensões. ``ies``: (id, criticality, valor APER)."""
    body = AperWriter().bits(0, 1).constrained(len(ies), 0, 65535)
    for ie_id, crit, value in ies:
        body.constrained(ie_id, 0, 65535).bits(crit, 2).open_type(value)
    return (AperWriter().bits(0, 1).bits(kind, 2).constrained(procedure_code, 0, 255)
            .bits(criticality, 2).open_type(body.to_bytes()).to_bytes())


def _ric_request_id(requestor: int, instance: int) -> bytes:
    return AperWriter().bits(0, 1).constrained(requestor, 0, 65535).constrained(instance, 0, 65535).to_bytes()


def _octet_string(data: bytes) -> bytes:
    return AperWriter().length(len(data)).octets(data).to_bytes()


def encode_ric_control_request(requestor: int, instance: int, ran_function_id: int, header: bytes,
                               message: bytes, ack_request: bool = True,
                               call_process_id: Optional[bytes] = None) -> bytes:
    """RICcontrolRequest (E2AP v03.01, 9.1.1.4), IEs na ordem da definição do ASN.1."""
    ies = [(IE_RIC_REQUEST_ID, CRIT_REJECT, _ric_request_id(requestor, instance)),
           (IE_RAN_FUNCTION_ID, CRIT_REJECT, AperWriter().constrained(ran_function_id, 0, 4095).to_bytes())]
    if call_process_id is not None:
        ies.append((IE_RIC_CALL_PROCESS_ID, CRIT_REJECT, _octet_string(call_process_id)))
    ies += [(IE_RIC_CONTROL_HEADER, CRIT_REJECT, _octet_string(header)),
            (IE_RIC_CONTROL_MESSAGE, CRIT_REJECT, _octet_string(message))]
    if ack_request is not None:
        # RICcontrolAckRequest ::= ENUMERATED { noAck, ack, ... }
        ies.append((IE_RIC_CONTROL_ACK_REQUEST, CRIT_REJECT,
                    AperWriter().bits(0, 1).bits(1 if ack_request else 0, 1).to_bytes()))
    return encode_e2ap_pdu(PDU_INITIATING, PROC_RIC_CONTROL, CRIT_REJECT, ies)


def decode_e2ap_pdu(pdu: bytes) -> Dict[str, Any]:
    """Cabeçalho do E2AP-PDU e IEs de identificação (RICrequestID, RANfunctionID)."""
    r = AperReader(pdu)
    if r.bits(1):
        raise CodecError("alternativa de extensão do E2AP-PDU")
    kind = r.bits(2)
    if kind > 2:
        raise CodecError(f"tipo de E2AP-PDU inválido: {kind}")
    code = r.constrained(0, 255)
    crit = r.bits(2)
    value = r.open_type()
    if (r.bit + 7) >> 3 != len(pdu):
        raise CodecError("bytes além do fim do E2AP-PDU")
    body = AperReader(value)
    if body.bits(1):
        raise CodecError("extensões no SEQUENCE da mensagem")
    ies: Dict[int, bytes] = {}
    for _ in range(body.constrained(0, 65535)):
        ie_id = body.constrained(0, 65535)
        body.bits(2)
        ies[ie_id] = body.open_type()
    out: Dict[str, Any] = {"pdu_type": PDU_KINDS[kind], "procedure_code": code, "criticality": crit,
                           "ie_ids": sorted(ies)}
    if IE_RIC_REQUEST_ID in ies:
        rr = AperReader(ies[IE_RIC_REQUEST_ID])
        rr.bits(1)
        out["ric_requestor_id"] = rr.constrained(0, 65535)
        out["ric_instance_id"] = rr.constrained(0, 65535)
    if IE_RAN_FUNCTION_ID in ies:
        out["ran_function_id"] = AperReader(ies[IE_RAN_FUNCTION_ID]).constrained(0, 4095)
    for ie_id, key in ((IE_RIC_CONTROL_HEADER, "control_header"), (IE_RIC_CONTROL_MESSAGE, "control_message"),
                       (IE_RIC_CONTROL_OUTCOME, "control_outcome"), (IE_RIC_CALL_PROCESS_ID, "call_process_id"),
                       (IE_RIC_INDICATION_HEADER, "indication_header"),
                       (IE_RIC_INDICATION_MESSAGE, "indication_message")):
        if ie_id in ies:
            rr = AperReader(ies[ie_id])
            out[key] = rr.octets(rr.length())
    if IE_RIC_CONTROL_ACK_REQUEST in ies:
        rr = AperReader(ies[IE_RIC_CONTROL_ACK_REQUEST])
        rr.bits(1)
        out["ack_request"] = bool(rr.bits(1))
    if IE_CAUSE in ies:
        out["cause_raw"] = ies[IE_CAUSE].hex()
    return out


def parse_ric_control_outcome(pdu: bytes) -> Dict[str, Any]:
    """RICcontrolAcknowledge ou RICcontrolFailure: tipo do desfecho e IDs para correlação."""
    d = decode_e2ap_pdu(pdu)
    if d["procedure_code"] != PROC_RIC_CONTROL or d["pdu_type"] == "initiatingMessage":
        raise CodecError(f"não é desfecho de RIC Control: {d['pdu_type']} procedimento {d['procedure_code']}")
    d["outcome"] = "ACK" if d["pdu_type"] == "successfulOutcome" else "FAILURE"
    return d


# ---------------------------------------------------------------------------
# E2SM (asn1tools sobre o ASN.1 do NORI)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SlicePrbQuota:
    sst: int                # Slice/Service Type (1 eMBB, 2 URLLC, ...)
    max_prb_ratio: int      # %
    min_prb_ratio: int = 0
    dedicated_prb_ratio: int = 0

    def validate(self) -> None:
        if not 0 <= self.sst <= 255:
            raise CodecError(f"SST fora de [0, 255]: {self.sst}")
        for name in ("max_prb_ratio", "min_prb_ratio", "dedicated_prb_ratio"):
            if not 0 <= getattr(self, name) <= 100:
                raise CodecError(f"{name} fora de [0, 100]: {getattr(self, name)}")
        if self.min_prb_ratio > self.max_prb_ratio:
            raise CodecError("min_prb_ratio > max_prb_ratio")


class E2smCodec:
    """E2SM-KPM v03.00 e E2SM-RC v03.01 compilados do ASN.1 do NORI."""

    def __init__(self, asn1_dir: Optional[Path] = None, download: bool = True) -> None:
        import asn1tools  # dependência opcional (extra "e2v3")
        d = ensure_asn1(asn1_dir, download=download)
        common = str(d / "e2sm-v03.01.asn")
        self.kpm = asn1tools.compile_files([common, str(d / "e2sm-kpm-v03.00.asn")], "per")
        self.rc = asn1tools.compile_files([common, str(d / "e2sm-rc-v03.01.asn")], "per")
        # Leitura tolerante: o NORI envia nomes de métrica com "_" (ex.: QosFlow.PdcpPduVolumeDL_Filter),
        # fora do alfabeto de PrintableString. Em APER alinhado, PrintableString e IA5String sem alfabeto
        # restrito têm a mesma codificação (8 bits por caractere, código ASCII); trocar só o tipo de
        # MeasurementTypeName na especificação de leitura aceita esses bytes. A codificação segue estrita.
        kpm_text = (d / "e2sm-kpm-v03.00.asn").read_text(encoding="utf-8")
        strict = "MeasurementTypeName ::= PrintableString(SIZE(1.. 150, ...))"
        if kpm_text.count(strict) != 1:
            raise CodecError("definição de MeasurementTypeName inesperada no ASN.1 KPM")
        self.kpm_lenient = asn1tools.compile_string(
            Path(common).read_text(encoding="utf-8") + "\n"
            + kpm_text.replace(strict, "MeasurementTypeName ::= IA5String(SIZE(1.. 150, ...))"), "per")
        self.asn1_sha256 = dict(NORI_ASN1_FILES)

    # KPM ------------------------------------------------------------------
    def kpm_event_trigger(self, reporting_period_ms: int) -> bytes:
        return self.kpm.encode("E2SM-KPM-EventTriggerDefinition", {
            "eventDefinition-formats": ("eventDefinition-Format1", {"reportingPeriod": reporting_period_ms})})

    def kpm_action_definition(self, meas_names: Sequence[str], granularity_ms: int, style: int = 1) -> bytes:
        return self.kpm.encode("E2SM-KPM-ActionDefinition", {
            "ric-Style-Type": style,
            "actionDefinition-formats": ("actionDefinition-Format1", {
                "measInfoList": [{"measType": ("measName", n), "labelInfoList": [{"measLabel": {"noLabel": "true"}}]}
                                 for n in meas_names],
                "granulPeriod": granularity_ms})})

    def kpm_decode_indication(self, header: bytes, message: bytes) -> Dict[str, Any]:
        """Indication KPM v03.00 normalizada: formato, instante de coleta e medições.

        Format 1 (nó): ``{"node": {métrica: valor}}``; Format 3 (por UE):
        ``{"ues": [{"ue_id": ..., "measurements": {métrica: valor}}]}``. Cada métrica traz o
        valor da última amostra (``measData``) do período de granularidade.
        """
        out: Dict[str, Any] = {}
        hdr = self.kpm_lenient.decode("E2SM-KPM-IndicationHeader", header)
        hfmt, hbody = hdr["indicationHeader-formats"]
        ts = hbody.get("colletStartTime")
        if isinstance(ts, (bytes, bytearray)) and len(ts) == 8:
            # TimeStamp: 4 octetos de segundos NTP + 4 de fração
            secs, frac = int.from_bytes(ts[:4], "big"), int.from_bytes(ts[4:], "big")
            out["collect_start_ntp"] = round(secs + frac / 2 ** 32, 6)
        msg = self.kpm_lenient.decode("E2SM-KPM-IndicationMessage", message)
        fmt, body = msg["indicationMessage-formats"]
        if fmt == "indicationMessage-Format1":
            out["format"] = 1
            out["node"] = self._kpm_format1(body)
        elif fmt == "indicationMessage-Format3":
            out["format"] = 3
            ues = []
            for item in body["ueMeasReportList"]:
                kind, ue = item["ueID"]
                ue_id = ue.get("amf-UE-NGAP-ID") if isinstance(ue, dict) else None
                ues.append({"ue_id": ue_id, "ue_id_type": kind, "measurements": self._kpm_format1(item["measReport"])})
            out["ues"] = ues
        else:
            raise CodecError(f"formato de Indication KPM não suportado: {fmt}")
        return out

    @staticmethod
    def _kpm_format1(body: Dict[str, Any]) -> Dict[str, Any]:
        names = []
        for info in body.get("measInfoList") or []:
            kind, value = info["measType"]
            names.append(value if kind == "measName" else f"measID:{value}")
        values: Dict[str, Any] = {}
        for sample in body.get("measData") or []:
            for name, (kind, value) in zip(names, sample["measRecord"]):
                values[name] = None if kind == "noValue" else value
        return values

    # RC -------------------------------------------------------------------
    def rc_slice_quota_header(self, plmn: bytes = b"\x00\xf1\x10", amf_ue_ngap_id: int = 0,
                              decision_accept: bool = True) -> bytes:
        """Control Header Format 1: estilo 2, ação 6. O UEID (obrigatório no Format 1) é nominal:
        a cota é por fatia e o NORI só o registra em log."""
        if len(plmn) != 3:
            raise CodecError("PLMN Identity tem 3 octetos")
        header = {
            "ueID": ("gNB-UEID", {
                "amf-UE-NGAP-ID": amf_ue_ngap_id,
                "guami": {"pLMNIdentity": plmn, "aMFRegionID": (b"\x01", 8),
                          "aMFSetID": (b"\x00\x40", 10), "aMFPointer": (b"\x04", 6)},
            }),
            "ric-Style-Type": RC_STYLE_RADIO_RESOURCE_ALLOCATION,
            "ric-ControlAction-ID": RC_ACTION_SLICE_PRB_QUOTA,
        }
        if decision_accept is not None:
            header["ric-ControlDecision"] = "accept" if decision_accept else "reject"
        return self.rc.encode("E2SM-RC-ControlHeader", {"ric-controlHeader-formats": ("controlHeader-Format1", header)})

    def rc_slice_quota_message(self, quotas: Sequence[SlicePrbQuota], param_ids: Optional[Dict[str, int]] = None) -> bytes:
        ids = {**NORI_RC_SLICE_IDS, **(param_ids or {})}
        if not quotas:
            raise CodecError("ao menos uma cota de fatia")
        structures = []
        for q in quotas:
            q.validate()

            def element(param_id: int, value: Tuple[str, Any]) -> Dict[str, Any]:
                return {"ranParameter-ID": param_id,
                        "ranParameter-valueType": ("ranP-Choice-ElementFalse", {"ranParameter-value": value})}

            structures.append({"sequence-of-ranParameters": [
                element(ids["sst"], ("valueOctS", bytes([q.sst]))),
                element(ids["max"], ("valueInt", q.max_prb_ratio)),
                element(ids["min"], ("valueInt", q.min_prb_ratio)),
                element(ids["dedicated"], ("valueInt", q.dedicated_prb_ratio)),
            ]})
        message = {"ranP-List": [{
            "ranParameter-ID": ids["list"],
            "ranParameter-valueType": ("ranP-Choice-List", {"ranParameter-List": {"list-of-ranParameter": structures}}),
        }]}
        return self.rc.encode("E2SM-RC-ControlMessage", {"ric-controlMessage-formats": ("controlMessage-Format1", message)})

    def rc_decode_header(self, data: bytes) -> Dict[str, Any]:
        return self.rc.decode("E2SM-RC-ControlHeader", data)

    def rc_decode_slice_quotas(self, data: bytes, param_ids: Optional[Dict[str, int]] = None) -> List[SlicePrbQuota]:
        """Lê as cotas como o NORI lê (ric-control-message.cc), para verificação do que foi enviado."""
        ids = {**NORI_RC_SLICE_IDS, **(param_ids or {})}
        decoded = self.rc.decode("E2SM-RC-ControlMessage", data)
        fmt, body = decoded["ric-controlMessage-formats"]
        if fmt != "controlMessage-Format1":
            raise CodecError(f"formato de Control Message não suportado: {fmt}")
        quotas = []
        for item in body["ranP-List"]:
            kind, value = item["ranParameter-valueType"]
            if item["ranParameter-ID"] != ids["list"] or kind != "ranP-Choice-List":
                continue
            for struct in value["ranParameter-List"]["list-of-ranParameter"]:
                fields = {}
                for p in struct.get("sequence-of-ranParameters", []):
                    _, element = p["ranParameter-valueType"]
                    vkind, v = element.get("ranParameter-value", (None, None))
                    fields[p["ranParameter-ID"]] = v[0] if vkind == "valueOctS" else v
                quotas.append(SlicePrbQuota(fields.get(ids["sst"], 0), fields.get(ids["max"], 100),
                                            fields.get(ids["min"], 0), fields.get(ids["dedicated"], 0)))
        return quotas


def build_slice_quota_control(codec: E2smCodec, requestor: int, instance: int, ran_function_id: int,
                              quotas: Sequence[SlicePrbQuota], plmn: bytes = b"\x00\xf1\x10") -> bytes:
    """RICcontrolRequest completo (E2AP + E2SM-RC) para cotas de PRB por fatia, pedindo ACK."""
    return encode_ric_control_request(requestor, instance, ran_function_id,
                                      codec.rc_slice_quota_header(plmn), codec.rc_slice_quota_message(quotas),
                                      ack_request=True)
