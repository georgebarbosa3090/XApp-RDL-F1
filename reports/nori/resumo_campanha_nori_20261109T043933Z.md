# Campanha NORI: cenários de conflito com E2 real (20261109T043933Z)

Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas pelo H-RDL e registradas, sem Control.

| Execução | Cadeia | tshark | Msgs | Indications xApp | Estratégias H-RDL | Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito (certificador) | Efeito v6 |
| :-- | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: | :-: |
| `nori_S0_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT | CONSISTENT |
| `nori_S0_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT | CONSISTENT |
| `nori_S0_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT | CONSISTENT |
| `nori_S0_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT | CONSISTENT |
| `nori_S0_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 80 / URLLC 20 | energy_saving TX_POWER g1 | — | CONSISTENT | CONSISTENT |
| `nori_S1_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S1_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S1_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S1_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S1_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | xslice → eMBB 75 / URLLC 25 | — | S1-energy_saving-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S2_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT | CONSISTENT |
| `nori_S2_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT | CONSISTENT |
| `nori_S2_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT | CONSISTENT |
| `nori_S2_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT | CONSISTENT |
| `nori_S2_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | EEVS | xslice → eMBB 80 / URLLC 20 | — | S2-traffic_steering-g0-HANDOVER | CONSISTENT | CONSISTENT |
| `nori_S6_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S6_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S6_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 84 | 78/78 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S6_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S6_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS,TVS,TVS,EEVS | xslice → eMBB 85 / URLLC 15 | load_balancer PRB_QUOTA g1; energy_saving TX_POWER g1; beamformer TX_POWER g2; xslice PRB_QUOTA g3 | S6-energy_saving-g0-PRB_QUOTA, S6-energy_saving-g2-TX_POWER, S6-isac_radar-g3-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S7_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT | CONSISTENT |
| `nori_S7_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT | CONSISTENT |
| `nori_S7_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT | CONSISTENT |
| `nori_S7_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 78/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT | CONSISTENT |
| `nori_S7_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | PASS_THROUGH | xslice → eMBB 70 / URLLC 30 | — | S7-rogue_xapp-g0-TX_POWER, S7-rogue_xapp-g1-PRB_QUOTA | INCONSISTENT | CONSISTENT |
| `nori_S8_B3_seed2001` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed2002` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed2003` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed2004` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |
| `nori_S8_B3_seed2005` | ✓✓✓✓✓✓ | ✓ | 86 | 80/80 | TVS | embb_throughput → eMBB 80 / URLLC 20 | — | S8-xslice-g0-PRB_QUOTA | CONSISTENT | CONSISTENT |

## Por cenário

| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| S0 | 5 | 5 | 5 | 5 |
| S1 | 5 | 5 | 5 | 5 |
| S2 | 5 | 5 | 5 | 5 |
| S6 | 5 | 5 | 5 | 5 |
| S7 | 5 | 5 | 0 | 5 |
| S8 | 5 | 5 | 5 | 5 |
