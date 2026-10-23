# xApp RDL (Resource and Decision Layer) — O-RAN Multi-xApp Conflict Governance

<div align="center">

**Arquitetura Unificada de Governança Cognitiva, Arbitragem Determinística e Mitigação de Conflitos Multi-xApp para Near-RT RIC**  
*Perfil-alvo documentado para O-RAN ALLIANCE WG2/WG3, O-RAN SC (Release J), NORI (5G-LENA v5.1 / ns-3.48) e OpenRAN@Brasil Blueprint v3; interoperabilidade externa segue em validação.*

[![O-RAN WG3](https://img.shields.io/badge/O--RAN%20Alliance-WG3%20E2AP%20v2.03%20%7C%20E2SM--RC%20v1.03-blue.svg)](https://o-ran.org)
[![ns-3 5G-LENA](https://img.shields.io/badge/ns--3.48-5G--LENA%20v5.1%20%7C%20NORI-green.svg)](https://cttc.es)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](LICENSE)

</div>

---

### 🗺️ Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1** | **RDL Determinística e Segura (H-RDL)**<br/>*Código experimental para heurísticas de prioridade, safety guards e mapeamento E2AP/E2SM.* | **Integração E2 e validação experimental não verificadas**<br/>*(closed loop causal e campanha científica multi-seed pendentes)* | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2** | **RDL Baseada em Contexto e Safe-RL (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (Safe-MAPPO sob CMDP Lagrangian), Grafos de Conhecimento (GraphSAGE / GNN) e Sensibilidade Contextual.* | **Em desenvolvimento ativo** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (A1 Intent-Driven), Federação Multi-RIC e SAGIN.* | **Roadmap Ativo (2026–2028)** | *Em especificação e testbed* |

---

### 🛡️ Matriz de Maturidade dos Gates de Evidência Experimental (Fase 1 — H-RDL)

Em conformidade rigorosa com a política de proveniência (`reproducibility/provenance_policy.yaml`) e auditoria técnica de 22/10/2026:

| Gate | Descrição Normativa | Status Atual | Evidência & Diagnóstico Técnico |
| :---: | :--- | :---: | :--- |
| **G0** | Ambiente Normativo Reproduzível | 🟡 **PARCIAL** | `uv.lock` fixa o ambiente Python; dependências transitivas do testbed ns-3/NORI precisam de registro de versão/commit por execução. |
| **G1** | E2SM-KPM Real (Telemetria Externa) | 🔴 **NÃO VALIDADO** | Não há evidência elegível de Setup/descoberta E2, subscrição e Indications de uma execução ns-3/5G-LENA + NORI. |
| **G2** | H-RDL Funcional (Decisão Determinística) | 🟢 **APROVADO LOCAL** | Testes locais de detecção, Safety default-deny, limites de potência e rollback; não certifica interoperabilidade E2 externa. |
| **G3** | E2SM-RC Real (Controle + ACK Externo) | 🔴 **NÃO VALIDADO** | Não há evidência de ação E2SM-RC aplicada à RAN nem ACK externo correlacionado. |
| **G4** | Closed-Loop Causal End-to-End | 🔴 **NÃO VALIDADO** | A fixture `CAUSAL_FIXTURE` não é experimento; não foi demonstrado loop causal na RAN simulada. |
| **G5** | Campanha Científica Multi-Semente | 🔴 **NÃO APROVADO** | Execuções do simulador Python local estão desativadas; não há campanha elegível ns-3/5G-LENA com proveniência completa. |
| **G6** | Artifact Readiness (ACM SIGSIM / IEEE) | ⚪ **BLOQUEADO** | Bloqueado formalmente até a coleta e certificação das evidências empíricas externas de G4 e G5. |

> **Retificação de evidências (23/10/2026):** valores numéricos e manifestos legados não foram verificados contra execuções elegíveis de ns-3/5G-LENA; não usar relatórios históricos como evidência científica. O simulador Python local está desativado e não deve ser usado para experimentos. C1–C6 estão `NOT_VERIFIED` em [`specs/claims.yaml`](specs/claims.yaml); testes unitários locais não aprovam gates experimentais.

---

## 1. Visão Geral da Arquitetura e Principais Inovações

A **xApp RDL (Resource and Decision Layer)** atua como o middleware central de governança no **Near-RT RIC**, interceptando e mitigando colisões de recursos geradas por **xApps concorrentes da literatura O-RAN**:

1. **xSlice (QoS & Slicing Optimizer) — [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran):** Solicita cotas elevadas de PRBs (`PRB_QUOTA = 80%`, prioridade 90) para fatias críticas URLLC e eMBB.
2. **Energy Saving (Green RAN Optimizer) — [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric):** Solicita redução de potência de transmissão (`TX_POWER = 20 dBm`, prioridade 65) e modo sleep de células, colidindo com as garantias de QoS.
3. **Traffic Steering (Mobility Optimizer) — [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts):** Solicita migração e balanceamento de tráfego (`HANDOVER`, prioridade 80), podendo induzir instabilidade e tempestades de Ping-Pong.

```mermaid
flowchart TD
    subgraph SMO_RIC["SMO & NEAR-RT RIC (OSC)"]
        direction TB
        subgraph RDL_CORE["xApp-RDL CORE (H-RDL Determinística)"]
            direction TB
            PA["Perception Agent<br/>(Decodificador ASN.1 APER E2SM-KPM)"]
            CD["Conflict Detector<br/>(Matriz Determinística de Conflitos)"]
            RE["Reasoning Engine<br/>(Heurísticas TVS / EEVS & Utilidade)"]
            SG["Safety Guard<br/>(Limites Físicos 3GPP TS 38.104)"]
            AE["Actuation Engine<br/>(Codificador ASN.1 E2SM-RC Format 1)"]
            
            PA --> CD
            CD --> RE
            RE --> SG
            SG --> AE
        end
    end

    subgraph XAPPS["xApps Concorrentes da Literatura"]
        X1["xSlice (QoS / Slicing)"]
        X2["Energy Saving (Green RAN)"]
        X3["Traffic Steering (Mobilidade)"]
    end

    subgraph E2_NODE["Nó E2 / 5G-LENA ns-3.48 (NORI)"]
        DU["O-DU (MAC / Scheduler / PRB)"]
        CU["O-CU-CP / O-CU-UP (RRC / PDCP)"]
        RU["O-RU (Massive MIMO / Tx Power)"]
    end

    X1 & X2 & X3 -->|Propostas Concorrentes de Controle| CD
    E2_NODE -->|E2SM-KPM v2.03 Indication| PA
    AE -->|E2SM-RC v1.03 Control Request Seguro| E2_NODE
```

---

## 2. Paradigmas de Controle e Governança: H-RDL (Fase 1) × CA-RDL (Fase 2)

A governança multi-xApp evolui através de dois paradigmas complementares e interoperáveis:

```mermaid
flowchart TD
    subgraph F1["Fase 1: H-RDL (Determinística & Heurística)"]
        direction TB
        A1["Propostas de xApps"] --> A2["Janela Fixa (200 ms)"]
        A2 --> A3["Heurística & Utilidade (TVS/EEVS)"]
        A3 --> A4["Safety Guard (Boundary Clip)"]
        A4 --> A5["Comando E2SM-RC validado (latência a medir)"]
    end

    subgraph F2["Fase 2: CA-RDL (Context-Aware & Safe-MAPPO)"]
        direction TB
        B1["Propostas de xApps"] --> B2["Janela Adaptativa (50 a 500 ms)"]
        B2 --> B3["Knowledge Graph & GNN (Topologia Dinâmica)"]
        B3 --> B4["Safe-MAPPO com Action Masking"]
        B4 --> B5["Comando E2SM-RC otimizado (meta < 10 ms; não medido)"]
    end
```

### 2.1 Comparativo Didático dos Paradigmas

| Dimensão de Análise | Fase 1: H-RDL (Heuristic RDL) | Fase 2: CA-RDL (Context-Aware RDL) |
| :--- | :--- | :--- |
| **Filosofia de Controle** | **Determinística e Reativa:** Aplica regras matemáticas estritas e funções de utilidade convexas sobre estados instantâneos. | **Cognitiva e Adaptativa:** Aprende padrões temporais complexos, antecipa tendências e adapta a decisão ao contexto operacional. |
| **Janela de Decisão ($\Delta t_{win}$)** | **Fixa ($200	ext{ ms}$):** Agrupa propostas que chegam no intervalo regular para arbitragem em lote. | **Dinâmica e Adaptativa ($50	ext{ a }500	ext{ ms}$):** Ajusta o intervalo com base na velocidade de variação do tráfego e churn de rádio. |
| **Mecanismo de Detecção** | **Tabela de Conflitos e Regras Estáticas:** Verifica sobreposição de parâmetros físicos ($P_{tx}$, PRBs, Handover) na matriz de conflito. | **Knowledge Graph & GraphSAGE (GNN):** Mapeia a topologia como grafo dinâmico e detecta conflitos diretos, indiretos e implícitos. |
| **Motor de Decisão (Reasoning)** | **Heurísticas TVS / EEVS:** Otimização combinatória convexa baseada em pesos estáticos de QoS e penalidades lineares. | **Safe-MAPPO (MARL):** Agentes neurais cooperativos treinados sob CMDP (*Constrained Markov Decision Process*) via Multiplicadores de Lagrange. |
| **Garantia de Segurança** | **Safety Guard Rígido (Hard Bound):** *Clipping* e truncamento imediato de comandos fora dos limites do 3GPP TS 38.104. | **Action Masking + Lagrange Guard:** Invalidação prévia de ações inseguras no espaço de probabilidade da política neural. |
| **Latência de Decisão** | A medir com traces de execução elegíveis; não há valor certificado nesta versão. | Meta arquitetural (< 10 ms), ainda sem resultado experimental certificado. |
| **Cenário Ideal de Operação** | Redes estáveis, tráfego homogêneo e requisitos determinísticos estritos de sub-milissegundo. | Redes densas heterogêneas, fatiamento dinâmico (URLLC/eMBB/mMTC), ISAC 6G e mobilidade NTN/V2X. |

---

## 3. Topologias e Cenários Especificados para Avaliação (O-RAN / ns-3)

A plataforma valida cenários de simulação científica, com foco em H-RDL:

| ID | Cenário | Topologia / Nós | xApps Concorrentes | Desafio de Conflito | Métrica Chave |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **C1** | **EEVS (Energy vs QoS)** | 1 gNB Macro + 3 Small Cells, 30 UEs | xSlice vs Energy Saving | Conflito Direto de $P_{tx}$ e PRBs | Consumo (J/Mbit) vs SLA Violation |
| **C2** | **TVS (Traffic Steering vs Slicing)** | 3 gNBs Interconectadas (Xn), 45 UEs | xSlice vs Traffic Steering | Conflito Indireto de Handover e Cota | Vazão Agregada (Mbps) e Ping-Pong |
| **C3** | **5G-Adv Multi-Carrier MIMO** | Dual Carrier (n78 + n258), 60 UEs | xSlice + ES + TS + MIMO Alloc | Acoplamento Cruzado de Banda e Potência | Eficiência Espectral (bps/Hz) |

---

## 4. Galeria de Figuras Científicas e Topologias de Rede

Todas as figuras científicas, topologias e diagramas de sequência estão catalogados em [`docs/figures/`](docs/figures/README.md).
- **Diagrama de Sequência Canônico Compacto (Dissertação / Artigos):** Modelado em 4 macro-entidades O-RAN e disponível em três formatos vetoriais:
  - [`docs/figures/diagrama_sequencia_compacto_dissertacao.mermaid`](docs/figures/diagrama_sequencia_compacto_dissertacao.mermaid) (Mermaid)
  - [`docs/figures/diagrama_sequencia_compacto_dissertacao.puml`](docs/figures/diagrama_sequencia_compacto_dissertacao.puml) (PlantUML)
  - [`docs/figures/diagrama_sequencia_compacto_dissertacao.tex`](docs/figures/diagrama_sequencia_compacto_dissertacao.tex) (LaTeX / TikZ puro)

---

## 5. Catálogo Formal de Relatórios Científicos e Normativos

O arcabouço científico consolida as matrizes de rastreabilidade normativa, orçamentos de latência e evidências experimentais documentadas em [`docs/`](docs/README.md):
- **Demonstrações legadas D1–D5:** consulte o [Volume 21](docs/21_relatorio_demonstracao_rica_closed_loop.md) somente como registro histórico retirado de evidência; o script correspondente está desativado.
- **Diagrama de Sequência e Fluxo de Controle Closed-Loop (H-RDL Fase 1):** Consulte o [Volume 23](docs/23_diagrama_sequencia_fluxo_closed_loop_hrdl_fase1.md) para a decomposição dos 5 estágios de arbitragem em malha fechada, mensagens normativas O-RAN WG2/WG3 e orçamento de latência.

---

## 6. Pipeline de Execução e Reproducibilidade

### 6.1 Execução dos Testes Automatizados
```bash
# Instalação das dependências para desenvolvimento e testes
# Inclui ferramentas de teste e, opcionalmente, dependência O-RAN SC/RMR
uv sync --extra test --extra oran

# Execução da suíte de testes
pytest tests/ -v
```

### 6.2 Execução da xApp
```bash
# Execução instalada
xapp-rdl

# Alternativa sem instalar o entry point
python -m src.main
```

---

## 7. Informações Acadêmicas e Governança

- **Autor do Projeto:** George Alexandro Ferreira Barbosa
- **Orientador:** Prof. Dr. André Riker
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC)
- **Programa:** Programa de Pós-Graduação em Ciência da Computação (PPGCOMP)
- **Área de Concentração:** Sistemas de Computação e Redes de Comunicação
- **Linha de Pesquisa:** Redes Sem Fio Inteligentes, Open RAN e Arquiteturas Cognitivas 6G
- **Versão declarada do pacote:** `1.1.0` (metadados de `pyproject.toml`)

---

## 8. Licença e Direitos

Este projeto é disponibilizado sob a licença **Apache License 2.0**. Consulte o arquivo [`LICENSE`](LICENSE) para obter os termos e condições na íntegra.
