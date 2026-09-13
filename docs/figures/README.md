# Catálogo Oficial da Suíte de Figuras Científicas XApp-RDL (S0 a S15)

Este documento registra a rastreabilidade completa de todas as **32 figuras científicas de arquitetura e cenários experimentais** mantidas em `docs/figures/02_cenarios_e_topologias/`, cobrindo os cenários da Fase 1 ($S_0$ a $S_8$) e a suíte avançada 5G-A/6G ($S_9$ a $S_{15}$), cada um disponível em **Tema Claro (Light)** e **Tema Escuro (Dark)**.

---

## 1. Diretriz Científica de Isenção de Dados Sintéticos

Conforme a regra do **Prompt Master IEEE/ACM XApp-RDL**:
> *"Experimental scenario — metrics shown are monitored variables, not experimental results."*

Nenhuma figura contém números aleatórios, curvas sintetizadas ou metas tratadas como resultados medidos. As figuras representam diagramas técnicos de arquitetura, topologia RAN, pilha Near-RT RIC / H-RDL, vetor de telemetria/controle E2 e marcadores temporais ($t_{conflict} \dots t_{recovery}$).

---

## 2. Mapeamento Completo por Cenário ($S_0$ a $S_{15}$)

| ID | Nome Oficial do Cenário | Fase | xApps Participantes | Figura Tema Claro | Figura Tema Escuro | Documento de Referência |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- |
| **S0** | No-Conflict Control | Fase 1 | `QoS/Slicing xApp`, `Traffic Steering xApp` | [`s0_architecture_light.png`](02_cenarios_e_topologias/s0_architecture_light.png) | [`s0_architecture_dark.png`](02_cenarios_e_topologias/s0_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S1** | Direct PRB Conflict | Fase 1 | `QoS/Slicing xApp`, `Energy Saving xApp` | [`s1_architecture_light.png`](02_cenarios_e_topologias/s1_architecture_light.png) | [`s1_architecture_dark.png`](02_cenarios_e_topologias/s1_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S2** | Energy Saving × QoS | Fase 1 | `Energy Saving xApp`, `QoS/Slicing xApp` | [`s2_architecture_light.png`](02_cenarios_e_topologias/s2_architecture_light.png) | [`s2_architecture_dark.png`](02_cenarios_e_topologias/s2_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S3** | Traffic Steering × Slicing | Fase 1 | `Traffic Steering xApp`, `QoS/Slicing xApp` | [`s3_architecture_light.png`](02_cenarios_e_topologias/s3_architecture_light.png) | [`s3_architecture_dark.png`](02_cenarios_e_topologias/s3_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S4** | Traffic Steering × Energy Saving | Fase 1 | `Traffic Steering xApp`, `Energy Saving xApp` | [`s4_architecture_light.png`](02_cenarios_e_topologias/s4_architecture_light.png) | [`s4_architecture_dark.png`](02_cenarios_e_topologias/s4_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S5** | Temporal Ping-Pong | Fase 1 | `Traffic Steering / MRO xApp`, `Energy / QoS xApp` | [`s5_architecture_light.png`](02_cenarios_e_topologias/s5_architecture_light.png) | [`s5_architecture_dark.png`](02_cenarios_e_topologias/s5_architecture_dark.png) | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) |
| **S6** | Multi-xApp Conflict Storm | Fase 1 | `QoS`, `Traffic Steering`, `Energy`, `Load Balancer`, `Beamformer` | [`s6_architecture_light.png`](02_cenarios_e_topologias/s6_architecture_light.png) | [`s6_architecture_dark.png`](02_cenarios_e_topologias/s6_architecture_dark.png) | [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) |
| **S7** | Fault / Rogue xApp / Adversarial Control | Fase 1 | `xApps Legítimas`, `Rogue / Fault-Injection xApp` | [`s7_architecture_light.png`](02_cenarios_e_topologias/s7_architecture_light.png) | [`s7_architecture_dark.png`](02_cenarios_e_topologias/s7_architecture_dark.png) | [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) |
| **S8** | Real NORI Closed Loop | Fase 1 | `KPM Monitor xApp`, `Traffic Steering xApp`, `H-RDL Core` | [`s8_architecture_light.png`](02_cenarios_e_topologias/s8_architecture_light.png) | [`s8_architecture_dark.png`](02_cenarios_e_topologias/s8_architecture_dark.png) | [`docs/relatorio_simulacoes_continuas_ns3_5glena_nori.md`](../relatorio_simulacoes_continuas_ns3_5glena_nori.md) |
| **S9** | NTN Terrestrial–Satellite Conflict | Fase 2 / 6G | `NTN Steering xApp`, `QoS / Latency Slicing`, `Load Balancer` | [`s9_architecture_light.png`](02_cenarios_e_topologias/s9_architecture_light.png) | [`s9_architecture_dark.png`](02_cenarios_e_topologias/s9_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S10** | UAV / Flying gNB / Swarm | Fase 2 / 6G | `UAV Mobility xApp`, `Energy Saving xApp`, `Load Balancer` | [`s10_architecture_light.png`](02_cenarios_e_topologias/s10_architecture_light.png) | [`s10_architecture_dark.png`](02_cenarios_e_topologias/s10_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S11** | V2X High-Mobility Platoon | Fase 2 / 6G | `Traffic Steering xApp`, `Mobility / MRO xApp`, `Platoon QoS xApp` | [`s11_architecture_light.png`](02_cenarios_e_topologias/s11_architecture_light.png) | [`s11_architecture_dark.png`](02_cenarios_e_topologias/s11_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S12** | IIoT / TSN Mission-Critical | Fase 2 / 6G | `Industrial QoS xApp`, `Energy Saving xApp`, `Load Balancer` | [`s12_architecture_light.png`](02_cenarios_e_topologias/s12_architecture_light.png) | [`s12_architecture_dark.png`](02_cenarios_e_topologias/s12_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S13** | SAGIN Multi-Domain | Fase 3 / 6G | `NTN Steering`, `UAV Coordination`, `QoS Slicing`, `Energy Saving` | [`s13_architecture_light.png`](02_cenarios_e_topologias/s13_architecture_light.png) | [`s13_architecture_dark.png`](02_cenarios_e_topologias/s13_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S14** | ISAC Sensing × Communication | Fase 3 / 6G | `ISAC / Sensing xApp`, `eMBB / QoS xApp`, `Beamformer xApp` | [`s14_architecture_light.png`](02_cenarios_e_topologias/s14_architecture_light.png) | [`s14_architecture_dark.png`](02_cenarios_e_topologias/s14_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |
| **S15** | Cross-Tier Governance / Anti-Rogue | Fase 3 / 6G | `QoS`, `Steering`, `Energy`, `Load Balancer`, `Beamformer`, `ISAC`, `Rogue xApp` | [`s15_architecture_light.png`](02_cenarios_e_topologias/s15_architecture_light.png) | [`s15_architecture_dark.png`](02_cenarios_e_topologias/s15_architecture_dark.png) | [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) |

---

## 3. Rastreabilidade de Arquivos no Repositório

```text
docs/figures/
├── README.md                                       # Catálogo consolidado oficial S0-S15 (32 figuras)
└── 02_cenarios_e_topologias/
    ├── s0_architecture_light.png / s0_architecture_dark.png
    ├── s1_architecture_light.png / s1_architecture_dark.png
    ├── s2_architecture_light.png / s2_architecture_dark.png
    ├── s3_architecture_light.png / s3_architecture_dark.png
    ├── s4_architecture_light.png / s4_architecture_dark.png
    ├── s5_architecture_light.png / s5_architecture_dark.png
    ├── s6_architecture_light.png / s6_architecture_dark.png
    ├── s7_architecture_light.png / s7_architecture_dark.png
    ├── s8_architecture_light.png / s8_architecture_dark.png
    ├── s9_architecture_light.png / s9_architecture_dark.png
    ├── s10_architecture_light.png / s10_architecture_dark.png
    ├── s11_architecture_light.png / s11_architecture_dark.png
    ├── s12_architecture_light.png / s12_architecture_dark.png
    ├── s13_architecture_light.png / s13_architecture_dark.png
    ├── s14_architecture_light.png / s14_architecture_dark.png
    └── s15_architecture_light.png / s15_architecture_dark.png
```
