"""
Provedor de Telemetria e Evidências Reais dos 6 Blocos Cognitivos O-RAN.
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

DIRETRIZ ESTRITA: ZERO DADOS SINTÉTICOS. ZERO MOCKS.
Todas as métricas, registros de UEs, sinalizações ASN.1 APER, grafos e
ações de controle são extraídos estritamente de:
  1. Artefatos de Simulação ns-3 / 5G-LENA (FlowMonitor XMLs);
  2. Traces de Captura de Pacotes PCAP E2 (e2_closed_loop_live.pcap);
  3. Cadeia Causal Certificada (experiments/runs/certified_closed_loop_chain/);
  4. Execução real dos módulos de Percepção, Raciocínio e Refinamento do core RDL.
"""

import os
import sys
import json
import struct
import datetime
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional

from src.conflict_types import (
    XAppAction,
    ConflictEvent,
    ConflictType,
    ConflictSeverity,
    KPMReport,
)
from src.core.perception import Perception
from src.core.reasoning import Reasoning
from src.core.refinement import Refinement
from src.infrastructure.sdl_repository import SdlRepository

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
        "gnbs": ["gnb_nori_01", "gnb_02"],
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
        "title": "S8: Closed-Loop NORI E2SM-KPM / RC em Malha Fechada",
        "gnbs": ["gnb_nori_01 (5G-LENA NR CTTC)", "gnb_02 (Handover Cell)"],
        "conflict_type": "CLOSED_LOOP_MULTI_TIER",
        "desc": "Arbitragem em malha fechada E2SM-KPM -> H-RDL -> E2SM-RC < 10ms comprovada",
        "involved_xapps": ["xapp_embb_optimizer", "xapp_urllc_guard"],
        "target_kpi": "DRB.RlcSduDelayDl",
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
    Consolidador de dados 100% empíricos e rastreáveis para os 6 blocos cognitivos O-RAN.
    Alimenta os Monitores de Painel no terminal WSL Ubuntu sem qualquer gerador estocástico.
    """

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        target_scenario: Optional[str] = None,
        target_run: Optional[str] = None,
    ):
        if workspace_dir is None:
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        else:
            self.base_dir = workspace_dir

        self.chain_dir = os.path.join(self.base_dir, "experiments", "runs", "certified_closed_loop_chain")
        self.pcap_path = os.path.join(self.chain_dir, "e2_closed_loop_live.pcap")
        self.ns3_runs_dir = os.path.join(self.base_dir, "experiments", "results", "ns3_runs")

        # Filtro de cenário / run
        self.target_scenario = target_scenario
        self.target_run = target_run

        # Core RDL real
        self.sdl = SdlRepository()
        self.perception = Perception()
        self.reasoning = Reasoning(memory=self.sdl)
        self.refinement = Refinement(memory=self.sdl, strict_capabilities=False)

        # Cache dinâmico dos artefatos da execução selecionada
        self._cached_run_dir = None
        self._cached_run_signature = None
        self._cached_run_data = {}

        # Step index para reprodução sequencial da cadeia causal real
        self.current_step = 0

    def set_target_scenario(self, scenario_id: Optional[str]):
        """Configura o cenário a ser monitorado dinamicamente (ex: 'S3', 'S8', etc.)."""
        self.target_scenario = scenario_id
        self._cached_run_dir = None
        self._cached_run_signature = None

    def set_target_run(self, run_dir_name: Optional[str]):
        """Configura uma pasta de execução específica em ns3_runs/."""
        self.target_run = run_dir_name
        self._cached_run_dir = None
        self._cached_run_signature = None

    def _load_certified_chain(self) -> Dict[str, Any]:
        """Carrega os arquivos JSON certificados da cadeia causal (L3)."""
        chain = {}
        files = {
            "indication_t0": "01_indication_t0.json",
            "rdl_decision": "02_rdl_decision.json",
            "control_request": "03_control_request.json",
            "control_ack": "04_control_ack.json",
            "mac_transition": "05_ran_mac_transition.log",
            "indication_t1": "06_indication_t1.json",
            "manifest": "chain_manifest.json",
        }
        for key, fname in files.items():
            fpath = os.path.join(self.chain_dir, fname)
            if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                try:
                    if fname.endswith(".json"):
                        with open(fpath, "r", encoding="utf-8") as fh:
                            chain[key] = json.load(fh)
                    else:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            chain[key] = fh.read().strip()
                except Exception:
                    chain[key] = {}
            else:
                chain[key] = {}
        return chain

    def _load_pcap_frames(self) -> List[Dict[str, Any]]:
        """Lê frames binários reais do PCAP E2 capturado com endianness exato."""
        frames = []
        if not os.path.exists(self.pcap_path):
            alt_pcap = os.path.join(self.base_dir, "experiments", "runs", "S1_B0_seed1001", "pcap", "e2.pcap")
            if os.path.exists(alt_pcap):
                self.pcap_path = alt_pcap
            else:
                return frames

        try:
            with open(self.pcap_path, "rb") as fh:
                global_hdr = fh.read(24)
                if len(global_hdr) < 24:
                    return frames

                magic = global_hdr[:4]
                is_nanosec = (magic == b'\x4d\x3c\xb2\xa1' or magic == b'\xa1\xb2\x3c\x4d')
                is_swapped = (magic == b'\xd4\xc3\xb2\xa1' or magic == b'\x4d\x3c\xb2\xa1')
                endian = "<" if (is_swapped or sys.byteorder == "little") else ">"

                pkt_idx = 0
                while True:
                    pkt_hdr = fh.read(16)
                    if not pkt_hdr or len(pkt_hdr) < 16:
                        break
                    pkt_idx += 1
                    sec, subsec, incl_len, orig_len = struct.unpack(endian + "IIII", pkt_hdr)
                    frame_bytes = fh.read(incl_len)
                    divisor = 1e9 if is_nanosec else 1e6
                    dt = datetime.datetime.fromtimestamp(sec + subsec / divisor, tz=datetime.timezone.utc)
                    hex_dump = frame_bytes.hex()

                    frames.append({
                        "frame_idx": pkt_idx,
                        "timestamp_utc": dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                        "length_bytes": incl_len,
                        "hex_preview": hex_dump[:48] + ("..." if len(hex_dump) > 48 else ""),
                        "raw_bytes": frame_bytes,
                    })
        except Exception:
            pass
        return frames

    def _empty_run_data(self) -> Dict[str, Any]:
        """Retorna estado explícito quando não há execução disponível."""
        return {
            "scenario_id": "SX",
            "scenario_meta": {
                "key": "none",
                "title": "Nenhuma execução encontrada",
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
            "status_message": "Nenhum diretório de execução encontrado.",
            "execution_log_tail": [],
            "xml_exists": False,
            "flowmonitor_error": None,
            "ues": [],
            "total_rx_bytes": 0,
            "total_tx_pkts": 0,
            "total_rx_pkts": 0,
            "total_lost_pkts": 0,
            "flow_count": 0,
            "mean_delay_ms": None,
            "throughput_mbps": None,
            "loss_ratio_pct": None,
            "prb_utilization_pct": None,
            "evidence": {},
            "simulation_engine": "ns-3 + 5G-LENA",
        }

    @staticmethod
    def _read_log_tail(path: str, max_bytes: int = 8192, max_lines: int = 8) -> List[str]:
        if not os.path.isfile(path):
            return []
        with open(path, "rb") as stream:
            stream.seek(max(0, os.path.getsize(path) - max_bytes))
            content = stream.read().decode("utf-8", errors="replace")
        return content.splitlines()[-max_lines:]

    def _run_has_active_traffic(self, dirname: str) -> bool:
        """Verifica rapidamente se a pasta possui flowmonitor.xml com tráfego real."""
        p = os.path.join(self.ns3_runs_dir, dirname, "flowmonitor.xml")
        if not os.path.exists(p) or os.path.getsize(p) < 1000:
            return False
        try:
            tree = ET.parse(p)
            for f in tree.getroot().iter("Flow"):
                if int(f.get("rxPackets", 0)) > 0 and int(f.get("rxBytes", 0)) > 500:
                    return True
        except Exception:
            return False
        return False

    def _scan_and_load_run(self) -> Dict[str, Any]:
        """
        Escaneia dinamicamente os artefatos de simulação em experiments/results/ns3_runs/.
        Recarrega de forma não-bloqueante apenas quando novos dados forem produzidos.
        """
        if not os.path.exists(self.ns3_runs_dir):
            return self._empty_run_data()

        candidate_dirs = sorted(
            (
                d for d in os.listdir(self.ns3_runs_dir)
                if os.path.isdir(os.path.join(self.ns3_runs_dir, d))
            ),
            key=lambda d: os.path.getmtime(os.path.join(self.ns3_runs_dir, d)),
            reverse=True,
        )
        if not candidate_dirs:
            return self._empty_run_data()

        selected_dir = None

        # 1. Filtro explícito de run
        if self.target_run:
            for d in candidate_dirs:
                if self.target_run in d:
                    selected_dir = d
                    break

        # 2. Filtro de cenário (ex: 'S3', 'S8', 'tvs_conflict')
        elif self.target_scenario:
            scen_key = self.target_scenario.upper()
            scen_info = SCENARIOS_CATALOG.get(scen_key)
            lookup_pattern = scen_info["key"] if scen_info else self.target_scenario.lower()
            matching = [d for d in candidate_dirs if lookup_pattern in d]
            if matching:
                selected_dir = matching[0]

        if (self.target_run or self.target_scenario) and not selected_dir:
            data = self._empty_run_data()
            requested = self.target_run or self.target_scenario
            data["status_message"] = f"Nenhuma execução corresponde a: {requested}"
            return data

        # A execução mais recente também deve ser exibida antes de gerar o FlowMonitor.
        if not selected_dir:
            selected_dir = candidate_dirs[0]

        full_run_dir = os.path.join(self.ns3_runs_dir, selected_dir)
        xml_path = os.path.join(full_run_dir, "flowmonitor.xml")
        status_path = os.path.join(full_run_dir, "run_status.json")
        log_path = os.path.join(full_run_dir, "execution.log")

        def file_signature(path: str):
            try:
                stat = os.stat(path)
                return stat.st_mtime_ns, stat.st_size
            except OSError:
                return None

        signature = (
            file_signature(status_path),
            file_signature(log_path),
            file_signature(xml_path),
        )

        # Cache check
        if (
            self._cached_run_dir == selected_dir
            and self._cached_run_signature == signature
            and self._cached_run_data
        ):
            return self._cached_run_data

        # Identificação do cenário pelo nome do diretório; não implica evidência E2.
        sid = "SX"
        scen_meta = {
            "key": "generic",
            "title": f"Cenário ns-3: {selected_dir}",
            "gnbs": [],
            "conflict_type": "MULTI_AGENT_CONTENTION",
            "desc": "",
            "involved_xapps": [],
            "target_kpi": "",
        }
        for k, v in SCENARIOS_CATALOG.items():
            if v["key"] in selected_dir:
                sid = k
                scen_meta = v
                break

        run_status = "unknown"
        run_status_updated_at = None
        status_message = "Esta execução não possui marcador de estado."
        if os.path.isfile(status_path):
            try:
                with open(status_path, "r", encoding="utf-8") as stream:
                    status_data = json.load(stream)
                run_status = str(status_data.get("status", "unknown")).lower()
                run_status_updated_at = status_data.get("updated_at_utc")
                status_message = run_status.replace("_", " ")
            except (OSError, json.JSONDecodeError, AttributeError) as exc:
                run_status = "invalid_status"
                status_message = f"Marcador de execução inválido: {exc}"

        execution_log_tail = self._read_log_tail(log_path)

        # Parse exclusivo do FlowMonitor pertencente a esta execução.
        ues = []
        total_rx_bytes = 0
        total_rx_pkts = 0
        total_lost_pkts = 0
        total_tx_pkts = 0
        weighted_delay_ns = 0.0
        flowmonitor_error = None
        xml_exists = os.path.isfile(xml_path)

        if os.path.exists(xml_path) and os.path.getsize(xml_path) > 100:
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                classifiers = {}
                for cl in root.iter("Ipv4FlowClassifier"):
                    for f in cl:
                        classifiers[f.get("flowId")] = {
                            "src": f.get("sourceAddress"),
                            "dst": f.get("destinationAddress"),
                            "port": f.get("destinationPort"),
                        }

                for flow in root.iter("Flow"):
                    fid = flow.get("flowId")
                    rx_bytes = int(flow.get("rxBytes", 0))
                    rx_pkts = int(flow.get("rxPackets", 0))
                    tx_pkts = int(flow.get("txPackets", 0))
                    lost_pkts = int(flow.get("lostPackets", 0))

                    total_rx_bytes += rx_bytes
                    total_tx_pkts += tx_pkts
                    total_rx_pkts += rx_pkts
                    total_lost_pkts += lost_pkts

                    if rx_pkts > 0 and rx_bytes > 500:
                        t_first = float(flow.get("timeFirstRxPacket", "+0ns").replace("ns", "").replace("+", ""))
                        t_last = float(flow.get("timeLastRxPacket", "+0ns").replace("ns", "").replace("+", ""))
                        dur_s = max(0.001, (t_last - t_first) / 1e9)
                        thp_mbps = (rx_bytes * 8.0) / (dur_s * 1e6)
                        delay_sum = float(flow.get("delaySum", "+0ns").replace("ns", "").replace("+", ""))
                        avg_delay_ms = delay_sum / rx_pkts / 1e6

                        classifier = classifiers.get(fid, {})

                        ues.append({
                            "flow_id": int(fid),
                            "src_ip": classifier.get("src"),
                            "dst_ip": classifier.get("dst"),
                            "destination_port": classifier.get("port"),
                            "throughput_mbps": round(thp_mbps, 2),
                            "delay_ms": round(avg_delay_ms, 2),
                            "rx_bytes": rx_bytes,
                            "rx_pkts": rx_pkts,
                            "tx_pkts": tx_pkts,
                            "lost_pkts": lost_pkts,
                        })
                        weighted_delay_ns += delay_sum
            except (ET.ParseError, OSError, ValueError, TypeError) as exc:
                flowmonitor_error = str(exc)

        # Ordena pelos fluxos com maior volume efetivamente recebido.
        ues.sort(key=lambda u: -u["rx_bytes"])

        if run_status == "unknown" and xml_exists and flowmonitor_error is None:
            run_status = "completed_inferred"
            status_message = "FlowMonitor presente; estado inferido (execução sem marcador)."
        elif run_status == "unknown" and not xml_exists:
            status_message = "Sem FlowMonitor; estado da execução não pode ser confirmado."
        if flowmonitor_error:
            status_message = f"FlowMonitor indisponível: {flowmonitor_error}"

        mean_delay_ms = (
            weighted_delay_ns / total_rx_pkts / 1e6 if total_rx_pkts else None
        )
        throughput_mbps = sum(flow["throughput_mbps"] for flow in ues) if ues else None
        loss_ratio_pct = (
            total_lost_pkts / total_tx_pkts * 100.0
            if total_tx_pkts > 0
            else None
        )
        evidence = {
            "flowmonitor": xml_exists and flowmonitor_error is None,
            "execution_log": os.path.isfile(log_path),
            "e2_pcap": os.path.isfile(os.path.join(full_run_dir, "e2.pcap")),
            "kpm": any(
                os.path.isfile(os.path.join(full_run_dir, name))
                for name in ("kpm.jsonl", "kpm.csv", "indications.jsonl")
            ),
            "rdl_decision": any(
                os.path.isfile(os.path.join(full_run_dir, name))
                for name in ("rdl_decision.json", "decisions.jsonl")
            ),
            "control_request": os.path.isfile(os.path.join(full_run_dir, "control_request.json")),
            "control_ack": os.path.isfile(os.path.join(full_run_dir, "control_ack.json")),
        }

        run_data = {
            "scenario_id": sid,
            "scenario_meta": scen_meta,
            "run_dir": selected_dir,
            "full_run_dir": full_run_dir,
            "run_status": run_status,
            "run_status_updated_at": run_status_updated_at,
            "status_message": status_message,
            "execution_log_tail": execution_log_tail,
            "xml_exists": xml_exists,
            "flowmonitor_error": flowmonitor_error,
            "ues": ues,
            "total_rx_bytes": total_rx_bytes,
            "total_tx_pkts": total_tx_pkts,
            "total_rx_pkts": total_rx_pkts,
            "total_lost_pkts": total_lost_pkts,
            "flow_count": len(ues),
            "mean_delay_ms": round(mean_delay_ms, 3) if mean_delay_ms is not None else None,
            "throughput_mbps": round(throughput_mbps, 3) if throughput_mbps is not None else None,
            "loss_ratio_pct": round(loss_ratio_pct, 3) if loss_ratio_pct is not None else None,
            "prb_utilization_pct": None,
            "evidence": evidence,
            "simulation_engine": "ns-3 + 5G-LENA",
        }

        self._cached_run_dir = selected_dir
        self._cached_run_signature = signature
        self._cached_run_data = run_data
        return run_data

    def step(self) -> Dict[str, Any]:
        """Avança o ciclo de observação sobre os dados reais da cadeia."""
        self.current_step = (self.current_step + 1) % 6
        return self.get_full_real_state()

    def get_full_real_state(self) -> Dict[str, Any]:
        """
        Retorna o estado consolidado dos 6 blocos utilizando exclusivamente
        evidências experimentais reais rastreáveis da simulação ns-3 ativa.
        """
        # Carrega dinamicamente a simulação ns-3 ativa
        run_data = self._scan_and_load_run()
        scen_meta = run_data["scenario_meta"]
        primary_gnb = scen_meta["gnbs"][0] if scen_meta["gnbs"] else "not available"
        ues = run_data["ues"]
        evidence = run_data["evidence"]

        # -------------------------------------------------------------
        # BLOCO 1: Estado da simulação e fluxos observados pelo FlowMonitor
        # -------------------------------------------------------------
        block1 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "engine": run_data["simulation_engine"],
            "run_status": run_data["run_status"],
            "status_message": run_data["status_message"],
            "node_id": primary_gnb,
            "all_nodes": scen_meta["gnbs"],
            "prb_utilization_pct": run_data["prb_utilization_pct"],
            "total_connected_ues": None,
            "active_data_flows": run_data["flow_count"],
            "total_traffic_mb": round(run_data["total_rx_bytes"] / 1e6, 2),
            "total_packets_rx": run_data["total_rx_pkts"],
            "total_packets_tx": run_data["total_tx_pkts"],
            "total_packets_lost": run_data["total_lost_pkts"],
            "ues": ues[:12],
            "flowmonitor_available": evidence.get("flowmonitor", False),
            "flowmonitor_error": run_data["flowmonitor_error"],
        }

        # -------------------------------------------------------------
        # BLOCO 2: Sinalizações e Mensagens de Protocolo (E2AP / E2SM / PCAP)
        # -------------------------------------------------------------
        block2 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "e2_pcap_available": evidence["e2_pcap"],
            "kpm_artifact_available": evidence["kpm"],
            "recent_execution_log": run_data["execution_log_tail"],
        }

        # -------------------------------------------------------------
        # BLOCO 3: Métricas derivadas dos contadores do FlowMonitor
        # -------------------------------------------------------------
        block3 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "flowmonitor_available": evidence.get("flowmonitor", False),
            "throughput_mbps": run_data["throughput_mbps"],
            "mean_delay_ms": run_data["mean_delay_ms"],
            "loss_ratio_pct": run_data["loss_ratio_pct"],
            "total_packets_tx": run_data["total_tx_pkts"],
            "total_packets_rx": run_data["total_rx_pkts"],
            "total_packets_lost": run_data["total_lost_pkts"],
            "prb_utilization_pct": None,
            "sla_evaluation": "unavailable_without_per_flow_qos_configuration",
            "conflict_detection": "unavailable_without_rdl_decision_artifact",
        }

        # -------------------------------------------------------------
        # BLOCO 4: Topologia de fluxos observados pelo FlowMonitor
        # -------------------------------------------------------------
        nodes_by_ip = {}
        edges = []
        for flow in ues:
            for address in (flow["src_ip"], flow["dst_ip"]):
                if address:
                    nodes_by_ip[address] = {
                        "id": address,
                        "label": address,
                        "type": "IP endpoint",
                    }
            if flow["src_ip"] and flow["dst_ip"]:
                edges.append({
                    "source": flow["src_ip"],
                    "target": flow["dst_ip"],
                    "rel": f"FLOW_{flow['flow_id']}",
                })
        nodes = list(nodes_by_ip.values())

        block4 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "topology_source": "FlowMonitor IPv4FlowClassifier",
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "active_conflict_cycles": None,
            "density": (
                round(len(edges) / (len(nodes) * (len(nodes) - 1)), 3)
                if len(nodes) > 1
                else 0.0
            ),
            "nodes": nodes,
            "edges": edges,
        }

        # -------------------------------------------------------------
        # BLOCO 5: Módulo de Refinamento & Segurança (H-RDL Safety Guards)
        # -------------------------------------------------------------
        block5 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "decision_artifact_available": evidence["rdl_decision"],
            "decision_status": (
                "artifact available in this run"
                if evidence["rdl_decision"]
                else "not emitted by this run"
            ),
        }

        # -------------------------------------------------------------
        # BLOCO 6: Evidências E2SM-RC produzidas nesta execução
        # -------------------------------------------------------------
        block6 = {
            "scenario_id": run_data["scenario_id"],
            "scenario_title": scen_meta["title"],
            "run_dir": run_data["run_dir"],
            "control_request_available": evidence["control_request"],
            "control_ack_available": evidence["control_ack"],
            "closed_loop_evidence_available": (
                evidence["control_request"] and evidence["control_ack"]
            ),
        }

        return {
            "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "active_scenario_id": run_data["scenario_id"],
            "active_scenario_title": scen_meta["title"],
            "active_run_dir": run_data["run_dir"],
            "run_status": run_data["run_status"],
            "run_status_message": run_data["status_message"],
            "run_status_updated_at": run_data["run_status_updated_at"],
            "evidence": evidence,
            "block1_ran_registration": block1,
            "block2_protocol_signaling": block2,
            "block3_perception_module": block3,
            "block4_knowledge_graph": block4,
            "block5_refinement_module": block5,
            "block6_ran_control_action": block6,
        }


# Instância global compartilhada
real_telemetry_provider = RealDataTelemetryProvider()
