#!/usr/bin/env python3
"""Roda funções de teste que exigem o Linux (shim, socket Unix) no venv do WSL, que não tem pytest.

Uso: python scripts/closed_loop/run_test_wsl.py tests/integration/test_shim_es_orange.py [nome_do_teste]
"""
import importlib.util
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    import pytest  # noqa: F401
except ImportError:  # o venv do WSL não tem pytest: só o necessário para importar os testes
    import types

    _mark = types.SimpleNamespace(skipif=lambda *a, **k: (lambda f: f), parametrize=lambda *a, **k: (lambda f: f))
    sys.modules["pytest"] = types.SimpleNamespace(mark=_mark, skip=lambda msg="": None)
path, wanted = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
spec = importlib.util.spec_from_file_location("teste", ROOT / path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
falhas = 0
for name, fn in inspect.getmembers(mod, inspect.isfunction):
    if not name.startswith("test_") or (wanted and name != wanted):
        continue
    args = [Path(tempfile.mkdtemp())] if "tmp_path" in inspect.signature(fn).parameters else []
    try:
        fn(*args)
        print("PASSOU", name)
    except Exception:  # noqa: BLE001
        falhas += 1
        print("FALHOU", name)
        traceback.print_exc()
sys.exit(1 if falhas else 0)
