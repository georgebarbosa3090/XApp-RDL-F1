# Campanha NORI: cenários de conflito com E2 real (20261109T130614Z)

Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas pelo H-RDL e registradas, sem Control.

| Execução | Baseline (fonte da decisão) | Cadeia | tshark | Msgs | Indications xApp | Estratégias H-RDL | Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito (certificador) | Efeito v6 |
| :-- | :-: | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: | :-: |
| `nori_S8_B0_seed5030` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5031` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5032` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5033` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5030` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5031` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5032` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 84 | 78/78 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5033` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5030` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5031` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5032` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5033` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5030` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5031` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5032` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5033` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |

## Por cenário

| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| S8 | 16 | 16 | 16 | 16 |

## Por baseline

| Baseline | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| B0 | 4 | 4 | 4 | 4 |
| B1 | 4 | 4 | 4 | 4 |
| B2 | 4 | 4 | 4 | 4 |
| B3 | 4 | 4 | 4 | 4 |
