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
* **Agente de Raciocínio (`ReasoningAgent`):** Aplica funções de utilidade multiobjetivo determinísticas (**TVS** e **EEVS**), priorizando incondicionalmente fatias de missão crítica (URLLC > eMBB > mMTC).
* **Agente de Refinamento (`RefinementAgent`):** Garante a segurança física da rede (*Safety Guards*), aplicando *clamping* de potência ($P_{\text{tx}} \le 43\text{ dBm}$), orçamento de PRBs ($\le 273$) e bloqueio de ping-pong.

---

## 2. Estrutura do Repositório

```text
.
├── configs/                     # Descritores de configuração xApp (config-file.json, routes.rt)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Charts oficiais (RDL, xSlice, Energy Saving, Traffic Steering)
│   └── kubernetes/              # Manifestos K8s puros (Near-RT RIC ricplt + 3 xApps + RDL ricxapp)
├── docs/                        # Portal de Documentação Técnica (Volumes 01 a 06)
│   └── README.md                # Índice e trilhas de leitura da documentação
├── reference-xapps/             # Adaptadores leves das 3 xApps de referência abertas
│   ├── qos-xslice/              # Baseado em peihaoY/xslice-oran
│   ├── energy-saving/           # Baseado em Orange-OpenSource/ns-O-RAN-flexric
│   └── traffic-steering/        # Baseado em o-ran-sc/ric-app-ts
├── experiments/                 # Resultados de Simulação e Evidências (Baseline vs H-RDL)
├── scripts/                     # Automação de Deploy, Testes e Verificação
│   ├── deploy_helm.sh           # Pipeline Helm (Near-RT RIC -> 3 xApps -> RDL)
│   ├── deploy_k8s.sh            # Pipeline K8s/Kustomize equivalente
│   ├── verify_3_xapps.sh        # Smoke test unificado de todas as xApps
│   └── run_full_experiment.sh   # Pipeline de execução experimental completa
├── simulations/                 # Cenários C++ de Co-Simulação no ns-3 NORI / 5G-LENA
├── src/                         # Código-Fonte Python da xApp RDL (Clean Architecture)
├── tests/                       # Suíte de Testes Unitários com pytest (14/14 PASS)
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
# Execução dos testes unitários (14/14 PASS):
make test
```
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

## 5. Simulação ns-3 NORI, Coleta de Métricas e Benchmarks

O projeto inclui suporte nativo ao **ns-3 NORI / 5G-LENA** com telemetria via **FlowMonitor** e interface **SCTP (porta 36422)**.

### Instalação Automatizada do Simulador:
```bash
# Instala dependências apt, clona e compila o ns-3 de forma otimizada:
make setup-ns3
```

### Executar Pipeline Experimental Completo (Baseline vs H-RDL):
```bash
# Executa a Rodada 1 (Baseline), Rodada 2 (Com RDL), coleta traces e gera CSVs/relatórios:
make run-experiments

# Reprocessar métricas e regenerar relatórios a qualquer momento:
make analyze-benchmarks
```

### 5.2. Acesso, Visualização e Sincronização dos Resultados com o GitHub:

* **Visualizar Relatório Comparativo no Terminal:**
  ```bash
  make view-results
  # ou: cat experiments/results/relatorio_comparativo.md
  ```

* **Enviar Resultados e Datasets para o GitHub (Automático):**
  ```bash
  make push-results
  ```
  *Ou via Git manual:*
  ```bash
  git add experiments/results/
  git commit -m "chore(experiments): upload latest ns-3 simulation results and datasets"
  git push origin main
  ```

* **Sincronização Automática e Rollback do Repositório:**
  ```bash
  make sync          # Sincronização rápida e segura com o GitHub
  make auto-sync     # Monitor contínuo (auto-commit & push a cada alteração salva)
  make rollback      # Rollback seguro com criação de tag de backup
  make rollback-push # Rollback sincronizado no repositório GitHub remoto
  ```

* **Acessar Datasets no Windows Explorer (WSL2):**
  Pressione `Win + R` e acerte o caminho: `\\wsl$\Ubuntu\root\XApp-RDL-F1\experiments\results`

* **Baixar Resultados via SCP (Máquina Remota):**
  ```bash
  scp -r root@<IP_DO_HOST>:~/XApp-RDL-F1/experiments/results ./meus_resultados
  ```

### 5.3. Estrutura de Resultados em `experiments/results/`:
* **`baseline/`**: Traces brutos do ns-3 e XML do FlowMonitor sem governança da RDL.
* **`rdl_phase1/`**: Traces do ns-3, XML do FlowMonitor, logs estruturados da RDL e dump de métricas Prometheus.
* **`dataset_flow_metrics.csv`**: Métricas de fluxo para análise estatística e visualização.
* **`dataset_rdl_decisions_ml.csv`**: Dataset de transições de estado para treinamento de modelos de Machine Learning (Scikit-Learn).
* **`relatorio_comparativo.json`**: Métricas consolidadas em JSON para pipelines e automações.
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

A documentação do projeto está estruturada em uma **jornada sequencial de 6 Volumes Temáticos**. Para acessar o índice completo, visite o **[Portal de Documentação Técnica](docs/README.md)**.

| Volume | Título Temático | Domínio Técnico e Escopo |
| :---: | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura, Módulos Core e Modelagem Matemática | Clean Architecture, DDD, agentes de percepção/raciocínio/refinamento, heurísticas TVS/EEVS, codecs ASN.1 APER (KPM/RC) e formulação analítica. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura k3d (3 Topologias), Redis DBAAS e Rancher | Requisitos completos, topologias k3d (Single, Dual, Multi-Node), mapeamento de portas O-RAN, namespaces `ricplt`/`ricxapp`, Redis DBAAS e gestão no Rancher UI. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Deploy da xApp RDL e Observabilidade Kiali | Estrutura Helm Chart (`1.1.0`), deploy Kustomize, onboarding DMS, Istio Service Mesh, Kiali Dashboard em tempo real e injeção contínua de tráfego. |
| **[Volume 04](docs/04_testes_simulacao_ns3_e_benchmarks.md)** | Testes, Simulação no ns-3 NORI e Benchmarks | Testes unitários (10/10 PASS), Smoke Test, instalação ns-3 NORI, parâmetros 5G NR, cenários C++, replicação (Baseline vs H-RDL) e relatórios. |
| **[Volume 05](docs/05_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica e Governança | Matriz de rastreabilidade (REQ-RDL-01 a 10), auditoria técnica de conformidade O-RAN Alliance (WG2/WG3), 3GPP e segurança Kubernetes. |
| **[Volume 06](docs/06_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Procedimentos de Backup | Procedimento Operacional Padrão (SOP), diagnóstico exaustivo de falhas (DNS/Rancher, ErrImageNeverPull, Python) e backup bare-metal WSL2 Ubuntu 20.04. |

---

<div align="center">

**Projeto xApp RDL — O-RAN Near-RT RIC Conflict Mitigation**  
*Desenvolvido em conformidade com as diretrizes O-RAN Alliance e 3GPP.*

</div>
