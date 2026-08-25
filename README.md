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

* **Rancher Dashboard:** Acesse `https://127.0.0.1:8443` para gerenciar nós, namespaces (`ricplt`, `ricxapp`), ver gráficos de consumo de CPU/RAM em tempo real e acompanhar logs.
* **Kiali Service Mesh:** Acesse `http://localhost:20001/kiali` para visualizar a topologia gráfica animada das mensagens RMR e HTTP entre as xApps e o RIC.
* **Testes de Endpoints:**
  ```bash
  make helm-test   # ou make k8s-test
  ```
* **Logs em Tempo Real:**
  ```bash
  make logs
  ```

---

## 5. Índice de Documentação Técnica (`docs/`)

| Documento | Descrição |
| :--- | :--- |
| **[00_introducao.md](docs/00_introducao.md)** | Visão geral do problema de conflito de xApps no O-RAN. |
| **[01_arquitetura.md](docs/01_arquitetura.md)** | Arquitetura DDD, Clean Architecture e fluxo de mensagens. |
| **[02_modulos_core.md](docs/02_modulos_core.md)** | Módulos de domínio, coordenação e infraestrutura. |
| **[03_modulos_heuristica.md](docs/03_modulos_heuristica.md)** | Algoritmos de resolução determinística (TVS e EEVS). |
| **[04_comunicacao_ric.md](docs/04_comunicacao_ric.md)** | Protocolos E2AP, E2SM-KPM, E2SM-RC e RMR. |
| **[05_testes_e_ci.md](docs/05_testes_e_ci.md)** | Estratégia de testes unitários e CI/CD. |
| **[06_guia_de_implantacao.md](docs/06_guia_de_implantacao.md)** | Implantação e operação no cluster Kubernetes. |
| **[07_modelagem_matematica.md](docs/07_modelagem_matematica.md)** | Funções de utilidade e modelagem formal. |
| **[08_guia_instalacao_osc_near_rt_ric.md](docs/08_guia_instalacao_osc_near_rt_ric.md)** | Instalação da plataforma Near-RT RIC da OSC. |
| **[09_cenarios_de_teste_e_benchmark_fase1_fase2.md](docs/09_cenarios_de_teste_e_benchmark_fase1_fase2.md)** | Cenários de teste e métricas comparativas. |
| **[10_relatorio_smoke_test_fase1.md](docs/10_relatorio_smoke_test_fase1.md)** | Relatório de aprovação do Smoke Test (HTTP 200 e Prometheus). |
| **[11_guia_empacotamento_helm_e_sincronizacao_github.md](docs/11_guia_empacotamento_helm_e_sincronizacao_github.md)** | Empacotamento Helm e onboarding O-RAN DMS. |
| **[12_guia_cenario_ns3_oran_benchmark.md](docs/12_guia_cenario_ns3_oran_benchmark.md)** | Simulação 5G NR no ns-O-RAN com E2 Agent. |
| **[13_guia_operacional_deploy_helm_e_backup_wsl.md](docs/13_guia_operacional_deploy_helm_e_backup_wsl.md)** | Procedimento Operacional Padrão (SOP) e backup WSL. |
| **[14_troubleshooting_helm_deploy_e_solucao_offline.md](docs/14_troubleshooting_helm_deploy_e_solucao_offline.md)** | Resolução autônoma de falhas de diretório e deploy offline. |
| **[15_topologias_cluster_k3d_oran_wsl.md](docs/15_topologias_cluster_k3d_oran_wsl.md)** | Análise comparativa de topologias (1S+1A vs Single-Node). |
| **[16_automacao_deploy_helm.md](docs/16_automacao_deploy_helm.md)** | Pipeline 100% automatizado de deploy Helm. |
| **[17_guia_deploy_kubernetes_puro_k8s.md](docs/17_guia_deploy_kubernetes_puro_k8s.md)** | Guia de implantação em Kubernetes puro com Kustomize. |
| **[18_guia_visualizacao_rancher_dashboard_oran.md](docs/18_guia_visualizacao_rancher_dashboard_oran.md)** | Manual de navegação e visualização no Rancher UI. |
| **[19_agente_especialista_cluster_k8s_oran.md](docs/19_agente_especialista_cluster_k8s_oran.md)** | Especificação do agente especialista `07-k8s-oran-cluster-operator`. |
| **[20_checklist_dependencias_e_observabilidade_kiali.md](docs/20_checklist_dependencias_e_observabilidade_kiali.md)** | Checklist de dependências e observabilidade de fluxo com Kiali. |
