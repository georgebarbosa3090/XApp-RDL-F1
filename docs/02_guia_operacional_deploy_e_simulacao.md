# 02 — Guia operacional

Como preparar o ambiente, executar cenários e experimentos, rodar campanhas, certificar a evidência e implantar a bancada NORI. Os comandos foram usados neste projeto em Windows 11 com WSL2 (Ubuntu 24.04).

## 1. Ambiente

| Item | Valor usado |
| :-- | :-- |
| Sistema | Windows 11 + WSL2 Ubuntu 24.04 (GCC 13.3, CMake 3.28) |
| Memória do WSL | 4,5 GB (`%UserProfile%\.wslconfig`: `[wsl2]` / `memory=4608MB`) |
| Python | 3.10+ com [`uv`](https://docs.astral.sh/uv/) |
| Git | Git para Windows (o Git Bash também é usado por ferramentas de automação) |
| Espaço em disco | ≥ 5 GB livres no disco do repositório e do WSL |

Depois de alterar o `.wslconfig`, aplique com `wsl --shutdown` (encerra tudo o que roda no WSL).

```bash
git clone https://github.com/georgebarbosa3090/XApp-RDL-F1.git
cd XApp-RDL-F1
uv sync --extra test
uv run pytest -q
```

## 2. Pilha nativa: ns-3.48 + 5G-LENA v5.1

Usada pelos cenários de conflito S0–S7. Não tem E2. Instalação com versões fixadas, sem `sudo` (as dependências de compilação do Ubuntu já precisam estar presentes: `build-essential`, `cmake`, `ninja-build`, `libsqlite3-dev`, `libboost-dev`; `libeigen3-dev` habilita MIMO no 5G-LENA):

```bash
mkdir -p ~/ns3-oran-workspace && cd ~/ns3-oran-workspace
git clone --branch ns-3.48 --depth 1 https://gitlab.com/nsnam/ns-3-dev.git ns-3-oran
git clone --branch v5.1 --depth 1 https://gitlab.com/cttc-lena/nr.git ns-3-oran/contrib/nr
cd ns-3-oran
./ns3 configure -d optimized --disable-examples --disable-tests --disable-werror
./ns3 build -j3        # ~16 min com 4,5 GB; mais processos podem estourar a memória
```

O 5G-LENA v5.1 declara compatibilidade com ns-3.48 (`contrib/nr/RELEASE_NOTES.md`). Commits usados: ns-3 `d2add90`, nr `cedcead`.

> `scripts/setup_ns3.sh` (legado) usa `sudo apt`, recai na branch padrão se a versão pedida não existir, altera o launcher `ns3` para rodar como root e remove o NORI quando falta `libe2sim.a`. Não o use para gerar evidência.

O executor certificado copia os cenários e cabeçalhos para `scratch/` automaticamente. Para compilar à mão:

```bash
cp simulations/ns3/*.h simulations/ns3/scenario_rdl_direct_prb_conflict.cc ~/ns3-oran-workspace/ns-3-oran/scratch/
cd ~/ns3-oran-workspace/ns-3-oran && ./ns3 build scenario_rdl_direct_prb_conflict
```

## 3. Executar um cenário com proveniência

[`scripts/certification/run_ns3_certified.sh`](../scripts/certification/run_ns3_certified.sh) roda **um** cenário com **uma** semente, mostra a saída ao vivo e grava a evidência em `experiments/runs/<run_id>/`:

```bash
bash scripts/certification/run_ns3_certified.sh \
  --scenario scenario_rdl_direct_prb_conflict --seed 1001 --run-id meu_teste \
  [--action-schedule cronograma.csv] [--attach arquivo] [--extra-source HRDL_RUNTIME] [--no-build] \
  -- --simTime=10
```

| Arquivo gravado | Conteúdo |
| :-- | :-- |
| `execution_manifest.json` | backend (`NS3_5GLENA` ou `NORI_NS3`), versões e commits lidos dos checkouts, comando, argumentos de semente, horários, código de saída, SHA-256 do cenário e dos cabeçalhos |
| `logs/stdout.log`, `logs/stderr.log` | saída completa do simulador |
| `raw/` | FlowMonitor, `rdl_kpi_timeseries.csv`, `rdl_actuation_log.csv`, cronograma e anexos |
| `hashes.sha256` | SHA-256 de todos os arquivos (integridade, não prova de execução) |

Regras do executor: nunca sobrescreve uma execução existente; recusa rodar com menos de 1 GB livre (`MIN_FREE_MB`); com `--no-build`, só roda se a fonte em `scratch/` for idêntica à do repositório e o binário for mais novo que ela; passa a semente por `--seed` (os cenários chamam `SeedManager::SetSeed` depois de ler a linha de comando, o que anula `--RngRun`).

No WSL a partir do Windows, use caminhos `/mnt/c/...`; no Git Bash, defina `MSYS_NO_PATHCONV=1` antes de chamar `wsl`.

## 4. Experimentos de conflito

[`scripts/certification/run_conflict_experiment.py`](../scripts/certification/run_conflict_experiment.py) lê as propostas do catálogo ([`simulations/ns3/conflicts/catalog.json`](../simulations/ns3/conflicts/catalog.json)), aplica o baseline, gera o cronograma de ações e chama o executor:

```bash
python scripts/certification/run_conflict_experiment.py --scenario S1 --baseline B3 --seed 1001
python scripts/certification/run_conflict_experiment.py --scenario S7 --baseline B0 --seed 1001 --dry-run   # só mostra o cronograma
```

A execução fica em `experiments/runs/nr_<S>_<B>_seed<N>/`, com `raw/action_schedule.csv` e `raw/decision_log.json` (propostas, conflitos, resoluções e decisões) cobertos pelos hashes. No B3 o manifesto declara também a origem `HRDL_RUNTIME`.

Durante a execução aparecem, ao vivo, as linhas `[RDL-ACT]` (cada ação aplicada na RAN, com o efeito) e `[RDL-KPI]` (vazão e atraso a cada segundo simulado).

## 5. Campanhas

[`scripts/certification/run_conflict_campaign.py`](../scripts/certification/run_conflict_campaign.py) roda cenários × baselines × sementes:

```bash
python scripts/certification/run_conflict_campaign.py --seeds 1001-1005 --jobs 2
python scripts/certification/run_conflict_campaign.py --scenarios S1 S7 --baselines B0 B3 --seeds 1001 --jobs 1
python scripts/certification/run_conflict_campaign.py --seeds 1001-1005 --jobs 2 --retry-failed
```

- Compila os cenários uma vez e roda as execuções com `--no-build`, em paralelo (`--jobs 2` é o máximo recomendado com 4,5 GB).
- É retomável: execuções com `hashes.sha256` são puladas; execuções interrompidas (sem hashes) são removidas e refeitas; com `--retry-failed`, as que falharam são movidas para `experiments/runs_failed/<run_id>__<UTC>` e refeitas.
- Ordena por semente, de modo que cada semente concluída forma um conjunto pareado completo.
- Para sozinha se o disco ficar com menos de 1 GB livre.
- Ao final roda a análise e o certificador.

Tempos medidos (20–30 s simulados, `--jobs 2`): S3 ~0,8 min; S7 ~1,5 min; S0 ~2 min; S5 ~2,5 min; S4 ~4 min; S1 4–7 min; S2 ~5,5 min. Uma campanha de 160 execuções leva cerca de 5 horas.

Rode campanhas longas num terminal visível para acompanhar ao vivo; os logs completos de cada execução ficam na própria evidência.

## 6. Análise e certificação

```bash
python scripts/certification/analyze_conflict_runs.py      # reports/conflicts/conflict_analysis_<UTC>.{md,json}
python scripts/certification/certify_chain.py              # reports/certification/certificate_<UTC>.{md,json}
python scripts/certification/certify_chain.py --run nr_S1_B3_seed1001
```

O certificador avalia cada execução contra [`reproducibility/provenance_policy.yaml`](../reproducibility/provenance_policy.yaml) e [`reproducibility/versions.lock`](../reproducibility/versions.lock) e emite os vereditos G0–G6. A análise considera só execuções elegíveis no certificador. Critérios em [`05_auditoria_e_conformidade_oran.md`](05_auditoria_e_conformidade_oran.md).

Validadores mais antigos, complementares: `scripts/validate_provenance.py`, `scripts/verify_provenance_and_integrity.py`, `scripts/validate_experiment_tree.py --check-gate1`, `scripts/check_no_synthetic_results.py`.

## 7. Pilha NORI via Helm (E2 real)

O NORI oficial exige ns-3.42, 5G-LENA `78b7179`, e2sim `da6f82f` e E2AP/E2SM v3.01. O chart [`deploy/helm/nori-ns3`](../deploy/helm/nori-ns3/README.md) compila tudo dentro de um pod, sem Docker, reproduzindo o Dockerfile oficial do NORI com versões fixadas:

```bash
sudo k3s server --write-kubeconfig-mode 644 >/tmp/k3s.log 2>&1 &     # requer sudo
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace
kubectl -n ricsim logs -f deploy/nori-ns3                               # preparo e compilação (horas na 1ª vez)
kubectl -n ricsim exec -it deploy/nori-ns3 -- bash /scripts/run.sh nori-rc-slicing-demo nori_rc_demo_seed1 --seed 1 -- --simTime=10
```

Para E2 real é preciso um Near-RT RIC O-RAN SC Release I acessível em `ric.e2termAddress`. Situação: chart validado com `helm lint`, **ainda não implantado** (o k3s não estava ativo).

## 8. Implantação da xApp no Kubernetes

| Chart | Conteúdo |
| :-- | :-- |
| `deploy/helm/iqos-xapp-rdl` | xApp RDL (portas 4560 RMR, 8080 HTTP, 8081 métricas) |
| `deploy/helm/xapp-qos-xslice`, `xapp-energy-saving`, `xapp-traffic-steering` | xApps de referência |
| `deploy/helm/nori-ns3` | bancada NORI |

```bash
helm upgrade --install rdl deploy/helm/iqos-xapp-rdl -n ricxapp --create-namespace
```

A imagem `iqos-xapp-rdl:1.1.0` precisa estar disponível para o cluster; o `docker/Dockerfile` existe, mas o projeto evita Docker, e a forma de construir a imagem sem ele (por exemplo, um builder no próprio cluster) ainda não foi definida. Os manifestos em `deploy/kubernetes/` e `deploy/openran-br-v3/` são alternativas sem Helm.

## 9. Solução de problemas

| Sintoma | Causa e solução |
| :-- | :-- |
| `No space left on device` | Disco cheio. Os traces completos do 5G-LENA geram GB por execução; em S2/S3 eles só são ativados com `--nrTraces=true`. Libere espaço e rode a campanha de novo. |
| ns-3 aborta com `Not allowed state for starting SRS reception` | Limitação do 5G-LENA v5.1 em handover em massa. Use `--disableSrs=true` (já definido no catálogo para S2, S4 e S5). |
| Nenhuma saída `NS_LOG` | O perfil otimizado remove `NS_LOG`; os cenários imprimem `[RDL-ACT]`/`[RDL-KPI]` via `std::cout`. |
| Variáveis vazias em `wsl -- bash -c '...'` | O `wsl` expande `$X` antes do bash; grave um script e rode-o por caminho `/mnt/c/...`. |
| Caminhos `C:/Program Files/Git/mnt/...` | Conversão de caminho do Git Bash; defina `MSYS_NO_PATHCONV=1`. |
| Hashes de execuções antigas não conferem | Conversão CRLF do Git no Windows; `experiments/runs/** -text` em `.gitattributes` preserva os bytes. Para restaurar, apague os arquivos e rode `git checkout -- experiments/runs`. |
| `scratch/ desatualizado` ao usar `--no-build` | A fonte mudou depois da compilação; rode a campanha (que recompila) ou compile o cenário. |
| Porta 8080 ocupada nos testes | Cada `RDLxApp` sobe um servidor HTTP; o erro de bind é apenas registrado. |
