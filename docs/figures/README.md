# Catálogo Oficial de Figuras e Arquitetura XApp-RDL

Este diretório mantém os artefatos visuais de arquitetura, topologia e modelos conceituais do projeto **XApp-RDL-F1**.

---

## 1. Diretrizes de Governança Visual e Firewall Epistemológico

De acordo com o **Firewall de Evidência e Classificação Epistemológica**:
- **Resultados Empíricos Puros (Fig. 01 a 25)**: Armazenados exclusivamente em `reports/figures/` (e espelhados em `docs/figures/03_resultados_e_benchmarks/`). São originados estritamente dos logs brutos de simulação ns-3.48 / FlowMonitor para as 30 sementes estocásticas canônicas.
- **Modelos Analíticos e Conceituais (Fig. 26 a 30)**: Armazenados exclusivamente em `docs/figures/01_modelos_analiticos_e_conceituais/`. Representam modelos matemáticos contínuos, trade-offs analíticos e diagramas de envelopes temporais, explicitamente rotulados como `[MODELO ANALÍTICO CONCEITUAL]`.
- **Topologias e Cenários (S0 a S15)**: Armazenados em `docs/figures/02_cenarios_e_topologias/` como coordenadas espaciais 2D exatas da topologia de simulação.
- **Arquitetura de Governança**: Armazenada em `docs/figures/01_arquitetura_e_modelagem/`.

---

## 2. Estrutura de Diretórios

```text
docs/figures/
├── README.md                                       # Catálogo de rastreabilidade e governança visual
├── 01_arquitetura_e_modelagem/                     # Diagramas de fluxo e arquitetura de sistema O-RAN
├── 01_modelos_analiticos_e_conceituais/             # Figuras analíticas/conceituais de suporte (Fig. 26-30)
│   ├── fig_26_jain_fairness_dynamics.png           # Dinâmica de Jain Fairness [MODELO ANALÍTICO]
│   ├── fig_27_energy_vs_qos_tradeoff_eevs.png      # Superfície 3D de Eficiência Energética [MODELO ANALÍTICO]
│   ├── fig_28_cross_tier_governance_latency_envelope.png # Envelopes temporais rApp/xApp/dApp [MODELO CONCEITUAL]
│   ├── fig_29_resilience_e2_timeout_recovery.png   # Tolerância a falhas E2 e timeout SCTP [MODELO CONCEITUAL]
│   └── fig_30_sbrc_multidimensional_radar.png      # Radar de desempenho consolidado [MODELO ANALÍTICO]
├── 02_cenarios_e_topologias/                       # Topologias espaciais e cenários experimentais S0-S15
└── 03_resultados_e_benchmarks/                     # Figuras empíricas geradas pelo ns-3 (Fig. 01 a 25)
```

---

## 3. Catálogo Oficial de Modelos Analíticos e Conceituais (Fig. 26 a 30)

| Figura | Título / Descrição | Classificação Epistemológica | Arquivo Imagem |
| :--- | :--- | :--- | :--- |
| **Fig 26** | Dinâmica Temporal do Índice de Jain ($J \ge 0,94$) | Modelo Analítico | `01_modelos_analiticos_e_conceituais/fig_26_jain_fairness_dynamics.png` |
| **Fig 27** | Superfície 3D de Eficiência Energética vs Potência | Modelo Analítico | `01_modelos_analiticos_e_conceituais/fig_27_energy_vs_qos_tradeoff_eevs.png` |
| **Fig 28** | Envelope de Latência e Escalas Temporais O-RAN | Modelo Conceitual | `01_modelos_analiticos_e_conceituais/fig_28_cross_tier_governance_latency_envelope.png` |
| **Fig 29** | Resiliência e Recuperação sob Injeção de Falhas E2 | Modelo Conceitual | `01_modelos_analiticos_e_conceituais/fig_29_resilience_e2_timeout_recovery.png` |
| **Fig 30** | Radar Multidimensional de Desempenho (8 Dimensões) | Modelo Analítico | `01_modelos_analiticos_e_conceituais/fig_30_sbrc_multidimensional_radar.png` |

---

## 4. Catálogo Oficial de Cenários e Topologias 2D (S0–S15)

| Cenário | Descrição da Topologia Espacial 2D | Arquivo Imagem |
| :--- | :--- | :--- |
| **S0** | Topologia Base sem Conflito no ns-3 (2 gNodeBs, 30 UEs Fatiados) | `02_cenarios_e_topologias/s0_topologia_espacial_plano_2d.png` |
| **S1** | Topologia Espacial Parametrizada & Zona de Contenção de PRBs (200m x 120m) | `02_cenarios_e_topologias/s1_topologia_espacial_plano_2d.png` |
| **S2** | Trade-off Energy Saving vs. QoS & Modo Sleep Pendente | `02_cenarios_e_topologias/s2_topologia_espacial_plano_2d.png` |
| **S3** | Corredor de Mobilidade Veicular & Janela de Handover no ns-3 | `02_cenarios_e_topologias/s3_topologia_espacial_plano_2d.png` |
| **S4** | Controle Temporal Anti Ping-Pong & Janela de Histerese | `02_cenarios_e_topologias/s4_topologia_espacial_plano_2d.png` |
| **S5** | Tempestade de Conflitos Multi-Slice & Hotspots de Sobrecarga | `02_cenarios_e_topologias/s5_topologia_espacial_plano_2d.png` |
| **S6** | Protection Active, Safety Guard & Mitigação de Ação Indevida | `02_cenarios_e_topologias/s6_topologia_espacial_plano_2d.png` |
| **S7** | Malha Fechada NORI + Interface E2 (SCTP 36422) Closed-Loop | `02_cenarios_e_topologias/s7_topologia_espacial_plano_2d.png` |
| **S8** | Extensão Integrada NTN (Satélite LEO) + UAV + Corredor V2X | `02_cenarios_e_topologias/s8_topologia_espacial_plano_2d.png` |


