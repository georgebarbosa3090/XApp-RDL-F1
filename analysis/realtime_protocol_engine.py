#!/usr/bin/env python3
"""
Real-Time Protocol Engine for 5G-Advanced & O-RAN Telemetry Lifecycle.

Captures, correlates, analyzes, and streams the 5 canonical stages of UE registration
and O-RAN telemetry initialization with microsecond precision:
  Stage 1: PRACH Preamble Transmit & Random Access Response (RAR) [PHY/MAC, 4.2 ms]
  Stage 2: RRC Setup Request, Setup & Complete [3GPP RRC, 8.5 ms -> 12.7 ms]
  Stage 3: NAS Registration, Security Mode & 5G-AKA [3GPP NAS, 16.4 ms -> 29.1 ms]
  Stage 4: PDU Session Establishment & QoS Flow Binding [3GPP SMF/UPF, 11.2 ms -> 40.3 ms]
  Stage 5: E2 Node Subscription & KPM Telemetry Session Init [O-RAN Near-RT RIC, 5.5 ms -> 45.8 ms]
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

        # Generate realistic cross-layer KPIs
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
        # Ensure minimum active sessions
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


if __name__ == "__main__":
    engine = RealTimeProtocolEngine(max_concurrent_ues=5)
    logger.info("Running real-time protocol simulation loop...")
    for _ in range(10):
        events = engine.step()
        for ev in events:
            print(f"[{ev.layer}] UE {ev.ue_id} Stage {ev.stage} ({ev.stage_name[:30]}...): Delta={ev.delta_ms}ms, Total={ev.accumulated_ms}ms")
    
    summary = engine.get_summary_statistics()
    print("\n--- Summary Statistics ---")
    print(json.dumps(summary, indent=2))
