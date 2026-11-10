"""
Políticas A1 pelo caminho O-RAN SC: A1 Mediator do Near-RT RIC ↔ xApp por RMR.

O Non-RT RIC (A1-PMS) cria instâncias de política no A1 Mediator, que as entrega à xApp:

- ``A1_POLICY_REQUEST`` (20010), mediador → xApp:
  ``{"operation": "CREATE"|"UPDATE"|"DELETE", "policy_type_id": 20001,
     "policy_instance_id": "greenran", "payload": {...}}``
- ``A1_POLICY_RESPONSE`` (20011), xApp → mediador:
  ``{"policy_type_id": 20001, "policy_instance_id": "greenran", "handler_id": "<xapp>",
     "status": "OK"|"ERROR"|"DELETED"}``
- ``A1_POLICY_QUERY`` (20012), xApp → mediador, na partida: ``{"policy_type_id": 20001}``;
  o mediador reenvia as instâncias existentes como 20010.

As instâncias são aplicadas no ``A1PolicyManager`` (validação pelos esquemas dos tipos), que
notifica a política efetiva aos ouvintes (doc 02 §7.1).
"""

import json
from typing import Any, Dict, List, Tuple

A1_POLICY_REQUEST = 20010
A1_POLICY_RESPONSE = 20011
A1_POLICY_QUERY = 20012


def handle_policy_request(manager, payload: bytes, handler_id: str) -> Tuple[Dict[str, Any], bool]:
    """Aplica uma mensagem 20010 e devolve (corpo da resposta 20011, aplicada?)."""
    try:
        msg = json.loads(payload.decode("utf-8") if isinstance(payload, (bytes, bytearray)) else payload)
        operation = str(msg["operation"]).upper()
        type_id = str(msg["policy_type_id"])
        instance_id = str(msg["policy_instance_id"])
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        return {"handler_id": handler_id, "status": "ERROR", "reason": f"mensagem A1 inválida: {exc}"}, False

    response: Dict[str, Any] = {"policy_type_id": int(type_id) if type_id.isdigit() else type_id,
                                "policy_instance_id": instance_id, "handler_id": handler_id}
    if operation == "DELETE":
        manager.delete_policy(type_id, instance_id)
        response["status"] = "DELETED"
        return response, True
    if operation not in ("CREATE", "UPDATE"):
        response.update(status="ERROR", reason=f"operação desconhecida: {operation}")
        return response, False
    body = msg.get("payload", {})
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except ValueError:
            response.update(status="ERROR", reason="payload não é JSON")
            return response, False
    ok, reason = manager.put_policy(type_id, instance_id, body)
    response["status"] = "OK" if ok else "ERROR"
    if not ok:
        response["reason"] = reason
    return response, ok


def query_messages(type_ids: List[str]) -> List[bytes]:
    """Corpos das mensagens 20012 para pedir ao mediador as instâncias já existentes."""
    return [json.dumps({"policy_type_id": int(t)}).encode("utf-8") for t in type_ids if str(t).isdigit()]


def policy_type_definitions(manager) -> List[Dict[str, Any]]:
    """Definições no formato do A1 Mediator (PUT /A1-P/v2/policytypes/{id})."""
    out = []
    for type_id, spec in sorted(manager.policy_types.items()):
        out.append({
            "policy_type_id": int(type_id),
            "name": spec["name"],
            "description": spec["description"],
            "create_schema": {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
                              "additionalProperties": False, "properties": spec["schema"]["properties"]},
        })
    return out
