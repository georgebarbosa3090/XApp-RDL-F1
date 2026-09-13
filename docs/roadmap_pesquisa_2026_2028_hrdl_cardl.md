# Programa e Roadmap Estratégico de Pesquisa (2026–2028)
## Evolução de H-RDL (Fase 1) a CA-RDL (Fase 2/3) — XApp-RDL

> **Projeto:** XApp-RDL (Resource and Decision Layer)  
> **Horizonte de Execução:** 24 Meses (Setembro de 2026 – Agosto/Setembro de 2028)  
> **Meta Global de Produção:** 7 a 9 Publicações Científicas de Alto Impacto (Nacionais, Internacionais e Periódicos IEEE)  
> **Meta de Interoperabilidade:**  
> $$\boxed{ H\text{-}RDL \longrightarrow CA\text{-}RDL \longrightarrow Cross\text{-}Backend \longrightarrow OpenRAN@Brasil }$$

---

## 1. Meta Global do Programa

Para transformar a linha de pesquisa **H-RDL $\rightarrow$ CA-RDL** em uma plataforma capaz de sustentar de 7 a 9 publicações científicas de alto impacto sem recorrer a *salami slicing* ou fragmentação artificial, o trabalho é estruturado como um programa experimental integrado. A base científica e experimental unificada serve a múltiplos trabalhos metodologicamente distintos.

### Matriz Quantitativa de Objetivos e Metas

| Meta | Alvo Quantitativo |
| :--- | :---: |
| **Conformidade técnica/científica H-RDL** | $\ge 95\%$ |
| **Conformidade técnica/científica CA-RDL** | $\ge 90\text{--}95\%$ |
| **Campanha total de simulação (Pareada)** | $\approx 2.000\text{--}2.500\text{ runs}$ |
| **Validações srsRAN/Open5GS/OpenRAN@Brasil** | $80\text{--}200\text{ runs}$ |
| **Cenários canônicos ($S_0$ a $S_{15}$)** | $16\text{ cenários}$ |
| **Publicações Nacionais (SBRC, SBrT, WGRS, WPEIF)** | $2\text{--}3\text{ artigos}$ |
| **Conferências Internacionais (CNSM, NOMS/IM, ICC, GLOBECOM)** | $2\text{--}4\text{ artigos}$ |
| **Periódicos Internacionais (IEEE TNSM, IEEE TCCN)** | $2\text{--}3\text{ journals}$ |
| **Demonstração / Ferramenta (Salão de Ferramentas SBRC/SBrT)** | $1\text{ artigo de ferramenta/demo}$ |
| **Produção total plausível** | **7 a 9 trabalhos acadêmicos** |

---

## 2. Definição Formal de "95% de Conformidade"

A conformidade do projeto é avaliada rigorosamente por uma matriz mensurável ponderada em 10 dimensões técnicas e normativas:

$$\text{Índice de Conformidade Globais (ICG)} = \sum_{i=1}^{10} w_i \cdot c_i$$

### Matriz Mensurável de Ponderação de Conformidade

| Dimensão | Peso ($w_i$) | Critério de Aceite para Pontuação Máxima ($c_i = 100\%$) |
| :--- | :---: | :--- |
| **Conformidade O-RAN normativa** | 15% | Perfil congelado H-RDL F1 (E2AP v02.03/v03.00, E2SM-KPM v03.00, E2SM-RC v01.03/v03.00) 100% verificado. |
| **E2AP/KPM/RC interoperability** | 15% | Codecs ASN.1 APER (`pycrate`) sem erros em golden vectors e round-trips. |
| **KPM externo real** | 10% | Gate 1 `PASS` ($g_1 \land \ldots \land g_7$ com `RICIndication` brutos externos do NORI/srsRAN). |
| **RC + ACK/Failure real** | 10% | Gate 3 `PASS` (emissão de `RICcontrolRequest` e decodificação de `RICcontrolAck` / `Failure`). |
| **Closed-loop causal** | 15% | Gate 4 `PASS` ($KPM(t_0) \rightarrow H\text{-}RDL \rightarrow RC \rightarrow ACK \rightarrow RANState \rightarrow KPM(t_1)$). |
| **Proveniência científica** | 10% | Zero dados sintéticos/mocks em resultados de publicação; firewall de proveniência ativado. |
| **Reprodutibilidade** | 10% | `versions.lock` congelado, hashes SHA-256 e script `make reproduce-f1` 100% determinístico. |
| **Cross-backend** | 5% | Validação equivalente entre `NORI_NS3` e `SRSRAN_OPEN5GS` no mesmo cenário lógico. |
| **CI, Safety e negative testing** | 5% | Suíte CI verde, 100% de aplicação dos *Safety Guards* físicos e testes negativos passados. |
| **Documentação/rastreabilidade** | 5% | Ausência de alegações prematuras (*claims*) e rastreabilidade total de requisitos. |
| **Total** | **100%** | |

> [!IMPORTANT]
> Para declarar a Fase 1 (H-RDL) próxima dos **95% de conformidade**, o projeto exige indispensavelmente:
> $$\boxed{ G_0=\text{PASS} \quad\land\quad G_1=\text{PASS} \quad\land\quad G_2=\text{PASS} \quad\land\quad G_3=\text{PASS} \quad\land\quad G_4=\text{PASS} \quad\land\quad G_5=\text{PASS} }$$
> Sem a conclusão dos Gates $G_1$, $G_3$ e $G_4$ com evidências externas brutas, o índice máximo declarável é L3+ (Local Integration avançada).

---

## 3. Estrutura e Escopo das Duas Fases

```text
H-RDL — Fase 1 (Deterministic + Safe)
   │
   ├─ Baseline Determinística
   ▼
CA-RDL — Fase 2 (Context-Aware + KG + MARL)
   │
   ▼
5G-Advanced / 6G (NTN / UAV / V2X / IIoT / ISAC)
```

- **Fase 1 (H-RDL) responde:**  
  *Como resolver colisões e conflitos multi-xApp de forma determinística, segura, transparente e normativamente compatível com a E2AP/E2SM?*
- **Fase 2 (CA-RDL) responde:**  
  *Como arbitrar e prever conflitos que dependem de contexto dinâmico, histórico de decisões, intenção de rede e interações não-lineares entre fatias e nós RAN?*

---

## 4. Roadmap Geral de Execução (2026–2028)

| Período | Objetivo Dominante | Entregáveis Principais |
| :--- | :--- | :--- |
| **Set–Out/2026** | **Congelar Arquitetura H-RDL F1** | Corrigir P0s (modo estrito RMR, backend explícito, `RICrequestID`, proveniência fail-closed). |
| **Nov–Dez/2026** | **Fechar Gates Externos ($G_1, G_3, G_4$)** | Capturas brutas APER, decodificação E2Term e prova causal em malha fechada ($L_5$). |
| **Jan–Fev/2027** | **Piloto Estatístico** | $120\text{ runs}$ piloto ($5\text{ seeds} \times 4\text{ baselines} \times 6\text{ cenários}$) para calibração. |
| **Mar–Abr/2027** | **Campanha H-RDL Completa** | Execução pareada de $1.080\text{ runs}$ ($30\text{ seeds} \times 4\text{ baselines} \times 9\text{ cenários}$). |
| **Mai–Jun/2027** | **Integração srsRAN / Open5GS** | Execução dos Gates $TB_0$ a $TB_8$ no testbed de software srsRAN + Open5GS. |
| **Jul–Ago/2027** | **Cross-Backend & Submissão Nacional** | Validação $NORI \leftrightarrow srsRAN$ + Escrita de papers nacionais (SBRC/WGRS/WPEIF). |
| **Set–Out/2027** | **CA-RDL Context Engine & KG** | Desenvolvimento do motor de contexto e Knowledge Graph de dependências RAN. |
| **Nov–Dez/2027** | **Integração MARL / MAPPO** | Integração do algoritmo MAPPO ao pipeline com *Safety Guards* como filtro inviolável. |
| **Jan–Fev/2028** | **Campanha Científica CA-RDL** | Execução pareada de $1.050\text{ runs}$ nos cenários avançados $S_9$ a $S_{15}$ (NTN/UAV/V2X/IIoT). |
| **Mar–Abr/2028** | **Estudos de Ablação e Generalização** | Avaliação $-Context$, $-KG$, $-MARL$, $-Safety$ e inferência cross-domain. |
| **Mai–Jun/2028** | **Submissões Internacionais F2** | Artigos para CNSM, NOMS/IM, ICC/GLOBECOM. |
| **Jul–Set/2028** | **Consolidação de Journals F1/F2** | Submissão dos artigos estendidos para IEEE TNSM e IEEE TCCN. |

---

## 5. Setembro–Outubro de 2026: Congelamento da Fase 1 (H-RDL Feature Freeze)

A meta desta etapa é eliminar todos os impedimentos apontados nas auditorias técnicas, congelando o núcleo H-RDL para receber apenas correções e validação experimental.

$$\boxed{\text{F1 Feature Freeze}}$$

### Definition of Done (DoD) do Congelamento

| Item | Resultado Esperado e Regra de Validação | Status |
| :--- | :--- | :---: |
| **Backend Explícito** | Em `RDL_MODE=O_RAN_INTEROP`, a variável `RAN_BACKEND` é obrigatória. Fallback silencioso desativado. | $\checkmark$ **CONFORME** |
| **Capability Discovery** | Renomeado para `register_static_profile_capabilities()`; ausência de auto-registro silencioso. | $\checkmark$ **CONFORME** |
| **Transaction Manager** | Gerenciamento de transações baseado na tupla `RICrequestID` `(requestor_id, instance_id, ran_function_id)`. | $\checkmark$ **CONFORME** |
| **ACK / Failure** | Decodificação física de APER `RICcontrolAcknowledge` e `RICcontrolFailure` via `correlate_ack()`. | $\checkmark$ **CONFORME** |
| **Subscription** | Suporte a subscrição via REST SubMgr (`/ric/v1/subscriptions`). | $\checkmark$ **CONFORME** |
| **KPM Externo** | Suporte a decodificação APER de indicações externas capturadas do E2Term. | $\checkmark$ **CONFORME** |
| **Proveniência Fail-Closed** | Scripts de auditoria retornam código 1 se fontes `NON_PUBLICATION` forem usadas em artigos. | $\checkmark$ **CONFORME** |
| **CI Software** | Pipeline local `CI-Software` 100% verde (58/58 testes). | $\checkmark$ **CONFORME** |
| **CI Scientific** | Pipeline `CI-Scientific-Readiness` separada e ativada por tags. | $\checkmark$ **CONFORME** |
| **Documentação** | Ajuste de alegações de homologação para "Perfil proposto para implantação no OpenRAN@Brasil". | $\checkmark$ **CONFORME** |

---

## 6. Novembro–Dezembro de 2026: Fechamento dos Gates Externos ($G_1, G_3, G_4$)

Demonstração prática dos 3 Gates de interoperabilidade com o simulador ns-3 + NORI ou srsRAN:

- **Gate 1 (Telemetria KPM):**  
  $$\text{E2 Setup} \longrightarrow \text{RAN Function} \longrightarrow \text{Subscription} \longrightarrow \text{RIC Indication APER} \longrightarrow \text{KPM Decoder}$$
- **Gate 3 (Controle E2SM-RC):**  
  $$\text{H-RDL} \longrightarrow \text{E2SM-RC} \longrightarrow \text{RICcontrolRequest APER} \longrightarrow \text{RAN} \longrightarrow \text{RICcontrolAcknowledge APER}$$
- **Gate 4 (Closed-Loop Causal):**  
  $$KPM(t_0) \longrightarrow \text{Conflito} \longrightarrow \text{H-RDL} \longrightarrow \text{Controle} \longrightarrow \text{ACK} \longrightarrow \Delta \text{Estado RAN} \longrightarrow KPM(t_1)$$

Ao final desta etapa, o objetivo é atingir o nível **L5 (External Interoperability Validated)** para pelo menos um cenário de referência.

---

## 7. O "Golden Scenario" de Interoperabilidade ($S_1$)

Para validar a interoperabilidade externa antes de expandir para os 16 cenários, é adotado um **Golden Scenario único**:

$$\boxed{S_1\ \text{--- Direct PRB Conflict}}$$

### Especificação Técnica do $S_1$:
- **xApp 1 (URLLC Slicing):** Solicita cota de $\text{PRB} = 75\%$.
- **xApp 2 (eMBB Slicing):** Solicita cota de $\text{PRB} = 80\%$.
- **Condição de Conflito Direto:** $75\% + 80\% = 155\% > 100\%$ do orçamento da célula.
- **Resultado Esperado:** O H-RDL intercepta a colisão, calcula a arbitragem determinística TVS/EEVS e emite uma decisão única e segura ($\text{PRB}_{\text{URLLC}} = 50\%$, $\text{PRB}_{\text{eMBB}} = 50\%$).
- **Execução Cross-Backend:** O mesmo payload de entrada deve ser testado sequencialmente em:
  1. `NORI_NS3` (ns-3.48 / 5G-LENA)
  2. `SRSRAN_OPEN5GS` (srsRAN Project + Open5GS)

---

## 8. Janeiro de 2027: Piloto Estatístico

Execução prévia de um piloto reduzido para identificar instabilidades, estouro de memória, vazamento de logs ou variações inesperadas de sementes antes do congelamento da campanha final:

$$\text{Total Piloto} = 5\ \text{seeds} \times 4\ \text{baselines} \times 6\ \text{cenários} (S_0, S_1, S_2, S_3, S_6, S_8) = \mathbf{120\ \text{runs}}$$

---

## 9. Fevereiro–Abril de 2027: Campanha H-RDL Definitiva (Fase 1)

### Baselines Comparativas Congeladas:
1. **$B_0$ (No Coordination):** Execução sem controle de conflito (colisão aberta).
2. **$B_1$ (FIFO Heuristic):** Atendimento por ordem de chegada sem priorização.
3. **$B_2$ (Static Partition):** Divisão rígida de recursos 50/50 sem adaptação dinâmica.
4. **$B_3$ (H-RDL Core):** Governança determinística H-RDL em lote de $200\text{ ms}$ com *Safety Guards*.

### Dimensionamento da Campanha H-RDL:
$$\text{Total F1} = 9\ \text{cenários } (S_0 \text{ a } S_8) \times 4\ \text{baselines } (B_0\text{--}B_3) \times 30\ \text{seeds pareadas} = \mathbf{1.080\ \text{runs}}$$

---

## 10. Metodologia de Design Pareado (Paired Design)

Para eliminar o viés de variação de canal de rádio e mobilidade entre as baselines, a campanha adota o **design pareado estrito**:

```text
Seed-1001 ──┬── B0 (No Control)       ── Configuração Física Idêntica
            ├── B1 (FIFO)             ── Posições UEs Idênticas
            ├── B2 (Static Partition) ── Canal 3GPP TR 38.901 Idêntico
            └── B3 (H-RDL)            ── Tráfego e Mobilidade Idênticos
```

A única variável independente permitida entre as execuções da mesma semente é:

$$\boxed{\text{Política de Coordenação / Governança}}$$

---

## 11. Conjunto Congelado de Métricas Científicas

| Dimensão | Métrica Primária | Unidade / Descrição |
| :--- | :--- | :--- |
| **Conflict Detection** | Precision, Recall, $F_1\text{-score}$ | Taxa de acerto na identificação de conflitos diretos/indiretos. |
| **Decision Speed** | $T_{\text{decision}}$ | Tempo de processamento interno do RDL ($\text{ms}$). |
| **Control Latency** | $T_{\text{control}}$ | Latência de codificação e envio E2SM-RC ($\text{ms}$). |
| **Closed-Loop Latency**| $T_{\text{loop}}$ | Tempo total $KPM(t_0) \rightarrow \text{Decisão} \rightarrow \text{ACK} \rightarrow KPM(t_1)$ ($\text{ms}$). |
| **QoS / Latência** | Latência P99 | Latência de entrega de pacotes no 99º percentil ($\text{ms}$). |
| **Capacidade** | Throughput AG | Vazão média agregada da célula ($\text{Mbps}$). |
| **Reliability** | PDR | Packet Delivery Ratio ($\%$). |
| **Fairness** | Índice de Jain | Equidade na distribuição de recursos entre fatias ($[0, 1]$). |
| **SLA Compliance** | SLA Violation Ratio | Porcentagem de violações dos contratos de serviço ($\%$). |
| **Conflict Resolution**| CRE | Conflict Resolution Efficiency ($\%$). |
| **Safety** | Unsafe Action Rate | Porcentagem de decisões que violaram *Safety Guards* ($\%$). |
| **Estabilidade** | Taxa de Oscilação / Ping-Pong | Frequência de alternância desnecessária de ações de controle. |

---

## 12. Protocolo Estatístico e Comparativo

Para cada métrica avaliada:
- Reportar: Média ($\mu$), Mediana, Desvio Padrão ($\sigma$), Percentis $P_{95}$ e $P_{99}$, e Intervalo de Confiança de 95% ($\text{IC}_{95\%}$).
- **Testes de Hipótese:** Para distribuições não-normais em amostras pareadas, utilizar o teste de **Wilcoxon Signed-Rank** com relatório de tamanho de efeito (*effect size* $r$).
- **Ajuste para Múltiplas Comparações:** Aplicar a correção de **Holm-Bonferroni** para evitar inflação do Erro Tipo I.

---

## 13. Validação Cross-Backend ($NORI \leftrightarrow srsRAN$)

A validação cross-backend compara a consistência da decisão lógica entre o ambiente de simulação e o testbed de software:

$$\text{Premissa de Consistência:} \quad \text{Decision}_{\text{NORI}}(S_1) \equiv \text{Decision}_{\text{srsRAN}}(S_1)$$

### Dimensionamento de Runs no Testbed srsRAN:
- 3 Baselines ($B_0, B_2, B_3$) em 3 Cenários Chave ($S_1, S_3, S_8$) $\times 10\text{ repetições}$.
- Total: $3 \times 3 \times 10 = 90\text{ runs}$ (expandido para $100\text{--}150\text{ runs}$ com calibrações).

---

## 14. Arquitetura Científica da Fase 2 (CA-RDL)

A Fase 2 introduz a consciência de contexto sem violar as garantias determinísticas da Fase 1:

```text
Entrada KPM / Estado RAN
       │
       ▼
┌─────────────────────────┐
│     Context Engine      │ ── Agrega histórico, SLAs, mobilidade e estado energético
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Knowledge Graph     │ ── Mapeia dependências implícitas (Ação -> KPI -> SLA -> Slice)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       MARL / MAPPO      │ ── Propõe ações otimizadas de longo prazo
└────────────┬────────────┘
             │ (Propostas)
             ▼
┌─────────────────────────┐
│      Safety Guards      │ ── Filtro Inviolável (Clamping / Limites Físicos H-RDL)
└────────────┬────────────┘
             │ (Ações Autorizadas)
             ▼
      Nó E2 / srsRAN
```

$$\boxed{\text{MARL Proposes} \longrightarrow \text{Refinement Validates} \longrightarrow \text{Safety Guards Authorize} \longrightarrow \text{RAN Executes}}$$

---

## 15. Campanha Experimental da Fase 2 (CA-RDL)

### Cenários Avançados ($S_9$ a $S_{15}$):
- **$S_9$ (NTN Satellite Handover):** Conflitos de steering entre feixes LEO e célula terrestre.
- **$S_{10}$ (UAV Aerial Relay):** Trajetória e energia de drones vs vazão de cobertura.
- **$S_{11}$ (V2X High Mobility):** Handover e alocação de PRB em alta velocidade veicular.
- **$S_{12}$ (IIoT Co-existence):** Ultra-latência industrial em ambientes densos.
- **$S_{13}$ (SAGIN Multi-tier):** Orquestração entre camadas terrestre, aérea e espacial.
- **$S_{14}$ (ISAC Sensing vs Comms):** Conflito entre feixes de sensoriamento e comunicação.
- **$S_{15}$ (Security Anomaly Mitigation):** Mitigação de ataques xApp desonesta.

### Dimensionamento da Campanha CA-RDL:
$$\text{Total F2} = 7\ \text{cenários } (S_9 \text{ a } S_{15}) \times 5\ \text{configurações} \times 30\ \text{seeds pareadas} = \mathbf{1.050\ \text{runs}}$$

$$\text{Volume Total do Programa (F1 + F2)} = 1.080 + 1.050 = \mathbf{2.130\ \text{runs pareados}}$$

---

## 16. Portfólio de 9 Publicações Científicas Mapeadas (P1 a P9)

| ID | Título Conceitual do Trabalho | Foco Metodológico | Alvo Principal | Período |
| :---: | :--- | :--- | :--- | :---: |
| **P1** | *H-RDL: Deterministic and Safe Multi-xApp Conflict Governance for O-RAN Near-RT RIC* | Arquitetura F1, taxonomia de conflito, raciocínio determinístico e testes $S_0\text{--}S_7$. | **WGRS / SBRC 2027** | Q2/2027 |
| **P2** | *Standards-Compliant Closed-Loop Multi-xApp Conflict Resolution in O-RAN Using H-RDL* | Interoperabilidade E2, SubMgr, E2SM-RC ACK/Failure e latência de closed-loop ($S_8$). | **SBRC / CNSM 2027** | Q2/2027 |
| **P3** | *H-RDL Tool: An Open-Source Framework for O-RAN Conflict Governance and Co-Simulation* | Demonstração prática, repositório de ferramenta, artefatos Docker e scripts de reprodução. | **Salão de Ferramentas SBRC / SBrT** | Q2/2027 |
| **P4** | *Cross-Backend Validation of Deterministic Multi-xApp Conflict Governance in O-RAN* | Validação experimental comparativa entre `NORI_NS3` e `SRSRAN_OPEN5GS`. | **IEEE/IFIP NOMS / IM / CNSM** | Q3/2027 |
| **P5** | *H-RDL: A Deterministic, Safe, and Standards-Compliant Governance Layer for O-RAN Near-RT RIC* | Versão estendida de periódico completa ($1.080\text{ runs}$, cross-backend, ablação e testbed). | **IEEE TNSM** | Q4/2027 |
| **P6** | *Context-Aware Conflict Detection in O-RAN Using Knowledge Graphs* | Motor de contexto, Knowledge Graph de dependências e resolução de conflitos indiretos. | **SBRC / CNSM 2028** | Q1/2028 |
| **P7** | *Multi-Agent Reinforcement Learning for Safe Context-Aware Conflict Governance in O-RAN* | Algoritmo MAPPO integrado aos *Safety Guards* determinísticos. | **IEEE/IFIP NOMS / CNSM / ICC** | Q2/2028 |
| **P8** | *Context-Aware Conflict Governance for 5G-Advanced and 6G Non-Terrestrial and Vehicular Networks* | Generalização da CA-RDL para cenários $S_9\text{--}S_{15}$ (NTN, UAV, V2X, ISAC). | **SBrT / IEEE GLOBECOM** | Q3/2028 |
| **P9** | *CA-RDL: Context-Aware Autonomous Multi-Agent Governance for 5G-Advanced and 6G O-RAN* | Periódico consolidado completo da Fase 2 (MAPPO, KG, generalização, ablação e escalabilidade). | **IEEE TCCN / Computer Networks** | Q3/2028 |

---

## 17. Critérios de Go/No-Go para Submissão de Artigos

```text
Nível 1: Validação Local / Unitária
  └── Proibido publicar como resultado O-RAN final (apenas notas internas).

Nível 2: Telemetria KPM Externa (Gate 1 PASS)
  └── Elegível para Workshops preliminares (WGRS / WPEIF).

Nível 3: Closed-Loop Externo com ACK (Gates 1, 3, 4 PASS)
  └── Elegível para Conferências Nacionais / Internacionais (SBRC, SBrT, CNSM).

Nível 4: Multi-Semente + Cross-Backend + Testbed (Gates 0-5 PASS)
  └── Elegível para Conferências Internacionais Principais e Periódicos (IEEE TNSM, IEEE TCCN).
```

---

## 18. Matriz Final de Execução e Dependências

$$\boxed{ \text{F1 Freeze} \rightarrow G_1 \rightarrow G_3 \rightarrow G_4 \rightarrow \text{Piloto} \rightarrow 1.080\text{ Runs} \rightarrow \text{Paper F1} \rightarrow \text{srsRAN} \rightarrow \text{Cross-Backend} \rightarrow \text{IEEE TNSM} }$$

$$\boxed{ \text{Context Engine} \rightarrow \text{Knowledge Graph} \rightarrow \text{MAPPO} \rightarrow 1.050\text{ Runs} \rightarrow \text{Ablation} \rightarrow \text{Generalization} \rightarrow \text{IEEE TCCN} }$$

---

### Referências Normativas e Científicas de Apoio
1. **O-RAN Alliance WG2 & WG3 Specifications:** E2AP v02.03/v03.00, E2SM-KPM v03.00, E2SM-RC v01.03/v03.00.
2. **IEEE Transactions on Network and Service Management (TNSM):** *Policies and Guidelines for Extended Conference Papers.*
3. **IEEE Transactions on Cognitive Communications and Networking (TCCN):** *Scope on Cognitive, Learning, and Autonomous RAN.*
4. **OpenRAN@Brasil Blueprint v3:** Especificações de testbed e integração de ilhas físicas.
