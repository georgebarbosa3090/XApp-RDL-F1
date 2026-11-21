# URLLC Slice Guard

xApp própria do projeto RDL (autor: George Barbosa; Apache-2.0). Ela protege a fatia URLLC limitando a fatia eMBB da célula, a partir do KPM. Faz o papel `xslice` do catálogo de cenários (`simulations/ns3/conflicts/catalog.json`), mas **não é o xSlice** nem uma reimplementação dele: o xSlice original (`peihaoY/xslice-oran`) decide por um agente PPO com GCN, que não está integrado ao projeto (docs/16 §8). O código original está em [`third_party/xapps/xslice-oran/`](../../third_party/xapps/).

**Nome anterior.** Até 21/11/2026, esta xApp se chamava `qos-xslice` (`xslice_xapp.py`, chart `xapp-qos-xslice`), e o núcleo era `XSliceDerivada`, com `xapp_id` `xslice`. As execuções anteriores registram esse nome. A versão anterior tinha carga simulada (`SIMULATED_TRAFFIC_LOAD`), perfis de cota fixos e metadados de energia e de SLA com valores constantes. Esses trechos foram retirados, e a regra ganhou histerese e tratamento de recusa ("Comparativo xApps originais e próprias", seção 3.2).

## Decisão

O núcleo é [`src/xapps/proprias.py`](../../src/xapps/proprias.py) (`UrllcSliceGuard`). O mesmo núcleo roda na malha fechada do ns-3, na bancada NORI (pod de proponentes da kpm-probe) e neste processo.

| Passo | Regra | Padrão |
| :-- | :-- | :-- |
| Entrada | Maior atraso por UE (`DRB.RlcSduDelayDl`) dos UEs da fatia URLLC, agrupados pelo SST do próprio KPM (`DRB.NetworkSlicing.SST`) | SST 2 |
| Proteger | Atraso acima do limite: propõe `PRB_QUOTA` (teto eMBB) baixo, prioridade alta | 10 ms; 25 %; prioridade 90 |
| Relaxar | Atraso abaixo de uma fração do limite por N janelas seguidas: propõe teto alto, prioridade baixa | 0,7 × limite; 5 janelas; 80 %; prioridade 60 |
| Histerese | Se a proteção volta em até N janelas depois de relaxar, N dobra | até 40 janelas |
| Recusa | `RDL_ACTION_RESULT` (30001) devolve a célula ao estado anterior; a xApp volta a propor enquanto a condição durar | |

**Descrição:** cada linha é uma etapa da decisão por célula, com os parâmetros de `UrllcSliceGuard.DEFAULTS` (prefixo `usg_`). A convenção da RDL é que `PRB_QUOTA` é a parcela da fatia eMBB, e a outra fatia recebe o resto.

Na malha fechada do ns-3, o SST de cada UE vem do próprio KPM (campo `sst`, gravado pelo cenário com `RdlActuation::SetUeSst`). O orquestrador não injeta mais a fatia.

## Implantação (Helm)

```bash
helm upgrade --install ricxapp-urllc-slice-guard deploy/helm/xapp-urllc-slice-guard -n ricxapp --set env.kpmNodes=<nós E2>
```

| Variável | Padrão | Descrição |
| :-- | :-- | :-- |
| `SUBMGR_URL` | `http://service-ricplt-submgr-http.ricplt:8088` | API REST do SubMgr. Sem ela, a xApp não recebe KPM e não propõe |
| `KPM_NODES` | vazio | Nós E2, separados por vírgula |
| `KPM_RAN_FUNCTION_ID` | `2` | RAN function E2SM-KPM do nó (NORI: 200) |
| `KPM_PERIOD_MS` | `1000` | Período de relatório pedido na subscrição |
| `DECISION_PERIOD_S` | `1.0` | Período de decisão |
| `RDL_TRANSPORT` | `rmr` | Entrega das propostas (`rmr`, `http`, `none`) |
| `HTTP_PORT`, `RMR_PORT` | `8082`, `4562` | Portas da API HTTP e da RMR |

**Descrição:** variáveis de ambiente lidas pelo processo. O chart passa todas a partir de `values.yaml`.

## Endpoints e métricas

- `GET :8082/health`, `GET :8082/ready` (pronto só com a subscrição KPM ativa), `GET :8082/state` (estado por célula e política em vigor), `GET :8082/proposals/latest` (última proposta enviada).
- `GET :8082/metrics`:
  - `usg_proposals_total{node_id,kind}`: propostas enviadas (`proteger` ou `relaxar`);
  - `usg_refusals_total{node_id,reason}`: recusas recebidas pela RMR 30001;
  - `usg_urllc_delay_ms{node_id}`: maior atraso da URLLC medido no KPM;
  - `usg_embb_cap_pct{node_id}`: último teto eMBB proposto.

**Não verificado com RAN real nem com RMR real**, como as demais xApps de `reference-xapps/`.
