# 23 — Fluxo de mensagens da H-RDL

Diagrama de sequência do ciclo implementado: subscrição, telemetria, propostas, decisão, controle e resposta. **Nenhum trecho deste fluxo foi exercitado contra um E2 Node e um Near-RT RIC reais**; os tempos indicados são parâmetros de configuração, não medições.

```mermaid
sequenceDiagram
    autonumber
    participant X as xApps<br/>(xSlice, Energy Saving, Traffic Steering)
    participant R as xApp RDL
    participant S as Subscription Manager
    participant T as E2Term
    participant N as E2 Node

    rect rgb(245, 247, 250)
        Note over R,N: Inicialização
        N->>T: E2 Setup (RAN Functions KPM e RC)
        R->>S: POST /ric/v1/subscriptions (SubscriptionParams, KPM a cada 200 ms)
        S-->>R: SubscriptionId (estado SUBSCRIBING)
        S->>T: RIC Subscription Request (E2AP)
        T->>N: RIC Subscription Request
        N-->>T: RIC Subscription Response
        S->>R: POST /ric/v1/subscriptions/response (E2EventInstanceId)
        Note over R: estado READY
    end

    rect rgb(240, 248, 255)
        Note over X,N: Telemetria e propostas
        N->>T: RIC Indication (E2SM-KPM)
        T->>R: RMR 12050
        par propostas concorrentes (RMR 30000, JSON)
            X->>R: xSlice: PRB_QUOTA 75 %, prioridade 90
        and
            X->>R: Energy Saving: PRB_QUOTA 30 %, prioridade 65
        end
        Note over R: janela de 200 ms (fecha antes se prioridade ≥ 80)
    end

    rect rgb(240, 253, 244)
        Note over R: Decisão
        R->>R: Safety Guard por proposta (limites e formato)
        R->>R: Percepção: conflitos por alvo (+ incumbente confirmada)
        R->>R: TVS: um vencedor por (nó, parâmetro)
        R->>R: EEVS: conflitos indiretos entre vencedores
        R->>R: Refinement: limites, histerese de 1 s, slew-rate opcional
    end

    rect rgb(254, 252, 232)
        Note over R,N: Controle
        R->>T: RIC Control Request (RMR 12040, MEID do nó, RICrequestID)
        T->>N: RIC Control Request (E2SM-RC)
        alt aceito
            N-->>T: RIC Control Acknowledge
            T-->>R: RMR 12041 → ação vira estado confirmado
        else recusado
            N-->>T: RIC Control Failure
            T-->>R: RMR 12042 → FAILED, sem rollback
        else sem resposta em 5 s
            R->>T: rollback para o último valor confirmado (novo RICrequestID, noAck)
        end
    end

    rect rgb(255, 241, 242)
        Note over R,N: Realimentação
        N->>T: RIC Indication seguinte (KPM)
        T->>R: RMR 12050 → entra nos modelos da próxima janela
    end
```

## Mensagens

| Mensagem | Transporte | Identificador | Origem → destino | Código |
| :-- | :-- | :-- | :-- | :-- |
| Pedido de subscrição | REST | `POST /ric/v1/subscriptions` | xApp → SubMgr | `src/infrastructure/subscription_manager.py` |
| Notificação de subscrição | REST | `POST /ric/v1/subscriptions/response` | SubMgr → xApp | `src/observability/health_server.py`, `RDLxApp._subscription_notification_handler` |
| RIC Indication | RMR | 12050 | E2Term → xApp | `RDLxApp._kpm_indication_handler` |
| Proposta de ação | RMR | 30000 | xApp → xApp RDL | `RDLxApp._action_proposal_handler` |
| RIC Control Request | RMR com MEID | 12040 | xApp RDL → E2Term | `ControlDispatcher.dispatch_control`, `rmr_transport.send_rmr_message` |
| RIC Control Acknowledge | RMR | 12041 | E2Term → xApp RDL | `ControlDispatcher.handle_ack` |
| RIC Control Failure | RMR | 12042 | E2Term → xApp RDL | `ControlDispatcher.handle_failure` |

## Parâmetros de tempo

| Parâmetro | Valor | Onde |
| :-- | :-- | :-- |
| Janela de decisão | 200 ms | `RDLxApp.WINDOW_DURATION_MS` |
| Histerese por alvo | 1000 ms | `Refinement.config["minimum_control_interval_ms"]` |
| Timeout de controle | 5 s | `ControlDispatcher(default_timeout_s=5.0)` |
| Período KPM pedido | 200 ms | backend (`default_kpm_period_ms`) |
| Retenção de transações finalizadas | 5 min | `ControlDispatcher.prune_finalized` |

Versões das figuras para a dissertação: [`figures/diagrama_sequencia_compacto_dissertacao.mermaid`](figures/diagrama_sequencia_compacto_dissertacao.mermaid), [`.puml`](figures/diagrama_sequencia_compacto_dissertacao.puml) e [`.tex`](figures/diagrama_sequencia_compacto_dissertacao.tex).
