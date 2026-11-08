# Runbook de reprodução — Fase 1

## 1. Pré-requisitos

| Item | Versão |
| :-- | :-- |
| Sistema | Ubuntu 22.04/24.04 (nativo ou WSL2 com 4,5 GB de memória) |
| Python | 3.10+ (`pip install -r requirements.txt`) |
| Compilação | CMake 3.25+, Ninja, g++ 11+ |
| Pilha nativa | ns-3.48 + 5G-LENA v5.1 em `~/ns3-oran-workspace/ns-3-oran` (commits em `versions.lock`, perfil `profile.native`) |
| Pilha NORI (opcional) | k3s + Helm 3; ns-3.42 + 5G-LENA `78b7179` + NORI `8a30867` compilados no pod (perfil `profile.nori`) |
| Disco | ≥ 1 GB livre por execução (os executores abortam abaixo disso) |

Não é usado Docker: a bancada NORI é implantada com Helm sobre k3s.

## 2. Testes

```bash
pytest tests/ -q
```

Os testes usam dependências simuladas e não produzem evidência experimental.

## 3. Cenários de conflito (pilha nativa)

Uma execução, com proveniência, para um cenário, baseline e semente:

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
```

Campanha completa (S0–S7 × B0–B3 × sementes), retomável — execuções já concluídas com sucesso são puladas:

```bash
python scripts/certification/run_conflict_campaign.py --scenarios S0 S1 S2 S3 S4 S5 S6 S7 --baselines B0 B1 B2 B3 --seeds 1001 1002 1003 1004 1005
```

Repetir só as que falharam:

```bash
python scripts/certification/run_conflict_campaign.py --retry-failed
```

Cada execução fica em `experiments/runs/nr_<cenário>_<baseline>_seed<semente>/` com `execution_manifest.json`, `logs/`, `raw/` (FlowMonitor, `rdl_kpi.csv`, `rdl_actions.csv`, `decision_log.json`) e `hashes.sha256`. Falhas vão para `experiments/runs_failed/`.

Análise:

```bash
python scripts/certification/analyze_conflict_runs.py
```

Gera `reports/conflicts/` com as tabelas por cenário e baseline, lidas dos arquivos brutos.

## 4. Certificação

```bash
python scripts/certification/certify_chain.py
```

Emite os vereditos por execução e dos gates G0–G6 em `reports/certification/`.

## 5. Bancada NORI (E2) via Helm

Requer um cluster k3s ativo (iniciado pelo usuário, com privilégios de administrador):

```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace
kubectl -n ricsim logs -f deploy/nori-ns3
kubectl -n ricsim exec -it deploy/nori-ns3 -- bash /scripts/run.sh nori-rc-slicing-demo nori_rc_demo_seed1 --seed 1 -- --simTime=10
```

Detalhes em [`deploy/helm/nori-ns3/README.md`](../deploy/helm/nori-ns3/README.md). Essa bancada ainda não foi implantada; G1–G4 dependem dela.

## 6. Implantação da xApp num Near-RT RIC

Helm (`deploy/helm/iqos-xapp-rdl`) ou manifestos (`deploy/openran-br-v3/`, `deploy/kubernetes/`). Ver [`deploy/openran-br-v3/README.md`](../deploy/openran-br-v3/README.md).

## 7. Scripts aposentados

`scripts/run_3_consecutive_simulations.py` e os demais simuladores em Python foram desativados: geravam valores estatísticos sem simulação de rede. Os resultados válidos vêm só do ns-3.
