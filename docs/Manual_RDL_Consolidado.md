# DocumentaÃ§Ã£o Oficial: Projeto xApp RDL (Resource and Decision Layer)

**VersÃ£o:** 1.1.0 (Zero to Hero Refactoring)
**Data:** 05/08/2026

---

## 1. IntroduÃ§Ã£o e Metodologia

Na arquitetura **O-RAN (Open Radio Access Network)**, as xApps (aplicaÃ§Ãµes do Near-RT RIC) operam de forma isolada e simultÃ¢nea para gerenciar os nÃ³s de rÃ¡dio. O problema intrÃ­nseco dessa arquitetura Ã© o **Conflito de Controle**. O que acontece se uma `QoS-xApp` decide aumentar a potÃªncia e os recursos de rÃ¡dio de uma cÃ©lula simultaneamente a uma `Energy-Savings-xApp` que decide diminuÃ­-los? A antena receberÃ¡ requisiÃ§Ãµes contraditÃ³rias (`RIC_CONTROL_REQUEST`), resultando em oscilaÃ§Ã£o agressiva (*ping-pong effect*) e degradaÃ§Ã£o de SLAs.

A **xApp RDL (Resource and Decision Layer)** surge como uma camada de OrquestraÃ§Ã£o Cognitiva (via RDP) que se posiciona de forma agnÃ³stica como um Ã¡rbitro entre o Near-RT RIC e as demais xApps. A metodologia adota **Domain-Driven Design (DDD)** para separar a lÃ³gica de decisÃ£o da infraestrutura de telecomunicaÃ§Ãµes.

Na RDL:
1. As xApps parceiras nÃ£o ativam comandos, apenas disparam intenÃ§Ãµes (`RDL_ACTION_PROPOSAL`) na rede RMR.
2. A **RDL intercepta as propostas e as agrupa em uma Janela de DecisÃ£o (Decision Window de 200ms)**, abandonando o modelo reativo de primeiro a chegar (First-Come-First-Served).
3. A IA funde os pedidos das xApps com a telemetria em tempo real (KPM) e **avalia o espaÃ§o combinatÃ³rio das aÃ§Ãµes** para detectar oportunidades de complementaridade (executar mÃºltiplas aÃ§Ãµes simultaneamente se aumentarem a utilidade global).
4. A RDL decide utilizando **fÃ³rmulas de Acordo de NÃ­vel de ServiÃ§o (SLA) â€” como TVS e EEVS â€” ou InteligÃªncia Artificial (MARL)**, valida regras fÃ­sicas rÃ­gidas (Safety Guard) e despacha o comando final oficial (`E2SM-RC`).

---

## 2. Arquitetura Geral

A RDL atua como um Man-in-the-middle inteligente em **Ciclo Fechado**:

1. **Coleta (E2):** O `E2NodeDiscoveryService` localiza as antenas. O `SubscriptionManager` assina as mÃ©tricas (E2SM-KPM). O payload ASN.1 APER Ã© decodificado (`e2ap_decoder` e `kpm_decoder`).
2. **Proposta e Agrupamento Temporal:** InterceptaÃ§Ã£o de `RDL_ACTION_PROPOSAL` da malha RMR, acumulando-as em um buffer atÃ© o fechamento da janela de 200ms.
3. **Arbitragem (DomÃ­nio/Agentes):** O `PerceptionAgent` gera o grafo situacional do lote inteiro. O `ReasoningAgent` escolhe a melhor resoluÃ§Ã£o iterando as combinaÃ§Ãµes e avaliando a utilidade com base em polÃ­ticas rigorosas de SLA (como **TVS - Throughput Violation-based Selection** e **EEVS - EE Violation-based Selection**), HistÃ³rico ou IA (MAPPO).
4. **Guarda de SeguranÃ§a:** O `RefinementAgent` valida restriÃ§Ãµes (limite percentual de blocos fÃ­sicos, frequÃªncia de controle).
5. **AtuaÃ§Ã£o (E2/RMR):** O comando Ã© formatado pelo `rc_encoder` e atirado Ã  rÃ¡dio base pelo `ControlDispatcher`. O ID da decisÃ£o Ã© salvo no banco de dados distribuÃ­do (SDL) via `sdl_repository` para esperar a confirmaÃ§Ã£o (ACK).

---

## 3. Estrutura do Projeto e Componentes

A estrutura obedece aos padrÃµes Clean Architecture:

* `configs/`: Schema de configuraÃ§Ã£o (`xapp_descriptor.json`, `schema.json`, `routes.rt.template`).
* `deploy/kubernetes/`: Manifestos O-RAN compliant para a xApp (Deployment, Service).
* `docker/`: Dockerfile Multi-stage build com usuÃ¡rio restrito `xapp`.
* `scripts/`: InjeÃ§Ã£o de variÃ¡veis RMR e coleta automÃ¡tica de evidÃªncias de experimentaÃ§Ã£o.
* `src/agents/`: Motores de percepÃ§Ã£o (Grafos), inteligÃªncia artificial MARL (MAPPO) e *Safety Guards*.
* `src/coordination/`: Despachantes (`control_dispatcher`) para gerir o handshake O-RAN (Request, Ack, Failure).
* `src/domain/`: `dataclasses` restritas que garantem a integridade das Entidades (Proposals, Decisions, Conflicts).
* `src/e2/`: Decodificadores e codificadores de carga Ãºtil especÃ­fica E2AP, E2SM-KPM e E2SM-RC.
* `src/infrastructure/`: Portas e Adaptadores, gerindo comunicaÃ§Ã£o com SDL (Redis), Subscription Manager e API E2 Manager.
* `src/observability/`: MÃ©tricas precisas em Prometheus (`rdl_kpm_indications_total`), servidor Uvicorn de Health e Logging Estruturado (JSON).

---

## 4. O Schema (RDL Action Proposal)

Para que xApps parceiras comuniquem-se com a RDL, o modelo JSON estrito (protocolado no DomÃ­nio) exige:

```json
{
  "schema_version": "1.0",
  "proposal_id": "uuid",
  "source_xapp": "qos_app_1",
  "timestamp": "2026-08-05T12:00:00Z",
  "valid_until": "2026-08-05T12:00:01Z",
  "target": {
    "node_id": "gnb_1",
    "cell_id": "cell_alpha",
    "ue_ids": [],
    "slice_ids": []
  },
  "action": {
    "type": "PRB_ALLOCATION",
    "parameters": {"prb_value": 40}
  },
  "priority": 100
}
```

---

## 5. Modelo de Funcionamento da InteligÃªncia (MARL)

A espinha dorsal cognitiva (`agents/marl/`) utiliza **Multi-Agent Proximal Policy Optimization (MAPPO)**. Quando ocorre um Conflito Indireto (xApps controlando parÃ¢metros diferentes que destroem o mesmo SLA em cadeia), o Reasoning Agent descarta regras estÃ¡ticas (Prioridade) e aciona a rede neural via PyTorch. A IA aprende, iterativamente, as consequÃªncias nÃ£o-lineares da RÃ¡dio FrequÃªncia para recomendar a intenÃ§Ã£o que mantÃ©m o EquilÃ­brio de Nash.

---

## 6. ConclusÃ£o

A reconstruÃ§Ã£o arquitetural sob o formato "Zero to Hero" garantiu que o projeto RDL evoluÃ­sse de uma pesquisa monolÃ­tica (Proof-of-Concept em laboratÃ³rio) para uma xApp determinÃ­stica, distribuÃ­da, e escalÃ¡vel (Production-Ready). AtravÃ©s da isolaÃ§Ã£o do domÃ­nio cognitivo em detrimento da casca de comunicaÃ§Ã£o E2, o empacotamento Multi-stage Non-root nativamente endossado pelas especificaÃ§Ãµes OSC Near-RT RIC foi alcanÃ§ado sem comprometer o nÃºcleo matemÃ¡tico de InteligÃªncia Artificial para resoluÃ§Ã£o de conflitos na RAN 5G e 6G.

