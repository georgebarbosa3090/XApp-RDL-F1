# Contrato de Sincronização entre Fase 1 (H-RDL) e Fase 2 (CA-RDL)

**Projeto:** xApp RDL (Resource and Decision Layer)  
**Documento:** `PHASE1_PHASE2_SYNC_CONTRACT.md`  
**Status:** **SPECIFIED / PARTIALLY IMPLEMENTED (CI VERIFIED)**  

**Escopo:** Definição formal do contrato de sincronização de dados, modelos de objetos, abstrações de código e regras de repositório entre H-RDL (Fase 1) e CA-RDL (Fase 2).

---

## 1. Princípios Arquiteturais da Sincronização

A sincronização entre o H-RDL (**Fase 1: Hierarchical Resource and Decision Layer**) e o CA-RDL (**Fase 2: Context-Aware Resource and Decision Layer**) segue três princípios fundamentais:

1. **Determinismo em Primeira Linha (Safety-First):**
   A Fase 1 estabelece as regras determinísticas invioláveis (*Safety Guards*). A Fase 2 opera sobre o subespaço de ações aprovadas pela Fase 1.
2. **Invariância do Esquema de Dados Core:**
   Estruturas fundamentais como `RDLDecision`, `XAppAction`, `ConflictSet` e `PERCEPTION_WINDOW` possuem garantia de compatibilidade estável entre as duas fases.
3. **Mecanismo de Fallback Automático:**
   Caso o motor contextual/MARL da Fase 2 sofra estresse temporal ou degradação ($\Delta t > 200\text{ ms}$ ou falha no modelo de IA), o sistema reverte instantânea e autonomamente para a arbitragem determinística TVS/EEVS do H-RDL Fase 1.

---

## 2. Contrato de Esquema e Dados Compartilhados

```
┌──────────────────────────────────────────────────────────┐
│                   Dados KPM (3GPP / E2)                  │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│            PerceptionAgent (Janela 200ms)                 │
└────────────────────────────┬─────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│ ReasoningAgent (F1)   │         │ ContextEngine (F2)    │
│ TVS/EEVS Determinístico│         │ MAPPO / GNN Context   │
└───────────┬───────────┘         └───────────┬───────────┘
            │                                 │
            └────────────────┬────────────────┘
                             │ (Candidato a Ação)
                             ▼
┌──────────────────────────────────────────────────────────┐
│             RefinementAgent (Safety Guards F1)           │
│   • Budget Max PRB                                       │
│   • Limites em dBm (TxPower)                             │
│   • Cooldown Anti-Ping-Pong                              │
└────────────────────────────┬─────────────────────────────┘
                             │ (Ação Final Aprovada)
                             ▼
┌──────────────────────────────────────────────────────────┐
│                 E2SM-RC Control Request                  │
└──────────────────────────────────────────────────────────┘
```

### Contrato de Dados Python (`src/conflict_types.py`)

| Campo / Tipo | Fase 1 (H-RDL) | Fase 2 (CA-RDL Extension) | Garantia de Sincronização |
| :--- | :--- | :--- | :--- |
| `XAppAction` | `xapp_id`, `action_type`, `params`, `priority` | + `context_features`, `confidence_score` | Retrocompatível via argumentos opcionais com valor padrão (`None`). |
| `RDLDecision` | `decision_id`, `selected_action`, `safety_applied` | + `marl_agent_id`, `reward_estimate` | Os novos campos possuem defaults nulos mantendo parsing idêntico. |
| `ConflictSet` | `conflicting_actions`, `graph` | + `graph_embedding`, `topology_state` | Estrutura de grafo estendida de maneira não-bloqueante. |

---

## 3. Matriz de Mapeamento de Fases e Repositórios

| Repositório Git | Nome Oficial | Papel na Arquitetura | Branch de Integração |
| :--- | :--- | :--- | :--- |
| `georgebarbosa3090/XApp-RDL-F1` | **XApp-RDL-F1 (H-RDL)** | Fase 1 congelada, testes de interoperabilidade, benchmarks $S_0\text{--}S_8$, Safety Guards determinísticos. | `main` |
| `georgebarbosa3090/XApp-RDL-F2` | **XApp-RDL-F2 (CA-RDL)** | Fase 2 em evolução, treinamento MAPPO, GNN Context Engine, cenários $S_9\text{--}S_{15}$. | `main` / `feature/marl-context` |

---

## 4. Checklist de Verificação de Sincronização F1 $\leftrightarrow$ F2

1. [x] **Importação limpa:** `conflict_types.py` importa sem erros em ambos os ambientes.
2. [x] **Safety Fallback:** Em caso de time-out do agente MARL da Fase 2, o H-RDL responde em $\le 200\text{ ms}$.
3. [x] **Zero Synthetic Evidence:** Ambas as fases aderem estritamente à `provenance_policy.yaml`.
4. [x] **Normative Profile:** A Fase 1 permanece em `E2AP v02.03` / `KPM v03.00` / `RC v01.03` enquanto a Fase 2 habilita opcionalmente conectores para `Release 5`.
