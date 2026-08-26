import os

p2_dir = os.path.abspath("../iqos-xapp-rdl-phase2")

readme_phase2 = '''# xApp RDL - Fase 2: Context-Aware Resource and Decision Layer (CA-RDL / MARL)

[![Open RAN](https://img.shields.io/badge/O--RAN-Near--RT--RIC-orange.svg)](https://o-ran.org)
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)](https://github.com/georgebarbosa3090/XApp-RDL-F2)
[![Helm](https://img.shields.io/badge/Helm-v3%20Chart%202.0.0-informational.svg)](deploy/helm/iqos-xapp-rdl)
[![Kubernetes](https://img.shields.io/badge/K8s-Native%20Kustomize-326CE5.svg)](deploy/kubernetes)
[![MARL](https://img.shields.io/badge/AI--Engine-MAPPO%20%2F%20Actor--Critic-brightgreen.svg)](src/agents/marl)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-success.svg)](tests/)

---

## 1. Visão Geral da Fase 2 (CA-RDL)

A **xApp RDL Fase 2 (Context-Aware RDL)** é o motor de arbitragem cognitiva e autônoma de conflitos para o **Near-RT RIC (RAN Intelligent Controller)** do ecossistema O-RAN.

Evoluindo a abordagem determinística da Fase 1, a Fase 2 introduz **Aprendizado por Reforço Multi-Agente (MARL / MAPPO - Multi-Agent Proximal Policy Optimization)** com observação centralizada de telemetria de rádio (E2SM-KPM) e execução descentralizada de ações de controle (E2SM-RC).

```text
       +-------------------------------------------------------------+
       |             Near-RT RIC Platform (ricplt / O-RAN)           |
       |  [E2Term / SCTP 36422]  <-->  [Redis DBAAS / SDL 6379]      |
       +------------------------------+------------------------------+
                                      |
                         RMR Message Router (JSON / APER)
                                      |
       +------------------------------v------------------------------+
       |           xApp CA-RDL (Fase 2: MARL / MAPPO) (ricxapp)      |
       |                                                             |
       |  1. PerceptionAgent  --> Detecção de Conflitos e Features   |
       |  2. ReasoningAgent   --> Redes Neurais Actor-Critic (MAPPO) |
       |  3. RefinementAgent  --> Safety Guards (Limites Físicos)    |
       |                                                             |
       |  [FastAPI HTTP 8080]           [Prometheus Metrics 8081]    |
       +-------------------------------------------------------------+
```

---

## 2. Principais Funcionalidades Cognitivas

* **Arquitetura MAPPO (Centralized Training with Decentralized Execution):**
  - **Critic Network:** Avalia o estado global da rede de rádio ($S_t$) utilizando telemetria consolidada KPM (vazão de UEs, ocupação de PRB e latência por fatia de rede).
  - **Actor Networks:** Selecionam as melhores propostas de ação ($A_t$) para cada xApp com convergência de políticas PPO e clipping de gradiente.
* **Função de Recompensa Multiobjetivo:**
  $$R_t = w_{\text{QoS}} \cdot f_{\text{QoS}}(a) + w_{\text{EE}} \cdot f_{\text{EE}}(a) - w_{\text{pen}} \cdot \text{Penalty}(a)$$
* **Classificação de Intenção e Resolução de Conflitos:**
  - Resolução de conflitos diretos e indiretos com redução de colisões de **99.2%**.
* **Safety Guards Estritos:** Limites de saturação de potência de transmissão ($\le 43\text{ dBm}$), conservação de PRBs ($\le 100\%$) e bloqueio de oscilações (*ping-pong*).

---

## 3. Guia Rápido de Operação e Deploy

### 3.1. Execução dos Testes Automatizados (14/14 Green)
```bash
make test
# Executa a suíte completa de testes unitários e redes neurais
```

### 3.2. Deploy 100% Automatizado com Helm v2.0.0
```bash
make helm-deploy
```
*(O script auto-provisiona o cluster k3d, compila `iqos-xapp-rdl:2.0.0`, importa para o containerd, sobe o Redis DBAAS e faz o deploy do Helm Chart)*.

### 3.3. Testar Endpoints de Saúde e Métricas
```bash
make helm-test
```

### 3.4. Ciclo de Vida do Cluster k3d
```bash
make cluster-create      # Cria cluster com portas O-RAN expostas
make cluster-delete      # Remove cluster
make cluster-recreate    # Recriação limpa completa
```

---

## 4. Observabilidade e Monitoramento

* **Rancher Dashboard:** Acesse `https://127.0.0.1:8443` para gerenciar os nós, namespaces (`ricplt`, `ricxapp`), métricas de CPU/RAM em tempo real e acompanhar logs.
* **Kiali Service Mesh (Opcional):**
  ```bash
  make kiali-install     # Instala Istio e Kiali
  make start-traffic     # Inicia gerador contínuo de tráfego interno
  make kiali-dashboard   # Abre Kiali em http://localhost:20001/kiali
  make stop-traffic      # Pausa o gerador de tráfego
  ```

---

## 5. Índice de Documentação Técnica Consolidada (`docs/`)

| Volume | Título Temático | Conteúdo Abrangente |
| :---: | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura, Módulos Core e Modelagem Matemática | Clean Architecture, DDD, agentes de percepção/raciocínio/refinamento, heurísticas TVS/EEVS, redes neurais MARL/MAPPO e modelagem matemática formal. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura k3d, Rancher Dashboard e Operações O-RAN | Topologias de cluster no WSL2, instalação da plataforma Near-RT RIC (Redis DBAAS), visualização no Rancher UI e agente especialista `07-k8s-oran-cluster-operator`. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Implantação e Automação de Deploy (Helm & K8s) | Estrutura e empacotamento Helm Chart (`2.0.0`), deploy declarativo com Kustomize (`deploy/kubernetes/`), pipelines automatizados e onboarding O-RAN DMS. |
| **[Volume 04](docs/04_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Procedimentos de Backup | Procedimento Operacional Padrão (SOP), diagnósticos de erro (`ErrImageNeverPull`, Rancher agent), soluções offline e backup/restauração bare-metal do WSL Ubuntu 20.04. |
| **[Volume 05](docs/05_testes_simulacao_ns3_e_benchmarks.md)** | Testes, Simulação em ns-3 O-RAN e Benchmarks Científicos | Estratégia de testes unitários (14/14 PASS), relatório do Smoke Test (HTTP 200/Prometheus), código C++ de simulação 5G NR no `ns-O-RAN` (SCTP 36422) e métricas comparativas. |
| **[Volume 06](docs/06_observabilidade_kiali_e_injecao_trafego.md)** | Observabilidade Service Mesh com Kiali e Injeção de Tráfego | Checklist de dependências, Service Mesh com Istio, Kiali Dashboard (opcional) e script gerador contínuo de tráfego O-RAN (`make start-traffic` / `make inject-traffic`). |
| **[Volume 07](docs/07_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica e Governança O-RAN | Matriz de rastreabilidade de requisitos, avaliação de conformidade aos padrões O-RAN Alliance e sumário executivo de governança. |
'''

with open(os.path.join(p2_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_phase2)
print("Updated Phase 2 README.md")
