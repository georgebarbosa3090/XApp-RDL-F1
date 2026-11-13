# Chart `xapp-kpm-probe` — assinatura E2SM-KPM v3.00 e RIC Control E2SM-RC v3.01 no Near-RT RIC Release I

xApp mínima, implantada via Helm sem Docker, que materializa os elos **Subscription**, **KPM**, **RIC Control** e **ACK** da cadeia closed-loop (gates G1 e G3). Quem decide as cotas é o RDL-N1 (modos `hrdl` e `catalog`); no modo `fixed`, a cota é configurada no chart.

1. Registra-se no AppMgr (`/ric/v1/register`); o RtMgr passa a distribuir rotas RMR para ela.
2. Acompanha os nós E2 no E2Mgr (`/v1/nodeb/states`). A cada nó que fica `CONNECTED`, envia ao SubMgr (`POST /ric/v1/subscriptions`, porta 8088) uma subscrição REPORT na RAN function KPM (200 no NORI). Quando o nó cai, apaga a subscrição.
3. Recebe por RMR as RIC Indications (tipo 12050) e registra tipo, subscription id, MEID, tamanho e sha256 do payload.
4. Depois da N-ésima Indication de cada conexão (`rc.afterIndications`), envia por RMR um RIC Control (12040, MEID do nó) com cotas de PRB por fatia (E2SM-RC v3.01, estilo 2, ação 6; `rc.sliceQuotas`) e registra o ACK ou Failure (12041/12042), conferindo a correlação por RICrequestID e RANfunctionID. O evento `control_request` guarda os bytes enviados, `decision_source: FIXED_PROBE` e o sha256 da Indication que disparou o envio: o certificador não aceita este Control como decisão do RDL-N1 (G4).

O código vem do repositório: [`scripts/deploy_kpm_probe.sh`](../../../scripts/deploy_kpm_probe.sh) passa ao chart, em base64, o `git archive` do `src/` do commit atual (codec E2 v3, ponte RDL-N1 e o próprio RDL-N1) e recusa um `src/` com alterações não commitadas. Com `rc.decision: hrdl` (padrão), as cotas são decididas pelo RDL-N1 sobre o KPM_t0 ([`src/closed_loop/hrdl_slice_loop.py`](../../../src/closed_loop/hrdl_slice_loop.py)) e o evento `control_request` traz o registro completo da decisão (estado, propostas, resoluções, ação selecionada, commit); com `rc.decision: catalog`, o RDL-N1 arbitra as propostas do cenário de conflito do catálogo ([`src/closed_loop/catalog_loop.py`](../../../src/closed_loop/catalog_loop.py); cenário lido de `/data/rdl_scenario`, padrão `rc.scenario` = S8) e só a cota de PRB no gNB 0 vira RIC Control (o resto fica em `not_actuated`, com o motivo; sem nada atuável, a xApp registra `control_decision` e não envia Control); com `rc.decision: fixed`, vêm de `rc.sliceQuotas`. No modo `catalog`, `/data/rdl_baseline` escolhe o baseline da decisão: B3 (RDL-N1, padrão) ou B0/B1/B2 (sem coordenação, FIFO, prioridade estática, `decide_baseline`). O B0 envia um Control por proposta atuável, em sequência, e o ACK de cada um é correlacionado pelo `RICInstanceID`. A decisão só dispara quando a Indication recebida completa o par KPM do período: nó (formato 1) e UEs (formato 3), chegados a no máximo `RC_PAIR_WINDOW_S` (0,5 s) um do outro. Assim, uma decisão rápida nunca usa os UEs do período anterior (achado 48). O intervalo do par vai para `kpm_pair_gap_ms` na decisão. Nos modos `hrdl` e `catalog`, a xApp aquece o RDL-N1 antes do primeiro KPM (evento `decision_warm_up`), para a importação das bibliotecas não atrasar o Control. A decisão registra o sha256 das duas Indications do relatório usado (`kpm_node_sha256`, formato 1, e `kpm_ues_sha256`, formato 3): o NORI as envia em par e o E2Term pode entregá-las em ordem trocada.

O *Event Trigger* (Format 1, `reportingPeriod` 1000 ms) e a *Action Definition* (estilo 1, Format 1, `granulPeriod` 1000 ms, métricas do estilo 1 anunciadas pelo NORI) são codificados em APER com `asn1tools`. A fonte é o ASN.1 do próprio NORI (`e2sm-v03.01.asn`, `e2sm-kpm-v03.00.asn`), baixado no commit fixado e conferido por sha256.

## Versões fixadas (`values.yaml`)

| Componente | Versão | Verificação |
| :-- | :-- | :-- |
| Imagem base | `python:3.10-slim-bookworm` | o `protobuf < 3.21` exigido pelo `ricxappframe` não tem wheel para 3.12 |
| RMR | 4.9.4 (`.deb` do packagecloud O-RAN SC) | sha256 `76b48a28…f10f84a` |
| `ricxappframe` | 3.2.2, sem dependências | só `ricxappframe.rmr` é usado (ctypes); as dependências declaradas (`ricsdl` → `hiredis`) exigiriam compilador C |
| `asn1tools` | 0.169.0 | — |
| Dependências do RDL-N1 | pydantic 2.13.5, numpy 2.2.6, pycrate 0.8.1, requests 2.34.2, structlog 26.1.0 | versões do `uv.lock`; instaladas com `--no-compile` (o bytecode do pycrate estoura a memória); limite do pod 1 GiB |
| ASN.1 E2SM do NORI | commit `8a30867` | sha256 por arquivo |

## Uso

```bash
bash scripts/deploy_kpm_probe.sh            # args extras vão para o helm (ex.: -f valores.yaml)
kubectl -n ricxapp logs -f deploy/kpm-probe | grep --line-buffered -v "RMR \[INFO\] sends"
bash scripts/observe/xapp_live.sh           # os mesmos eventos formatados (subscrição, KPM por UE, decisão, Control, ACK)
bash scripts/deploy_kpm_probe.sh --set rc.decision=catalog --set rc.afterIndications=12   # modo dos cenários S0–S8
```

Os eventos ficam em `/data/logs/kpm_probe_events.jsonl` (volume persistente). [`scripts/collect_nori_run.sh`](../../../scripts/collect_nori_run.sh) recorta os eventos do intervalo de uma execução NORI para `experiments/xapp_logs/<run_id>/`. Lá a dissecação do PCAP casa cada Indication do fio com a recebida pela xApp.

Eventos registrados: `start`, `kpm_encoded` (bytes hex do trigger e da action definition, sha256 do ASN.1 e do codec), `appmgr_register`, `rmr_ready`, `e2_node_status`, `subscription_request` (status e resposta do SubMgr), `submgr_notification` (resultado da subscrição no nó), `rmr_message`, `kpm` (KPM decodificado: formato 1 com as métricas do nó; formato 3 com UE, SST, PRBs, vazão e TBs), `decision_warm_up`, `control_decision` (decisão sem Control), `control_request`, `control_outcome`, `control_error`, `e2_node_disconnected`, `subscription_delete`, `appmgr_deregister`, `stop`.

## Detalhes de implantação

- Os serviços `service-ricxapp-kpm-probe-http` e `-rmr` expõem as portas 8080 (HTTP), 4560 (RMR dados) e 4561 (rotas). Eles usam `publishNotReadyAddresses`: o pod só fica pronto quando o RMR recebe a tabela de rotas, e o RtMgr só a entrega pelo serviço.
- `rmr_torcv_msg` precisa de um buffer alocado: com `None`, devolve ponteiro nulo.
- A RtMgr da Release I exige o A1 Mediator implantado. Sem ele, a criação da rota da subscrição estoura o prazo do SubMgr ([guia, seção 7.2](../../../docs/04_instalacao_e_operacao.md#72-near-rt-ric-o-ran-sc-release-i)).

## Resultado (2026-11-08)

Com o NORI (`nori-rc-slicing-flowmon`), a subscrição foi aceita (HTTP 201 e notificação com `E2EventInstanceId` ≠ 0). A xApp recebeu por RMR todas as Indications que o PCAP mostra no fio, com os mesmos bytes: 11 954 de 11 954 com período de 10 ms e 80 de 80 com período de 1 s. Detalhes no [docs/06, seção 5.2](../../../docs/06_metodologia_e_resultados.md#52-fase-2-subscrição-e-indications-kpm-reais-2026-11-08).

Fase 3, com o NORI corrigido pelo patch do chart `nori-ns3`: o Control (RICrequestID 1003/1, função 300, cotas eMBB 70 % e URLLC 30 % de PRB máximo) saiu por RMR e o ACK voltou correlacionado em 1,9 ms; os bytes do Control e do ACK são os mesmos do PCAP. Detalhes no [docs/06, seção 5.3](../../../docs/06_metodologia_e_resultados.md#53-fase-3-ric-control-e2sm-rc-com-ack-2026-11-08).
