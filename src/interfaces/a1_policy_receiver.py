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

import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logger = logging.getLogger("A1PolicyReceiver")


class A1PolicyManager:
    """
    Gerenciador de Estado e Validador de Políticas A1-P O-RAN WG2.
    """
    def __init__(self):
        self.active_policies: Dict[str, Dict[str, Any]] = {}
        self.policy_types: Dict[str, Dict[str, Any]] = {
            "20000": {
                "name": "ORAN_RDL_Governance_Policy",
                "description": "Diretrizes de priorização e cotas globais para xApp RDL",
                "schema": {
                    "type": "object",
                    "properties": {
                        "urllc_priority_boost": {"type": "number", "minimum": 0, "maximum": 50},
                        "energy_saving_allowed": {"type": "boolean"},
                        "max_cell_prb_limit": {"type": "number", "minimum": 10, "maximum": 100},
                        "cooling_lockout_ms": {"type": "number", "minimum": 100, "maximum": 5000}
                    }
                }
            }
        }

    def put_policy(self, policy_type_id: str, policy_id: str, policy_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Adiciona ou atualiza uma política A1-P."""
        if policy_type_id not in self.policy_types:
            return False, f"Policy type {policy_type_id} not supported"

        # Validação básica de esquema
        if "max_cell_prb_limit" in policy_data:
            val = policy_data["max_cell_prb_limit"]
            if not (10 <= val <= 100):
                return False, f"max_cell_prb_limit {val} out of bounds [10, 100]"

        self.active_policies[f"{policy_type_id}:{policy_id}"] = policy_data
        logger.info(f"[A1-P] Política {policy_type_id}:{policy_id} registrada com sucesso: {policy_data}")
        return True, "Policy created/updated successfully"

    def get_policy(self, policy_type_id: str, policy_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma política A1-P ativa."""
        return self.active_policies.get(f"{policy_type_id}:{policy_id}")

    def delete_policy(self, policy_type_id: str, policy_id: str) -> bool:
        """Remove uma política A1-P."""
        key = f"{policy_type_id}:{policy_id}"
        if key in self.active_policies:
            del self.active_policies[key]
            logger.info(f"[A1-P] Política {key} removida")
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
                content_len = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_len)
                try:
                    policy_json = json.loads(body.decode("utf-8"))
                    ok, msg = self.policy_manager.put_policy(ptype, pid, policy_json)
                    if ok:
                        self._send_json_response(201, {"status": "CREATED", "message": msg})
                    else:
                        self._send_json_response(400, {"error": msg})
                except Exception as e:
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
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
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
