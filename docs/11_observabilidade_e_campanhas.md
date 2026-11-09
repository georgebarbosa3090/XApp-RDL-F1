# 11 — Observabilidade ao vivo e campanhas

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
- tshark 4.2.2 local (ver docs/02);
- `tmux`, só para o painel.

## 1. Por que o porte para o NORI

| Pilha | Cenários | E2 | Gates que o certificador pode avaliar |
| :-- | :-- | :-- | :-- |
| Nativa (ns-3.48 + 5G-LENA v5.1) | S0–S7 (`simulations/ns3/scenario_s*.cc`) | não | G0 |
| NORI (ns-3.42 + 5G-LENA + E2 real) | S0–S8 (variante `nori-rc-slicing-flowmon`) | sim | G0–G4 |

A pilha nativa aplica um cronograma de ações dentro do ns-3, sem E2. Por isso a cadeia KPM_t0 → H-RDL → E2SM-RC → ACK → KPM_t1 só pode ser certificada na bancada NORI, o único lugar onde o nó E2 fala com o RIC.

Na bancada NORI, cada cenário do catálogo (`simulations/ns3/conflicts/catalog.json`) roda assim:

1. O cenário é escrito em `/data/rdl_scenario`, no volume da xApp kpm-probe.
2. A xApp, em modo `catalog`, assina o KPM do nó.
3. Na 12.ª Indication, o H-RDL real (`src/closed_loop/catalog_loop.py`) arbitra as propostas das xApps do cenário. O estado de entrada é o KPM decodificado: PRBs do nó, UEs e fatias.
4. Se houver o que atuar, a xApp envia o RIC Control E2SM-RC (função 300). O ACK e o efeito na vazão por fatia são medidos.

O que o NORI consegue atuar:

| Proposta do catálogo | Atuação no NORI |
| :-- | :-- |
| `PRB_QUOTA` no gNB 0 | RIC Control de cota de PRB por fatia: eMBB (SST 1) recebe o teto `v`, URLLC (SST 2) recebe `100 − v` |
| `TX_POWER`, `HANDOVER` | Decidida e registrada como **não atuável**: potência de transmissão não existe no E2SM-RC do NORI, e o handover ele só registra em log (há um único gNB) |
| Qualquer proposta nos gNBs 1–3 | Não atuável: o NORI tem um único gNB |

As propostas não atuáveis aparecem na decisão (`not_actuated`, com o motivo). Nenhum Control é enviado por elas.

Cada execução faz uma única decisão. Ela usa a primeira ocorrência de cada proposta (xApp, gNB, parâmetro) e mantém o gNB de origem no alvo (`<meid>#g<gnb>`). Assim, propostas para gNBs diferentes não viram conflito falso.

| Cenário | Decisão do H-RDL (verificada em `tests/unit/test_catalog_loop.py`) | Control no NORI |
| :-- | :-- | :-- |
| S0 | xslice `PRB_QUOTA` 80; `TX_POWER` no gNB 1 não atuável | 80/20 |
| S1 | conflito direto → TVS escolhe xslice 75 | 75/25 |
| S2 | conflito indireto → EEVS escolhe xslice 80; `HANDOVER` não selecionado | 80/20 |
| S3 | TVS escolhe `TX_POWER` (não atuável) | nenhum |
| S4 | sem conflito (pass-through): `HANDOVER` no gNB 0 (só registrado em log pelo NORI) e `TX_POWER` no gNB 1 (inexistente no NORI) | nenhum |
| S5 | sem conflito (pass-through): `HANDOVER` nos gNBs 0 e 1, nenhum atuável | nenhum |
| S6 | xslice 85 | 85/15 |
| S7 | Safety Guard bloqueia `rogue_xapp` (`TX_POWER` 60 e `PRB_QUOTA` 150); xslice 70 | 70/30 |
| S8 | conflito direto xslice 25 × embb_throughput 80 → H-RDL escolhe embb_throughput 80 | 80/20 |

### S8: o closed loop do NORI

O S8 antigo (`scenario_rdl_closed_loop_nori.cc`) não alterava a RAN e só imprimia um handshake E2 fixo (achados 14 e 15 da auditoria). Ele foi removido.

No catálogo, o S8 passou a ser o cenário de closed loop da bancada NORI:

- `"ns3": null`;
- `"backend": "NORI_NS3"`;
- `"nori_scenario": "nori-rc-slicing-flowmon"`.

Com isso, o S8 só roda pelo `scripts/run_nori_scenario.sh`. A campanha nativa recusa o S8 com a mensagem "cenário(s) só da bancada NORI".

### Critério "disparado pelo KPM_t0"

O NORI envia o KPM de cada período em par: formato 1 (nó) e formato 3 (UEs), com menos de 1 ms entre os dois. O E2Term pode entregar esse par à xApp em ordem trocada.

A decisão usa as duas mensagens do par. Os sha256 de ambas ficam registrados em `decision.kpm_node_sha256` e `decision.kpm_ues_sha256`. Por isso, o dissector considera o Control disparado pelo KPM_t0 (o último KPM antes do Control, no PCAP) quando esse KPM é uma das entradas da decisão.

Na execução `nori_S1_B3_seed1001`, o gatilho registrado era a mensagem de formato 1 do par. No fio, porém, a última mensagem antes do Control era a de formato 3, que também entrou na decisão.

A xApp também só decide quando a Indication recebida completa o par do período (nó e UEs chegados a no máximo 0,5 s um do outro), em qualquer ordem de entrega, para que uma decisão rápida não use os UEs do período anterior (achado 48). Além disso, a xApp aquece o H-RDL antes do primeiro KPM (evento `decision_warm_up`). Isso evita que a importação das bibliotecas atrase o Control na hora da decisão.

## 2. Painel pronto (tmux)

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

## 3. Comandos de cada aba (para subir manualmente)

Abra um terminal Ubuntu por aba, entre na raiz do repositório e exporte o `KUBECONFIG` em cada um.

### 3.1 Execução NORI: o cenário rodando ao vivo

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

### 3.2 Protocolo E2AP: tcpdump do pod direto para o tshark local

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

### 3.3 xApp: subscrição, KPM por UE, decisão do H-RDL, Control e ACK

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

### 3.4 RIC: E2Term, E2Mgr, SubMgr, RtMgr e o estado dos nós

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

### 3.5 Kubernetes: pods e deployments ao vivo

```bash
bash scripts/observe/k8s_live.sh
```

O comando manual equivalente:

```bash
watch -n 2 'kubectl get deploy,statefulset,pods -n ricplt; kubectl get deploy,pods -n ricxapp; kubectl get deploy,pods -n ricsim; free -m'
```

### 3.6 Registro de UEs

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

## 4. Campanha NORI: S0–S8 × 5 sementes, com a cadeia certificada

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

Na bancada NORI, o baseline padrão é o B3 (H-RDL real). Para a campanha do G5, a xApp também decide como B0 (sem coordenação: toda proposta atuável vai à RAN na ordem de chegada, vale a última), B1 (FIFO por alvo) e B2 (prioridade estática por alvo), com a mesma semântica da pilha nativa (`src/closed_loop/catalog_loop.decide_baseline`). O baseline é escolhido com `--baselines` ou `BASELINE=B0..B3`, gravado em `/data/rdl_baseline` e no `run_id` (`nori_<S>_<B>_seed<N>`). A fonte da decisão registrada é `BASELINE_B0`, `BASELINE_B1`, `BASELINE_B2` ou `H_RDL` ([pré-registro do G5](07_preregistro_g5_campanha_s8.md)).

Para acompanhar a campanha ao vivo, abra o painel (seção 2) ou as abas da seção 3. Rode a campanha em primeiro plano em uma delas.

## 5. Campanha nativa: S0–S7 × B0–B3 × 5 sementes, seguida de análise, certificação e relatório

```bash
bash scripts/run_native_campaign.sh                               # 160 execuções
bash scripts/run_native_campaign.sh --seeds 1001-1002 --jobs 1
```

O script ativa o venv (`$VENV`, padrão `~/.venvs/xapp-rdl`, ver docs/02) e roda, em sequência:

1. `scripts/certification/run_conflict_campaign.py`: as execuções, mostrando ao vivo as linhas `[RDL-ACT]` (cada ação aplicada na RAN) e `[RDL-KPI]` (vazão e atraso por segundo simulado), com o run_id;
2. `scripts/certification/analyze_conflict_runs.py`: a análise de conflitos;
3. `scripts/certification/certify_chain.py`: a certificação (só G0 é avaliável sem E2);
4. `scripts/certification/generate_campaign_report.py`: o relatório.

A campanha é retomável.

## 6. Certificação

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

## 7. Limites

- O NORI tem um único gNB e só atua cota de PRB por fatia. Nos cenários que dependem de potência, handover ou de vários gNBs (S3, S4, S5), ou nas propostas desse tipo dos demais cenários, a decisão do H-RDL é registrada, mas não há efeito na RAN para medir.
- A decisão é única por execução: não há rearbitragem periódica, como no cronograma da pilha nativa.
- A previsão de efeito usa a curva v5 (teto → vazão, `experiments/calibration/slice_cap_curve_v5.json`), calibrada com 2 UEs e tráfego de 300 Mb/s. Fora dessa configuração, o veredito de efeito não vale.

## 8. Resultado da campanha NORI (S0–S8 × 1001–1005, 2026-11-09)

A campanha rodou as 45 execuções, todas concluídas. O resumo por execução está em [`reports/nori/resumo_campanha_nori_20261109T015402Z.md`](../reports/nori/resumo_campanha_nori_20261109T015402Z.md) e o certificado em `reports/certification/certificate_20261109T015457Z.md`.

| Cenário | Execuções | Cadeia completa | Efeito `CONSISTENT` | Observação |
| :-: | --: | --: | --: | :-- |
| S0, S1, S2, S6, S8 | 5 cada | 5 | 4 | semente 1005: ver achado 42 |
| S3, S4, S5 | 5 cada | 0 | 0 | sem nada atuável, portanto sem Control (`NOT_TESTABLE`) |
| S7 | 5 | 5 | 0 | regra de previsão no teto de 30 %: ver achado 41 |

Em todas as 45 execuções o tshark concordou com o dissecador. Em todas as 30 com Control:

- a decisão foi do H-RDL e teve o KPM_t0 entre as entradas;
- o ACK foi correlacionado;
- a eMBB não perdeu vazão.

Certificador: G0, G1 (60 execuções), G3 (43) e G4 (23 cadeias: 3 da v5 e 20 desta campanha) `CERTIFIED`. G5 continua `NOT_CERTIFIED`, porque o mínimo é 30 sementes pareadas e a campanha tem 5.

Vazão da URLLC antes e depois do Control (a mesma em todas as sementes de cada linha):

| Teto URLLC | Sementes 1001–1004 (antes → depois, Mb/s) | Previsão v5 | Semente 1005 (antes → depois, Mb/s) | Depois/antes |
| --: | :-- | --: | :-- | --: |
| 15 % (S6) | 151,49 → 56,25 | 56,95 | 75,74 → 28,10 | 0,371 |
| 20 % (S0, S2, S8) | 151,49 → 76,44 | 75,50 | 75,74 → 38,14 | 0,505 |
| 25 % (S1) | 151,49 → 95,24 | 95,22 | 75,74 → 47,52 | 0,628 |
| 30 % (S7) | 151,49 → 113,98 | 91,45 | 75,74 → 56,87 | 0,752 |

Três achados, registrados como exploratórios em docs/05:

- **Achado 41.** No S7, a regra v5 erra a previsão para o teto de 30 %. Ela deixa de fora o próprio nível e interpola entre 20 % e 70 %, mas 70 % já não restringe a vazão, que satura por volta de 40 % dos PRBs. A previsão sai 91,45 Mb/s; o medido, 113,98 Mb/s, é igual ao ponto de 30 % da curva.
- **Achado 42.** Com a semente 1005, cada UE chega no máximo a 75,74 Mb/s, metade das outras sementes, desde o início da execução. A curva v5 está em Mb/s absolutos e foi calibrada a 151,49 Mb/s. Por isso só funciona quando a vazão de base coincide com a da calibração: quatro execuções saíram `NOT_TESTABLE` e o S6 saiu `INCONSISTENT`. A razão depois/antes, porém, é a mesma nas duas vazões de base, para cada teto. Isso indica que o efeito da cota é relativo à vazão sem restrição.
- **Achado 43.** Em 6 das 45 execuções, a xApp não recebeu o primeiro par de Indications (78/80): o nó o enviou cerca de 2 ms depois do Subscription Response, antes de a rota RMR da subscrição chegar. A decisão, na 12.ª Indication, não é afetada.

Os vereditos acima são os da regra pré-registrada v5, sem ajuste depois de ver os dados. Uma regra relativa (razão depois/antes por teto) e uma interpolação só entre níveis que restringem exigem um novo desenho pré-registrado antes de serem aplicadas. Esse desenho é o [pré-registro v6](07_preregistro_fase4_v6.md), com avaliação em sementes novas (2001–2005): `bash scripts/run_nori_campaign.sh --scenarios "S0 S1 S2 S6 S7 S8" --seeds "2001 2002 2003 2004 2005"`. A coleta grava o veredito v6 em `slice_effect_v6.json`, e o resumo da campanha mostra as duas colunas.

## 9. Avaliação do desenho v6 (S0, S1, S2, S6, S7, S8 × 2001–2005, 2026-11-09)

As 30 avaliações pré-registradas em [docs/07 v6](07_preregistro_fase4_v6.md) saíram `CONSISTENT` pela regra v6 (previsão relativa à vazão antes do Control), com erro de no máximo 0,03 %. Pela regra v5, 25 saíram `CONSISTENT` e os cinco S7 saíram `INCONSISTENT`.

| Hipótese | Resultado |
| :-- | :-- |
| H6.1 (cadeia E2 completa, decisão do H-RDL sobre o KPM_t0, ACK, tshark) | cumprida nas 30 |
| H6.2 (≥ 27 de 30 `CONSISTENT` pela v6) | cumprida: 30 de 30 |
| H6.3 (os cinco S7, teto de 30 %, `CONSISTENT`) | cumprida |
| H6.4 (invariância à vazão de base) | não testada: as cinco sementes deram 151,49 Mb/s |

Resumo em [`reports/nori/resumo_campanha_nori_20261109T043933Z.md`](../reports/nori/resumo_campanha_nori_20261109T043933Z.md). Certificado `certificate_20261109T043932Z`: G0, G1 (90), G3 (73) e G4 (48 cadeias, regra v5) `CERTIFIED`; G5 `NOT_CERTIFIED`. Com a v6 adotada no certificador, sem efeito retroativo, o G4 passou a 53 cadeias (`certificate_20261109T045007Z`).

## 10. Avaliação do desenho v7 (banda de 50 MHz, sementes 4001–4005, 2026-11-09)

O [pré-registro v7](07_preregistro_fase4_v7.md) testou a H6.4 reduzindo a banda para 50 MHz (URLLC com vazão de base de 40 Mb/s). As 30 avaliações saíram `INCONSISTENT` pela regra v6, todas com cadeia E2 completa: **H6.4 refutada para mudança de banda.** Pela análise exploratória, o teto age em PRBs absolutos da portadora. Por exemplo, URLLC a 20 % de 50 MHz → 37,46 Mb/s, igual a 10 % de 100 MHz. A regra v6 continua válida na banda da calibração (100 MHz), onde foi confirmada.

## 11. Campanha do G5 (S8 × B0–B3 × 30 sementes, 2026-11-09)

O [pré-registro da campanha do G5](07_preregistro_g5_campanha_s8.md) rodou o S8 com os quatro baselines e E2 real nas sementes 5001–5033. Três pares foram perdidos e repostos, declarados antes das execuções de reposição: um pela corrida no disparo da decisão do B0 (5012), dois pela perda de registro do E2Term no RIC (5028 e 5029). **G5 `CERTIFIED`, com 30 pares.** Todas as execuções válidas saíram `CONSISTENT` pela regra v6, com as cotas previstas: B0 com dois Controls e 25/75 final, B1 80/20, B2 25/75, B3 80/20. Na vazão total, o H-RDL e o FIFO dão 227,93 Mb/s, e o B0 e o B2 dão 246,73 Mb/s, sem hipótese de superioridade pré-registrada. Resumo em [`reports/nori/resumo_campanha_nori_20261109T130646Z.md`](../reports/nori/resumo_campanha_nori_20261109T130646Z.md); certificado `certificate_20261109T130613Z`: G0, G1 (249), G3 (230), G4 (84) e G5 `CERTIFIED`, G6 `NOT_CERTIFIED`.
