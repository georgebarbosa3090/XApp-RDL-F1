# Autoria

## Autor

**George Barbosa** — autor do software próprio deste repositório (xApp RDL, Fase 1 – RDL-N1), licenciado sob Apache-2.0 ([`LICENSE`](LICENSE)).

## Software próprio

Escrito para este projeto. Os arquivos principais trazem o cabeçalho `Autor: George Barbosa`.

| Componente | Caminho |
| :-- | :-- |
| xApp RDL (percepção, TVS/EEVS, Safety Guard, janela de decisão, governança, grafo de conhecimento, A1, E2) | `src/` |
| RANSlicer-GreenRAN e EnergySaver-GreenRAN do GreenRAN | `src/greenran/` |
| Perfis de backend do testbed (NORI, srsRAN, OAI) | `src/e2/backends/testbed_profiles.py`, `configs/testbed_ufpa/backends/` |
| kpm-probe (xApp que fecha o loop E2 real na bancada NORI) | `deploy/helm/xapp-kpm-probe/files/kpm_probe.py` |
| rApp-ResourceOptimizer e rApp de governança | `rapps/` |
| xApps de referência: Rogue e transporte RMR comum | `reference-xapps/rogue-xapp/`, `reference-xapps/common/` |
| xApps de referência reimplementadas em Python, inspiradas em trabalhos de terceiros (sem código deles): xSlice, Energy Saving, Traffic Steering | `reference-xapps/qos-xslice/`, `reference-xapps/energy-saving/`, `reference-xapps/traffic-steering/` |
| Cenários ns-3/5G-LENA, harness de atuação, certificador, campanhas, charts Helm e documentação | `simulations/`, `scripts/`, `deploy/helm/`, `docs/` |

## Código de terceiros

Copiado **sem modificação**, só para registro de procedência das xApps inspiradas. Não é compilado nem importado por este projeto e não faz parte do software próprio. Cada pasta tem a licença original e um `SOURCE.md` com repositório, commit e sha256 de cada arquivo.

| Pasta | Origem | Licença | Usada como referência por |
| :-- | :-- | :-- | :-- |
| [`third_party/xapps/ric-app-ts`](third_party/xapps/ric-app-ts/SOURCE.md) | o-ran-sc/ric-app-ts (Traffic Steering) | Apache-2.0 | `reference-xapps/traffic-steering` |
| [`third_party/xapps/xslice-oran`](third_party/xapps/xslice-oran/SOURCE.md) | peihaoY/xslice-oran (xSlice, Yan et al.) | OAI Public License v1.1 | `reference-xapps/qos-xslice` |
| [`third_party/xapps/flexric-orange-es`](third_party/xapps/flexric-orange-es/SOURCE.md) | mosaic5g/flexric, ramo `oie-ric-taap-xapps` (Energy Saving da Orange) | Collaborative Standards Software License v1.0 | `reference-xapps/energy-saving` |

Dependências de execução (O-RAN SC `ricxappframe`, NORI, ns-3, 5G-LENA, A1-PMS, Neo4j etc.) são usadas como bibliotecas, imagens ou ferramentas externas, com as licenças delas, e não estão neste repositório.
