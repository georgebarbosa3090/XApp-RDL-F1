# Análise estatística — Concurso Prefeitura de Canaã dos Carajás/PA 2025 (FGV)

Edital nº 01/2024 · provas objetivas em 23/03, 30/03, 06/04 e 13/04/2025.

| Arquivo | Conteúdo |
|---|---|
| `dist/Analise-Canaa-dos-Carajas-2025-FGV.pdf` | Relatório completo (16 p.) |
| `relatorio.md` | Fonte do relatório |
| `dados/estatisticas_por_cargo.csv` | 56 cargos: vagas, inscritos, aprovados, taxa, corte das vagas, média, acerto por disciplina (geral e na faixa do corte) |
| `dados/mudancas_gabarito.csv` | Todas as questões anuladas ou com resposta alterada (preliminar → definitivo) |
| `scripts/` | Extração (`parse.py`, `gab.py`) e cálculo (`stats.py`, `agg.py`, `qmap.py`, `report.py`) |

**Fontes oficiais (FGV Conhecimento)**: resultado preliminar e definitivo da prova objetiva (nota de cada aprovado por disciplina), demanda de candidatos por vaga, gabaritos preliminares e definitivos, resultados da prova discursiva e edital retificado.

**Limitação**: a FGV publica notas apenas dos aprovados (11.776); por isso a análise de "o que eliminou" usa os aprovados na faixa do corte (até 2 pontos acima do mínimo) como referência.
