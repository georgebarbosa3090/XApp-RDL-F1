#!/usr/bin/env python3
"""
Script de Formalização da Documentação de Implantação e Experimentos da Fase 2 (CA-RDL / MARL)
Repositório: https://github.com/georgebarbosa3090/XApp-RDL-F2
"""

import os
import shutil

P1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P2_DIR = os.path.abspath(os.path.join(P1_DIR, "..", "iqos-xapp-rdl-phase2"))

def formalize_docs():
    print(f"Formalizando documentacao da Fase 2 em: {P2_DIR}")
    os.makedirs(os.path.join(P2_DIR, "docs"), exist_ok=True)
    os.makedirs(os.path.join(P2_DIR, "simulations", "ns3"), exist_ok=True)
    os.makedirs(os.path.join(P2_DIR, "scripts"), exist_ok=True)

    # -------------------------------------------------------------
    # 1. docs/03_guia_deploy_helm_e_k8s.md
    # -------------------------------------------------------------
    doc_deploy = """# Volume 03: Guia de Implantação e Operação no Kubernetes (Helm e K8s Nativo)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimentos de Deploy Helm v3, Kustomize K8s, Gestão de Cluster k3d, Roteamento RMR e Verificação de Endpoints  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão do Chart / Imagem:** `2.0.0` (Fase 2 - CA-RDL)  

---

## 1. Visão Geral da Arquitetura de Implantação

A **xApp RDL Fase 2** opera como um microserviço nativo em contêiner no namespace `ricxapp` do Near-RT RIC, integrando:
* **Tríade de Agentes Cognitivos:** Perception Agent, Reasoning Agent (Motor MAPPO/MARL) e Refinement Agent (Safety Guards).
* **Barramento de Mensageria RMR:** Portas `4560/TCP` (dados de controle E2) e `4561/TCP` (rotas dinâmicas).
* **Servidor HTTP de Ciclo de Vida:** Porta `8080/TCP` (`/health` e `/state`).
* **Servidor de Telemetria Prometheus:** Porta `8081/TCP` (`/metrics` com métricas `rdl_*`).
* **Persistência SDL (Shared Data Layer):** Redis no namespace `ricplt` ou Mock Resiliente em memória.

```mermaid
graph TD
    subgraph K8s["Cluster Kubernetes (k3d: rancher-lab)"]
        subgraph ricplt["Namespace: ricplt (Near-RT RIC Platform)"]
            E2TERM["E2Term (SCTP 36422 / RMR 38000)"]
            E2MGR["E2Mgr (HTTP 3800)"]
            SDL["Redis SDL (Porta 6379)"]
            RMR_RTG["RMR Route Generator (Porta 4561)"]
        end

        subgraph ricxapp["Namespace: ricxapp (Aplicações xApps)"]
            RDL["ricxapp-iqos-xapp-rdl (v2.0.0 - MARL)"]
            XS["ricxapp-qos-xslice (PRB Manager)"]
            ES["ricxapp-energy-saving (Tx Power Manager)"]
            TS["ricxapp-traffic-steering (Handover Manager)"]
        end
    end

    E2TERM <-->|RMR E2AP/KPM| RDL
    RDL <-->|RMR Control Actions| XS
    RDL <-->|RMR Control Actions| ES
    RDL <-->|RMR Control Actions| TS
    RDL <-->|SDL State| SDL
```

---

## 2. Pré-requisitos de Infraestrutura

1. **Docker Engine:** 20.10+ com suporte a contêineres Linux.
2. **Kubernetes CLI (`kubectl`):** v1.26+.
3. **Helm:** v3.10+.
4. **k3d / k3s:** v5.4+ (para orquestração local leve de clusters O-RAN).
5. **Python:** 3.10+ (para testes unitários e pipelines de simulação).

---

## 3. Criação e Configuração do Cluster k3d

Para instanciar o cluster local com todas as portas de rede necessárias mapeadas para o host:

```bash
# Criação do cluster k3d com portas O-RAN e Near-RT RIC
make cluster-create

# Verificar status dos nós
kubectl get nodes -o wide
```

As seguintes portas são expostas no host:
* `36422/SCTP`: Interface O-RAN E2 para conexão com o simulador ns-3.
* `8080-8087/TCP`: Endpoints HTTP REST das xApps e RIC Platform.
* `4560-4561/TCP`: Barramento de Mensageria RMR.

---

## 4. Implantação via Helm Charts (Padrão O-RAN Alliance)

A Fase 2 disponibiliza 4 Helm Charts modulares:
1. `deploy/helm/iqos-xapp-rdl` (Chart v2.0.0 da xApp RDL com MARL)
2. `deploy/helm/xapp-qos-xslice` (Chart da Reference xApp de Fatiamento)
3. `deploy/helm/xapp-energy-saving` (Chart da Reference xApp de Economia de Energia)
4. `deploy/helm/xapp-traffic-steering` (Chart da Reference xApp de Direcionamento de Tráfego)

### 4.1. Deploy Completo com Governança RDL Ativa (Modo Proposta):
```bash
# Empacota e instala todos os Helm Charts no namespace ricxapp
make helm-deploy

# Ou execute diretamente o script shell:
bash scripts/deploy_helm.sh --with-rdl
```

### 4.2. Deploy em Modo Baseline (Sem RDL - Para Benchmarks de Comparação):
```bash
make helm-deploy-baseline
```

### 4.3. Verificação do Status dos Pods:
```bash
kubectl get pods -n ricxapp -o wide
kubectl get pods -n ricplt -o wide
```

---

## 5. Validação de Endpoints e Smoke Testing

### 5.1. Teste de Saúde e Conectividade das xApps:
```bash
# Executa o script de validação das 3 Reference xApps + RDL
make test-3xapps
# ou: bash scripts/verify_3_xapps.sh
```

### 5.2. Verificação Manual dos Endpoints HTTP e Prometheus:
```bash
# 1. Healthcheck da xApp RDL
curl -i http://localhost:8080/health
# Resposta esperada: HTTP/1.1 200 OK  {"status": "UP", "phase": "2.0.0"}

# 2. Métricas Prometheus de Governança e Decisão MARL
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"
```

### 5.3. Logs Estruturados em Tempo Real:
```bash
make logs
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -f
```

---

## 6. Desinstalação e Limpeza

```bash
# Remoção dos Helm releases
make helm-uninstall

# Destruição completa do cluster k3d
make cluster-delete
```
"""

    with open(os.path.join(P2_DIR, "docs", "03_guia_deploy_helm_e_k8s.md"), "w", encoding="utf-8") as f:
        f.write(doc_deploy)
    print("[OK] docs/03_guia_deploy_helm_e_k8s.md formalizado.")

    # -------------------------------------------------------------
    # 2. docs/05_testes_simulacao_ns3_e_benchmarks.md
    # -------------------------------------------------------------
    doc_sim = """# Volume 05: Guia de Simulação 5G NR no ns-3, Testes Automatizados e Benchmarks Científicos

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Co-Simulação 5G NR no ns-3 (5G-LENA + NORI), Arquitetura EpcHelper (Plano de Usuário), Conexão E2 ao Near-RT RIC, Pipeline de Benchmarks e Análise de ML  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Arquitetura da Co-Simulação ns-3 / 5G-LENA

A validação experimental da Fase 2 é executada no simulador de eventos discretos **ns-3 v3.40** com os módulos:
* **5G-LENA (CTTC-LENA NR):** Pilha completa 3GPP Release 15/16/17 (PHY, MAC, RLC, PDCP, SDAP, BWP, Beamforming e Canais 3GPP TR 38.901).
* **ns-O-RAN / NORI:** Implementação de nós E2 Agent na gNodeB com conectividade SCTP para o Near-RT RIC.
* **NrPointToPointEpcHelper (User Plane Core):** Roteamento IP fim a fim com tunelamento GTP-U e mapeamento de portadores de QoS (5QI).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      Arquitetura de Co-Simulação ns-3 / 5G-LENA                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [Remote Host] (Servidor de Aplicações de Tráfego UDP/TCP)                            │
│         │                                                                              │
│   (Enlace Ponto a Ponto - Backhaul)                                                    │
│         │                                                                              │
│   [PGW / SGW] (Core Gateway - Instanciado via NrPointToPointEpcHelper)                 │
│         │ (Tunelamento GTP-U / S1-U / N3)                                              │
│   [gNodeB 5G NR] ◄──────── (Interface E2 / SCTP 36422) ────────► [Near-RT RIC (xApps)] │
│         │                                                                              │
│     (3.5 GHz n78 - 3GPP NR PHY/MAC/RLC/PDCP)                                           │
│         │                                                                              │
│   [UEs: URLLC / eMBB / mMTC]                                                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Por que o uso de `NrPointToPointEpcHelper` é o padrão canônico?
1. **Conformidade com a Arquitetura O-RAN:** A interface E2 termina na gNodeB (`E2AgentHelper`). O Near-RT RIC é completamente desacoplado dos microserviços de sinalização HTTP/2 SBA do 5GC.
2. **Plano de Dados Realista (GTP-U):** Encapsula os pacotes em túneis com enlace de backhaul configurável (latência e taxa), sem o overhead excessivo de emular o plano de controle SBA do Core.
3. **Mapeamento de Fatias (5QI):** Permite instanciar *Dedicated EPS/5G Bearers* com filtros TFT específicos para fluxos URLLC (5QI 82), eMBB (5QI 9) e mMTC (5QI 79).

---

## 2. Cenários de Simulação Implementados em C++

Os cenários estão disponíveis em `simulations/ns3/`:
1. **`scenario_rdl_tvs_conflict.cc`:** Conflito direto de PRBs e potência entre xSlice e Energy Saving em topologia multicelular densa (3.5 GHz Banda n78, 100 MHz, numerologia $\mu=1$).
2. **`scenario_rdl_energy_vs_qos.cc`:** Trade-off dinâmico entre economia de energia e cumprimento estrito de SLA URLLC ($<5\text{ ms}$).

### Compilação e Execução dos Cenários no ns-3:
```bash
# 1. Configurar o ambiente ns-3 com CMake e Ninja
make setup-ns3

# 2. Executar cenário Baseline (Sem mediação RDL)
make run-baseline

# 3. Executar cenário com RDL Fase 2 (Mediação MARL via E2)
make run-rdl
```

---

## 3. Suíte de Testes Automatizados (Pytest)

A suíte unitária da Fase 2 cobre 100% dos componentes:
* Codecs APER E2AP, E2SM-KPM e E2SM-RC (`tests/test_aper_codecs.py`)
* Coordenação e Inferência MAPPO (`tests/test_marl_mappo.py`)
* Agentes de Percepção, Raciocínio e Refinamento (`tests/test_*_agent.py`)
* Tríades de conflito das Reference xApps (`tests/test_reference_xapps.py`)

```bash
# Execução dos 18 testes unitários
make test
# Saída esperada: 18 passed in < 1s (100% green)
```

---

## 4. Pipeline de Benchmarks e Estrutura de Resultados por Data

O orquestrador `scripts/run_experiment_suite.py` executa o pipeline experimental completo:
1. Coleta traces brutos (`RxPacketTrace.txt`, `flowmonitor_results.xml`, logs RDL).
2. Processa métricas de rede (latência URLLC, P95, P99, PDR, Throughput, Jain's Index).
3. Treina e valida os 6 modelos de Machine Learning / Ensembles.
4. Gera gráficos comparativos em alta resolução (300 DPI) e relatórios Markdown e JSON.
5. Salva em diretório isolado por data e timestamp: `experiments/results/YYYY-MM-DD/run_HHMMSS/` sem sobrescrever execuções anteriores.
6. Sincroniza automaticamente com o repositório GitHub (`origin main`).

### Execução da Suíte Completa:
```bash
# Executa simulação, benchmarks, ML e push para GitHub
make run-suite
# ou: python3 scripts/run_experiment_suite.py --push
```

---

## 5. Estrutura dos Resultados Gerados

```
experiments/results/
├── 2026-08-31/
│   ├── run_113445/
│   │   ├── dataset_flow_metrics.csv
│   │   ├── dataset_rdl_decisions_ml.csv
│   │   ├── relatorio_comparativo.md
│   │   ├── relatorio_comparativo_detalhado.md
│   │   ├── avaliacao_completa_metricas.json
│   │   ├── graficos_benchmarks_rdl.png
│   │   ├── comparativo_completo_cenarios_rdl.png
│   │   ├── avaliacao_modelos_ml_rdl.png
│   │   └── relatorio_tecnico_experimentos_2026-08-31.tex
└── latest/               <-- Espelho da última execução para compatibilidade
```
"""

    with open(os.path.join(P2_DIR, "docs", "05_testes_simulacao_ns3_e_benchmarks.md"), "w", encoding="utf-8") as f:
        f.write(doc_sim)
    print("[OK] docs/05_testes_simulacao_ns3_e_benchmarks.md formalizado.")

    # -------------------------------------------------------------
    # 3. README.md da Fase 2
    # -------------------------------------------------------------
    readme_content = """# xApp RDL - Fase 2: Context-Aware Resource and Decision Layer (CA-RDL / MARL)

[![Open RAN](https://img.shields.io/badge/O--RAN-Near--RT--RIC-orange.svg)](https://o-ran.org)
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)](https://github.com/georgebarbosa3090/XApp-RDL-F2)
[![Helm](https://img.shields.io/badge/Helm-v3%20Chart%202.0.0-informational.svg)](deploy/helm/iqos-xapp-rdl)
[![Kubernetes](https://img.shields.io/badge/K8s-Native%20Kustomize-326CE5.svg)](deploy/kubernetes)
[![MARL](https://img.shields.io/badge/AI--Engine-MAPPO%20%2F%20Actor--Critic-brightgreen.svg)](src/agents/marl)
[![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passing-success.svg)](tests/)

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote (200ms), heurísticas TVS/EEVS e Safety Guards físicos.* | **Concluída e Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2 (Atual)** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (MARL / MAPPO) e cognição contextual.* | **Ativa / Em Produção** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (Intent-Driven) e O-Cloud 6G.* | **Roadmap / Planejada** | *Em especificação futura* |

---

## 1. Visão Geral da Fase 2 (CA-RDL)

A **xApp RDL Fase 2 (Context-Aware RDL)** é o motor de arbitragem cognitiva e autônoma de conflitos para o **Near-RT RIC (RAN Intelligent Controller)** do ecossistema O-RAN.

Evoluindo a abordagem determinística da Fase 1, a Fase 2 introduz **Aprendizado por Reforço Multi-Agente (MARL / MAPPO - Multi-Agent Proximal Policy Optimization)** com:
1. **Crítico Centralizado:** Observação global do estado de rádio da rede (SINR, PRBs, carga, interferência, potência).
2. **Atores Descentralizados:** Decisões probabilísticas por fatia de rede e xApp concorrente.
3. **Recompensa Multi-Objetivo:** Otimização conjunta de Latência URLLC, Throughput eMBB, Eficiência Energética e Equidade de Jain.
4. **Safety Guards de Proteção:** Barreiras determinísticas que impedem violações de limites físicos ou SLAs 3GPP.

```mermaid
graph TD
    subgraph NearRTRIC["Near-RT RIC (O-RAN)"]
        subgraph RDL_F2["xApp RDL Fase 2 (CA-RDL / MARL)"]
            PA["1. Perception Agent<br/>(Telemetria KPM & Feature Engineering)"]
            RA["2. Reasoning Agent<br/>(Motor MAPPO Centralized-Critic)"]
            RE["3. Refinement Agent<br/>(Safety Guards Determinísticos)"]
            IC["4. Intent Classifier<br/>(Modulação de Pesos de Recompensa)"]
        end

        XAPPS["Reference xApps Concorrentes<br/>(xSlice | Energy Saving | Traffic Steering)"]
    end

    gNB["gNodeB 5G NR (ns-3 / 5G-LENA)"] <-->|E2SM-KPM / E2SM-RC| NearRTRIC
    XAPPS -->|Ações Propostas| PA
    PA --> RA
    IC --> RA
    RA --> RE
    RE -->|Ações Harmonizadas| gNB
```

---

## 2. Início Rápido (Quickstart)

### 2.1. Executar Testes Unitários:
```bash
make test
# 18/18 testes passando com 100% de sucesso
```

### 2.2. Implantar no Kubernetes / Near-RT RIC:
```bash
# Criar cluster k3d e fazer deploy dos 4 Helm Charts
make cluster-create
make helm-deploy
```

### 2.3. Executar Simulação ns-3 e Benchmarks:
```bash
# Executa pipeline completo, gera datasets e relatórios
make run-suite
```

---

## 3. Estrutura Documental da Fase 2

| Volume Documental | Título do Documento | Descrição e Escopo |
| :--- | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura de Software e Modelagem Matemática | Tríade de agentes, formulação MAPPO/Actor-Critic e modelagem de utilidade. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura de Cluster k3d e Rancher | Provisionamento de cluster Kubernetes com portas O-RAN expostas. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Implantação Helm e K8s Nativo | Deploy dos 4 Helm Charts, barramento RMR e validação de endpoints. |
| **[Volume 04](docs/04_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Backup | Procedimentos operacionais, diagnóstico de logs e recuperação. |
| **[Volume 05](docs/05_testes_simulacao_ns3_e_benchmarks.md)** | Simulação ns-3, Testes e Benchmarks | Co-simulação 5G-LENA + NORI, `NrPointToPointEpcHelper` e datasets. |
| **[Volume 06](docs/06_observabilidade_kiali_e_injecao_trafego.md)** | Observabilidade Service Mesh e Tráfego | Métricas Prometheus, dashboards e injeção de tráfego sintético. |
| **[Volume 07](docs/07_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica O-RAN | Matriz de rastreabilidade de requisitos e conformidade O-RAN Alliance. |

---

## 4. Repositórios Oficiais

* **Fase 1 (H-RDL Determinística):** [https://github.com/georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)
* **Fase 2 (CA-RDL / MARL):** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)
"""

    with open(os.path.join(P2_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("[OK] README.md formalizado na Fase 2.")
    print("\nFormalizacao documental da Fase 2 concluida com sucesso!")

if __name__ == "__main__":
    formalize_docs()
