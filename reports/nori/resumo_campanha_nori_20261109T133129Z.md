# Campanha NORI: cenários de conflito com E2 real (20261109T133129Z)

Gerado por `scripts/certification/nori_campaign_summary.py`. Papéis da cadeia na ordem E2 Setup, Subscription, KPM_t0, Control, ACK, KPM_t1 (✓ presente no PCAP, · ausente). Só PRB_QUOTA no gNB 0 é atuável no NORI; potência, handover e ações em outros gNBs são decididas pelo H-RDL e registradas, sem Control.

| Execução | Baseline (fonte da decisão) | Cadeia | tshark | Msgs | Indications xApp | Estratégias H-RDL | Atuado (E2SM-RC) | Decidido, não atuável no NORI | Não selecionadas | Efeito (certificador) | Efeito v6 |
| :-- | :-: | :-: | :-: | --: | :-: | :-- | :-- | :-- | :-- | :-: | :-: |
| `nori_S8_B0_pairfix_seed9101` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_pairfix_seed9102` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_pairfix_seed9103` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_pairfix_seed9104` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 86 | 78/78 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |
| `nori_S8_B0_pairfix_seed9105` | B0 (BASELINE_B0) | ✓✓✓✓✓✓ | ✓ | 88 | 80/80 | — | xslice → eMBB 25 / URLLC 75 | — | — | CONSISTENT | CONSISTENT |

## Por cenário

| Cenário | Execuções | Cadeia completa | Efeito CONSISTENT | Efeito v6 CONSISTENT |
| :-: | --: | --: | --: | --: |
| S8 | 5 | 5 | 5 | 5 |
