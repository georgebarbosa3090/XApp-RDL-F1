# Catálogo Oficial de Figuras e Resultados Experimentais H-RDL (Fase 1)

Este diretório contém o acervo oficial, auditado e padronizado de figuras de arquitetura, topologias e resultados experimentais de co-simulação ns-3 / 5G-LENA / NORI / O-RAN Near-RT RIC para a **Fase 1 (H-RDL)** gerados **exclusivamente a partir da última rodada de simulação**.

Todas as figuras de resultados são disponibilizadas em alta fidelidade (300 DPI, `constrained_layout`, sem colisões de texto) com rastreabilidade direta à Matriz Canônica SSOT (`experiments/results/canonical_simulation_master.csv`).

---

## 📁 Estrutura Canônica de Diretórios

```
docs/figures/
├── 01_arquitetura_e_governanca/          # Diagramas conceituais e arquiteturais de governança O-RAN
├── 01_arquitetura_e_modelagem/           # Fluxo funcional e diagramas de blocos do pipeline
├── 01_modelos_analiticos_e_conceituais/  # Modelos matemáticos, dinâmica de equidade e trade-offs
├── 02_cenarios_e_topologias/             # Topologias espaciais e cenários canônicos (S0 a S15)
├── figures_manifest.json                 # Manifesto oficial de metadados das figuras canônicas
└── fig_01_*.png ... fig_37_*.png         # Figuras científicas 300 DPI da última simulação
```

---

## 📊 Catálogo de Figuras Científicas da Última Rodada de Simulação

| Arquivo | Título / Métrica Principal | Descrição Científica |
| :--- | :--- | :--- |
| `fig_01_causal_timeline.png` | Fechamento Causal E2 (Gate 4) | Linha do tempo dos 6 elos causais E2SM-KPM $\to$ H-RDL $\to$ E2SM-RC $\to$ MAC. |
| `fig_02_throughput_timeseries.png` | Série Temporal de Vazão | Dinâmica de throughput agregado por fatia (eMBB/URLLC) ao longo do tempo. |
| `fig_03_latency_ecdf.png` | ECDF de Latência URLLC | Função de Distribuição Cumulativa confrontada com o limiar de 10 ms. |
| `fig_04_throughput_boxplot.png` | Distribuição de Vazão | Dispersão estatística de vazão entre baselines B0 a B3 ($N=35$ execuções). |
| `fig_05_sla_violation_violin.png` | Taxa de Violação de SLA | Violin plots comparando a supressão de violações contratuais por baseline. |
| `fig_06_paired_seed_plot.png` | Comparações Pareadas Multi-Semente | Linhas pareadas por semente empírica demonstrando ganho determinístico. |
| `fig_07_effect_forest.png` | Forest Plot de Tamanhos de Efeito | Tamanhos de efeito de Cohen ($d_z$) com intervalos de confiança de 95%. |
| `fig_08_scenario_baseline_heatmap.png`| Heatmap Cenários vs Baselines | Matriz de desempenho transversal em todos os cenários (S0 a S15). |
| `fig_09_prb_slice_area.png` | Alocação de PRB por Fatia | Gráfico de área empilhada da partição espectral sob alta demanda. |
| `fig_10_sinr_throughput_hexbin.png` | Densidade Hexbin SINR vs Vazão | Distribuição de densidade conjunta de qualidade de canal e taxa útil. |
| `fig_11_mcs_bler.png` | BLER vs Esquema de Modulação (MCS) | Curvas de taxa de erro de bloco sob adaptação de enlace. |
| `fig_12_latency_breakdown.png` | Decomposição da Latência de Decisão| Tempo gasto em KPM, detecção, Nash, ASN.1 e despacho E2. |
| `fig_13_pareto.png` | Fronteira de Pareto Vazão vs Latência | Espaço multi-objetivo destacando a dominância das soluções RDL. |
| `fig_14_conflict_timeline.png` | Linha do Tempo de Resolução de Conflitos| Identificação e mitigação de colisões PRB/Potência ao longo do tempo. |
| `fig_15_action_churn.png` | Taxa de Oscilação (Action Churn) | Supressão de ping-pong e estabilização de políticas de controle. |
| `fig_16_mappo_convergence.png` | Convergência de Treinamento MAPPO | Curvas de recompensa e perda do crítico/ator no modelo cooperativo. |
| `fig_17_safety_cost.png` | Custo de Segurança (Safe-RL) | Restrições do multiplicador de Lagrange $\lambda$ garantindo $C_t \le d_{limit}$. |
| `fig_18_generalization_gap.png` | Gap de Generalização | Desempenho do modelo treinado em cenários não vistos (S6, S9, S10, S14). |
| `fig_19_crosslayer_pairplot.png` | Pairplot Cruzado Multi-Camada | Correlações cruzadas entre PHY (SINR), MAC (PRB) e RDL (Latência). |
| `fig_20_3d_pareto_surface.png` | Superfície de Pareto 3D | Superfície tridimensional Vazão $\times$ Latência $\times$ Eficiência Energética. |
| `fig_21_3d_gradient_scatter_latency_recovery.png`| Scatter 3D de Recuperação | Tempo de recuperação pós-falha versus sobrecarga e atraso. |
| `fig_22_cognitive_stages_waterfall.png` | Cascata dos Estágios Cognitivos | Decomposição sequencial do motor de inferência hierárquico L0 a L4. |
| `fig_23_decision_windows_tradeoff.png` | Trade-off de Janelas de Decisão | Impacto do intervalo de amostragem TTI nos tempos de resposta. |
| `fig_24_implicit_explicit_conflict_confusion.png`| Matriz de Confusão de Conflitos | Precisão e Recall na classificação de conflitos explícitos e implícitos. |
| `fig_25_ue_registration_breakdown.png`| Decomposição de UEs Conectados | Distribuição de terminais veiculares, industriais e de banda larga. |
| `fig_26_jain_fairness_dynamics.png` | Dinâmica de Equidade de Jain | Índice de Jain ao longo da carga celular demonstrando justiça de alocação. |
| `fig_27_energy_vs_qos_tradeoff_eevs.png`| Trade-off Energia vs QoS (EEVS) | Consumo de potência gNB (W) versus garantia estrita de SLA. |
| `fig_28_cross_tier_governance_latency_envelope.png`| Envelope de Latência Multi-Tier | Orçamento de tempo rApp (100ms) $\leftrightarrow$ xApp (10ms) $\leftrightarrow$ dApp (<1ms). |
| `fig_29_resilience_e2_timeout_recovery.png`| Resiliência a Falhas e Timeouts E2 | Recuperação automática com circuito de fallback (*Circuit Breaker*). |
| `fig_30_sbrc_multidimensional_radar.png`| Radar Multidimensional SBRC | Avaliação holística de 6 eixos (Vazão, Latência, SLA, Jain, Energia, Churn). |
| `fig_31_rich_demo_8stages_execution_timeline.png`| Timeline de Execução em 8 Estágios | Rastreio temporal dos 8 estágios do circuito fechado ao vivo. |
| `fig_32_conflict_storm_scalability_l0_l4.png`| Escalabilidade sob Tempestade de Conflitos| Sobrecarga de decisão sob saturação de 100 xApps concorrentes. |
| `fig_33_influx_grafana_realtime_closed_loop_recovery.png`| Telemetria InfluxDB/Grafana em Tempo Real| Curvas de monitoramento do painel operacional durante injeção de anomalia. |
| `fig_34_two_tier_dapp_bounding_box_envelope.png`| Envelope do Bounding Box dApp | Faixas seguras de controle em tempo real sub-TTI executadas na O-DU/O-CU. |
| `fig_35_multi_scenario_demonstration_cockpit_comparison.png`| Cockpit Comparativo Multi-Cenário | Painel consolidado confrontando cenários S1 (PRB), S2 (Potência) e S9 (NTN). |
| `fig_36_flowmonitor_ns3_s0_s15_traffic_profiles.png`| Perfis de Tráfego ns-3 FlowMonitor | Vazão e atraso amostrados diretamente na camada IP/MAC do ns-3.48. |
| `fig_37_demonstration_master_dashboard.png`| Dashboard Mestre de Demonstração | Painel executivo consolidado com todas as métricas-chave de homologação. |

---

## 🔬 Proveniência e Política Zero Synthetic Data

Todos os dados gráficos, tabelas e manifestos contidos neste repositório derivam exclusivamente de execuções factuais registradas em:
- **SSOT Mestre:** [`experiments/results/canonical_simulation_master.csv`](../../experiments/results/canonical_simulation_master.csv)
- **Tabelas Canônicas:** [`experiments/results/tables/`](../../experiments/results/tables/)
- **Telemetria de Cenários:** [`experiments/results/s0_s15_simulations/`](../../experiments/results/s0_s15_simulations/)
- **Traces E2 & PCAP:** [`experiments/results/traces/`](../../experiments/results/traces/)
