# Runbook de Execução e Reprodutibilidade Experimental — Fase 1 (H-RDL)

**Projeto:** xApp RDL (Resource and Decision Layer)  
**Autor:** George Alexandro F. Barbosa / PPGC-UFPA  
**Data:** 10 de Setembro de 2026  

---

## 1. Pré-Requisitos do Sistema

* Linux Ubuntu 22.04 LTS (Nativo ou WSL2 no Windows 11);
* Docker CE 24.0+ e k3d v5.6.0+;
* Python 3.10+ / 3.12 com ambiente virtual `.venv`;
* Toolchain de compilação CMake 3.22+, Ninja e g++ 11+;
* Árvore de fontes do `ns-3.48` com módulo `5G-LENA v5.1` e `NORI`.

---

## 2. Roteiro Passo a Passo de Execução

### Passo 1: Inicialização do Cluster de Simulação e Near-RT RIC
```bash
# Cria o cluster k3d com mapeamento de portas SCTP e RMR
make cluster-create

# Implanta a plataforma Near-RT RIC e as 3 Reference xApps
make helm-deploy
```

### Passo 2: Inicialização da xApp RDL em Modo O-RAN Interoperável
```bash
# Execução local / contêiner
export RDL_MODE="O_RAN_INTEROP"
export USE_FAKE_SDL="false"
export DISPATCH_RAW_APER_CONTROL="true"
python src/rdl_xapp.py
```

### Passo 3: Execução do Cenário Closed-Loop ns-3/NORI
```bash
cd $HOME/ns3-oran-workspace/ns-3-oran
./ns3 run "scenario_rdl_closed_loop_nori --ricIp=172.18.0.4 --ricPort=36422 --simTime=30"
```

### Passo 4: Execução da Avaliação Estatística Multi-Semente ($N = 30$ Runs)
```bash
python scripts/run_multi_seed_evaluation.py
```

### Passo 5: Geração de Figuras Científicas em Alta Resolução (300 DPI)
```bash
python scripts/generate_sbrc_figures.py
```
