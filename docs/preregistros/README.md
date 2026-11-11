# Pré-registros

Cada pré-registro foi escrito e commitado **antes** das execuções que avalia. Ele fixa:

- as hipóteses;
- a calibração;
- os critérios de aceite;
- as regras de relato.

O resultado é anexado depois, sem alterar o que foi fixado. A ordem é cronológica. Os resultados resumidos estão em [06 §5](../06_metodologia_e_resultados.md#5-resultados-com-e2-real-bancada-nori).

| # | Pré-registro | O que testa | Resultado |
| :-: | :-- | :-- | :-- |
| 01 | [Fase 4, desenho v2](01_fase4_v2.md) | efeito causal da decisão H-RDL na RAN, com calibração de teto de 30 % | calibração inválida; avaliações não rodadas |
| 02 | [Fase 4, desenho v3](02_fase4_v3.md) | calibração por cotas complementares (soma 100 %), H4.0–H4.3 | H4.0 refutada; calibração inválida |
| 03 | [Fase 4, desenho v4](03_fase4_v4.md) | curva teto → vazão (10–30 %) e previsão deixa-um-fora | curva inválida pela janela; achado do atraso de aplicação do Control |
| 04 | [Fase 4, desenho v5](04_fase4_v5.md) | janela ancorada no instante de aplicação do Control, três avaliações | três `CONSISTENT`; G4 certificado, com ressalvas |
| 05 | [Fase 4, desenho v6](05_fase4_v6.md) | efeito relativo à vazão sem restrição (achados 41 e 42), H6.1–H6.4, sementes 2001–2005 | 30/30 `CONSISTENT`; regra adotada no G4 |
| 06 | [Fase 4, desenho v7](06_fase4_v7.md) | teste da H6.4: outra vazão de base (50 MHz), sementes 4001–4005 | 30/30 `INCONSISTENT`; H6.4 refutada para mudança de banda (teto em PRBs absolutos) |
| 07 | [Campanha do G5](07_campanha_g5_s8.md) | S8 × B0–B3 × sementes 5001–5030 com E2 real, H8.1–H8.3 | G5 certificado (30 pares); desvios e reposições declarados |
| 08 | [Conflitos entre células: S4 e S5](08_conflitos_entre_celulas_s4_s5.md) | decisão `INTER_CELL` do B3 na RAN simulada, S4/S5 × B0–B3 × sementes 1006–1010, H9.1–H9.3 | H9.1 confirmada (10/10); H9.2 refutada no S5/B3 (handovers sem UEs); H9.3 refutada (vazão do S4 menor no B3); S5: ping-pong suprimido melhorou vazão e atraso |
| 09 | [EEVS aditivo](09_eevs_aditivo.md) | B3A × B3 em S2, S13 e S15, sementes 12001–12005, H10.1–H10.3 | pendente |
| 10 | [Campanha S9–S15, G1 e G2](10_campanha_s9_s15_g1_g2.md) | 9 cenários × B0–B3 × sementes 11001–11005 (180 execuções), H11.1–H11.5 | agendada para 2026-11-12 9h |
