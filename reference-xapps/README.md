# xApps de referência

Geradores de propostas usados para exercitar a xApp RDL. **Todas são implementações locais em Python** (`*_xapp.py`), escritas para este projeto. Algumas se inspiram no comportamento de xApps publicadas, mas nenhuma contém código upstream nem foi validada contra a implementação original.

Cada xApp expõe `/health`, `/ready` e `/metrics` (FastAPI + Prometheus) e envia propostas `RDL_ACTION_PROPOSAL` (mtype RMR 30000) no formato:

```json
{"xapp_id": "...", "node_id": "gnb_01", "parameter": "PRB_QUOTA", "value": 66.0, "priority": 90}
```

## 1. Catálogo

| xApp | Diretório | Parâmetro proposto | Inspiração | Classe |
| :-- | :-- | :-- | :-- | :-- |
| Traffic Steering | [`traffic-steering/`](traffic-steering/) | `HANDOVER` | comportamento de `o-ran-sc/ric-app-ts` | inspirada |
| xSlice | [`qos-xslice/`](qos-xslice/) | `PRB_QUOTA` | `peihaoY/xslice-oran` (Yan et al.) | inspirada |
| Energy Saving | [`energy-saving/`](energy-saving/) | `TX_POWER` | `Orange-OpenSource/ns-O-RAN-flexric` (`xapp_es_with_cell_util`) | inspirada |
| Load Balancer | [`load-balancer/`](load-balancer/) | `LOAD_THRESHOLD` | — | experimental |
| Beamformer | [`beamformer/`](beamformer/) | `VERTICAL_DOWNTILT` | — | experimental |
| ISAC Radar | [`isac-radar/`](isac-radar/) | `SENSING_RATIO` | — | experimental |
| Rogue | [`rogue-xapp/`](rogue-xapp/) | `TX_POWER` fora dos limites | — | teste de segurança |
| Bouncer | [`bouncer/`](bouncer/) | `PING_INTERVAL` | — | teste de latência |

A xApp RDL só sabe controlar os parâmetros definidos em `src/e2/rc/control_parameter.py` (`PRB_QUOTA`, `SCHEDULER_WEIGHT`, `TX_POWER`, `HANDOVER`). Propostas para `LOAD_THRESHOLD`, `VERTICAL_DOWNTILT`, `SENSING_RATIO` ou `PING_INTERVAL` são aceitas pelo pipeline, mas não têm codificação RC nem efeito na simulação.

## 2. Relação com os cenários ns-3

Os cenários de conflito S0–S7 **não executam estas xApps**. As propostas de cada cenário vêm de [`simulations/ns3/conflicts/catalog.json`](../simulations/ns3/conflicts/catalog.json), cujos `xapp_id` (`xslice`, `traffic_steering`, `energy_saving` etc.) reproduzem o papel dessas xApps. Ver [`docs/03_taxonomia_de_conflitos_e_cenarios.md`](../docs/03_taxonomia_de_conflitos_e_cenarios.md).

## 3. Execução

```bash
python reference-xapps/qos-xslice/xslice_xapp.py
```

As portas e os nós-alvo são configurados por variáveis de ambiente descritas no README de cada xApp.
