#!/usr/bin/env python3
"""
Script de Download e Sincronização das Figuras Canônicas de Alta Qualidade do XApp-RDL-F2.
Baixa todas as figuras do repositório georgebarbosa3090/XApp-RDL-F2 (branch main).
"""

import os
import urllib.request

DEST_DIR = os.path.join("docs", "figures", "02_cenarios_e_topologias")
os.makedirs(DEST_DIR, exist_ok=True)

BASE_URL = "https://raw.githubusercontent.com/georgebarbosa3090/XApp-RDL-F2/main/docs/figures/02_cenarios_e_topologias/"

FIGURE_FILES = [
    "fig_topologia_cenarios_ns3.png",
    "cenario_1_topologia_tvs_conflict.png",
    "cenario_2_tradeoff_energy_vs_qos.png",
    "fig_cenario1_energy_vs_qos.png",
    "fig_cenario2_tvs_conflict.png",
    "scenario_1_eevs_energy_vs_qos.png",
    "scenario_1_eevs_energy_vs_qos_light.png",
    "scenario_2_tvs_traffic_steering_slicing.png",
    "scenario_2_tvs_traffic_steering_slicing_light.png",
    "scenario_3_5ga_multicarrier_mimo.png",
    "scenario_3_5ga_multicarrier_mimo_light.png",
    "scenario_4_6g_isac_sensing_coexistence.png",
    "scenario_4_6g_isac_sensing_coexistence_light.png",
    "scenario_5_6g_cross_tier_governance.png",
    "scenario_5_6g_cross_tier_governance_light.png"
]

def download_figures():
    print("=" * 80)
    print(" BAIXANDO FIGURAS CANÔNICAS DE ALTA QUALIDADE DO XAPP-RDL-F2")
    print("=" * 80)
    
    for filename in FIGURE_FILES:
        url = BASE_URL + filename
        dest_path = os.path.join(DEST_DIR, filename)
        print(f"[+] Baixando {filename} ...")
        try:
            urllib.request.urlretrieve(url, dest_path)
            file_size = os.path.getsize(dest_path)
            print(f"    [OK] Salvo ({file_size / 1024:.1f} KB)")
        except Exception as e:
            print(f"    [ERRO] Falha ao baixar {filename}: {e}")

if __name__ == "__main__":
    download_figures()
