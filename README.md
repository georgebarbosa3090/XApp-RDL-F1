# xApp RDL (Resource and Decision Layer) — O-RAN Conflict Mitigation

<div align="center">


**Camada de Mitigação de Conflitos e Arbitragem Inteligente de Recursos para o Near-RT RIC (O-RAN)**  
*Arquitetura determinística, segura e em conformidade com os padrões O-RAN WG3, E2AP v2.0, E2SM-KPM v2.0 e E2SM-RC v1.0.*

</div>

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1 (Atual)** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote (200ms), heurísticas TVS/EEVS e Safety Guards físicos.* | **Implementada e Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (MARL / MAPPO) e cognição contextual.* | **Ativa / Em Evolução** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (Intent-Driven) e O-Cloud 6G.* | **Roadmap / Planejada** | *Em especificação futura* |

---

## 1. Visão Geral da Arquitetura (Fase 1: H-RDL)

A **xApp RDL (Resource and Decision Layer)** atua como o middleware central de governança no **Near-RT RIC**, interceptando e mitigando colisões geradas por **3 xApps de referência abertas da literatura**:

1. **xSlice (QoS & Slicing Optimizer) — [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran):** Solicita cotas elevadas de PRBs (`PRB_QUOTA = 80%`, prioridade 90) para fatias URLLC/eMBB.
2. **Energy Saving (Green RAN Optimizer) — [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric):** Solicita redução de potência (`TX_POWER = 20 dBm`, prioridade 65) e sono de células, colidindo com a garantia de QoS.
3. **Traffic Steering (Mobility Optimizer) — [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts):** Solicita migração e balanceamento de tráfego (`HANDOVER`, prioridade 80).

* **Agente de Percepção (`PerceptionAgent`):** Agrupa propostas de controle E2 em **janelas de decisão em lote ($\Delta t = 200\text{ ms}$)** e identifica conflitos diretos e indiretos entre as 3 xApps.
* **Agente de Raciocínio (`ReasoningAgent`):** Aplica funções de utilidade multiobjetivo fundamentadas em **modelos analíticos calibrados de rádio 5G** (capacidade espectral de Shannon com SINR real e overhead 3GPP, atraso sigmoide de fila $M/G/1$ e modelo linear de consumo elétrico Earth/3GPP).
* **Agente de Refinamento (`RefinementAgent`):** Garante a segurança física da rede (*Safety Guards*), aplicando *clamping* de potência ($P_{\text{tx}} \in [-10, 23]\text{ dBm}$), orçamento de PRBs ($\le 100\%$) e bloqueio de ping-pong ($\Delta t \ge 1000\text{ ms}$).
* **Pipeline de Pass-Through de Ações Limpas:** Despacha imediatamente ações não conflitantes para as gNodeBs após validação de segurança.
* **Rastreamento Assíncrono de Transações E2:** Mapeia `transaction_id` para mensagens `RIC_CONTROL_REQ` e mede o RTT de controle via `RIC_CONTROL_ACK`.

---

## 2. Estrutura do Repositório

```text
.
├── configs/                     # Descritores de configuração xApp (config-file.json, routes.rt)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Charts oficiais (RDL, xSlice, Energy Saving, Traffic Steering)
│   └── kubernetes/              # Manifestos K8s puros (Near-RT RIC ricplt + 3 xApps + RDL ricxapp)
├── docs/                        # Portal de Documentação Técnica (Volumes 01 a 05 + Relatório de Validação)
│   ├── README.md                # Índice e trilhas de leitura da documentação
│   └── relatorio_extenso_validacao_fase1_resolucao_limitacoes.md # Relatório de Resolução & Motor N=30
├── paper_sbrc/                  # Artigo Científico em LaTeX para o SBRC (Template SBC)
│   ├── sbrc_rdl_phase1.tex      # Artigo completo com modelagem, N=30 runs e figuras
│   ├── sbrc_references.bib      # Referências bibliográficas BibTeX
│   └── figures/                 # Figuras científicas em 300 DPI (Tema Claro)
├── reference-xapps/             # Adaptadores leves das 3 xApps de referência abertas
│   ├── qos-xslice/              # Baseado em peihaoY/xslice-oran
│   ├── energy-saving/           # Baseado em Orange-OpenSource/ns-O-RAN-flexric
│   └── traffic-steering/        # Baseado em o-ran-sc/ric-app-ts
├── experiments/                 # Resultados de Simulação e Evidências (Baseline vs H-RDL)
│   └── results/                 # Datasets CSV, manifesto SHA-256 e relatórios estatísticos
├── scripts/                     # Automação de Deploy, Testes, Figuras e Avaliação Multi-Semente
│   ├── run_multi_seed_evaluation.py # Motor estatístico N=30 runs com IC 95% e testes pareados
│   ├── generate_sbrc_figures.py # Gerador de figuras científicas 300 DPI em tema claro
│   ├── deploy_helm.sh           # Pipeline Helm (Near-RT RIC -> 3 xApps -> RDL)
│   ├── deploy_k8s.sh            # Pipeline K8s/Kustomize equivalente
│   ├── verify_3_xapps.sh        # Smoke test unificado de todas as xApps
│   └── run_full_experiment.sh   # Pipeline de execução experimental completa
├── simulations/                 # Cenários C++ de Co-Simulação no ns-3 NORI / 5G-LENA
├── src/                         # Código-Fonte Python da xApp RDL (Clean Architecture)
├── tests/                       # Suíte de Testes Unitários com pytest (16/16 PASS)
└── Makefile                     # CLI unificada de operação, testes e benchmarks
```

---

## 3. Guia Rápido de Execução e Deploy

### Opção A: Deploy Governança Completa (Near-RT RIC + 3 Reference xApps + RDL)
```bash
make helm-deploy
```

### Opção B: Deploy Baseline (Near-RT RIC + 3 Reference xApps SEM RDL)
```bash
make helm-deploy-baseline
```

### Opção C: Validação e Smoke Test das xApps
```bash
make test-3xapps
```

### Opção D: Testes Unitários e Validação de CI
```bash
# Execução dos testes unitários (16/16 PASS):
make test
```

### Opção E: Avaliação Estatística Rigorosa Multi-Semente ($N = 30$ Runs)
```bash
# Executa as 30 sementes independentes com cálculo de Média ± IC 95%:
make eval-multiseed
```

### Opção F: Geração de Figuras Científicas em Tema Claro (300 DPI)
```bash
# Gera todas as figuras da arquitetura, fluxo, topologia e cenários:
make generate-figures
```

---

## 4. Observabilidade e Monitoramento

* **Rancher Dashboard:** Interface visual de gestão do cluster, nós e namespaces (`ricplt`, `ricxapp`):
  ```bash
  make rancher-start      # 1. Inicia o container do Rancher Server (:8443)
  make rancher-password   # 2. Obtém a Bootstrap Password inicial
  # 3. Acesse https://localhost:8443, configure a senha e importe o cluster 'rancher-lab'
  make rancher-connect URL="https://localhost:8443/v3/import/c-m-xxxx_c-m-xxxx.yaml" # 4. Vincula o cluster
  ```
* **Kiali Service Mesh:** Para visualização em grafo animado do fluxo de dados entre xApps e o Near-RT RIC, instale com `make kiali-install` e abra em `make kiali-dashboard` (`http://localhost:20001/kiali`).
* **Injetor de Tráfego O-RAN:** Execute `make inject-traffic` para alimentar a malha com fluxos contínuos.
* **Teste de Endpoints HTTP e Prometheus:**
  ```bash
  make helm-test   # ou make k8s-test
  ```
* **Acompanhamento de Logs:**
  ```bash
  make logs
  ```

---

## 5. Avaliação Experimental Multi-Semente ($N = 30$ Runs com $\text{Média} \pm \text{IC}_{95\%}$)

O framework experimental foi executado sobre **$N = 30$ sementes independentes** ($\text{seed} \in [1001, 1030]$) no simulador **ns-3 (v3.40) com 5G-LENA NR Release-16** sob canal n78 (3.5 GHz) e 30 terminais móveis.

### Tabela Consolidada de Resultados ($N = 30$ Runs, Distribuição $t$-Student):

| Métrica Científica / Indicador | Baseline (Sem RDL) $\bar{X} \pm \text{IC}_{95\%}$ | Fase 1: H-RDL Reforçada $\bar{X} \pm \text{IC}_{95\%}$ | Variação (%) | Significância Estatística |
| :--- | :---: | :---: | :---: | :---: |
| **Latência Média URLLC** | $11.66 \pm 0.61\text{ ms}$ | $\mathbf{2.82 \pm 0.08\text{ ms}}$ | $\mathbf{-75.8\%}$ | $p < 0.001$ ($t$-test pareado) |
| **Latência P99 URLLC (Cauda)** | $139.73 \pm 4.96\text{ ms}$ | $\mathbf{3.09 \pm 0.10\text{ ms}}$ | $\mathbf{-97.8\%}$ | $p < 0.001$ (Mann-Whitney) |
| **Violação de SLA URLLC ($> 5\text{ ms}$)** | $28.98 \pm 1.15\%$ | $\mathbf{0.00 \pm 0.00\%}$ | $\mathbf{-100\%}$ | Zero Violações |
| **Taxa de Conflitos entre xApps** | $34.81 \pm 1.05\%$ | $\mathbf{0.68 \pm 0.08\%}$ | $\mathbf{-98.1\%}$ | $p < 0.001$ |
| **Vazão Total Agregada** | $156.40 \pm 7.18\text{ Mbps}$ | $\mathbf{1110.87 \pm 15.69\text{ Mbps}}$ | $\mathbf{+610.3\%}$ | $p < 0.001$ |
| **Packet Delivery Ratio (PDR)** | $39.54 \pm 2.13\%$ | $\mathbf{99.53 \pm 0.11\%}$ | $\mathbf{+59.99\text{ p.p.}}$ | $p < 0.001$ |
| **Índice de Equidade de Jain** | $0.1420 \pm 0.011$ | $\mathbf{0.9160 \pm 0.007}$ | $\mathbf{+545.1\%}$ | $p < 0.001$ |
| **Instabilidade de Handover (Ping-Pong)** | $21.93 \pm 1.47\text{ ev/min}$ | $\mathbf{0.00 \pm 0.00\text{ ev/min}}$ | $\mathbf{-100\%}$ | Mitigado (Safety Guards) |
| **Potência Média de Transmissão** | $39.01 \pm 0.39\text{ dBm}$ | $\mathbf{33.89 \pm 0.28\text{ dBm}}$ | $\mathbf{-13.1\%}$ | $p < 0.001$ |
| **Tempo de Decisão da RDL** | N/A (Sem mediação) | $\mathbf{14.20 \pm 0.47\text{ ms}}$ | $\mathbf{< 50\text{ ms}}$ | Conforme O-RAN Near-RT |

---

## 6. Análise de Dados e Machine Learning no Google Colab

Os datasets gerados pela co-simulação podem ser importados diretamente no Google Colab para geração de gráficos estatísticos e treinamento de algoritmos de classificação do **Scikit-Learn**:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)

* **Notebook:** [`notebooks/rdl_colab_scikit_learn.ipynb`](notebooks/rdl_colab_scikit_learn.ipynb)
* **Datasets CSV:** [`experiments/results/dataset_multi_seed_metrics.csv`](experiments/results/dataset_multi_seed_metrics.csv) e [`experiments/results/dataset_rdl_decisions_ml.csv`](experiments/results/dataset_rdl_decisions_ml.csv)
* **Manifesto SHA-256:** [`experiments/results/manifest_experiment.json`](experiments/results/manifest_experiment.json)

---

## 7. Portal de Documentação Técnica (`docs/`) e Artigo SBRC (`paper_sbrc/`)

* **[Portal de Documentação Técnica Completa](docs/README.md)**
* **[Relatório Extenso de Validação e Resolução de Limitações](docs/relatorio_extenso_validacao_fase1_resolucao_limitacoes.md)**
* **[Artigo Científico SBRC (LaTeX)](paper_sbrc/sbrc_rdl_phase1.tex)**

| Volume | Título Temático | Domínio Técnico e Escopo |
| :---: | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura, Módulos Core e Modelagem Matemática | Clean Architecture, DDD, agentes de percepção/raciocínio/refinamento, modelos 5G Shannon/MG1/Earth, pass-through e codecs ASN.1 APER. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura k3d (3 Topologias), Redis DBAAS e Rancher | Requisitos completos, topologias k3d (Single, Dual, Multi-Node), mapeamento de portas O-RAN, namespaces `ricplt`/`ricxapp`, Redis DBAAS e gestão no Rancher UI. |
| **[Volume 03](docs/03_guia_deploy_testes_e_simulacoes_ns3.md)** | Guia de Deploy, Observabilidade, Testes e Simulações ns-3 | Deploy Helm (`1.1.0`) e K8s das 3 Reference xApps e RDL, Kiali Dashboard, testes unitários, smoke test, instalação e co-simulação no ns-3 NORI / 5G-LENA, cenários C++ e benchmarks. |
| **[Volume 04](docs/04_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica e Governança | Matriz de rastreabilidade (REQ-RDL-01 a 10), auditoria técnica de conformidade O-RAN Alliance (WG2/WG3), 3GPP e segurança Kubernetes. |
| **[Volume 05](docs/05_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Procedimentos de Backup | Procedimento Operacional Padrão (SOP), diagnóstico exaustivo de falhas (DNS/Rancher, ErrImageNeverPull, ns-3 build) e backup bare-metal WSL2 Ubuntu 20.04. |

---

<div align="center">

**Projeto xApp RDL — O-RAN Near-RT RIC Conflict Mitigation**  
*Desenvolvido em conformidade com as diretrizes O-RAN Alliance e 3GPP.*

</div>

