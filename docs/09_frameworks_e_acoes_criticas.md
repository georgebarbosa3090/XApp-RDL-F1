# 09 — Frameworks avaliados e ações críticas fora da janela de 200 ms

Avaliação feita em 2026-11-10 para o projeto GreenRAN (testbed UFPA). Para cada framework: o que oferece, o que acrescentaria à RDL e o custo de adoção nesta bancada (host com 7,7 GB de RAM; WSL com 5 GB).

## 1. Frameworks e ferramentas

| Framework | O que é | O que acrescentaria | Custo / risco | Recomendação |
| :-- | :-- | :-- | :-- | :-- |
| **O-RAN SC Non-RT RIC — A1 Policy Management Service** ([docs](https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric-plt-a1policymanagementservice/en/latest/developer-guide.html)) | NBI REST para políticas A1 em todos os Near-RT RICs; charts Helm em `it/dep` (`nonrtric/helm/policymanagementservice`) | o caminho O-RAN real para o rApp-ResourceOptimizer chegar à RDL (A1-PMS → A1 Mediator → RMR 20010) | um serviço Java no k3s; cabe na bancada | **adotar** (doc 10) |
| **SMO completo (ONAP + O-RAN SC)** | orquestração, O1/O2, inventário, rApps, AI/ML workflow | fidelidade ao GreenRAN (Rede-5G-Green com SMO) | dezenas de GB de RAM; só no testbed | **documentar passo a passo** para o testbed (doc 10 §4) |
| **NORI** (UFPA/LASSE, já em uso) | ns-3 + 5G-LENA com E2 real para o Near-RT RIC do O-RAN SC | já é a bancada E2 do projeto | atraso de aplicação do Control (achado 36), KPM limitado (achados 30–31) | **manter**; propor upstream o ACK do RC (achado 26) |
| **ns-O-RAN** (Mavenir/Northeastern, [artigo](https://deepai.org/publication/ns-o-ran-simulating-o-ran-5g-systems-in-ns-3)) e seu ambiente Gym | ns-3 (mmWave/LTE) ligado ao RIC; Gym para DRL | ambiente Gym de referência para comparar o MAPPO | pilha diferente da do projeto (ns-3-mmwave, não 5G-LENA) | **referência metodológica**; não trocar a pilha |
| **OpenRAN Gym / ColO-RAN / SCOPE** ([artigo](https://arxiv.org/pdf/2207.12362)) | coleta de dados, RIC leve e teste de xApps em Colosseum, Arena, POWDER | transferência simulação → testbed real | depende de Colosseum/PAWR (EUA) | **referência**; útil se houver acesso a testbed PAWR |
| **dApps** (Lacava et al., [arXiv 2501.16502](https://arxiv.org/pdf/2501.16502v2); O-RAN nGRG, [relatório v2.0](https://mediastorage.o-ran.org/ngrg-rr/nGRG-RR-2025-05-dApps%20Architecture%20and%20Interfaces-v2.0.pdf)) | aplicações na DU/CU com interface E3, laço < 1 ms, código aberto sobre OAI | o caminho para ações críticas que não podem esperar a janela (seção 2) | ainda não é especificação O-RAN; exige OAI | **adotar como alternativa para ações críticas** se o testbed usar OAI |
| **QACM** (Wadud et al., IEEE TGCN 2024, [arXiv 2405.07324](https://arxiv.org/pdf/2405.07324)) e o CMF de [arXiv 2305.07117](https://arxiv.org/pdf/2305.07117) | mitigação de conflitos maximizando xApps com QoS atendida | baseline da literatura para comparar com TVS/EEVS e MAPPO | sem código público confirmado; reimplementação | **adotar como baseline B4** (reimplementado e declarado como tal) |
| **Mitigação por escalonador A2C** ([arXiv 2504.06867](https://arxiv.org/html/2504.06867v3)) | reconcilia ações de xApps por aprendizado, sem treino conjunto das xApps | comparação direta com o MAPPO da RDL-N2 | reimplementação | **referência** para a Fase 2 |
| **NTN no ns-3** (Sandri et al., TR 38.811, [WNS3 2023](https://www.nsnam.org/workshops/wns3-2023/04-sandri-slides-wns3-2023.pdf)) | modelos de propagação NTN | S9 (NTN) e o caso Skylo/direct-to-cell do GreenRAN | **já presente** no ns-3.48 instalado (`ThreeGppNTN*PropagationLossModel`) | **usar** na reconstrução do S9 |
| **NR V2X do 5G-LENA** ([v1.0](https://5g-lena.cttc.es/blog/26/)) | sidelink NR (Mode 2) | V2X real para o S11 | ramo separado (`nr-v2x-dev`) sobre ns-3 com patch (3.42); incompatível com a pilha nativa 3.48 | **não adotar agora**; S11 reconstruído com Uu (gNBs na rodovia) e handover |
| **Módulo de energia do ns-3** (`BasicEnergySource`) | fonte de energia com consumo | bateria do UAV (S10) e nós rurais (GreenRAN) | presente no ns-3.48 | **usar** no S10 |
| **NetworkX** | grafos em Python | grafo de conhecimento | já é dependência comum | **não necessário**: o grafo da RDL é implementado sem dependência externa (doc 02) |

## 2. Ações críticas que não podem esperar a janela de 200 ms

### 2.1 Antes de 2026-11-10

A janela de decisão era de 200 ms. Uma proposta com prioridade ≥ 80 antecipava o fechamento da janela (*fast-flush*, doc 02 §3), mas ainda passava pela arbitragem do lote inteiro.

### 2.2 Classes de urgência (implementado)

Cada proposta é classificada na chegada (`src/core/decision_window.py`, `RDLxApp._enqueue`):

| Classe | Critério | Tratamento |
| :-- | :-- | :-- |
| `CRITICAL` | prioridade ≥ 95, ou (xApp, parâmetro) marcado como crítico em `RDL_CRITICAL_TARGETS` ou na política A1 20000 (`critical_targets`) | **caminho rápido**: o laço acorda na hora e decide a crítica junto com as propostas pendentes do mesmo nó e das células vizinhas, sem esperar a janela |
| `URGENT` | 80 ≤ prioridade < 95, ou crítica acima da cota | janela fixa: fecha na hora; janela adaptativa: espera no máximo 20 ms |
| `NORMAL` | demais | janela de 200 ms (fecha entre 200 e 250 ms, porque o laço acorda a cada 50 ms); adaptativa: 50–500 ms pela taxa de chegada |

**Garantias e limites do caminho rápido:**

- **Safety Guard e arbitragem valem.** Duas críticas no mesmo alvo caem no mesmo grupo e são decididas pelo TVS.
- **Intervalo mínimo próprio.** No alvo, vale `critical_control_interval_ms` (100 ms; ajustável pela política A1), não os 1000 ms da classe normal. Sem isso, uma ação crítica numa célula controlada há menos de 1 s seria recusada.
- **Cota por xApp.** No máximo `RDL_CRITICAL_MAX_PER_S` (5) críticas por segundo; o excedente vira `URGENT`. Isso impede uma xApp de se declarar crítica o tempo todo para furar a fila.
- **Auditoria.** A decisão sai com `reason = CRITICAL_FAST_PATH`, fica em `CausalTracker.fast_path_decisions` e conta em `rdl_critical_path_decisions_total`.
- **Medida.** A latência de decisão do pipeline RDL-N1 é de milissegundos; o que domina o tempo até a RAN é o E2 (RIC Control → ACK). Uma ação abaixo de 10 ms não cabe no Near-RT RIC (seção 2.3).

### 2.3 Alternativas fora da RDL

| Camada | Mecanismo | Escala de tempo | Quando usar |
| :-- | :-- | :-- | :-- |
| **DU/CU — dApp** | lógica na própria DU (E3), com limites fixados pela RDL ou pelo rApp | < 1 ms a 10 ms | preempção URLLC, ajuste de escalonador por slot, desligamento de *layer* quando o tráfego some; ações que precisam do estado do slot |
| **DU — guarda local no escalonador** (RAN-CodeUpdates) | piso garantido de PRB para a fatia crítica, aplicado pelo escalonador antes de qualquer Control | por TTI | garantir que nenhum Control da RDL derrube a fatia crítica abaixo do mínimo; a RDL só ajusta acima do piso |
| **Near-RT RIC — E2SM-RC Policy/Insert** | a xApp instala uma política no nó E2 (Style de Policy) ou é consultada por Insert, e o nó decide no evento | ms (no nó) | regras do tipo "se a fatia URLLC passar de X ms, aplique Y" sem ida e volta à xApp |
| **Near-RT RIC — xApp de emergência dedicada** | xApp separada, só para eventos críticos, com prioridade de RMR | 10–100 ms | quando a ação crítica é rara e precisa de lógica própria; a RDL a trata como incumbente de alta prioridade |
| **Non-RT RIC — A1 / rApp** | política que pré-autoriza ações críticas (lista de parâmetros e faixas) e define os pisos da DU | > 1 s | configurar o que é crítico, não executá-lo |

**Recomendação para o GreenRAN:**

1. Caminho rápido `CRITICAL` na RDL, para não depender de nada novo no testbed.
2. Piso de PRB da fatia crítica no escalonador da DU, junto com as atividades 1.1 e 1.2.
3. dApp, se o testbed usar OAI, para ações abaixo de 10 ms (por exemplo, desligar *layer* SDM quando a carga zera).

### 2.4 Propostas que não cabem na janela: registro, aviso e adiamento (implementado)

Nenhuma proposta some sem rastro: toda proposta que não vira RIC Control é registrada com o motivo (`SAFETY`, `HYSTERESIS`, `LOST_ARBITRATION`, `STALE`, `OVERFLOW`, `DISPATCH_FAILED`). Detalhes em doc 02 §3.2.

| Mecanismo | O que faz | Interface |
| :-- | :-- | :-- |
| Registro consultável | entrada com motivo, detalhe, vencedora, decisão e `retry_after_ms` | `GET /rejections`; SDL (`save_rejection`) na implantação |
| Aviso à xApp | resultado da proposta, para a xApp decidir se repropõe | RMR `RDL_ACTION_RESULT` (30001) |
| Adiamento | só para `HYSTERESIS` e só com `defer_ok`; volta à janela quando o bloqueio expira, se ainda estiver na validade, e é reavaliada contra o estado atual | campos `defer_ok` e `ttl_ms` da proposta |
| Validade | proposta mais velha que a validade é descartada como `STALE` antes da decisão | `RDL_PROPOSAL_MAX_AGE_MS` (1000 ms) |

**Princípio:** guardar para consultar, sempre; executar depois, só com validade curta e nova avaliação. Uma ação de RAN decidida sobre um estado velho é pior do que nenhuma ação. Por isso o adiamento é opcional, limitado a 3 s (`RDL_DEFER_MAX_TTL_MS`) e restrito à histerese. Uma proposta que perdeu a arbitragem não volta sozinha: quem decide repropor é a xApp, com dados novos.

### 2.5 Acima de 1000 ms: Non-RT RIC e SMO

As escalas do O-RAN são: tempo real (DU/CU) abaixo de 10 ms, Near-RT RIC de 10 ms a 1 s, Non-RT RIC acima de 1 s. Com a histerese de 1000 ms, a RDL muda cada alvo no máximo uma vez por segundo (fora da classe crítica): está no teto do Near-RT.

| O que | Onde deve ficar | Por quê |
| :-- | :-- | :-- |
| Intenção com horizonte maior que 1 s (desligar células à noite, trocar prioridades por período, metas de energia) | rApp → política A1 (20001 para objetivos, 20000 para regras) | a RDL aplica a política como parâmetro de cada decisão; virar proposta de 200 ms em 200 ms só gera recusas por histerese |
| O que é crítico, a cota e os intervalos mínimos | rApp → política A1 20000 (`critical_targets`, `critical_control_interval_ms`, `cooling_lockout_ms`) | configurar o caminho rápido é decisão de operação, não de cada xApp |
| Aprendizado sobre os conflitos (quem briga com quem, onde, quantas recusas por histerese) | Non-RT RIC (rApp ou *data lake* do SMO) | lê `GET /rejections` (resumo) e as métricas Prometheus e ajusta a política em segundos ou minutos |

**O que falta:** a exportação ativa para o SMO (O1/VES ou R1) não existe; hoje o rApp tem de ler `GET /rejections` e as métricas Prometheus. O rApp de exemplo (`rapps/greenran_resource_optimizer.py`) ainda não lê esse resumo.

### 2.6 xApps fora do "guarda-chuva" da RDL (implementado em 2026-11-11)

Uma xApp que manda RIC Control (12040) direto ao E2Term passa por fora da RDL. Desde 2026-11-11 a governança é hierárquica, em quatro níveis, descrita no [doc 11](11_governanca_hierarquica_xapps.md):

1. **Plataforma:**
   - registro de xApps (identidade pela origem RMR);
   - `NetworkPolicy` que só deixa a RDL e a plataforma alcançarem a porta RMR de dados do E2Term (verificada no cluster da bancada);
   - porta RMR da RDL restrita às xApps proponentes;
   - tabela de rotas.
2. **Interceptação por rota:** o RIC Control de xApps de terceiros vira proposta, e a RDL responde ACK ou Failure.
3. **Conflito implícito:** KPM incoerente com a ação confirmada vira `IMPLICIT`, com suspeitas.
4. **Non-RT/SMO:** o rApp de governança põe a xApp em quarentena ou limita a prioridade dela por A1, ou recomenda retirá-la.

O doc 11 também traz a supervisão sob demanda (modo `ON_DEMAND`) e onde ficam o dbaas, o NetworkX e o Neo4j.

No GreenRAN, o RANSlicer-GreenRAN e o EnergySaver-GreenRAN são do próprio projeto: bastam o nível 1 e as propostas por RMR 30000. A interceptação só é necessária para xApps prontas de terceiros.
