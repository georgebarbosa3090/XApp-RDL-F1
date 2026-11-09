# 05 — Observabilidade e campanhas

Este documento mostra como acompanhar uma execução ao vivo no terminal do Ubuntu (WSL), aba por aba. Ele cobre:

- o cenário NORI;
- o protocolo E2AP;
- a xApp;
- o RIC;
- o Kubernetes;
- o registro de UEs.

Também explica como rodar as duas campanhas, a da bancada NORI (S0–S8 com E2 real e a cadeia certificável) e a nativa (S0–S7 sem E2), e como certificar o resultado.

Todos os comandos rodam no Ubuntu do WSL, a partir da raiz do repositório:

```bash
cd <raiz-do-repositório>          # ex.: o caminho /mnt/c/... do clone no WSL
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

Pré-requisitos:

- RIC O-RAN SC Release I nos namespaces `ricplt`/`ricxapp`;
- bancada NORI em `ricsim` (chart `deploy/helm/nori-ns3`);
- tshark 4.2.2 local (ver docs/04);
- `tmux`, só para o painel.

## 1. Painel pronto (tmux)

```bash
bash scripts/observe/panel.sh          # sessão tmux "rdl"; Ctrl-b <número> troca de aba; Ctrl-b d sai sem parar
```

| Janela | Conteúdo |
| :-- | :-- |
| 0 campanha | terminal livre, com os comandos de campanha sugeridos |
| 1 nori | execução NORI corrente |
| 2 e2ap | E2AP decodificado ao vivo |
| 3 xapp | eventos da xApp |
| 4 ric | logs do RIC (em cima) e estado dos nós e subscrições (embaixo) |
| 5 k8s | pods e deployments |
| 6 ues | registro de UEs |

Para encerrar o painel: `tmux kill-session -t rdl`.

## 2. Comandos de cada aba (para subir manualmente)

Abra um terminal Ubuntu por aba, entre na raiz do repositório e exporte o `KUBECONFIG` em cada um.

### 2.1 Execução NORI: o cenário rodando ao vivo

Para rodar um cenário com a saída ao vivo nesta mesma aba:

```bash
bash scripts/run_nori_scenario.sh S1 1001
```

Para só acompanhar (por exemplo, enquanto a campanha roda em outra aba):

```bash
bash scripts/observe/nori_live.sh
```

A aba mostra:

- a vazão por fatia a cada 2 s simulados (`[t = …] Per-Slice Performance Monitoring`, `Slice 0 (eMBB…)`, `Slice 1 (URLLC…)`);
- as linhas `[RDL-UE]`;
- o E2 Setup e a Subscription (`E2SimMod`, `SETUP`, `ubscription`);
- o recebimento do Control (`RICcontrol`);
- os marcos `=== [...]` do `run.sh`.

O `nori_live.sh` segue a execução mais recente até ela gravar `hashes.sha256` e então espera a próxima. Ele não reexibe uma execução já encerrada, a menos que você use `FOLLOW_LAST=1`. Para trocar o filtro, passe uma regex: `bash scripts/observe/nori_live.sh 'Slice|RICcontrol'`.

O comando manual equivalente, para uma execução em andamento:

```bash
kubectl -n ricsim exec deploy/nori-ns3 -- sh -c 'tail -F /workspace/runs/$(ls -t /workspace/runs | head -1)/logs/stdout.log'
```

### 2.2 Protocolo E2AP: tcpdump do pod direto para o tshark local

```bash
bash scripts/observe/e2ap_live.sh
```

O script passa o `tcpdump -i any -U -s 0 -w - sctp` do pod do NORI direto para o tshark local. O tshark decodifica E2AP na porta SCTP 36422 (`-o sctp.reassembly:TRUE -d sctp.port==36422,e2ap`) e imprime uma linha por mensagem:

- horário;
- sentido;
- procedimento (E2 Setup, RIC Subscription, Indication, RIC Control, ACK);
- RICrequestID (requestor/instance);
- RAN function (4 e 200 = KPM, 300 = RC).

Para usar outro executável: `TSHARK=/caminho/tshark bash scripts/observe/e2ap_live.sh`.

O comando manual equivalente:

```bash
kubectl -n ricsim exec -i deploy/nori-ns3 -- tcpdump -i any -U -s 0 -w - sctp 2>/dev/null \
  | ~/.local/tshark-4.2.2/root/usr/bin/tshark -l -n -r - -o sctp.reassembly:TRUE -d sctp.port==36422,e2ap -Y e2ap \
      -T fields -e frame.time -e sctp.dstport -e e2ap.procedureCode -e e2ap.ricRequestorID -e e2ap.ricInstanceID -e e2ap.ranFunctionID
```

A dissecação completa, com hashes, concordância com o tshark e papéis da cadeia, continua sendo feita depois, sobre o PCAP da execução (`scripts/certification/e2_pcap_dissect.py`). A aba ao vivo serve para acompanhar; não é evidência.

### 2.3 xApp: subscrição, KPM por UE, decisão do H-RDL, Control e ACK

```bash
bash scripts/observe/xapp_live.sh                 # também cada Indication RMR: --indications
```

O script formata os eventos JSON da kpm-probe (`scripts/observe/format_xapp_events.py`) em linhas legíveis e coloridas:

- início da xApp (modo, commit do `src/`), registro no AppMgr, RMR pronto;
- RIC Subscription (HTTP do SubMgr e `SubscriptionId`) e Subscription Response do nó;
- `KPM nó`: PRBs usados e disponíveis, UEs ativos, RRC conectados;
- `KPM UEs`: UE, SST da fatia, PRBs, vazão e TBs;
- a decisão do H-RDL: cenário, tipo de conflito → estratégia, propostas selecionadas, não atuáveis e não selecionadas;
- `RIC Control -> nó` (RICrequestID, função 300, teto por SST) e `RIC Control ACK do nó`, com a latência.

O comando manual equivalente:

```bash
kubectl -n ricxapp logs -f deploy/kpm-probe --since=1s | python3 -u scripts/observe/format_xapp_events.py
```

O arquivo completo de eventos fica no volume da xApp: `kubectl -n ricxapp exec deploy/kpm-probe -- tail -f /data/logs/kpm_probe_events.jsonl`.

### 2.4 RIC: E2Term, E2Mgr, SubMgr, RtMgr e o estado dos nós

```bash
bash scripts/observe/ric_live.sh                  # ou só alguns: bash scripts/observe/ric_live.sh e2term submgr
bash scripts/observe/ric_nodes.sh                 # estado: nós E2 no E2Mgr, subscrições no SubMgr, xApps no AppMgr
```

O `ric_live.sh` segue os logs dos quatro componentes, prefixa cada linha com o componente e filtra a mensageria RMR, as rotas e as subscrições. Ele descarta o polling REST da xApp ao E2Mgr, que de outra forma inundaria a aba a cada segundo.

O comando manual de um componente:

```bash
kubectl -n ricplt logs -f deploy/deployment-ricplt-e2term-alpha --since=5s | grep -E 'RIC_INDICATION|RIC_CONTROL|RIC_SUB|SETUP'
kubectl -n ricplt logs -f deploy/deployment-ricplt-submgr --since=5s | grep -E 'SubReq|SubResp|SubDel|REST'
kubectl -n ricplt logs -f deploy/deployment-ricplt-rtmgr --since=5s | grep -E 'Update Routes|Push policy|Endpoint'
```

O `ric_nodes.sh` consulta, a cada 3 s e de dentro do pod da xApp:

- o E2Mgr: nós, estado da conexão e RAN functions;
- o SubMgr: subscrições ativas, na porta 8088;
- o AppMgr: xApps registradas.

### 2.5 Kubernetes: pods e deployments ao vivo

```bash
bash scripts/observe/k8s_live.sh
```

O comando manual equivalente:

```bash
watch -n 2 'kubectl get deploy,statefulset,pods -n ricplt; kubectl get deploy,pods -n ricxapp; kubectl get deploy,pods -n ricsim; free -m'
```

### 2.6 Registro de UEs

```bash
bash scripts/observe/ue_live.sh
```

No build otimizado do ns-3, os `NS_LOG` desaparecem, e o NORI não imprime a conexão dos UEs. Por isso, a variante `nori-rc-slicing-flowmon`, gerada pelo entrypoint do chart `deploy/helm/nori-ns3`, liga callbacks aos traces RRC do 5G-LENA. Cada callback imprime uma linha `[RDL-UE]`:

| Trace | Linha |
| :-- | :-- |
| `NrGnbRrc/NewUeContext` | novo contexto no gNB (célula, RNTI) |
| `NrUeRrc/InitialCellSelectionEndOk` | seleção de célula pelo UE (IMSI, célula) |
| `NrGnbRrc/ConnectionEstablished` | conexão RRC confirmada no gNB (IMSI, célula, RNTI) |
| `NrUeRrc/ConnectionEstablished` | conexão RRC no UE |
| resumo a t = 0,3 s | UE i → IMSI, IP e fatia |

No início da execução, cada trace aparece como "conectado" ou "indisponível". Para mudar a variante, basta recompilá-la (cerca de 20 s, no próprio `run.sh`); o resto do ns-3 não muda.

### 2.7 InfluxDB e Grafana: séries das simulações

InfluxDB 2.7.4 e Grafana 12.3.1 rodam via Helm no namespace `monitoring`, com versões fixadas, limites de memória baixos e cerca de 200 MB no total. Implantação, uma vez:

```bash
bash scripts/observe/deploy_observability.sh     # charts influxdata/influxdb2 2.1.2 e grafana/grafana 10.5.15 (cache local, com novas tentativas)
```

Os valores estão em `deploy/helm/observability/`: `values-influxdb2.yaml`, `values-grafana.yaml` e o dashboard `dashboards/rdl_simulacoes.json`, gerado por `scripts/observe/make_grafana_dashboard.py`. A senha e o token do administrador do InfluxDB são gerados pelo chart no Secret `influxdb2-auth`. O Grafana lê o token de lá e tem acesso anônimo somente de leitura.

Em duas abas:

```bash
bash scripts/observe/influx_live.sh     # alimentador: abre o port-forward do InfluxDB, lê o token e envia os pontos
bash scripts/observe/grafana.sh         # Grafana em http://localhost:3000 (abre no navegador do Windows)
```

O alimentador (`scripts/observe/influx_feeder.py`) só lê, sem alterar nada no repositório ou no cluster. Ele envia ao bucket `simulacoes` (org `rdl`):

| Measurement | Fonte | Conteúdo |
| :-- | :-- | :-- |
| `nori_slice` | `raw/slice_series.csv` da execução NORI corrente (a cada 2 s) | vazão (Mb/s) e atraso (ms) por UE/fatia, com o tempo simulado; tags `run`, `scenario`, `baseline`, `condition`, `seed`, `slice` |
| `xapp_kpm_node`, `xapp_kpm_ue` | eventos `kpm` da kpm-probe | PRBs do nó, UEs ativos e PRBs por UE/fatia |
| `xapp_indication` | `rmr_message` (RIC Indication) | contagem de Indications |
| `xapp_control`, `xapp_control_outcome`, `xapp_decision` | `control_request`, `control_outcome`, `control_decision` | cotas por fatia, fonte da decisão, ordem do Control (B0), intervalo do par KPM, latência e correlação do ACK |
| `campanha_execucao` | `slice_effect*.json` e manifestos no repositório (histórico completo na primeira passada) | veredito por regra (v5, v6), vazões antes e depois, previsão, cotas, disparo pelo KPM_t0 |
| `certificado` | certificado mais recente | veredito de cada gate |

O dashboard "xApp RDL — simulações" tem três blocos:

- **Execução NORI ao vivo:** vazão e atraso por fatia, e a execução escolhida com o tempo simulado no eixo X, onde a queda da fatia restrita aparece no instante de aplicação do Control.
- **xApp:** KPM do nó, Indications por 10 s, latência do ACK e tabela dos RIC Control. O Control também aparece como anotação nos gráficos.
- **Campanhas e certificação:** gates do certificado, vereditos por baseline e regra, URLLC antes, depois e prevista, e as execuções mais recentes.

Remover: `helm -n monitoring uninstall grafana influxdb2`.

### 2.8 Rancher (opcional)

```bash
bash scripts/observe/deploy_rancher.sh                # cert-manager v1.14.7 + Rancher 2.8.5, uma réplica
kubectl -n cattle-system port-forward svc/rancher 8443:443     # https://localhost:8443 (certificado autoassinado)
kubectl -n cattle-system get secret bootstrap-secret -o jsonpath='{.data.bootstrapPassword}' | base64 -d   # senha inicial
bash scripts/observe/deploy_rancher.sh --uninstall    # remove
```

O chart do Rancher 2.8.x é o último que aceita o Kubernetes da bancada (k3s v1.26). O roteiro limita o Rancher a 1,25 GiB e informa a memória livre no fim.

**Não cabe neste ambiente.** Na tentativa de 2026-11-09, o cert-manager subiu, mas a máquina virtual do WSL reiniciou durante o download e a descompactação da imagem do Rancher (cerca de 1,4 GB). A causa foi o disco C: do Windows, que guarda o `ext4.vhdx` do Ubuntu e estava praticamente cheio: o `.vhdx` cresceu até esgotar o C:, e o WSL passou a dar erro de E/S. Os 7,7 GB de RAM do host agravam o problema. A queda derrubou o RIC, o NORI e a xApp, e a recuperação foi manual (achado 50 de docs/07). O Rancher e o cert-manager foram removidos. Por isso o roteiro agora exige 4,5 GB livres por padrão. Para usar o Rancher, rode-o fora deste WSL, em outra máquina ou num WSL com 8 GB ou mais, e importe o cluster k3s por lá. Para acompanhar a bancada, ficam as abas da seção 2 e o Grafana da seção 2.7.

## 3. Campanha NORI: S0–S8 × 5 sementes, com a cadeia certificada

```bash
bash scripts/run_nori_campaign.sh                                          # 45 execuções, ~3 min cada (~2,5 h)
bash scripts/run_nori_campaign.sh --scenarios "S1 S7" --seeds "1001 1002"  # subconjunto
bash scripts/run_nori_campaign.sh --no-deploy                              # reaproveita a xApp já implantada
bash scripts/run_nori_campaign.sh --tag _bw50 --args "--bandwidth=50e6"   # outra condição do cenário (run_id nori_<S>_B3_bw50_seed<N>)
bash scripts/run_nori_campaign.sh --scenarios S8 --baselines "B0 B1 B2 B3" --seeds "$(seq -s ' ' 5001 5030)"   # campanha do G5
```

O script:

1. implanta a kpm-probe em modo `catalog`, com o `src/` e o catálogo do commit atual (`scripts/deploy_kpm_probe.sh` recusa alterações não commitadas);
2. roda cada cenário × semente com `scripts/run_nori_scenario.sh`. Execuções que já existem são puladas, então a campanha é retomável;
3. no fim, roda o certificador (`scripts/certification/certify_chain.py`) e o resumo (`scripts/certification/nori_campaign_summary.py`), que grava `reports/nori/resumo_campanha_nori_<UTC>.md`.

O resumo tem uma linha por execução, com:

- os papéis da cadeia no PCAP;
- a concordância com o tshark;
- as Indications casadas com a xApp;
- as estratégias do H-RDL;
- o que foi atuado e o que não foi atuável;
- o veredito do efeito na RAN.

Ele traz também uma tabela por cenário.

Cada execução fica em três lugares:

- `experiments/runs/nori_<S>_B3_seed<semente>/`: manifesto, PCAP, FlowMonitor, `slice_series.csv` e hashes;
- `experiments/xapp_logs/<run>/`: eventos da xApp recortados;
- `experiments/e2_dissection/<run>/`: dissecação E2 e `slice_effect.json`.

Na bancada NORI, o baseline padrão é o B3 (H-RDL real). Para a campanha do G5, a xApp também decide como B0 (sem coordenação: toda proposta atuável vai à RAN na ordem de chegada, vale a última), B1 (FIFO por alvo) e B2 (prioridade estática por alvo), com a mesma semântica da pilha nativa (`src/closed_loop/catalog_loop.decide_baseline`). O baseline é escolhido com `--baselines` ou `BASELINE=B0..B3`, gravado em `/data/rdl_baseline` e no `run_id` (`nori_<S>_<B>_seed<N>`). A fonte da decisão registrada é `BASELINE_B0`, `BASELINE_B1`, `BASELINE_B2` ou `H_RDL` ([pré-registro do G5](preregistros/07_campanha_g5_s8.md)).

Para acompanhar a campanha ao vivo, abra o painel (seção 1) ou as abas da seção 2. Rode a campanha em primeiro plano em uma delas.

## 4. Campanha nativa: S0–S7 × B0–B3 × 5 sementes, seguida de análise, certificação e relatório

```bash
bash scripts/run_native_campaign.sh                               # 160 execuções
bash scripts/run_native_campaign.sh --seeds 1001-1002 --jobs 1
```

O script ativa o venv (`$VENV`, padrão `~/.venvs/xapp-rdl`, ver docs/04) e roda, em sequência:

1. `scripts/certification/run_conflict_campaign.py`: as execuções, mostrando ao vivo as linhas `[RDL-ACT]` (cada ação aplicada na RAN) e `[RDL-KPI]` (vazão e atraso por segundo simulado), com o run_id;
2. `scripts/certification/analyze_conflict_runs.py`: a análise de conflitos;
3. `scripts/certification/certify_chain.py`: a certificação (só G0 é avaliável sem E2);
4. `scripts/certification/generate_campaign_report.py`: o relatório.

A campanha é retomável.

## 5. Certificação

```bash
python3 scripts/certification/certify_chain.py          # certificado em reports/certification/certificate_<UTC>.{json,md}
```

| Gate | Fonte |
| :-- | :-- |
| G0 | execuções nativas e NORI com manifesto e hashes íntegros |
| G1 | KPM_t0 e Subscription no PCAP de uma execução NORI |
| G3 | RIC Control e ACK no PCAP, enviados e recebidos pela xApp |
| G4 | cadeia completa, decisão `H_RDL` cujas entradas incluem o KPM_t0, e efeito na RAN `CONSISTENT`: regra v6 (previsão relativa) nas execuções iniciadas depois do pré-registro v6; regra v5 nas anteriores, sem efeito retroativo |
| G5 | ≥ 30 (cenário, semente) pareados nos quatro baselines B0–B3, cada um com cadeia E2 completa, Control decidido pelo próprio baseline e disparado pelo KPM_t0 (só bancada NORI) |

## 6. Limites

- O NORI tem um único gNB e só atua cota de PRB por fatia. Nos cenários que dependem de potência, handover ou de vários gNBs (S3, S4, S5), ou nas propostas desse tipo dos demais cenários, a decisão do H-RDL é registrada, mas não há efeito na RAN para medir.
- A decisão é única por execução: não há rearbitragem periódica, como no cronograma da pilha nativa.
- A previsão de efeito usa a curva v5 (teto → vazão, `experiments/calibration/slice_cap_curve_v5.json`), calibrada com 2 UEs e tráfego de 300 Mb/s. Fora dessa configuração, o veredito de efeito não vale.

