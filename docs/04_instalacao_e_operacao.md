# 04 — Instalação e operação

Como preparar o ambiente, executar cenários e experimentos, rodar campanhas, certificar a evidência e implantar a bancada NORI. O que cada componente faz e como eles se registram está em [01](01_componentes_e_fluxos.md); os resultados, em [06](06_metodologia_e_resultados.md). Os comandos foram usados neste projeto em Windows 11 com WSL2 (Ubuntu 24.04).

## 1. Ambiente

| Item | Valor usado |
| :-- | :-- |
| Sistema | Windows 11 + WSL2 Ubuntu 24.04 (GCC 13.3, CMake 3.28) |
| Memória do WSL | 5 GB (`%UserProfile%\.wslconfig`: `[wsl2]` / `memory=5GB`; era 4,5 GB até 2026-11-08, quando a pilha RIC + NORI passou a rodar) |
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
./ns3 build -j3        # ~16 min (medido com 4,5 GB); mais processos podem estourar a memória
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

- Compila os cenários uma vez e roda as execuções com `--no-build`, em paralelo (`--jobs 2` é o máximo recomendado; medido com 4,5 GB).
- É retomável: execuções com `hashes.sha256` são puladas; execuções interrompidas (sem hashes) são removidas e refeitas; com `--retry-failed`, as que falharam são movidas para `experiments/runs_failed/<run_id>__<UTC>` e refeitas.
- Ordena por semente, de modo que cada semente concluída forma um conjunto pareado completo.
- Para sozinha se o disco ficar com menos de 1 GB livre.
- Ao final roda a análise e o certificador.

Tempos medidos (20–30 s simulados, `--jobs 2`): S3 ~0,8 min; S7 ~1,5 min; S0 ~2 min; S5 ~2,5 min; S4 ~4 min; S1 4–7 min; S2 ~5,5 min. Em 2026-11-08, 96 execuções (S0–S7 × B0–B3 × 3 sementes) levaram 2 h 20 min; as 160 da campanha completa, cerca de 4 horas.

Rode campanhas longas num terminal visível para acompanhar ao vivo; os logs completos de cada execução ficam na própria evidência.

### 5.1 Direto no terminal WSL/Ubuntu

Os scripts rodam nativamente no Ubuntu, sem passar pelo Windows (fora do Windows o driver chama `bash` direto, em vez de `wsl`). No B3 o driver usa a `RDLxApp` real, que precisa das dependências do projeto. O Ubuntu 24.04 não traz `python3-venv` e o pip do sistema é gerenciado externamente; sem `sudo`, crie o venv sem pip e instale com o pip do sistema (uma vez):

```bash
python3 -m venv --without-pip ~/.venvs/xapp-rdl
python3 -m pip --python ~/.venvs/xapp-rdl/bin/python install "pydantic>=2.0.0" "structlog>=23.1.0" "prometheus-client>=0.19.0" "pycrate>=0.7.0" "requests>=2.31.0" "numpy>=1.24.0" "fastapi>=0.100.0" "uvicorn>=0.20.0" "PyYAML>=6.0.1"
```

Em cada terminal novo:

```bash
cd <raiz-do-repositório>          # o caminho do clone visto pelo WSL, ex.: /mnt/c/.../XApp-RDL-F1
source ~/.venvs/xapp-rdl/bin/activate
python scripts/certification/run_conflict_campaign.py --scenarios S0 S1 S2 S3 S4 S5 S6 S7 --baselines B0 B1 B2 B3 --seeds 1001-1005 --jobs 2
```

Verificado em 2026-11-08: os cronogramas gerados no Ubuntu são idênticos aos das 160 execuções (32 combinações cenário × baseline), e uma execução real pelo Ubuntu (S0/B0/1003) reproduziu byte a byte `rdl_kpi_timeseries.csv`, `rdl_actuation_log.csv` e `action_schedule.csv` da execução da campanha. No B3, as mensagens de porta 8080/8081 em uso vêm dos servidores de saúde e métricas da `RDLxApp` e não afetam a decisão.

## 6. Análise e certificação

```bash
python scripts/certification/analyze_conflict_runs.py      # reports/conflicts/conflict_analysis_<UTC>.{md,json}
python scripts/certification/certify_chain.py              # reports/certification/certificate_<UTC>.{md,json}
python scripts/certification/certify_chain.py --run nr_S1_B3_seed1001
python scripts/certification/generate_campaign_report.py   # reports/conflicts/relatorio_campanha_<UTC>.md
```

O relatório da campanha ([`generate_campaign_report.py`](../scripts/certification/generate_campaign_report.py)) é gerado só a partir da análise, dos manifestos, do catálogo e do certificado: hipóteses e critérios, comandos de execução, ambiente, resultados agregados, uma tabela por semente com todas as métricas, diferenças pareadas B3 − Bx, cronogramas idênticos entre baselines, avaliação das hipóteses, conclusões, ameaças à validade, falhas preservadas e o comando ns-3 de cada execução.

O certificador avalia cada execução contra [`reproducibility/provenance_policy.yaml`](../reproducibility/provenance_policy.yaml) e [`reproducibility/versions.lock`](../reproducibility/versions.lock) e emite os vereditos G0–G6. A análise considera só execuções elegíveis no certificador. Critérios em [`07_certificacao_e_achados.md`](07_certificacao_e_achados.md).

Evidências e relatórios não guardam caminhos locais. O executor ns-3, o dissecador e o relatório da campanha gravam a raiz do clone como `<repo>` e o HOME como `~`. Para conferir o repositório inteiro:

```bash
python scripts/certification/redact_local_paths.py --check    # código 1 se algum arquivo versionado tiver caminho local
python scripts/certification/redact_local_paths.py --apply    # redige, recalcula hashes.sha256 e propaga os sha256; log em reports/redaction/
```

Validadores mais antigos, complementares: `scripts/validate_provenance.py`, `scripts/verify_provenance_and_integrity.py`, `scripts/validate_experiment_tree.py --check-gate1`, `scripts/check_no_synthetic_results.py`.

## 7. Bancada E2 real: Near-RT RIC, NORI e xApp

### 7.1 k3s nativo

O k3s v1.26.5 do WSL roda como serviço systemd permanente, instalado uma vez com [`install_k3s_service.sh`](../scripts/install_k3s_service.sh) (requer `systemd=true` em `/etc/wsl.conf`; kubeconfig legível sem sudo):

```bash
sudo bash scripts/install_k3s_service.sh
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
```

**Mantenha uma sessão do Ubuntu aberta enquanto o cluster estiver em uso.** O WSL encerra a distribuição quando nenhuma sessão fica conectada, mesmo com serviços systemd ativos, e a religa no próximo `wsl`: o k3s reinicia a cada vez e o nó não chega a `Ready` (observado em 2026-11-08: `ActiveEnterTimestamp` do k3s sempre igual à hora do comando). Um terminal Ubuntu aberto basta, ou uma sessão dedicada:

```bash
wsl -d Ubuntu -- sleep infinity      # no PowerShell; feche para liberar o WSL
```

Clusters k3d e o Rancher (Docker) que existam no WSL disputam a memória com o RIC e o NORI; pare-os antes (`sudo k3d cluster stop --all`, `sudo docker stop <rancher>`; reversível). Não use `sudo k3s server ... &`: em segundo plano o `sudo` não consegue pedir a senha.

### 7.2 Near-RT RIC O-RAN SC Release I

[`deploy_ric_i_release.sh`](../scripts/deploy_ric_i_release.sh) implanta, sem sudo e em primeiro plano, só os componentes da cadeia E2 (DBaaS, AppMgr, RtMgr, E2Mgr, E2Term, SubMgr) e o A1 Mediator a partir do `ric-dep` (branch `i-release`, commit `0a6f18e`), com a receita [`recipe_ric_i_release_e2.yaml`](../deploy/ric/recipe_ric_i_release_e2.yaml) (mesmas imagens e tags da receita oficial da Release I):

```bash
bash scripts/deploy_ric_i_release.sh            # implanta ou atualiza
bash scripts/deploy_ric_i_release.sh --status   # pods, serviços e releases
```

- Os charts da Release I usam APIs removidas no Kubernetes 1.22 (RBAC e Ingress `v1beta1`). O plugin pós-renderizador do Helm 4 [`deploy/ric/helm-postrenderer`](../deploy/ric/helm-postrenderer/plugin.yaml) troca o RBAC para `v1` e remove os Ingress (usados só com o Kong, que não é implantado); os charts oficiais não são alterados.
- O chart `ric-common` é servido por HTTP local (127.0.0.1:8879) em vez do `chartmuseum` do instalador oficial, que exige sudo.
- O A1 Mediator não participa da cadeia E2, mas o RtMgr o tem fixo em `PlatformComponents`. Sem ele, cada distribuição de rotas espera o timeout do *wormhole* para o A1, e a criação da rota de uma subscrição (`/ric/v1/handles/xapp-subscription-handle`) estoura o prazo do SubMgr: a subscrição volta com `ErrorSource: RTMGR`, "context deadline exceeded" (observado em 2026-11-08 antes de incluí-lo).
- Fora da receita: Kong, Prometheus, O1, VES, alarmes, InfluxDB e Jaeger.
- O E2Term SCTP fica em `service-ricplt-e2term-sctp-alpha.ricplt:36422` (NodePort 32222), o endereço padrão do chart do NORI. O kernel do WSL2 (6.6) tem o módulo `sctp`.
- Verificado em 2026-11-08: 7 pods prontos, rotas distribuídas pelo RtMgr a todos os endpoints (inclusive xApps registradas), ~3,4 GB livres no WSL com RIC, NORI e xApp ativos.
- API REST de subscrição do SubMgr: porta **8088** (`service-ricplt-submgr-http.ricplt:8088/ric/v1/subscriptions`); a 8080 só responde ao *health check*.

### 7.3 Bancada NORI

O NORI oficial exige ns-3.42, 5G-LENA `78b7179`, e2sim `da6f82f` e E2AP/E2SM v3.01. O chart [`deploy/helm/nori-ns3`](../deploy/helm/nori-ns3/README.md) compila tudo dentro de um pod, sem Docker, reproduzindo o Dockerfile oficial do NORI com versões fixadas:

```bash
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace
kubectl -n ricsim logs -f deploy/nori-ns3                               # preparo e compilação (horas na 1ª vez)
```

O chart aplica os patches do projeto sobre o NORI listados no `versions.lock` (hoje um: [`0001-rc-control-ack.patch`](../deploy/helm/nori-ns3/files/patches/0001-rc-control-ack.patch), que faz a função E2SM-RC responder ao RIC Control com ACK; ver [06 §5.3](06_metodologia_e_resultados.md#53-fase-3-ric-control-e2sm-rc-com-ack-2026-11-08)) e recompila incrementalmente; `BUILD_INFO.json` e cada manifesto registram `nori_patches`.

O exemplo `nori-rc-slicing-demo` instala um FlowMonitor mas nunca o grava. O chart gera, em `scratch/`, a variante `nori-rc-slicing-flowmon`, idêntica ao exemplo exceto por gravar `flowmonitor.xml` ao fim de `Simulator::Run()` (os fontes do NORI ficam intactos; o manifesto registra o sha256 do fonte compilado em `scenario_source`). Execução ao vivo, com o período de relatório E2 alinhado ao da subscrição:

```bash
kubectl -n ricsim exec -it deploy/nori-ns3 -- bash /scripts/run.sh nori-rc-slicing-flowmon nori_kpm_flowmon_seed1_p1s \
  --seed 1 -- --simTime=40 --ns3::E2Interface::E2Periodicity=1
```

O NORI ignora o *Event Trigger* da subscrição e reporta a cada `E2Interface::E2Periodicity` (padrão 0,01 s de tempo simulado: duas Indications, nó e UE, a cada 10 ms). Sem o ajuste, 60 s geram ~12 mil Indications e um PCAP de ~16 MB.

Trazer a evidência para o repositório, recortar os eventos da xApp e dissecar o E2 (Ubuntu do WSL):

```bash
bash scripts/collect_nori_run.sh nori_kpm_flowmon_seed1_p1s
python scripts/certification/certify_chain.py
```

### 7.4 xApp `kpm-probe` (assinatura E2SM-KPM)

O chart [`deploy/helm/xapp-kpm-probe`](../deploy/helm/xapp-kpm-probe/README.md) implanta, sem Docker, uma xApp mínima no namespace `ricxapp`: registra-se no AppMgr, assina E2SM-KPM v3.00 pelo SubMgr em cada nó E2 que fica `CONNECTED` no E2Mgr e registra cada RIC Indication recebida por RMR (tipo, subscription id, tamanho e sha256 do payload) em JSON Lines. O *Event Trigger* (Format 1, 1000 ms) e a *Action Definition* (estilo 1, Format 1) são codificados em APER com `asn1tools` a partir do ASN.1 do próprio NORI, baixado no commit fixado e conferido por sha256. A xApp não decide nada: materializa os elos Subscription e KPM da cadeia.

```bash
bash scripts/deploy_kpm_probe.sh            # pacote do src/ do commit atual (recusa src/ não commitado)
kubectl -n ricxapp logs -f deploy/kpm-probe | grep --line-buffered -v "RMR \[INFO\] sends"
```

O script gera o pacote do `src/` com `git archive` do commit atual e o passa ao chart em base64; a xApp registra o commit no evento `start` e em cada decisão.

Desde a fase 3, a xApp também envia, depois da N-ésima Indication de cada conexão (`rc.afterIndications`), um RIC Control E2SM-RC v3.01 por RMR (tipo 12040, MEID do nó) com cotas de PRB por fatia, e registra o ACK/Failure. Com `rc.decision: hrdl` (fase 4, padrão) as cotas são decididas pelo RDL-N1 sobre o KPM_t0 (`decision_source: H_RDL`); com `rc.decision: fixed`, vêm de `rc.sliceQuotas` (`FIXED_PROBE`).

### 7.5 Dissecação E2 do PCAP

[`e2_pcap_dissect.py`](../scripts/certification/e2_pcap_dissect.py) separa o tráfego SCTP de uma execução NORI em mensagens E2AP, classifica cada uma pelo papel (Setup, Subscription, Indication, Control, ACK...) e identifica a cadeia KPM_t0 → Control → ACK → KPM_t1. Dois decodificadores de origens distintas:

1. o próprio script (só biblioteca padrão; não usa o codec da xApp): PCAP, remontagem SCTP e cabeçalho APER do E2AP-PDU com os IEs de identificação;
2. o `tshark` (Wireshark 4.2.2, gerado do ASN.1 oficial), comparado mensagem a mensagem em tipo de PDU, código de procedimento, RICrequestID e RANfunctionID.

O certificador só aceita a dissecação (R14 `PASS`) quando os dois concordam e o hash do PCAP de origem confere; sem tshark, R14 fica `WARN` e os gates E2 não são certificados. A saída vai para `experiments/e2_dissection/<run_id>/` (o diretório da execução não é alterado): `e2_messages.json` (resumo, papéis da cadeia, resultado do tshark e cruzamento com a xApp), `messages.tsv` (uma linha por mensagem), `messages/*.aper` (bytes das mensagens notáveis), `tshark_fields.tsv` e `hashes.sha256`. Com `experiments/xapp_logs/<run_id>/kpm_probe_events.jsonl`, cada Indication do PCAP é casada por sha256 com as recebidas pela xApp.

O tshark pode ser instalado com `sudo apt-get install -y tshark` ou, sem sudo, extraído do pacote oficial do Ubuntu na mesma versão das bibliotecas do Wireshark já instaladas (é o caminho padrão de `collect_nori_run.sh`):

```bash
mkdir -p ~/.local/tshark-4.2.2 && cd ~/.local/tshark-4.2.2
apt-get download tshark=4.2.2-1.1build3
dpkg-deb -x tshark_4.2.2-1.1build3_amd64.deb root
root/usr/bin/tshark --version | head -1
```

### 7.6 Cenários de conflito S0–S8 na bancada NORI e observabilidade ao vivo

Os cenários do catálogo também rodam na bancada NORI, com a cadeia E2 real e a decisão do RDL-N1 sobre o KPM (só a cota de PRB no gNB 0 é atuável). Um cenário: `bash scripts/run_nori_scenario.sh S1 1001`; a campanha S0–S8 × 5 sementes, com certificação e resumo: `bash scripts/run_nori_campaign.sh`. Os comandos de cada aba ao vivo (execução NORI, E2AP pelo tshark, xApp, RIC, Kubernetes, registro de UEs), o painel tmux e a campanha nativa com análise, certificação e relatório estão em [docs/05](05_observabilidade_e_campanhas.md).

## 8. Implantação da xApp no Kubernetes

| Chart | Conteúdo |
| :-- | :-- |
| `deploy/helm/iqos-xapp-rdl` | xApp RDL (portas 4560 RMR, 8080 HTTP, 8081 métricas) |
| `deploy/helm/xapp-qos-xslice`, `xapp-energy-saving`, `xapp-traffic-steering` | xApps de referência |
| `deploy/helm/nori-ns3` | bancada NORI |
| `deploy/helm/xapp-kpm-probe` | xApp de assinatura E2SM-KPM (fase 2) |

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
| E2 Setup do NORI sem resposta depois de reiniciar o WSL (só o Setup Request no PCAP) | Os pods do RIC subiram fora de ordem: o RtMgr não recebeu o registro do E2Term e não há rota para a mensagem 1101. Reinicie em ordem e confira os logs: `kubectl -n ricplt rollout restart deploy/deployment-ricplt-rtmgr`, espere ficar pronto, depois o E2Mgr e o E2Term (achado 51 de [07](07_certificacao_e_achados.md)). |
