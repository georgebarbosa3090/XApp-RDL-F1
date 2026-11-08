# Documentos históricos

Relatórios produzidos antes de novembro de 2026, mantidos para rastreabilidade do projeto. **Nenhum deles é evidência experimental.** Os números que contêm não vêm de execuções com proveniência verificável.

| Documento | Por que não é evidência |
| :-- | :-- |
| [04 — Relatório científico mestre](04_relatorio_cientifico_mestre_rdl.md) | Usa a campanha `S1_B0..B6_seed1001..1030`, gerada por `scripts/run_b0_b6_campaign_30seeds.py` com `numpy.random`, e FlowMonitor de cenários que não aplicavam conflitos. |
| [07 — Resultados de baselines B0–B6](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md) | Tabelas derivadas das mesmas 210 execuções sintéticas. |
| [20 — Relatório FlowMonitor S0–S15](20_relatorio_experimental_ns3_flowmonitor_s0_s15.md) | Na época, nenhum cenário alterava a RAN durante a simulação; S0 e S4–S7 não anexavam os UEs (FlowMonitor vazio) e os arquivos de S8 eram cópias byte a byte dos de S3. Os arquivos não têm manifesto nem hashes. |
| [21 — Demonstração closed loop](21_relatorio_demonstracao_rica_closed_loop.md) | O "handshake E2" exibido era texto fixo impresso pelo cenário (`TraceLifecycleE2`), não troca E2 real. |

Como ler: os textos descrevem intenções e desenho experimental que ainda podem ser úteis, mas qualquer valor numérico deve ser ignorado. Os resultados atuais estão em [`../04_metodologia_experimental_e_resultados.md`](../04_metodologia_experimental_e_resultados.md), e as auditorias anteriores em [`../auditoria/`](../auditoria/README.md).

Alguns links internos destes documentos apontam para volumes que nunca existiram no repositório (06, 22, 24) ou para figuras de resultados antigos; eles foram mantidos como estavam.
