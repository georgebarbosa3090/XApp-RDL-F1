# Figuras

## Diagramas de sequência da dissertação (revisados em 2026-11-08)

O mesmo fluxo em três formatos, alinhado ao código e sem valores medidos (a troca E2 real ainda não foi exercitada). Descrição completa em [`../01_componentes_e_fluxos.md`](../01_componentes_e_fluxos.md).

| Arquivo | Formato | Uso |
| :-- | :-- | :-- |
| [`diagrama_sequencia_compacto_dissertacao.mermaid`](diagrama_sequencia_compacto_dissertacao.mermaid) | Mermaid | Markdown/GitHub |
| [`diagrama_sequencia_compacto_dissertacao.puml`](diagrama_sequencia_compacto_dissertacao.puml) | PlantUML | `plantuml -tpdf` |
| [`diagrama_sequencia_compacto_dissertacao.tex`](diagrama_sequencia_compacto_dissertacao.tex) | TikZ (standalone) | LaTeX/Overleaf |

## Diagramas de arquitetura e conceituais

`01_arquitetura_e_governanca/` e `01_arquitetura_e_modelagem/` contêm diagramas ilustrativos (pipeline, componentes, infraestrutura, observabilidade, roadmap). Eles representam a arquitetura pretendida; quando divergirem do código, vale a descrição de [`../02_modelo_de_decisao_h_rdl.md`](../02_modelo_de_decisao_h_rdl.md). Em particular, figuras que mostram conformidade O-RAN ou integração E2 retratam objetivos, não interoperabilidade verificada.

## Topologias de cenários

`02_cenarios_e_topologias/` contém ilustrações espaciais dos cenários. Parte dos arquivos usa uma numeração antiga (por exemplo, `scenario_1_eevs_*`, `scenario_3_5ga_*`) que não corresponde aos identificadores S0–S15 atuais; a correspondência válida está em [`../03_cenarios_e_conflitos.md`](../03_cenarios_e_conflitos.md).

## Gráficos de resultados antigos — não são evidência

Os gráficos abaixo foram gerados antes de novembro de 2026 a partir de `experiments/results/canonical_simulation_master.csv`, da campanha `S1_B0..B6_seed1001..1030` (produzida com `numpy.random`) ou de demonstrações cujo E2 era texto fixo. **Não os use em publicações.**

- `fig_01_*.png` a `fig_40_*.png` (raiz desta pasta) e as cópias em `01_modelos_analiticos_e_conceituais/`
- `02_cenarios_e_topologias/comparacao_multissemente_b0_b3.*` e `pareamento_b1_b3.*`
- os manifestos `figures_manifest.json` e `02_cenarios_e_topologias/manifesto_proveniencia.json`, que os descrevem como derivados de execuções reais

Gráficos de resultados válidos devem ser gerados a partir das execuções `experiments/runs/nr_*` (via [`analyze_conflict_runs.py`](../../scripts/certification/analyze_conflict_runs.py)) e citar os `run_id` usados.
