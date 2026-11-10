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
| **Mitigação por escalonador A2C** ([arXiv 2504.06867](https://arxiv.org/html/2504.06867v3)) | reconcilia ações de xApps por aprendizado, sem treino conjunto das xApps | comparação direta com o MAPPO da CA-RDL | reimplementação | **referência** para a Fase 2 |
| **NTN no ns-3** (Sandri et al., TR 38.811, [WNS3 2023](https://www.nsnam.org/workshops/wns3-2023/04-sandri-slides-wns3-2023.pdf)) | modelos de propagação NTN | S9 (NTN) e o caso Skylo/direct-to-cell do GreenRAN | **já presente** no ns-3.48 instalado (`ThreeGppNTN*PropagationLossModel`) | **usar** na reconstrução do S9 |
| **NR V2X do 5G-LENA** ([v1.0](https://5g-lena.cttc.es/blog/26/)) | sidelink NR (Mode 2) | V2X real para o S11 | ramo separado (`nr-v2x-dev`) sobre ns-3 com patch (3.42); incompatível com a pilha nativa 3.48 | **não adotar agora**; S11 reconstruído com Uu (gNBs na rodovia) e handover |
| **Módulo de energia do ns-3** (`BasicEnergySource`) | fonte de energia com consumo | bateria do UAV (S10) e nós rurais (GreenRAN) | presente no ns-3.48 | **usar** no S10 |
| **NetworkX** | grafos em Python | grafo de conhecimento | já é dependência comum | **não necessário**: o grafo da RDL é implementado sem dependência externa (doc 02) |

## 2. Ações críticas que não podem esperar a janela de 200 ms

### 2.1 O que existe hoje

A janela de decisão é de 200 ms. Uma proposta com prioridade ≥ 80 já antecipa o fechamento da janela (*fast-flush*, doc 02 §3). Mas ela ainda passa pela arbitragem do lote, e a decisão espera o resto do pipeline.

### 2.2 Mecanismo proposto dentro da RDL: classes de urgência

Cada proposta é classificada:

| Classe | Critério | Tratamento |
| :-- | :-- | :-- |
| `CRITICAL` | prioridade ≥ 95, ou parâmetro/xApp marcado como crítico por política A1 | **caminho rápido**: despacho imediato, sem esperar a janela, depois do Safety Guard por proposta e de uma verificação de conflito só contra o estado confirmado e as ações em voo no mesmo alvo e nas células vizinhas |
| `URGENT` | 80 ≤ prioridade < 95 | janela encurtada (`urgent_window_ms`, padrão 20 ms) |
| `NORMAL` | demais | janela normal (200 ms), ajustável |

**Janela adaptativa** para `NORMAL`: o tamanho é escolhido entre um mínimo e um máximo (50–500 ms) pela taxa de chegada de propostas e pelo tempo desde o último KPM. Muitas propostas por segundo pedem janela maior, para agrupar conflitos. KPM novo e pouca concorrência pedem janela menor.

**Garantias:**

- O caminho rápido não pula o Safety Guard nem a histerese.
- Uma ação `CRITICAL` que conflite com outra `CRITICAL` no mesmo alvo dentro de `critical_guard_ms` é decidida por TVS entre as duas, sem esperar mais ninguém.
- Toda ação do caminho rápido é registrada como tal no `CausalTracker` para auditoria.

A implementação fica em `src/core/decision_window.py` (doc 02 §3).

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
