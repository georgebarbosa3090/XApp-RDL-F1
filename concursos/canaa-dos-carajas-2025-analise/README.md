# Análise estatística — Concurso Prefeitura de Canaã dos Carajás/PA 2025 (FGV)

Edital nº 01/2024 · provas objetivas em 23/03, 30/03, 06/04 e 13/04/2025.

| Arquivo | Conteúdo |
|---|---|
| `dist/Analise-Canaa-dos-Carajas-2025-FGV.pdf` | Relatório completo (16 p.) |
| `relatorio.md` | Fonte do relatório |
| `dados/estatisticas_por_cargo.csv` | 56 cargos: vagas, inscritos, aprovados, taxa, corte das vagas, média, acerto por disciplina (geral e na faixa do corte) |
| `dist/Mapa-Questoes-Agente-Administrativo-Canaa-2025.pdf` | Mapa das 50 questões da prova de Agente de Serviços Administrativos: tema do edital, gabarito, resolução e dificuldade |
| `dados/questoes_agente_administrativo.csv` | O mesmo mapa em planilha |
| `dist/Programa-Estudos-FGV-Agente-Administrativo.pdf` | **Programa de estudos** (28 p.): cronograma de 8 semanas, resumos de Português, RLM, Informática e Específicos no estilo FGV, questões resolvidas, outras provas FGV, cursos ENAP e vídeos |
| `dist/Simulados-FGV-Agente-Administrativo.pdf` | **2 simulados com provas reais da FGV** (31 p.): Caraguatatuba 2024 (45 q.) e São José dos Campos 2025 (50 q.), com folha de respostas e gabarito comentado |
| `programa-estudos-fgv/` | Fontes em Markdown do programa e dos simulados |
| `dados/mudancas_gabarito.csv` | Todas as questões anuladas ou com resposta alterada (preliminar → definitivo) |
| `scripts/` | Extração (`parse.py`, `gab.py`) e cálculo (`stats.py`, `agg.py`, `qmap.py`, `report.py`) |

**Fontes oficiais (FGV Conhecimento)**: resultado preliminar e definitivo da prova objetiva (nota de cada aprovado por disciplina), demanda de candidatos por vaga, gabaritos preliminares e definitivos, resultados da prova discursiva e edital retificado.

**Limitação**: a FGV publica notas apenas dos aprovados (11.776); por isso a análise de "o que eliminou" usa os aprovados na faixa do corte (até 2 pontos acima do mínimo) como referência.
