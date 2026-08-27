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

A **xApp RDL (Resource and Decision Layer)** atua como o middleware central de governança no **Near-RT RIC**, mitigando colisões e decisões conflitantes emitidas por múltiplas xApps concorrentes (*Traffic Steering*, *Energy Savings*, *QoS Manager*):

* **Agente de Percepção (`PerceptionAgent`):** Agrupa propostas de controle E2 em **janelas de decisão em lote ($\Delta t = 200\text{ ms}$)** e identifica conflitos diretos (mesmo PRB/potência) e indiretos (trade-off energia vs QoS).
* **Agente de Raciocínio (`ReasoningAgent`):** Aplica funções de utilidade multiobjetivo determinísticas (**TVS — Time-Varying Slicing** e **EEVS — Energy-Efficiency vs SLA**), priorizando incondicionalmente fatias de missão crítica (URLLC > eMBB > mMTC).
* **Agente de Refinamento (`RefinementAgent`):** Garante a segurança física da rede (*Safety Guards*), aplicando *clamping* incondicional de potência de transmissão ($P_{\text{tx}} \le 43\text{ dBm}$), orçamento de PRBs ($\le 273$) e bloqueio de oscilações de *handover* (efeito ping-pong).
* **Codecs ASN.1 APER:** Suporte de baixo nível a E2AP, E2SM-KPM v2.0 (telemetria de rádio) e E2SM-RC v1.0 (mensagens de controle arbitradas).

---

## 2. Estrutura do Repositório

```text
.
├── configs/                     # Descritores de configuração xApp (config-file.json)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Chart oficial (versão 1.1.0)
│   └── kubernetes/              # Manifestos K8s declarativos (Kustomize)
├── docs/                        # Portal de Documentação Técnica (Volumes 01 a 07)
│   ├── assets/                  # Imagens e banners comerciais do projeto
│   └── README.md                # Índice e trilhas de leitura da documentação
├── experiments/                 # Resultados de Simulação e Evidências
│   └── results/                 # Diretório estruturado de coleta (Baseline vs H-RDL)
│       ├── baseline/            # Evidências brutas da Rodada 1 (Sem RDL)
│       ├── rdl_phase1/          # Evidências brutas da Rodada 2 (Com H-RDL)
│       ├── dataset_flow_metrics.csv      # Dataset tabular por fluxo para Colab
│       ├── dataset_rdl_decisions_ml.csv  # Dataset temporal para Scikit-Learn
│       ├── relatorio_comparativo.json    # Métricas consolidadas em JSON
│       └── relatorio_comparativo.md      # Relatório executivo formal
├── notebooks/                   # Jupyter Notebooks para Google Colab & Scikit-Learn
│   └── rdl_colab_scikit_learn.ipynb
├── scripts/                     # Automação de Deploy, Testes e Análise de Benchmarks
│   ├── deploy_helm.sh           # Script de implantação via Helm
│   ├── run_full_experiment.sh   # Pipeline de execução experimental completa
│   └── run_and_analyze_benchmarks.py # Parser de FlowMonitor, gerador de CSVs e gráficos
├── simulations/                 # Cenários C++ de Co-Simulação no ns-3 NORI / 5G-LENA
│   └── ns3/
│       ├── scenario_rdl_tvs_conflict.cc   # Cenário de conflito TVS (URLLC vs eMBB vs mMTC)
│       └── scenario_rdl_energy_vs_qos.cc  # Cenário de economia de energia vs SLA
├── src/                         # Código-Fonte Python da xApp RDL (Clean Architecture)
│   ├── core/                    # Agentes de Percepção, Raciocínio e Refinamento
│   ├── e2/                      # Codecs ASN.1 APER (E2AP, KPM, RC)
│   └── web/                     # Servidores FastAPI (Health na 8080, Métricas na 8081)
├── tests/                       # Suíte de Testes Unitários com pytest (10/10 PASS)
└── Makefile                     # CLI unificada de operação, testes e benchmarks
```

---

## 3. Guia Rápido de Execução e Deploy

### Opção A: Deploy Oficial no Kubernetes via Helm
```bash
make helm-deploy
```

### Opção B: Deploy Kubernetes Puro (K8s / Kustomize)
```bash
make k8s-deploy
```

### Opção C: Smoke Test Standalone no Docker
```bash
make smoke-test
```

### Opção D: Testes Unitários e Validação de CI
```bash
# Configuração do ambiente virtual (uma única vez):
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt

# Execução dos testes:
make test
# Saída esperada: 10 passed in 1.20s (100% green)
```

---

## 4. Observabilidade e Monitoramento

* **Rancher Dashboard:** Acesse `https://127.0.0.1:8443` para gerenciar namespaces (`ricplt`, `ricxapp`), nós e telemetria de CPU/RAM em tempo real.
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

## 5. Simulação ns-3 NORI, Coleta de Métricas e Benchmarks

O projeto inclui suporte nativo ao **ns-3 NORI / 5G-LENA** com telemetria via **FlowMonitor** e interface **SCTP (porta 36422)**.

### Executar Pipeline Experimental Completo (Baseline vs H-RDL):
```bash
# Executa a Rodada 1 (Baseline), Rodada 2 (Com RDL), coleta traces e gera CSVs/relatórios:
make run-experiments

# Reprocessar métricas e regenerar relatórios a qualquer momento:
make analyze-benchmarks
```

### Estrutura de Resultados em `experiments/results/`:
* **`baseline/`**: Traces brutos do ns-3 e XML do FlowMonitor sem governança da RDL.
* **`rdl_phase1/`**: Traces do ns-3, XML do FlowMonitor, logs estruturados da RDL e dump de métricas Prometheus.
* **`relatorio_comparativo.md`**: Tabela executiva com comprovação científica de redução de conflitos em 96.8% e latência URLLC $< 3\text{ ms}$.

---

## 6. Análise de Dados e Machine Learning no Google Colab

Os datasets gerados pela co-simulação podem ser importados diretamente no Google Colab para geração de gráficos estatísticos e treinamento de algoritmos de classificação do **Scikit-Learn**:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)

* **Notebook:** [`notebooks/rdl_colab_scikit_learn.ipynb`](notebooks/rdl_colab_scikit_learn.ipynb)
* **Datasets CSV:** [`experiments/results/dataset_flow_metrics.csv`](experiments/results/dataset_flow_metrics.csv) e [`experiments/results/dataset_rdl_decisions_ml.csv`](experiments/results/dataset_rdl_decisions_ml.csv)
* **Modelos Inclusos:** Random Forest, Decision Tree e Gradient Boosting para predição proativa de conflitos O-RAN e análise de importância de variáveis (*Feature Importance*).

---

## 7. Portal de Documentação Técnica (`docs/`)

A documentação do projeto está estruturada e separada em **7 Volumes Temáticos**. Para acessar o índice completo, visite o **[Portal de Documentação Técnica](docs/README.md)**.

| Volume | Título Temático | Domínio Técnico e Escopo |
| :---: | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura, Módulos Core e Modelagem Matemática | Clean Architecture, DDD, agentes de percepção/raciocínio/refinamento, heurísticas TVS/EEVS, codecs ASN.1 APER (KPM/RC) e formulação analítica. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura k3d, Rancher Dashboard e Operações | Topologias de cluster no WSL2 (Single-Node vs Multi-Node), mapeamento de portas O-RAN (SCTP/RMR/HTTP) e agente `07-k8s-oran-cluster-operator`. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Implantação e Automação de Deploy | Estrutura Helm Chart (`1.1.0`), deploy declarativo com Kustomize (`deploy/kubernetes/`), pipelines automatizados e onboarding O-RAN DMS. |
| **[Volume 04](docs/04_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Procedimentos de Backup | Procedimento Operacional Padrão (SOP), diagnóstico de erros (`ErrImageNeverPull`, Rancher agent) e backup bare-metal WSL Ubuntu 20.04. |
| **[Volume 05](docs/05_testes_simulacao_ns3_e_benchmarks.md)** | Testes, Simulação no ns-3 NORI, Procedimento Experimental e Benchmarks | Testes unitários/CI, Smoke Test, instalação ns-3 NORI, parâmetros 5G NR, cenários C++, replicação passo-a-passo (Baseline vs H-RDL) e relatórios. |
| **[Volume 06](docs/06_observabilidade_kiali_e_injecao_trafego.md)** | Observabilidade Service Mesh com Kiali e Tráfego | Checklist de dependências, Istio Service Mesh, Kiali Dashboard em tempo real e injetor sintético de tráfego (`make inject-traffic`). |
| **[Volume 07](docs/07_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica e Governança | Matriz de rastreabilidade de requisitos (REQ-RDL-01 a 10), auditoria técnica de conformidade O-RAN Alliance (WG2/WG3) e segurança K8s. |

---

<div align="center">

**Projeto xApp RDL — O-RAN Near-RT RIC Conflict Mitigation**  
*Desenvolvido em conformidade com as diretrizes O-RAN Alliance e 3GPP.*

</div>
