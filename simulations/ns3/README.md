# Mapeamento e Matriz Metodológica da Campanha de Cenários (S0 a S15)

Este diretório contém a suíte de simulações físicas **ns-3 + 5G-LENA + NORI + E2 real** para validação experimental do middleware **xApp RDL (H-RDL)**.

---

## 1. Núcleo Fase 1 (S0–S8): Validação Obrigatória H-RDL

| Identificador | Nome do Cenário | Arquivo C++ Executável | Propósito Metodológico / Métrica Principal |
| :---: | :--- | :--- | :--- |
| **S0** | Passthrough Limpo e Não-Interferência | [`scenario_rdl_no_conflict.cc`](scenario_rdl_no_conflict.cc) | Taxa de Interferência = 0%, Preservação de Ações Válidas |
| **S1** | Conflito Direto de PRB | [`scenario_rdl_direct_prb_conflict.cc`](scenario_rdl_direct_prb_conflict.cc) | Precision, Recall, F1-Score em Colisão de Bloco de Recursos |
| **S2** | Conflito Indireto TVS (Throughput x Slicing) | [`scenario_rdl_tvs_conflict.cc`](scenario_rdl_tvs_conflict.cc) | Resolução de Conflito de Domínio Cruzado (PRB vs SLA) |
| **S3** | Multi-Métrica Cross-Layer (Power x QoS) | [`scenario_rdl_energy_vs_qos.cc`](scenario_rdl_energy_vs_qos.cc) | Equilíbrio Pareto entre Economia de Energia e SLA |
| **S4** | Mobilidade (TS) x Economia de Energia (ES) | [`scenario_rdl_ts_vs_energy.cc`](scenario_rdl_ts_vs_energy.cc) | Arbitragem Assimétrica de Sono de gNB e Cobertura |
| **S5** | Histerese Temporal e Trava de Ping-Pong | [`scenario_rdl_temporal_pingpong.cc`](scenario_rdl_temporal_pingpong.cc) | Cooldown Lock e Supressão de Oscilação Temporal |
| **S6** | Conflict Storm (50 req/janela) | [`scenario_rdl_conflict_storm.cc`](scenario_rdl_conflict_storm.cc) | Tempo de Resolução Near-RT Estritamente < 50 ms |
| **S7** | Injeção de Falhas Adversárias | [`scenario_rdl_fault_injection.cc`](scenario_rdl_fault_injection.cc) | Zero-Violation (100% de Ações Inseguras Bloqueadas) |
| **S8** | Malha Fechada E2AP/E2SM com NORI | [`scenario_rdl_closed_loop_nori.cc`](scenario_rdl_closed_loop_nori.cc) | Integração Completa com Codec ASN.1 e RIC Real |

---

## 2. Suíte Avançada 5G-A/6G (S9–S15): Roadmap e Generalização

Os cenários **S9 a S15** representam a extensão da campanha para ambientes de próxima geração (5G-Advanced / 6G). Estão documentados no roadmap formal em [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](../../docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) e cobertos por contratos de validação em [`tests/unit/test_campaign_scenarios.py`](../../tests/unit/test_campaign_scenarios.py).

| Identificador | Domínio de Pesquisa | xApp Relacionada | Requisito Principal de Simulação |
| :---: | :--- | :--- | :--- |
| **S9** | Non-Terrestrial Networks (NTN) | `ntn-steering`, `satellite-ho` | Handover Orbital LEO & Compensação Doppler |
| **S10** | UAV Swarm & Cobertura Aérea | `uav-mobility`, `energy-conserver-uav` | Gestão de Bateria SoC & Mobilidade 3D em Enxame |
| **S11** | V2X Platoon Highway (110 km/h) | `v2x-mobility`, `platoon-qos` | Latência URLLC Sub-10ms & Handover de Alta Velocidade |
| **S12** | IIoT / Factory TSN | `industrial-qos` | Latência Determinística & Supressão de Jitter |
| **S13** | Emergency SAGIN | `rescue-qos` | Orquestração Multidomínio Satélite-UAV-Terrestre |
| **S14** | 6G ISAC (Radar + Comms) | `isac-radar` | Mitigação de Interferência Sensoriamento x Comunicação |
| **S15** | Segurança Cross-Tier Zero-Trust | `sec-guardian` | Controle Hieraquico Near-RT / Non-RT com Zero-Trust |

---

## 3. Diretriz de Execução Científica

Nenhum resultado experimental dos cenários S0 a S15 deve ser derivado de geradores sintéticos. A execução deve seguir obrigatoriamente a cadeia de evidências reais:

$$
\text{Cenário C++} \longrightarrow \text{ns-3 + 5G-LENA} \longrightarrow \text{E2AP/E2SM via NORI} \longrightarrow \text{Logs Brutos} \longrightarrow \text{Post-Hoc Calculador}
$$
