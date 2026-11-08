# Documentação — xApp RDL (Fase 1: H-RDL)

## Documentos principais

| Documento | Conteúdo |
| :-- | :-- |
| [01 — Arquitetura e modelagem](01_arquitetura_e_modelagem.md) | Componentes da xApp, pipeline de decisão, modelos TVS/EEVS, Safety Guard, integração E2 e limitações |
| [02 — Guia operacional](02_guia_operacional_deploy_e_simulacao.md) | Instalação das pilhas ns-3, execução de cenários, experimentos e campanhas, certificação, implantação Helm, solução de problemas |
| [03 — Taxonomia de conflitos e cenários](03_taxonomia_de_conflitos_e_cenarios.md) | Tipos de conflito, cenários S0–S15, propostas das xApps por cenário |
| [04 — Metodologia experimental e resultados](04_metodologia_experimental_e_resultados.md) | Baselines, métricas, proveniência, campanha e resultados |
| [05 — Conformidade O-RAN e auditoria](05_auditoria_e_conformidade_oran.md) | Versões de especificação, estado de cada interface, gates G0–G6, achados e correções |
| [07 — Pré-registro da fase 4, desenho v2](07_preregistro_fase4_v2.md) | Hipóteses, calibração, critérios e regras de relato do efeito causal da decisão H-RDL, registrados antes das execuções, e o resultado (calibração inválida) |
| [07 — Pré-registro da fase 4, desenho v3](07_preregistro_fase4_v3.md) | Calibração por cotas complementares (soma 100 %), hipóteses H4.0–H4.3 e regras de relato, registrados antes das execuções, e o resultado (H4.0 refutada, calibração inválida) |
| [07 — Pré-registro da fase 4, desenho v4](07_preregistro_fase4_v4.md) | Curva teto → vazão (10–30 %) e previsão por interpolação deixa-um-fora, registrados antes das execuções; resultado (curva inválida pela janela) e o achado do atraso de aplicação do Control |
| [07 — Pré-registro da fase 4, desenho v5](07_preregistro_fase4_v5.md) | Janela de efeito ancorada no instante de aplicação do Control, curva v4 como calibração e três avaliações prospectivas, registrados antes das avaliações; resultado: as três `CONSISTENT`, G4 certificado, com ressalvas |
| [23 — Fluxo de mensagens](23_diagrama_sequencia_fluxo_closed_loop_hrdl_fase1.md) | Diagrama de sequência do ciclo subscrição → decisão → controle → ACK |

## Referência

| Pasta | Conteúdo |
| :-- | :-- |
| [`compliance/`](compliance/README.md) | Perfis de compatibilidade, política de evidência, matriz de rastreabilidade, perfil O-RAN SC |
| [`e2/`](e2/version-matrix.md) | Matriz de versões E2 e fontes das especificações |
| [`figures/`](figures/README.md) | Figuras e diagramas |
| [`auditoria/`](auditoria/README.md) | Auditorias anteriores (registro histórico) |
| [`historico/`](historico/README.md) | Relatórios antigos retirados de evidência |

## Outros documentos do repositório

- [`../simulations/ns3/README.md`](../simulations/ns3/README.md) — cenários ns-3, atuação na RAN e catálogo de conflitos
- [`../deploy/helm/nori-ns3/README.md`](../deploy/helm/nori-ns3/README.md) — bancada NORI via Helm
- [`../reproducibility/runbook.md`](../reproducibility/runbook.md) — roteiro de reprodução
- [`../reference-xapps/README.md`](../reference-xapps/README.md) — xApps que geram as propostas

## Convenções

- Status de validação só é declarado com evidência: execução em `experiments/runs/` com manifesto e hashes, ou veredito do certificador. Testes unitários comprovam o comportamento do código, não interoperabilidade.
- Toda mudança de código vem acompanhada da atualização dos documentos afetados no mesmo commit.
