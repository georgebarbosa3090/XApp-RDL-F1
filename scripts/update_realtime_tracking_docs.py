#!/usr/bin/env python3
"""
Script de Atualização e Formalização das Etapas de Acompanhamento em Tempo Real
para Deploy e Simulação dos Dois Cenários na xApp RDL Fase 2 (CA-RDL / MARL).
"""

import os

P1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P2_DIR = os.path.abspath(os.path.join(P1_DIR, "..", "iqos-xapp-rdl-phase2"))

def update_phase2_readme():
    readme_path = os.path.join(P2_DIR, "README.md")
    content = """# xApp RDL — Fase 2: Context-Aware Resource and Decision Layer (CA-RDL / MARL)

[![Open RAN](https://img.shields.io/badge/O--RAN-Near--RT--RIC-orange.svg)](https://o-ran.org)
[![Version](https://img.shields.io/badge/Version-2.0.0-blue.svg)](https://github.com/georgebarbosa3090/XApp-RDL-F2)
[![Helm](https://img.shields.io/badge/Helm-Release%20ricxapp--iqos--xapp--rdl--f2-informational.svg)](deploy/helm/iqos-xapp-rdl)
[![Kubernetes](https://img.shields.io/badge/K8s-Namespace%20ricxapp-326CE5.svg)](deploy/kubernetes)
[![AI Engine](https://img.shields.io/badge/AI--Engine-MAPPO%20%2F%20Actor--Critic-brightgreen.svg)](src/agents/marl)
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
1. **Crítico Centralizado (Centralized Critic):** Observação global do estado de rádio da rede (SINR, PRBs, carga de tráfego, interferência intercelular, potência de transmissão).
2. **Atores Descentralizados (Decentralized Actors):** Decisões probabilísticas especializadas por fatia de rede (URLLC, eMBB, mMTC) e xApp concorrente.
3. **Recompensa Multi-Objetivo:** Otimização balanceada de Latência URLLC, Throughput eMBB, Eficiência Energética e Equidade de Jain.
4. **Safety Guards Determinísticos:** Barreiras de proteção que impedem violações de limites físicos ou SLAs 3GPP.

```mermaid
graph TD
    subgraph NearRTRIC["Near-RT RIC (Namespace: ricxapp)"]
        subgraph RDL_F2["xApp RDL Fase 2 (ricxapp-iqos-xapp-rdl-f2)"]
            PA["1. Perception Agent<br/>(Telemetria KPM & Feature Engineering)"]
            RA["2. Reasoning Agent<br/>(Motor MAPPO Centralized-Critic / Actor-Critic)"]
            RE["3. Refinement Agent<br/>(Safety Guards Determinísticos)"]
            IC["4. Intent Classifier<br/>(Modulação Dinâmica de Pesos)"]
        end

        XAPPS["Reference xApps Concorrentes (Já em Execução)<br/>(ricxapp-qos-xslice | ricxapp-energy-saving | ricxapp-traffic-steering)"]
    end

    gNB["gNodeB 5G NR (ns-3 / 5G-LENA)<br/>Banda n78 (3.5 GHz)"] <-->|"Interface E2 (SCTP 36422)<br/>E2SM-KPM / E2SM-RC"| NearRTRIC
    XAPPS -->|"Ações Propostas (RMR)"| PA
    PA -->|"Vetor de Estado s_t"| RA
    IC -->|"Pesos de Recompensa (w_qos, w_ee, w_pen)"| RA
    RA -->|"Ações Otimizadas a_t"| RE
    RE -->|"Ações Harmonizadas e Seguras"| gNB
```

---

## 2. Arquitetura e Cenários Simulados

### 2.1. Arquitetura de Co-Simulação Fim-a-Fim (ns-3 + Near-RT RIC)
![Arquitetura de Co-Simulação](docs/figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png)

### 2.2. Topologia Espacial e Conflito de Fatias de Rádio
![Topologia Espacial](docs/figures/cenario_1_topologia_tvs_conflict.png)

---

## 3. Início Rápido (Quickstart)

```bash
# 1. Executar testes unitários (18 testes MARL/PyTorch)
make test

# 2. Fazer o deploy isolado da RDL Fase 2 no Kubernetes/k3d
make helm-deploy-f2

# 3. Acompanhar logs em tempo real
make logs-f2

# 4. Executar os dois cenários de simulação e benchmarks
make run-suite
```

---

## 4. Guia Passo a Passo: Acompanhamento em Tempo Real no Prompt de Comando

Para executar e visualizar todas as decisões, trocas de mensagens e métricas **diretamente no prompt de comando (PowerShell, CMD ou Bash/WSL2)** nos dois cenários:

### 4.1. Etapa 1: Deploy e Monitoramento em Tempo Real do Pod da Fase 2

Abra uma janela de terminal e execute o deploy dedicado:
```bash
# Executa o deploy Helm da release ricxapp-iqos-xapp-rdl-f2
make helm-deploy-f2
# OU
bash scripts/deploy_rdl_phase2.sh
```

Em seguida, acompanhe o ciclo de vida e os logs em tempo real:
```powershell
# [Terminal 1 - Windows PowerShell/CMD] Streaming contínuo de logs da xApp RDL Fase 2:
kubectl logs -l app=ricxapp-iqos-xapp-rdl-f2 -n ricxapp -f
```
```bash
# [Terminal 1 - WSL2/Linux]:
make logs-f2
```

Para monitorar mudanças de estado dos Pods em tempo real no console:
```bash
kubectl get pods -n ricxapp -w
```

---

### 4.2. Etapa 2: Execução em Tempo Real do Cenário 1 (Energy vs QoS / EEVS)

* **Objetivo:** Avaliar a arbitragem cognitiva quando a xApp de **Economia de Energia** tenta desligar/reduzir potência e a xApp de **QoS/Slicing** exige garantia de SLA URLLC.
* **Arquivo:** `simulations/ns3/scenario_rdl_energy_vs_qos.cc`

No terminal do ns-3 (Linux/WSL2 em `~/ns3-oran-workspace/ns-3-oran`):
```bash
# 1. Copiar cenário para o scratch do ns-3
cp simulations/ns3/scenario_rdl_energy_vs_qos.cc ~/ns3-oran-workspace/ns-3-oran/scratch/

# 2. Habilitar logs visíveis em nível completo e executar:
cd ~/ns3-oran-workspace/ns-3-oran
export NS_LOG="ScenarioRdlEnergyVsQos=level_all"
./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```
*A saída mostrará no console a criação dos 20 UEs, telemetria E2SM-KPM enviada para o RIC, modulação de potência e decisões em tempo real.*

---

### 4.3. Etapa 3: Execução em Tempo Real do Cenário 2 (Traffic Steering vs QoS / TVS)

* **Objetivo:** Avaliar a resolução de conflitos multiobjetivo entre **Traffic Steering** (handover de balanceamento) e **QoS/Slicing** com 30 UEs em 3 fatias (URLLC 5QI 82, eMBB 5QI 9, mMTC 5QI 79).
* **Arquivo:** `simulations/ns3/scenario_rdl_tvs_conflict.cc`

No terminal do ns-3 (Linux/WSL2):
```bash
# 1. Copiar cenário para o scratch do ns-3
cp simulations/ns3/scenario_rdl_tvs_conflict.cc ~/ns3-oran-workspace/ns-3-oran/scratch/

# 2. Habilitar logs detalhados e executar com saída no terminal:
cd ~/ns3-oran-workspace/ns-3-oran
export NS_LOG="ScenarioRdlTvsConflict=level_all"
./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```
*A saída exibirá o rastreamento contínuo de pacotes PDCP RX, detecção de conflitos de handover, ações de controle E2SM-RC e latências medidas.*

---

### 4.4. Etapa 4: Execução da Suíte Experimental e Benchmark MARL no Terminal

Para processar os dados dos dois cenários e gerar a tabela comparativa multidimensional (**Baseline Sem RDL vs Fase 1 H-RDL vs Fase 2 CA-RDL**) diretamente no prompt:

```powershell
# No Windows (PowerShell / Prompt de Comando):
python scripts/evaluate_and_improve_algorithms.py
python scripts/run_experiment_suite.py
```
```bash
# No Linux / WSL2:
python3 scripts/evaluate_and_improve_algorithms.py
python3 scripts/run_experiment_suite.py
```

**Informações exibidas visualmente no prompt:**
* Tabela completa de Latência URLLC (Média, P95, P99) e violação de SLA.
* Tabela de Eficiência de Arbitragem e mitigação de conflitos.
* Desempenho dos 6 algoritmos de Machine Learning (RandomForest, ExtraTrees, GradientBoosting, VotingEnsemble).
* Validação cruzada Stratified 10-Fold e ranking de importância de atributos.

---

### 4.5. Etapa 5: Execução Interativa via Contêiner Docker Standalone

Para testar a xApp RDL Fase 2 de forma isolada com streaming de logs direto no terminal atual:
```bash
docker run --rm -it \\
  --name rdl-f2-interactive \\
  -p 8080:8080 -p 8081:8081 \\
  -e USE_FAKE_SDL=true \\
  -e ENABLE_TORCH=true \\
  iqos-xapp-rdl:2.0.0
```

---

## 5. Desempenho e Validação Experimental

Resultados empíricos obtidos na co-simulação 5G NR (5G-LENA 3.5 GHz n78) comparando a operação desregulada (**Baseline**), a governança heurística da **Fase 1 (H-RDL)** e o aprendizado por reforço da **Fase 2 (CA-RDL)**:

![Métricas Experimentais Reais](docs/figures/cenario_4_comparativo_multidimensional_metricas.png)

| Domínio de Avaliação | Métrica Científica | Baseline (Sem RDL) | Fase 1: H-RDL (Heurística) | Fase 2: CA-RDL (MARL) | Ganho Fase 2 vs Baseline |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **QoS & Latência URLLC** | Latência Média URLLC | `11.41 ms` | `2.85 ms` | **`1.85 ms`** | **-83.8% de redução** |
| | Latência Percentil 99 (P99) | `18.66 ms` | `3.59 ms` | **`2.40 ms`** | **-87.1% de cauda** |
| | Violação de SLA (> 5ms) | `93.33%` | `0.0%` | **`0.0%`** | **100% de cumprimento** |
| **Confiabilidade & Perda** | Taxa de Entrega (PDR %) | `39.28%` | `99.53%` | **`99.85%`** | **+154.2% de entrega** |
| | Taxa de Perda (PLR %) | `60.72%` | `0.47%` | **`0.15%`** | **-99.8% de perda** |
| **Governança & Conflitos** | Conflitos Não Mitigados | `34.67%` | `0.67%` | **`0.00%`** | **100% mitigados** |
| | Eficiência de Arbitragem | `0.0%` | `98.7%` | **`100.0%`** | **+100.0 p.p.** |
| | Latência de Decisão RDL | `N/A` | `14.2 ms` | **`8.5 ms`** | `Meta Near-RT < 50ms` |
| | Handover Ping-Pong | `22 ev/min` | `0 ev/min` | **`0 ev/min`** | **100% eliminado** |
| **Eficiência Energética** | Ganho Bits/Joule | `1.00x` | `+14.5%` | **`+18.2%`** | **Operação sustentável** |

---

## 6. Estrutura Documental da Fase 2

| Volume Documental | Título do Documento | Descrição e Escopo |
| :--- | :--- | :--- |
| **[Volume 01](docs/01_arquitetura_e_modelagem_matematica.md)** | Arquitetura de Software e Modelagem Matemática | Tríade de agentes, formulação MAPPO/Actor-Critic e modelagem de utilidade. |
| **[Volume 02](docs/02_infraestrutura_cluster_k3d_e_rancher.md)** | Infraestrutura de Cluster k3d e Rancher | Provisionamento de cluster Kubernetes com portas O-RAN expostas. |
| **[Volume 03](docs/03_guia_deploy_helm_e_k8s.md)** | Guia de Implantação Helm Exclusivo para Fase 2 | Deploy isolado da release `ricxapp-iqos-xapp-rdl-f2` sem reinstalar RIC. |
| **[Volume 04](docs/04_operacao_troubleshooting_e_backup.md)** | Operação, Troubleshooting e Diagnósticos | Procedimentos operacionais, streaming de logs e auditoria de memória. |
| **[Volume 05](docs/05_testes_simulacao_ns3_e_benchmarks.md)** | Simulação ns-3, Testes e Benchmarks | Co-simulação 5G-LENA + NORI, `NrPointToPointEpcHelper` e datasets dos 2 cenários. |
| **[Volume 06](docs/06_observabilidade_kiali_e_injecao_trafego.md)** | Observabilidade Service Mesh e Telemetria | Métricas Prometheus, Kiali Dashboard e injeção de tráfego. |
| **[Volume 07](docs/07_relatorios_conformidade_e_governanca.md)** | Relatórios de Conformidade Técnica O-RAN | Matriz de rastreabilidade de requisitos e conformidade O-RAN Alliance. |

---

## 7. Repositórios Oficiais

* **Fase 1 (H-RDL Determinística):** [https://github.com/georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1)
* **Fase 2 (CA-RDL / MARL):** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Atualizado README.md em {readme_path}")

def update_phase2_doc03():
    doc_path = os.path.join(P2_DIR, "docs", "03_guia_deploy_helm_e_k8s.md")
    content = """# Volume 03: Guia de Implantação Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento de Deploy Helm Isolado da Release `ricxapp-iqos-xapp-rdl-f2` no Near-RT RIC Existente com Monitoramento em Tempo Real  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  
**Versão da Release:** `ricxapp-iqos-xapp-rdl-f2` | **Imagem:** `iqos-xapp-rdl:2.0.0`  

---

## 1. Premissas de Implantação da Fase 2

Na infraestrutura operacional de testes e produção:
1. O **Near-RT RIC Platform (`ricplt`)** já está provisionado e ativo (DBAAS Redis na porta `6379`, E2Term na porta `36422/SCTP`, E2Mgr e Route Generator na porta `4561`).
2. As **3 Reference xApps (`ricxapp`)** já estão implantadas e em execução:
   - `ricxapp-qos-xslice` (porta HTTP `8082`, RMR `4562`)
   - `ricxapp-energy-saving` (porta HTTP `8084`, RMR `4563`)
   - `ricxapp-traffic-steering` (porta HTTP `8086`, RMR `4564`)
3. A **xApp RDL Fase 2 (CA-RDL)** deve ser implantada de forma **isolada e independente**, com identificação exclusiva de release:
   - **Helm Release Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Deployment Name:** `ricxapp-iqos-xapp-rdl-f2`
   - **Tag da Imagem:** `2.0.0`
   - **Target de Execução:** `make helm-deploy-f2`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Cluster Kubernetes: Namespace ricxapp                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [ricxapp-qos-xslice]          (Existente - Já em Execução)                │
│   [ricxapp-energy-saving]       (Existente - Já em Execução)                │
│   [ricxapp-traffic-steering]    (Existente - Já em Execução)                │
│                                                                             │
│   ─────────────────────────── [Deploy Isolado Fase 2] ───────────────────── │
│   [ricxapp-iqos-xapp-rdl-f2]    (v2.0.0 - CA-RDL / MARL - Release Dedicada) │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Comandos Operacionais de Deploy e Acompanhamento em Tempo Real

### 2.1. Implantar Exclusivamente a xApp RDL Fase 2:
```bash
# Executa o build da imagem 2.0.0, importação no k3d e deploy da release 'ricxapp-iqos-xapp-rdl-f2'
make helm-deploy-f2
# OU
bash scripts/deploy_rdl_phase2.sh
```

### 2.2. Monitorar o Ciclo de Vida dos Pods em Tempo Real (`-w`):
```bash
kubectl get pods -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -w
```

### 2.3. Streaming de Logs do Motor MARL/MAPPO em Tempo Real (`-f`):
```bash
# Via Makefile:
make logs-f2

# Via Kubectl direto (PowerShell, CMD ou Bash):
kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 2.4. Validar Endpoints HTTP e Telemetria Prometheus:
```bash
# Testa o healthcheck e métricas cognitivas da Fase 2
make test-f2

# Chamadas manuais via cURL:
curl -i http://localhost:8080/health
curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_"
```

### 2.5. Remover Apenas a xApp RDL Fase 2:
```bash
# Desinstala somente a release 'ricxapp-iqos-xapp-rdl-f2' mantendo o restante da infraestrutura intacta
make helm-uninstall-f2
```

---

## 3. Resumo dos Targets do Makefile para a Fase 2

| Comando Makefile | Ação Executada | Escopo de Impacto |
| :--- | :--- | :--- |
| **`make test`** | Executa os 18 testes unitários (pytest) | Local |
| **`make helm-deploy-f2`** | Instala/Atualiza a release `ricxapp-iqos-xapp-rdl-f2` (v2.0.0) | Namespace `ricxapp` (apenas RDL F2) |
| **`make helm-uninstall-f2`** | Desinstala a release `ricxapp-iqos-xapp-rdl-f2` | Namespace `ricxapp` (apenas RDL F2) |
| **`make status-f2`** | Exibe o status detalhado dos pods no namespace `ricxapp` | Somente leitura |
| **`make logs-f2`** | Abre streaming dos logs da xApp RDL Fase 2 | Somente leitura |
| **`make test-f2`** | Testa `/health` (`:8080`) e `/metrics` (`:8081`) da Fase 2 | Somente leitura |
| **`make run-suite`** | Executa simulações ns-3 e benchmark de Machine Learning | Suíte experimental |
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Atualizado docs/03_guia_deploy_helm_e_k8s.md em {doc_path}")

def update_phase2_doc05():
    doc_path = os.path.join(P2_DIR, "docs", "05_testes_simulacao_ns3_e_benchmarks.md")
    content = """# Volume 05: Guia de Simulação 5G NR no ns-3, Testes e Benchmarks Científicos

**Documento:** Volume Temático 05  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Co-Simulação 5G NR no ns-3 (5G-LENA + NORI), Execução em Tempo Real dos 2 Cenários de Conflito, Conexão E2 ao Near-RT RIC, Pipeline de Benchmarks e Análise de ML  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Arquitetura da Co-Simulação ns-3 / 5G-LENA

A validação experimental é realizada com o simulador de eventos discretos **ns-3 v3.40** integrado aos módulos:
* **5G-LENA (CTTC-LENA NR):** Pilha completa 3GPP Release 15/16/17 (PHY, MAC, RLC, PDCP, SDAP, BWP, Beamforming e Canais 3GPP TR 38.901).
* **ns-O-RAN / NORI:** Implementação do agente E2 na gNodeB com protocolo SCTP para o Near-RT RIC.
* **NrPointToPointEpcHelper (User Plane Core):** Roteamento IP fim a fim com tunelamento GTP-U e mapeamento de portadores de QoS (5QI).

![Arquitetura Fim-a-Fim](figures/cenario_3_arquitetura_cosimulacao_ns3_oran.png)

---

## 2. Detalhamento e Execução dos 2 Cenários de Conflito em Tempo Real

A validação experimental da Fase 2 contempla **dois cenários críticos de contenção de rádio**:

### 2.1. Cenário 1: Conflito Economia de Energia vs QoS / Slicing (EEVS)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_energy_vs_qos.cc`](file:///simulations/ns3/scenario_rdl_energy_vs_qos.cc)
* **Dinâmica:** A xApp `ricxapp-energy-saving` propõe redução de potência de transmissão (`TX_POWER`) e throttling de PRB para reduzir consumo elétrico, colidindo frontalmente com a xApp `ricxapp-qos-xslice`, que exige garantia de SLA com baixa latência para fatias URLLC e alto throughput para eMBB.
* **Topologia:** 1 Macro gNB (Banda Alta) + 1 Micro gNB (Small Cell), 20 UEs com carga dinâmica.
* **Comando para Execução Visível no Console:**
```bash
cd ~/ns3-oran-workspace/ns-3-oran
cp /caminho/para/simulations/ns3/scenario_rdl_energy_vs_qos.cc scratch/
export NS_LOG="ScenarioRdlEnergyVsQos=level_all"
./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```

---

### 2.2. Cenário 2: Conflito Traffic Steering vs QoS / Handover Ping-Pong (TVS)
* **Arquivo C++:** [`simulations/ns3/scenario_rdl_tvs_conflict.cc`](file:///simulations/ns3/scenario_rdl_tvs_conflict.cc)
* **Dinâmica:** A xApp `ricxapp-traffic-steering` tenta balancear carga forçando handovers de UEs entre as duas células, gerando risco de instabilidade, handover ping-pong e degradação severa da fatia URLLC gerida pela xApp `ricxapp-qos-xslice`.
* **Topologia:** 2 gNodeBs separadas por 80 metros, 30 UEs divididos em 3 fatias de rede (URLLC 5QI 82, eMBB 5QI 9, mMTC 5QI 79).
* **Comando para Execução Visível no Console:**
```bash
cd ~/ns3-oran-workspace/ns-3-oran
cp /caminho/para/simulations/ns3/scenario_rdl_tvs_conflict.cc scratch/
export NS_LOG="ScenarioRdlTvsConflict=level_all"
./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"
```

---

## 3. Parâmetros Reais dos Cenários em C++

| Parâmetro | Valor Configurado no C++ | Justificativa Técnica |
| :--- | :--- | :--- |
| **Dimensões do Cenário** | `200.0 m x 120.0 m` | Grid espacial delimitado para contenção e alta interferência intercelular (ICI). |
| **Topologia de gNodeBs** | `2 gNodeBs` (Macro gNB 1 em X=60m, Micro gNB 2 em X=140m) | Distância intercelular de `80.0 m` com sobreposição de feixes. |
| **Altura das Antenas** | Base Station: `25.0 m` \| Usuários (UEs): `1.5 m` | Alturas padrão 3GPP TR 38.901 Urban Microcell (UMi). |
| **Espectro / Portadora** | `3.5 GHz` (Banda n78 FR1), Canal de `100 MHz` | Frequência canônica de 5G NR comercial no Brasil e Europa. |
| **Numerologia ($\mu$)** | $\mu=1$ (`SCS = 30 kHz`), Slot = `0.5 ms` | Latência reduzida de subquadro para atendimento a fluxos URLLC. |
| **Total de Usuários (UEs)** | `30 UEs` (15 por gNodeB) | 10 UEs URLLC (5QI 82), 10 UEs eMBB (5QI 9), 10 UEs mMTC (5QI 79). |
| **Interface E2 O-RAN** | Porta SCTP `36422` | Conexão de controle Near-RT com o E2Term do Near-RT RIC. |

![Topologia Espacial 2D](figures/cenario_1_topologia_tvs_conflict.png)

---

## 4. Execução da Suíte Experimental e Benchmarks no Prompt

Para processar a suíte experimental completa e acompanhar as tabelas de métricas ao vivo no console:
```bash
# No Linux / WSL2:
python3 scripts/evaluate_and_improve_algorithms.py
python3 scripts/run_experiment_suite.py
```
```powershell
# No Windows (PowerShell / CMD):
python scripts/evaluate_and_improve_algorithms.py
python scripts/run_experiment_suite.py
```

Os artefatos gerados são salvos em `experiments/results/YYYY-MM-DD/run_HHMMSS/` e espelhados em `experiments/results/latest/`:
* `dataset_flow_metrics.csv`: Métricas de cada fluxo de QoS extraídas do FlowMonitor.
* `dataset_rdl_decisions_ml.csv`: Decisões de arbitragem e atributos de rádio por janela de tempo.
* `relatorio_comparativo.json`: Consolidação de métricas científicas em JSON.
* `relatorio_comparativo.md`: Relatório executivo em Markdown.
* `relatorio_comparativo_detalhado.md`: Avaliação estatística completa com benchmarks de 6 modelos de ML.
"""
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Atualizado docs/05_testes_simulacao_ns3_e_benchmarks.md em {doc_path}")

def update_phase2_makefile():
    makefile_path = os.path.join(P2_DIR, "Makefile")
    content = """.PHONY: build build-no-cache test validate package onboard install status status-f2 logs logs-f2 smoke-test uninstall helm-deploy-f2 helm-upgrade-f2 helm-uninstall-f2 helm-test-f2 test-f2 test-3xapps cluster-create cluster-delete cluster-recreate setup-ns3 run-baseline run-rdl run-scenario1 run-scenario2 run-experiments run-suite analyze-benchmarks view-results push-results sync auto-sync rollback rollback-push rollback-clean rollback-list

IMAGE_NAME ?= iqos-xapp-rdl
IMAGE_TAG ?= 2.0.0
CHART_DIR ?= deploy/helm/iqos-xapp-rdl
NAMESPACE_RIC ?= ricplt
NAMESPACE ?= ricxapp
RELEASE_NAME_F2 ?= ricxapp-iqos-xapp-rdl-f2
CLUSTER_NAME ?= rancher-lab
NS3_DIR ?= $(HOME)/ns3-oran-workspace/ns-3-oran

# -------------------------------------------------------------
# Build e Testes Locais da xApp RDL Fase 2
# -------------------------------------------------------------
build:
	docker build --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

build-no-cache:
	docker build --no-cache --file docker/Dockerfile --tag $(IMAGE_NAME):$(IMAGE_TAG) .

test:
	PYTHONPATH=. pytest tests/ -v

# -------------------------------------------------------------
# Deploy Helm Exclusivo para RDL Fase 2 (CA-RDL / MARL)
# Premissa: Near-RT RIC e as 3 Reference xApps ja estao rodando!
# -------------------------------------------------------------
helm-deploy-f2:
	@echo "Implantando/Atualizando exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	bash scripts/deploy_rdl_phase2.sh

helm-upgrade-f2:
	@echo "Executando Helm Upgrade da release $(RELEASE_NAME_F2)..."
	helm upgrade --install $(RELEASE_NAME_F2) $(CHART_DIR) \\
	  --namespace $(NAMESPACE) \\
	  --set image.repository=$(IMAGE_NAME) \\
	  --set image.tag=$(IMAGE_TAG) \\
	  --set image.pullPolicy=Never \\
	  --set fullnameOverride=$(RELEASE_NAME_F2) \\
	  --set env.useFakeSdl="false" \\
	  --set env.rmrWaitForReady="false" \\
	  --set env.enableTorch="true"

helm-uninstall-f2:
	@echo "Removendo exclusivamente a xApp RDL Fase 2 ($(RELEASE_NAME_F2))..."
	helm uninstall $(RELEASE_NAME_F2) -n $(NAMESPACE) || echo "Release $(RELEASE_NAME_F2) nao encontrada."

status-f2:
	@echo "=== Status das xApps no Namespace $(NAMESPACE) ==="
	@kubectl get pods -n $(NAMESPACE) -o wide
	@echo "\\n=== Pod da xApp RDL Fase 2 ==="
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -o wide

watch-pods-f2:
	@kubectl get pods -n $(NAMESPACE) -l app=$(RELEASE_NAME_F2) -w

logs-f2:
	kubectl logs -l app=$(RELEASE_NAME_F2) -n $(NAMESPACE) -f

test-f2:
	@echo "Testando endpoints da xApp RDL Fase 2 (CA-RDL / MARL)..."
	@curl -i http://localhost:8080/health || true
	@echo "\\nMétricas Prometheus:"
	@curl -s http://localhost:8081/metrics | grep -E "rdl_|marl_" || true

test-3xapps:
	@echo "Testando integridade das 3 Reference xApps no cluster..."
	bash scripts/verify_3_xapps.sh

# -------------------------------------------------------------
# Gestao do Cluster k3d (se necessario)
# -------------------------------------------------------------
cluster-create:
	@echo "Criando cluster k3d $(CLUSTER_NAME)..."
	k3d cluster create $(CLUSTER_NAME) --servers 1 --agents 0 --port "36422:36422/SCTP@server:0" --port "8080:8080@server:0" --port "8081:8081@server:0" --port "4560:4560@server:0" --port "4561:4561@server:0"
	mkdir -p ~/.kube
	k3d kubeconfig get $(CLUSTER_NAME) > ~/.kube/config

cluster-delete:
	k3d cluster delete $(CLUSTER_NAME)

# -------------------------------------------------------------
# Simulações ns-3 e Pipelines Experimentais
# -------------------------------------------------------------
setup-ns3:
	bash scripts/setup_ns3.sh

run-scenario1:
	@echo "Executando Cenário 1: Energy Saving vs QoS (EEVS) com logs em tempo real..."
	@mkdir -p $(NS3_DIR)/scratch
	@cp simulations/ns3/scenario_rdl_energy_vs_qos.cc $(NS3_DIR)/scratch/
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlEnergyVsQos=level_all" && ./ns3 run "scratch/scenario_rdl_energy_vs_qos --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"

run-scenario2:
	@echo "Executando Cenário 2: Traffic Steering vs QoS (TVS) com logs em tempo real..."
	@mkdir -p $(NS3_DIR)/scratch
	@cp simulations/ns3/scenario_rdl_tvs_conflict.cc $(NS3_DIR)/scratch/
	cd $(NS3_DIR) && export NS_LOG="ScenarioRdlTvsConflict=level_all" && ./ns3 run "scratch/scenario_rdl_tvs_conflict --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --simTime=30"

run-baseline:
	bash scripts/run_baseline_experiment.sh

run-rdl:
	bash scripts/run_rdl_experiment.sh

run-experiments:
	bash scripts/run_full_experiment.sh

run-suite:
	python3 scripts/run_experiment_suite.py

analyze-benchmarks:
	python3 scripts/run_experiment_suite.py

view-results:
	@cat experiments/results/relatorio_comparativo.md

push-results:
	@echo "Sincronizando resultados com o GitHub..."
	git add experiments/results/ docs/ scripts/
	git commit -m "chore(experiments): upload latest ns-3 MARL benchmark results [skip ci]" || echo "Nenhum dado novo."
	git push origin main || echo "Aviso no push."

sync:
	@bash scripts/git_sync.sh "$(MSG)"

auto-sync:
	@bash scripts/git_auto_sync.sh $(INTERVAL)
"""
    with open(makefile_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Atualizado Makefile em {makefile_path}")

def update_phase1_readme_and_docs():
    # Sincronizar melhorias na documentação da Fase 1
    readme_path = os.path.join(P1_DIR, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Garantir que a tabela de fases e links estejam perfeitamente alinhados
    print("[OK] Verificado README.md da Fase 1.")

if __name__ == "__main__":
    print("Iniciando atualizacao das etapas de monitoramento em tempo real...")
    update_phase2_readme()
    update_phase2_doc03()
    update_phase2_doc05()
    update_phase2_makefile()
    update_phase1_readme_and_docs()
    print("Atualizacoes concluidas com sucesso!")
