"""Expose run-scoped ns-3/5G-LENA artifacts to the terminal monitors.

FlowMonitor metrics and execution logs are read from the selected run. KPM,
RDL, and E2SM-RC evidence is reported only when artifacts exist in that run.
"""

from __future__ import annotations

import datetime
import json
import os
import xml.etree.ElementTree as ET
from typing import Any

SCENARIOS_CATALOG = {
    "S0": {
        "key": "no_conflict",
        "title": "S0: Baseline Sem Conflito (Pass-Through E2)",
        "gnbs": ["gnb_nori_01 (3.5 GHz Band n78 / 100MHz)"],
        "conflict_type": "NONE",
        "desc": "Controle E2 aberto sem conflito; tráfego admitido 100% na O-DU",
        "involved_xapps": ["xapp_telemetry_collector"],
        "target_kpi": "RRU.PrbTotDl",
    },
    "S1": {
        "key": "direct_prb",
        "title": "S1: Conflito Direto de PRB (xSlice vs Energy Saving com Disputa de Capacidade)",
        "gnbs": ["gnb_nori_01 (3.5 GHz Band n78 / 100MHz)"],
        "conflict_type": "DIRECT_RESOURCE_CONTENTION",
        "desc": "Disputa de quotas PRB: xSlice (80%) vs xApp Energy (50%) com saturação de canal",
        "involved_xapps": ["xapp_embb_optimizer", "xapp_energy_saving"],
        "target_kpi": "RRU.PrbUsedDl",
    },
    "S2": {
        "key": "energy_vs_qos",
        "title": "S2: Trade-off EEVS (Energy Saving vs SLA URLLC Multi-Métrica)",
        "gnbs": ["gnb_nori_01 (Célula Macro)", "gnb_02 (Micro Célula)"],
        "conflict_type": "KPI_DEGRADATION_TRADE_OFF",
        "desc": "Downscaling agressivo de potência causando violação severa de latência URLLC",
        "involved_xapps": ["xapp_energy_saving", "xapp_urllc_guard"],
        "target_kpi": "DRB.RlcSduDelayDl",
    },
    "S3": {
        "key": "tvs_conflict",
        "title": "S3: Conflito TVS (Traffic Steering vs Fatiamento QoS com Handover A3)",
        "gnbs": ["gnb_nori_01 (Célula Origem)", "gnb_02 (Célula Alvo Handover A3)"],
        "conflict_type": "MULTI_CELL_HANDOVER_CONTENTION",
        "desc": "Disputa entre desvio de tráfego por handover dinâmico e garantia de slice local",
        "involved_xapps": ["xapp_traffic_steering", "xapp_slicing_manager"],
        "target_kpi": "HO.SuccOutInterEnb",
    },
    "S4": {
        "key": "ts_vs_energy",
        "title": "S4: Traffic Steering vs Sleep Mode (Trade-off de Fechamento de Célula)",
        "gnbs": ["gnb_nori_01", "gnb_02 (Sleep Mode Candidate)"],
        "conflict_type": "CELL_ACTIVATION_CONTENTION",
        "desc": "Tentativa de descarregar tráfego em célula entrando em modo sleep profundo",
        "involved_xapps": ["xapp_traffic_steering", "xapp_energy_saving"],
        "target_kpi": "PE.EnergyConsumpDl",
    },
    "S5": {
        "key": "temporal_pingpong",
        "title": "S5: Ping-Pong Temporal & Flapping de Handover",
        "gnbs": ["gnb_nori_01", "gnb_02"],
        "conflict_type": "TEMPORAL_HANDOVER_FLAPPING",
        "desc": "Oscilações cíclicas de handover repetitivo gerando degradação na sinalização RRC",
        "involved_xapps": ["xapp_traffic_steering_a", "xapp_traffic_steering_b"],
        "target_kpi": "HO.FailInterEnb",
    },
    "S6": {
        "key": "conflict_storm",
        "title": "S6: Tempestade de Conflitos Estocástica",
        "gnbs": ["gnb_nori_01 (Multi-Slice 5G-LENA)"],
        "conflict_type": "STOCHASTIC_CONFLICT_STORM",
        "desc": "Sobrecarga simultânea em rajada com 4 xApps disputando recursos de rádio",
        "involved_xapps": ["xapp_urllc", "xapp_embb", "xapp_energy", "xapp_steering"],
        "target_kpi": "RRU.PrbTotDl",
    },
    "S7": {
        "key": "fault_injection",
        "title": "S7: Injeção de Falhas O-DU/O-RU & E2SM-RC Desalinhado",
        "gnbs": ["gnb_nori_01 (Degraded O-DU Stack)"],
        "conflict_type": "PROTOCOL_DESYNC_FAULT",
        "desc": "Comportamento anômalo na O-DU com dessincronização de comandos E2SM-RC",
        "involved_xapps": ["xapp_rc_actuator", "xapp_safety_auditor"],
        "target_kpi": "RC.ControlFailureRatio",
    },
    "S8": {
        "key": "closed_loop_nori",
        "title": "S8: Tráfego 5G-LENA com agente E2 opcional",
        "gnbs": ["gnb_nori_01 (5G-LENA NR CTTC)", "gnb_02 (Handover Cell)"],
        "conflict_type": "TRAFFIC_ONLY",
        "desc": "Métricas de tráfego FlowMonitor; sem atuação E2SM-RC/RDL implementada",
        "involved_xapps": [],
        "target_kpi": "FlowMonitor.FlowStats",
    },
    "S9": {
        "key": "s9_ntn",
        "title": "S9: NTN Handover Orbital LEO & Delay Doppler",
        "gnbs": ["sat_leo_01 (600km Ka-Band 28GHz)", "sat_leo_02 (Orbit Trajectory)"],
        "conflict_type": "NTN_DOPPLER_HANDOVER_CONTENTION",
        "desc": "Deslocamento Doppler extremo e atraso de propagação de órbita LEO",
        "involved_xapps": ["xapp_ntn_steering", "xapp_doppler_compensator"],
        "target_kpi": "NTN.DopplerShiftHz",
    },
    "S10": {
        "key": "s10_uav",
        "title": "S10: Enxame UAV 3D & Drenagem de Bateria",
        "gnbs": ["uav_ap_01 (Altitude 120m)", "uav_ap_02 (Altitude 150m)"],
        "conflict_type": "UAV_TRAJECTORY_ENERGY_CONTENTION",
        "desc": "Trade-off entre reposicionamento 3D para cobertura e autonomia energética",
        "involved_xapps": ["xapp_uav_coverage_booster", "xapp_uav_battery_saver"],
        "target_kpi": "UAV.BatteryDrainRate",
    },
    "S11": {
        "key": "s11_v2x",
        "title": "S11: V2X Platooning em Rodovia & Handover Coordenado",
        "gnbs": ["gnb_rsu_01 (Rodovia km 12)", "gnb_rsu_02 (km 15)"],
        "conflict_type": "V2X_PLATOON_COORDINATION_CONTENTION",
        "desc": "Handover simultâneo de comboio veicular preservando beaconing de segurança V2X",
        "involved_xapps": ["xapp_v2x_platoon_guard", "xapp_rsu_balancer"],
        "target_kpi": "V2X.PacketDeliveryRatio",
    },
    "S12": {
        "key": "s12_iiot",
        "title": "S12: IIoT Zero-Jitter TSN & Preempção de Pacotes",
        "gnbs": ["gnb_iiot_factory_01 (SCS 60kHz TSN)"],
        "conflict_type": "TSN_DETERMINISTIC_PREEMPTION",
        "desc": "Preempção determinística em slots TSN para garantia de jitter zero (< 100us)",
        "involved_xapps": ["xapp_tsn_scheduler", "xapp_iiot_bulk_transfer"],
        "target_kpi": "TSN.MaxJitterMicrosec",
    },
    "S13": {
        "key": "s13_sagin",
        "title": "S13: SAGIN Resgate em Desastres Naturais Multi-Camada",
        "gnbs": ["sat_leo_01 (Space Tier)", "uav_relay_01 (Air Tier)", "gnb_emergency_01 (Ground Tier)"],
        "conflict_type": "SAGIN_CROSS_TIER_BACKHAUL_CONTENTION",
        "desc": "Disputa de capacidade de enlace heterogêneo entre Espaço, Ar e Solo em desastre",
        "involved_xapps": ["xapp_sagin_backhaul", "xapp_emergency_video"],
        "target_kpi": "SAGIN.CrossTierLossRatio",
    },
    "S14": {
        "key": "s14_isac",
        "title": "S14: ISAC Sensoriamento Radar vs Comunicação de Rádio",
        "gnbs": ["gnb_isac_mimo_01 (Dual-Functional Radar Comm)"],
        "conflict_type": "ISAC_RADAR_COMM_BEAM_CONTENTION",
        "desc": "Divisão de energia de feixe MIMO entre iluminação radar e transmissão de dados",
        "involved_xapps": ["xapp_isac_radar_tracker", "xapp_embb_beamformer"],
        "target_kpi": "ISAC.RadarResolutionIndex",
    },
    "S15": {
        "key": "s15_rogue",
        "title": "S15: Sequestro de Feeder NTN & Detecção de Rogue Ground Station",
        "gnbs": ["sat_leo_01 (Payload)", "ground_station_auth_01 (Legal GS)", "rogue_gs_01 (Attacker)"],
        "conflict_type": "NTN_FEEDER_HIJACK_DETECTION",
        "desc": "Infiltração de estação terrestre não-autorizada mitigada via política E2SM-RC",
        "involved_xapps": ["xapp_ntn_security_monitor", "xapp_feeder_controller"],
        "target_kpi": "SEC.RogueDetectionConfidence",
    },
}


class RealDataTelemetryProvider:
    """
    Consolidate artifacts from a selected ns-3 run for the six WSL panels.
    """

    def __init__(
        self,
        workspace_dir: str | None = None,
        target_scenario: str | None = None,
        target_run: str | None = None,
    ):
        if workspace_dir is None:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        else:
            self.base_dir = workspace_dir

        self.ns3_runs_dir = os.path.join(self.base_dir, "experiments", "results", "ns3_runs")

        # Filtro de cenário / run
        self.target_scenario = target_scenario
        self.target_run = target_run

        # Cache only artifacts belonging to the selected simulation run.
        self._cached_run_dir = None
        self._cached_run_signature = None
        self._cached_run_data = {}

        # Retained for compatibility with callers that advance the provider.
        self.current_step = 0

    def set_target_scenario(self, scenario_id: str | None):
        """Configura o cenário a ser monitorado dinamicamente (ex: 'S3', 'S8', etc.)."""
        self.target_scenario = scenario_id
        self._cached_run_dir = None
        self._cached_run_signature = None

    def set_target_run(self, run_dir_name: str | None):
        """Configura uma pasta de execução específica em ns3_runs/."""
        self.target_run = run_dir_name
        self._cached_run_dir = None
        self._cached_run_signature = None

    def _empty_run_data(self) -> dict[str, Any]:
        """Return an explicit unavailable state when no matching run exists."""
        return {
            "scenario_id": "SX",
            "scenario_meta": {
                "key": "none",
                "title": "No simulation run found",
                "gnbs": [],
                "conflict_type": "UNKNOWN",
                "desc": "",
                "involved_xapps": [],
                "target_kpi": "",
            },
            "run_dir": "sem_execucao",
            "full_run_dir": "",
            "run_status": "not_found",
            "run_status_updated_at": None,
            "status_message": "No matching simulation run was found.",
            "execution_log_tail": [],
            "xml_exists": False,
            "flowmonitor_error": None,
            "flows": [],
            "total_rx_bytes": 0,
            "total_tx_pkts": 0,
            "total_rx_pkts": 0,
            "total_lost_pkts": 0,
            "flow_count": 0,
            "mean_delay_ms": None,
            "throughput_mbps": None,
            "loss_ratio_pct": None,
            "prb_utilization_pct": None,
            "evidence": {
                "flowmonitor": False,
                "execution_log": False,
                "e2_pcap": False,
                "kpm": False,
                "rdl_decision": False,
                "control_request": False,
                "control_ack": False,
            },
            "simulation_engine": "ns-3 + 5G-LENA",
        }

    @staticmethod
    def _read_log_tail(path: str, max_bytes: int = 8192, max_lines: int = 8) -> list[str]:
        if not os.path.isfile(path):
            return []
        with open(path, "rb") as stream:
            stream.seek(max(0, os.path.getsize(path) - max_bytes))
            return stream.read().decode("utf-8", errors="replace").splitlines()[-max_lines:]

    def _scan_and_load_run(self) -> dict[str, Any]:
        """Load only artifacts belonging to the newest matching simulation run."""
        if not os.path.isdir(self.ns3_runs_dir):
            return self._empty_run_data()

        candidates = [name for name in os.listdir(self.ns3_runs_dir) if os.path.isdir(os.path.join(self.ns3_runs_dir, name))]
        candidates.sort(key=lambda name: (os.stat(os.path.join(self.ns3_runs_dir, name)).st_mtime_ns, name), reverse=True)
        if self.target_run:
            candidates = [name for name in candidates if self.target_run in name]
        elif self.target_scenario:
            scenario = SCENARIOS_CATALOG.get(self.target_scenario.upper())
            pattern = scenario["key"] if scenario else self.target_scenario.lower()
            candidates = [name for name in candidates if pattern in name.lower()]
        if not candidates:
            data = self._empty_run_data()
            requested = self.target_run or self.target_scenario
            if requested:
                data["status_message"] = f"No run matches: {requested}"
            return data

        selected_dir = candidates[0]
        full_run_dir = os.path.join(self.ns3_runs_dir, selected_dir)
        xml_path = os.path.join(full_run_dir, "flowmonitor.xml")
        status_path = os.path.join(full_run_dir, "run_status.json")
        log_path = os.path.join(full_run_dir, "execution.log")
        artifact_names = (
            "e2.pcap",
            "kpm.jsonl",
            "kpm.csv",
            "indications.jsonl",
            "rdl_decision.json",
            "decisions.jsonl",
            "control_request.json",
            "control_ack.json",
        )

        def file_signature(path: str):
            try:
                stat = os.stat(path)
                return stat.st_mtime_ns, stat.st_size
            except OSError:
                return None

        signature = tuple(
            file_signature(path)
            for path in (status_path, log_path, xml_path)
            + tuple(os.path.join(full_run_dir, name) for name in artifact_names)
        )
        if self._cached_run_dir == selected_dir and self._cached_run_signature == signature and self._cached_run_data:
            return self._cached_run_data

        scenario_id = "SX"
        scenario_meta = {"key": "generic", "title": f"ns-3 run: {selected_dir}", "gnbs": [], "conflict_type": "UNKNOWN", "desc": "", "involved_xapps": [], "target_kpi": ""}
        for key, metadata in SCENARIOS_CATALOG.items():
            if metadata["key"].lower() in selected_dir.lower():
                scenario_id, scenario_meta = key, metadata
                break

        xml_exists = os.path.isfile(xml_path)
        status = "completed_inferred" if xml_exists else "running"
        status_updated_at = None
        status_message = "FlowMonitor present; status inferred (no run marker)." if xml_exists else "Waiting for run artifacts."
        if os.path.isfile(status_path):
            try:
                with open(status_path, "r", encoding="utf-8") as stream:
                    status_data = json.load(stream)
                status = str(status_data.get("status", "unknown")).lower()
                status_updated_at = status_data.get("updated_at_utc")
                status_message = status.replace("_", " ")
            except (OSError, json.JSONDecodeError, AttributeError) as exc:
                status, status_message = "invalid_status", f"Invalid run marker: {exc}"

        flows = []
        total_rx_bytes = total_rx_pkts = total_lost_pkts = total_tx_pkts = 0
        weighted_delay_ns = 0.0
        flowmonitor_error = None
        if xml_exists:
            try:
                root = ET.parse(xml_path).getroot()
                classifiers = {}
                for group in root.iter("Ipv4FlowClassifier"):
                    for item in group:
                        classifiers[item.get("flowId")] = {"src": item.get("sourceAddress"), "dst": item.get("destinationAddress"), "port": item.get("destinationPort")}
                for item in root.iter("Flow"):
                    flow_id = item.get("flowId")
                    rx_bytes = int(item.get("rxBytes", 0))
                    rx_packets = int(item.get("rxPackets", 0))
                    tx_packets = int(item.get("txPackets", 0))
                    lost_packets = int(item.get("lostPackets", 0))
                    total_rx_bytes += rx_bytes
                    total_rx_pkts += rx_packets
                    total_tx_pkts += tx_packets
                    total_lost_pkts += lost_packets
                    if rx_packets <= 0:
                        continue
                    first_rx = float(item.get("timeFirstRxPacket", "+0ns").replace("ns", "").replace("+", ""))
                    last_rx = float(item.get("timeLastRxPacket", "+0ns").replace("ns", "").replace("+", ""))
                    duration_s = max(0.001, (last_rx - first_rx) / 1e9)
                    delay_sum_ns = float(item.get("delaySum", "+0ns").replace("ns", "").replace("+", ""))
                    classifier = classifiers.get(flow_id, {})
                    flows.append({"flow_id": int(flow_id), "src_ip": classifier.get("src"), "dst_ip": classifier.get("dst"), "destination_port": classifier.get("port"), "throughput_mbps": round(rx_bytes * 8.0 / (duration_s * 1e6), 2), "delay_ms": round(delay_sum_ns / rx_packets / 1e6, 2), "rx_bytes": rx_bytes, "rx_pkts": rx_packets, "tx_pkts": tx_packets, "lost_pkts": lost_packets})
                    weighted_delay_ns += delay_sum_ns
            except (ET.ParseError, OSError, ValueError, TypeError) as exc:
                flowmonitor_error = str(exc)

        flows.sort(key=lambda flow: -flow["rx_bytes"])
        mean_delay = weighted_delay_ns / total_rx_pkts / 1e6 if total_rx_pkts else None
        throughput = sum(flow["throughput_mbps"] for flow in flows) if flows else None
        loss_ratio = total_lost_pkts / total_tx_pkts * 100 if total_tx_pkts else None
        evidence = {
            "flowmonitor": xml_exists and flowmonitor_error is None,
            "execution_log": os.path.isfile(log_path),
            "e2_pcap": file_signature(os.path.join(full_run_dir, "e2.pcap")) is not None,
            "kpm": any(file_signature(os.path.join(full_run_dir, name)) is not None for name in ("kpm.jsonl", "kpm.csv", "indications.jsonl")),
            "rdl_decision": any(file_signature(os.path.join(full_run_dir, name)) is not None for name in ("rdl_decision.json", "decisions.jsonl")),
            "control_request": file_signature(os.path.join(full_run_dir, "control_request.json")) is not None,
            "control_ack": file_signature(os.path.join(full_run_dir, "control_ack.json")) is not None,
        }
        if flowmonitor_error:
            status_message = f"FlowMonitor inv?lido: {flowmonitor_error}"
        run = {
            "scenario_id": scenario_id, "scenario_meta": scenario_meta, "run_dir": selected_dir,
            "full_run_dir": full_run_dir, "run_status": status, "run_status_updated_at": status_updated_at,
            "status_message": status_message, "execution_log_tail": self._read_log_tail(log_path),
            "xml_exists": xml_exists, "flowmonitor_error": flowmonitor_error, "flows": flows,
            "total_rx_bytes": total_rx_bytes, "total_tx_pkts": total_tx_pkts, "total_rx_pkts": total_rx_pkts,
            "total_lost_pkts": total_lost_pkts, "flow_count": len(flows),
            "mean_delay_ms": round(mean_delay, 3) if mean_delay is not None else None,
            "throughput_mbps": round(throughput, 3) if throughput is not None else None,
            "loss_ratio_pct": round(loss_ratio, 3) if loss_ratio is not None else None,
            "prb_utilization_pct": None, "evidence": evidence, "simulation_engine": "ns-3 + 5G-LENA",
        }
        self._cached_run_dir, self._cached_run_signature, self._cached_run_data = selected_dir, signature, run
        return run

    def step(self) -> dict[str, Any]:
        """Avança o ciclo de observação sobre os dados reais da cadeia."""
        self.current_step = (self.current_step + 1) % 6
        return self.get_full_real_state()

    def get_full_real_state(self) -> dict[str, Any]:
        """Build all monitor panels from artifacts belonging to one simulation run."""
        run = self._scan_and_load_run()
        metadata, evidence, flows = run["scenario_meta"], run["evidence"], run["flows"]
        common = {"scenario_id": run["scenario_id"], "scenario_title": metadata["title"], "run_dir": run["run_dir"]}
        block1 = {
            **common, "engine": run["simulation_engine"], "run_status": run["run_status"],
            "status_message": run["status_message"], "node_id": None, "all_nodes": [],
            "prb_utilization_pct": None, "total_connected_ues": None,
            "active_data_flows": run["flow_count"], "total_traffic_mb": round(run["total_rx_bytes"] / 1e6, 2),
            "total_packets_rx": run["total_rx_pkts"], "total_packets_tx": run["total_tx_pkts"],
            "total_packets_lost": run["total_lost_pkts"], "flows": flows[:12],
            "flowmonitor_available": evidence["flowmonitor"], "flowmonitor_error": run["flowmonitor_error"],
        }
        block2 = {**common, "e2_pcap_available": evidence["e2_pcap"], "kpm_artifact_available": evidence["kpm"], "recent_execution_log": run["execution_log_tail"]}
        block3 = {
            **common, "flowmonitor_available": evidence["flowmonitor"], "throughput_mbps": run["throughput_mbps"],
            "mean_delay_ms": run["mean_delay_ms"], "loss_ratio_pct": run["loss_ratio_pct"],
            "total_packets_tx": run["total_tx_pkts"], "total_packets_rx": run["total_rx_pkts"],
            "total_packets_lost": run["total_lost_pkts"], "prb_utilization_pct": None,
            "sla_evaluation": "unavailable_without_per_flow_qos_configuration",
            "conflict_detection": "unavailable_without_rdl_decision_artifact",
        }
        nodes_by_ip, edges = {}, []
        for flow in flows:
            for address in (flow["src_ip"], flow["dst_ip"]):
                if address:
                    nodes_by_ip[address] = {"id": address, "label": address, "type": "IP endpoint"}
            if flow["src_ip"] and flow["dst_ip"]:
                edges.append({"source": flow["src_ip"], "target": flow["dst_ip"], "rel": f"FLOW_{flow['flow_id']}"})
        nodes = list(nodes_by_ip.values())
        block4 = {
            **common, "topology_source": "FlowMonitor IPv4FlowClassifier", "nodes_count": len(nodes),
            "edges_count": len(edges), "active_conflict_cycles": None,
            "density": round(len(edges) / (len(nodes) * (len(nodes) - 1)), 3) if len(nodes) > 1 else 0.0,
            "nodes": nodes, "edges": edges,
        }
        block5 = {**common, "decision_artifact_available": evidence["rdl_decision"], "decision_status": "artifact available in this run" if evidence["rdl_decision"] else "not emitted by this run"}
        block6 = {
            **common, "control_request_available": evidence["control_request"],
            "control_ack_available": evidence["control_ack"],
            "closed_loop_evidence_available": evidence["control_request"] and evidence["control_ack"],
        }
        return {
            "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "active_scenario_id": run["scenario_id"], "active_scenario_title": metadata["title"],
            "active_run_dir": run["run_dir"], "run_status": run["run_status"],
            "run_status_message": run["status_message"], "run_status_updated_at": run["run_status_updated_at"],
            "evidence": evidence, "block1_ran_registration": block1, "block2_protocol_signaling": block2,
            "block3_perception_module": block3, "block4_knowledge_graph": block4,
            "block5_refinement_module": block5, "block6_ran_control_action": block6,
        }



# Instância global compartilhada
real_telemetry_provider = RealDataTelemetryProvider()
