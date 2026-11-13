# Perfil de integração com o O-RAN SC

## 1. Interfaces

```text
            ┌──────────────── Plataforma Near-RT RIC (O-RAN SC) ────────────────┐
            │   Subscription Manager (REST :8088)        E2Term (SCTP / RMR)     │
            └──────────────┬───────────────────────────────────┬────────────────┘
                 REST      │  ▲ notificação HTTP           RMR │ ▲
                           ▼  │                                ▼ │
            ┌──────────────────── xApp RDL (RDL-N1) ─────────────────────────────┐
            │  SubscriptionManager    HTTP :8080        RMR :4560 (MEID por msg) │
            │  métricas Prometheus :8081                                        │
            └────────────────────────────────────────────────────────────────────┘
```

## 2. Tipos de mensagem

| Operação | Transporte | `mtype` RMR | ProcedureCode E2AP | Direção |
| :-- | :-- | :-: | :-: | :-- |
| E2 Setup | SCTP (E2Term) | — | 1 | E2 Node → E2Term |
| Pedido de subscrição | REST `POST /ric/v1/subscriptions` | — | 8 (gerado pelo SubMgr) | xApp → SubMgr |
| Resultado da subscrição | REST `POST /ric/v1/subscriptions/response` | — | — | SubMgr → xApp |
| RIC Indication | RMR | 12050 | 5 | E2Term → xApp |
| RIC Control Request | RMR com MEID | 12040 | 4 | xApp → E2Term |
| RIC Control Acknowledge | RMR | 12041 | 4 | E2Term → xApp |
| RIC Control Failure | RMR | 12042 | 4 | E2Term → xApp |
| Proposta de ação (interna) | RMR | 30000 | — | xApps → xApp RDL |

Os mtypes 12010/12011 (subscrição por RMR) existem nas constantes, mas a subscrição usa a API REST.

## 3. Subscrição

Corpo `SubscriptionParams` conforme o modelo do cliente REST do `ricxappframe` 3.2.2:

```json
{
  "ClientEndpoint": {"Host": "service-ricxapp-iqos-xapp-rdl-http.ricxapp", "HTTPPort": 8080, "RMRPort": 4560},
  "Meid": "gnb_01",
  "RANFunctionID": 2,
  "SubscriptionDetails": [{
    "XappEventInstanceId": 1,
    "EventTriggers": [/* octetos E2SM-KPM */],
    "ActionToBeSetupList": [{
      "ActionID": 1, "ActionType": "report",
      "ActionDefinition": [/* octetos E2SM-KPM */],
      "SubsequentAction": {"SubsequentActionType": "continue", "TimeToWait": "zero"}
    }]
  }]
}
```

O host e as portas vêm de `XAPP_HTTP_HOST`, `XAPP_HTTP_PORT` e `XAPP_RMR_PORT`; o endereço do SubMgr, de `SUBMGR_URL` (padrão `http://service-ricplt-submgr-http.ricplt:8088` no modo estrito). A subscrição só é considerada ativa depois da notificação com `E2EventInstanceId` positivo e sem `ErrorCause`.

## 4. Envio RMR com MEID

`rmr_send(payload, mtype, retries)` do `ricxappframe` não define MEID. A xApp usa `rmr_alloc_msg(..., meid=<nó>)` e `rmr_send_msg`, repetindo só enquanto o RMR devolve `RMR_ERR_RETRY`, e sempre libera o buffer (`src/infrastructure/rmr_transport.py`).

## 5. Rotas e implantação

- Tabelas de rota de exemplo: `configs/routes.rt.template`, `configs/uta_rtg.rt`.
- Descritor da xApp: `configs/xapp_descriptor.json`.
- Helm: `deploy/helm/iqos-xapp-rdl`; manifestos: `deploy/kubernetes/`.

Nenhum destes itens foi verificado contra uma plataforma O-RAN SC em funcionamento.
