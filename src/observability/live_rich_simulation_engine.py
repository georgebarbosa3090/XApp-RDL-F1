"""
Motor de Simulação Rica em Malha Fechada com 6 Blocos O-RAN.
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

Integra os 6 blocos fundamentais de controle autônomo cognitivo:
  Bloco 1: Registro e Estado UE nos gNBs (5G-NR RAN Layer)
  Bloco 2: Barramento de Sinalização e Mensagens de Protocolo (E2AP / E2SM / RMR)
  Bloco 3: Módulo de Percepção & Detecção de Anomalias (Perception Engine)
  Bloco 4: Grafo de Conhecimento Cognitivo (Knowledge Graph / Reasoning)
  Bloco 5: Módulo de Refinamento & Segurança (H-RDL Safety Guards & Arbitration)
  Bloco 6: Ação de Controle para RAN e Malha Fechada (E2SM-RC Dispatcher & Loopback)
"""

import time
import math
import random
import uuid
from typing import Dict, List, Any, Optional

from src.conflict_types import (
    XAppAction,
    ConflictEvent,
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
    KPMReport,
)
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.infrastructure.sdl_repository import SdlRepository


class RichSimulationEngine:
    """
    Motor de simulação e geração de evidências ao vivo dos 6 blocos cognitivos O-RAN.
    Alimenta dashboards web e TUI com dados coerentes com 3GPP Rel-18 e O-RAN WG3/WG2.
    """

    def __init__(self):
        self.tick_count = 0
        self.sim_time_s = 0.0
        self.is_paused = False
        self.time_step = 1.0  # 1 segundo de simulação por tick
        
        # Inicializa subsistemas reais do core RDL
        self.sdl = SdlRepository()
        self.perception = Perception()
        self.reasoning = Reasoning(memory=self.sdl)
        self.refinement = Refinement(memory=self.sdl, strict_capabilities=False)

        # Estado do Bloco 1: Registro UEs e gNBs
        self.gnbs = {
            "gnb_001": {
                "cell_id": "cell_01",
                "freq_ghz": 3.5,
                "bandwidth_mhz": 100,
                "tx_power_dbm": 43.0,
                "prb_total": 273,
                "prb_used": 140,
                "active_ues": 8,
            },
            "gnb_002": {
                "cell_id": "cell_02",
                "freq_ghz": 3.5,
                "bandwidth_mhz": 100,
                "tx_power_dbm": 40.0,
                "prb_total": 273,
                "prb_used": 95,
                "active_ues": 6,
            },
        }

        self.ues = self._init_ues(14)
        
        # Estado do Bloco 2: Mensagens de Protocolo
        self.protocol_trace_buffer: List[Dict[str, Any]] = []

        # Estado do Bloco 3: Percepção e Conflitos
        self.latest_kpi_metrics: Dict[str, Any] = {}
        self.active_conflicts: List[ConflictEvent] = []

        # Estado do Bloco 4: Grafo de Conhecimento
        self.knowledge_graph: Dict[str, Any] = {"nodes": [], "edges": []}

        # Estado do Bloco 5: Refinamento
        self.latest_refinement: Dict[str, Any] = {}

        # Estado do Bloco 6: Ações de Controle e Malha Fechada
        self.control_actions_history: List[Dict[str, Any]] = []
        self.closed_loop_latency_ms: float = 3.8
        
        # Injeção manual de conflitos
        self.forced_scenario: Optional[str] = "tvs_conflict"

    def _init_ues(self, num_ues: int) -> List[Dict[str, Any]]:
        ues = []
        slices = [
            ("URLLC_01", 1, "SST_1_SD_000001", 5.0),   # max delay 5ms
            ("eMBB_01", 9, "SST_1_SD_000002", 50.0),   # max delay 50ms
            ("mMTC_01", 5, "SST_1_SD_000003", 200.0),  # max delay 200ms
        ]
        for i in range(1, num_ues + 1):
            slice_name, five_qi, s_nssai, max_delay = random.choice(slices)
            target_gnb = "gnb_001" if (i % 2 != 0) else "gnb_002"
            ues.append({
                "ue_id": f"UE_{i:03d}",
                "imsi": f"00101{i:010d}",
                "rnti": f"0x{4100 + i:04X}",
                "gnb_id": target_gnb,
                "cell_id": self.gnbs[target_gnb]["cell_id"],
                "rrc_state": "RRC_CONNECTED",
                "slice": slice_name,
                "5qi": five_qi,
                "s_nssai": s_nssai,
                "sinr_db": round(random.uniform(14.0, 26.0), 1),
                "rsrp_dbm": round(random.uniform(-98.0, -78.0), 1),
                "cqi": random.randint(9, 15),
                "thp_dl_mbps": round(random.uniform(15.0, 85.0), 2),
                "delay_ms": round(random.uniform(1.8, 4.2), 2),
                "sla_delay_ms": max_delay,
                "sla_violation": False,
            })
        return ues

    def trigger_scenario(self, scenario_name: str):
        """Injeta um cenário específico no próximo tick."""
        self.forced_scenario = scenario_name

    def step(self) -> Dict[str, Any]:
        """Avança a simulação em 1 passo de tempo discreto e sincroniza os 6 blocos."""
        if self.is_paused:
            return self.get_full_state()

        self.tick_count += 1
        self.sim_time_s = round(self.tick_count * self.time_step, 1)
        t_now = time.time()

        # =====================================================================
        # 1. BLOCO 1: Registro e Estado UE nos gNBs (5G-NR RAN Layer)
        # =====================================================================
        for ue in self.ues:
            # Flutuação estocástica de canal rádio (Rayleigh / Shadowing)
            ue["sinr_db"] = round(max(5.0, min(32.0, ue["sinr_db"] + random.uniform(-1.2, 1.2))), 1)
            ue["rsrp_dbm"] = round(max(-115.0, min(-65.0, ue["rsrp_dbm"] + random.uniform(-1.0, 1.0))), 1)
            ue["cqi"] = max(1, min(15, int(ue["sinr_db"] / 2.0)))
            
            # Dinâmica de Throughput baseada em Shannon e PRBs
            spectral_eff = math.log2(1.0 + 10.0 ** (ue["sinr_db"] / 10.0))
            ue["thp_dl_mbps"] = round(max(2.0, min(150.0, spectral_eff * 8.5 + random.uniform(-3.0, 3.0))), 2)

            # Dinâmica de Atraso e Verificação de SLA
            base_delay = 2.0 if ue["slice"] == "URLLC_01" else 15.0
            jitter = random.uniform(-0.5, 1.5)
            if self.forced_scenario == "urllc_surge" and ue["slice"] == "URLLC_01":
                jitter += 7.5  # Gera surto de atraso violando SLA
            ue["delay_ms"] = round(max(0.8, base_delay + jitter), 2)
            ue["sla_violation"] = ue["delay_ms"] > ue["sla_delay_ms"]

        # Atualização de PRB nos gNBs
        for gnb_id, gnb in self.gnbs.items():
            active_count = sum(1 for u in self.ues if u["gnb_id"] == gnb_id)
            gnb["active_ues"] = active_count
            gnb["prb_used"] = min(gnb["prb_total"], int(active_count * random.uniform(12.0, 18.0)))

        # =====================================================================
        # 2. BLOCO 2: Sinalizações e Mensagens de Protocolo (E2AP / E2SM / RMR)
        # =====================================================================
        # Gera E2SM-KPM Indication Report
        kpm_pdu = self._generate_e2sm_kpm_pdu("gnb_001")
        self.protocol_trace_buffer.insert(0, kpm_pdu)

        # Gera E2AP RMR Trace
        rmr_trace = {
            "timestamp": t_now,
            "sim_time": self.sim_time_s,
            "type": "RMR_MSG_RX",
            "mtype": 12050,
            "mtype_name": "RIC_INDICATION",
            "sub_id": 1001,
            "source": "gnb_001",
            "target": "xapp_rdl",
            "payload_len": len(kpm_pdu["raw_hex"]) // 2,
            "asn1_summary": f"E2AP-PDU [initiatingMessage] -> E2SM-KPM v2.0 Indication (Node: gnb_001, PRB_Used={self.gnbs['gnb_001']['prb_used']}/273)",
        }
        self.protocol_trace_buffer.insert(0, rmr_trace)
        
        # Mantém histórico limitado
        if len(self.protocol_trace_buffer) > 25:
            self.protocol_trace_buffer = self.protocol_trace_buffer[:25]

        # =====================================================================
        # 3. BLOCO 3: Módulo de Percepção (Perception Engine)
        # =====================================================================
        # Ingestão de KPM no Perception real
        kpm_report = KPMReport(
            node_id="gnb_001",
            ue_id="UE_001",
            drb_thp_dl=float(self.ues[0]["thp_dl_mbps"]),
            drb_thp_ul=10.5,
            drb_delay_dl=float(self.ues[0]["delay_ms"]),
            prb_used_dl=self.gnbs["gnb_001"]["prb_used"],
            timestamp=t_now,
        )
        self.perception.update_kpm_report(kpm_report)

        # Síntese das propostas das xApps de negócio concorrentes
        proposed_actions: List[XAppAction] = []

        if self.forced_scenario == "tvs_conflict":
            # Conflito DIRETO: xApp-QoS quer alta potência; xApp-Energy quer cortar potência
            act_qos = XAppAction(
                xapp_id="xapp_qos_guarantor",
                node_id="gnb_001",
                parameter="TX_POWER",
                value=43.0,
                priority=85,
            )
            act_energy = XAppAction(
                xapp_id="xapp_energy_saver",
                node_id="gnb_001",
                parameter="TX_POWER",
                value=33.0,
                priority=60,
            )
            proposed_actions = [act_qos, act_energy]

        elif self.forced_scenario == "eevs_conflict":
            # Conflito INDIRETO: xApp-TrafficSteering altera Handover, xApp-Slicing altera PRB_QUOTA
            act_ts = XAppAction(
                xapp_id="xapp_traffic_steering",
                node_id="gnb_001",
                parameter="HANDOVER",
                value=2.0,  # handover para gnb_002
                priority=70,
            )
            act_slice = XAppAction(
                xapp_id="xapp_slicing",
                node_id="gnb_001",
                parameter="PRB_QUOTA",
                value=35.0,  # reduz quota para 35%
                priority=75,
            )
            proposed_actions = [act_ts, act_slice]

        else:
            # Cenário limpo ou normal
            act_normal = XAppAction(
                xapp_id="xapp_qos_guarantor",
                node_id="gnb_001",
                parameter="PRB_QUOTA",
                value=80.0,
                priority=70,
            )
            proposed_actions = [act_normal]

        # Detecção de Conflitos via Perception Engine
        self.active_conflicts = self.perception.detect_action_group(proposed_actions)
        
        # Métricas de Percepção
        self.latest_kpi_metrics = {
            "monitored_nodes": ["gnb_001", "gnb_002"],
            "avg_sinr_db": round(sum(u["sinr_db"] for u in self.ues) / len(self.ues), 1),
            "total_throughput_mbps": round(sum(u["thp_dl_mbps"] for u in self.ues), 1),
            "sla_violations_count": sum(1 for u in self.ues if u["sla_violation"]),
            "anomaly_detected": len(self.active_conflicts) > 0,
            "detected_conflicts_count": len(self.active_conflicts),
        }

        # =====================================================================
        # 4. BLOCO 4: Grafo de Conhecimento Cognitivo (Knowledge Graph)
        # =====================================================================
        self.knowledge_graph = self._build_knowledge_graph(proposed_actions, self.active_conflicts)

        # =====================================================================
        # 5. BLOCO 5: Módulo de Refinamento & Segurança (H-RDL Safety Guards)
        # =====================================================================
        resolution = None
        safety_status = {"is_safe": True, "level": 2, "reason": "No conflicts detected; passed default checks"}
        winning_actions: List[XAppAction] = []

        if self.active_conflicts:
            # Arbitragem determinística H-RDL (TVS / EEVS)
            primary_conflict = self.active_conflicts[0]
            resolution = self.reasoning.resolve(primary_conflict)
            is_safe, level, reason = self.refinement.validate(resolution, primary_conflict)
            safety_status = {"is_safe": is_safe, "level": level, "reason": reason}
            winning_actions = resolution.winning_actions if is_safe else []
        else:
            # Pass-Through Seguro com validação unitária
            if proposed_actions:
                is_safe, level, reason = self.refinement.validate_single_action(proposed_actions[0])
                safety_status = {"is_safe": is_safe, "level": level, "reason": reason}
                if is_safe:
                    winning_actions = [proposed_actions[0]]

        self.latest_refinement = {
            "strategy": resolution.strategy_used.value if resolution else "PASS_THROUGH",
            "confidence": resolution.confidence if resolution else 1.0,
            "safety_guard": safety_status,
            "winning_actions": [
                {
                    "xapp_id": a.xapp_id,
                    "node_id": a.node_id,
                    "parameter": a.parameter,
                    "value": a.value,
                    "priority": a.priority,
                }
                for a in winning_actions
            ],
            "clipped_or_modified": resolution.modified_value if resolution else None,
            "shannon_utility": round(random.uniform(0.78, 0.94), 3),
            "earth_energy_savings_pct": round(random.uniform(12.4, 24.8), 1),
        }

        # =====================================================================
        # 6. BLOCO 6: Ação de Controle para RAN e Malha Fechada (E2SM-RC Dispatch)
        # =====================================================================
        if winning_actions:
            for act in winning_actions:
                t_dispatch = time.perf_counter()
                
                # Aplica o efeito físico simulado na RAN (Loopback)
                if act.parameter == "TX_POWER" and act.node_id in self.gnbs:
                    self.gnbs[act.node_id]["tx_power_dbm"] = float(act.value)
                elif act.parameter == "PRB_QUOTA" and act.node_id in self.gnbs:
                    self.gnbs[act.node_id]["prb_used"] = int(self.gnbs[act.node_id]["prb_total"] * (act.value / 100.0))

                t_ack = time.perf_counter()
                # Latência de malha fechada realista (3-7 ms)
                loop_lat = (t_ack - t_dispatch) * 1000.0 + random.uniform(2.8, 4.5)
                self.closed_loop_latency_ms = round(loop_lat, 2)

                control_entry = {
                    "timestamp": t_now,
                    "sim_time": self.sim_time_s,
                    "control_id": str(uuid.uuid4())[:8],
                    "target_node": act.node_id,
                    "target_param": act.parameter,
                    "commanded_value": act.value,
                    "origin_xapp": act.xapp_id,
                    "e2sm_rc_action_id": 101 if act.parameter == "TX_POWER" else 102,
                    "ack_status": "RIC_CONTROL_ACK (SUCCESS)",
                    "causal_latency_ms": self.closed_loop_latency_ms,
                    "budget_limit_ms": 10.0,
                    "sla_budget_pass": self.closed_loop_latency_ms < 10.0,
                }
                self.control_actions_history.insert(0, control_entry)

                # Adiciona sinalização E2SM-RC no barramento de protocolo (Bloco 2)
                self.protocol_trace_buffer.insert(0, {
                    "timestamp": t_now,
                    "sim_time": self.sim_time_s,
                    "type": "RMR_MSG_TX",
                    "mtype": 12010,
                    "mtype_name": "RIC_CONTROL_REQ",
                    "sub_id": 2001,
                    "source": "xapp_rdl",
                    "target": act.node_id,
                    "payload_len": 64,
                    "asn1_summary": f"E2AP-PDU [initiatingMessage] -> E2SM-RC v1.0 ControlReq (Param: {act.parameter}={act.value}, Target: {act.node_id})",
                })
                self.protocol_trace_buffer.insert(0, {
                    "timestamp": t_now + 0.004,
                    "sim_time": self.sim_time_s,
                    "type": "RMR_MSG_RX",
                    "mtype": 12011,
                    "mtype_name": "RIC_CONTROL_RESP",
                    "sub_id": 2001,
                    "source": act.node_id,
                    "target": "xapp_rdl",
                    "payload_len": 32,
                    "asn1_summary": f"E2AP-PDU [successfulOutcome] -> RICcontrolAcknowledge (Status: EXECUTED, Latency: {self.closed_loop_latency_ms} ms)",
                })

        if len(self.control_actions_history) > 20:
            self.control_actions_history = self.control_actions_history[:20]

        return self.get_full_state()

    def _generate_e2sm_kpm_pdu(self, node_id: str) -> Dict[str, Any]:
        """Gera PDU representativo de telemetria ASN.1 / APER de E2SM-KPM v2.0."""
        prb = self.gnbs[node_id]["prb_used"]
        raw_hex = f"00c80104{random.randint(1000, 9999):04x}000100{prb:02x}4120a104f210"
        return {
            "timestamp": time.time(),
            "sim_time": self.sim_time_s,
            "type": "E2SM_KPM_INDICATION",
            "mtype": 12050,
            "mtype_name": "RIC_INDICATION",
            "node_id": node_id,
            "raw_hex": raw_hex,
            "asn1_summary": f"E2SM-KPM v2.0 IndicationReport (Meas: DRB.UEThpDl, RRU.PrbUsedDl={prb}, Granul=100ms)",
            "pdu_decoded": {
                "procedureCode": 202,
                "criticality": "ignore",
                "ranFunctionID": 2,
                "indicationHeader": {"colletStartTime": int(time.time()), "fileFormatVersion": "1.0"},
                "indicationMessage": {
                    "measInfoList": ["DRB.UEThpDl", "RRU.PrbUsedDl", "L1M.DL-sinr"],
                    "measValues": [128.4, prb, 19.8],
                },
            },
        }

    def _build_knowledge_graph(
        self, proposed_actions: List[XAppAction], conflicts: List[ConflictEvent]
    ) -> Dict[str, Any]:
        """Constrói a representação semântica do grafo de conhecimento."""
        nodes = [
            {"id": "gnb_001", "label": "gNB 001 (Macro)", "type": "gNB", "status": "active"},
            {"id": "gnb_002", "label": "gNB 002 (SmallCell)", "type": "gNB", "status": "active"},
            {"id": "slice_urllc", "label": "Slice URLLC-01", "type": "Slice", "sla": "< 5ms"},
            {"id": "slice_embb", "label": "Slice eMBB-01", "type": "Slice", "sla": "> 50Mbps"},
            {"id": "xapp_qos", "label": "xApp QoS Guarantor", "type": "xApp", "prio": 85},
            {"id": "xapp_energy", "label": "xApp Energy Saver", "type": "xApp", "prio": 60},
            {"id": "xapp_ts", "label": "xApp Traffic Steering", "type": "xApp", "prio": 70},
            {"id": "param_tx_power", "label": "RCP: TX_POWER", "type": "Parameter"},
            {"id": "param_prb", "label": "RCP: PRB_QUOTA", "type": "Parameter"},
        ]

        edges = [
            {"source": "gnb_001", "target": "slice_urllc", "rel": "hosts_slice"},
            {"source": "gnb_001", "target": "slice_embb", "rel": "hosts_slice"},
            {"source": "gnb_002", "target": "slice_embb", "rel": "hosts_slice"},
            {"source": "xapp_qos", "target": "param_tx_power", "rel": "proposes"},
            {"source": "xapp_energy", "target": "param_tx_power", "rel": "proposes"},
            {"source": "xapp_ts", "target": "param_prb", "rel": "proposes"},
        ]

        # Adiciona arestas de conflito ativas
        has_direct = any(c.conflict_type == ConflictType.DIRECT for c in conflicts)
        has_indirect = any(c.conflict_type == ConflictType.INDIRECT for c in conflicts)

        if has_direct:
            edges.append({
                "source": "xapp_qos",
                "target": "xapp_energy",
                "rel": "DIRECT_CONFLICT",
                "severity": "CRITICAL",
                "param": "TX_POWER",
            })

        if has_indirect:
            edges.append({
                "source": "xapp_ts",
                "target": "xapp_qos",
                "rel": "INDIRECT_CONFLICT",
                "severity": "MEDIUM",
                "param": "PRB_vs_Throughput",
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "metrics": {
                "nodes_count": len(nodes),
                "edges_count": len(edges),
                "conflict_cycles_count": 1 if has_direct or has_indirect else 0,
                "density": round(len(edges) / (len(nodes) * (len(nodes) - 1)), 3),
            },
        }

    def get_full_state(self) -> Dict[str, Any]:
        """Retorna o estado consolidado dos 6 blocos para consumo da interface."""
        return {
            "sim_time_s": self.sim_time_s,
            "tick": self.tick_count,
            "is_paused": self.is_paused,
            "forced_scenario": self.forced_scenario,
            "block1_ran_registration": {
                "gnbs": self.gnbs,
                "ues": self.ues,
                "total_connected_ues": len(self.ues),
            },
            "block2_protocol_signaling": {
                "latest_traces": self.protocol_trace_buffer[:10],
                "total_messages": len(self.protocol_trace_buffer),
            },
            "block3_perception_module": {
                "metrics": self.latest_kpi_metrics,
                "active_conflicts": [
                    {
                        "conflict_id": c.conflict_id,
                        "type": c.conflict_type.value,
                        "severity": c.severity.value,
                        "description": c.description,
                        "involved_xapps": [a.xapp_id for a in c.involved_xapps],
                        "affected_kpis": c.affected_kpis,
                    }
                    for c in self.active_conflicts
                ],
            },
            "block4_knowledge_graph": self.knowledge_graph,
            "block5_refinement_module": self.latest_refinement,
            "block6_ran_control_action": {
                "closed_loop_latency_ms": self.closed_loop_latency_ms,
                "budget_ms": 10.0,
                "recent_actions": self.control_actions_history[:6],
            },
        }


# Instância singleton global do motor
simulation_engine = RichSimulationEngine()
