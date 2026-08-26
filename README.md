# xApp RDL (Resource and Decision Layer) — O-RAN Conflict Mitigation

<div align="center">

[![O-RAN WG3 Compliant](https://img.shields.io/badge/O--RAN-WG3%20Near--RT%20RIC-blue.svg)](https://www.o-ran.org/)
[![Status: Implemented](https://img.shields.io/badge/Fase%201-Implementada%20%26%20Segura-brightgreen.svg)](#)
[![Python 3.11](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Helm 3](https://img.shields.io/badge/Helm-3.x-informational.svg)](https://helm.sh/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

</div>

---

## Navegação do Ecossistema Multi-Fases

Selecione a versão correspondente da plataforma **xApp RDL**:

| Fase | Título e Paradigma | Status do Projeto | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** *(Este Repositório)* | **RDL Determinística e Segura (H-RDL)**<br>• Janelas de decisão em lote (200ms)<br>• Heurísticas de utilidade TVS / EEVS<br>• *Safety Guards* físicos de potência e PRB | **Implementada e Estável**<br>*(Produção / Baseline)* | **[georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)** |
| **Fase 2** | **RDL Baseada em Contexto (CA-RDL)**<br>• Aprendizado por Reforço Multi-Agente (MARL / MAPPO)<br>• Redes Neurais com Atenção Contextual<br>• Arbitragem adaptativa em tempo real | **Ativa / Em Evolução**<br>*(Cognitiva / MARL)* | **[georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)** |
| **Fase 3** | **RDL Autônoma e Federada 6G**<br>• Zero-Touch Network & Intent-Driven Arbitration<br>• Multi-RIC Federated Learning & Graph Neural Networks<br>• Otimização semântica 6G | **Roadmap / Planejada**<br>*(Ainda não implementada)* | *Em especificação técnica* |

---

## 1. Visão Geral

A **xApp RDL (Resource and Decision Layer)** é uma camada de inteligência e arbitragem para o **O-RAN Near-RT RIC** (Radio Access Network Intelligent Controller). Sua missão central é resolver **conflitos diretos e indiretos de controle de rádio** decorrentes da execução concorrente de múltiplas xApps (ex: *Traffic Steering*, *Energy Savings*, *QoS Management* e *Handover Optimization*).

Na **Fase 1 (H-RDL)**, a mitigação de conflitos opera sob rigor matemático determinístico:
* **Janela Temporal de Decisão:** Agrupamento em buffer thread-safe ($\le 200\text{ ms}$) para cruzamento combinatório par a par das intenções de rádio.
* **Heurísticas de Utilidade:** Otimização multiobjetivo por Throughput vs. Prioridade de Serviço (**TVS**) e Eficiência Energética vs. Prioridade (**EEVS**).
* **Safety Guards Físicos:** Validação e clamp incondicional contra violações de potência máxima ($P_{\text{max}}$), orçamento de PRBs e limites de taxa de dados.

---

## 2. Estrutura Arquitetural (Clean Architecture e DDD)

O projeto adota **Clean Architecture** com isolamento total das regras de negócio em relação a drivers de comunicação e frameworks:

```text
src/
├── agents/                  # Motores de percepção (200ms), raciocínio (TVS/EEVS) e Safety Guards
├── coordination/            # Despachante de controle e correlacionador de ACKs E2
├── domain/                  # Entidades de domínio imutáveis (Proposals, Conflicts, Decisions)
├── e2/                      # Codecs ASN.1 APER (E2AP, E2SM-KPM v2.0 e E2SM-RC v1.0)
├── infrastructure/          # Conectores RMRXapp, SDL (Redis / Fake-SDL) e Config Manager
└── observability/           # Servidores HTTP (porta 8080) e Prometheus Metrics (porta 8081)
```

---

## 3. Guia de Execução Rápida

### Opção A: Deploy Helm Automatizado no Cluster k3d (Recomendado)
Compila o container, importa no containerd dos nós k3d, empacota o Helm Chart e faz o rollout:
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
make test
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

## 5. Análise de Dados e Machine Learning no Google Colab

Os dados experimentais gerados pelo ns-3 FlowMonitor e pela xApp RDL podem ser importados diretamente no Google Colab para geração de gráficos, relatórios e treinamento de modelos de classificação do **Scikit-Learn**:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/georgebarbosa3090/XApp-RDL-F1/blob/main/notebooks/rdl_colab_scikit_learn.ipynb)

* **Notebook:** [`notebooks/rdl_colab_scikit_learn.ipynb`](notebooks/rdl_colab_scikit_learn.ipynb)
* **Datasets CSV:** [`experiments/results/dataset_flow_metrics.csv`](experiments/results/dataset_flow_metrics.csv) e [`experiments/results/dataset_rdl_decisions_ml.csv`](experiments/results/dataset_rdl_decisions_ml.csv)
* **Modelos Inclusos:** Random Forest, Decision Tree e Gradient Boosting para predição de conflitos O-RAN e análise de importância de variáveis.

---

## 6. Portal de Documentação Técnica (`docs/`)

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
