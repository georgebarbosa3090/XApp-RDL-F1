# Catálogo e Mapeamento de Figuras do Repositório (`docs/figures/`)

Este documento mapeia sistematicamente a localização, o cenário correspondente e o documento de referência de cada figura diagramática e topológica do repositório **XApp-RDL-F1**.

> [!IMPORTANT]
> **Política de Zero Dados Sintéticos:** Todas as figuras mantidas neste diretório são estritamente diagramas arquiteturais de componentes ou mapas de topologia física espacial de nós de rádio (gNBs/UEs). Figuras contendo gráficos de resultados sintéticos ou números mockados são terminantemente proibidas.

---

## 1. Mapeamento Consolidado de Figuras por Cenário

| Nome da Figura / Caminho | Cenário Relacionado | Documento de Referência | Descrição e Conteúdo | Classificação e Provênia |
| :--- | :---: | :--- | :--- | :---: |
| [`fig_topologia_cenarios_ns3.png`](02_cenarios_e_topologias/fig_topologia_cenarios_ns3.png) | **S0 a S8** / Topologia Geral | [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md)<br/>[`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md)<br/>[`reference-xapps/README.md`](../../reference-xapps/README.md) | Topologia espacial multi-célula (`gNB_01` eMBB, `gNB_02` Energy Saver, `gNB_03` URLLC) e nós E2 conectados ao Near-RT RIC. | `TOPOLOGIA_FISICA` (100% Conforme) |
| [`fig_fluxo_funcional_arquitetura_rdl.png`](01_arquitetura_e_modelagem/fig_fluxo_funcional_arquitetura_rdl.png) | **Arquitetura Geral H-RDL** | [`README.md`](../../README.md)<br/>[`docs/01_arquitetura_e_modelagem_matematica.md`](../01_arquitetura_e_modelagem_matematica.md) | Fluxo de interceptação RMR, agrupamento de ações pelo Perception Agent, arbitragem pelo Reasoning Agent e aplicação de Safety Guards pelo Refinement Agent. | `ARQUITETURA_SISTEMA` (100% Conforme) |

---

## 2. Detalhamento por Estrutura de Diretórios

```text
docs/figures/
├── README.md                                  # Este catálogo de rastreabilidade
├── 01_arquitetura_e_modelagem/
│   └── fig_fluxo_funcional_arquitetura_rdl.png # Diagrama funcional da arquitetura H-RDL
└── 02_cenarios_e_topologias/
    └── fig_topologia_cenarios_ns3.png          # Topologia física espacial dos cenários ns-3
```

---

## 3. Matriz de Cruzamento: Cenário vs. Figura vs. Documento

### 3.1. Cenários de Validação do Núcleo H-RDL (S0 a S8)
* **Cenário S0 (Passthrough Limpo):** Mapeado teoricamente em [`simulations/ns3/README.md`](../../simulations/ns3/README.md) e ilustrado topologicamente em [`fig_topologia_cenarios_ns3.png`](02_cenarios_e_topologias/fig_topologia_cenarios_ns3.png).
* **Cenários S1 a S5 (Conflitos PRB, TVS, EEVS, Mobilidade, Ping-Pong):** Caracterizados contratualmente em [`docs/topologia_espacial_e_cenarios_s1_s5.md`](../topologia_espacial_e_cenarios_s1_s5.md) utilizando a topologia espacial [`fig_topologia_cenarios_ns3.png`](02_cenarios_e_topologias/fig_topologia_cenarios_ns3.png).
* **Cenários S6 a S8 (Storm <50ms, Zero-Violation, Malha Fechada E2/NORI):** Mapeados em [`simulations/ns3/README.md`](../../simulations/ns3/README.md) com rastreabilidade de código C++ e testes em [`tests/unit/test_campaign_scenarios.py`](../../tests/unit/test_campaign_scenarios.py).

### 3.2. xApps de Terceiros (`ORAN_SC_OFFICIAL`, `ACADEMIC_REIMPLEMENTATION`, `LITERATURE_INSPIRED`)
* **Traffic Steering (`ric-app-ts`):** Documentado em [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) e [`reference-xapps/README.md`](../../reference-xapps/README.md).
* **KPIMON (`ric-app-kpimon`):** Documentado em [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) e [`reference-xapps/README.md`](../../reference-xapps/README.md).
* **xSlice (`qos-xslice`):** Documentado em [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) e [`reference-xapps/README.md`](../../reference-xapps/README.md).
* **Energy Saving (`energy-saving`):** Documentado em [`docs/modelagem_cenarios_xapps_terceiros.md`](../modelagem_cenarios_xapps_terceiros.md) e [`reference-xapps/README.md`](../../reference-xapps/README.md).

---

## 4. Diretriz de Manutenção

Caso uma nova figura arquitetural ou mapa topológico seja adicionado ao projeto:
1. Certifique-se de que a figura **NÃO contenha dados sintéticos, gráficos de resultados ou valores hardcoded**.
2. Salve-a no subdiretório apropriado (`01_arquitetura_e_modelagem/` ou `02_cenarios_e_topologias/`).
3. Registre a nova figura nesta tabela com o link do arquivo, o cenário correspondente e o documento de referência.
