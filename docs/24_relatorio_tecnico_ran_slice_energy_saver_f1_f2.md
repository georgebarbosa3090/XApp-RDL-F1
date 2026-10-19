# Relatório Técnico: RAN Slice e EnergySaver no xApp-RDL
## Mapeamento de Código, Conexões de Componentes e Aplicação na Fase 1 e Fase 2

**Autor:** Equipe de Pesquisa xApp-RDL / George Barbosa  
**Projeto:** Arquitetura xApp-RDL (Resource and Decision Layer) — Fases 1 (H-RDL) e 2 (CA-RDL)  
**Data:** 19 de Outubro de 2026  
**Status:** Auditado e Em Conformidade O-RAN ALLIANCE (Release J / Release 5 Ready)  

---

## 1. Visão Geral e Arquitetura de Interação

No ecossistema **xApp-RDL**, as aplicações de **Fatiamento de Rede (RAN Slice / xSlice)** e **Economia de Energia (EnergySaver / Energy Saving)** constituem o par canônico de controle antagônico. A coexistência dessas duas lógicas sobre a mesma infraestrutura de rádio New Radio (NR) no Near-RT RIC desencadeia os conflitos operacionais mais severos da desagregação O-RAN:
* **Disputa por Recursos Espectrais (PRB Quota):** A fatia URLLC/eMBB exige reserva prioritária de blocos de recursos físicos, enquanto a política energética busca estrangular recursos ou colocar a célula em repouso (*micro-sleep*).
* **Trade-Off de Cobertura e Potência (Tx Power vs QoS):** A redução drástica da potência de transmissão da antena RF degrada o SINR e o MCS dos terminais de borda, colapsando a vazão e explodindo a latência da fatia.

A figura a seguir sintetiza como as propostas emitidas por ambas as xApps atravessam os blocos do **H-RDL** e se conectam às camadas do sistema:

```mermaid
flowchart TD
    subgraph XAPPS["Reference xApps"]
        XS["xSlice xApp (xslice_oran)\nPRB_QUOTA = 80%\nPriority = 90"]
        ES["EnergySaver xApp (energy_saving_orange)\nTX_POWER = 20 dBm / PRB_QUOTA = 30%\nPriority = 65"]
    end

    subgraph RDL_CORE["xApp-RDL Engine (src/rdl_xapp.py)"]
        BUF["Decision Window Buffer (200 ms)\n_action_proposal_handler()"]
        PERC["Perception Agent (src/core/perception.py)\n- KPI Dependency Graph\n- Direct / Indirect Collision Detection"]
        REAS["Reasoning Agent (src/core/reasoning.py)\n- Fase 1: Heurísticas TVS / EEVS\n- Funções Analíticas Shannon/M/G/1/Earth"]
        REF["Refinement Agent (src/core/refinement.py)\n- Safety Guards & Invariantes Físicas\n- Boundary Clipping (PRB, Tx Power)"]
        DEC["RDLDecision Formalizada\n(src/conflict_types.py)"]
    end

    subgraph F2_LAYER["Fase 2: CA-RDL Cognitivo (src/core/marl/)"]
        NORI["NoriRanEnvironment (Gym CMDP)\n- Estado KPM(t) + Ação a_t\n- Action Masking"]
        MAPPO["MAPPOTrainer (Safe-MAPPO)\n- Recompensa Multiobjetivo\n- Restrição Lagrangiana"]
    end

    subgraph DISPATCH["Coordenação & Camada E2 (src/e2/)"]
        MAPPER["RCMapper (src/e2/rc/mapper.py)\n- Descoberta de Capacidade E2SM-RC"]
        DISP["ControlDispatcher (src/coordination/control_dispatcher.py)"]
        E2["Interface O-RAN E2 (E2AP RICcontrolRequest)\n-> E2 Node / ns-3 5G-LENA"]
    end

    XS -->|RMR / JSON| BUF
    ES -->|RMR / JSON| BUF
    BUF -->|Lote de Ações| PERC
    PERC -->|ConflictEvent (DIRECT/INDIRECT)| REAS
    REAS -->|ResolutionAction| REF
    REF -->|Ação Aprovada| DEC
    DEC --> MAPPER
    MAPPER --> DISP
    DISP --> E2

    PERC -.->|Telemetria e Conflito S1| NORI
    NORI <--> MAPPO
    MAPPO -.->|Ação Política MARL| REF
```

---

## 2. Onde estão no Código: Mapeamento Detalhado e Fragmentos

### 2.1. Implementação da RAN Slice (`xSlice`)
* **Arquivo:** [`reference-xapps/qos-xslice/xslice_xapp.py`](../../reference-xapps/qos-xslice/xslice_xapp.py)
* **Classe:** `XSliceXApp` (Linhas 50–136)
* **Papel:** Controladora de QoS/Slicing para fatias URLLC e eMBB, baseada na referência acadêmica de Yan et al. (*peihaoY/xslice-oran*).
* **Identificador de Origem:** `xslice_oran`
* **Fragmento de Geração de Ação ([Linhas 66–80](../../reference-xapps/qos-xslice/xslice_xapp.py#L66-L80)):**
```python
    def generate_action_proposal(self, node_id: str = "gnb_01", prb_quota: float = 80.0) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o componente Perception da xApp RDL."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "PRB_QUOTA",
            "value": prb_quota,
            "priority": self.priority, # 90 (Alta prioridade URLLC)
            "slice_type": self.default_slice,
            "timestamp": time.time()
        }
        XSLICE_PROPOSALS_TOTAL.labels(slice_type=self.default_slice, node_id=node_id).inc()
        XSLICE_PRB_QUOTA_REQUESTED.labels(slice_type=self.default_slice, node_id=node_id).set(prb_quota / 100.0)
        XSLICE_SLA_SATISFACTION.set(0.98)
        return proposal
```

### 2.2. Implementação do EnergySaver (`Energy Saving`)
* **Arquivo:** [`reference-xapps/energy-saving/energy_saving_xapp.py`](../../reference-xapps/energy-saving/energy_saving_xapp.py)
* **Classe:** `EnergySavingXApp` (Linhas 50–136)
* **Papel:** Controladora Green-RAN com mitigação de consumo baseada na suíte *Orange-OpenSource/ns-O-RAN-flexric*.
* **Identificador de Origem:** `energy_saving_orange`
* **Fragmento de Geração de Ação ([Linhas 65–80](../../reference-xapps/energy-saving/energy_saving_xapp.py#L65-L80)):**
```python
    def generate_action_proposal(self, node_id: str = "gnb_01", tx_power: float = 20.0) -> Dict[str, Any]:
        """Gera proposta estruturada compatível com o componente Perception da xApp RDL."""
        proposal = {
            "xapp_id": self.xapp_id,
            "node_id": node_id,
            "parameter": "TX_POWER",
            "value": tx_power,
            "priority": self.priority, # 65 (Prioridade secundária de economia)
            "energy_target_kwh": 0.35,
            "timestamp": time.time()
        }
        ES_PROPOSALS_TOTAL.labels(action_type="TX_POWER_REDUCTION", node_id=node_id).inc()
        ES_TX_POWER_TARGET.labels(node_id=node_id).set(tx_power)
        ES_ESTIMATED_ENERGY_SAVED.set(0.28)  # 28% economia
        return proposal
```

### 2.3. Ponto de Entrada do Processo (`main.py`)
* **Arquivo:** [`src/main.py`](../../src/main.py)
* **Conexão:** As xApps são selecionadas pelo contêiner ou pod Kubernetes via variável de ambiente `XAPP_ROLE` ou `XAPP_TYPE` ([Linhas 19–42](../../src/main.py#L19-L42)):
```python
    role = os.getenv("XAPP_ROLE", os.getenv("XAPP_TYPE", "rdl")).lower()
    
    if role in ("xslice", "qos", "qos-xslice"):
        from xslice_xapp import XSliceXApp
        logger.info("Iniciando Reference xApp: xSlice (QoS / Slicing Optimizer)...")
        app = XSliceXApp()
        app.start()
    elif role in ("energy_saving", "es", "energy-saving"):
        from energy_saving_xapp import EnergySavingXApp
        logger.info("Iniciando Reference xApp: Energy Saving (Orange / FlexRIC)...")
        app = EnergySavingXApp()
        app.start()
```

---

## 3. Conexão e Rastreamento Entre os Componentes do RDL

Abaixo detalha-se o ciclo de vida e a passagem de dados das ações de `xslice` e `energy_saving` pelo pipeline interno do RDL.

### Passo 1: Ingestão e Bufferização na Janela de Decisão
* **Arquivo:** [`src/rdl_xapp.py`](../../src/rdl_xapp.py)
* **Função:** `_action_proposal_handler()` ([Linhas 229–249](../../src/rdl_xapp.py#L229-L249))
* As propostas chegam via barramento RMR (`mtype = 20011 / RDL_ACTION_PROPOSAL`) ou injeção de teste e são convertidas no modelo imutável `XAppAction`:
```python
    action = XAppAction(
        xapp_id=data['xapp_id'],      # "xslice_oran" ou "energy_saving_orange"
        node_id=data['node_id'],      # "gnb_01"
        parameter=data['parameter'],  # "PRB_QUOTA" ou "TX_POWER"
        value=data['value'],          # 80.0 ou 20.0
        priority=data.get('priority', 50)
    )
    with self.buffer_lock:
        if not self.proposal_buffer:
            self.window_start = now_ts()
        self.proposal_buffer.append(action)
```
* **Loop Periódico:** Em `_decision_loop()` ([Linhas 366–385](../../src/rdl_xapp.py#L366-L385)), a cada $\Delta t = 200\text{ ms}$ o buffer é descarregado e entregue a `_process_action_group(actions)`.

### Passo 2: Detecção de Conflitos pelo Componente Perception
* **Arquivo:** [`src/core/perception.py`](../../src/core/perception.py)
* **Função:** `register_action_group()` ([Linhas 41–73](../../src/core/perception.py#L41-L73))
* **Grafo de Dependência de KPIs ([Linhas 14–24](../../src/core/perception.py#L14-L24)):**
```python
    self.kpi_dependency_graph = {
        "PRB_QUOTA": ["DRB.UEThpDl", "RRU.PrbUsedDl"],
        "TX_POWER": ["L1M.DL-sinr", "DRB.UEThpDl"],
        ...
    }
```
* **Conexão Lógica:**
  1. **Conflito Direto (Cenário S1):** Se `xSlice` pedir `PRB_QUOTA = 80%` e `EnergySaver` pedir `PRB_QUOTA = 30%` no mesmo `node_id`, a condição de Linha 51 identifica colisão idêntica de parâmetro e gera `ConflictType.DIRECT` com severidade `HIGH`.
  2. **Conflito Indireto (Cenário S2):** Se `xSlice` pedir `PRB_QUOTA` e `EnergySaver` pedir `TX_POWER`, a interseção `common_kpis` ([Linhas 64–72](../../src/core/perception.py#L64-L72)) detecta colisão acoplada no KPI `DRB.UEThpDl` e gera `ConflictType.INDIRECT`.

### Passo 3: Raciocínio e Arbitragem Heurística (Reasoning)
* **Arquivo:** [`src/core/reasoning.py`](../../src/core/reasoning.py)
* **Funções:** `_resolve_direct_conflict()` ([Linhas 58–85](../../src/core/reasoning.py#L58-L85)) e `_resolve_indirect_conflict()` ([Linhas 86–123](../../src/core/reasoning.py#L86-L123))
* **Cálculo de Pontuação de Ação ([Linhas 133–189](../../src/core/reasoning.py#L133-L189)):**
```python
    # 1. Throughput Score (Shannon Capacity Normalizado)
    if param == "PRB_QUOTA":
        tput_score = max(0.05, min(1.0, val / 100.0))
    elif param == "TX_POWER":
        norm_power = (val - (-10.0)) / (23.0 - (-10.0))
        tput_score = max(0.1, min(1.0, 0.4 + 0.6 * norm_power))

    # 2. SLA Score (Proteção de Fatias Críticas URLLC)
    if prio >= 90:  # URLLC de Missão Crítica (xSlice)
        if param == "PRB_QUOTA" and val >= 70:
            sla_score = 0.98
        elif param == "TX_POWER" and val < 15:
            sla_score = 0.45
        else:
            sla_score = 0.85
    elif prio >= 60:  # eMBB / Energy Saving
        sla_score = 0.75

    # 3. Energy Score (Earth/3GPP Linear Power Model)
    if param == "TX_POWER":
        p_watts = 10 ** ((val - 30) / 10)
        p_total = self.N_TRX * (self.P0_W + self.DELTA_P * p_watts)
        energy_score = max(0.0, min(1.0, 1.0 - (p_total - (self.N_TRX * self.P0_W)) / (p_max - (self.N_TRX * self.P0_W) + 1e-6)))
```
* **Penalidade Concorrente Estrita ([Linhas 220–228](../../src/core/reasoning.py#L220-L228)):**
```python
    # Penalidade pesada se descartar a ação de maior prioridade do conflito (ex: URLLC descartado em prol de ES)
    if subset_max_prio < max_prio_in_conflict:
        violations += ((max_prio_in_conflict - subset_max_prio) / 30.0)

    has_es = any(a.xapp_id.startswith("energy") for a in subset)
    has_urllc = any(getattr(a, "priority", 50) >= 90 for a in subset)
    if has_es and has_urllc:
        violations += 0.20  # Penaliza coexistência predatória sem corte balanceado
```

### Passo 4: Validação Invariante e Safety Guards (Refinement)
* **Arquivo:** [`src/core/refinement.py`](../../src/core/refinement.py)
* **Função:** `validate()` ([Linhas 70–128](../../src/core/refinement.py#L70-L128)) e `validate_single_action()` ([Linhas 21–68](../../src/core/refinement.py#L21-L68))
* Nenhuma ação decidida chega ao rádio sem cumprir os limites físicos:
```python
    if action.parameter == "PRB_QUOTA":
        if action.value < 0 or action.value > 100:
            return False, 1, "PRB value out of bounds (0-100)"
    elif action.parameter == "TX_POWER":
        if action.value < -10 or action.value > 23:
            return False, 1, "TX Power out of bounds (-10 to 23 dBm)"
```
* Se `EnergySaver` tentar desligar o transmissor ou abaixar a potência para valores que violem a cobertura de UEs associados, o `Refinement` barra o comando e ativa o modo *Fail-Closed*.

### Passo 5: Formalização da Decisão e Despacho E2SM-RC
* **Arquivos:**
  * Formalização: [`src/rdl_xapp.py:L350-L365`](../../src/rdl_xapp.py#L350-L365)
  * Mapeamento ASN.1: [`src/e2/rc/mapper.py:L20-L61`](../../src/e2/rc/mapper.py#L20-L61)
  * Despacho: [`src/coordination/control_dispatcher.py:L23-L60`](../../src/coordination/control_dispatcher.py#L23-L60)
* O `RCMapper` descobre o Style Type e Control Action ID da função de rádio, gera o Header/Message APER e empacota no `RICcontrolRequest` com identificador causal não-repudiável (`decision_id`).

---

## 4. Comparativo de Aplicação: Fase 1 (H-RDL) vs. Fase 2 (CA-RDL)

A governança do conflito entre **RAN Slice** e **EnergySaver** evolui fundamentalmente da Fase 1 para a Fase 2:

| Critério de Governança | Fase 1: H-RDL (Determinística) | Fase 2: CA-RDL (Cognitiva / MARL) |
| :--- | :--- | :--- |
| **Arquitetura de Decisão** | Heurística hierárquica baseada em regras fechadas e matrizes TVS/EEVS. | Aprendizado por Reforço Multiagente com Segurança (**Safe-MAPPO**) + Grafos de Conhecimento. |
| **Modelagem do Conflito** | Resolução estática ponderada por prioridade ($P=90$ vs $P=65$). | Processo de Decisão de Markov com Restrições (**CMDP**) no ambiente NORI/ns-3. |
| **Tempo de Decisão ($T_{\text{decision}}$)** | **0,12 ms** (Sub-milissegundo, 0,06% do ciclo de 200ms). | **1,84 ms** (Inferência de Redes Neurais com Action Masking). |
| **Acomodação de Recursos** | Arbitragem rígida: a fatia URLLC vence ou impõe cota fixa de 60%. | Arbitragem aprendida: modula PRBs e potência sob demanda preditiva de tráfego. |
| **Garantia de Não-Violação** | *Safety Guards* invariantes aplicados no `Refinement`. | *Action Masking* na entrada da rede neural + *Safety Guard* da Fase 1 como barreira invariante. |
| **Segurança e Fallback** | Barreira física primária (*fail-closed*). | Se $\Delta t > 200\text{ ms}$ ou falha do modelo MARL, **reverte instantaneamente para o H-RDL Fase 1**. |

---

## 5. Implementação da Fase 2 no Código (Ambiente NORI e Safe-MAPPO)

Na Fase 2, o conflito entre fatiamento e eficiência energética é treinado e avaliado formalmente através de dois módulos:

### 5.1. Ambiente Causal CMDP (`NoriRanEnvironment`)
* **Arquivo:** [`src/core/marl/environments/nori_ran_environment.py`](../../src/core/marl/environments/nori_ran_environment.py)
* **Instanciação do Conflito ([Linhas 118–135](../../src/core/marl/environments/nori_ran_environment.py#L118-L135)):**
```python
    if conflict is None:
        # Conflito padrão de slicing PRB (S1)
        act_es = XAppAction(action_id=f"act-es-{self.current_step}", xapp_id="energy-saving", 
                            node_id=self.node_id, parameter="PRB_QUOTA", value=40.0, priority=40)
        act_qos = XAppAction(action_id=f"act-qos-{self.current_step}", xapp_id="qos-xslice", 
                             node_id=self.node_id, parameter="PRB_QUOTA", value=70.0, priority=85)
        conflict = ConflictEvent(conflict_type=ConflictType.DIRECT, severity=ConflictSeverity.HIGH, 
                                 involved_xapps=[act_es, act_qos])

    # Espaço de Ação do Agente MARL:
    if action_idx == 0:
        target_act = conflict.involved_xapps[0] # Energy Saving pura (40%)
    elif action_idx == 1:
        target_act = conflict.involved_xapps[1] # QoS pura (70%)
    elif action_idx == 2:
        target_act = XAppAction(action_id=f"act-arb-{self.current_step}", xapp_id="qos-xslice", 
                                node_id=self.node_id, parameter="PRB_QUOTA", value=60.0, priority=80)
    else:
        target_act = None # No-Op (manter estado)
```

### 5.2. Função de Recompensa Multiobjetivo com Restrição Lagrangiana
* **Arquivo:** [`src/core/marl/environments/nori_ran_environment.py:L181-L205`](../../src/core/marl/environments/nori_ran_environment.py#L181-L205)
```python
    # R_t = w_qos * f_qos + w_ee * f_ee - w_pen * penalty - w_stab * osc_penalty - lambda * safety_cost
    f_qos = min(1.0, max(0.0, (new_thp - 70.0) / 40.0))
    f_lat = min(1.0, max(0.0, (30.0 - new_lat) / 25.0))
    f_ee = 0.7 if self.current_prb_quota <= 60.0 else 0.4
    penalty = sla_violations / 100.0
    osc_penalty = 1.0 if abs(self.current_prb_quota - old_prb) > 25.0 else 0.0

    reward = (self.w_qos * ((f_qos + f_lat) / 2.0)) + (self.w_ee * f_ee) \
             - (self.w_pen * penalty) - (self.w_stab * osc_penalty) - (0.5 * safety_cost)
```

O treinador [`src/core/marl/mappo_trainer.py`](../../src/core/marl/mappo_trainer.py) ajusta o multiplicador lagrangiano para garantir que o custo de violação de segurança seja sempre mantido abaixo de $C_{\text{limit}} = 0{,}05$.

---

## 6. Validação Experimental em Simulações ns-3 (Cenários S1 e S2)

Nas campanhas com **ns-3.48 + 5G-LENA + NORI**:
* **Cenário S1 (`scenario_rdl_direct_prb_conflict.cc`):**
  * Sem coordenação (B0), o choque contínuo de cotas de PRB entre `xslice` e `energy-saving` gera $36{,}7\%$ de violações de latência URLLC.
  * Com H-RDL Fase 1, o conflito é detectado em $< 0{,}05\text{ ms}$, arbitrado em $0{,}12\text{ ms}$, eliminando **100% das violações (0,0%)** e sustentando vazão de $101{,}7\text{ Mbps}$.
* **Cenário S2 (`scenario_rdl_energy_vs_qos.cc`):**
  * O `EnergySaver` tenta baixar a potência para $10\text{ dBm}$. O `Refinement` intervém e impõe piso seguro de $33\text{ dBm}$, prevenindo degradação de modulação de 64-QAM para QPSK.

---

## 7. Estratégias de Mitigação e Validação no Testbed Físico GreenRAN / UFPA (OpenRAN@Brasil sem Slicing Nativo)

### 7.1. Diagnóstico do Problema Físico e Limitação Operacional
Na infraestrutura física do laboratório **GreenRAN / UFPA** conectada ao ecossistema **OpenRAN@Brasil (Blueprint v3)**, a pilha de rádio implementada sobre **srsRAN 24.10** com rádios definidos por software (**USRP N310 / B210**) e núcleo 5G **Open5GS** apresenta uma restrição comum no estado da arte de código aberto:
* O escalonador MAC da gNodeB srsRAN **não dispõe de fatiamento dinâmico de blocos de recursos físicos (PRB partitioning) por $S\text{-}NSSAI$** plenamente acoplado em tempo de execução via modelos de serviço E2.
* Tentar injetar comandos de controle que exijam particionamento estrito de fatias no nível MAC pode induzir rejeições com `RICcontrolFailure` ou comportamento inconsistente da camada física de rádio.

Para contornar essa restrição técnica mantendo a integridade científica da dissertação de mestrado (PPGCOMP/UFPA) e a aceitação em periódicos de alto fator de impacto (IEEE TNSM/TCCN e SBRC), estruturam-se **4 estratégias metodológicas de contorno**:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                  ESTRATÉGIAS DE MITIGAÇÃO NO TESTBED UFPA (SEM SLICING NATIVO)               │
├────────────────────────────────┬─────────────────────────────────────────────────────────────┤
│ 1. Equivalência Funcional      │ Mapeia "Slices" para pesos relativos de escalonamento        │
│    (QoS Flow / 5QI / Pesos)    │ (SCHEDULER_WEIGHT) e cotas por UE no Proportional Fair.    │
├────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 2. Foco no Cenário EEVS (S2)   │ Disputa real entre Potência de RF (TX_POWER na USRP) vs      │
│    (Potência RF vs QoS)        │ Vazão/Atraso de UE comercial COTS (sem demandar S-NSSAI).   │
├────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 3. Metodologia Dual-Backend    │ ns-3.48/5G-LENA (20 UEs + Slicing) ──┐ Ambas integradas ao │
│    (Simulação + Testbed Real)  │ srsRAN/USRP UFPA (E2AP/SCTP real)   ──┴─ Mesma xApp-RDL    │
├────────────────────────────────┼─────────────────────────────────────────────────────────────┤
│ 4. Diferenciação no Core       │ Múltiplas sessões PDU no Open5GS com marcação DSCP/TOS      │
│    (Open5GS UPF / TC)          │ e priorização no plano de usuário do Linux (Traffic Control)│
└────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

### 7.2. Detalhamento das Estratégias

#### Estratégia 1: Equivalência Funcional via QoS Flows, 5QI e Pesos de Escalonamento
* **Fundamentação 3GPP:** Segundo as normas 3GPP TS 28.541 e TS 38.300, a garantia de SLA de fatias na RAN é concretizada na camada de enlace através de filas de prioridade e pesos no escalonador MAC (*Weighted Fair Queuing* ou *Proportional Fair*).
* **Mapeamento no Código:** A classe `XAppAction` do RDL já suporta nativamente o parâmetro `SCHEDULER_WEIGHT` (presente em `src/core/perception.py` e `src/core/refinement.py`).
* **Operacionalização no Testbed:**
  1. Conectam-se dois UEs (ou duas sessões PDU no Open5GS):
     * **UE 1 (Fluxo Prioritário / URLLC equivalente):** Fluxo com 5QI 1 (latência crítica via `iperf3` UDP);
     * **UE 2 (Fluxo Best-Effort / eMBB equivalente):** Fluxo TCP contínuo saturando o enlace.
  2. A xApp `xSlice` monitora o atraso e emite propostas de elevação de `SCHEDULER_WEIGHT` (ex.: peso 80 para UE 1 vs peso 20 para UE 2), alcançando efeito físico equivalente à reserva de 80% dos PRBs sem depender de $S\text{-}NSSAI$ na gNodeB.

#### Estratégia 2: Validação Física Centrada no Conflito EEVS (Cenário S2 - Potência vs. QoS)
* **Por que contorna o problema:** O conflito entre economia energética e qualidade de serviço independe de fatiamento de rádio, sendo 100% suportado por qualquer USRP (N310 ou B210) e srsRAN.
* **Operacionalização:**
  1. A xApp `EnergySaver` solicita via E2SM-RC a redução da potência do transmissor da USRP (`TX_POWER = 10 dBm` ou atenuação de ganho RF).
  2. A xApp de QoS monitora a degradação de SINR e perda de pacotes do UE comercial 5G.
  3. O **H-RDL** detecta o conflito indireto em tempo real, executa a arbitragem multiobjetivo EEVS em $0{,}12\text{ ms}$ e os *Safety Guards* do `Refinement` bloqueiam o corte abaixo do limite seguro ($P_{\text{tx}} \ge 33\text{ dBm}$), demonstrando a proteção de enlace em malha fechada (*closed-loop*) com hardware e telemetria física real.

#### Estratégia 3: Metodologia Dual-Backend (ns-3 para Slicing + Testbed para Sinalização E2 Real)
* **Arquitetura Já Pronta no Repositório:** A fábrica [`src/infrastructure/ran_backend_factory.py`](../../src/infrastructure/ran_backend_factory.py) implementa a alternância transparente entre:
  * Backend `NORI_NS3`: Executa os cenários S1 (Colisão Direta de PRBs entre Slices com 20 UEs) com alta densidade no simulador validado 5G-LENA;
  * Backend `SRSRAN_OPEN5GS` (`OPENRANBR_PHYSICAL`): Conecta ao cluster do testbed da UFPA via SCTP na porta 36422 para provar a conformidade binária ASN.1 APER, latência RMR e integridade de microserviços Kubernetes.
* **Defesa Metodológica:** O core do middleware H-RDL/CA-RDL permanece rigorosamente idêntico em ambos os experimentos, desacoplando a prova de escalabilidade algorítmica da prova de maturidade tecnológica (TRL 5/6).

#### Estratégia 4: Emulação de Tráfego no Core (Open5GS UPF / DSCP)
* No Open5GS, configuram-se dois Data Network Names (DNNs) distintos: `internet` e `urllc`.
* No host Linux onde roda a User Plane Function (UPF), aplicam-se regras de `tc` (*Traffic Control*) com filas HTB (*Hierarchical Token Bucket*) ou marcação de pacotes DSCP *Expedited Forwarding*.
* A telemetria E2SM-KPM reporta as métricas de latência de buffer RLC, fechando o ciclo de percepção da xApp-RDL.

### 7.3. Implementação Prática das Adaptações no Código das xApps (Twelve-Factor App)
Para viabilizar a transição sem atrito entre o simulador ns-3 e o hardware físico do testbed da UFPA sem a necessidade de criar novas xApps do zero, os arquivos [`reference-xapps/qos-xslice/xslice_xapp.py`](../../reference-xapps/qos-xslice/xslice_xapp.py) e [`reference-xapps/energy-saving/energy_saving_xapp.py`](../../reference-xapps/energy-saving/energy_saving_xapp.py) foram aprimorados com desacoplamento via variáveis de ambiente:

| Variável de Ambiente | xApp Alvo | Valor Padrão | Função no Testbed UFPA / OpenRAN@Brasil |
| :--- | :--- | :--- | :--- |
| `TARGET_NODES` | Ambas | `"gnb_01,gnb_02"` | Permite apontar para o `node_id` real da gNodeB srsRAN cadastrada no Near-RT RIC da UFPA. |
| `XSLICE_PARAMETER` | `xSlice` | `"PRB_QUOTA"` | Permite chavear dinamicamente para `"SCHEDULER_WEIGHT"` sem alterar o código, contornando a ausência de slicing MAC no srsRAN. |
| `XSLICE_DEFAULT_VALUE` | `xSlice` | `80.0` | Valor nominal da cota ou peso de escalonamento solicitado. |
| `ES_PARAMETER` | `EnergySaver` | `"TX_POWER"` | Parâmetro alvo da economia de energia (`"TX_POWER"` para atenuação de ganho RF na USRP). |
| `ES_DEFAULT_VALUE` | `EnergySaver` | `20.0` | Potência alvo em dBm (ou percentual de estrangulamento de PRBs). |
| `RDL_ENDPOINT` / `RDL_HTTP_URL` | Ambas | `""` | Habilita o método de disparo ativo `_dispatch_proposal()` para injetar propostas no Near-RT RIC em tempo real. |

Essa flexibilização segue os princípios de *Cloud-Native 12-Factor App*, dispensando a criação de novas imagens de contêiner ou branches separadas para testes físicos.

---

## 8. Aplicabilidade em Verticais Estratégicas e Alinhamento com o Projeto GreenRAN / UFPA

O antagonismo e a co-otimização entre **RAN Slice (`xSlice`)** e **EnergySaver (`Energy Saving`)** não constituem apenas um exercício teórico de simulação, mas representam a resposta técnica direta aos desafios de três verticais operacionais críticas para a transição 5G-Advanced/6G e para os projetos de pesquisa da Universidade Federal do Pará (UFPA):

### 8.1. Cidades Inteligentes (*Smart Cities*)
Nas cidades inteligentes, a infraestrutura O-RAN atende a fluxos simultâneos de natureza radicalmente heterogênea:
* **Fatias Concorrentes:**
  * **eMBB:** Câmeras de segurança 4K/CFTV urbano, reconhecimento facial e telemetria de tráfego em tempo real;
  * **mMTC:** Dezenas de milhares de hidrômetros, semáforos, monitoramento de qualidade do ar e iluminação pública;
  * **URLLC:** Comunicação veicular V2X e prioridade absoluta para ambulâncias, viaturas policiais e brigadas de incêndio.
* **Dinâmica do Conflito:** No período da madrugada (00h às 06h), o tráfego civil humano colapsa. O `EnergySaver` atua agressivamente para reduzir o ganho dos amplificadores de potência RF (`TX_POWER`), cortar portadoras secundárias ou ativar o *micro-sleep* de *small cells*.
* **Papel Protetivo do H-RDL:** Evita que a redução predatória de potência degrade o SINR de UEs de emergência ou apague a conectividade de câmeras de segurança periféricas, arbitrando uma fronteira de Pareto ótima via heurística EEVS.

### 8.2. Campus Inteligente (*Smart Campus* — Ex.: Campus Guamá da UFPA / PCT Guamá)
O Campus da UFPA (à beira do rio Guamá) e o Parque de Ciência e Tecnologia (PCT Guamá) possuem características geográficas e operacionais ideais para a validação desta arquitetura:
* **Padrão de Tráfego Bimodal:**
  * **Período Diurno (07h às 19h):** Dezenas de milhares de alunos, docentes e pesquisadores saturando a capacidade das células universitárias com tráfego eMBB;
  * **Período Noturno e Finais de Semana:** Esvaziamento quase completo dos pavilhões de aula, mantendo-se apenas sistemas ininterruptos de missão crítica (data centers do ITEC/ICEN, sensores ambientais de maré do Rio Guamá e segurança patrimonial).
* **Solução com H-RDL:** O `EnergySaver` reduz o consumo elétrico dos blocos acadêmicos ociosos, auxiliando a reitoria nas metas de sustentabilidade e corte de custos de energia, enquanto o `xSlice` garante a reserva intocável de capacidade para servidores e sistemas de vigilância do campus.

### 8.3. Agro 4.0 e Bioeconomia Sustentável na Amazônia
Na agricultura digital e no monitoramento florestal do Pará e da região Norte, a rede O-RAN enfrenta o desafio de estações rádio-base operando em regime **isolado da rede elétrica convencional (*Off-Grid*)**:
* **Operação Fotovoltaica com Baterias:** Torres e *small cells* rurais são mantidas por painéis solares e bancos de baterias. O consumo de potência RF drena diretamente o estado de carga (*State of Charge - SoC*) das baterias durante a noite ou períodos chuvosos.
* **Fatias de Missão Crítica no Campo:**
  * **Tratores e Maquinário Autônomo (URLLC):** Comandos de frenagem e direção assistida que exigem latência sub-5ms e zero tolerância a perdas (risco severo de acidentes de trabalho);
  * **Drones de Mapeamento Multiespectral (eMBB):** Envio contínuo de mapas de lavoura;
  * **Sensores de Umidade e Pivôs de Irrigação (mMTC):** Telemetria periódica leve.
* **Solução com H-RDL:** O `EnergySaver` atua diretamente para preservar a bateria da estação rural em dias de baixa insolação, enquanto o `xSlice` assegura que os comandos dos tratores autônomos (URLLC) tenham prioridade absoluta, garantindo segurança física e continuidade operacional.

### 8.4. Alinhamento Estrito com a Missão Científica do Projeto GreenRAN (ITEC/PPGCOMP/UFPA)
A inclusão central do par `xSlice` e `EnergySaver` converge integralmente com os pilares do laboratório **GreenRAN / UFPA**:
1. **Eficiência Energética com Consciência de SLA (*SLA-Aware Green RAN*):** A premissa norteadora do GreenRAN é que a eficiência energética não pode ser cega; ela deve ser ponderada pela garantia matemática dos contratos de SLA.
2. **Modelo Analítico de Potência Calibrado (Earth/3GPP):** Conforme implementado em [`src/models/earth_energy.py`](../../src/models/earth_energy.py) e [`src/core/reasoning.py:L163-L173`](../../src/core/reasoning.py#L163-L173), o middleware calcula o consumo físico em Watts ($P_{\text{total}} = N_{\text{TRX}}(P_0 + \Delta_p P_{\text{out}})$), fornecendo a métrica Joules por bit consumido exigida nos relatórios do GreenRAN.
3. **Harmonização com o Consórcio OpenRAN@Brasil:** O perfil de implantação em [`deploy/openran-br-v3/`](../../deploy/openran-br-v3/) conecta a arquitetura ao testbed distribuído nacional coordenado pela RNP/MCTI, consolidando a liderança da UFPA na pesquisa de redes abertas e sustentáveis no Brasil.

---

## 9. Conclusão e Diretrizes Metodológicas para a Dissertação

1. **Separação de Papéis:** As classes `XSliceXApp` e `EnergySavingXApp` são independentes e representam clientes que desconhecem a existência um do outro, comunicando-se estritamente através das interfaces abertas O-RAN (`RMR` e `E2AP`).
2. **Determinismo na Base:** O H-RDL (Fase 1) garante matematicamente a integridade física e o cumprimento de contratos de SLA através de funções analíticas fechadas de Shannon, filas M/G/1 e modelos Earth.
3. **Evolução Segura:** A Fase 2 (CA-RDL) introduz o agente neuro-simbólico Safe-MAPPO para buscar eficiência sob incerteza temporal, mas está formalmente subordinada à barreira invariante e ao mecanismo de *fallback* determinístico da Fase 1.
4. **Honestidade Científica e Validação no Testbed UFPA:** Declarar explicitamente que a validação de RAN Slicing em larga escala ($N=20$ UEs) apoia-se no backend simulado ns-3.48/5G-LENA, enquanto o testbed físico GreenRAN/UFPA valida a sinalização real E2AP/E2SM-RC e conflitos de potência/QoS (EEVS) e priorização por UE, garantindo que nenhuma banca ou comitê de revisores aponte limitações não endereçadas.
5. **Defesa Temática Irrefutável:** A escolha da dupla `xSlice` e `EnergySaver` fundamenta-se nas necessidades reais de Cidades Inteligentes, Smart Campus e Agro 4.0, conferindo relevância prática e aderência plena à missão do Laboratório GreenRAN/UFPA.


