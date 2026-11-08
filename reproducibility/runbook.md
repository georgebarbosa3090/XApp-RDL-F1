# Runbook de Execução e Reprodutibilidade Experimental — Fase 1 (H-RDL)

<div align="center">

**Protocolo de Reprodutibilidade Determinística, Simulações ns-3 5G-LENA e Auditoria de Conformidade O-RAN**  
*Autor: George Alexandro F. Barbosa — PPGC / Universidade Federal do Pará (UFPA)*

</div>

---

## 1. Pré-Requisitos do Sistema

* **Sistema Operacional:** Linux Ubuntu 22.04 LTS (WSL2 no Windows 11 ou Bare-Metal);
* **Contêineres e Cluster:** Docker Engine 24.0+ e k3d v5.6.0+;
* **Ambiente Python:** Python 3.10+ / 3.12 com dependências instaladas (`pip install -r requirements.txt`);
* **Toolchain de Compilação:** CMake 3.25+, Ninja e g++ 11+;
* **Simulador de Rádio 5G:** pilha nativa `ns-3.48` + `5G-LENA v5.1` (cenários de conflito, sem E2) e pilha NORI `ns-3.42` + 5G-LENA `78b7179` + NORI `8a30867` via Helm (E2 v3.01). Memória do WSL: 4,5 GB.

---

## 2. Roteiro Passo a Passo de Execução

### Passo 1: Inicialização do Cluster k3d (Escolha sua topologia)

* Opção 1: Single-Node (~450 MB RAM):
```bash
k3d cluster create rdl-cluster --servers 1 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"
```

* Opção 2: Dual-Node (~900 MB RAM):
```bash
k3d cluster create rdl-cluster --servers 1 --agents 1 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"
```

* Opção 3: Multi-Node (~1.5 GB RAM):
```bash
k3d cluster create rdl-cluster --servers 1 --agents 2 -p "36422:36422/sctp@server:0" -p "8080-8087:8080-8087@server:0" -p "4560-4561:4560-4561@server:0"
```

### Passo 2: Implantação da Infraestrutura Near-RT RIC e xApps

* Deploy via manifestos Kubernetes puros (Perfil OpenRAN@Brasil Blueprint v3):
```bash
kubectl apply -f deploy/openran-br-v3/config-map.yaml
kubectl apply -f deploy/openran-br-v3/service.yaml
kubectl apply -f deploy/openran-br-v3/deployment.yaml
```

* Verificar prontidão dos pods:
```bash
kubectl get pods -n ricxapp -l app=iqos-xapp-rdl
```

### Passo 2b: Bancada NORI (E2) via Helm

O NORI oficial exige ns-3.42 e E2 v3.01 (ver `versions.lock`, perfil `profile.nori`). Ele é compilado dentro do cluster, sem Docker:
```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace
kubectl -n ricsim logs -f deploy/nori-ns3
kubectl -n ricsim exec -it deploy/nori-ns3 -- bash /scripts/run.sh nori-rc-slicing-demo nori_rc_demo_seed1 --seed 1 -- --simTime=10
```
Detalhes em [`deploy/helm/nori-ns3/README.md`](../deploy/helm/nori-ns3/README.md).

### Passo 2c: Cenários de conflito na pilha nativa e certificação
```bash
bash scripts/certification/run_ns3_certified.sh --scenario scenario_rdl_direct_prb_conflict --seed 1001 --baseline B3 -- --simTime=10
python scripts/certification/certify_chain.py
```
O certificador emite o veredito dos gates G0–G6 em `reports/certification/`.

Experimentos de conflito com atuação na RAN (baselines B0–B3; propostas em `simulations/ns3/conflicts/catalog.json`):
```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
python scripts/certification/analyze_conflict_runs.py
```

### Passo 3: Execução da Suíte de 3 Simulações Consecutivas

* Executa em sequência rigorosa os cenários TVS, EEVS e Closed-Loop NORI (N = 30 Runs):
```bash
python scripts/run_3_consecutive_simulations.py
```

### Passo 4: Execução dos Testes Automatizados e Interoperabilidade
```bash
pytest tests/ -v
```

### Passo 5: Geração do Catálogo Visual e Figuras em Alta Resolução (300 DPI)
```bash
python scripts/generate_sbrc_figures.py
```
