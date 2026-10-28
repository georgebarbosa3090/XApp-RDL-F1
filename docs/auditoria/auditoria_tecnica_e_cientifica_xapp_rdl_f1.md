# Auditoria Técnica e Científica do XApp-RDL-F1

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Data:** 13/09/2026  
**Escopo:** Avaliação técnica do estado do branch `main` com foco em H-RDL Fase 1, E2/O-RAN, ns-3/5G-LENA/NORI, cenários S0–S8, suíte de testes, CI/CD, proveniência experimental, reprodutibilidade científica, Kubernetes e modo de demonstração em tempo real.

---

## Síntese Executiva

A arquitetura e o núcleo de software do H-RDL estão em um estágio maduro e refinado. No entanto, o repositório exige rigor contínuo no pipeline de evidência experimental para sustentar resultados científicos oficiais.

Conforme a regra de proveniência do projeto:
$$\boxed{\text{resultado valido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}}$$

Números provenientes exclusivamente de emulação, codec local ou vetores sintéticos são estritamente classificados como testes de integração/software, devendo ser isolados da campanha de publicação.

---

## 1. Resultado Geral da Auditoria

| Área Auditada | Avaliação | Observações Técnicas |
| :--- | :---: | :--- |
| **Arquitetura H-RDL** | **9,1/10** | Modular e bem definida em camadas. |
| **Perception / Reasoning / Refinement** | **9,0/10** | Excelente separação de responsabilidades. |
| **E2AP Estrutural** | **8,8/10** | Separação correta entre RMR MTypes e E2AP ProcedureCodes. |
| **E2SM-RC / Capability Discovery** | **8,8/10** | Suporte ao modo `oran-strict` operacional. |
| **Segurança / Safety Guards** | **9,0/10** | Validação física de invariantes madura. |
| **Cenários C++ ns-3/5G-LENA** | **7,2/10** | Infraestrutura funcional e estendida com suporte a parâmetros CLI. |
| **Modo Demonstração Realtime** | **6,8/10** | Suporte a `ns3::RealtimeSimulatorImpl` operacional. |
| **Interoperabilidade E2 Externa** | **4,5/10** | Estrutura pronta; aguardando evidência externa dos 4 Gates. |
| **Gate 1 (KPM Real)** | **3,5/10** | Requer validação conjunta dos 7 critérios formais. |
| **Gate 3 (E2SM-RC Real)** | **5,0/10** | Codec e estrutura prontos; aguardando ACK externo em malha. |
| **Gate 4 (Closed-Loop Causal)** | **4,0/10** | Cadeia lógica definida; aguardando prova causal ponta a ponta. |
| **Proveniência Científica** | **3,5/10** | Separação rígida entre modelo discreto local e traces ns-3/NORI. |
| **CI/CD Científico** | **5,5/10** | Cobertura Python e validação estática operacionais. |
| **Documentação** | **5,5/10** | Extensa e detalhada; números experimentais devem ser purgados até evidência externa. |
| **Evidência Pronta para Artigo** | **4,5/10** | Em estruturação para a campanha formal de 30 seeds. |
| **Potencial de Publicação** | **9,5/10** | Relevância e rigor formal elevados para IEEE/ACM. |

**Nível de Maturidade Atual:**
$$\boxed{\text{L3 — O-RAN Structurally Compatible}}$$
*Componentes próximos de L4, com evolução planejada:*
$$\text{L3} \longrightarrow \text{L4 (E2 Externo)} \longrightarrow \text{L5 (Closed-Loop)} \longrightarrow \text{L6 (30 Seeds)}$$

---

## 2. Uma Melhoria Importante Confirmada: E2AP Procedure Codes

Um problema crítico de auditorias anteriores foi devidamente corrigido.  
O código agora separa corretamente os `mtypes` do RMR dos `ProcedureCode` E2AP:

- **RMR Message Types:** `12010` (Subscription Request), `12040` (Control Request), `12050` (Indication).
- **E2AP ProcedureCodes:** `1` (E2 Setup), `4` (RIC Control), `5` (RIC Indication), `8` (RIC Subscription), `9` (RIC Subscription Delete).

O arquivo `src/e2/constants.py` reflete exatamente essa separação.

$$\boxed{\text{P0 anterior: RESOLVIDO}}$$

---

## 3. Capability Registry e Modo Strict

O `RanFunctionCapabilityRegistry` possui dois modos distintos:
- **`OFFLINE_SIMULATION`:** utiliza capacidades padrão para depuração local.
- **`RDL_MODE=oran-strict`:** uma ação só pode ser resolvida se a capacidade do E2 Node tiver sido realmente descoberta via E2. Caso contrário, a exceção `CapabilityNotDiscoveredError` é lançada.

### Injeção em Implantações Helm e Kubernetes
No perfil experimental O-RAN, a variável `rdlMode: "oran-strict"` deve ser ativada no Helm Chart (`values.yaml`) e repassada ao container no manifesto Deployment:
```yaml
env:
  - name: RDL_MODE
    value: "oran-strict"
```

---

## 4. Proveniência e Classificação dos Motores de Simulação

Para garantir o rigor na publicação de resultados científicos:

- **`DiscreteEventRANSimulator` (Python):** classificado estritamente como `LOCAL_DISCRETE_MODEL` / `EMULATED_RAN_MODEL`. É utilizado para testes unitários, validação rápida de algoritmos e depuração local de regressão.
- **`ns-3 + 5G-LENA + NORI` (C++):** classificado como `NS3_FLOWMONITOR` / `NORI_E2`. É o único backend autorizado para geração de datasets finais e tabelas da dissertação/artigo.

### Matriz Canônica de Proveniência:

| Origem / Fonte de Dados | Categoria | Elegibilidade para Publicação |
| :--- | :--- | :---: |
| **`NS3_FLOWMONITOR`** | Simulação Físico-Matemática 5G-LENA | **SIM (Publicável)** |
| **`NORI_E2`** | Co-Simulação E2/O-RAN Fechada | **SIM (Publicável)** |
| **`HRDL_RUNTIME`** | Telemetria e Logs da xApp RDL | **SIM (Publicável)** |
| **`REAL_RIC_LOG`** | Logs do Near-RT RIC (O-RAN SC) | **SIM (Publicável)** |
| `DISCRETE_EVENT_SIMULATOR` | Modelo Discreto Python (Local) | *Apenas Dev / Testes* |
| `EMULATED` / `SYNTHETIC` / `MOCK` | Injeção / Test Harness | *Apenas Dev / Testes* |

---

## 5. Validação Formal dos 4 Gates de Interoperabilidade

1. **Gate 1 — KPM Real ($\odot$ PENDENTE):** Requer validação conjunta dos 7 critérios formais:
   $$G_1 = g_1 \land g_2 \land g_3 \land g_4 \land g_5 \land g_6 \land g_7$$
   *(Conexão NORI, E2 Setup, KPM RAN Function, Subscription ACK, Raw Indication, APER Decode e Validação Cruzada com FlowMonitor).*
2. **Gate 2 — H-RDL Decision ($\checkmark$ FORTE):** Núcleo determinístico de decisão e Safety Guards 100% operacionais e testados.
3. **Gate 3 — E2SM-RC Real ($\odot$ PARCIAL):** Codec ASN.1 APER e mapeador `RCMapper` concluídos; aguardando confirmação externa de `RICcontrolAck`/`RICcontrolFailure` no Near-RT RIC.
4. **Gate 4 — Closed-Loop Causal ($\odot$ PENDENTE):** Cadeia lógica ponta a ponta pronta:
   $$KPM(t_0) \longrightarrow H\text{-}RDL \longrightarrow E2SM\text{-}RC \longrightarrow NORI \longrightarrow 5G\text{-}LENA \longrightarrow KPM(t_1)$$

---

## 6. Recomendações e Plano de Ação Prioritário

1. **P0.1 / P0.2 — Isolamento de Proveniência:** Manter o `DiscreteEventRANSimulator` para desenvolvimento/testes locais, garantindo que a campanha científica oficial consuma apenas traces do ns-3 + NORI.
2. **P0.7 — Ajuste no RealtimeSimulatorImpl em S8:** Garantir o uso de `Config::SetDefault("ns3::RealtimeSimulatorImpl::SynchronizationMode", StringValue(syncMode))` no cenário `scenario_rdl_closed_loop_nori.cc`.
3. **P0.9 — Congelamento da Nomenclatura S0–S8:** Manter alinhamento 1:1 entre código C++, documentação e catálogo de figuras.

---

## 7. Conclusão e Veredito

O projeto XApp-RDL-F1 apresenta uma arquitetura excepcionalmente bem projetada, modular e fundamentada nas normas O-RAN. Com a conclusão do pipeline de evidência externa nos Gates 1 e 4 no ambiente ns-3 + NORI, o projeto atingirá o nível máximo de maturidade experimental (L4/L5) e prontidão para publicação científica de alto impacto.
