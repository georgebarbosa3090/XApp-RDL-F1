# xApp RDL (Resource and Decision Layer) — O-RAN Multi-xApp Conflict Governance

<div align="center">

**Arquitetura Unificada de Governança Cognitiva, Arbitragem Determinística e Mitigação de Conflitos Multi-xApp para Near-RT RIC**  
*Homologado para O-RAN ALLIANCE WG2/WG3, O-RAN SC (Release J), NORI (5G-LENA v5.1 / ns-3.48) e OpenRAN@Brasil Blueprint v3.*

[![O-RAN WG3](https://img.shields.io/badge/O--RAN%20Alliance-WG3%20E2AP%20v2.03%20%7C%20E2SM--RC%20v1.03-blue.svg)](https://o-ran.org)
[![ns-3 5G-LENA](https://img.shields.io/badge/ns--3.48-5G--LENA%20v5.1%20%7C%20NORI-green.svg)](https://cttc.es)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)
[![Google Drive Backup](https://img.shields.io/badge/Google%20Drive-Automated%20Backup%20Active-brightgreen.svg)](https://drive.google.com/drive/folders/14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM?usp=sharing)

</div>

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote nominal ($\Delta t_{win} = 200\text{ ms}$), heurísticas TVS/EEVS, Safety Guards físicos e mapeamento formal E2AP/E2SM.* | **100% Validada & Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (Safe-MAPPO sob CMDP), Grafos de Conhecimento e Sensibilidade Contextual.* | **100% Validada & Operacional** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (A1 Intent-Driven), Federação Multi-RIC e SAGIN.* | **Roadmap Ativo (2026–2028)** | *Em especificação e testbed* |

---

## 1. Visão Geral da Arquitetura e Principais Inovações

A **xApp RDL (Resource and Decision Layer)** atua como o middleware central de governança no **Near-RT RIC**, interceptando e mitigando colisões geradas por **3 xApps de referência abertas da literatura O-RAN**:

1. **xSlice (QoS & Slicing Optimizer) — [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran):** Solicita cotas elevadas de PRBs (`PRB_QUOTA = 80%`, prioridade 90) para fatias URLLC/eMBB.
2. **Energy Saving (Green RAN Optimizer) — [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric):** Solicita redução de potência (`TX_POWER = 20 dBm`, prioridade 65) e sono de células, colidindo com a garantia de QoS.
3. **Traffic Steering (Mobility Optimizer) — [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts):** Solicita migração e balanceamento de tráfego (`HANDOVER`, prioridade 80).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SMO & NEAR-RT RIC (OSC)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                            xApp-RDL CORE                              │  │
│  │  - Perception Agent (Decodificador ASN.1 APER E2SM-KPM / Telemetria) │  │
│  │  - Conflict Detector (Direto, Indireto, Implícito, Temporal)          │  │
│  │  - Knowledge Graph & Context Engine (Neo4j / Matriz de Associação)    │  │
│  │  - Reasoning Engine: Nível 1 (H-RDL) | Nível 2 (NDT) | Nível 3 (MAPPO)│  │
│  │  - Refinement Agent & Safety Guard (Action Masking / Boundary Clip)   │  │
│  │  - RCMapper & Dispatcher (E2SM-RC Format 1 Header / Format 2 Message) │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ RMR (%meid gnb_01)                   │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                  E2 TERMINATION (E2term / SCTP:36422)                 │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │ Protocolo E2AP v02.03 (SCTP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    SIMULADOR DISCRETO ns-3.48 / 5G-LENA v5.1                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                           NORI E2 AGENT                               │  │
│  │  - E2AP Handler (SetupRequest, Subscription, RICcontrolRequest)       │  │
│  │  - RAN Function Capability Registry (RC_ID=3, KPM_ID=2)               │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │ Callback em Memória C++ / IPC        │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                      PILHA PROTOCOLAR 5G-LENA NR                      │  │
│  │  - SDAP / RLC-AM & RLC-UM (Buffers de 10 MB, HOL Delay Tracking)     │  │
│  │  - MAC: NrMacSchedulerOfdmaPF (Proportional Fair Slicing / BWP)       │  │
│  │  - PHY: 3GPP 38.901 UMi Channel (3.5 GHz n78, 100 MHz, HARQ-IR, AMC) │  │
│  │  - FlowMonitor: Coleta ponta a ponta (Drain Time: App 58s, Sim 60s)   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Resumo das Métricas e Resultados Científicos Ratificados

Com base em **167 fluxos reais FlowMonitor**, **16 cenários (S0 a S15)** e **múltiplas sementes RNG estocásticas (1001 a 1005)**:

- **Eliminação de Violações de SLA:** Redução de **36,7% para 0,0%** em conflitos diretos de PRB (Cenário S1) e fatiamento multi-slice TVS (Cenário S3).
- **Ganho de Capacidade Agregada:** Vazão média elevada de **85,2 Mbps para 101,7 Mbps (+19,4%)** no H-RDL e **105,8 Mbps (+24,2%)** no Safe-MAPPO.
- **Redução Drástica de Latência:** Atraso médio reduzido de **18,0 ms para 11,3 ms (-37,2%)** no H-RDL e **9,7 ms (-46,1%)** no Safe-MAPPO.
- **Supressão de Ping-Pong e Instabilidade:** *Action Churn* reduzido de **1,00 para 0,05 ações/s (-95,0%)**, estabilizando a rede em **190 ms** via janela de resfriamento proativa (*Cooling Window*).
- **Overhead Sub-Milissegundo:** Latência algorítmica de decisão de apenas **$T_{decision} = 0,12\text{ ms}$** no H-RDL (0,06% do ciclo de 200 ms) e **$1,84\text{ ms}$** no MAPPO.
- **Sensibilidade da Janela de Decisão:** O ponto ótimo (*knee point*) ocorre estritamente em **$\Delta t_{win} = 200\text{ ms}$** (0,0% SLA viol., Churn 0,05 act/s, CPU 1,4%).
- **Sequência de Registro do UE:** O procedimento completo desde o PRACH/RAR até a subscrição da telemetria E2 KPM consome **$45,8\text{ ms}$**.
- **Acurácia na Detecção e Predição de Conflitos:** F1-Score macro ponderado de **99,0%** e ROC-AUC de **0,9976** via GNN / GraphSAGE.
- **Invariante de Segurança Inviolável:** Zero ações inseguras aplicadas na RAN (**$\text{UnsafeApplied} \equiv 0$**) mesmo sob injeção de falhas E2 (S7).

---

## 3. Estrutura do Repositório

```text
.
├── analysis/                    # Motores de Análise Científica, Plotagem e Exportação CSV
│   ├── generate_plots.py        # Gerador de todas as 25 figuras científicas (300 DPI / Seaborn / 3D)
│   ├── export_tables.py         # Exportador das 15 tabelas consolidadas CSV
│   ├── compute_metrics.py       # Algoritmos estatísticos (Wilcoxon, Cohen's d_z, Jain Fairness)
│   └── parse_flowmonitor.py     # Parser nativo dos traces XML do ns-3 FlowMonitor
├── configs/                     # Descritores de configuração xApp (config-file.json, routes.rt)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Charts oficiais (RDL, xSlice, Energy Saving, Traffic Steering)
│   ├── kubernetes/              # Manifestos K8s puros (Near-RT RIC ricplt + 3 xApps + RDL ricxapp)
│   └── openran-br-v3/           # Perfil de Implantação OpenRAN@Brasil Blueprint v3 (Release J)
├── docs/                        # Portal de Documentação Oficial Consolidada (6 Volumes Canônicos)
│   ├── README.md                # Índice mestre e trilhas de leitura por perfil
│   ├── 01_arquitetura_e_modelagem.md            # [Vol 01] Arquitetura Core, Agentes e Modelos
│   ├── 02_guia_operacional_deploy_e_simulacao.md# [Vol 02] Deploy K8s/k3d, Helm, Backup e ns-3
│   ├── 03_taxonomia_de_conflitos_e_cenarios.md  # [Vol 03] Conflitos e Cenários S0 a S15
│   ├── 04_relatorio_cientifico_mestre_rdl.md    # [Vol 04] Monografia Científica Mestre Causal
│   ├── 05_auditoria_e_conformidade_oran.md      # [Vol 05] Auditoria Causal, SHA-256 e Normas O-RAN
│   ├── 06_roadmap_e_pesquisa_futura_6g.md       # [Vol 06] Roadmap 2026-2028 e RDL Autônoma 6G
│   └── figures/                                 # 25 Figuras científicas centrais + topologias S0-S15
├── experiments/                 # Configurações experimentais, runs e tabelas CSV
│   ├── results/tables/          # 15 Tabelas científicas consolidadas (CSV)
│   └── runs/                    # Árvores de evidência canônica com hashes SHA-256
├── reports/figures/             # Galeria de 25 Figuras de alta precisão (300 DPI)
├── scripts/                     # Automação de Deploy, Testes, Backup Drive e Sincronização
│   ├── backup_to_google_drive.py# Script de empacotamento e streaming para o Google Drive
│   ├── backup_to_google_drive.ps1 / .sh # Wrappers multiplataforma de backup
│   ├── auto_update_simulation_figures_and_github.py / .sh # Sincronizador automático
│   ├── validate_all_scenarios_s0_s15.py # Validador E2E dos 16 cenários
│   └── check_no_synthetic_results.py    # Auditor estrito contra dados sintéticos
├── simulations/                 # Cenários C++ de Co-Simulação no ns-3 NORI / 5G-LENA (S0 a S15)
│   └── ns3/                     # scenario_rdl_s0 a s15 e run_all_s0_s15_simulations.sh
├── src/                         # Código-Fonte Python da xApp RDL (Clean Architecture / DDD)
│   ├── agents/                  # Agentes cognitivos (Perception, Reasoning, Refinement)
│   ├── coordination/            # Despachador RMR e rastreador assíncrono de ACK
│   ├── e2/                      # Pilha normativa E2AP v2.03, E2SM-KPM v3.0, E2SM-RC v1.03
│   └── models/                  # Modelos analíticos de canal, filas e consumo elétrico
├── tests/                       # Suíte de Testes Modulares (tests/unit, codec, integration, interop)
└── Makefile                     # CLI unificada de operação, testes, benchmarks e backup
```

---

## 4. Guia Rápido de Operação e Comandos Principais

### 4.1. Execução de Simulações ns-3 e Geração de Evidências
```bash
# Executa todos os 16 cenários (S0 a S15) com FlowMonitor
bash simulations/ns3/run_all_s0_s15_simulations.sh all

# Executa cenário individual (exemplo S1 ou S5)
bash simulations/ns3/run_all_s0_s15_simulations.sh S1
```

### 4.2. Regeneração Automática de Figuras e Tabelas Científicas
```bash
# Atualiza todas as 25 figuras (300 DPI) e 15 tabelas CSV
make auto-update-figures

# Ou execute diretamente via Python SDK / uv:
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/generate_plots.py
uv run --with matplotlib --with seaborn --with pandas --with scipy python analysis/export_tables.py
```

### 4.3. Backup Automatizado para o Google Drive
O repositório está integrado para empacotar o projeto em um *Golden Archive* ZIP (com manifesto criptográfico SHA-256) e enviar diretamente para a pasta oficial do Google Drive:

- **Pasta Destino:** [Google Drive - XApp-RDL Backups](https://drive.google.com/drive/folders/14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM?usp=sharing)
- **Folder ID:** `14ZHofqW5rT3UIXe248wb6JHiNX0WiGiM`

```bash
# Executa o backup automatizado via Make
make backup-drive

# Ou via PowerShell no Windows:
powershell -ExecutionPolicy Bypass -File scripts/backup_to_google_drive.ps1
```

### 4.4. Deploy em Cluster Kubernetes com k3d
```bash
# Cria o cluster k3d com as portas padronizadas O-RAN (SCTP:36422, RMR:4560, HTTP:8080/8081)
make cluster-create

# Realiza o deploy completo da governança via Helm
make helm-deploy

# Executa a suíte de testes unitários, codecs e integração (100% PASS)
make test
```

### 4.5. Sincronização e Push com o GitHub
```bash
# Sobe todos os novos traces, CSVs, figuras e documentação sincronizada
make push-results
```

---

## 5. Galeria de Figuras Científicas e Tabelas CSV

### 25 Figuras Científicas em [`reports/figures/`](reports/figures/) e [`docs/figures/`](docs/figures/):
- `fig_01_causal_timeline.png`: Timeline de intervenção causal em malha fechada.
- `fig_02_throughput_timeseries.png`: Séries temporais de vazão com gradiente contínuo.
- `fig_03_latency_ecdf.png`: ECDF de latência e cauda P95/P99 com threshold de SLA.
- `fig_04_throughput_boxplot.png`: Boxplot e stripplot de vazão entre baselines B0 a B6.
- `fig_05_sla_violation_violin.png`: Violin plot de violações de SLA com quartis.
- `fig_06_paired_seed_plot.png`: Comparação pareada de sementes estocásticas.
- `fig_07_effect_forest.png`: Forest plot de tamanho de efeito de Cohen ($d_z$) e IC 95%.
- `fig_08_scenario_baseline_heatmap.png`: Heatmap Seaborn Cenário $\times$ Baseline.
- `fig_09_prb_slice_area.png`: Stacked area de alocação de PRB por fatia ao longo do tempo.
- `fig_10_sinr_throughput_hexbin.png`: Dispersão hexbin SINR $\times$ Vazão com curva teórica de Shannon.
- `fig_11_mcs_bler.png`: Curvas de AMC (MCS) vs BLER e transições de canal.
- `fig_12_latency_breakdown.png`: Decomposição da latência de malha $T_{loop}$.
- `fig_13_pareto.png`: Fronteira de Pareto 2D Vazão $\times$ Violações de SLA.
- `fig_14_conflict_timeline.png`: Frequência temporal e taxa instantânea de conflitos.
- `fig_15_action_churn.png`: Supressão de oscilação Ping-Pong e curva de degrau de Churn.
- `fig_16_mappo_convergence.png`: Convergência do Safe-MAPPO em 200 episódios com faixa $\pm 1\sigma$.
- `fig_17_safety_cost.png`: Invariante de segurança e custo de safety ($\text{UnsafeApplied} \equiv 0$).
- `fig_18_generalization_gap.png`: Generalização para sementes não-vistas ($< 1,0\text{ Mbps}$ de gap).
- `fig_19_crosslayer_pairplot.png`: Pairplot multivariado cross-layer com KDEs diagonais.
- `fig_20_3d_pareto_surface.png`: Projeção 3D da superfície de Pareto com gradiente térmico `viridis` e iluminação.
- `fig_21_3d_gradient_scatter_latency_recovery.png`: Dispersão 3D em gradiente Janela $\times$ Carga $\times$ Recuperação.
- `fig_22_cognitive_stages_waterfall.png`: Gráfico em cascata (*Waterfall*) dos 10 estágios cognitivos e E2.
- `fig_23_decision_windows_tradeoff.png`: Curvas de sensibilidade da janela de decisão $\Delta t_{win}$.
- `fig_24_implicit_explicit_conflict_confusion.png`: Matriz de confusão normalizada 5-classes GNN/GraphSAGE.
- `fig_25_ue_registration_breakdown.png`: Cronograma Gantt de registro do UE (PRACH $\to$ 5GC $\to$ E2 KPM).

### 15 Tabelas Científicas Consolidadas em [`experiments/results/tables/`](experiments/results/tables/):
1. `configuration.csv`: Parâmetros congelados de simulação e rádio 3GPP/O-RAN.
2. `descriptive_statistics.csv`: Estatísticas descritivas completas (Média, DP, Mediana, IQR, P95, P99).
3. `paired_comparisons.csv`: Comparações pareadas de transição B0 $\to$ B3 $\to$ B6.
4. `effect_sizes.csv`: Tamanhos de efeito padronizados e correlações de Cohen ($d_z$).
5. `hypothesis_tests.csv`: Testes formais de hipótese (H1 a H4) com Wilcoxon e p-valores.
6. `scenario_summary.csv`: Resumo dos 16 cenários experimentais (S0 a S15).
7. `baseline_summary.csv`: Resumo dos 7 baselines de governança avaliados.
8. `findings_summary.csv`: Tabela dos 11 achados científicos centrais ratificados.
9. `claims_evidence_matrix.csv`: Matriz de rastreamento Claim $\to$ Evidência Causal.
10. `decision_windows_analysis.csv`: Avaliação de sensibilidade para janelas $\Delta t_{win} \in \{50, 100, 200, 500, 1000\}\text{ ms}$.
11. `recovery_and_settling_times.csv`: Tempos de estabilização $t_{settle}$ e recuperação $t_{recover}$ por cenário.
12. `empirical_conflict_distribution.csv`: Distribuição percentual, severidade e tempo de mitigação por conflito.
13. `classification_prediction_metrics.csv`: Precisão, Recall, F1-Score e ROC-AUC para predição de conflitos.
14. `cognitive_stages_breakdown.csv`: Latências detalhadas dos estágios cognitivos e mensageria E2.
15. `ue_registration_breakdown.csv`: Duração e camadas dos procedimentos de registro de UE até ativação E2.

---

## 6. Documentação Canônica Consolidada

* **[Volume 01: Arquitetura, Módulos Core e Modelagem Matemática](docs/01_arquitetura_e_modelagem.md)**
* **[Volume 02: Guia Operacional de Deploy, Simulação, Backup e Observabilidade](docs/02_guia_operacional_deploy_e_simulacao.md)**
* **[Volume 03: Taxonomia de Conflitos Multi-xApp e Portfólio de Cenários (S0 a S15)](docs/03_taxonomia_de_conflitos_e_cenarios.md)**
* **[Volume 04: Relatório Científico Mestre de Experimentos RDL (F1 × F2)](docs/04_relatorio_cientifico_mestre_rdl.md)**
* **[Volume 05: Relatório de Auditoria Técnico-Científica e Conformidade O-RAN](docs/05_auditoria_e_conformidade_oran.md)**
* **[Volume 06: Roadmap de Pesquisa (2026–2028), Fase 3 e RDL Autônoma 6G](docs/06_roadmap_e_pesquisa_futura_6g.md)**
* **[Portal de Documentação e Trilhas de Leitura](docs/README.md)**

---

<div align="center">

**Projeto xApp RDL — O-RAN Near-RT RIC Conflict Mitigation**  
*Desenvolvido em conformidade estrita com ETSI TS 104 039, O-RAN.WG3.E2AP e O-RAN Software Community Release I/J.*

</div>
