#!/usr/bin/env python3
import os
import sys
import glob
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "experiments", "results", "s0_s15_simulations")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

def parse_flowmonitor_xml(xml_path: str) -> Dict[str, Any]:
    if not os.path.exists(xml_path):
        return {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        flow_stats = root.find("FlowStats")
        if flow_stats is None:
            return {}

        flows = []
        total_tx_bytes = 0
        total_rx_bytes = 0
        total_tx_pkts = 0
        total_rx_pkts = 0
        total_lost_pkts = 0
        total_delay_sum_ns = 0.0

        for flow in flow_stats.findall("Flow"):
            tx_b = int(flow.attrib.get("txBytes", 0))
            rx_b = int(flow.attrib.get("rxBytes", 0))
            tx_p = int(flow.attrib.get("txPackets", 0))
            rx_p = int(flow.attrib.get("rxPackets", 0))
            lost_p = int(flow.attrib.get("lostPackets", 0))
            delay_str = flow.attrib.get("delaySum", "+0.0ns").rstrip("ns").lstrip("+")
            try:
                delay_ns = float(delay_str)
            except ValueError:
                delay_ns = 0.0

            total_tx_bytes += tx_b
            total_rx_bytes += rx_b
            total_tx_pkts += tx_p
            total_rx_pkts += rx_p
            total_lost_pkts += lost_p
            total_delay_sum_ns += delay_ns

            mean_delay_ms = (delay_ns / (rx_p * 1e6)) if rx_p > 0 else 0.0
            pdr = (rx_p / tx_p * 100.0) if tx_p > 0 else 0.0

            flows.append({
                "flow_id": int(flow.attrib.get("flowId", 0)),
                "tx_bytes": tx_b,
                "rx_bytes": rx_b,
                "tx_packets": tx_p,
                "rx_packets": rx_p,
                "lost_packets": lost_p,
                "mean_delay_ms": round(mean_delay_ms, 3),
                "pdr_pct": round(pdr, 2)
            })

        mean_delay_global_ms = (total_delay_sum_ns / (total_rx_pkts * 1e6)) if total_rx_pkts > 0 else 0.0
        global_pdr = (total_rx_pkts / total_tx_pkts * 100.0) if total_tx_pkts > 0 else 0.0

        return {
            "num_flows": len(flows),
            "total_tx_bytes": total_tx_bytes,
            "total_rx_bytes": total_rx_bytes,
            "total_tx_pkts": total_tx_pkts,
            "total_rx_pkts": total_rx_pkts,
            "total_lost_pkts": total_lost_pkts,
            "global_pdr_pct": round(global_pdr, 2),
            "global_mean_delay_ms": round(mean_delay_global_ms, 3),
            "flows": flows
        }
    except Exception as e:
        print(f"[ERRO] Falha ao processar XML {xml_path}: {e}")
        return {}

def generate_report():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    xml_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.xml")))
    csv_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.csv")))

    report_path_p1 = os.path.join(DOCS_DIR, "12_relatorio_experimental_ns3_flowmonitor_s0_s15.md")

    content = []
    content.append("# Relatório Experimental e Rastreabilidade do ns-3 FlowMonitor (Cenários S0 a S15)")
    content.append("")
    content.append("## 1. Proveniência e Conformidade Estrita com o FlowMonitor")
    content.append("")
    content.append("Este relatório é compilado diretamente a partir dos artefatos XML e CSV gerados pelo módulo `FlowMonitor` do simulador **ns-3.48 / 5G-LENA v5.1 / NORI** durante a execução da suíte de cenários.")
    content.append("")
    content.append(f"* **Diretório de Traces Brutos:** `{RESULTS_DIR}`")
    content.append(f"* **Total de Arquivos XML Encontrados:** {len(xml_files)}")
    content.append(f"* **Total de Arquivos CSV Encontrados:** {len(csv_files)}")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## 2. Tabela Consolidada de Métricas Físicas por Cenário")
    content.append("")
    content.append("| Cenário / Arquivo | Fluxos Monitorados | Pacotes TX | Pacotes RX | Pacotes Perdidos | PDR (%) | Latência Média (ms) |")
    content.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    if not xml_files:
        content.append("| *Nenhum XML de FlowMonitor detectado ainda no diretório de resultados* | - | - | - | - | - | - |")
    else:
        for f in xml_files:
            bname = os.path.basename(f)
            data = parse_flowmonitor_xml(f)
            if data:
                content.append(f"| `{bname}` | {data['num_flows']} | {data['total_tx_pkts']} | {data['total_rx_pkts']} | {data['total_lost_pkts']} | **{data['global_pdr_pct']}%** | **{data['global_mean_delay_ms']} ms** |")

    content.append("")
    content.append("---")
    content.append("")
    content.append("## 3. Detalhamento dos Fluxos por Cenário")
    content.append("")

    for f in xml_files:
        bname = os.path.basename(f)
        data = parse_flowmonitor_xml(f)
        if data:
            content.append(f"### Cenário: `{bname}`")
            content.append("")
            content.append(f"* **Volume Total Transferido:** {data['total_rx_bytes'] / (1024*1024):.2f} MB")
            content.append(f"* **Taxa de Entrega Global (PDR):** {data['global_pdr_pct']}%")
            content.append(f"* **Atraso Médio Fim-a-Fim:** {data['global_mean_delay_ms']} ms")
            content.append("")
            content.append("| Flow ID | Pacotes TX | Pacotes RX | Perdas | PDR (%) | Atraso Médio (ms) |")
            content.append("| :---: | :---: | :---: | :---: | :---: | :---: |")
            for fl in data["flows"][:10]:
                content.append(f"| {fl['flow_id']} | {fl['tx_packets']} | {fl['rx_packets']} | {fl['lost_packets']} | {fl['pdr_pct']}% | {fl['mean_delay_ms']} ms |")
            if len(data["flows"]) > 10:
                content.append(f"| ... | ... | ... | ... | ... | *(+ {len(data['flows']) - 10} fluxos adicionais)* |")
            content.append("")

    content.append("---")
    content.append("")
    content.append("## 4. Instruções para Regeneração dos Traces")
    content.append("")
    content.append("Para reexecutar a suíte no ns-3 e reprocessar este documento:")
    content.append("")
    content.append("```bash")
    content.append("bash simulations/ns3/run_all_s0_s15_simulations.sh all")
    content.append("python3 scripts/generate_ns3_flowmonitor_markdown_report.py")
    content.append("```")
    content.append("")

    report_text = "\n".join(content)
    with open(report_path_p1, "w", encoding="utf-8") as f:
        f.write(report_text)

    p2_docs = os.path.abspath(os.path.join(BASE_DIR, "..", "iqos-xapp-rdl-phase2", "docs"))
    if os.path.exists(p2_docs):
        report_path_p2 = os.path.join(p2_docs, "20_relatorio_experimental_ns3_flowmonitor_s0_s15.md")
        with open(report_path_p2, "w", encoding="utf-8") as f:
            f.write(report_text)

    print(f"[OK] Relatório Markdown compilado com sucesso: {report_path_p1}")

if __name__ == "__main__":
    generate_report()
