# Campanha NORI: cenários de conflito com E2 real (20261109T130646Z)

Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas pelo H-RDL e registradas, sem Control.

| Execução | Baseline (fonte da decisão) | Cadeia | tshark | Msgs | Indications xApp | Estratégias H-RDL | Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito (certificador) | Efeito v6 |
| :-- | :-: | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: | :-: |
| `nori_S8_B0_seed5001` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 86 | 78/78 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5002` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5003` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5004` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5005` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5006` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5007` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5008` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5009` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5010` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5011` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5012` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 79/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5013` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5014` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5015` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5016` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5017` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5018` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5019` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5020` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5021` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5022` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5023` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5024` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5025` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5026` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5027` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5028` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5029` | B0 (—) | ······ | ✓ | 1 | 0/0 | — | — | — | — | NOT_TESTABLE | NOT_TESTABLE |
| `nori_S8_B0_seed5030` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5031` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5032` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_seed5033` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5001` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5002` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5003` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5004` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5005` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5006` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5007` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5008` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5009` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5010` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5011` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5012` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5013` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5014` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5015` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5016` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5017` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5018` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5019` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5020` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5021` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5022` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5023` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5024` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5025` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5026` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5027` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5028` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5029` | B1 (—) | ······ | ✓ | 1 | 0/0 | — | — | — | — | NOT_TESTABLE | NOT_TESTABLE |
| `nori_S8_B1_seed5030` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5031` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5032` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 84 | 78/78 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B1_seed5033` | B1 (BASELINE_B1) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5001` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5002` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5003` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5004` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5005` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5006` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5007` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5008` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5009` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5010` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5011` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5012` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5013` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5014` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5015` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5016` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5017` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5018` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5019` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5020` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5021` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5022` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5023` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5024` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5025` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5026` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5027` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5028` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 28/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5030` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5031` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5032` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B2_seed5033` | B2 (BASELINE_B2) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | S8-embb_throughput-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5001` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5002` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5003` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5004` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5005` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5006` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5007` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5008` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5009` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5010` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5011` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5012` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5013` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 84 | 78/78 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5014` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5015` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5016` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5017` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5018` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5019` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5020` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5021` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 84 | 78/78 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5022` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5023` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5024` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5025` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5026` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5027` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5028` | B3 (—) | ······ | ✓ | 1 | 0/0 | PASS_THROUGH | — | — | — | NOT_TESTABLE | NOT_TESTABLE |
| `nori_S8_B3_seed5029` | B3 (—) | ······ | ✓ | 1 | 0/0 | PASS_THROUGH | — | — | — | NOT_TESTABLE | NOT_TESTABLE |
| `nori_S8_B3_seed5030` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5031` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5032` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed5033` | B3 (H_RDL) | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |

## Por cenário

| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| S8 | 131 | 127 | 127 | 127 |

## Por baseline

| Baseline | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| B0 | 33 | 32 | 32 | 32 |
| B1 | 33 | 32 | 32 | 32 |
| B2 | 32 | 32 | 32 | 32 |
| B3 | 33 | 31 | 31 | 31 |
