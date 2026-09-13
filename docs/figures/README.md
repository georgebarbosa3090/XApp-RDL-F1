# Catálogo Completo de Figuras de Topologia Espacial e Cenários (S0 a S15)

Este documento registra a rastreabilidade completa de todas as **21 figuras topológicas e cenariais** mantidas em `docs/figures/02_cenarios_e_topologias/`, cobrindo o núcleo da Fase 1 ($S_0$ a $S_8$) e a suíte avançada 5G-A/6G ($S_9$ a $S_{15}$), incluindo todas as xApps de Terceiros e xApps Propostas/Experimentais.

---

## 1. Tabela de Mapeamento Completo por Cenário e xApp Relacionada

| Identificador | Nome do Cenário | xApps Relacionadas (Terceiros / Propostas) | Figura Tema Claro | Figura Tema Escuro | Documento de Referência |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **S0** | Passthrough Limpo / Topologia Geral | `kpimon`, `qos-xslice`, `traffic-steering` | [`fig_topologia_cenarios_ns3.png`](02_cenarios_e_topologias/fig_topologia_cenarios_ns3.png) | [`fig_topologia_cenarios_ns3.png`](02_cenarios_e_topologias/fig_topologia_cenarios_ns3.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S1** | Trade-Off EEVS (Energy Saver x QoS) | `energy-saving`, `qos-xslice` | [`scenario_1_eevs_energy_vs_qos_light.png`](02_cenarios_e_topologias/scenario_1_eevs_energy_vs_qos_light.png) | [`scenario_1_eevs_energy_vs_qos.png`](02_cenarios_e_topologias/scenario_1_eevs_energy_vs_qos.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S2** | Conflito TVS (Traffic Steering x Slice) | `traffic-steering`, `qos-xslice` | [`scenario_2_tvs_traffic_steering_slicing_light.png`](02_cenarios_e_topologias/scenario_2_tvs_traffic_steering_slicing_light.png) | [`scenario_2_tvs_traffic_steering_slicing.png`](02_cenarios_e_topologias/scenario_2_tvs_traffic_steering_slicing.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S3** | 5G-A Multi-Carrier MIMO | `load-balancer`, `beamformer` *(PROPOSED)* | [`scenario_3_5ga_multicarrier_mimo_light.png`](02_cenarios_e_topologias/scenario_3_5ga_multicarrier_mimo_light.png) | [`scenario_3_5ga_multicarrier_mimo.png`](02_cenarios_e_topologias/scenario_3_5ga_multicarrier_mimo.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S4** | 6G ISAC Radar & Coexistência | `isac-radar` *(PROPOSED)* | [`scenario_4_6g_isac_sensing_coexistence_light.png`](02_cenarios_e_topologias/scenario_4_6g_isac_sensing_coexistence_light.png) | [`scenario_4_6g_isac_sensing_coexistence.png`](02_cenarios_e_topologias/scenario_4_6g_isac_sensing_coexistence.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S5** | Governança Cross-Tier 6G | `sec-guardian` *(PROPOSED)* | [`scenario_5_6g_cross_tier_governance_light.png`](02_cenarios_e_topologias/scenario_5_6g_cross_tier_governance_light.png) | [`scenario_5_6g_cross_tier_governance.png`](02_cenarios_e_topologias/scenario_5_6g_cross_tier_governance.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S9** | NTN Orbital Handover & Doppler | `ntn-steering`, `satellite-ho` *(PROPOSED)* | [`scenario_9_ntn_orbital_handover_light.png`](02_cenarios_e_topologias/scenario_9_ntn_orbital_handover_light.png) | [`scenario_9_ntn_orbital_handover.png`](02_cenarios_e_topologias/scenario_9_ntn_orbital_handover.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S10** | UAV Swarm Coverage & Battery | `uav-mobility`, `energy-conserver-uav` *(PROPOSED)* | [`scenario_10_uav_swarm_coverage_light.png`](02_cenarios_e_topologias/scenario_10_uav_swarm_coverage_light.png) | [`scenario_10_uav_swarm_coverage.png`](02_cenarios_e_topologias/scenario_10_uav_swarm_coverage.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S11** | V2X Highway Platoon URLLC | `v2x-mobility`, `platoon-qos` *(PROPOSED)* | [`scenario_11_v2x_highway_platoon_light.png`](02_cenarios_e_topologias/scenario_11_v2x_highway_platoon_light.png) | [`scenario_11_v2x_highway_platoon.png`](02_cenarios_e_topologias/scenario_11_v2x_highway_platoon.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S12** | IIoT Factory TSN Determinística | `industrial-qos` *(PROPOSED)* | [`scenario_12_iiot_factory_tsn_light.png`](02_cenarios_e_topologias/scenario_12_iiot_factory_tsn_light.png) | [`scenario_12_iiot_factory_tsn.png`](02_cenarios_e_topologias/scenario_12_iiot_factory_tsn.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S13** | Emergency SAGIN Multi-Domain | `rescue-qos` *(PROPOSED)* | [`scenario_13_emergency_sagin_multidomain_light.png`](02_cenarios_e_topologias/scenario_13_emergency_sagin_multidomain_light.png) | [`scenario_13_emergency_sagin_multidomain.png`](02_cenarios_e_topologias/scenario_13_emergency_sagin_multidomain.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |

---

## 2. Rastreabilidade Arquitetural Geral

```text
docs/figures/
├── README.md                                       # Catálogo consolidado de rastreabilidade S0-S15
├── 01_arquitetura_e_modelagem/
│   └── fig_fluxo_funcional_arquitetura_rdl.png      # Fluxo funcional do middleware H-RDL
└── 02_cenarios_e_topologias/
    ├── fig_topologia_cenarios_ns3.png               # Topologia espacial geral
    ├── scenario_1_eevs_energy_vs_qos*.png           # Cenário S1 (EEVS)
    ├── scenario_2_tvs_traffic_steering_slicing*.png # Cenário S2 (TVS)
    ├── scenario_3_5ga_multicarrier_mimo*.png        # Cenário S3 (5G-A MIMO)
    ├── scenario_4_6g_isac_sensing_coexistence*.png  # Cenário S4 (6G ISAC)
    ├── scenario_5_6g_cross_tier_governance*.png     # Cenário S5 (Zero-Trust)
    ├── scenario_9_ntn_orbital_handover*.png         # Cenário S9 (NTN LEO)
    ├── scenario_10_uav_swarm_coverage*.png          # Cenário S10 (UAV Swarm)
    ├── scenario_11_v2x_highway_platoon*.png         # Cenário S11 (V2X 110km/h)
    ├── scenario_12_iiot_factory_tsn*.png            # Cenário S12 (IIoT TSN)
    └── scenario_13_emergency_sagin_multidomain*.png # Cenário S13 (SAGIN Emergência)
```
