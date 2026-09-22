#!/usr/bin/env python3
"""
Real-Time Protocol Engine & Cognitive Knowledge Graph Demonstration Suite for 5G/O-RAN.

Models and executes:
  1. The 5-Stage UE Registration & Telemetry Lifecycle (PRACH -> RRC -> NAS -> PDU -> E2 = 45.8 ms)
  2. The 7-Phase End-to-End Simulation Demonstration Protocol:
     Phase 1: UE Access & 5-Step Registration
     Phase 2: E2SM-KPM Telemetry Ingestion (Radio KPIs, Buffers, Channel Quality)
     Phase 3: Concurrent xApp Proposals Recognition (xSlice, Energy-Saving, Traffic-Steering)
     Phase 4: Dynamic Knowledge Graph (KG) Activation & Conflict Detection
     Phase 5: RDL Cognitive Reasoning & Safety Guard Verification (TVS / EEVS / Safe-MAPPO)
     Phase 6: E2SM-RC Control Message Encoding & RMR Dispatch
     Phase 7: RAN MAC Scheduler Physical Application & Closed-Loop Telemetry Convergence (T1)
"""

from __future__ import annotations

import asyncio
import dataclasses
import enum
import json
import logging
import math
import os
import random
import time
from typing import Any, Dict, List, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [RealTimeProtocol] %(message)s",
)
logger = logging.getLogger("RealTimeProtocol")


# =============================================================================
# 1. 5 Canonical Registration Stages (3GPP / O-RAN)
# =============================================================================

class ProtocolStage(int, enum.Enum):
    STAGE_1_PRACH = 1
    STAGE_2_RRC = 2
    STAGE_3_NAS = 3
    STAGE_4_PDU = 4
    STAGE_5_E2_TELEMETRY = 5


@dataclasses.dataclass(frozen=True)
class StageMetadata:
    stage_id: int
    name: str
    layer: str
    source_entity: str
    target_entity: str
    nominal_delta_ms: float
    nominal_accumulated_ms: float
    sla_max_ms: float
    protocol_procedure: str


STAGE_DEFINITIONS: Dict[int, StageMetadata] = {
    1: StageMetadata(
        stage_id=1,
        name="PRACH Preamble Transmit & Random Access Response (RAR)",
        layer="PHY / MAC (gNB)",
        source_entity="UE",
        target_entity="gNB-DU",
        nominal_delta_ms=4.2,
        nominal_accumulated_ms=4.2,
        sla_max_ms=6.0,
        protocol_procedure="3GPP TS 38.321 / TS 38.211 PRACH Msg1-Msg2",
    ),
    2: StageMetadata(
        stage_id=2,
        name="RRC Setup Request, Setup & RRC Setup Complete",
        layer="3GPP RRC (gNB-DU/CU)",
        source_entity="UE",
        target_entity="gNB-CU",
        nominal_delta_ms=8.5,
        nominal_accumulated_ms=12.7,
        sla_max_ms=12.0,
        protocol_procedure="3GPP TS 38.331 RRCSetup / RRCSetupComplete",
    ),
    3: StageMetadata(
        stage_id=3,
        name="NAS Registration, Security Mode & 5G-AKA Authentication",
        layer="3GPP NAS (5GC AMF/AUSF)",
        source_entity="UE",
        target_entity="5GC_AMF",
        nominal_delta_ms=16.4,
        nominal_accumulated_ms=29.1,
        sla_max_ms=22.0,
        protocol_procedure="3GPP TS 24.501 NAS Registration & 5G-AKA Auth",
    ),
    4: StageMetadata(
        stage_id=4,
        name="PDU Session Establishment, QoS Flow Binding & NG-U Path",
        layer="3GPP SMF / UPF (5GC)",
        source_entity="5GC_AMF",
        target_entity="5GC_UPF",
        nominal_delta_ms=11.2,
        nominal_accumulated_ms=40.3,
        sla_max_ms=16.0,
        protocol_procedure="3GPP TS 29.502 / TS 38.413 PDU Session Resource Setup",
    ),
    5: StageMetadata(
        stage_id=5,
        name="E2 Node Subscription & KPM Telemetry Session Init",
        layer="O-RAN Near-RT RIC (E2term)",
        source_entity="E2term",
        target_entity="gNB-CU/DU",
        nominal_delta_ms=5.5,
        nominal_accumulated_ms=45.8,
        sla_max_ms=8.0,
        protocol_procedure="O-RAN WG3 E2AP RIC Subscription (E2SM-KPM / RC)",
    ),
}


@dataclasses.dataclass
class SignalingEvent:
    event_id: str
    timestamp_ns: int
    ue_id: int
    gnb_id: str
    stage: int
    stage_name: str
    layer: str
    source_entity: str
    target_entity: str
    delta_ms: float
    accumulated_ms: float
    sla_violation: bool
    protocol_procedure: str
    radio_kpis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class UESessionFSM:
    """Finite State Machine tracking an individual UE registration and telemetry lifecycle."""

    def __init__(self, ue_id: int, gnb_id: str = "gnb-n78-01", jitter_factor: float = 0.05):
        self.ue_id = ue_id
        self.gnb_id = gnb_id
        self.jitter_factor = jitter_factor
        self.current_stage = 0
        self.accumulated_time_ms = 0.0
        self.is_completed = False
        self.history: List[SignalingEvent] = []
        self.start_timestamp_ns = time.time_ns()

    def advance_stage(self, simulated_jitter: bool = True) -> Optional[SignalingEvent]:
        if self.is_completed or self.current_stage >= 5:
            return None

        self.current_stage += 1
        meta = STAGE_DEFINITIONS[self.current_stage]

        if simulated_jitter:
            jitter = (random.gauss(0.0, 1.0) * self.jitter_factor) * meta.nominal_delta_ms
            delta = max(0.5, meta.nominal_delta_ms + jitter)
        else:
            delta = meta.nominal_delta_ms

        self.accumulated_time_ms += delta
        sla_violation = delta > meta.sla_max_ms

        base_sinr = 16.0 + random.uniform(-1.0, 1.5)
        prb_usage = 75.0 + random.uniform(0.0, 6.0)
        throughput = max(50.0, 108.0 - (self.accumulated_time_ms * 0.1) + random.uniform(-2.0, 2.0))
        latency_e2e = 2.5 + (0.05 * self.current_stage) + random.uniform(0.0, 0.4)

        event = SignalingEvent(
            event_id=f"evt-{self.ue_id}-{self.current_stage}-{int(time.time()*1000)%100000}",
            timestamp_ns=time.time_ns(),
            ue_id=self.ue_id,
            gnb_id=self.gnb_id,
            stage=self.current_stage,
            stage_name=meta.name,
            layer=meta.layer,
            source_entity=meta.source_entity,
            target_entity=meta.target_entity,
            delta_ms=round(delta, 2),
            accumulated_ms=round(self.accumulated_time_ms, 2),
            sla_violation=sla_violation,
            protocol_procedure=meta.protocol_procedure,
            radio_kpis={
                "sinr_db": round(base_sinr, 2),
                "prb_usage_pct": round(prb_usage, 2),
                "throughput_mbps": round(throughput, 2),
                "latency_e2e_ms": round(latency_e2e, 2),
                "mcs_dl": 24 if base_sinr > 15.0 else 20,
                "rdl_decision_latency_ms": round(0.12 + random.uniform(0.0, 0.03), 3),
                "active_xapps": ["xApp-xSlice", "xApp-ES", "xApp-TS"],
            },
        )

        self.history.append(event)
        if self.current_stage == 5:
            self.is_completed = True

        return event


class RealTimeProtocolEngine:
    """Manages concurrent UE sessions, event broadcasting, and statistics."""

    def __init__(self, max_concurrent_ues: int = 10, event_interval_sec: float = 0.05):
        self.max_concurrent_ues = max_concurrent_ues
        self.event_interval_sec = event_interval_sec
        self.active_sessions: Dict[int, UESessionFSM] = {}
        self.completed_events: List[SignalingEvent] = []
        self.is_running = False
        self.next_ue_id = 1001

    def spawn_ue(self) -> UESessionFSM:
        ue_id = self.next_ue_id
        self.next_ue_id += 1
        session = UESessionFSM(ue_id=ue_id)
        self.active_sessions[ue_id] = session
        return session

    def step(self) -> List[SignalingEvent]:
        """Performs one simulation step advancing active sessions."""
        while len(self.active_sessions) < self.max_concurrent_ues:
            self.spawn_ue()

        new_events: List[SignalingEvent] = []
        finished_ue_ids: List[int] = []

        for ue_id, session in list(self.active_sessions.items()):
            event = session.advance_stage()
            if event:
                new_events.append(event)
                self.completed_events.append(event)
            if session.is_completed:
                finished_ue_ids.append(ue_id)

        for fid in finished_ue_ids:
            del self.active_sessions[fid]

        return new_events

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates aggregated performance and stage metrics."""
        stage_deltas: Dict[int, List[float]] = {i: [] for i in range(1, 6)}
        violations_count = 0

        for evt in self.completed_events:
            stage_deltas[evt.stage].append(evt.delta_ms)
            if evt.sla_violation:
                violations_count += 1

        stage_stats = {}
        for s_id, deltas in stage_deltas.items():
            meta = STAGE_DEFINITIONS[s_id]
            if deltas:
                mean_val = sum(deltas) / len(deltas)
                variance = sum((x - mean_val) ** 2 for x in deltas) / max(1, len(deltas) - 1)
                std_dev = math.sqrt(variance) if len(deltas) > 1 else 0.0
            else:
                mean_val = meta.nominal_delta_ms
                std_dev = 0.0

            stage_stats[s_id] = {
                "name": meta.name,
                "layer": meta.layer,
                "nominal_delta_ms": meta.nominal_delta_ms,
                "empirical_mean_delta_ms": round(mean_val, 2),
                "empirical_std_ms": round(std_dev, 2),
                "nominal_accumulated_ms": meta.nominal_accumulated_ms,
                "samples_count": len(deltas),
            }

        total_sessions = len(self.completed_events) // 5 if self.completed_events else 0
        return {
            "total_events": len(self.completed_events),
            "completed_sessions": total_sessions,
            "sla_violations_count": violations_count,
            "nominal_total_time_ms": 45.8,
            "stages": stage_stats,
        }

    def export_trace(self, output_path: str) -> None:
        """Exports JSON trace of all collected events."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        data = {
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_events": len(self.completed_events),
                "summary": self.get_summary_statistics(),
            },
            "events": [e.to_dict() for e in self.completed_events],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Protocol trace successfully exported to {output_path}")


# =============================================================================
# 2. 7-Phase Cognitive Demonstration Protocol
# =============================================================================

class DemonstrationPhase(int, enum.Enum):
    PHASE_1_UE_REGISTRATION = 1
    PHASE_2_KPM_TELEMETRY = 2
    PHASE_3_XAPP_PROPOSALS = 3
    PHASE_4_KNOWLEDGE_GRAPH = 4
    PHASE_5_RDL_REASONING = 5
    PHASE_6_RC_DISPATCH = 6
    PHASE_7_RAN_APPLICATION = 7


@dataclasses.dataclass(frozen=True)
class PhaseMetadata:
    phase_id: int
    name: str
    short_name: str
    subsystem: str
    description: str
    nominal_duration_ms: float
    color: str


PHASE_DEFINITIONS: Dict[int, PhaseMetadata] = {
    1: PhaseMetadata(
        phase_id=1,
        name="Registro e Acesso de UEs (5 Etapas Canônicas)",
        short_name="1. Acesso & Registro UEs",
        subsystem="PHY / RRC / 5GC / E2term",
        description="Execução da sequência PRACH (4.2ms) -> RRC Setup (8.5ms) -> 5GC NAS/AKA (16.4ms) -> PDU Session (11.2ms) -> E2 Sub (5.5ms).",
        nominal_duration_ms=45.8,
        color="#38bdf8",
    ),
    2: PhaseMetadata(
        phase_id=2,
        name="Ingestão de Telemetria E2SM-KPM",
        short_name="2. Telemetria KPM",
        subsystem="O-RAN Near-RT RIC (E2term & Perception Agent)",
        description="Recepção de métricas de rádio 3GPP 28.552 (SINR, PRB, MCS, HOL Delay, Throughput) a cada 200 ms.",
        nominal_duration_ms=2.0,
        color="#818cf8",
    ),
    3: PhaseMetadata(
        phase_id=3,
        name="Reconhecimento de Propostas de xApps",
        short_name="3. Propostas xApps",
        subsystem="Near-RT RIC (xSlice, Energy-Saving, Traffic-Steering)",
        description="Recepção assíncrona de intenções conflitantes de micro-aplicações em janela de agregação de 200 ms.",
        nominal_duration_ms=0.5,
        color="#fbbf24",
    ),
    4: PhaseMetadata(
        phase_id=4,
        name="Ativação do Grafo de Conhecimento e Detecção de Conflitos",
        short_name="4. Grafo de Conhecimento",
        subsystem="xApp-RDL Context Engine & GraphSAGE GNN",
        description="Mapeamento ontológico de nós (UEs, Slices, gNBs, Parâmetros) e arestas (CONTROLS, IMPACTS, COLLIDES_WITH).",
        nominal_duration_ms=0.62,
        color="#c084fc",
    ),
    5: PhaseMetadata(
        phase_id=5,
        name="Raciocínio Cognitivo da RDL & Safety Guard",
        short_name="5. Raciocínio & Safety",
        subsystem="xApp-RDL Reasoning Engine & Boundary Clipping",
        description="Arbitragem por utilidade TVS/EEVS ou inferência Safe-MAPPO com Action Masking e garantia de UnsafeApplied = 0.",
        nominal_duration_ms=0.12,
        color="#34d399",
    ),
    6: PhaseMetadata(
        phase_id=6,
        name="Codificação ASN.1 APER e Despacho E2SM-RC",
        short_name="6. Despacho E2SM-RC",
        subsystem="RCMapper, RMR Router & SCTP:36422",
        description="Montagem da PDU E2SM-RC Format 1 Header / Format 2 Message e envio do comando RICcontrolRequest (RMR 12040).",
        nominal_duration_ms=0.83,
        color="#06b6d4",
    ),
    7: PhaseMetadata(
        phase_id=7,
        name="Aplicação Física na RAN e Fechamento da Malha (T1)",
        short_name="7. Aplicação na RAN",
        subsystem="gNodeB MAC Scheduler (NrMacSchedulerOfdmaPF) & 5G-LENA",
        description="Reconfiguração atômica do escalonador MAC, emissão do ACK (RMR 12041) e estabilização de QoS pós-intervenção.",
        nominal_duration_ms=2.32,
        color="#10b981",
    ),
}


class ScenarioType(str, enum.Enum):
    S1_DIRECT_PRB = "S1_DIRECT_PRB"
    S2_ENERGY_VS_QOS = "S2_ENERGY_VS_QOS"
    S5_PING_PONG = "S5_PING_PONG"
    S7_E2_TIMEOUT = "S7_E2_TIMEOUT"


@dataclasses.dataclass
class DemonstrationState:
    current_phase: int
    scenario: str
    active_ues_count: int
    cycle_index: int
    is_conflict_active: bool
    conflict_type: str
    proposed_actions: Dict[str, Any]
    arbitrated_decision: Dict[str, Any]
    safety_guard_status: str
    decision_latency_ms: float
    total_loop_latency_ms: float
    radio_kpis: Dict[str, float]
    knowledge_graph: Dict[str, Any]
    asn1_payload_preview: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class CognitiveDemonstrationProtocol:
    """Manages the full 7-phase step-by-step cognitive demonstration protocol."""

    def __init__(self, initial_scenario: ScenarioType = ScenarioType.S1_DIRECT_PRB):
        self.current_phase = 1
        self.scenario = initial_scenario.value
        self.cycle_index = 1
        self.active_ues_count = 5
        self.history: List[DemonstrationState] = []
        self.is_conflict_active = True

    def set_scenario(self, scenario_name: str) -> None:
        self.scenario = scenario_name
        self.current_phase = 1
        self.is_conflict_active = True
        logger.info(f"Scenario switched to: {scenario_name}")

    def advance_phase(self) -> DemonstrationState:
        """Advances protocol to the next phase (1 -> 2 -> ... -> 7 -> 1)."""
        nodes = [
            {"id": "gnb_01", "label": "gNB Macro 01 (n78)", "group": "gnb", "x": 0, "y": 0},
            {"id": "slice_urllc", "label": "Slice URLLC (SST=1)", "group": "slice", "x": -150, "y": -100},
            {"id": "slice_embb", "label": "Slice eMBB (SST=2)", "group": "slice", "x": 150, "y": -100},
            {"id": "ue_1001", "label": "UE #1001 (URLLC)", "group": "ue", "x": -220, "y": -180},
            {"id": "ue_1002", "label": "UE #1002 (eMBB)", "group": "ue", "x": 220, "y": -180},
            {"id": "xapp_xslice", "label": "xApp-xSlice (QoS)", "group": "xapp", "x": -180, "y": 120},
            {"id": "xapp_es", "label": "xApp-EnergySaving", "group": "xapp", "x": 0, "y": 150},
            {"id": "xapp_ts", "label": "xApp-TrafficSteering", "group": "xapp", "x": 180, "y": 120},
            {"id": "param_prb", "label": "PRB_Quota_S1", "group": "param", "x": -80, "y": 40},
            {"id": "param_ptx", "label": "Tx_Power_Carrier", "group": "param", "x": 80, "y": 40},
            {"id": "kpi_thr", "label": "Throughput (Mbps)", "group": "kpi", "x": -120, "y": -40},
            {"id": "kpi_lat", "label": "Latency URLLC (ms)", "group": "kpi", "x": 120, "y": -40},
        ]

        edges = [
            {"from": "ue_1001", "to": "slice_urllc", "label": "ASSOCIATED_WITH", "color": "#38bdf8"},
            {"from": "ue_1002", "to": "slice_embb", "label": "ASSOCIATED_WITH", "color": "#818cf8"},
            {"from": "slice_urllc", "to": "gnb_01", "label": "HOSTED_ON", "color": "#94a3b8"},
            {"from": "slice_embb", "to": "gnb_01", "label": "HOSTED_ON", "color": "#94a3b8"},
            {"from": "xapp_xslice", "to": "param_prb", "label": "CONTROLS", "color": "#fbbf24"},
            {"from": "xapp_es", "to": "param_ptx", "label": "CONTROLS", "color": "#fbbf24"},
            {"from": "param_prb", "to": "kpi_thr", "label": "IMPACTS", "color": "#34d399"},
            {"from": "param_ptx", "to": "kpi_lat", "label": "IMPACTS", "color": "#34d399"},
        ]

        if self.current_phase in [3, 4]:
            if self.scenario == ScenarioType.S1_DIRECT_PRB.value:
                edges.append({"from": "xapp_xslice", "to": "xapp_es", "label": "COLLIDES_WITH (Direct PRB)", "color": "#ef4444", "dashes": True})
            elif self.scenario == ScenarioType.S2_ENERGY_VS_QOS.value:
                edges.append({"from": "param_ptx", "to": "slice_urllc", "label": "VIOLATES_SLA (Low SINR)", "color": "#ef4444", "dashes": True})
            elif self.scenario == ScenarioType.S5_PING_PONG.value:
                edges.append({"from": "xapp_ts", "to": "xapp_xslice", "label": "PING_PONG_REVERSAL", "color": "#ef4444", "dashes": True})

        if self.scenario == ScenarioType.S1_DIRECT_PRB.value:
            proposed = {
                "xApp-xSlice": {"action": "SET_PRB_QUOTA", "target_slice": "URLLC", "requested_value": "75.0%"},
                "xApp-EnergySaving": {"action": "REDUCE_PRB_QUOTA", "target_slice": "ALL", "requested_value": "40.0%"},
            }
            arbitrated = {
                "engine": "H-RDL TVS / Utility Vector",
                "resolved_parameter": "PRB_QUOTA_URLLC",
                "final_value": "60.0%",
                "rationale": "Priorização estrita de SLA URLLC (<= 5 ms) com preservação de cota viável para eMBB.",
                "cooling_window_applied": True,
            }
        elif self.scenario == ScenarioType.S2_ENERGY_VS_QOS.value:
            proposed = {
                "xApp-EnergySaving": {"action": "SET_TX_POWER", "requested_value": "30.0 dBm (Delta -13dBm)"},
                "xApp-xSlice": {"action": "GUARANTEE_SINR", "required_min_sinr": "15.0 dB"},
            }
            arbitrated = {
                "engine": "H-RDL EEVS / Energy-QoS Tradeoff",
                "resolved_parameter": "TX_POWER",
                "final_value": "37.5 dBm (Delta -5.5dBm)",
                "rationale": "Economia de energia aprovada dentro do envelope de Shannon sem violar SINR de borda.",
                "cooling_window_applied": True,
            }
        else:
            proposed = {
                "xApp-TrafficSteering": {"action": "HANDOVER_UE", "target_cell": "gnb_02"},
                "xApp-xSlice": {"action": "RETAIN_UE_LOCAL", "target_slice": "URLLC"},
            }
            arbitrated = {
                "engine": "H-RDL Anti-Ping-Pong / Memory Lock",
                "resolved_parameter": "HANDOVER_DECISION",
                "final_value": "RETAIN_HOLD (Cooldown 5.0s)",
                "rationale": "Supressão de reversão rápida de handover (Ping-Pong Rate: 0 ev/min).",
                "cooling_window_applied": True,
            }

        if self.current_phase in [1, 2, 3]:
            throughput = 95.0 + random.uniform(-2.0, 2.0)
            latency = 14.5 + random.uniform(-0.5, 1.0)
            prb_usage = 88.0 + random.uniform(-2.0, 3.0)
            sinr = 14.8 + random.uniform(-0.5, 0.5)
        else:
            throughput = 106.8 + random.uniform(-1.0, 1.5)
            latency = 2.8 + random.uniform(-0.2, 0.2)
            prb_usage = 78.5 + random.uniform(-1.5, 1.5)
            sinr = 16.2 + random.uniform(-0.3, 0.4)

        asn1_payload = {
            "protocolIEs": [
                {"id": "id-RICrequestID", "criticality": "reject", "value": {"ricRequestorID": 1, "ricInstanceID": 1001}},
                {"id": "id-RANfunctionID", "criticality": "reject", "value": 3},
                {"id": "id-RICcontrolHeader", "criticality": "reject", "value": "E2SM-RC-ControlHeader-Format-1 (RIC-Style-Type: 1)"},
                {"id": "id-RICcontrolMessage", "criticality": "reject", "value": {
                    "format": "E2SM-RC-ControlMessage-Format-2",
                    "targetParam": arbitrated["resolved_parameter"],
                    "allocatedValue": arbitrated["final_value"],
                    "safetyGuardStatus": "VERIFIED_BOUNDARY_CLIP_OK"
                }},
                {"id": "id-RICcontrolAckRequest", "criticality": "reject", "value": "ack"}
            ]
        }

        state = DemonstrationState(
            current_phase=self.current_phase,
            scenario=self.scenario,
            active_ues_count=self.active_ues_count,
            cycle_index=self.cycle_index,
            is_conflict_active=self.current_phase in [3, 4],
            conflict_type=f"Conflito Multi-xApp ({self.scenario})",
            proposed_actions=proposed,
            arbitrated_decision=arbitrated,
            safety_guard_status="PASSED (UnsafeApplied = 0)",
            decision_latency_ms=0.12 if "H-RDL" in arbitrated["engine"] else 1.84,
            total_loop_latency_ms=200.0,
            radio_kpis={
                "throughput_mbps": round(throughput, 2),
                "latency_e2e_ms": round(latency, 2),
                "prb_usage_pct": round(prb_usage, 2),
                "sinr_db": round(sinr, 2),
                "action_churn": 0.05 if self.current_phase >= 5 else 0.85,
            },
            knowledge_graph={"nodes": nodes, "edges": edges},
            asn1_payload_preview=asn1_payload,
        )

        self.history.append(state)

        if self.current_phase < 7:
            self.current_phase += 1
        else:
            self.current_phase = 1
            self.cycle_index += 1

        return state


if __name__ == "__main__":
    protocol = CognitiveDemonstrationProtocol()
    logger.info("Running 7-phase step-by-step demonstration protocol...")
    for step_num in range(1, 8):
        state = protocol.advance_phase()
        meta = PHASE_DEFINITIONS[state.current_phase]
        print(f"Step {step_num} -> Phase {state.current_phase} [{meta.short_name}]: QoS Thr={state.radio_kpis['throughput_mbps']} Mbps, Lat={state.radio_kpis['latency_e2e_ms']} ms")
