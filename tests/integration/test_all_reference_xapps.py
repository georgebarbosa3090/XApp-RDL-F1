"""
Suíte de Testes de Integração para as 8 Reference xApps e o H-RDL
Testa:
  1. qos-xslice (PRB_QUOTA, SCHEDULER_WEIGHT)
  2. energy-saving (TX_POWER, SLEEP_MODE)
  3. traffic-steering (HANDOVER, CIO_OFFSET)
  4. beamformer (VERTICAL_DOWNTILT, BEAM_WEIGHTS)
  5. isac-radar (SENSING_RATIO, RADAR_PERIOD)
  6. rogue-xapp (TX_POWER Flapping, PRB_QUOTA Inseguro)
  7. load-balancer (LOAD_THRESHOLD, CARRIER_PRB_ALLOCATION)
  8. bouncer (PING_INTERVAL, E2_LOOPBACK_FLAG)
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

from src.agents.perception_agent import PerceptionAgent
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.refinement_agent import RefinementAgent
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
    """Valida que PerceptionAgent detecta conflitos entre xApps da Fase 2 e O-RAN SC e Reasoning resolve."""
    perception = PerceptionAgent()
    memory = MemoryModule()
    reasoning = ReasoningAgent(memory, config={})
    refinement = RefinementAgent(memory)

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
    assert is_valid

def test_discrete_event_ran_simulator_physics_and_metrics():
    """Valida o funcionamento físico do DiscreteEventRANSimulator sem dados sintéticos."""
    sim = DiscreteEventRANSimulator(seed=42)
    sim.add_gnb("gnb_01", x=0.0, y=0.0, tx_power_dbm=43.0)
    sim.add_gnb("gnb_02", x=80.0, y=0.0, tx_power_dbm=30.0)

    # Adiciona 5 UEs em diferentes distâncias
    sim.add_ue("ue_01", "URLLC", x=15.0, y=10.0, gnb_id="gnb_01")
    sim.add_ue("ue_02", "eMBB", x=30.0, y=20.0, gnb_id="gnb_01")
    sim.add_ue("ue_03", "SENSING", x=40.0, y=0.0, gnb_id="gnb_01")
    sim.add_ue("ue_04", "URLLC", x=70.0, y=5.0, gnb_id="gnb_02")
    sim.add_ue("ue_05", "eMBB", x=75.0, y=15.0, gnb_id="gnb_02")

    # Roda 50 slots de 10ms (500 ms de tráfego real)
    for _ in range(50):
        sim.step_slot(0.010)

    metrics = sim.get_kpm_metrics()
    assert metrics["throughput_mbps"] > 0.0
    assert metrics["urllc_latency_mean_ms"] > 0.0
    assert 0.0 <= metrics["jain_fairness"] <= 1.0

    # Aplica controle E2SM-RC real e verifica mudança física
    sim.apply_rc_control({"node_id": "gnb_01", "parameter": "TX_POWER", "value": 35.0})
    assert sim.gnbs["gnb_01"].tx_power_dbm == 35.0
