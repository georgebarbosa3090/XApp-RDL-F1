# RELATÓRIO DE AUDITORIA TÉCNICO-CIENTÍFICA PROFUNDA
## XApp-RDL Fase 1 (H-RDL) × XApp-RDL Fase 2 (CA-RDL)

**Data da auditoria:** 14 de setembro de 2026  
**Escopo:** arquitetura, implementação, O-RAN/E2, CI/CD, rastreabilidade causal, proveniência, experimentos, resultados, reprodutibilidade e prontidão para publicação.  
**Repositórios auditados:**

- `georgebarbosa3090/XApp-RDL-F1`
- `georgebarbosa3090/XApp-RDL-F2`

---

# 0. NOTA DE EVIDÊNCIA E FRESCOR DOS DADOS

Este relatório adota deliberadamente uma política conservadora de evidência.

A última leitura **autenticada e diretamente verificável** obtida durante esta linha de auditorias registrou:

- **F1 HEAD:** `f154728a4374e16ada2faaebd4780415a40fd313`
- **F2 HEAD:** `3663d1654a9a71fc44874f773b231ee6cf9de7cb`

Naquela leitura:

- F1 possuía GitHub Actions vermelha no estágio `Syntax & Smoke Import Check`;
- F2 possuía GitHub Actions vermelha no estágio `Run Pyright Static Audit`.

Durante a elaboração desta auditoria, a integração GitHub autenticada ficou indisponível. A inspeção pública do GitHub retornou páginas em cache, com defasagem de aproximadamente 3–5 dias, portanto **não foi usada para substituir o estado autenticado mais recente**.

As páginas públicas em cache mostram estados históricos distintos, por exemplo:

- F1 com 138 commits e histórico visível até 10/09/2026;
- F2 com 132 commits, 121 workflow runs e uma sequência de commits de evolução arquitetural;
- diretórios históricos de resultados contendo datasets e relatórios.

Esses artefatos públicos são úteis como contexto histórico, mas não podem ser tratados como prova do HEAD atual, pois conflitam com a leitura autenticada posterior.

**Regra adotada neste relatório:**

> quando houver divergência entre documentação pública em cache e leitura autenticada posterior, prevalece a evidência autenticada mais recente.

---

# 1. RESUMO EXECUTIVO

A família RDL já atingiu um nível arquitetural alto. O problema principal deixou de ser “falta de componentes” e passou a ser **fechamento científico, interoperabilidade externa e disciplina de evidência**.

A Fase 1 está madura o suficiente para **congelamento de features**. O H-RDL possui uma arquitetura coerente, separação entre percepção/raciocínio/refinamento, abstração de backend, mecanismos de segurança e uma evolução relevante da cadeia de controle. O próximo salto não virá de novas classes ou novos cenários; virá de um bundle externo irrefutável contendo:

```text
E2 Setup
→ RANFunctionDefinition
→ KPM Subscription
→ KPM Indication
→ conflito
→ RDLDecision
→ E2SM-RC
→ ACK/Failure
→ mudança observável do estado RAN
→ KPM pós-controle
```

A Fase 2 é arquiteturalmente mais ambiciosa e potencialmente mais forte cientificamente, incorporando contexto, causal graph, MAPPO, action masking, observation contracts e Safe-RL. Entretanto, ela ainda não possui uma base experimental causal e externa suficientemente forte para sustentar claims de superioridade científica sobre a F1.

A conclusão central é:

```text
F1 = baseline científica a ser congelada e validada externamente.
F2 = arquitetura cognitiva promissora que deve parar de expandir e estabilizar foundation + ciência.
```

---

# 2. VEREDITO GLOBAL

| Dimensão | F1 — H-RDL | F2 — CA-RDL | Auditoria |
|---|---:|---:|---|
| Arquitetura de software | 9,1/10 | 8,8/10 | forte em ambas |
| Separação core/backend | 9,0 | 8,7 | F1 ligeiramente mais madura |
| Safety/Refinement | 9,1 | 8,8 | F1 mais previsível |
| Raciocínio/contexto | 8,2 | 9,0 | vantagem F2 |
| MARL/MAPPO | N/A | 8,7 algorítmico | ainda não científico |
| Rastreamento causal | 7,8 | 6,5–7,2 | F2 precisa herdar integralmente F1 |
| CI/software | 6,5 | 6,0–6,5 | ambos com HEAD não confirmado verde |
| Proveniência científica | 7,5–7,8 | 5,5–6,0 | F1 à frente |
| Interop E2 externa | 1–2/10 | 0,5–1,5/10 | sem prova L4 robusta |
| Closed loop externo | 0/10 | 0/10 | principal gap |
| Reprodutibilidade | 4,5/10 | 3,5–4,0/10 | ainda incompleta |
| Prontidão de publicação | ~55–60% | ~45–55% | F1 mais próxima do primeiro paper experimental |

Classificação conservadora:

```text
F1: L3+ avançado
F2: L3 de software/cognição, L2–L3 científico
```

Nenhuma das duas fases deve ser classificada como L5 científico enquanto não houver closed loop causal externo demonstrado.

---

# 3. METODOLOGIA DA AUDITORIA

A auditoria usa quatro camadas.

## 3.1 Conformidade arquitetural

Verifica se a organização do código reflete a proposta científica.

## 3.2 Conformidade protocolar

Verifica:

- E2AP;
- E2SM-KPM;
- E2SM-RC;
- RMR;
- Subscription Manager;
- RAN Function Discovery;
- ACK/Failure;
- modo `oran-strict`.

## 3.3 Conformidade experimental

Verifica:

- fonte dos dados;
- manifests;
- SHA-256;
- seeds;
- raw evidence;
- PCAP;
- logs;
- artefatos intermediários;
- causalidade.

## 3.4 Conformidade científica

Verifica se cada claim pode ser mapeada para:

```text
claim
→ métrica
→ cenário
→ baseline
→ seeds
→ raw evidence
→ análise
→ figura/tabela
```

---

# 4. TAXONOMIA DE MATURIDADE USADA

```text
DESIGNED
→ IMPLEMENTED
→ UNIT_VALIDATED
→ LOCALLY_INTEGRATED
→ EXTERNAL_INTEROP
→ CLOSED_LOOP_VALIDATED
→ SCIENTIFICALLY_VALIDATED
→ INDEPENDENTLY_REPRODUCED
```

Níveis operacionais:

```text
L0 — Generated
L1 — Unit
L2 — Codec
L3 — Local Integration
L4 — External E2 Interoperability
L5 — Closed Loop
L6 — Multi-seed Scientific Validation
```

Apenas L4+ sustenta claim de interoperabilidade externa.

Apenas L5 sustenta claim de closed loop.

Apenas L6 sustenta comparação estatística robusta.

---

# PARTE I — FASE 1 / H-RDL

# 5. OBJETIVO CIENTÍFICO DA F1

A F1 deve responder essencialmente:

> É possível governar conflitos entre múltiplas xApps de maneira determinística, auditável, segura e interoperável com Near-RT RIC?

A contribuição forte da F1 não é IA.

É:

```text
governança determinística
+ safety
+ rastreabilidade
+ integração E2
+ estabilidade
+ reprodutibilidade
```

Isso é suficiente para uma publicação forte se o closed loop for demonstrado de forma correta.

---

# 6. ARQUITETURA F1

A arquitetura conceitual é sólida:

```text
xApps concorrentes
→ RDL_ACTION_PROPOSAL
→ Decision Window
→ PerceptionAgent
→ Conflict Detection
→ ReasoningAgent
→ RefinementAgent / Safety
→ RDLDecision
→ Backend
→ E2SM-RC
```

Os papéis são suficientemente separados.

## 6.1 PerceptionAgent

Responsável por:

- KPM;
- estado observado;
- registro de xApps;
- conflito direto;
- conflito indireto;
- agregação de propostas.

Avaliação:

```text
IMPLEMENTED / LOCALLY_INTEGRATED
```

## 6.2 ReasoningAgent

Responsável por arbitragem determinística.

O principal valor científico aqui é previsibilidade e explicabilidade.

Avaliação:

```text
IMPLEMENTED / UNIT-LOCAL VALIDATED
```

## 6.3 RefinementAgent

Camada mais importante para safety.

Deve garantir que nenhuma decisão — inclusive futura decisão aprendida da F2 — ultrapasse restrições físicas e políticas.

Avaliação:

```text
forte arquiteturalmente
```

---

# 7. DECISION WINDOW

A janela de decisão de 200 ms é um elemento estrutural importante.

Ela permite:

- agrupar propostas concorrentes;
- detectar conflitos simultâneos;
- evitar arbitragem puramente FIFO;
- tornar a comparação B0/B1/B2/B3 consistente.

A janela deve aparecer explicitamente no manifesto experimental.

Exemplo:

```yaml
decision_window_ms: 200
```

---

# 8. TIPOS DE CONFLITO F1

A F1 é adequada para estudar:

```text
direto:
  duas xApps controlam o mesmo parâmetro

indireto:
  parâmetros diferentes afetam o mesmo KPI/SLA

temporal:
  decisões alternantes produzem instabilidade

resource contention:
  soma de demandas excede capacidade

safety:
  ação individualmente válida gera estado coletivo inseguro
```

O conflito indireto é particularmente relevante como ponte para a F2.

---

# 9. CENÁRIOS CANÔNICOS F1

Recomenda-se congelar a F1 em:

```text
S0 — no conflict
S1 — direct PRB conflict
S2 — energy vs QoS
S3 — TVS multi-slice
S4 — traffic steering vs energy
S5 — temporal ping-pong
S6 — conflict storm
S7 — fault injection
S8 — closed loop NORI
```

A F1 não deve incorporar S9–S15.

---

# 10. BASELINES F1

```text
B0 — no coordination
B1 — FIFO
B2 — static priority/rule
B3 — H-RDL
```

Esse conjunto é cientificamente defensável.

---

# 11. CAMADA E2 F1

O projeto evoluiu significativamente ao longo das auditorias.

Foram identificados componentes de:

- E2AP;
- KPM;
- RC;
- Subscription;
- ACK;
- Failure;
- mapper;
- capability registry.

Entretanto, existência de classes não prova interoperabilidade.

---

# 12. E2AP

O perfil congelado da F1 deve continuar sendo:

```text
O-RAN SC Release J
E2AP v02.03
E2SM-KPM v03.00
E2SM-RC v01.03
```

A vantagem disso é reprodutibilidade.

Migrar agora para outra release enfraqueceria o experimento porque mudaria simultaneamente:

```text
algoritmo
+
protocolo
+
service model
+
infraestrutura
```

---

# 13. KPM F1

KPM só pode ser considerado externo quando a cadeia observada for:

```text
E2 Node
→ RIC Indication
→ E2Term
→ RMR
→ xApp
→ APER decode
→ KPMReport
```

Testes de codec são L2.

KPM gerado localmente é no máximo L3.

KPM recebido do E2Term com raw/PCAP é L4.

---

# 14. RC F1

A cadeia correta:

```text
RDLDecision
→ selected action
→ RCMapper
→ ControlHeader
→ ControlMessage
→ RICcontrolRequest
→ E2Term
→ E2 Node
```

Ponto crítico:

`TX_POWER`, `HANDOVER` ou `PRB_QUOTA` só podem ser enviados se a capacidade correspondente tiver sido realmente descoberta ou definida pelo perfil testado.

---

# 15. RAN FUNCTION DISCOVERY

Este continua sendo um dos maiores blockers da F1.

Não basta:

```python
ran_fn_id = 3
```

ou:

```python
ran_fn_id = 2
```

O fluxo científico correto é:

```text
E2 Setup
→ RANFunctionDefinition
→ decode
→ CapabilityRegistry
→ KPM ranFunctionID
→ RC ranFunctionID
```

Em DEV/OFFLINE, IDs fixos são aceitáveis.

Em `oran-strict`, não.

---

# 16. ACTION IDENTITY E CAUSALIDADE F1

A arquitetura deve preservar:

```text
causal_event_id
decision_id
action_id
RICrequestID
```

A cadeia mínima deve ser:

```text
decision_id
→ action_id
→ requestor_id
→ instance_id
```

O motivo é simples:

uma única decisão pode conter múltiplas ações.

Sem `action_id`, a causalidade fica ambígua.

---

# 17. CHAVE DE CORRELAÇÃO EXTERNA

Recomendação definitiva:

```text
(node_id, ran_function_id, requestor_id, instance_id)
```

Não usar apenas:

```text
transaction_id
```

como identidade principal.

---

# 18. ACK E FAILURE F1

Estados canônicos:

```text
ACK_RECEIVED
FAILURE_RECEIVED
MALFORMED_RESPONSE
TIMEOUT
CORRELATION_ERROR
```

O projeto deve possuir testes para todos.

---

# 19. ORAN-STRICT F1

Em strict:

```text
MockRMR              -> proibido
fake SDL             -> proibido
MemoryModule fallback-> proibido
JSON ACK fallback    -> proibido
static capability    -> proibido
silent fallback      -> proibido
```

Se uma dependência externa não estiver disponível:

```text
FAIL EXPLICITLY
```

Isso é importante para impedir “experimentos O-RAN” que na prática rodam em mock.

---

# 20. BACKEND ABSTRACTION F1

Interface esperada:

```text
connect()
discover_capabilities()
create_kpm_subscription()
decode_kpm()
encode_control()
send_control()
decode_control_response()
collect_evidence()
```

Backends:

```text
NORI_NS3
SRSRAN_OPEN5GS
OPENRANBR_PHYSICAL
```

Esta abstração é um ponto forte.

Ela permite comparar:

```text
algoritmo constante
backend variável
```

---

# 21. NS-3 / NORI F1

Perfil conhecido:

```text
ns-3.48
5G-LENA v5.1
NORI commit 9b64c12
```

No ns-3:

```text
NrPointToPointEpcHelper
```

Não chamar isso de Free5GC/Open5GS.

Open5GS pertence ao testbed srsRAN separado.

---

# 22. CI F1

Último estado autenticado:

```text
HEAD f154728...
GitHub Actions: FAILURE
primeiro ponto relevante: Syntax & Smoke Import Check
```

A hipótese de causa mais forte foi:

```text
ricxappframe instalado
+
biblioteca nativa RMR ausente
→ import pode lançar OSError/loader error
```

Isso foi uma **hipótese de causa provável**, não traceback confirmado.

Correções recomendadas:

```text
instalar rmr/rmr-dev no CI
ou
capturar ImportError/OSError apenas para modo local
```

sem enfraquecer strict.

---

# 23. STATUS DOCUMENTAL F1

Se `STATUS.md` afirma:

```text
58/58 PASS
G2 PASS
zero-synthetic 100%
```

e o HEAD está vermelho:

a classificação correta é:

```text
STALE DOCUMENTATION
```

Regra:

```text
CI do HEAD > STATUS.md
```

---

# 24. PROVENIÊNCIA F1

Ponto positivo:

a F1 já possui conceito de scientific compliance.

Problemas detectados:

1. validação permissiva por flags de manifesto;
2. procura do primeiro manifest;
3. validação por extensão;
4. ausência de fechamento SHA de todos os artefatos;
5. árvore raw não demonstrada de forma suficiente.

---

# 25. PROBLEMA DO PRIMEIRO MANIFESTO

Um validador científico não pode fazer:

```text
find first execution_manifest.json
→ validate
→ whole campaign PASS
```

Deve fazer:

```text
for run in campaign:
    validate(run)
```

---

# 26. GATE 1 F1

G1 exige:

```text
E2 Setup Request.raw
E2 Setup Response.raw
RANFunctionDefinition.raw
KPM Subscription Request
KPM Subscription Response.raw
RIC Indication.raw
Decoded KPM
e2.pcap
e2term.log
execution_manifest.json
hashes.sha256
semantic_validation.json
```

Manifest boolean não substitui raw.

---

# 27. GATE 2 F1

G2 representa o core H-RDL.

Último julgamento:

```text
PREVIOUSLY VALIDATED / CURRENT HEAD UNVERIFIED
```

por causa da CI vermelha.

---

# 28. GATE 3 F1

G3 exige:

```text
valid RC
→ external ACK

invalid RC
→ external Failure
```

Sem isso:

```text
PENDING
```

---

# 29. GATE 4 F1

Este é o gate decisivo.

Bundle mínimo:

```text
KPM(t0)
→ proposals
→ conflict
→ decision
→ safety
→ RC
→ ACK
→ state change
→ KPM(t1)
```

Artefatos:

```text
pcap/
logs/
raw/
decoded/
decisions.jsonl
conflicts.jsonl
causal.jsonl
manifest
hashes
```

---

# 30. G5 F1

Campanha final:

```text
9 cenários × 4 baselines × 30 seeds = 1080 runs
```

Não executar antes de G4.

---

# 31. ESTATÍSTICA F1

Por métrica:

```text
mean
median
SD
P95
P99
95% CI
effect size
```

Comparação pareada:

```text
mesma seed
mesma topologia
mesmo tráfego
mesmo canal
mesma mobilidade
```

Testes:

```text
Wilcoxon paired
ou paramétrico justificado
Holm correction
```

---

# 32. RESULTADOS F1 — O QUE PODE SER AFIRMADO

Existem artefatos históricos de simulação e relatórios.

O histórico público anterior mostrou arquivos como:

```text
dataset_flow_metrics.csv
dataset_rdl_decisions_ml.csv
relatorio_comparativo.md
relatorio_comparativo_detalhado.md
figuras
FlowMonitor
```

Entretanto, houve posteriormente:

- limpeza de artefatos antigos;
- mudança da política de proveniência;
- ausência, na auditoria autenticada recente, de uma árvore raw completa aceita como G1/G4.

Consequência:

> os resultados históricos são úteis como material exploratório e de engenharia, mas não devem ser promovidos automaticamente a “resultado científico final F1”.

---

# 33. VEREDITO F1

```text
Arquitetura:        FORTE
Core determinístico:FORTE
Safety:             FORTE
Protocolo local:    BOM
External E2:        PENDENTE
Closed loop:        PENDENTE
Campanha final:     BLOQUEADA
Publicação:         PROMISSORA, MAS AINDA DEPENDENTE DE G1/G3/G4
```

Gates:

| Gate | Status |
|---|---|
| G0 | PARCIAL+ |
| G1 | PENDING |
| G2 | PREVIOUSLY VALIDATED / CURRENT HEAD UNVERIFIED |
| G3 | PENDING |
| G4 | PENDING |
| G5 | BLOCKED |
| G6 | BLOCKED |

---

# PARTE II — FASE 2 / CA-RDL

# 34. OBJETIVO CIENTÍFICO F2

A F2 deve responder:

> Contexto, representação causal/semântica e Safe-MARL melhoram a governança multi-xApp em relação ao H-RDL sem violar safety?

A contribuição deve ser incremental.

Não deve tentar provar tudo de uma vez.

---

# 35. ARQUITETURA F2

A arquitetura desejada:

```text
KPM/context
→ Perception
→ Context Model
→ Conflict Detection
→ Causal Graph / KG
→ Reasoning
→ MAPPO
→ Action Mask
→ Deterministic Safety
→ RDLDecision
→ E2SM-RC
```

---

# 36. PRINCIPAL VANTAGEM F2

A F2 consegue representar conflitos que a F1 determinística pode não perceber facilmente.

Exemplo:

```text
xApp A -> TX_POWER
xApp B -> PRB_QUOTA

TX_POWER -> SINR
PRB_QUOTA -> throughput

SINR + throughput -> SLA
```

Parâmetros diferentes.

Mesmo SLA.

Conflito indireto.

---

# 37. CAUSAL GRAPH F2

A integração do causal graph ao `ReasoningAgent` foi um avanço real.

Classificação recomendada:

```text
Causal Dependency Graph = LOCALLY_INTEGRATED
Semantic KG            = PARTIAL / PENDING
GNN                    = ROADMAP
```

Não chamar causal dependency graph de KG completo sem:

```text
typed schema
persistence
provenance
temporal semantics
query interface
versioning
```

---

# 38. OBSERVATION CONTRACT

A F2 avançou no conceito de observation contract.

Isso é essencial para evitar:

```text
training/inference mismatch
schema drift
feature order drift
unstable hashing
```

O contrato deve definir:

```text
field
unit
range
normalization
TTL
missing-value rule
source
hash
```

---

# 39. ACTION CONTRACT

O espaço de ações deve ser versionado.

Exemplo:

```text
PRB_QUOTA
SCHEDULER_WEIGHT
TX_POWER
HANDOVER
NO_OP
...
```

Cada ação deve ter:

```text
action_id
parameter
value
bounds
capability requirement
safety requirement
backend mapping
```

---

# 40. ACTION MASKING

A inclusão de action masking é uma evolução correta.

Pipeline:

```text
policy logits
→ capability mask
→ safety pre-mask
→ sampled action
→ deterministic RefinementAgent
```

Isso reduz o espaço inválido.

Mas:

```text
action masking != proof of safe operation
```

O Safety Guard final continua obrigatório.

---

# 41. MAPPO F2

O core algorítmico é forte.

Características esperadas:

```text
centralized critic
decentralized actors
multi-agent observation
joint state
PPO clipping
GAE
entropy
value loss
safety cost
```

Classificação:

```text
ALGORITHMICALLY IMPLEMENTED
```

Não:

```text
SCIENTIFICALLY VALIDATED
```

---

# 42. MAPPO SMOKE ENV

O projeto fez algo metodologicamente correto:

```text
environment = MAPPO_SMOKE_ENV
publication_eligible = false
```

Isso deve permanecer.

Treino smoke serve para:

```text
shape validation
gradient validation
checkpoint serialization
optimizer validation
runtime smoke
```

Não serve para paper de desempenho RAN.

---

# 43. TRACE REPLAY

Classificação correta:

```text
OFFLINE_REPLAY_ONLY
NOT_CAUSAL_TRAINING_ENV
```

Porque:

```text
s(t+1) = trace[t+1]
```

e não:

```text
s(t+1) ~ P(. | s(t), a(t))
```

Logo:

```text
ds(t+1)/da(t) = 0
```

em replay congelado.

---

# 44. AMBIENTE CAUSAL NECESSÁRIO

A F2 precisa de:

```text
NoriRanEnvironment
SrsRanEnvironment
```

Fluxo:

```text
obs(t)
→ MAPPO
→ action(t)
→ RC
→ RAN
→ KPM(t+1)
→ reward
→ next observation
```

Sem isso, não há aprendizagem causal de controle RAN.

---

# 45. RDLDECISION PRÉ-DISPATCH F2

A F2 precisa herdar completamente a semântica da F1:

```text
reasoning
→ safety
→ RDLDecision
→ action_id
→ allocator
→ RC
```

Não:

```text
reasoning
→ send_control()
```

diretamente.

---

# 46. ACTION_ID F2

O `XAppAction` precisa ter um identificador persistente.

A cadeia deve ser:

```text
decision_id
→ action_id
→ RICrequestID
```

Isso é ainda mais importante na F2 porque uma política MARL pode produzir múltiplas decisões em pouco tempo.

---

# 47. STRICT MODE F2

Problemas detectados historicamente:

```text
SDL exception -> MemoryModule fallback
ACK fallback enabled in strict
hardcoded node_id
hardcoded ran_fn_id
```

Todos devem ser eliminados em strict.

---

# 48. HELM F2

Problema relevante:

o Helm historicamente não injetava explicitamente:

```text
RDL_MODE
RAN_BACKEND
```

e possuía:

```text
RMR_WAIT_FOR_READY=false
```

Perfil científico correto:

```text
RDL_MODE=O_RAN_INTEROP
RAN_BACKEND=SRSRAN_OPEN5GS
USE_FAKE_SDL=false
RMR_WAIT_FOR_READY=true
REQUIRE_OPERATIONAL_TRANSPORT=true
```

---

# 49. F2 CURRENT PROFILE × FUTURE PROFILE

A F2 possui uma visão futura de versões mais novas.

É válido, desde que separado.

## Current execution

```text
NORI-compatible baseline
srsRAN-compatible profile
```

## Future target

```text
newer E2AP
newer KPM
newer RC
post-J profile
```

Nunca comparar F1 e F2 mudando simultaneamente o algoritmo e o protocolo.

---

# 50. CI F2

Último estado autenticado:

```text
HEAD 3663d165...
CI FAILURE
native RMR PASS
dependencies PASS
smoke import PASS
Pyright FAIL
subsequent stages SKIPPED
```

Isso é importante.

O problema não estava mais no import.

Estava na análise estática.

---

# 51. PYRIGHT F2

Houve um defeito de portabilidade:

```text
venvPath -> caminho Windows local
```

inclusive apontando para F1.

Isso deve ser removido.

Config deve ser:

```text
portable
repo-relative
CI-friendly
```

---

# 52. COVERAGE F2

O workflow verificado exigia:

```text
--cov-fail-under=75
```

enquanto documentação falava em:

```text
>85%
```

Inconsistência.

Regra:

```text
documented threshold == enforced threshold
```

Recomendação:

```text
coverage >= 85%
branch coverage enabled
```

---

# 53. REGRESSÃO DE CI F2

Snapshots públicos históricos indicaram que a F2 passou por:

```text
green
→ many feature commits
→ failures
```

Isso caracteriza:

```text
FeatureVelocity > ValidationVelocity
```

Resposta correta:

```text
FEATURE FREEZE
CI HARDENING
```

---

# 54. PROVENIÊNCIA F2

A política de proveniência não pode ser simplesmente cópia da F1.

Ela deve adicionar ML provenance.

---

# 55. MANIFESTO MAPPO PUBLICÁVEL

Campos mínimos:

```text
git_sha
environment_id
environment_sha
training_seeds
evaluation_seeds
episodes
steps_per_episode
n_agents
obs_dim
action_dim
hyperparameters
pytorch_version
cuda_version
cudnn_version
device
observation_schema_hash
action_schema_hash
reward_definition_hash
actor_checkpoint_sha256
critic_checkpoint_sha256
optimizer_checkpoint_sha256
raw_transition_sources
```

---

# 56. TREINO × EVAL

Obrigatório:

```text
train seeds ∩ eval seeds = ∅
```

A avaliação deve usar seeds não vistas.

---

# 57. SAFETY F2

O MAPPO nunca deve controlar diretamente fora do domínio seguro.

Arquitetura:

```text
MAPPO proposal
→ ActionMask
→ Refinement/Safety
→ RDLDecision
→ RC
```

Fallback:

```text
model timeout
model exception
NaN
out-of-domain state
uncertainty high
→ H-RDL deterministic fallback
```

---

# 58. RESULTADOS F2 — ÚLTIMO ESTADO AUTENTICADO

O snapshot autenticado recente encontrou:

```text
experiments/results/
    .gitkeep
```

e treinos smoke em:

```text
experiments/training/
```

Isso é um dado importante.

Significa que, no estado mais recente efetivamente verificado, não havia um conjunto de resultados publicáveis consolidado na árvore principal.

---

# 59. RESULTADOS PÚBLICOS HISTÓRICOS F2

A página pública em cache mostra historicamente:

```text
dataset_multi_seed_metrics.csv
dataset_flow_metrics.csv
dataset_rdl_decisions_ml.csv
relatorio_estatistico_multi_semente.md
manifest_experiment.json
raw/
plots/
runs/
```

e documentação alegando:

```text
N=30
IC95
ANOVA
p < 0.001
```

Porém essa página é anterior ao snapshot autenticado e conflita com o estado posterior.

Logo:

> não usar esses resultados históricos como evidência atual sem recuperar os raw files e validar a proveniência.

---

# 60. RESULTADO F2 CIENTIFICAMENTE ACEITÁVEL

Para o primeiro paper CA-RDL:

```text
B3 H-RDL
B4 Context
B5 Context+KG
B6 Full MAPPO
```

No mesmo cenário.

Mesmas seeds.

Mesmo backend.

Mesmo transport profile.

---

# 61. ABLATIONS F2

```text
Full
No Context
No KG
No MARL
No Safety
```

`No Safety` apenas offline.

---

# 62. CONVERGÊNCIA MAPPO

Não basta:

```text
reward curve increases
```

Exigir:

```text
multi-seed
mean reward
CI
variance
safety cost
constraint violation
unseen evaluation
policy stability
```

---

# 63. GENERALIZAÇÃO

Após convergência:

```text
train NORI
evaluate frozen policy srsRAN
```

Depois:

```text
OpenRAN@Brasil physical
```

Isso gera um paper forte de generalização.

---

# 64. VEREDITO F2

```text
Arquitetura cognitiva:     FORTE
Context:                    PROMISSOR
Causal graph:               LOCALMENTE INTEGRADO
Semantic KG:                PARCIAL
MAPPO:                      ALGORÍTMICO
Safe-RL:                    BOM DESIGN
Causal training environment:PENDENTE
External E2:                PENDENTE
Scientific results:         NÃO CONFIRMADOS NO HEAD VERIFICADO
```

---

# PARTE III — COMPARAÇÃO F1 × F2

# 65. O QUE PODE SER COMPARADO AGORA

Pode-se comparar com segurança:

```text
arquitetura
complexidade
explicabilidade
safety design
state/action model
reprodutibilidade de software
maturidade da CI
proveniência
nível de evidência
```

Ainda não se deve afirmar cientificamente:

```text
F2 reduz latência X%
F2 aumenta throughput Y%
F2 melhora energia Z%
F2 supera F1 estatisticamente
```

sem campaign bundle validado.

---

# 66. COMPARAÇÃO DE PARADIGMA

| Aspecto | H-RDL | CA-RDL |
|---|---|---|
| Decisão | determinística | adaptativa |
| Explicabilidade | alta | média/alta |
| Dependência de dados | baixa | alta |
| Segurança | explícita | explícita + aprendizado restrito |
| Reprodutibilidade | mais simples | mais complexa |
| Generalização | limitada | potencialmente alta |
| Custo de validação | menor | muito maior |
| Risco científico | menor | maior |
| Potencial de contribuição | alto | muito alto |

---

# 67. COMPLEXIDADE

F1:

```text
rules
utilities
safety
```

F2:

```text
context
graph
state encoding
policy
critic
training
checkpoints
safety
```

A F2 precisa provar que o ganho justifica essa complexidade.

---

# 68. EXPLICABILIDADE

F1 possui vantagem natural.

Uma decisão pode ser explicada por:

```text
conflict
→ priority/utility
→ safety
→ selected action
```

F2 precisa produzir:

```text
state
context
graph evidence
policy output
mask
safety result
selected action
```

---

# 69. LATÊNCIA

Não misturar:

```text
T_decision
T_encode
T_dispatch
T_control
T_ack
T_loop
```

A F2 pode aumentar `T_decision`, mas ainda melhorar o resultado global.

---

# 70. MÉTRICAS PRIMÁRIAS PARA COMPARAÇÃO

```text
URLLC latency
SLA violation rate
aggregate throughput
packet loss
Jain fairness
energy efficiency
conflict resolution rate
unsafe action rate
decision latency
closed-loop latency
ping-pong
control failure rate
```

---

# 71. MÉTRICAS ESPECÍFICAS F2

```text
reward
cost
constraint violation
policy entropy
KL divergence
critic loss
actor loss
episode return
generalization gap
contextual advantage
indirect-conflict recall
```

---

# 72. MÉTRICA MAIS IMPORTANTE

Para a narrativa científica:

```text
utility improvement under zero/near-zero safety violations
```

Ou:

```text
F2 improves utility while preserving F1 safety envelope.
```

---

# 73. EXPERIMENTO PAREADO IDEAL

```text
seed_i
topology_i
traffic_i
channel_i
mobility_i
xApp proposals_i
```

executados com:

```text
B3
B4
B5
B6
```

---

# 74. HIPÓTESE PRINCIPAL

```text
H0:
CA-RDL does not improve system utility over H-RDL.

H1:
CA-RDL improves utility while maintaining safety constraints.
```

---

# 75. HIPÓTESES SECUNDÁRIAS

```text
H2:
Context improves indirect-conflict detection.

H3:
KG improves decisions in semantically coupled conflicts.

H4:
MAPPO improves long-horizon utility relative to deterministic arbitration.

H5:
Safety layer prevents policy-induced unsafe controls.

H6:
Policy generalizes across backends.
```

---

# 76. POR QUE A COMPARAÇÃO ATUAL AINDA É INCOMPLETA

Porque os dois projetos ainda não compartilham uma evidência externa fechada equivalente.

Uma comparação válida exige:

```text
same scenario
same raw workload
same backend
same protocol profile
same seed
same metrics
```

---

# 77. RESULTADOS HISTÓRICOS NÃO SÃO SUFICIENTES

A existência de:

```text
CSV
PNG
Markdown report
JSON aggregate
```

não prova que o dado veio de uma execução externa válida.

Precisamos da cadeia:

```text
raw source
→ manifest
→ hash
→ parser
→ dataset
→ statistic
→ plot
```

---

# 78. CLAIMS FIREWALL

Arquivo:

```yaml
claims:
  - id: C1
    text: "H-RDL reduces SLA violations versus FIFO"
    metric: sla_violation_rate
    scenario: S3
    baselines: [B1, B3]
    seeds: 30
    raw:
      - ...
    table: T2
    figure: F4
```

Sem mapping:

```text
NO CLAIM
```

---

# PARTE IV — RISCOS

# 79. MATRIZ DE RISCO

| Risco | F1 | F2 | Impacto |
|---|---|---|---|
| CI vermelha | alto | alto | bloqueia confiança |
| hardcoded ranFunctionID | alto | alto | interoperabilidade |
| capability discovery incompleto | alto | alto | O-RAN |
| fallback em strict | médio | alto | invalida experimento |
| ACK sem correlação causal | médio | alto | G3/G4 |
| ausência action_id | médio | alto | causalidade |
| proveniência fraca | alto | crítico | paper |
| smoke tratado como ciência | baixo | crítico | F2 |
| replay tratado como causal | baixo | crítico | F2 |
| documentação overclaim | médio | alto | revisão |
| feature velocity alta | baixo | alto | regressão |
| mixed protocol profile | baixo | alto | confounding |

---

# 80. RISCO DE OVERCLAIM

Expressões perigosas:

```text
operacional
em produção
fim-a-fim
100% O-RAN
validated
scientific
```

Só usar se houver evidência adequada.

---

# 81. RISCO DE SALAMI SLICING

Evitar transformar cada pequena feature em paper separado.

Narrativa recomendada:

```text
Paper 1 — H-RDL
Paper 2 — standards/cross-backend
Paper 3 — CA-RDL Context+KG
Paper 4 — Safe MAPPO
Journal — full architecture
```

---

# PARTE V — PRONTIDÃO DE PUBLICAÇÃO

# 82. F1

## Para workshop/conferência nacional

Pode ficar pronta relativamente rápido se fechar:

```text
G1
G3
G4
pilot
30 seeds
```

## Para TNSM

Exigir:

```text
full campaign
cross-backend
scalability
ablation
artifact package
```

---

# 83. F2

Para paper nacional:

```text
Context + KG
vs H-RDL
```

pode ser suficiente antes do MAPPO completo.

Para MAPPO paper:

```text
causal environment
multi-seed
ablation
safety
generalization
```

---

# 84. VENUES

Possíveis:

```text
SBRC
WGRS
SBrT
CNSM
NOMS
IM
ICC
GLOBECOM
IEEE TNSM
IEEE TCCN
Computer Networks
```

---

# 85. NARRATIVA DE DISSERTAÇÃO

A dissertação pode ser organizada como:

```text
Cap. 1 — problema multi-xApp
Cap. 2 — O-RAN
Cap. 3 — H-RDL
Cap. 4 — validação F1
Cap. 5 — limitação determinística
Cap. 6 — CA-RDL
Cap. 7 — Context/KG
Cap. 8 — Safe MARL
Cap. 9 — comparação experimental
Cap.10 — generalização e 6G
```

---

# PARTE VI — ROADMAP OPERACIONAL

# 86. P0 — BLOQUEADORES

## F1

```text
P0.1 CI verde
P0.2 action_id
P0.3 real capability discovery
P0.4 real KPM subscription
P0.5 external ACK/Failure
P0.6 G4 golden closed loop
```

## F2

```text
P0.1 CI/Pyright
P0.2 coverage alignment
P0.3 strict fail-closed
P0.4 Helm profile
P0.5 RDLDecision pre-dispatch
P0.6 action_id
P0.7 ML provenance
```

---

# 87. P1

F1:

```text
pilot 5 seeds
campaign 30 seeds
claims.yaml
artifact bundle
```

F2:

```text
NoriRanEnvironment
Context+KG experiment
unseen evaluation
Safe-MAPPO training
```

---

# 88. P2

```text
cross-backend
srsRAN/Open5GS
OpenRAN@Brasil
physical testbed
scalability
international paper
```

---

# 89. O QUE NÃO FAZER AGORA

Não:

```text
GNN
federation
NTN
UAV
ISAC
SAGIN
LLM
novos agentes
novos cenários
```

antes de fechar a base.

---

# PARTE VII — BUNDLE CIENTÍFICO IDEAL

# 90. ESTRUTURA POR RUN

```text
run_x/
├── execution_manifest.json
├── hashes.sha256
├── config/
├── raw/
│   ├── e2_setup_request.raw
│   ├── e2_setup_response.raw
│   ├── ran_function_definition.raw
│   ├── subscription_request.raw
│   ├── subscription_response.raw
│   ├── kpm_indication_t0.raw
│   ├── ric_control_request.raw
│   ├── ric_control_response.raw
│   └── kpm_indication_t1.raw
├── decoded/
├── logs/
├── pcap/
├── decisions/
├── metrics/
└── analysis/
```

---

# 91. MANIFEST

```json
{
  "git_sha": "...",
  "backend": "NORI_NS3",
  "seed": 1001,
  "scenario": "S1",
  "baseline": "B3",
  "protocol_profile": "F1_RELEASE_J",
  "container_digest": "...",
  "ns3_sha256": "...",
  "scenario_sha256": "...",
  "config_sha256": "..."
}
```

---

# 92. TRANSAÇÃO

```json
{
  "causal_event_id": "...",
  "decision_id": "...",
  "action_id": "...",
  "node_id": "...",
  "ran_function_id": 3,
  "requestor_id": 123,
  "instance_id": 7,
  "parameter": "PRB_QUOTA",
  "old_value": 40,
  "new_value": 60,
  "t_send": 0.0,
  "t_ack": 0.0
}
```

---

# PARTE VIII — CI RECOMENDADA

# 93. F1 CI SOFTWARE

```text
checkout
Python
native RMR
install
compileall
smoke import
codec
unit
negative
integration
interoperability
zero-synthetic
Docker
```

---

# 94. F1 CI SCIENCE

Separada:

```text
provenance
Gate1
Gate3
Gate4 artifact validation
hash validation
claims mapping
```

---

# 95. F2 CI SOFTWARE

```text
native RMR
compileall
Pyright
pytest
coverage >=85
branch coverage
zero-synthetic
Docker
```

---

# 96. F2 CI SCIENCE

```text
network provenance
ML provenance
checkpoint hashes
train/eval split
reward hash
obs/action schema hash
external artifacts
```

---

# PARTE IX — COMPARAÇÃO FINAL

# 97. QUEM ESTÁ MAIS MADURO?

Hoje:

```text
F1 > F2 em maturidade experimental
```

---

# 98. QUEM TEM MAIOR POTENCIAL?

```text
F2 > F1 em potencial de novidade
```

---

# 99. QUEM DEVE SER PUBLICADO PRIMEIRO?

```text
F1
```

Porque:

```text
menor espaço de hipótese
menor número de variáveis
mais explicável
mais fácil de reproduzir
mais fácil de defender
```

---

# 100. QUAL DEVE SER A BASE DA F2?

```text
H-RDL frozen baseline
```

Não recriar uma base paralela.

---

# 101. VEREDITO FINAL

## F1

```text
GO:
  external integration
  G1
  G3
  G4
  scientific campaign after G4

NO-GO:
  new features
  new scenarios
  final publication claim before external evidence
```

## F2

```text
GO:
  CI hardening
  strict
  provenance
  causal MARL environment
  Context/KG validation

NO-GO:
  production claim
  MARL scientific superiority claim
  GNN/6G expansion before foundation
```

---

# 102. CONCLUSÃO GERAL

A família RDL já possui arquitetura suficiente para produzir pesquisa de alto nível.

O gargalo agora não é criatividade arquitetural.

É:

```text
evidência
causalidade
interoperabilidade
reprodutibilidade
estatística
```

A F1 precisa transformar um protótipo local forte em um **closed loop O-RAN demonstrado**.

A F2 precisa transformar uma arquitetura cognitiva forte em um **sistema de controle causal treinável e comparável**.

A sequência correta é:

```text
H-RDL deterministic governance
→ external E2 validation
→ causal closed loop
→ multi-seed publication
→ Context/KG
→ Safe-MAPPO
→ cross-backend generalization
→ physical testbed
→ 5G-A/6G extension
```

O maior risco atual seria continuar aumentando o número de funcionalidades antes de fechar as provas científicas fundamentais.

O maior ganho científico possível agora é produzir **um único run S1 perfeitamente rastreável**, seguido de um segundo run equivalente em F2.

Quando esses dois bundles existirem, a comparação F1 × F2 deixa de ser uma comparação arquitetural e passa a ser uma comparação experimental cientificamente defensável.

---

# 103. REFERÊNCIAS DE EVIDÊNCIA USADAS NESTA AUDITORIA

## Repositórios

- https://github.com/georgebarbosa3090/XApp-RDL-F1
- https://github.com/georgebarbosa3090/XApp-RDL-F2

## Actions F2 — snapshot público histórico

- https://github.com/georgebarbosa3090/XApp-RDL-F2/actions

## Histórico de commits

- https://github.com/georgebarbosa3090/XApp-RDL-F1/commits/main/
- https://github.com/georgebarbosa3090/XApp-RDL-F2/commits/main/

## Resultados históricos

- https://github.com/georgebarbosa3090/XApp-RDL-F1/tree/main/experiments/results
- https://github.com/georgebarbosa3090/XApp-RDL-F2/tree/main/experiments/results

---

# 104. NOTA FINAL DE AUDITORIA

Este relatório separa deliberadamente:

```text
existência de código
existência de testes
integração local
interoperabilidade
closed loop
resultado científico
```

Essa separação deve ser preservada em README, STATUS, paper, dissertação e apresentações.

Critério final de maturidade:

> O projeto estará pronto quando código, CI, protocolo, raw evidence, estatística e documentação contarem exatamente a mesma história.
