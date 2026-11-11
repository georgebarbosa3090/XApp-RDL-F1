# 11 — Governança hierárquica das xApps sob a RDL

Implementado em 2026-11-11 (achado 62 de [`07`](07_certificacao_e_achados.md)). Responde a duas perguntas:

1. Como garantir que nenhuma xApp mande RIC Control por fora da RDL?
2. Como supervisionar uma xApp só quando é preciso?

A governança tem quatro níveis. Cada nível cobre o que o anterior não alcança, e o mais lento fica no Non-RT RIC.

| Nível | Onde atua | Mecanismo | Escala de tempo | Código |
| :-: | :-- | :-- | :-- | :-- |
| 1 | plataforma (Kubernetes + RMR) | registro de xApps, descritores, NetworkPolicy e tabela de rotas | implantação | `src/governance/xapp_registry.py`, `deploy/helm/ric-governance` |
| 2 | Near-RT RIC (RMR) | interceptação por rota do RIC Control de xApps de terceiros | ms | `src/governance/interception.py` |
| 3 | Near-RT RIC (KPM) | conflito implícito: KPM incoerente com a ação confirmada | segundos | `src/core/implicit_conflict.py` |
| 4 | Non-RT RIC / SMO | rApp de governança: quarentena e teto de prioridade por A1, recomendação de retirada | segundos a minutos | `rapps/governance_rapp.py` |

## 1. Nível 1 — plataforma: a RDL é o único caminho de RIC Control

**Registro de xApps** (`RDL_XAPP_REGISTRY`, exemplo em [`configs/xapp_registry.example.json`](../configs/xapp_registry.example.json)). Para cada xApp:

- `sources`: expressões regulares para a origem RMR do remetente (`hostname:porta`);
- `mode`: modo de supervisão (seção 3);
- `max_priority`: teto de prioridade;
- `intercept_requestor_ids` e `default_priority`: dados para o nível 2.

Como o registro decide se uma proposta entra:

- **Modo estrito (`O_RAN_INTEROP`):** a proposta só entra se a xApp está registrada e a origem confere. Sem registro configurado, toda proposta externa é descartada, como antes.
- **Fora do modo estrito:** xApps não registradas são aceitas, como na bancada. Uma origem que contradiz o registro é recusada.
- **Toda recusa** é registrada como `UNAUTHORIZED` (`GET /rejections`).

**Por que a NetworkPolicy é necessária.** A origem RMR pode ser declarada pelo próprio remetente (`RMR_SRC_ID`), e uma xApp pode forjar a própria tabela de rotas. O registro, sozinho, não basta. O chart [`deploy/helm/ric-governance`](../deploy/helm/ric-governance) instala:

| Objeto | Efeito |
| :-- | :-- |
| `NetworkPolicy e2term-rmr-data-rdl-only` (ricplt) | a porta RMR de dados do E2Term (38000) só aceita a plataforma (ricplt), a RDL e a kpm-probe da bancada; o E2 Setup (SCTP 36422), as métricas e o namespace do NORI (`ricsim`) continuam abertos |
| `NetworkPolicy rdl-rmr-data-proposers-only` (ricxapp) | a porta RMR de dados da RDL (4560) só aceita a plataforma e os pods com o rótulo `rdl.governance/proposer: "true"`, que os charts das xApps de referência agora aplicam |
| `ConfigMap rdl-governance-routes` | tabela de rotas RMR (`RMR_SEED_RT`): 30000 → RDL, 30001 → xApps proponentes, 12040 de cada xApp interceptada → RDL, 12040 da RDL → E2Term |

O descritor da RDL ([`configs/xapp_descriptor.json`](../configs/xapp_descriptor.json)) é o único que declara `RIC_CONTROL_REQ` em `txMessages`. Ele também recebe `RIC_CONTROL_REQ`, por causa da interceptação.

**Verificado no cluster da bancada** (k3s, O-RAN SC Release I), em 2026-11-11:

| Origem → E2Term:38000 | Sem a política | Com a política |
| :-- | :-: | :-: |
| kpm-probe (ricxapp, autorizada) | aberta | aberta |
| a1pms-osc-adapter (nonrtric, não autorizada) | aberta | **recusada** (`ConnectionRefused`) |

O controlador de NetworkPolicy do k3s (kube-router) aplica a regra. **Não verificado:** o E2 Setup do NORI com a política ativa. A regra libera o namespace `ricsim` inteiro justamente para não depender de a implementação reconhecer SCTP.

## 2. Nível 2 — interceptação por rota (xApps de terceiros)

Para xApps que não podem ser alteradas, uma rota com remetente (`mse|12040,<origem>|-1|<RDL>`) entrega o RIC Control Request delas à RDL em vez do E2Term. A RDL então:

1. Decodifica o E2AP e o E2SM-RC. Formatos entendidos:
   - E2SM-RC v03.01 do NORI, Style 2 / Action 6 (cotas por fatia → `PRB_QUOTA` com o teto da SST 1);
   - o perfil próprio da RDL (um parâmetro por mensagem).
   Outros formatos recebem Failure.
2. Cria a proposta com a identidade e a prioridade do registro (`intercept_requestor_ids`). Um RICrequestorID desconhecido recebe Failure e entra no registro como `UNAUTHORIZED`.
3. Arbitra a proposta como qualquer outra. Se ela vence, a RDL envia o controle ao nó com o próprio RICrequestID.
4. Responde à xApp por *return to sender*, com o RICrequestID e o RANfunctionID que ela usou:
   - **Acknowledge**, quando o nó confirma o controle da RDL;
   - **Failure** (Cause `ricRequest / control-failed-to-execute`), quando a proposta é recusada, o nó falha ou o tempo esgota;
   - **Failure** com Cause `unspecified`, depois de 10 s sem desfecho.

**Verificado:** decodificação dos dois formatos, montagem do ACK e do Failure, e o fluxo completo com RMR simulado (`tests/unit/test_governance.py`). **Não verificado:** com RMR real, uma xApp de terceiros e uma rota de remetente no RtMgr. A sintaxe de rota com remetente é a do RMR; a forma de expressá-la no RtMgr (rotas de plataforma) precisa ser confirmada no testbed.

## 3. Supervisão sob demanda: gerenciar uma xApp só quando é preciso

Cada xApp tem um modo, definido no registro ou na política A1 20000 (`xapp_modes`):

| Modo | Tratamento |
| :-- | :-- |
| `MANAGED` (padrão) | toda proposta passa pela janela de decisão |
| `ON_DEMAND` | a proposta é decidida **na chegada, sozinha** (Safety Guard e intervalo mínimo valem). Vai para a janela só quando há disputa: outra xApp propôs para o mesmo nó ou para um vizinho nos últimos `RDL_ON_DEMAND_LOOKBACK_S` (2 s), há proposta pendente nesses nós ou o grafo registra conflito recente no alvo |
| `QUARANTINED` | toda proposta é recusada como `UNAUTHORIZED` |

**Para que serve o `ON_DEMAND`.** Uma xApp que raramente disputa recursos (por exemplo, o EnergySaver à noite) não paga a espera da janela. A RDL passa a supervisioná-la quando aparece concorrência e, depois disso, a trata como `MANAGED` enquanto a disputa durar. A decisão sai com `reason = ON_DEMAND` e conta em `rdl_on_demand_decisions_total`.

**Fora da RDL: ligar e desligar a própria xApp.** Isso é o ciclo de vida da xApp, papel do SMO:

- um rApp pede ao AppMgr (ou ao Helm) para implantar a xApp quando um gatilho de negócio aparece (horário, intenção A1, alarme) e para retirá-la depois;
- dá para escalar a zero por evento (por exemplo, KEDA);
- a xApp implantada sob demanda ainda passa pela RDL, nos modos acima.

**Teto de prioridade** (`max_priority` no registro, `xapp_priority_caps` na A1). A proposta é rebaixada ao teto, e a prioridade pedida fica em `requested_priority`. Um teto abaixo de 95 impede a xApp de usar o caminho crítico pela prioridade.

## 4. Nível 3 — conflito implícito

A RDL confere cada relatório KPM contra as ações que o nó confirmou:

| Ação confirmada | Violação |
| :-- | :-- |
| `CELL_STATE = 0` | vazão DL > 0,5 Mb/s ou PRBs em uso |
| `PRB_QUOTA = q` | fatia SST 1 com mais de q + 10 % dos PRBs (só quando o KPM traz a fatia: `sst1_prb_share_pct`) |

Para não confundir transitório com conflito, a verificação começa `RDL_IMPLICIT_GRACE_S` (2 s) depois do ACK. A violação precisa se repetir em `RDL_IMPLICIT_PERSISTENCE` (3) relatórios seguidos, e cada episódio gera um único achado.

O achado vira `ConflictType.IMPLICIT`. Ele fica no grafo de conhecimento, nas métricas (`rdl_implicit_conflicts_total`) e no relatório `GET /governance`, com uma lista de suspeitas:

- xApps interceptadas ou que propuseram para o nó nos últimos 30 s;
- ou `out-of-band`, se não houver nenhuma.

`TX_POWER`, `SCHEDULER_WEIGHT` e `HANDOVER` ficam sem verificação: o KPM disponível não mede potência nem célula servidora por UE.

## 5. Nível 4 — Non-RT RIC / SMO

`GET /governance` (porta 8080) devolve:

- recusas por motivo e por xApp;
- conflitos implícitos;
- rebaixamentos de ações críticas por xApp;
- o registro, com os modos efetivos;
- interceptações pendentes;
- o estado da janela.

O [`rapps/governance_rapp.py`](../rapps/governance_rapp.py) lê esse relatório e aplica regras fixas:

| Evidência | Ação |
| :-- | :-- |
| ≥ 5 recusas `SAFETY` | `QUARANTINED` |
| ≥ 20 recusas `UNAUTHORIZED` | `QUARANTINED` |
| ≥ 10 ações críticas acima da cota | teto de prioridade 94 |
| xApp registrada suspeita de conflito implícito | `QUARANTINED` e candidata à retirada |
| xApp fora do registro suspeita | recomendação de retirada |
| `out-of-band` | investigação pelo operador |

As ações sobre a RDL saem numa única instância A1 20000 (`rdl-governance`), publicada no A1-PMS. A retirada (`DELETE /ric/v1/xapps/{nome}` no AppMgr) só acontece com `--undeploy`; sem isso, a recomendação é só impressa. **Sair da quarentena é decisão do operador.** Perder arbitragem não é falta: o rApp não pune quem perde.

## 6. Onde ficam o estado e o grafo

| Pergunta | Resposta |
| :-- | :-- |
| O dbaas (Redis) é do Near-RT ou do Non-RT? | Do **Near-RT RIC**: o `dbaas` roda no namespace `ricplt` e é o SDL das xApps. O Non-RT RIC (A1-PMS) tem banco próprio, desligado na bancada. |
| O modo catálogo fica no dbaas? | **Não.** O cenário e o baseline da kpm-probe ficam em arquivos no volume dela (`/data/rdl_scenario`, `/data/rdl_baseline`). No modo `O_RAN_INTEROP`, a RDL grava no SDL (dbaas) os pedidos de controle, as decisões e as recusas (`rejection:<id>`). |
| Onde atua o grafo de conhecimento próprio? | Dentro da RDL, no Near-RT RIC: em memória, consultado a cada decisão (contexto da CA-RDL, disputa do modo sob demanda) e exposto em `GET /kg`. |
| Onde atua o NetworkX? | **Fora do laço de decisão:** análise do grafo exportado (centralidade, componentes, caminhos de conflito) num notebook, num teste ou no rApp (`src/core/kg_export.py: to_networkx`; extra `kg`). |
| Onde atua o Neo4j? | **No SMO / Non-RT RIC:** histórico persistente, que sobrevive ao reinício da RDL e é consultado pelos rApps. A RDL não depende dele. Exportação por `scripts/kg/export_kg.py` (Cypher para `cypher-shell`, ou gravação direta com `--neo4j-uri` e senha em `NEO4J_PASSWORD`). Um banco de grafos externo no caminho de cada decisão poria latência de rede dentro da janela de 200 ms. |

## 7. Configuração

| Variável | Padrão | Efeito |
| :-- | :-- | :-- |
| `RDL_XAPP_REGISTRY` | — | arquivo JSON do registro |
| `RDL_ADAPTIVE_WINDOW` | `true` (desde 2026-11-11) | janela adaptativa; `false` volta à janela fixa de 200 ms |
| `RDL_ON_DEMAND_LOOKBACK_S` | 2,0 | quanto tempo uma disputa mantém a xApp `ON_DEMAND` na janela |
| `RDL_IMPLICIT_GRACE_S` / `RDL_IMPLICIT_PERSISTENCE` | 2,0 / 3 | período de graça e persistência do conflito implícito |

Na política A1 20000, os campos `xapp_modes` (lista `xapp:MODO`) e `xapp_priority_caps` (lista `xapp:N`) sobrepõem o registro enquanto a política vale.
