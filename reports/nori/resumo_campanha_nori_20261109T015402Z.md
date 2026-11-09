# Campanha NORI: cenários de conflito com E2 real (20261109T015402Z)

Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas pelo H-RDL e registradas, sem Control.

| Execução | Cadeia | tshark | Msgs | Indications xApp | Estratégias H-RDL | Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito |
| :-- | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: |
| `nori_S0_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT |
| `nori_S0_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT |
| `nori_S0_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT |
| `nori_S0_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT |
| `nori_S0_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S1_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT |
| `nori_S1_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT |
| `nori_S1_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT |
| `nori_S1_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT |
| `nori_S1_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | NOT_TESTABLE |
| `nori_S2_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT |
| `nori_S2_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT |
| `nori_S2_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT |
| `nori_S2_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT |
| `nori_S2_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | NOT_TESTABLE |
| `nori_S3_B3_seed1001` | ✓✓✓··· | ✓ | 84 | 80/80 | TVS | — | xslice TX_POWER g0 | S3-energy_saving-g0-TX_POWER | NOT_TESTABLE |
| `nori_S3_B3_seed1002` | ✓✓✓··· | ✓ | 84 | 78/80 | TVS | — | xslice TX_POWER g0 | S3-energy_saving-g0-TX_POWER | NOT_TESTABLE |
| `nori_S3_B3_seed1003` | ✓✓✓··· | ✓ | 84 | 80/80 | TVS | — | xslice TX_POWER g0 | S3-energy_saving-g0-TX_POWER | NOT_TESTABLE |
| `nori_S3_B3_seed1004` | ✓✓✓··· | ✓ | 84 | 78/80 | TVS | — | xslice TX_POWER g0 | S3-energy_saving-g0-TX_POWER | NOT_TESTABLE |
| `nori_S3_B3_seed1005` | ✓✓✓··· | ✓ | 84 | 80/80 | TVS | — | xslice TX_POWER g0 | S3-energy_saving-g0-TX_POWER | NOT_TESTABLE |
| `nori_S4_B3_seed1001` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S4_B3_seed1002` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S4_B3_seed1003` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S4_B3_seed1004` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S4_B3_seed1005` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; energy_saving TX_POWER g1 | — | NOT_TESTABLE |
| `nori_S5_B3_seed1001` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; load_balancer HANDOVER g1 | — | NOT_TESTABLE |
| `nori_S5_B3_seed1002` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; load_balancer HANDOVER g1 | — | NOT_TESTABLE |
| `nori_S5_B3_seed1003` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; load_balancer HANDOVER g1 | — | NOT_TESTABLE |
| `nori_S5_B3_seed1004` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; load_balancer HANDOVER g1 | — | NOT_TESTABLE |
| `nori_S5_B3_seed1005` | ✓✓✓··· | ✓ | 84 | 80/80 | PASS_THROUGH | — | traffic_steering HANDOVER g0; load_balancer HANDOVER g1 | — | NOT_TESTABLE |
| `nori_S6_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT |
| `nori_S6_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT |
| `nori_S6_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT |
| `nori_S6_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT |
| `nori_S6_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | INCONSISTENT |
| `nori_S7_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT |
| `nori_S7_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT |
| `nori_S7_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT |
| `nori_S7_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT |
| `nori_S7_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | NOT_TESTABLE |
| `nori_S8_B3_seed1001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT |
| `nori_S8_B3_seed1002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT |
| `nori_S8_B3_seed1003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT |
| `nori_S8_B3_seed1004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT |
| `nori_S8_B3_seed1005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | NOT_TESTABLE |

## Por cenário

| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT |
| :-: | --: | --: | --: |
| S0 | 5 | 5 | 4 |
| S1 | 5 | 5 | 4 |
| S2 | 5 | 5 | 4 |
| S3 | 5 | 0 | 0 |
| S4 | 5 | 0 | 0 |
| S5 | 5 | 0 | 0 |
| S6 | 5 | 5 | 4 |
| S7 | 5 | 5 | 0 |
| S8 | 5 | 5 | 4 |
