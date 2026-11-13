# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
Laço comum das xApps derivadas: propõem só a partir do KPM (decisão do autor de 2026-11-13).

O núcleo de decisão fica em ``src/xapps`` (o mesmo usado na malha fechada do ns-3). Aqui ele recebe o
KPM do RIC: subscrição E2SM-KPM pelo SubMgr do O-RAN SC e Indications pelo RMR 12050
(``src.greenran.common.RicKpmSource``). Sem ``SUBMGR_URL``, a xApp não tem KPM e não propõe nada.

Variáveis: ``SUBMGR_URL``, ``KPM_NODES`` (nós E2, separados por vírgula), ``KPM_RAN_FUNCTION_ID``
(padrão 2), ``KPM_PERIOD_MS`` (padrão 1000).
"""
import logging
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logger = logging.getLogger("kpm_runtime")


def make_core(core_cls, transport):
    """Núcleo KPM da xApp, usando o transporte (RMR 30000/30001) da própria xApp."""
    return core_cls(transport=transport)


def attach_kpm(core) -> bool:
    url = os.getenv("SUBMGR_URL", "")
    if not url:
        logger.warning("SUBMGR_URL não definido: sem KPM, a xApp não propõe (toda proposta vem do KPM)")
        return False
    from src.greenran.common import RicKpmSource
    nodes = [n.strip() for n in os.getenv("KPM_NODES", "").split(",") if n.strip()]
    src = RicKpmSource(core, url, nodes, int(os.getenv("KPM_RAN_FUNCTION_ID", "2")),
                       period_ms=int(os.getenv("KPM_PERIOD_MS", "1000")))
    ok = src.attach() and src.subscribe() > 0
    logger.info("KPM: subscrição %s em %s nós", "ativa" if ok else "falhou", len(nodes))
    return ok


def run_kpm_loop(owner, core, period_s: float) -> None:
    """Enquanto ``owner.running``: propõe à RDL o que o núcleo decidir com o KPM observado."""
    attach_kpm(core)
    while owner.running:
        for proposal in core.decide(time.time()):
            owner.transport.send(proposal)
            logger.debug("proposta a partir do KPM: %s", proposal)
        time.sleep(period_s)
