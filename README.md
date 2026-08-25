# xApp RDL (Resource and Decision Layer) - O-RAN Conflict Mitigation

## 1. Visão Geral
A **xApp RDL** é um orquestrador determinístico e cognitivo para o O-RAN Near-RT RIC. Sua principal função é arbitrar intenções de controle concorrentes provenientes de múltiplas xApps em uma rede, decidindo a alocação ótima de recursos utilizando regras determinísticas e funções de utilidade multiobjetivo (**Fase 1: H-RDL**) e modelos de aprendizado por reforço multi-agente MARL/MAPPO (**Fase 2: CA-RDL**).

---

## 2. Estrutura Arquitetural
A arquitetura foi desenhada utilizando **Clean Architecture** e **Domain-Driven Design (DDD)**:
* `src/agents/`: Motores de percepção (Decision Window de 200ms), raciocínio (Heurísticas TVS/EEVS e MAPPO) e *Safety Guards*.
* `src/coordination/`: Despachante de controle e correlacionador de ACKs.
* `src/domain/`: Entidades imutáveis (`Proposals`, `Conflicts`, `Decisions`).
* `src/e2/`: Decodificadores e encoders E2AP / KPM e E2SM-RC Control (isolamento ASN.1 APER).
* `src/infrastructure/`: Clientes RMR (`RMRXapp`), SDL (Redis), Subscription Manager e Config Manager.
* `src/observability/`: Métricas no padrão Prometheus na porta 8081 (`/metrics`), healthcheck na porta 8080 (`/health`) e logs estruturados em JSON.

---

## 3. Guia de Execução Rápida

### Opção A: Deploy Helm Automatizado (Recomendado)
Compila o container, importa automaticamente nos nós `k3d`, empacota o Helm Chart e faz o deploy:
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

### Opção D: Testes Unitários
```bash
make test
```

---

## 4. Observabilidade e Monitoramento

* **Rancher Dashboard (Padrão):** Acesse `https://127.0.0.1:8443` para gerenciar nós, namespaces (`ricplt`, `ricxapp`), ver gráficos de consumo de CPU/RAM em tempo real e acompanhar logs.
* **Kiali Service Mesh (Opcional):** Para visualização em grafo animado da topologia de rede entre xApps e o RIC, instale opcionalmente com `make kiali-install` e abra em `make kiali-dashboard` (`http://localhost:20001/kiali`).
* **Injetor de Tráfego O-RAN:** Para ver o grafo animado no Kiali com tráfego em tempo real, execute `make inject-traffic`.
* **Testes de Endpoints:**
  ```bash
  make helm-test   # ou make k8s-test
  ```
* **Logs em Tempo Real:**
  ```bash
  make logs
  ```

---

## 5. Índice de Documentação Técnica Consolidada (`docs/`)

| Volume | Título Temático | Conteúdo Abrangente |
| :---: | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura, Módulos Core e Modelagem Matemática | Clean Architecture, DDD, agentes de percepção/raciocínio/refinamento, heurísticas TVS/EEVS, protocolos E2AP/KPM/RC/RMR e modelagem matemática. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura k3d, Rancher Dashboard e Operações O-RAN | Topologias de cluster no WSL2 (1S+1A vs Single-Node), instalação do Near-RT RIC, visualização no Rancher UI e agente especialista `07-k8s-oran-cluster-operator`. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Implantação e Automação de Deploy (Helm & K8s) | Estrutura e empacotamento Helm Chart (`1.1.0`), deploy declarativo com Kustomize (`deploy/kubernetes/`), pipelines automatizados e onboarding O-RAN DMS. |
| **[Volume 04](docs/04_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Procedimentos de Backup | Procedimento Operacional Padrão (SOP), diagnósticos de erro (`ErrImageNeverPull`, Rancher agent), soluções offline e backup/restauração bare-metal do WSL Ubuntu 20.04. |
| **[Volume 05](docs/05_testes_simulacao_ns3_e_benchmarks.md)** | Testes, Simulação em ns-3 O-RAN e Benchmarks Científicos | Estratégia de testes unitários (10/10 PASS), relatório do Smoke Test (HTTP 200/Prometheus), código C++ de simulação 5G NR no `ns-O-RAN` (SCTP 36422) e métricas comparativas. |
| **[Volume 06](docs/06_observabilidade_kiali_e_injecao_trafego.md)** | Observabilidade Service Mesh com Kiali e Injeção de Tráfego | Checklist de dependências, Service Mesh com Istio, Kiali Dashboard (opcional) e script gerador contínuo de tráfego O-RAN (`make inject-traffic`). |
| **[Volume 07](docs/07_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica, Governança e Manual Consolidado | Matriz de rastreabilidade de requisitos, avaliação de conformidade aos padrões O-RAN Alliance e sumário executivo de governança. |
