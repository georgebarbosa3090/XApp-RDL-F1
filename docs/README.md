# Documentação — xApp RDL (Fase 1: H-RDL)

## Por onde começar

| Se você quer… | Leia |
| :-- | :-- |
| entender as peças do projeto, quem fala com quem e por qual protocolo | [01 — Componentes e fluxos](01_componentes_e_fluxos.md) |
| entender como a H-RDL decide | [02 — Modelo de decisão](02_modelo_de_decisao_h_rdl.md) |
| saber o que cada cenário testa | [03 — Cenários e conflitos](03_cenarios_e_conflitos.md) |
| instalar e rodar a bancada | [04 — Instalação e operação](04_instalacao_e_operacao.md) |
| acompanhar uma execução ao vivo ou rodar uma campanha | [05 — Observabilidade e campanhas](05_observabilidade_e_campanhas.md) |
| ver os resultados | [06 — Metodologia e resultados](06_metodologia_e_resultados.md) |
| saber o que está certificado e o que foi corrigido | [07 — Certificação, conformidade e achados](07_certificacao_e_achados.md) |
| conferir o que foi fixado antes de cada avaliação | [Pré-registros](preregistros/README.md) |

## Documentos principais

| # | Documento | Conteúdo |
| :-: | :-- | :-- |
| 01 | [Componentes e fluxos](01_componentes_e_fluxos.md) | O que é simulado, emulado ou real. Quem se registra em quem. Protocolos, portas, tipos de mensagem RMR e identificadores E2. O que cada ação faz em cada pilha. Componentes do NORI. PCAP e tshark. Diagramas de cada fluxo: registro, subscrição, KPM, decisão e Control, efeito, certificação, observabilidade e pilha nativa |
| 02 | [Modelo de decisão da H-RDL](02_modelo_de_decisao_h_rdl.md) | Modos de operação, entrada de propostas, Safety Guard, percepção, TVS/EEVS, Refinement, parâmetros controláveis, integração E2 da `RDLxApp`, limitações |
| 03 | [Cenários e conflitos](03_cenarios_e_conflitos.md) | Tipos de conflito, cenários S0–S8 e o que cada um atua na bancada NORI |
| 04 | [Instalação e operação](04_instalacao_e_operacao.md) | Ambiente, pilha nativa, execução com proveniência, campanhas, certificação, k3s, Near-RT RIC, NORI, xApp `kpm-probe`, dissecação do PCAP, Helm, solução de problemas |
| 05 | [Observabilidade e campanhas](05_observabilidade_e_campanhas.md) | Painel tmux, comandos de cada aba ao vivo (NORI, E2AP, xApp, RIC, Kubernetes, UEs), InfluxDB e Grafana, campanhas NORI e nativa |
| 06 | [Metodologia e resultados](06_metodologia_e_resultados.md) | Pergunta, desenho, métricas, proveniência, resultados da pilha nativa e da bancada com E2 real (fases 1–4, campanha S0–S8, v6, v7, G5), ameaças à validade |
| 07 | [Certificação, conformidade e achados](07_certificacao_e_achados.md) | Versões de especificação, estado por interface, gates G0–G6, registro de achados e correções |
| 09 | [Frameworks e ações críticas](09_frameworks_e_acoes_criticas.md) | Frameworks avaliados para o GreenRAN; classes de urgência e alternativas fora da RDL (dApps, E2SM-RC Policy, guarda na DU, A1) |
| 10 | [SMO, Non-RT RIC e rApp](10_smo_non_rt_ric_e_rapp.md) | A1-PMS do O-RAN SC na bancada, A1 via RMR, fluxo de ML do MAPPO, passo a passo do SMO completo |
| — | [Pré-registros](preregistros/README.md) | Desenhos v2–v7 da fase 4, campanha do G5 e conflitos entre células (08), cada um com o resultado registrado depois |

## Glossário curto

| Termo | Significado |
| :-- | :-- |
| H-RDL | a camada de decisão da Fase 1: Safety Guard, TVS/EEVS e Refinement |
| NORI | módulo E2 para o ns-3 + 5G-LENA (`lasseufpa/nori`); na bancada, o gNB simulado fala E2 real com o RIC |
| KPM_t0 / KPM_t1 | o relatório KPM antes do Control (que dispara a decisão) e o primeiro depois dele |
| B0–B3 | baselines: sem coordenação, FIFO, prioridade estática e H-RDL |
| G0–G6 | gates de evidência avaliados pelo certificador |
| MEID | identificador do nó E2 usado pelo RMR para rotear o Control (`gnb_268_341_00000001` na bancada) |
| RMR | o roteador de mensagens interno do Near-RT RIC |

## Referência

| Pasta | Conteúdo |
| :-- | :-- |
| [`compliance/`](compliance/README.md) | Perfis de compatibilidade, política de evidência, matriz de rastreabilidade, perfil O-RAN SC |
| [`e2/`](e2/version-matrix.md) | Matriz de versões E2 e fontes das especificações |
| [`figures/`](figures/README.md) | Figuras e diagramas |
| [`preregistros/`](preregistros/README.md) | Pré-registros das avaliações |

## Outros documentos do repositório

- [`../simulations/ns3/README.md`](../simulations/ns3/README.md): cenários ns-3, atuação na RAN e catálogo de conflitos.
- [`../deploy/helm/nori-ns3/README.md`](../deploy/helm/nori-ns3/README.md): bancada NORI via Helm.
- [`../deploy/helm/xapp-kpm-probe/README.md`](../deploy/helm/xapp-kpm-probe/README.md): xApp da bancada.
- [`../reproducibility/runbook.md`](../reproducibility/runbook.md): roteiro de reprodução.
- [`../reference-xapps/README.md`](../reference-xapps/README.md): xApps que geram as propostas.

## Convenções

- Status de validação só é declarado com evidência: uma execução em `experiments/runs/` com manifesto e hashes, ou um veredito do certificador. Testes unitários comprovam o comportamento do código, não a interoperabilidade.
- Toda mudança de código vem acompanhada da atualização dos documentos afetados, no mesmo commit.
- Os documentos são numerados na ordem de leitura. Rascunhos locais ficam em `docs/local/`, que não vai para o repositório.
