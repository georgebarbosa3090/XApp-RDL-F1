"""
========================================================================================
Projeto: xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)
Módulo: Testes Unitários do Receptor de Políticas A1-P (O-RAN WG2)
Arquivo: tests/unit/test_a1_policy_receiver.py
========================================================================================
"""

import pytest
from src.interfaces.a1_policy_receiver import A1PolicyManager


def test_a1_policy_manager_crud():
    manager = A1PolicyManager()

    # 1. Validação de tipos suportados
    assert "20000" in manager.policy_types

    # 2. Inserção de política válida
    valid_policy = {
        "urllc_priority_boost": 15.0,
        "energy_saving_allowed": True,
        "max_cell_prb_limit": 85.0,
        "cooling_lockout_ms": 1000.0
    }
    ok, msg = manager.put_policy("20000", "policy_s01", valid_policy)
    assert ok is True
    assert "successfully" in msg

    # 3. Consulta de política existente
    retrieved = manager.get_policy("20000", "policy_s01")
    assert retrieved is not None
    assert retrieved["max_cell_prb_limit"] == 85.0

    # 4. Inserção de política com parâmetro fora dos limites
    invalid_policy = {
        "max_cell_prb_limit": 150.0  # Inválido (> 100)
    }
    ok_inv, msg_inv = manager.put_policy("20000", "policy_s02", invalid_policy)
    assert ok_inv is False
    assert "out of bounds" in msg_inv

    # 5. Remoção de política
    assert manager.delete_policy("20000", "policy_s01") is True
    assert manager.get_policy("20000", "policy_s01") is None


def test_a1_policy_http_handler():
    from unittest.mock import MagicMock
    from io import BytesIO
    import json
    from src.interfaces.a1_policy_receiver import A1PolicyHttpHandler, A1PolicyReceiverServer

    handler = A1PolicyHttpHandler.__new__(A1PolicyHttpHandler)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = BytesIO()

    # 1. GET /health e /
    handler.path = "/health"
    handler.do_GET()
    assert handler.send_response.called

    handler.path = "/"
    handler.do_GET()

    # 2. GET /a1-p/v3/policytypes
    handler.path = "/a1-p/v3/policytypes"
    handler.do_GET()

    # 3. GET /a1-p/v3/policytypes/20000
    handler.path = "/a1-p/v3/policytypes/20000"
    handler.do_GET()

    # 4. GET /a1-p/v3/policytypes/99999 (not found)
    handler.path = "/a1-p/v3/policytypes/99999"
    handler.do_GET()

    # 5. PUT /a1-p/v3/policytypes/20000/policies/p_test
    body = json.dumps({"max_cell_prb_limit": 70.0}).encode("utf-8")
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_test"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = BytesIO(body)
    handler.do_PUT()

    # 6. GET /a1-p/v3/policytypes/20000/policies/p_test
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_test"
    handler.do_GET()

    # 7. GET /a1-p/v3/policytypes/20000/policies/p_nonexistent
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_nonexistent"
    handler.do_GET()

    # 8. PUT with malformed JSON
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_bad"
    handler.headers = {"Content-Length": "7"}
    handler.rfile = BytesIO(b"bad_json")
    handler.do_PUT()

    # 9. PUT with invalid schema / parameter
    bad_body = json.dumps({"max_cell_prb_limit": 999.0}).encode("utf-8")
    handler.headers = {"Content-Length": str(len(bad_body))}
    handler.rfile = BytesIO(bad_body)
    handler.do_PUT()

    # 10. DELETE /a1-p/v3/policytypes/20000/policies/p_test
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_test"
    handler.do_DELETE()

    # 11. DELETE nonexistent
    handler.path = "/a1-p/v3/policytypes/20000/policies/p_test"
    handler.do_DELETE()

    # 12. Invalid paths
    for path in ["/unknown", "/a1-p/v3/policytypes/too/many/path/segments/here"]:
        handler.path = path
        handler.do_GET()
        handler.do_PUT()
        handler.do_DELETE()

    handler.log_message("test format %s", "arg")

    # 13. Server Lifecycle
    server = A1PolicyReceiverServer(host="127.0.0.1", port=18089)
    server.start()
    server.stop()

