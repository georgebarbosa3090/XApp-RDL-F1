# 🐧 Guia Completo de Execução em WSL2 — k3d, Rancher, Near-RT RIC & ns-3 5G-LENA

Este guia detalha o fluxo completo para executar a infraestrutura O-RAN real amanhã dentro do **WSL2 (Ubuntu)**, alternando entre a avaliação **Baseline (sem RDL)** e **Governança (com H-RDL e CA-RDL)** em malha fechada com o **ns-3.48 / 5G-LENA v5.1 / NORI**.

---

## 📋 Pré-requisitos no WSL2
1. **Docker Daemon ativo**:
   ```bash
   sudo service docker status || sudo service docker start
   ```
2. **Ferramentas de CLI instaladas**: `k3d`, `kubectl`, `helm`, `cmake`, `g++`, `python3`.

---

## 🚀 Etapa 1: Provisionar Cluster k3d + Near-RT RIC

### A. Modo Baseline (3 Reference xApps SEM RDL)
Para medir o desempenho da rede **sem a camada de governança RDL** (para baseline comparativo):
```bash
cd ~/XApp-RDL-F1  # ou path do repositório no WSL
bash scripts/deploy_helm.sh --baseline
```
- **Componentes Ativados**:
  - Cluster `k3d` (`rancher-lab`) com portas SCTP (36422) e RMR (4560-4561).
  - DBAAS Redis + Platform Near-RT RIC no namespace `ricplt`.
  - 3 Reference xApps no namespace `ricxapp`: `xSlice QoS`, `Energy Saving`, `Traffic Steering`.

---

### B. Modo Governança Cognitiva (Com xApp H-RDL / CA-RDL)
Para ativar a camada determinística e Safe-RL de arbitragem de conflitos:
```bash
# Na Fase 1 (H-RDL):
cd ~/XApp-RDL-F1
bash scripts/deploy_helm.sh --with-rdl

# Na Fase 2 (CA-RDL / MARL MAPPO):
cd ~/XApp-RDL-F2
bash scripts/deploy_helm.sh --with-rdl
```
- **Componentes Ativados**:
  - Todos os componentes do baseline + Pod `ricxapp-iqos-xapp-rdl` no namespace `ricxapp`.

---

## 📡 Etapa 2: Registro no Rancher (Opcional)
Se você estiver utilizando a interface web do **Rancher** para monitoramento visual:
```bash
bash scripts/register_rancher.sh
```

---

## 🌐 Etapa 3: Preparar o Simulador ns-3 + 5G-LENA + Módulo NORI

Execute o script de compilação automatizado para baixar o `ns-3.48`, o módulo `5G-LENA (nr v5.1)` e a extensão `NORI E2SIM`:
```bash
bash scripts/setup_ns3.sh
```
> **Nota**: O script automaticamente converte permisssões, copia os cenários C++ para `scratch/` e compila o ns-3 com `CMake`.

---

## 🔬 Etapa 4: Executar os Cenários de Co-Simulação E2AP / E2SM

Acesse o diretório do ns-3 compilado (padrão: `~/workspace/ns-3-dev` ou `~/ns-3-dev`) e execute os cenários:

### 1. Cenário Closed-Loop NORI (E2AP + E2SM-KPM + E2SM-RC):
```bash
cd ~/workspace/ns-3-dev
./ns3 run scenario_rdl_closed_loop_nori
```

### 2. Cenário de Conflito Triádico TVS & EEVS:
```bash
./ns3 run scenario_rdl_tvs_conflict
```

### 3. Cenário 5G-A Massive MIMO & 6G ISAC Sensing (Repositório F2):
```bash
./ns3 run scenario_rdl_5ga_multicarrier_mimo
./ns3 run scenario_rdl_6g_isac_sensing_coexistence
```

---

## 📊 Etapa 5: Coleta de Resultados & Manifesto SHA-256

Após concluir a rodada de simulação, execute o validador de proveniência para atualizar o firewall editorial:

```bash
# No repositório F1:
cd ~/XApp-RDL-F1
python3 scripts/prepare_simulation_run.py

# No repositório F2:
cd ~/XApp-RDL-F2
python3 scripts/prepare_simulation_run.py
python3 scripts/validate_ml_provenance.py
```

---

## 🔍 Comandos de Diagnóstico Úteis

- **Verificar Pods em execução**:
  ```bash
  kubectl get pods -A -o wide
  ```
- **Verificar Logs do RDL em Tempo Real**:
  ```bash
  kubectl logs -n ricxapp -l app.kubernetes.io/name=iqos-xapp-rdl -f
  ```
- **Verificar Mensagens RMR e E2AP**:
  ```bash
  kubectl logs -n ricplt deployment/deployment-ricplt-e2term -f
  ```
