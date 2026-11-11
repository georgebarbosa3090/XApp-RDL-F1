"""
Integração das xApps de referência com o núcleo H-RDL.

Desde 2026-11-10 restam quatro xApps de referência:
  1. qos-xslice (PRB_QUOTA) — inspirada em Yan et al.
  2. energy-saving (TX_POWER) — inspirada em Wadud et al.
  3. traffic-steering (HANDOVER) — inspirada no papel da o-ran-sc/ric-app-ts
  4. rogue-xapp (TX_POWER alternando 45/5 dBm) — teste do Safety Guard
Beamformer, ISAC Radar, Load Balancer e Bouncer saíram: propunham parâmetros fora do catálogo da
RDL e não enviavam propostas (relatório de adequação, seção 7.1).
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
for name in ("qos-xslice", "energy-saving", "traffic-steering", "rogue-xapp"):
    sys.path.insert(0, str(root_dir / "reference-xapps" / name))

from xslice_xapp import XSliceXApp  # noqa: E402
from energy_saving_xapp import EnergySavingXApp  # noqa: E402
from traffic_steering_xapp import TrafficSteeringXApp  # noqa: E402
from rogue_xapp import RogueXApp  # noqa: E402

from src.conflict_types import ConflictType, XAppAction  # noqa: E402
from src.core.inter_cell import default_handover_target  # noqa: E402
from src.core.perception import Perception  # noqa: E402
from src.core.reasoning import Reasoning  # noqa: E402
from src.core.refinement import Refinement  # noqa: E402
from src.infrastructure.memory_module import MemoryModule  # noqa: E402


def _action(p):
    return XAppAction(xapp_id=p["xapp_id"], node_id=p["node_id"], parameter=p["parameter"],
                      value=float(p["value"]), priority=int(p["priority"]))


def test_reference_xapps_proposal_parameters():
    assert XSliceXApp(http_port=19082, metrics_port=19083).generate_action_proposal(
        node_id="gnb_01", prb_quota=85.0)["parameter"] == "PRB_QUOTA"
    assert EnergySavingXApp(http_port=19084, metrics_port=19085).generate_action_proposal(
        node_id="gnb_01", tx_power=15.0)["parameter"] == "TX_POWER"
    assert TrafficSteeringXApp(http_port=19086, metrics_port=19087).generate_action_proposal(
        source_node="gnb_01", target_node="gnb_02", target_ue="UE-01")["parameter"] == "HANDOVER"
    assert RogueXApp(http_port=19092, metrics_port=19093).generate_action_proposal(node_id="gnb_01")["parameter"] == "TX_POWER"


def test_reference_xapps_contract_with_rdl_safety_guard():
    """O que a RDL aceita de cada xApp (default-deny) e o contrato do HANDOVER."""
    proposals = {
        "xslice": XSliceXApp(http_port=19182, metrics_port=19183).generate_action_proposal(node_id="gnb_01", prb_quota=85.0),
        "es": EnergySavingXApp(http_port=19184, metrics_port=19185).generate_action_proposal(node_id="gnb_01", tx_power=15.0),
        "ts": TrafficSteeringXApp(http_port=19186, metrics_port=19187).generate_action_proposal(
            source_node="gnb_01", target_node="gnb_02", target_ue="UE-01"),
    }
    guard = Refinement(MemoryModule())
    assert {name: guard.check_bounds(_action(p))[0] for name, p in proposals.items()} == {"xslice": True, "es": True, "ts": True}

    # HANDOVER: value é o índice da célula de destino, coerente com target_node
    assert proposals["ts"]["value"] == 2.0
    assert default_handover_target(_action(proposals["ts"])) == "gnb_02"

    # Rogue alterna 45 dBm (rejeitada) e 5 dBm (aceita)
    rogue = RogueXApp(http_port=19192, metrics_port=19193)
    results = [guard.check_bounds(_action(rogue.generate_action_proposal(node_id="gnb_01")))[0] for _ in range(2)]
    assert sorted(results) == [False, True]


def test_xslice_and_energy_saving_conflict_is_resolved():
    """Conflito direto xSlice × Energy Saving no mesmo alvo, resolvido por TVS e validado pelo Safety Guard."""
    memory = MemoryModule()
    xslice = _action(XSliceXApp(http_port=19282, metrics_port=19283).generate_action_proposal(node_id="gnb_01", prb_quota=85.0))
    energy = XAppAction(xapp_id="energy_saving", node_id="gnb_01", parameter="PRB_QUOTA", value=30.0, priority=65)
    conflicts = Perception().detect_action_group([xslice, energy])
    assert [c.conflict_type for c in conflicts] == [ConflictType.DIRECT]
    resolution = Reasoning(memory, config={}).resolve(conflicts[0])
    assert resolution.winning_actions == [xslice]
    assert Refinement(memory).validate(resolution, conflicts[0])[0]
