# Arquitetura Geral da RDL

A **xApp RDL** é construída em **Python** e utiliza Domain-Driven Design (DDD). Isso significa que separamos "como pensamos na solução de conflito" (Domínio e Agentes) de "como falamos com a rede" (Infraestrutura e E2).

## Visão Macro

A xApp atua como um Orquestrador (Man-in-the-middle).
1. **Ouvir a Rede (Infraestrutura e E2):** O E2NodeDiscoveryService localiza as antenas. O SubscriptionManager assina as métricas da estação rádio-base (srsRAN gNB). As mensagens chegam via protocolo **E2SM-KPM**.
2. **Ouvir as outras xApps (Coordenação):** Interceptamos intenções de mudança (RDL_ACTION_PROPOSAL) na rede RMR através de uma Decision Window (janela de tempo de agrupamento de 200 ms).
3. **Pensar (Agentes e Domínio):** O PerceptionAgent identifica os nós e conflitos (diretos ou indiretos). O ReasoningAgent escolhe a melhor ação combinada utilizando uma Heurística Determinística Multiobjetivo (TVS/EEVS). O RefinementAgent age como *Safety Guard*.
4. **Agir (E2 e Coordenação):** A ação escolhida é adaptada para E2SM-RC pelo c_encoder.py e enviada pelo ControlDispatcher.

---

## O Ciclo Fechado (Closed Loop)
Um "Ciclo Fechado" O-RAN funciona de forma contínua:

1. **RIC_INDICATION (Coleta):**
   - O payload (ASN.1 APER) chega do Near-RT RIC.
   - O e2ap_decoder.py abre o envelope. O kpm_decoder.py traduz em medições (KpmMeasurement).
   
2. **RDL_ACTION_PROPOSAL (Proposta):**
   - Múltiplas xApps parceiras enviam propostas.
   - Geramos um ConflictEvent agrupando ações da janela de 200ms.

3. **Resolução e Validação:**
   - A Heurística de Resolução calcula os pesos SLA, Energy, Priority, etc.
   - A decisão passa pelo crivo dos limites físicos e anti-ping-pong do RefinementAgent.

4. **RIC_CONTROL_REQUEST (Atuação):**
   - Enviamos e esperamos o RIC_CONTROL_ACK do E2 Node.
   - O sucesso (ou a RIC_CONTROL_FAILURE) são correlacionados e persistidos via SDL (sdl_repository.py).

---

## Persistência e Memória (SDL)
O Near-RT RIC exige que xApps sejam "Stateless". Por isso, o módulo sdl_repository.py escreve os IDs das decisões, propostas, subscrições e estado dos nós diretamente no banco compartilhado Redis O-RAN. Esse histórico é fundamental para otimizar as heurísticas baseadas em KNN no futuro.

## Métricas e Observabilidade
Tudo é monitorado. O health_server.py diz ao Kubernetes que o contêiner está UP. O metrics.py varre as operações e incrementa contadores Prometheus sob as nomenclaturas exatas padronizadas pela O-RAN (ex: dl_control_requests_total).
