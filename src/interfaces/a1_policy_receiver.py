"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Módulo: Receptor REST de Políticas A1-P (O-RAN.WG2.A1AP-v03.01 / A1-PMS)
Arquivo: src/interfaces/a1_policy_receiver.py
Descrição: Implementa o servidor de gerenciamento de políticas A1-P do Non-RT RIC (SMO)
           permitindo injeção de diretrizes de intenção de alto nível que governam
           a arbitragem do Reasoning e os limites do Refinement.
========================================================================================
"""

import fnmatch
import itertools
import json
import logging
import math
import re
import ipaddress
from typing import Callable, Dict, Any, Optional, Tuple, List
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logger = logging.getLogger("A1PolicyReceiver")

def _reject_json_constant(value: str):
    raise ValueError(f"Invalid JSON numeric constant: {value}")


class A1PolicyManager:
    """
    Gerenciador de Estado e Validador de Políticas A1-P O-RAN WG2.
    """
    def __init__(self):
        self.active_policies: Dict[str, Dict[str, Any]] = {}
        self.policy_types: Dict[str, Dict[str, Any]] = {
            "20000": {
                "name": "ORAN_RDL_Governance_Policy",
                "description": "Diretrizes de priorizacao e cotas globais para a xApp RDL",
                "schema": {
                    "type": "object",
                    "properties": {
                        "urllc_priority_boost": {"type": "number", "minimum": 0, "maximum": 50},
                        "energy_saving_allowed": {"type": "boolean"},
                        "max_cell_prb_limit": {"type": "number", "minimum": 10, "maximum": 100},
                        "cooling_lockout_ms": {"type": "number", "minimum": 100, "maximum": 5000},
                        # Janela de decisão: o que é crítico e o intervalo mínimo da classe crítica
                        "critical_targets": {"type": "array", "maxItems": 32,
                                             "items": {"type": "string", "pattern": "^[^:]+:[A-Z_]+$"}},
                        "critical_control_interval_ms": {"type": "number", "minimum": 20, "maximum": 1000},
                        # Governança (rApp de governança): modo de supervisão e teto de prioridade por xApp
                        "xapp_modes": {"type": "array", "maxItems": 64,
                                       "items": {"type": "string", "pattern": "^[^:]+:(MANAGED|ON_DEMAND|QUARANTINED)$"}},
                        "xapp_priority_caps": {"type": "array", "maxItems": 64,
                                               "items": {"type": "string", "pattern": "^[^:]+:(100|[1-9]?[0-9])$"}}
                    }
                }
            },
            # GreenRAN (OpenRAN@Brasil, UFPA): objetivos que o rApp-ResourceOptimizer
            # repassa à coordenação Near-RT entre xApp1-RANSlicer e xApp2-EnergySaver.
            "20001": {
                "name": "GreenRAN_Intent_Policy",
                "description": "Peso de energia e de SLA na arbitragem e regras de economia entre celulas",
                "schema": {
                    "type": "object",
                    "properties": {
                        "energy_weight": {"type": "number", "minimum": 0, "maximum": 0.6},
                        "sla_weight": {"type": "number", "minimum": 0.1, "maximum": 0.8},
                        "allow_neighbor_sleep": {"type": "boolean"},
                        "low_power_threshold_dbm": {"type": "number", "minimum": -10, "maximum": 43}
                    }
                }
            },
            # CA-RDL (Fase 2): liga/desliga a arbitragem MAPPO; a H-RDL só armazena e ignora
            "20002": {
                "name": "CARDL_Model_Policy",
                "description": "Liga ou desliga a arbitragem MAPPO da CA-RDL e ajusta a confianca minima (reserva: H-RDL)",
                "schema": {
                    "type": "object",
                    "properties": {
                        "marl_enabled": {"type": "boolean"},
                        "min_confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        }
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        # Dono e precedência por campo (doc 11 §5.1): (tipo, campo) -> padrões de policy_instance_id em
        # ordem de precedência (o primeiro vence). Campo fora do mapa: livre, vale a escrita mais recente.
        self.field_owners: Dict[Tuple[str, str], List[str]] = {}
        self._written_seq: Dict[str, int] = {}
        self._seq = itertools.count(1)

    # ------------------------------------------------------------------ dono e precedência por campo
    def set_field_owners(self, owners: Dict[str, Dict[str, List[str]]]) -> None:
        """``{"20000": {"cooling_lockout_ms": ["operator*", "rdl-governance"]}}``; padrões estilo glob sobre
        o policy_instance_id (o A1 Mediator não repassa o serviço do A1-PMS, só o ID da instância)."""
        parsed: Dict[Tuple[str, str], List[str]] = {}
        for type_id, fields in (owners or {}).items():
            if str(type_id).startswith("_"):
                continue
            type_id = str(type_id)
            if type_id not in self.policy_types:
                raise ValueError(f"tipo de política desconhecido no mapa de donos: {type_id}")
            schema = self.policy_types[type_id]["schema"]["properties"]
            for field, patterns in fields.items():
                if field not in schema:
                    raise ValueError(f"campo {field} não existe no tipo {type_id}")
                if not isinstance(patterns, list) or not patterns or not all(isinstance(x, str) and x for x in patterns):
                    raise ValueError(f"donos de {type_id}.{field} devem ser uma lista não vazia de padrões")
                parsed[(type_id, field)] = list(patterns)
        self.field_owners = parsed
        self._notify()

    def _owner_rank(self, type_id: str, field: str, instance_id: str) -> Optional[int]:
        """Posição do dono na precedência (0 = maior); ``None`` = instância sem direito ao campo."""
        owners = self.field_owners.get((type_id, field))
        if owners is None:
            return 0
        for rank, pattern in enumerate(owners):
            if fnmatch.fnmatchcase(instance_id, pattern):
                return rank
        return None

    def _rank_or_last(self, type_id: str, field: str, instance_id: str) -> int:
        """Precedência de uma instância já gravada; sem direito (mapa de donos mudou depois) fica por último."""
        rank = self._owner_rank(type_id, field, instance_id)
        return rank if rank is not None else 1_000_000

    def _candidates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Por campo: as instâncias ativas que o definem, com valor, precedência e ordem de escrita."""
        out: Dict[str, List[Dict[str, Any]]] = {}
        for key, policy in self.active_policies.items():
            type_id, _, instance_id = key.partition(":")
            for field, value in policy.items():
                out.setdefault(field, []).append({
                    "policy": key, "type": type_id, "instance": instance_id, "value": value,
                    "rank": self._rank_or_last(type_id, field, instance_id),
                    "seq": self._written_seq.get(key, 0),
                })
        return out

    def conflicts(self) -> List[Dict[str, Any]]:
        """Campos definidos por duas ou mais instâncias com valores diferentes (conflito entre rApps)."""
        found = []
        for field, cands in sorted(self._candidates().items()):
            values = {json.dumps(c["value"], sort_keys=True) for c in cands}
            if len(cands) < 2 or len(values) < 2:
                continue
            winner = min(cands, key=lambda c: (c["rank"], -c["seq"]))
            owned = any((c["type"], field) in self.field_owners for c in cands)
            found.append({
                "field": field,
                "rule": "owner_precedence" if owned else "most_recent",
                "winner": winner["policy"], "effective_value": winner["value"],
                "writers": [{"policy": c["policy"], "value": c["value"], "rank": c["rank"]}
                            for c in sorted(cands, key=lambda c: (c["rank"], -c["seq"]))],
            })
        return found

    def field_owners_view(self) -> Dict[str, Dict[str, List[str]]]:
        view: Dict[str, Dict[str, List[str]]] = {}
        for (type_id, field), patterns in sorted(self.field_owners.items()):
            view.setdefault(type_id, {})[field] = list(patterns)
        return view

    def add_listener(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registra quem aplica a política efetiva; é chamado a cada criação, atualização ou remoção."""
        self._listeners.append(callback)
        callback(self.effective_policy())

    def effective_policy(self) -> Dict[str, Any]:
        """Política efetiva, campo a campo: vence o dono de maior precedência; entre iguais (ou em campo
        sem dono definido), a escrita mais recente."""
        merged: Dict[str, Any] = {}
        for field, cands in self._candidates().items():
            merged[field] = min(cands, key=lambda c: (c["rank"], -c["seq"]))["value"]
        return merged

    def _notify(self) -> None:
        effective = self.effective_policy()
        for callback in self._listeners:
            try:
                callback(effective)
            except Exception as exc:  # um ouvinte com erro não derruba o receptor
                logger.error(f"[A1-P] Falha ao aplicar política efetiva: {exc}")

    def put_policy(self, policy_type_id: str, policy_id: str, policy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Adiciona ou atualiza uma política A1-P."""
        if policy_type_id not in self.policy_types:
            return False, f"Policy type {policy_type_id} not supported"
        if not isinstance(policy_data, dict):
            return False, "Policy body must be a JSON object"

        schema = self.policy_types[policy_type_id]["schema"]["properties"]
        for key, value in policy_data.items():
            if key not in schema:
                return False, f"Unsupported policy property: {key}"
            definition = schema[key]
            if definition["type"] == "boolean":
                if not isinstance(value, bool):
                    return False, f"{key} must be a boolean"
                continue
            if definition["type"] == "array":
                if not isinstance(value, list) or len(value) > definition.get("maxItems", 64):
                    return False, f"{key} must be a list with at most {definition.get('maxItems', 64)} items"
                pattern = re.compile(definition["items"]["pattern"])
                if not all(isinstance(item, str) and pattern.match(item) for item in value):
                    return False, f"{key} items must match {definition['items']['pattern']}"
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False, f"{key} must be a finite number"
            try:
                value = float(value)
            except (OverflowError, TypeError, ValueError):
                return False, f"{key} must be a finite number"
            if not math.isfinite(value):
                return False, f"{key} must be a finite number"
            if value < definition["minimum"] or value > definition["maximum"]:
                return False, f"{key} {value} out of bounds [{definition['minimum']}, {definition['maximum']}]"

        for field in policy_data:
            if self._owner_rank(policy_type_id, field, policy_id) is None:
                owners = self.field_owners[(policy_type_id, field)]
                return False, (f"Field {field} of type {policy_type_id} is owned by {owners}; "
                               f"instance {policy_id} may not write it")

        key = f"{policy_type_id}:{policy_id}"
        self.active_policies.pop(key, None)
        self.active_policies[key] = policy_data
        self._written_seq[key] = next(self._seq)  # ordem de escrita: desempate entre donos iguais
        logger.info(f"[A1-P] Política {policy_type_id}:{policy_id} registrada com sucesso: {policy_data}")
        self._notify()
        return True, "Policy created/updated successfully"

    def get_policy(self, policy_type_id: str, policy_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma política A1-P ativa."""
        return self.active_policies.get(f"{policy_type_id}:{policy_id}")

    def delete_policy(self, policy_type_id: str, policy_id: str) -> bool:
        """Remove uma política A1-P."""
        key = f"{policy_type_id}:{policy_id}"
        if key in self.active_policies:
            del self.active_policies[key]
            self._written_seq.pop(key, None)
            logger.info(f"[A1-P] Política {key} removida")
            self._notify()
            return True
        return False


class A1PolicyHttpHandler(BaseHTTPRequestHandler):
    policy_manager = A1PolicyManager()

    def do_GET(self):
        # /a1-p/v3/policytypes
        if self.path == "/a1-p/v3/policytypes":
            self._send_json_response(200, list(self.policy_manager.policy_types.keys()))
        elif "/a1-p/v3/policytypes/" in self.path:
            parts = self.path.strip("/").split("/")
            if len(parts) == 4: # /a1-p/v3/policytypes/{type}
                ptype = parts[3]
                if ptype in self.policy_manager.policy_types:
                    self._send_json_response(200, self.policy_manager.policy_types[ptype])
                else:
                    self._send_json_response(404, {"error": "Policy type not found"})
            elif len(parts) == 6: # /a1-p/v3/policytypes/{type}/policies/{id}
                ptype, pid = parts[3], parts[5]
                policy = self.policy_manager.get_policy(ptype, pid)
                if policy is not None:
                    self._send_json_response(200, policy)
                else:
                    self._send_json_response(404, {"error": "Policy not found"})
            else:
                self._send_json_response(400, {"error": "Invalid URI path"})
        elif self.path == "/health" or self.path == "/":
            self._send_json_response(200, {"status": "HEALTHY", "service": "A1-P Policy Receiver"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def do_PUT(self):
        if "/a1-p/v3/policytypes/" in self.path:
            parts = self.path.strip("/").split("/")
            if len(parts) == 6 and parts[4] == "policies":
                ptype, pid = parts[3], parts[5]
                try:
                    content_len = int(self.headers.get("Content-Length", 0))
                except (TypeError, ValueError):
                    self._send_json_response(400, {"error": "Invalid Content-Length"})
                    return
                if content_len <= 0 or content_len > 65536:
                    self._send_json_response(413, {"error": "Policy body must be between 1 and 65536 bytes"})
                    return
                body = self.rfile.read(content_len)
                try:
                    policy_json = json.loads(body.decode("utf-8"), parse_constant=_reject_json_constant)
                    ok, msg = self.policy_manager.put_policy(ptype, pid, policy_json)
                    if ok:
                        self._send_json_response(201, {"status": "CREATED", "message": msg})
                    else:
                        self._send_json_response(400, {"error": msg})
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
                    self._send_json_response(400, {"error": f"Malformed JSON: {str(e)}"})
            else:
                self._send_json_response(400, {"error": "Invalid PUT URI"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        if "/a1-p/v3/policytypes/" in self.path:
            parts = self.path.strip("/").split("/")
            if len(parts) == 6 and parts[4] == "policies":
                ptype, pid = parts[3], parts[5]
                ok = self.policy_manager.delete_policy(ptype, pid)
                if ok:
                    self._send_json_response(204, {})
                else:
                    self._send_json_response(404, {"error": "Policy not found"})
            else:
                self._send_json_response(400, {"error": "Invalid DELETE URI"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _send_json_response(self, status_code: int, data: Any):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if data:
            self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        # Desativa logs verbosos no stdout
        return


class A1PolicyReceiverServer:
    """Servidor A1-P em segundo plano."""
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        if host != "localhost":
            try:
                is_loopback = ipaddress.ip_address(host).is_loopback
            except ValueError as exc:
                raise ValueError("A1 Policy Receiver host must be a loopback address.") from exc
            if not is_loopback:
                raise ValueError("A1 Policy Receiver has no authentication; bind it to loopback only.")
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.server = HTTPServer((self.host, self.port), A1PolicyHttpHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"[A1-P] Servidor de Políticas A1-P ativo em http://{self.host}:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("[A1-P] Servidor de Políticas A1-P encerrado")
