# Catálogo Oficial de Figuras e Arquitetura XApp-RDL

Este diretório mantém os artefatos visuais de arquitetura e topologia do projeto **XApp-RDL-F1**.

---

## 1. Diretrizes de Governança Visual e Isenção Científica

De acordo com o **O-RAN OpenRAN@Brasil Researcher Skill (v1.1.0)**:
- Nenhuma figura contém dados numéricos sintéticos ou resultados simulados não medidos.
- Artefatos visuais representam exclusivamente abstrações de arquitetura, barramento RMR, terminação E2, pilhas de protocolo e topologias de rede.

---

## 2. Estrutura e Catálogo Oficial de Cenários (S1–S15)

```text
docs/figures/
├── README.md                                       # Catálogo de rastreabilidade de figuras
├── 01_arquitetura_e_modelagem/                     # Diagramas de fluxo e arquitetura de sistema
└── 02_cenarios_e_topologias/                       # Topologias espaciais e cenários experimentais S1-S15
```

### Lista de Figuras Conceituais 3D e Ilustrativas

| Cenário | Título / Descrição | Arquivo Imagem |
| :--- | :--- | :--- |
| **S1** | Energy Saving vs QoS (EEVS) (Dark / Light) | [`s1_eevs_energy_vs_qos_dark.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s1_eevs_energy_vs_qos_dark.png) / [`s1_eevs_energy_vs_qos_light.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s1_eevs_energy_vs_qos_light.png) |
| **S2** | Traffic Steering vs Slicing (TVS) (Dark / Light) | [`s2_tvs_traffic_steering_dark.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s2_tvs_traffic_steering_dark.png) / [`s2_tvs_traffic_steering_light.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s2_tvs_traffic_steering_light.png) |
| **S3** | Multi-Slice Traffic Steering vs Slicing | [`s3_multi_slice_traffic_steering.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s3_multi_slice_traffic_steering.png) |
| **S7** | 5G-Advanced Channel Overlap & Multicarrier MIMO | [`s7_5ga_channel_overlap_mimo.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s7_5ga_channel_overlap_mimo.png) / [`s7_5ga_multicarrier_mimo_dark.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s7_5ga_multicarrier_mimo_dark.png) |
| **S8** | 6G ISAC Sensing Coexistence & Urban Green Sensing | [`s8_6g_isac_urban_green_sensing.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s8_6g_isac_urban_green_sensing.png) / [`s8_urban_environmental_sensing.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s8_urban_environmental_sensing.png) / [`s8_6g_isac_sensing_dark.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s8_6g_isac_sensing_dark.png) |
| **S9** | NTN Orbital Handover & Satellite Connectivity | [`s9_ntn_orbital_handover.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s9_ntn_orbital_handover.png) |
| **S10** | UAV Swarm Stadium Coverage & Battery Constraints | [`s10_uav_swarm_stadium_coverage.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s10_uav_swarm_stadium_coverage.png) |
| **S11** | V2X Highway Ping-Pong Storm & Platoon Protection | [`s11_v2x_highway_pingpong_storm.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s11_v2x_highway_pingpong_storm.png) |
| **S12** | IIoT Zero-Jitter Robotic Slicing & URLLC | [`s12_iiot_zero_jitter_robotic_slicing.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s12_iiot_zero_jitter_robotic_slicing.png) |
| **S13** | Disaster Rescue Heterogeneous Mesh (UAV + LEO) | [`s13_disaster_rescue_heterogeneous_mesh.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s13_disaster_rescue_heterogeneous_mesh.png) |
| **S14** | Rural Agriculture 4.0 & Environmental Sensing | [`s14_rural_agriculture_sensing.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s14_rural_agriculture_sensing.png) |
| **S15** | 6G Conflict Storm in Dense Smart City | [`s15_6g_dense_city_conflict_storm.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s15_6g_dense_city_conflict_storm.png) / [`s15_6g_cross_tier_governance_dark.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s15_6g_cross_tier_governance_dark.png) |

---

### Lista de Figuras de Topologias Espaciais 2D Geométricas (Planos Espaciais em Metros — Estilo Figura 5)

| Cenário | Descrição da Topologia Espacial 2D | Arquivo Imagem |
| :--- | :--- | :--- |
| **S0** | Topologia Base sem Conflito no ns-3 (2 gNodeBs, 30 UEs Fatiados) | [`s0_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s0_topologia_espacial_plano_2d.png) |
| **S1** | Topologia Espacial Parametrizada & Zona de Contenção de PRBs (200m x 120m) | [`s1_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s1_topologia_espacial_plano_2d.png) |
| **S2** | Trade-off Energy Saving vs. QoS & Modo Sleep Pendente | [`s2_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s2_topologia_espacial_plano_2d.png) |
| **S3** | Corredor de Mobilidade Veicular & Janela de Handover no ns-3 | [`s3_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s3_topologia_espacial_plano_2d.png) |
| **S4** | Controle Temporal Anti Ping-Pong & Janela de Histerese | [`s4_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s4_topologia_espacial_plano_2d.png) |
| **S5** | Tempestade de Conflitos Multi-Slice & Hotspots de Sobrecarga | [`s5_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s5_topologia_espacial_plano_2d.png) |
| **S6** | Protection Active, Safety Guard & Mitigação de Ação Indevida | [`s6_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s6_topologia_espacial_plano_2d.png) |
| **S7** | Malha Fechada NORI + Interface E2 (SCTP 36422) Closed-Loop | [`s7_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s7_topologia_espacial_plano_2d.png) |
| **S8** | Extensão Integrada NTN (Satélite LEO) + UAV + Corredor V2X | [`s8_topologia_espacial_plano_2d.png`](file:///c:/Users/georg/XApp-RDL-F1/docs/figures/02_cenarios_e_topologias/s8_topologia_espacial_plano_2d.png) |


