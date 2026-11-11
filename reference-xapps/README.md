# xApps de referência

Geradores de propostas usados para exercitar a xApp RDL. **Todas são implementações locais em Python** (`*_xapp.py`), escritas para este projeto. Algumas se inspiram no comportamento de xApps publicadas, mas nenhuma contém código upstream nem foi validada contra a implementação original. Nenhuma lê KPM: os valores propostos vêm de configuração.

Cada xApp expõe `/health`, `/ready` e `/metrics` (FastAPI + Prometheus) e gera propostas no formato:

```json
{"xapp_id": "...", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 66.0, "priority": 90}
```

**Entrega (desde 2026-11-11):** xSlice, Energy Saving, Traffic Steering e Rogue enviam a proposta por RMR `RDL_ACTION_PROPOSAL` (30000) e recebem `RDL_ACTION_RESULT` (30001) com o motivo da recusa e `retry_after_ms`. O módulo comum é [`common/rdl_transport.py`](common/rdl_transport.py), e `RDL_TRANSPORT` escolhe o modo:

- `rmr`: padrão nos charts;
- `http`: POST para `RDL_HTTP_URL`, que a RDL não recebe; serve só a um coletor de testes;
- `none`: só registra localmente.

Os charts aplicam o rótulo `rdl.governance/proposer: "true"`, exigido pela NetworkPolicy da RDL ([doc 11](../docs/11_governanca_hierarquica_xapps.md)). No modo estrito, a xApp também precisa estar no registro da RDL (`RDL_XAPP_REGISTRY`; exemplo em [`configs/xapp_registry.example.json`](../configs/xapp_registry.example.json)). **Não verificado com RMR real.**

Campos opcionais da proposta: `defer_ok` (reavaliar a proposta quando o bloqueio de histerese do alvo expirar) e `ttl_ms` (validade pedida, até 3000 ms). Ver [docs/02 §3.2](../docs/02_modelo_de_decisao_h_rdl.md).

## 1. Catálogo

| xApp | Diretório | Parâmetro proposto | Inspiração | Classe |
| :-- | :-- | :-- | :-- | :-- |
| Traffic Steering | [`traffic-steering/`](traffic-steering/) | `HANDOVER` (valor = índice da célula de destino) | comportamento de `o-ran-sc/ric-app-ts` | inspirada |
| xSlice | [`qos-xslice/`](qos-xslice/) | `PRB_QUOTA` | `peihaoY/xslice-oran` (Yan et al.) | inspirada |
| Energy Saving | [`energy-saving/`](energy-saving/) | `TX_POWER` | `Orange-OpenSource/ns-O-RAN-flexric` (`xapp_es_with_cell_util`) | inspirada |
| Rogue | [`rogue-xapp/`](rogue-xapp/) | `TX_POWER` alternando 45 dBm (fora dos limites) e 5 dBm | — | teste de segurança |

Beamformer, ISAC Radar, Load Balancer e Bouncer saíram em 2026-11-10 (achado 58 de `docs/07`): propunham parâmetros fora do catálogo da RDL, que o Safety Guard rejeita por *default-deny*, e não enviavam propostas. O histórico do git os preserva.

A xApp RDL só controla os parâmetros de `src/e2/rc/control_parameter.py` (`PRB_QUOTA`, `SCHEDULER_WEIGHT`, `TX_POWER`, `HANDOVER`, `CELL_STATE`).

## 2. Relação com os cenários ns-3

Os cenários de conflito **não executam estas xApps**. As propostas de cada cenário vêm de [`simulations/ns3/conflicts/catalog.json`](../simulations/ns3/conflicts/catalog.json), cujos `xapp_id` (`xslice`, `traffic_steering`, `energy_saving`, `rogue_xapp` etc.) reproduzem o papel dessas xApps. Ver [`docs/03_cenarios_e_conflitos.md`](../docs/03_cenarios_e_conflitos.md).

## 3. Execução

```bash
python reference-xapps/qos-xslice/xslice_xapp.py
```

As portas e os nós-alvo são configurados por variáveis de ambiente descritas no README de cada xApp.
