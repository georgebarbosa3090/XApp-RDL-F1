# Catálogo Oficial da Suíte de Figuras Científicas XApp-RDL (S0 a S15 — Estilo Figuras 4 e 5)

Este documento registra a rastreabilidade completa de todas as **64 figuras científicas** (Figura A — Conceitual e Figura B — Geométrica 2D em Metros) mantidas em `docs/figures/02_cenarios_e_topologias/`, criadas de acordo com a **SKILL `xapp-figure-generator`** ([SKILL.md](../../.agents/skills/xapp-figure-generator/SKILL.md)).

---

## 1. Estrutura Visual Estilo Figuras 4 e 5

- **Figura A (Conceitual 3D/Isométrica - Estilo Fig. 4)**: Ilustração operacional com torres gNB, UEs por classe de tráfego (URLLC, eMBB, mMTC), caixa de chamada interna (*Callout*) descrevendo a disputa entre xApps, arbitragem H-RDL e gráfico de trade-off conceitual.
- **Figura B (Geométrica 2D em Metros - Estilo Fig. 5)**: Gráfico métrico ($X \times Y$ em metros) indicando posições exatas dos nós (`pos_m`), raios de cobertura reais, sombreamento da área de sobreposição, legenda explicativa e anotação do efeito H-RDL.
- **Conformidade Científica**: Zero dados sintéticos ou números inventados (*"Representação esquemática do cenário; não substitui resultados experimentais."*).

---

## 2. Tabela de Rastreabilidade ($S_0$ a $S_{15}$)

| ID | Nome do Cenário | Figura A (Claro / Escuro) | Figura B (Claro / Escuro) |
| :---: | :--- | :--- | :--- |
| **S0** | No-Conflict Control | [`s0_figura_a_light.png`](02_cenarios_e_topologias/s0_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s0_figura_a_dark.png) | [`s0_figura_b_light.png`](02_cenarios_e_topologias/s0_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s0_figura_b_dark.png) |
| **S1** | Direct PRB Conflict | [`s1_figura_a_light.png`](02_cenarios_e_topologias/s1_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s1_figura_a_dark.png) | [`s1_figura_b_light.png`](02_cenarios_e_topologias/s1_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s1_figura_b_dark.png) |
| **S2** | Energy Saving vs QoS | [`s2_figura_a_light.png`](02_cenarios_e_topologias/s2_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s2_figura_a_dark.png) | [`s2_figura_b_light.png`](02_cenarios_e_topologias/s2_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s2_figura_b_dark.png) |
| **S3** | Traffic Steering vs Slicing | [`s3_figura_a_light.png`](02_cenarios_e_topologias/s3_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s3_figura_a_dark.png) | [`s3_figura_b_light.png`](02_cenarios_e_topologias/s3_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s3_figura_b_dark.png) |
| **S4** | Traffic Steering vs Energy Saving | [`s4_figura_a_light.png`](02_cenarios_e_topologias/s4_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s4_figura_a_dark.png) | [`s4_figura_b_light.png`](02_cenarios_e_topologias/s4_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s4_figura_b_dark.png) |
| **S5** | Temporal Ping-Pong | [`s5_figura_a_light.png`](02_cenarios_e_topologias/s5_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s5_figura_a_dark.png) | [`s5_figura_b_light.png`](02_cenarios_e_topologias/s5_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s5_figura_b_dark.png) |
| **S6** | Multi-xApp Conflict Storm | [`s6_figura_a_light.png`](02_cenarios_e_topologias/s6_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s6_figura_a_dark.png) | [`s6_figura_b_light.png`](02_cenarios_e_topologias/s6_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s6_figura_b_dark.png) |
| **S7** | Fault / Rogue xApp | [`s7_figura_a_light.png`](02_cenarios_e_topologias/s7_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s7_figura_a_dark.png) | [`s7_figura_b_light.png`](02_cenarios_e_topologias/s7_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s7_figura_b_dark.png) |
| **S8** | Real NORI Closed Loop | [`s8_figura_a_light.png`](02_cenarios_e_topologias/s8_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s8_figura_a_dark.png) | [`s8_figura_b_light.png`](02_cenarios_e_topologias/s8_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s8_figura_b_dark.png) |
| **S9** | NTN Terrestrial–Satellite | [`s9_figura_a_light.png`](02_cenarios_e_topologias/s9_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s9_figura_a_dark.png) | [`s9_figura_b_light.png`](02_cenarios_e_topologias/s9_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s9_figura_b_dark.png) |
| **S10** | UAV Swarm Coverage | [`s10_figura_a_light.png`](02_cenarios_e_topologias/s10_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s10_figura_a_dark.png) | [`s10_figura_b_light.png`](02_cenarios_e_topologias/s10_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s10_figura_b_dark.png) |
| **S11** | V2X High-Mobility Platoon | [`s11_figura_a_light.png`](02_cenarios_e_topologias/s11_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s11_figura_a_dark.png) | [`s11_figura_b_light.png`](02_cenarios_e_topologias/s11_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s11_figura_b_dark.png) |
| **S12** | IIoT / TSN Mission-Critical | [`s12_figura_a_light.png`](02_cenarios_e_topologias/s12_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s12_figura_a_dark.png) | [`s12_figura_b_light.png`](02_cenarios_e_topologias/s12_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s12_figura_b_dark.png) |
| **S13** | SAGIN Multi-Domain | [`s13_figura_a_light.png`](02_cenarios_e_topologias/s13_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s13_figura_a_dark.png) | [`s13_figura_b_light.png`](02_cenarios_e_topologias/s13_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s13_figura_b_dark.png) |
| **S14** | ISAC Sensing × Comms | [`s14_figura_a_light.png`](02_cenarios_e_topologias/s14_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s14_figura_a_dark.png) | [`s14_figura_b_light.png`](02_cenarios_e_topologias/s14_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s14_figura_b_dark.png) |
| **S15** | Cross-Tier Governance | [`s15_figura_a_light.png`](02_cenarios_e_topologias/s15_figura_a_light.png) / [`dark`](02_cenarios_e_topologias/s15_figura_a_dark.png) | [`s15_figura_b_light.png`](02_cenarios_e_topologias/s15_figura_b_light.png) / [`dark`](02_cenarios_e_topologias/s15_figura_b_dark.png) |

---

## 3. Artefatos de Suporte e Proveniência

- **JSON Canônico**: [`cenarios_canonicos_s0_s15.json`](02_cenarios_e_topologias/cenarios_canonicos_s0_s15.json)
- **Relatório de Correspondência $A \leftrightarrow B$**: [`relatorio_correspondencia_A_B.md`](02_cenarios_e_topologias/relatorio_correspondencia_A_B.md)
- **Manifesto de Proveniência SHA-256**: [`manifesto_proveniencia.json`](02_cenarios_e_topologias/manifesto_proveniencia.json)
