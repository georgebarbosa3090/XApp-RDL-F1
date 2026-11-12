# Relatório técnico — desenvolvimento e governança de rApps no Non-RT RIC

Data: 2026-11-11. Escopo: levantamento de trabalhos, especificações e frameworks sobre o desenvolvimento de rApps e sobre como a governança de rApps acontece no O-RAN, e o que isso implica para a RDL (Fase 1) e para o testbed GreenRAN da UFPA.

**Método e limites.** Busca na web (especificações O-RAN/ETSI, documentação do O-RAN SC, arXiv, periódicos e blogs técnicos de fornecedores). Foram lidos resumos, índices e trechos, não os textos completos. Onde só o índice ou o resumo foi visto, isso está indicado. Nenhum procedimento normativo foi conferido no texto integral da especificação.

---

## 1. Conclusões

| Pergunta | Resposta curta |
| :-- | :-- |
| Há trabalhos sobre desenvolvimento de rApps? | Poucos e recentes. O mais direto é um framework de desenvolvimento e validação de rApps com IA/ML (Kim et al., 2026). O resto vem da especificação (interface R1), do projeto open source do O-RAN SC e de fornecedores. |
| Como a governança de rApps acontece? | Em camadas, no Non-RT RIC/SMO: pacote e ciclo de vida (rApp Manager), acesso a serviços só pela R1 com registro, descoberta e autorização (SME/CAPIF), acesso a dados controlado (DME) e saída para a RAN centralizada no A1-PMS. |
| Há tratamento padronizado de conflito entre rApps? | Não maduro. A pesquisa de conflitos se concentra em xApps no Near-RT RIC. Para rApps, a proposta mais concreta é de fornecedor: conflitos tratados no SMO por regras configuráveis, a partir das dependências declaradas pelas rApps. |
| O que muda no projeto? | A RDL já tratava o conflito **vertical** (rApp × xApp): a política A1 ajusta pesos, limites e modos da decisão, sem virar ação. Faltava o **horizontal** (rApp × rApp) na política A1, agora implementado como dono e precedência por campo (achado 64; [doc 11 §5.1](../../docs/11_governanca_hierarquica_xapps.md)). |

---

## 2. Trabalhos e frameworks sobre desenvolvimento de rApps

### 2.1 Acadêmicos

| Trabalho | Contribuição | O que foi lido |
| :-- | :-- | :-- |
| Kim et al., *A development and validation framework for AI/ML-driven rApps in open RAN*, EURASIP JWCN, 2026, DOI 10.1186/s13638-026-02601-0 | framework integrado para o ciclo de vida de rApps com IA/ML, do protótipo à verificação funcional, sobre uma arquitetura de Non-RT RIC aderente à norma, com testes de sinalização R1/O1 em emulador | resumo |
| Polese et al., *Understanding O-RAN: Architecture, Interfaces, Algorithms, Security, and Research Challenges*, IEEE COMST, 2023 (arXiv 2202.01032) | referência geral de O-RAN; registra que a especificação não fixava com rigor a divisão de funções entre SMO e Non-RT RIC | resumo e trechos |
| Alam et al., tutorial e survey de O-RAN (arXiv 2405.03555, IEEE COMST) | arquitetura, opções de implantação e casos de uso, com o papel do Non-RT RIC | resumo |
| Artigo sobre zero trust em O-RAN (arXiv 2511.18568) | a R1 como fronteira de API das rApps, inclusive na comunicação entre rApps | trechos |
| Visão geral de Open RAN nativo em IA para redes não terrestres (arXiv 2507.11935) | rApps como módulos de terceiros que rodam em qualquer Non-RT RIC, em escalas acima de 1 s | trechos |
| Tese da Universidade Técnica de Poznań | seções sobre rApps no Non-RT RIC, desafios e frameworks de mitigação de conflitos | só o sumário |

### 2.2 Especificação

- **O-RAN.WG2 R1GAP** (*R1 interface: General Aspects and Principles*), publicada como **ETSI TS 104 228 V11.0.0 (2026-02)**. O índice traz seções de registro de serviço, descoberta, autenticação e autorização, e registro de rApp. Pelas notas de versão da O-RAN Alliance, a atualização e o cancelamento do registro de rApp foram movidos para a parte de SME (Service Management and Exposure), e uma especificação própria traz a estrutura das APIs da SME. Só o índice foi visto.

### 2.3 Open source — O-RAN SC, projeto NONRTRIC

O mesmo projeto fornece o A1-PMS usado na bancada (doc 10).

| Componente | Papel |
| :-- | :-- |
| **rApp Manager** | ciclo de vida da rApp; integrado ao ACM (Automation Composition Management) do ONAP e, por ele, à SME, à DME, ao A1-PMS, ao KServe e ao Kubernetes. O pacote da rApp descreve os serviços que ela produz e consome. |
| **Service Manager** | implementa a exposição de serviços da R1 sobre o **CAPIF** do 3GPP: registro e cancelamento, publicação, entrada e saída de consumidores de API e descoberta. Uma rApp só acessa um serviço publicado por ele. A autorização usa tokens Keycloak/JWT. |
| **ICS / DME** | coordenação de informação, papel de DME (gestão e exposição de dados) para as rApps. A própria documentação diz que ainda não implementa fielmente a R1-DME. |
| **Requisitos do projeto** | rApps consomem serviços só pela R1, e os serviços da plataforma são expostos pela R1. |

### 2.4 Indústria

- **Ericsson (2023):** a R1 é a camada que liga as rApps aos serviços do SMO e do Non-RT RIC e permite que uma rApp rode em plataformas de fornecedores diferentes.
- **Ericsson (2024):** como hospedeiro das rApps, o SMO/Non-RT RIC deve conduzir a gestão de conflitos entre elas. Propõe uma abordagem por políticas: as dependências de dados e de API declaradas pelas rApps alimentam uma lógica de conflito configurável em tempo de execução, sem mudar o software da plataforma nem das rApps.

---

## 3. Como a governança de rApps acontece

| Camada | Mecanismo | Onde está |
| :-- | :-- | :-- |
| 1. Pacote e ciclo de vida | a rApp declara no pacote os serviços e dados que produz e consome; o rApp Manager faz integração, implantação, atualização e remoção | rApp Manager + ACM (O-RAN SC) |
| 2. Acesso a serviços | toda chamada passa pela R1: registro, descoberta, autenticação e autorização via CAPIF; uma rApp não alcança serviço que não foi exposto a ela | Service Manager / SME |
| 3. Acesso a dados | produtores e consumidores de cada tipo de dado são registrados; a plataforma controla quem lê o quê | ICS / DME |
| 4. Saída para a RAN | as políticas A1 de todas as rApps passam pelo A1-PMS, que as associa ao serviço que as criou, mantém o estado e fala com o Near-RT RIC | A1-PMS |
| 5. Conflitos entre rApps | não padronizado; proposta de fornecedor: regras no SMO a partir das dependências declaradas | — |

**Tipos de conflito.** Os resumos de dois artigos do arXiv sobre conflitos em O-RAN (2311.13389 e 2411.03326) trazem a distinção usada neste relatório; não foi conferido qual dos dois a define:

- **Horizontais:** entre componentes do mesmo nível (xApp × xApp, rApp × rApp).
- **Verticais:** entre níveis (decisão do Near-RT RIC × política do Non-RT RIC).

A mesma literatura registra que a coordenação e a mitigação de conflitos costumam ficar a cargo da plataforma (RIC ou SMO), não das próprias aplicações.

**Lacuna.** Quase toda a pesquisa de conflitos encontrada trata de xApps no Near-RT RIC. Não foi encontrado um survey dedicado à governança e ao ciclo de vida de rApps.

---

## 4. Implicações para a RDL e o projeto

### 4.1 Conflito vertical (rApp × xApp)

Já tratado. Na RDL, a política A1 não é uma ação a arbitrar: ela ajusta pesos (TVS/EEVS), limites (Safety Guard), regras entre células, alvos críticos e modos de supervisão das xApps ([doc 02 §7.1](../../docs/02_modelo_de_decisao_h_rdl.md)). A decisão de curto prazo continua no Near-RT RIC.

### 4.2 Conflito horizontal entre rApps na política A1

**Era uma lacuna; foi corrigido nesta data.** O `A1PolicyManager` juntava as instâncias A1 ativas com a escrita mais recente vencendo em cada campo. Dois rApps, ou um rApp e o operador, escrevendo o mesmo campo se sobrescreviam sem aviso (achado 64).

**Implementado** ([doc 11 §5.1](../../docs/11_governanca_hierarquica_xapps.md), `src/interfaces/a1_policy_receiver.py`, `tests/unit/test_a1_field_owners.py`):

- **Mapa de donos** (`RDL_A1_FIELD_OWNERS`; exemplo em `configs/a1_field_owners.example.json`): para cada tipo e campo, padrões de `policy_instance_id` em ordem de precedência. O operador usa o prefixo `operator`.
- **Escrita fora do dono:** a instância é recusada, com `status = ERROR` na resposta A1 20011, e fica `NOT_ENFORCED` no A1-PMS.
- **Precedência:** vence o primeiro dono da lista, mesmo que tenha escrito antes; entre iguais, a escrita mais recente.
- **Conflito entre rApps:** quando duas instâncias têm valores diferentes no mesmo campo, ele é reportado em `GET /governance` (`rapp_conflicts`), no log e na métrica `rdl_a1_field_conflicts`. O rApp de governança o transforma em recomendação `RESOLVE_A1_FIELD_CONFLICT` para o operador.

**Limite que a RDL não fecha.** O A1 Mediator repassa à xApp só o ID da instância, não o serviço do A1-PMS. Um rApp que use o nome de instância de outro o sobrescreve. A autorização forte é da R1/CAPIF no SMO (seção 3, camada 2).

### 4.3 Bancada e testbed GreenRAN

| Item | Bancada (hoje) | Testbed UFPA (recomendado) |
| :-- | :-- | :-- |
| Non-RT RIC | só o A1-PMS 2.8.0 com adaptador para o A1 Mediator da Release I (doc 10) | Non-RT RIC completo do O-RAN SC ou do ONAP (doc 10, passo a passo) |
| Ciclo de vida das rApps | manual (scripts em `rapps/`) | rApp Manager + ACM; pacotes com os serviços declarados |
| Autorização das rApps | não há; identidade pelo ID da instância A1 | R1 via Service Manager (CAPIF), uma identidade por rApp |
| Dados para as rApps | `GET /governance`, `/kg`, métricas Prometheus; histórico no Neo4j (chart `kg-neo4j`) | DME/ICS para os tipos de dado da RDL (recusas, conflitos implícitos, grafo) |
| Conflito entre rApps | dono e precedência por campo na RDL (seção 4.2) | o mesmo mapa, com identidades vindas da R1 em vez do ID da instância |

### 4.4 Recomendações

1. Combinar com a UFRGS (rApp-ResourceOptimizer) os nomes das instâncias A1 e o mapa de donos dos campos 20000/20001 antes da integração no testbed.
2. Registrar os dados da RDL (recusas, conflitos implícitos, grafo) como tipos de dado da DME no SMO completo, para que os rApps os consumam pela R1, e não por HTTP direto à xApp.
3. Acompanhar a R1GAP/SME (ETSI TS 104 228) e o rApp Manager do O-RAN SC, para passar a identidade do rApp à RDL quando a plataforma a expuser.

---

## 5. Referências

- Kim et al., EURASIP JWCN, 2026 — https://doi.org/10.1186/s13638-026-02601-0
- O-RAN SC NONRTRIC, visão geral — https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric/en/latest/overview.html
- O-RAN SC NONRTRIC, requisitos — https://o-ran-sc-nonrtric.readthedocs.io/en/stable/requirements.html
- O-RAN SC Service Manager (SME/CAPIF) — https://docs.o-ran-sc.org/projects/o-ran-sc-nonrtric-plt-sme/en/latest/overview.html
- O-RAN SC rApp Manager (apresentação, nov/2023) — https://wiki.o-ran-sc.org/download/attachments/100499474/20231121%20-%20NONRTRIC%20-%20rApp%20manager.pdf?api=v2
- O-RAN SC, exposição de serviços (apresentação, 2022) — https://wiki.o-ran-sc.org/download/attachments/51905338/20220511-OSC-NONRTRIC-service-exposure.pdf?api=v2
- ETSI TS 104 228 V11.0.0 (O-RAN R1GAP) — https://etsi.org/deliver/etsi_ts/104200_104299/104228/11.00.00_60/ts_104228v110000p.pdf
- O-RAN Alliance, especificações publicadas desde março/2023 — https://o-ran.org/blog/57-new-or-updated-o-ran-specifications-released-since-march-2023
- Ericsson, interface R1 (2023) — https://www.ericsson.com/en/blog/2023/12/how-the-o-ran-alliance-r1-interface-empowers-a-global-ran-automation-community
- Ericsson, benefícios de rApps e gestão de conflitos (2024) — https://www.ericsson.com/en/blog/2024/6/the-benefits-of-rapps-for-ran-automation
- Polese et al., Understanding O-RAN (arXiv 2202.01032) — https://arxiv.org/pdf/2202.01032
- Alam et al., survey O-RAN (arXiv 2405.03555) — https://arxiv.org/html/2405.03555v6
- Zero trust em O-RAN (arXiv 2511.18568) — https://arxiv.org/pdf/2511.18568
- Open RAN nativo em IA para redes não terrestres (arXiv 2507.11935) — https://arxiv.org/pdf/2507.11935
- Conflitos em O-RAN (arXiv 2311.13389 e 2411.03326) — https://arxiv.org/pdf/2311.13389 , https://www.arxiv.org/pdf/2411.03326
- Tese, Universidade Técnica de Poznań — https://bip.put.poznan.pl/attachments/11115/download/rozprawa
