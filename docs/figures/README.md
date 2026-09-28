# Catálogo Estruturado de Figuras Científicas (Fase 1 vs Fase 2)

Este diretório contém os conjuntos completos de figuras científicas, diagramas conceituais de arquitetura e gráficos de benchmarks experimentais do ecossistema **H-RDL (Fase 1)** e **CA-RDL (Fase 2)**, rigorosamente segregados para publicação e documentação da dissertação e artigos de periódicos (IEEE TNSM / IEEE TCCN / SBRC).

Todas as figuras são exportadas em três formatos de publicação: **PNG (300 DPI)**, **PDF Vetorial** e **SVG**.

---

## 📁 Estrutura de Diretórios Segregados

```
docs/figures/
├── fase1_hrdl/                     # 🎯 FASE 1: Middleware H-RDL (Foco em Baselines Clássicos e Teoria dos Jogos)
│   ├── fig_fase1_arquitetura_hrdl.{png,pdf,svg}
│   ├── fig_fase1_benchmarks_principais.{png,pdf,svg}
│   ├── fig_fase1_metricas_estendidas_baselines.{png,pdf,svg}
│   ├── fig_fase1_radar_multidimensional_baselines.{png,pdf,svg}
│   └── fig_fase1_distribuicoes_multissemente_boxplots.{png,pdf,svg}
│
├── fase2_cardl/                    # 🧠 FASE 2: Coordenação Cognitiva CA-RDL (Safe-RL, MAPPO, CKG e Two-Tier dApp)
│   ├── fig_fase2_arquitetura_cardl.{png,pdf,svg}
│   ├── fig_fase2_benchmarks_cognitivos.{png,pdf,svg}
│   └── fig_fase2_convergencia_treinamento_safe_rl.{png,pdf,svg}
│
└── catalogo_legado_e_topologias/   # Topologias conceituais de cenários e assets de suporte
```

---

## 🔬 1. Fase 1: H-RDL (Hierarchical Conflict Resolution & Baseline Validation)

A Fase 1 foca estritamente na validação do **Middleware H-RDL Determinístico** contra os baselines de governança de RAN:
- **B0 (Desgovernado / Sem Coordenação):** Atuação predatória e concorrente de xApps.
- **B1 (FIFO Queue):** Fila sequencial sem inteligência ou consciência de conflitos semânticos.
- **B2 (Cota Estática 60/30):** Fatiamento estático rígido de PRBs (60% eMBB / 30% URLLC / 10% Guarda).
- **B3 (H-RDL Proposta):** Arbitragem Nash Bargaining Solution (NBS) com Safe Guard determinístico e projeção Euclidiana.

### Figuras Disponíveis em `docs/figures/fase1_hrdl/`

| Arquivo | Descrição Técnica | Métricas Avaliadas |
| :--- | :--- | :--- |
| `fig_fase1_arquitetura_hrdl` | Arquitetura funcional e fluxo de controle H-RDL | Ingestão KPM, Deteção C1–C4, TVS/Nash e E2SM-RC Format 1 |
| `fig_fase1_benchmarks_principais` | Painel quadripartite de validação primária | Vazão agregada, Violação de SLA (%), ECDF da cauda de latência URLLC (Log-Scale), Escalabilidade (2 a 100 xApps) e Fechamento causal de malha fechada (Cenário S8) |
| `fig_fase1_metricas_estendidas_baselines` | Comparativo das métricas estendidas de simulação | Índice de Equidade de Jain ($J$), Taxa de Descarte de Pacotes RLC (%), Consumo de Potência do gNB (W), Eficiência Energética (Mbit/J), Jitter URLLC vs eMBB, Action Churn (ações/s) e Tempo de Estabilização ($t_{\text{settle}}$) |
| `fig_fase1_radar_multidimensional_baselines` | Gráfico Radar Polar de 6 eixos normalizados | Dominância de Pareto em Vazão, Estabilidade de Latência, Equidade, Preservação de SLA, Eficiência Energética e Estabilidade de Controle |
| `fig_fase1_distribuicoes_multissemente_boxplots` | Distribuição empírica multissemente ($N=30$) | Dispersão estatística (IQR e outliers) para Vazão da Célula, Latência RLC P95, Jitter Médio e Taxa de Violação de SLA |

---

## 🧠 2. Fase 2: CA-RDL (Cognitive Conflict Architecture & Safe-RL / MARL)

A Fase 2 foca na expansão cognitiva com grafos de conhecimento, aprendizado por reforço multiagente seguro e dApps em tempo real:
- **B3 (H-RDL Ref):** Âncora de desempenho da Fase 1.
- **B4 (Heurística + Contexto):** Regras dinâmicas contextuais.
- **B5 (Grafo de Conhecimento CKG):** Grafo causal e relacional com detecção GNN.
- **B6 (CA-RDL Proposta - Safe-MAPPO):** Safe Multi-Agent PPO com multiplicadores Lagrangianos e Action Masking.

### Figuras Disponíveis em `docs/figures/fase2_cardl/`

| Arquivo | Descrição Técnica | Métricas Avaliadas |
| :--- | :--- | :--- |
| `fig_fase2_arquitetura_cardl` | Arquitetura cognitiva estratificada de três níveis | xApps Near-RT, Motor Cognitivo CA-RDL (CKG + Safe-MAPPO), Codec ASN.1 e dApp O-DU Sub-1ms |
| `fig_fase2_benchmarks_cognitivos` | Comparativo experimental B3 vs B4 vs B5 vs B6 | Vazão Efetiva, Latência de Decisão ($T_{\text{dec}}$), Taxa de Conflitos Resumidos e Eficiência Espectral (bit/s/Hz) |
| `fig_fase2_convergencia_treinamento_safe_rl` | Curvas de convergência e segurança do Safe-MAPPO | Recompensa Episódica, Função de Custo de Segurança $J_C$, Multiplicador Lagrangiano $\lambda_k$ e Ações Inseguras ($\equiv 0\%$) |

---

## ⚙️ Script de Geração

Todas as figuras são geradas deterministicamente pelo script:
```bash
uv run python scripts/generate_separated_phase1_phase2_figures.py
```
Assegura conformidade visual estrita com os padrões IEEE/ACM, tipografia sans-serif elegante, paletas de alto contraste e reprodutibilidade com $N=30$ sementes estocásticas.
