# 18. Calibração dos pesos da arbitragem (TVS/EEVS) com dados

Status: **desenho**, escrito em 2026-11-12 durante a campanha 10. Nada aqui está implementado. Este arquivo só entra no git depois da campanha 10, porque o executor grava o HEAD em cada execução.

**Decisões do autor (2026-11-12):**
- Aprovados, para depois da campanha 10:
  - os campos opcionais da proposta `scope`, `slice_sst` e `ratio_kind`;
  - o motivo de recusa `SLA_PROTECTION`, separado de `LOST_ARBITRATION`.
- **Ordem:** o pré-registro 13 espera o doc 16 e roda em malha fechada, com as xApps originais no laço. Não há exceção para malha aberta.
  - Em malha fechada, a decisão deixa de ser constante por partes nos pesos, porque as propostas reagem ao KPM. Por isso a enumeração exata da Parte B (seção 5.2) tem de ser revista antes do registro.
  - O merge de `eevs-aditivo-padrao`, já previsto para o fim da campanha 10, vem antes da calibração.

Limite que este desenho resolve (artigo SBRC, seção Limitações): *"Os pesos da arbitragem são calibrados à mão. Com E2 real, uma margem de 0,0125 no TVS fez a RDL preferir um pedido de eMBB à proteção da URLLC."*

## 1. Decisões

1. **Antes de calibrar pesos, corrigir a raiz semântica (Parte A).** No S8, o termo de vazão do TVS ordena as duas opções ao contrário da vazão total medida. Calibrar pesos sobre um escore com erro de sinal só desloca a fronteira de decisão. Isso acertaria o S8 pelo motivo errado.
2. **Separar modelo de preferência.** O peso de energia frente à QoS é preferência do operador e já chega por A1 (`energy_weight`, tipo 20001; o rApp usa 0,10 de dia e 0,45 à noite). Ele não se aprende com dados de vazão. A calibração **fixa** `w_energy` e `w_energy_ind` nos valores padrão e ajusta só os pesos que dependem do modelo.
3. **Método da Parte B: enumeração exata das regiões de decisão, e não otimização bayesiana.** Em malha aberta, a decisão é uma função determinística e constante por partes dos pesos (seção 5.2). O espaço tem poucas regiões, que a programação linear enumera de forma exata.
4. **Objetivo:** o menor arrependimento máximo entre os cenários (vazão e atraso). Segurança e proteção da fatia crítica entram como **restrições**, e não como termos ponderados, a mesma ideia do CMDP da Fase 2. O desempate é pela **maior margem**: o raio da maior bola de pesos em que nenhuma decisão muda. É a resposta direta à margem de 0,0125.
5. **Separação estrita entre calibração e avaliação:**
   - **calibração:** campanha 10 (sementes 11001–11005), rodadas de calibração nessas mesmas sementes e o S8 do pré-registro 07;
   - **avaliação:** sementes novas (14001–14005 no ns-3; 5101–5110 e 5201–5210 no NORI) e cenários que não entraram na calibração (S1–S7 e um S8b novo).

## 2. O problema, com números

### 2.1 A decisão do S8 e o que ela custou

Margem do TVS no S8, xSlice menos eMBB, com os pesos padrão 0,40/0,25/0,15/0,10/0,10. Fonte: `artigos/dados/insights/p1_tvs_s8_decomposicao.csv`, calculado com a classe `Reasoning` real.

| Termo | xSlice (teto eMBB 25 %, prio. 90) | eMBB (teto eMBB 80 %, prio. 60) | Diferença ponderada |
| :-- | --: | --: | --: |
| SLA | 0,85 | 0,75 | +0,0400 |
| vazão | 0,25 | 0,80 | −0,1375 |
| energia | 0,833 | 0,467 | +0,0550 |
| estabilidade | 0,90 | 0,90 | 0 |
| prioridade | 0,90 | 0,60 | +0,0300 |
| **U_TVS** | 0,7075 | 0,7200 | **−0,0125** |

- **Limiares** (`p1_tvs_s8_limiares.csv`, com os demais pesos reescalados): o xSlice passaria a vencer com `w_sla` ≥ 0,47, `w_throughput` ≤ 0,23, `w_energy` ≥ 0,18 ou `w_priority` ≥ 0,14.
- **Reforço A1:** o `urllc_priority_boost` não vira a decisão. A prioridade normalizada satura em 1,0, e a margem máxima atingível é −0,0025.
- **Deslocamento mínimo** (derivado da tabela acima): transferir 0,014 de peso da vazão para a energia zera a margem. A decisão está a 0,014 de peso de virar.
- **No simplex dos 5 pesos** (2 milhões de pontos Dirichlet(1), cálculo deste desenho com os escores da tabela): o xSlice vence em 67 % dos vetores de peso. O ponto padrão está na minoria.
- **Efeito medido com E2 real** (pré-registro 07, 30 pares, desvio-padrão entre sementes < 0,01 Mb/s):

  | Baseline | Cotas eMBB/URLLC | eMBB (Mb/s) | URLLC (Mb/s) | Total (Mb/s) |
  | :-- | :-: | --: | --: | --: |
  | B0, B2 | 25/75 | 95,24 | 151,49 | 246,73 |
  | B1, B3 | 80/20 | 151,49 | 76,45 | 227,93 |

  O B3 entregou 18,79 Mb/s a menos no total e metade da vazão da URLLC.

### 2.2 As políticas do rApp não resolvem, e uma delas acerta pelo motivo errado

A política A1 escreve `w_sla` e `w_energy` sem renormalizar (`RDLxApp._apply_a1_policy` e `Reasoning.apply_policy`). Os demais pesos ficam no padrão. Margem do S8 com os valores de `rapps/greenran_resource_optimizer.py`, calculada com a classe `Reasoning` real (código no Apêndice A):

| Política A1 do rApp | `w_sla` | `w_energy` | Margem (xSlice − eMBB) | Vence |
| :-- | --: | --: | --: | :-- |
| nenhuma (padrão) | 0,40 | 0,15 | −0,0125 | eMBB |
| `DAY` | 0,60 | 0,10 | −0,0108 | eMBB |
| `NIGHT` | 0,35 | 0,45 | +0,0925 | xSlice |
| `NIGHT` com energia prioritária | 0,35 | 0,55 | +0,1292 | xSlice |
| SLA em risco | 0,75 | 0,10 | +0,0042 | xSlice |

- **De dia:** a política que dá mais peso ao SLA ainda escolhe o eMBB.
- **À noite:** o xSlice vence pelo termo de **energia**, que supõe que uma cota de 25 % ativa menos PRBs. Com a semântica de cota por fatia do NORI, as duas opções somam 100 % dos PRBs (seção 3).
- **SLA em risco:** a decisão vira por 0,0042.

## 3. Diagnóstico: a raiz semântica

A mesma ação `PRB_QUOTA` com valor *v* significa coisas diferentes conforme o backend, e o `XAppAction` não diz qual (`src/conflict_types.py`: não há campo de fatia nem de escopo).

| Backend | O que `PRB_QUOTA = v` faz | Onde |
| :-- | :-- | :-- |
| ns-3 nativo (S\*, G\*) | máscara de RBG da **célula inteira**: v % dos RBGs para todos os UEs | `RdlActuation::Apply`, `simulations/ns3/rdl-nr-common.h` (`SetDlNotchedRbgMask`) |
| NORI (S8, malha fechada) | teto **da fatia eMBB** = v, e a URLLC recebe 100 − v | `quotas_for`, `src/closed_loop/hrdl_slice_loop.py` |

Os escores de `Reasoning._calculate_action_scores` supõem que um *v* maior é mais recurso para quem propõe e menos economia de energia:

- s_vazão = v/100;
- s_SLA, com prioridade ≥ 90: 0,98 se v ≥ 70, senão 0,85;
- s_energia = max(0,2; 1 − v/150).

Na célula inteira do ns-3, essa leitura está certa: um teto maior é mais recurso para todos. Na cota por fatia, ela erra três vezes:

1. **Vazão:** a opção com s_vazão maior (80/20) entrega 18,79 Mb/s a menos no total. O termo tem o sinal trocado em relação à grandeza que ele diz representar.
2. **SLA:** a ação que protege a URLLC (25) recebe s_SLA = 0,85, menor que o 0,98 que receberia se pedisse 70 % ou mais. A ação protetora é penalizada por proteger.
3. **Energia:** 25/75 e 80/20 ativam os mesmos 100 % de PRBs, mas o termo dá 0,833 a um e 0,467 ao outro.

Nenhum vetor de pesos faz a decisão certa pelo motivo certo. Por isso a Parte A vem antes da Parte B.

## 4. Parte A: modelo de efeito por fatia

### 4.1 Esquema da proposta

- Campos opcionais em `XAppAction` e na mensagem RMR 30000:
  - `scope`: `cell` ou `slice`;
  - `slice_sst`;
  - `ratio_kind`: `max`, `min` ou `dedicated`, os três campos do RRM Policy Ratio que o codec já monta: `SlicePrbQuota(sst, max_prb_ratio, min_prb_ratio, dedicated_prb_ratio)` em `src/e2/v3/codec.py`.
- **Padrão por backend:** declarado no perfil de backend (`docs/12` §4), e não inferido.
  - ns-3 nativo: `scope = cell`;
  - NORI: `scope = slice`, SST 1, com complemento no SST 2, como faz `quotas_for`;
  - srsRAN e OAI: campo a confirmar no TB0.

### 4.2 Efeito previsto

- Para cada candidata, a RDL monta a alocação depois da decisão, a′ (teto por fatia), e prevê a vazão de cada fatia:

  T̂_s(a′) = T_s^livre · r_s(a′_s)

- r_s é a curva teto → vazão relativa medida no NORI: `XApp-RDL-F1/experiments/calibration/slice_cap_curve_v5.json`, sha256 `d7c2f54e…8282d`, idêntico à cópia da Fase 2. A interpolação só usa níveis que restringem (regra v6, achados 41 e 42), como em `CapCurve.ratio`.
- **Validação já feita fora da amostra:** no teto de 25 %, previsto 95,2155 contra medido 95,2397 Mb/s, erro de −0,025 %, n = 64 (`p2_calibracao_validacao_fora_amostra.csv`). Os pontos da curva são 10, 15, 20 e 30 %, com saturação estimada em 39,99 %.
- **T_s^livre:**
  - o KPM do NORI **não** mede vazão por UE (`DRB.UEThpDl` sai sempre 0) e superestima o `RRU.PrbUsedDl` (225 de 139; `docs/06` §5.4, `hrdl_slice_loop.py`);
  - por isso, no NORI, T_s^livre é a vazão de base da condição de calibração (151,488 Mb/s por fatia, `base_throughput_mbps` da curva), e o KPM só informa quais fatias têm UEs;
  - **o modelo de efeito vale só na condição calibrada** (100 MHz, 300 Mb/s). O pré-registro 06 refutou a transferência para 50 MHz (H6.4), e fora dela o modelo cai no modo heurístico (seção 4.5).
  - Com um agente E2 que meça vazão por fatia (testbed), T_s^livre vem do KPM_t0. Se a fatia já estiver limitada, ele vem da inversa da curva na região que restringe.

### 4.3 Escores novos para `PRB_QUOTA` com `scope = slice`

- s_vazão(a) = Σ_s T̂_s(a′) ÷ Σ_s T_s^livre.
- s_SLA(a) = min, sobre as fatias com SLA, de min(1, T̂_s(a′)/T_s^req).
  - T_s^req vem da política A1 21000 (`embb_min_thp_mbps` das câmeras) ou, sem SLA declarado, é T_s^livre.
  - Fatia com SLA: prioridade ≥ 90 ou declarada na política.
- s_energia(a): pelo modelo do docs/17, a partir da ocupação prevista Σ_s min(teto_s, demanda_s). Com cotas complementares que somam 100 % e demanda que satura, as duas opções empatam, como deve ser.

### 4.4 Guarda de SLA (restrição, não peso)

- **Regra:** uma candidata cuja previsão leva uma fatia com SLA abaixo do requisito (s_SLA < 1) é inelegível se outra candidata do mesmo conflito mantém s_SLA = 1.
- **Se todas violam:** vence a de maior s_SLA.
- **Motivo de recusa novo:** `SLA_PROTECTION`. Hoje são 7 motivos (`REASONS`, `src/core/proposal_registry.py`).
  - A recusa não pode ser contada como `LOST_ARBITRATION`. O rApp aumenta o peso de energia quando o EnergySaver perde arbitragens à noite (`greenran_resource_optimizer.py`), e uma recusa por proteção de SLA não deve alimentar essa regra.
- **Analogia com a Fase 2:** é a restrição de custo do CMDP da CA-RDL (`cost_limit` = 0,05 em `cardl/marl/mappo.py`) levada à heurística. A diferença é que a guarda é uma regra determinística, não um multiplicador de Lagrange.

### 4.5 Modo heurístico

- Sem curva válida para o backend e a condição, ou sem informação de fatia, a RDL usa os escores atuais e registra `effect_model: "heuristic"` no log de decisão. Com o modelo de efeito, registra `effect_model: "curve:<sha256>"`.
- **Em malha aberta no ns-3:** as propostas do catálogo têm `scope = cell` e não há KPM. A Parte A **não muda nenhum cronograma do ns-3**, o que se verifica antes do registro (H14.0). Ela age onde há fatia e modelo de efeito: no NORI, no testbed e na malha fechada do docs/16.

### 4.6 Previsões do desenho (a confirmar na implementação)

**S8** (25/75 contra 80/20), com os valores medidos no pré-registro 07:

- s_vazão = 246,73/302,98 = 0,814 contra 227,93/302,98 = 0,752;
- s_SLA (URLLC) = 1,0 contra 0,5046;
- a guarda já elimina 80/20. Sem a guarda, com os pesos padrão, a margem seria 0,40 × 0,495 + 0,25 × 0,062 + 0,10 × 0,30 = **+0,244** a favor do xSlice, contra −0,0125 hoje.
- **Ressalva:** esses números vêm dos mesmos dados que motivaram a correção. O S8 confirma a implementação, mas não testa a generalização.

**S8b** (novo, para avaliação; teto eMBB de 35 % pelo xSlice com prioridade 90, contra 55 % pelo eMBB com prioridade 60). Pela curva:

- 35/65 dá eMBB 0,8763 × 151,49 = 132,75 e URLLC 151,49, total 284,24 Mb/s;
- 55/45 deixa as duas fatias acima da saturação de 39,99 %, com total previsto de 302,98 Mb/s;
- a guarda não age, porque as duas opções protegem a URLLC;
- **com os pesos padrão, o TVS ainda escolhe o xSlice** por +0,0145, e só o termo de prioridade (+0,03) supera a perda de vazão prevista (−0,0155). O custo previsto é de 18,74 Mb/s.

O S8b mostra o que a Parte A não resolve: o termo de prioridade continua favorecendo quem tem prioridade maior mesmo quando o pedido dela não protege nada. Esse é um papel da Parte B, testado fora da calibração.

## 5. Parte B: calibração dos pesos

### 5.1 O que se calibra

- **TVS:** `w_sla`, `w_throughput`, `w_stability` e `w_priority`, com `w_energy` = 0,15 fixo. Como o argmax não muda se todos os pesos forem multiplicados pela mesma constante positiva, normaliza-se a soma em 0,85, um simplex de 3 dimensões.
- **EEVS:** `w_qos_ind`, `w_fairness_ind` e `w_viol_ind`, com `w_energy_ind` = 0,20 fixo e soma 0,80, um simplex de 2 dimensões.
- **Agregação do EEVS:** a que for padrão depois do merge de `eevs-aditivo-padrao` (pendência citada no status do `docs/16`), declarada no pré-registro.
- **Valores de preferência fixados** (`w_energy` e `w_energy_ind`): continuam ajustáveis por A1. A avaliação confere as decisões nos pontos `DAY`, `NIGHT` e "SLA em risco" do rApp.

### 5.2 Por que enumeração exata e não otimização bayesiana

- Em malha aberta, os escores de cada candidata são constantes (sem KPM, `Reasoning.kpm_by_node` fica vazio), e o histórico está desligado (`get_similar_resolutions` devolve `[]` em `memory_module.py` e `sdl_repository.py`).
- Cada decisão do TVS é o argmax de w·s_a sobre as candidatas. Cada decisão do EEVS é o argmax de w·(Q, E, J, −V) sobre os subconjuntos compatíveis. Ambas são lineares em w.
- O cronograma de um cenário é, então, constante dentro das células de um arranjo de hiperplanos w·(s_a − s_b) = 0.
- Um processo gaussiano supõe um objetivo suave, mas aqui o objetivo é feito de platôs com degraus. A otimização bayesiana gastaria avaliações caras do ns-3 para reaprender degraus que a programação linear acha de forma exata e barata.
- A otimização bayesiana volta a fazer sentido na malha fechada do docs/16, em que a decisão depende do KPM e cada avaliação é uma co-simulação. Fica como extensão.

### 5.3 Algoritmo (`scripts/calibration/decision_regions.py`, novo, depois da campanha)

1. **Instrumentar sem alterar a decisão.** Interceptar `Reasoning.resolve`, como `run_conflict_experiment.py` já faz com `capture_resolve`. Para cada conflito, gravar o vetor de escores de cada candidata (TVS) ou de cada subconjunto compatível (EEVS).
2. **Hiperplanos.** Para cada par de candidatas, w·(s_a − s_b) = 0, restrito à face de pesos da seção 5.1.
3. **Células do arranjo.** Para cada padrão de sinais viável, resolver um LP de viabilidade com folga. Em cada célula, achar o **centro de Chebyshev** w_c e o raio ρ_c (LP).
4. **Ponto fixo.** Rodar `decide()` (`scripts/certification/run_conflict_experiment.py`) em cada w_c, em todos os cenários de calibração. Uma decisão numa janela muda o estado das seguintes (ações confirmadas, histerese, regras entre células) e pode criar conflitos novos. Os hiperplanos novos entram, e o ciclo se repete até uma rodada sem cronograma novo.
5. **Saída:** para cada região, o sha256 do cronograma por cenário, w_c, ρ_c e a fração do volume da face, estimada com 10⁵ pontos.

**Custo:** a decisão leva mediana de 0,376 ms por janela (710 janelas; `artigos/dados/insights/p1_latencia_resumo.csv`, linha `TODAS`). Mesmo com milhares de pontos e algumas dezenas de janelas por cenário, são minutos de CPU em Python, sem ns-3.

### 5.4 Medida de cada cronograma distinto

- **Cronograma igual** (sha256 do `action_schedule.csv`) ao de uma execução B0–B3 da campanha 10 no mesmo cenário: reaproveitam-se as métricas das 5 sementes.
- **Cronograma novo:** vira **rodada de calibração** com as sementes 11001–11005, pelo executor certificado, em `experiments/calibration/weights/<região>/`. Fica fora de `experiments/runs/` e, portanto, fora das análises dos artigos.
- **Orçamento** (fixado antes): se houver mais de 30 pares (cenário, cronograma novo), só se medem as regiões com volume ≥ 1 % da face. As demais ficam "não medidas" e inelegíveis.
- **S8:** os dois cronogramas possíveis (25/75 e 80/20) já estão medidos no pré-registro 07, com 30 ou mais sementes cada. A calibração não precisa de rodada nova no NORI.

### 5.5 Objetivo, restrições e seleção

As métricas vêm de `analyze_conflict_runs.py`, na janela de conflito do catálogo, com a média das 5 sementes de calibração.

- **Arrependimento por cenário s e cronograma σ**, sobre todos os cronogramas medidos de s:
  - r_vazão(σ) = (max_σ′ thp − thp(σ)) ÷ max_σ′ thp;
  - r_atraso(σ) = (atraso(σ) − min_σ′ atraso) ÷ min_σ′ atraso.
- **Objetivo:** R(região) = max sobre s e sobre {vazão, atraso} do arrependimento. É o arrependimento minimax: não depende de escala e não cria pesos sobre os pesos. A única escolha de desenho é a lista de métricas, declarada aqui.
- **Restrições:**
  - C1: `unsafe_applied` = 0 em todas as execuções dos cronogramas da região;
  - C2: no S8, cronograma 25/75 (URLLC medida 151,49 contra 76,45 Mb/s).
- **Seleção**, no padrão de `cardl/marl/select.py`:
  1. elegíveis = C1 e C2;
  2. menor R;
  3. empate (diferença < 0,01): maior ρ;
  4. novo empate: menor distância L1 aos pesos padrão;
  5. sem elegível: os pesos padrão ficam, e o fato é relatado.
- **Saída:** `experiments/calibration/weights/weights_selection.json` com a regra, os sha256 das entradas (análise da campanha 10, catálogo, `reasoning.py` e dados do pré-registro 07), todas as regiões e a escolha. Leva `publication_eligible: false` até o pré-registro 13.
- **Robustez relatada:**
  - ρ da região escolhida;
  - a menor diferença de utilidade entre a vencedora e a segunda colocada em todos os conflitos da calibração, com os pesos escolhidos. Hoje, no S8, é 0,0125.

### 5.6 Entrega dos pesos

- Hoje o `RDLxApp` cria `Reasoning(self.memory, config={})` (`src/rdl_xapp.py`), e os pesos padrão estão no código.
- Proposta: `RDL_WEIGHTS_FILE` aponta para o `weights_selection.json`, e o sha256 dele vai para o log de decisão. A política A1 continua sobrepondo `w_sla` e `w_energy` (seção 8, C18.1–C18.2).

### 5.7 Limites honestos da Parte B

- **Identificabilidade:** com 8 cenários de ns-3 e o S8, várias regiões produzem os mesmos cronogramas em todos os cenários e são indistinguíveis pelos dados. A afirmação possível é sobre **decisões**, não sobre "pesos verdadeiros".
- **Malha aberta:** as regiões valem para propostas fixas do catálogo. Na malha fechada (docs/16), o mapa muda com o estado, e a calibração em malha aberta é só o ponto de partida.
- **Sobreajuste:** a defesa é a avaliação em cenários que não entraram na calibração (S1–S7 e S8b), e não só em sementes novas. Em malha aberta, a decisão não depende da semente, e sementes novas testam só a variância do ns-3.

## 6. O que reaproveitar da Fase 2

| Componente da Fase 2 | Uso aqui | Observação |
| :-- | :-- | :-- |
| `cardl/marl/calibration.py` (`CapCurve`, `load_curve`, verificação do sha256, interpolação só entre níveis que restringem) | modelo de efeito por fatia (4.2), portado para `src/core/effect_model.py` | a curva original já está no F1 (`experiments/calibration/slice_cap_curve_v5.json`, mesmo sha256) |
| validação fora da amostra da curva (`p2_calibracao_validacao_fora_amostra.csv`) | evidência de que o modelo de efeito acerta no ponto de 25 % | só a 100 MHz e 300 Mb/s |
| `cardl/marl/select.py` (sementes disjuntas; elegibilidade por restrição; desempate lexicográfico; sem elegível, mantém a reserva; JSON com sha256) | protocolo da seleção (5.5) | mesma estrutura de arquivo |
| restrição do CMDP (`cost_limit` = 0,05, `cardl/marl/mappo.py`) | ideia da guarda de SLA (4.4) e da restrição C2 | sem Lagrange: a busca é exaustiva |
| **Não reaproveitar:** a política MAPPO e o ambiente (`cardl/marl/env.py`) | — | o ambiente é estilizado. A energia dele é a soma dos tetos, e a observação tem lacuna entre treino e implantação (`p2_lacuna_observacao.csv`): no NORI, a demanda cai no valor neutro porque `DRB.UEThpDl` sai 0. Usá-lo como substituto do ns-3 traria essas limitações para a calibração |

## 7. Etapas

| Etapa | Entrega | Gate |
| :-- | :-- | :-- |
| W0 | campanha 10 concluída e analisada; merge de `eevs-aditivo-padrao` decidido | — |
| W1 | Parte A: campos `scope`, `slice_sst` e `ratio_kind`; `effect_model.py`; escores novos; guarda; motivo `SLA_PROTECTION`; perfil de backend; baselines `B3S` e `B3C` no driver nativo e no NORI | testes de unidade; S8 com os KPM gravados do pré-registro 07, reprocessados offline, dá 25/75 |
| W2 | `decision_regions.py`; mapa de regiões; tabela H14.0 | ponto fixo atingido; B3S = B3 em todos os cenários do ns-3 |
| W3 | rodadas de calibração (seção 5.4) | orçamento respeitado; todas as execuções `SUCCESS` ou relatadas |
| W4 | `weights_selection.json` | regra aplicada sem intervenção manual |
| W5 | pré-registro 13 commitado antes da avaliação | seção 9 |
| W6 | avaliação e artigos (números só pelos scripts) | — |

## 8. Lista de correções (divergências achadas)

| # | Onde | Divergência | Proposta |
| :-: | :-- | :-- | :-- |
| C18.1 | `src/rdl_xapp.py`, `_apply_a1_policy` | `sla_weight` escreve `w_sla` **e** `w_qos_ind`, e `energy_weight` escreve `w_energy` **e** `w_energy_ind`. TVS e EEVS têm escalas e termos diferentes (o EEVS subtrai violações), então o mesmo número não significa o mesmo nos dois | campos A1 separados, ou multiplicadores relativos aos pesos de base |
| C18.2 | `Reasoning.apply_policy` | não renormaliza: com `DAY`, a soma do TVS é 1,15, e margens de políticas diferentes não são comparáveis | renormalizar os pesos não fixados, ou documentar que a escala muda |
| C18.3 | `Reasoning._calculate_action_scores` (`PRB_QUOTA`) | s_vazão, s_SLA e s_energia supõem "*v* maior = mais recurso de quem propõe". Isso só vale na célula inteira (ns-3), não na cota por fatia (NORI) | Parte A |
| C18.4 | `docs/02` §4 e catálogo | a semântica de `PRB_QUOTA` por backend não está escrita. O S8 diz "teto eMBB 25 %", e o G1 diz "reserva 80 % para as câmeras", o que no ns-3 é um teto da célula inteira | documentar por backend; no G1, dizer "teto de 80 % da célula" |
| C18.5 | `docs/16` §9 | o rascunho do pré-registro 11 usa as sementes 12001–12005, já usadas no pré-registro 09 | trocar, por exemplo, para 16001–16005 |
| C18.6 | artigo SBRC, Limitações | o texto fala só da margem | acrescentar que a política `DAY` também escolhe o eMBB (−0,0108) e que o termo de vazão ordena as opções ao contrário da vazão total medida (−18,79 Mb/s) |

## 9. Rascunho do pré-registro 13 (não registrado)

Formato dos pré-registros 08–10. É fechado e commitado depois de W4 e antes da avaliação.

### 1. Objetivo

Avaliar, fora dos dados de calibração:

- (a) o modelo de efeito por fatia com a guarda de SLA (`B3S`, pesos padrão);
- (b) o modelo de efeito com os pesos calibrados (`B3C`);

contra o H-RDL atual (`B3`), na RAN simulada (ns-3) e com E2 real (NORI).

### 2. Estado do código

- O commit deste pré-registro, o mesmo da avaliação.
- O `weights_selection.json` (sha256 citado aqui) e a curva `slice_cap_curve_v5.json` (sha256 `d7c2f54e…8282d`).
- Agregação do EEVS declarada.

### 3. Desenho

- **Verificação determinística (H14.0, antes do registro, sem ns-3):** cronogramas de B3, B3S e B3C em todos os cenários do catálogo e do S8b, anexados como tabela, como no pré-registro 09 §2.
- **ns-3, cenários de calibração** (S9, S10, S11, S12, S13, S15, G1 e G2): **só** os cenários em que o cronograma do B3C difere do B3. Onde são iguais, os braços são idênticos por construção e isso é relatado.
  - Baselines B3 e B3C.
  - Sementes **14001–14005**, nunca rodadas, as mesmas nos dois baselines.
- **ns-3, cenários fora da calibração** (S1 a S7; S0 como controle sem conflito): mesma regra.
  - Baselines B3 e B3C.
  - Sementes 14001–14005.
- **NORI:**
  - S8 com B2, B3, B3S e B3C nas sementes **5101–5110**;
  - S8b (catálogo novo: xSlice com teto eMBB de 35 % e prioridade 90, contra eMBB com 55 % e prioridade 60; mesma condição do S8, 100 MHz e 300 Mb/s) com B2, B3, B3S e B3C nas sementes **5201–5210**.
  - São 10 sementes em cada, porque o S8 mostrou desvio-padrão < 0,01 Mb/s entre sementes (pré-registro 07). O que as sementes testam no NORI é a cadeia e a reprodutibilidade.
- **Duração:** estimada depois de H14.0, porque depende de quantos cenários divergem. As durações dos cenários S9–G2 vêm do pré-registro 10.
- **Comandos** (em primeiro plano, no painel Terminal):

  ```bash
  bash scripts/run_native_campaign.sh --scenarios "<cenários com B3C ≠ B3, da tabela H14.0>" \
    --baselines "B3 B3C" --seeds 14001-14005 --jobs 2
  bash scripts/run_nori_campaign.sh --scenarios "S8" --baselines "B2 B3 B3S B3C" --seeds "$(seq -s ' ' 5101 5110)"
  bash scripts/run_nori_campaign.sh --scenarios "S8b" --baselines "B2 B3 B3S B3C" --seeds "$(seq -s ' ' 5201 5210)"
  ```

### 4. Hipóteses e critérios

| Hipótese | Onde | Critério |
| :-- | :-- | :-- |
| H14.0 (determinística) | todos | os cronogramas do B3, do B3S e do B3C são os da tabela anexada, em todas as sementes. B3S = B3 em todos os cenários do ns-3 |
| H14.1 | S8, NORI | B3S e B3C aplicam 25/75 em 10/10 sementes. A vazão da URLLC depois do Control fica a ±1 % de 151,49 Mb/s, e a total a ±1 % de 246,73 Mb/s (B0/B2 do pré-registro 07) |
| H14.2 (modelo de efeito fora da calibração) | S8b, NORI | em cada baseline, a vazão medida por fatia depois do Control fica a ±5 % da prevista pela curva para as cotas aplicadas (35/65: eMBB 132,75 e URLLC 151,49; 55/45: 151,49 e 151,49 Mb/s), em ≥ 9/10 sementes. A escolha de cada braço é a da H14.0. Com os pesos padrão, o B3S deve escolher 35/65 (seção 4.6) |
| H14.3 (segurança) | ns-3 e NORI | `unsafe_applied` = 0 em todas as execuções do B3S e do B3C; nenhum Control fora de 0–100 no NORI |
| H14.4 (replicação) | cenários de calibração com B3C ≠ B3 | o sinal da diferença pareada B3C − B3 em `thp_conflict` e em `delay_conflict_ms`, medido na calibração, repete-se em ≥ 4/5 sementes novas, em cada cenário |
| H14.5 (não inferioridade fora da calibração) | S1–S7 com B3C ≠ B3 | em cada cenário: média pareada de `thp_conflict` do B3C ≥ 0,95 × a do B3, e de `delay_conflict_ms` ≤ 1,10 × a do B3 (margens do pré-registro 09, H10.3) |

- **Descritivo:**
  - vazão por fatia e total no NORI, com diferenças pareadas B3S − B2 e B3C − B2 (no S8b, quanto custa escolher pela prioridade);
  - no ns-3, `thp_pre`, `thp_conflict`, `thp_post`, `delay_conflict_ms`, ações e oscilações, com IC 95 %;
  - decisões nos pontos A1 `DAY`, `NIGHT` e "SLA em risco" (cronograma, sem ns-3).
- **Regra de adoção** (fixada aqui):
  - a Parte A vira padrão se H14.0–H14.3 forem confirmadas;
  - os pesos calibrados viram padrão se H14.0–H14.5 forem confirmadas;
  - caso contrário, ficam como opção, e o resultado negativo vai para os artigos com o mesmo destaque.

### 5. Regras de relato

- Iguais às do pré-registro 10: `--retry-failed` uma vez; retomada depois de interrupção; execuções incompletas refeitas desde o início.
- Nenhuma execução de avaliação volta para a calibração. Um novo `weights_selection.json` exige um novo pré-registro com sementes novas.
- Nada fixado aqui é alterado depois de ver os dados.

## Apêndice A: cálculo da margem do S8 sob as políticas do rApp

Executado em 2026-11-12 com o `.venv` dos artigos, importando `src/` do F1 sem alterá-lo:

```python
import sys
sys.path.insert(0, r"C:\Users\georg\RDL\XApp-RDL-F1")
from src.core.reasoning import Reasoning
from src.conflict_types import XAppAction

class Mem:
    def get_similar_resolutions(self, c): return []

xs = XAppAction(xapp_id="xslice", node_id="gnb_0", parameter="PRB_QUOTA", value=25, priority=90, action_id="x")
eb = XAppAction(xapp_id="embb_throughput", node_id="gnb_0", parameter="PRB_QUOTA", value=80, priority=60, action_id="e")
for name, w in {"padrao": {}, "DAY": {"w_sla": .60, "w_energy": .10}, "NIGHT": {"w_sla": .35, "w_energy": .45},
                "NIGHT alta": {"w_sla": .35, "w_energy": .55}, "SLA em risco": {"w_sla": .75, "w_energy": .10}}.items():
    r = Reasoning(Mem()); r.apply_policy(w)
    u = {a.xapp_id: sum(getattr(r, f"w_{k}") * v for k, v in r._calculate_action_scores(a).items()) for a in (xs, eb)}
    print(name, round(u["xslice"] - u["embb_throughput"], 4))
```

Saída: −0,0125; −0,0108; +0,0925; +0,1292; +0,0042. Para o artigo, este cálculo deve entrar em `artigos/scripts/insights_complemento.py`, para que o número saia do script.

## Fontes

- Código F1: `src/core/reasoning.py`, `src/rdl_xapp.py` (`_apply_a1_policy`), `src/conflict_types.py`, `src/core/proposal_registry.py`, `src/closed_loop/hrdl_slice_loop.py`, `src/e2/v3/codec.py`, `rapps/greenran_resource_optimizer.py`, `scripts/certification/run_conflict_experiment.py`, `simulations/ns3/rdl-nr-common.h`, `simulations/ns3/conflicts/catalog.json`, `src/infrastructure/memory_module.py`.
- Código F2: `cardl/marl/calibration.py`, `cardl/marl/select.py`, `cardl/marl/mappo.py`, `cardl/calibration/slice_cap_curve_v5.json`.
- Dados: `artigos/dados/insights/p1_tvs_s8_decomposicao.csv`, `p1_tvs_s8_limiares.csv`, `p1_tvs_s8_sensibilidade.csv`, `p1_g5_s8_recalculado.csv`, `p2_calibracao_validacao_fora_amostra.csv` e `p2_lacuna_observacao.csv`; `docs/preregistros/07_campanha_g5_s8.md` (tabela de resultados); `docs/06` §5.4.
- Cálculos deste desenho: margens sob A1 (Apêndice A); fração do simplex (Monte Carlo com 2·10⁶ pontos); previsões do S8b pela curva v5 (`CapCurve.ratio`: 0,8763 em 35 %; 1,0 em 45 % e 55 %).
