"""
Suíte de Testes de Integração para as 8 Reference xApps e o H-RDL
Testa:
  1. qos-xslice (PRB_QUOTA, SCHEDULER_WEIGHT)
  2. energy-saving (TX_POWER, SLEEP_MODE)
  3. traffic-steering (HANDOVER)
  4. beamformer (VERTICAL_DOWNTILT, BEAM_WEIGHTS)
  5. isac-radar (SENSING_RATIO, RADAR_PERIOD)
  6. rogue-xapp (TX_POWER alternando 45/5 dBm)
  7. load-balancer (LOAD_THRESHOLD)
  8. bouncer (PING_INTERVAL)
"""

import pytest
import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "reference-xapps" / "qos-xslice"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "energy-saving"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "traffic-steering"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "beamformer"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "isac-radar"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "rogue-xapp"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "load-balancer"))
sys.path.insert(0, str(root_dir / "reference-xapps" / "bouncer"))

from xslice_xapp import XSliceXApp
from energy_saving_xapp import EnergySavingXApp
from traffic_steering_xapp import TrafficSteeringXApp
from beamformer_xapp import BeamformerXApp
from isac_radar_xapp import ISACRadarXApp
from rogue_xapp import RogueXApp
from load_balancer_xapp import LoadBalancerXApp
from bouncer_xapp import BouncerXApp

from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.infrastructure.memory_module import MemoryModule
from src.conflict_types import XAppAction, ConflictType
from src.simulation.discrete_event_ran_simulator import DiscreteEventRANSimulator

def test_all_8_xapps_proposal_generation():
    """Valida a geração de propostas conforme o modelo de cada uma das 8 xApps."""
    xslice = XSliceXApp(http_port=19082, metrics_port=19083)
    es = EnergySavingXApp(http_port=19084, metrics_port=19085)
    ts = TrafficSteeringXApp(http_port=19086, metrics_port=19087)
    bf = BeamformerXApp(http_port=19088, metrics_port=19089)
    isac = ISACRadarXApp(http_port=19090, metrics_port=19091)
    rogue = RogueXApp(http_port=19092, metrics_port=19093)
    lb = LoadBalancerXApp(http_port=19094, metrics_port=19095)
    bouncer = BouncerXApp(http_port=19096, metrics_port=19097)

    p1 = xslice.generate_action_proposal(node_id="gnb_01", prb_quota=85.0)
    p2 = es.generate_action_proposal(node_id="gnb_01", tx_power=15.0)
    p3 = ts.generate_action_proposal(source_node="gnb_01", target_node="gnb_02", target_ue="UE-01")
    p4 = bf.generate_action_proposal(node_id="gnb_01", downtilt=7.5)
    p5 = isac.generate_action_proposal(node_id="gnb_01", sensing_ratio=0.35)
    p6 = rogue.generate_action_proposal(node_id="gnb_01")
    p7 = lb.generate_action_proposal(node_id="gnb_01", threshold=0.80)
    p8 = bouncer.generate_action_proposal(node_id="gnb_01", interval_ms=100.0)

    assert p1["parameter"] == "PRB_QUOTA"
    assert p2["parameter"] == "TX_POWER"
    assert p3["parameter"] == "HANDOVER"
    assert p4["parameter"] == "VERTICAL_DOWNTILT"
    assert p5["parameter"] == "SENSING_RATIO"
    assert p6["parameter"] == "TX_POWER"
    assert p7["parameter"] == "LOAD_THRESHOLD"
    assert p8["parameter"] == "PING_INTERVAL"

def test_perception_and_resolution_with_new_parameters():
    """Valida que Perception detecta conflitos entre xApps da Fase 2 e O-RAN SC e Reasoning resolve."""
    perception = Perception()
    memory = MemoryModule()
    reasoning = Reasoning(memory, config={})
    refinement = Refinement(memory)

    # Conflito Indireto: Beamformer (DOWNTILT -> afeta L1M.DL-sinr e DRB.UEThpDl) vs Energy Saving (TX_POWER -> afeta L1M.DL-sinr)
    actions = [
        XAppAction(xapp_id="beamformer_mimo_5ga", node_id="gnb_01", parameter="VERTICAL_DOWNTILT", value=7.0, priority=75),
        XAppAction(xapp_id="energy_saving_orange", node_id="gnb_01", parameter="TX_POWER", value=12.0, priority=65)
    ]

    conflicts = perception.register_action_group(actions)
    assert len(conflicts) >= 1
    assert conflicts[0].conflict_type == ConflictType.INDIRECT

    resolution = reasoning.resolve(conflicts[0])
    assert resolution is not None
    is_valid, level, reason = refinement.validate(resolution, conflicts[0])
    assert not is_valid
    assert "unsupported" in reason.lower()

def test_retired_discrete_event_simulator_is_disabled():
    """Ensures the former local simulator cannot be run as experimental evidence."""
    with pytest.raises(RuntimeError, match="disabled.*ns-3 and 5G-LENA"):
        DiscreteEventRANSimulator(seed=42)


def test_reference_xapps_contract_with_rdl_safety_guard():
    """Adequação (2026-11-10): que propostas das xApps de referência a RDL aceita (default-deny).

    As xApps derivadas de trabalhos (xSlice, Energy Saving, Traffic Steering) usam parâmetros do
    catálogo da RDL; as escritas para este projeto (Beamformer, ISAC, Load Balancer, Bouncer)
    propõem parâmetros fora do catálogo e são rejeitadas antes da arbitragem.
    """
    from src.core.inter_cell import default_handover_target

    xapps = {
        "xslice": XSliceXApp(http_port=19182, metrics_port=19183).generate_action_proposal(node_id="gnb_01", prb_quota=85.0),
        "es": EnergySavingXApp(http_port=19184, metrics_port=19185).generate_action_proposal(node_id="gnb_01", tx_power=15.0),
        "ts": TrafficSteeringXApp(http_port=19186, metrics_port=19187).generate_action_proposal(
            source_node="gnb_01", target_node="gnb_02", target_ue="UE-01"),
        "bf": BeamformerXApp(http_port=19188, metrics_port=19189).generate_action_proposal(node_id="gnb_01", downtilt=7.5),
        "isac": ISACRadarXApp(http_port=19190, metrics_port=19191).generate_action_proposal(node_id="gnb_01", sensing_ratio=0.35),
        "lb": LoadBalancerXApp(http_port=19194, metrics_port=19195).generate_action_proposal(node_id="gnb_01", threshold=0.80),
        "bouncer": BouncerXApp(http_port=19196, metrics_port=19197).generate_action_proposal(node_id="gnb_01", interval_ms=100.0),
    }
    guard = Refinement(MemoryModule())
    accepted = {}
    actions = {}
    for name, p in xapps.items():
        action = XAppAction(xapp_id=p["xapp_id"], node_id=p["node_id"], parameter=p["parameter"],
                            value=float(p["value"]), priority=int(p["priority"]))
        actions[name] = action
        accepted[name] = guard.check_bounds(action)[0]
    assert accepted == {"xslice": True, "es": True, "ts": True,
                        "bf": False, "isac": False, "lb": False, "bouncer": False}

    # HANDOVER: value é o índice da célula de destino, coerente com target_node
    assert xapps["ts"]["value"] == 2.0
    assert default_handover_target(actions["ts"]) == "gnb_02"

    # Rogue alterna 45 dBm (rejeitada) e 5 dBm (aceita)
    rogue = RogueXApp(http_port=19192, metrics_port=19193)
    results = []
    for _ in range(2):
        p = rogue.generate_action_proposal(node_id="gnb_01")
        results.append(guard.check_bounds(XAppAction(xapp_id=p["xapp_id"], node_id="gnb_01", parameter=p["parameter"],
                                                     value=float(p["value"]), priority=int(p["priority"])))[0])
    assert sorted(results) == [False, True]
