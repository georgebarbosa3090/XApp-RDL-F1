# Chart `xapp-kpm-probe` — assinatura E2SM-KPM v3.00 no Near-RT RIC Release I

xApp mínima, implantada via Helm sem Docker, que materializa os elos **Subscription** e **KPM** da cadeia closed-loop (gate G1). Ela não decide nem controla nada.

1. Registra-se no AppMgr (`/ric/v1/register`); o RtMgr passa a distribuir rotas RMR para ela.
2. Acompanha os nós E2 no E2Mgr (`/v1/nodeb/states`). A cada nó que fica `CONNECTED`, envia ao SubMgr (`POST /ric/v1/subscriptions`, porta 8088) uma subscrição REPORT na RAN function KPM (200 no NORI). Quando o nó cai, apaga a subscrição.
3. Recebe por RMR as RIC Indications (tipo 12050) e registra tipo, subscription id, MEID, tamanho e sha256 do payload.

O *Event Trigger* (Format 1, `reportingPeriod` 1000 ms) e a *Action Definition* (estilo 1, Format 1, `granulPeriod` 1000 ms, métricas do estilo 1 anunciadas pelo NORI) são codificados em APER com `asn1tools`. A fonte é o ASN.1 do próprio NORI (`e2sm-v03.01.asn`, `e2sm-kpm-v03.00.asn`), baixado no commit fixado e conferido por sha256.

## Versões fixadas (`values.yaml`)

| Componente | Versão | Verificação |
| :-- | :-- | :-- |
| Imagem base | `python:3.10-slim-bookworm` | o `protobuf < 3.21` exigido pelo `ricxappframe` não tem wheel para 3.12 |
| RMR | 4.9.4 (`.deb` do packagecloud O-RAN SC) | sha256 `76b48a28…f10f84a` |
| `ricxappframe` | 3.2.2, sem dependências | só `ricxappframe.rmr` é usado (ctypes); as dependências declaradas (`ricsdl` → `hiredis`) exigiriam compilador C |
| `asn1tools` | 0.169.0 | — |
| ASN.1 E2SM do NORI | commit `8a30867` | sha256 por arquivo |

## Uso

```bash
helm upgrade --install kpm-probe deploy/helm/xapp-kpm-probe -n ricxapp
kubectl -n ricxapp logs -f deploy/kpm-probe | grep --line-buffered -v "RMR \[INFO\] sends"
```

Os eventos ficam em `/data/logs/kpm_probe_events.jsonl` (volume persistente). [`scripts/collect_nori_run.sh`](../../../scripts/collect_nori_run.sh) recorta os eventos do intervalo de uma execução NORI para `experiments/xapp_logs/<run_id>/`. Lá a dissecação do PCAP casa cada Indication do fio com a recebida pela xApp.

Eventos registrados: `start`, `kpm_encoded` (bytes hex do trigger e da action definition, sha256 do ASN.1), `appmgr_register`, `rmr_ready`, `e2_node_status`, `subscription_request` (status e resposta do SubMgr), `submgr_notification` (resultado da subscrição no nó), `rmr_message`, `e2_node_disconnected`, `subscription_delete`, `appmgr_deregister`, `stop`.

## Detalhes de implantação

- Os serviços `service-ricxapp-kpm-probe-http` e `-rmr` expõem as portas 8080 (HTTP), 4560 (RMR dados) e 4561 (rotas). Eles usam `publishNotReadyAddresses`: o pod só fica pronto quando o RMR recebe a tabela de rotas, e o RtMgr só a entrega pelo serviço.
- `rmr_torcv_msg` precisa de um buffer alocado: com `None`, devolve ponteiro nulo.
- A RtMgr da Release I exige o A1 Mediator implantado. Sem ele, a criação da rota da subscrição estoura o prazo do SubMgr ([guia, seção 7.2](../../../docs/02_guia_operacional_deploy_e_simulacao.md#72-near-rt-ric-o-ran-sc-release-i)).

## Resultado (2026-11-08)

Com o NORI (`nori-rc-slicing-flowmon`), a subscrição foi aceita (HTTP 201 e notificação com `E2EventInstanceId` ≠ 0). A xApp recebeu por RMR todas as Indications que o PCAP mostra no fio, com os mesmos bytes: 11 954 de 11 954 com período de 10 ms e 80 de 80 com período de 1 s. Detalhes no [guia, seção 7.7](../../../docs/02_guia_operacional_deploy_e_simulacao.md#77-resultado-da-fase-2-subscrição-e-indications-kpm-reais-2026-11-08).
