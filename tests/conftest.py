import os
import pytest

# Garante variáveis de ambiente padronizadas para testes unitários
os.environ.setdefault("USE_FAKE_SDL", "True")
os.environ.setdefault("RDL_MODE", "OFFLINE_SIMULATION")
os.environ.setdefault("RAN_BACKEND", "NORI_NS3")

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reseta singletons e estado global entre testes para isolamento completo."""
    from src.observability.causal_tracker import causal_tracker
    causal_tracker.reset()
    yield
    causal_tracker.reset()
