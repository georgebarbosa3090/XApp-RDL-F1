# Módulo 11 — Específicos 6: Governança, Gestão e Contratação de TIC no Setor Público

> Estimativa: 3–4 questões. A IDCAP cobra **ITIL 4** (práticas), **COBIT 2019** (domínios), **gerenciamento de projetos** (fases) e **lei seca** (14.133, 14.129, IN 94). Tema clássico de **discursiva** (planejamento de contratação).

## Mapa do edital (item 6)
6.1 COBIT, ITIL · 6.2 Gerenciamento de projetos · 6.3 PETI e PDTIC · 6.4 Governo Digital (Lei 14.129/2021) · 6.5 Lei 14.133/2021 · 6.6 IN SGD/ME 94/2022 · 6.7 Relatórios e especificações técnicas.

## 6.1 Governança × gestão
| **Governança** | **Gestão** |
|---|---|
| **Avalia, direciona e monitora** (EDM) | **Planeja, constrói, executa e monitora** (PBRM) |
| Alta administração, conselhos, comitês | Gerentes e equipes |
| "Fazer a coisa **certa**" | "Fazer **certo** a coisa" |

- **Governança de TI**: garantir que a TI sustente e estenda as estratégias e objetivos da organização (alinhamento estratégico, entrega de valor, gestão de riscos, gestão de recursos, medição de desempenho). Norma **ISO/IEC 38500** (governança corporativa de TI: princípios — responsabilidade, estratégia, aquisição, desempenho, conformidade, comportamento humano; modelo **Avaliar–Dirigir–Monitorar**).

### COBIT 2019 (ISACA)
- **6 princípios do sistema de governança**: (1) prover **valor às partes interessadas**; (2) **abordagem holística**; (3) sistema de governança **dinâmico**; (4) **governança distinta da gestão**; (5) **adaptado às necessidades** da organização; (6) sistema de governança **ponta a ponta**.
- **3 princípios do framework**: baseado em **modelo conceitual**; **aberto e flexível**; **alinhado a padrões**.
- **40 objetivos de governança e gestão** em **5 domínios**:

| Domínio | Natureza | Foco |
|---|---|---|
| **EDM** — Avaliar, Dirigir e Monitorar | **Governança** | Estabelecer e manter o sistema de governança, entrega de benefícios, otimização de riscos e recursos, engajamento das partes interessadas |
| **APO** — Alinhar, Planejar e Organizar | Gestão | **Estratégia**, arquitetura, inovação, portfólio, orçamento, RH, relacionamentos, acordos de serviço, fornecedores, **qualidade, riscos, segurança**, dados |
| **BAI** — Construir, Adquirir e Implementar | Gestão | **Definição e implementação de soluções**, programas, projetos, requisitos, capacidade, mudanças organizacionais e de TI, ativos, configuração, **gestão de projetos** |
| **DSS** — Entregar, Servir e Suportar | Gestão | **Operações**, requisições e **incidentes**, problemas, **continuidade**, serviços de segurança, controles de processos de negócio |
| **MEA** — Monitorar, Avaliar e Analisar | Gestão | Desempenho e conformidade, sistema de controle interno, **conformidade com requisitos externos**, **garantia (assurance)** |

- **7 componentes** (antigos habilitadores): **processos**; **estruturas organizacionais**; **princípios, políticas e frameworks**; **informação**; **cultura, ética e comportamento**; **pessoas, habilidades e competências**; **serviços, infraestrutura e aplicações**.
- **Fatores de design** (11: estratégia, metas, perfil de risco, problemas de TI, cenário de ameaças, requisitos de conformidade, papel da TI, modelo de sourcing, métodos de implementação, estratégia de adoção de tecnologia, porte) — para **customizar** o sistema de governança.
- **Cascata de metas**: necessidades das partes interessadas → **metas corporativas** → **metas de alinhamento** → objetivos de governança e gestão.
- **Capacidade de processo**: níveis **0 a 5** (baseado no CMMI).

🧠 Domínios: "**E**u **A**prendo **B**em **D**epois do **M**ercado" → EDM, APO, BAI, DSS, MEA.

### ITIL 4 (AXELOS/PeopleCert, 2019)
- **Sistema de Valor de Serviço (SVS)**: oportunidade/demanda → **valor**. Componentes: **princípios orientadores**, **governança**, **cadeia de valor de serviço**, **práticas**, **melhoria contínua**.
- **4 dimensões**: **organizações e pessoas**; **informação e tecnologia**; **parceiros e fornecedores**; **fluxos de valor e processos**.
- **7 princípios orientadores**: **foco no valor**; **comece onde você está**; **progrida iterativamente com feedback**; **colabore e promova visibilidade**; **pense e trabalhe holisticamente**; **mantenha simples e prático**; **otimize e automatize**.
- **Cadeia de valor — 6 atividades**: **planejar**, **melhorar**, **engajar**, **desenho e transição**, **obter/construir**, **entregar e suportar**.
- **34 práticas**: **14 gerais** de gerenciamento, **17 de gerenciamento de serviço**, **3 de gerenciamento técnico**.

| Gerais (14) | De serviço (17) | Técnicas (3) |
|---|---|---|
| Arquitetura · **Melhoria contínua** · **Segurança da informação** · Conhecimento · Medição e relatório · Mudança organizacional · Portfólio · **Projetos** · Relacionamento · **Riscos** · Financeiro de serviços · Estratégia · **Fornecedores** · Força de trabalho e talentos | Análise de negócio · **Ativos de TI** · **Catálogo de serviços** · Capacidade e desempenho · **Central de serviço** · **Configuração** · **Continuidade** · Design de serviço · Disponibilidade · **Habilitação/controle de mudanças** · **Incidentes** · **Liberação** · Monitoramento e eventos · **Nível de serviço** · **Problemas** · **Requisições de serviço** · Validação e teste | **Implantação** · Infraestrutura e plataforma · Desenvolvimento e gerenciamento de software |

| Conceito ITIL | Definição |
|---|---|
| **Incidente** | Interrupção não planejada ou redução da qualidade de um serviço → **restaurar o serviço o mais rápido possível** |
| **Problema** | **Causa** (real ou potencial) de um ou mais incidentes → análise de **causa raiz**; **erro conhecido** e **solução de contorno (workaround)** |
| **Requisição de serviço** | Pedido de usuário pré-definido (acesso, senha, informação) |
| **Mudança** | Adição, modificação ou remoção que possa afetar serviços: **padrão** (pré-autorizada, baixo risco), **normal** (avaliada por uma **autoridade de mudança**), **emergencial** |
| **Central de serviço** | **Ponto único de contato** (SPOC) entre provedor e usuários |
| **Nível de serviço** | **SLA** (com cliente), **OLA** (entre áreas internas), **UC** (contrato de apoio com fornecedor externo) |
| **Item de configuração (IC)** e **CMDB** | Componentes gerenciados e sua base de dados de configuração |

> ⚠️ **Incidente** (restaura rápido) ≠ **problema** (causa raiz). IDCAP 2025: "identificar causa raiz" = **problema**; "restaurar o serviço" = **incidente**.
> ⚠️ ITIL **v3** tinha **ciclo de vida com 5 estágios**: estratégia, desenho, transição, operação e melhoria contínua de serviço — e falava em **processos**; ITIL 4 fala em **práticas**.

## 6.2 Gerenciamento de projetos
- **Projeto**: esforço **temporário** para criar produto, serviço ou resultado **único** (≠ operação contínua). Restrições: escopo, tempo, custo, qualidade, recursos, riscos.
- **PMBOK 6ª ed.** — **5 grupos de processos**: **Iniciação** (termo de abertura, partes interessadas) → **Planejamento** (EAP, cronograma, orçamento) → **Execução** → **Monitoramento e Controle** → **Encerramento**. **10 áreas de conhecimento**: integração, escopo, cronograma, custos, qualidade, recursos, comunicações, riscos, aquisições, partes interessadas. **49 processos**. (IDCAP 2025: etapas intermediárias = **Planejamento, Execução, Monitoramento**.)
- **PMBOK 7ª ed. (2021)**: baseado em **princípios** e **domínios de desempenho** (não mais processos). **12 princípios** (ser um administrador diligente, criar ambiente colaborativo, engajar partes interessadas, focar no valor, pensamento sistêmico, liderança, tailoring, qualidade, complexidade, riscos, adaptabilidade e resiliência, mudança). **8 domínios de desempenho**: **partes interessadas, equipe, abordagem de desenvolvimento e ciclo de vida, planejamento, trabalho do projeto, entrega, medição, incerteza**.
- Ferramentas: **Termo de Abertura do Projeto (TAP)** — autoriza formalmente o projeto e nomeia o gerente; **EAP/WBS** (decomposição hierárquica do escopo em **pacotes de trabalho**); **caminho crítico** (sequência mais longa, folga zero — define a duração mínima); **Gantt**; **matriz RACI** (Responsável, Aprovador/Autoridade, Consultado, Informado); registro de riscos.
- **Valor agregado (EVM)**: VP/PV (valor planejado), VA/EV (valor agregado), CR/AC (custo real). **CPI = EV/AC** (< 1: acima do orçamento); **SPI = EV/PV** (< 1: atrasado); CV = EV − AC; SV = EV − PV.
- **Estruturas organizacionais**: funcional (gerente com pouca autoridade) → matricial fraca → balanceada → forte → **projetizada** (gerente com autoridade máxima).
- **PMO** (escritório de projetos): de suporte, de controle ou diretivo. **Portfólio** ⊃ **programas** ⊃ projetos.
- Ágil/híbrido: Scrum, Kanban (Módulo 6). Abordagem **preditiva** (cascata) × **adaptativa** (ágil) × **híbrida**.

## 6.3 Planejamento Estratégico de TI (PETI) e PDTIC
| | **PETI** | **PDTIC** |
|---|---|---|
| Natureza | **Estratégico**: missão, visão, objetivos de TI de longo prazo, alinhados ao **PEI** (Planejamento Estratégico Institucional) | **Tático/operacional**: **diagnóstico, planejamento e gestão** dos recursos e processos de TIC para um período |
| Horizonte | 4–5 anos | Em geral **2 a 4 anos** (revisado periodicamente) |

- **PDTIC** (modelo do SISP): instrumento de **diagnóstico, planejamento e gestão dos recursos e processos de TIC** que visa atender às necessidades tecnológicas e de informação do órgão. Conteúdo típico: referencial estratégico, **diagnóstico** (análise **SWOT/FOFA**, resultados do PDTIC anterior), **inventário de necessidades** priorizadas (matriz **GUT**: Gravidade, Urgência, Tendência), **plano de metas e ações**, plano de gestão de pessoas, **plano orçamentário**, **plano de gestão de riscos**, fatores críticos de sucesso.
- Elaborado pela área de TI com as áreas de negócio; aprovado pelo **Comitê de Governança Digital** (ou comitê de TI).
- **Toda contratação de TIC deve estar alinhada ao PDTIC** e ao **Plano de Contratações Anual (PCA)** (IN SGD 94/2022).
- Ferramentas: **SWOT** (Forças e Fraquezas = **internas**; Oportunidades e Ameaças = **externas**), **BSC** (4 perspectivas: financeira, clientes/sociedade, processos internos, aprendizado e crescimento — no setor público, a "sociedade" fica no topo), OKR, indicadores **SMART**.
- Esfera federal: **Estratégia de Governo Digital** (EGD) e **Plano de Transformação Digital** dos órgãos.

## 6.4 Governo Digital — Lei nº 14.129/2021
- Dispõe sobre **princípios, regras e instrumentos para o Governo Digital e para o aumento da eficiência pública**, especialmente por **desburocratização, inovação, transformação digital e participação do cidadão**.
- **Abrangência (art. 2º)**: administração **direta e indireta federal** (incluindo os três Poderes, TCU e MPU) e as administrações dos **Estados, DF e Municípios que adotarem os comandos da lei por meio de atos normativos próprios**.
> ⚠️ A lei **não se aplica automaticamente** ao Estado do Amapá — depende de **adesão por ato normativo próprio**.

- **Princípios e diretrizes (art. 3º — destaques)**: desburocratização e **simplificação**; **disponibilização em plataforma única** do acesso às informações e serviços; possibilidade de **demandar e acessar serviços por meio digital, sem necessidade de solicitação presencial**; transparência e **dados abertos**; **governo como plataforma**; **linguagem clara**; uso de tecnologia para otimizar processos; **atuação integrada** entre órgãos e **interoperabilidade**; **presunção de boa-fé** do usuário; **permanência da possibilidade de atendimento presencial**; **proteção de dados pessoais** (LGPD); cumprimento de compromissos de qualidade; **acessibilidade** (pessoas com deficiência, idosos); **adoção preferencial de tecnologias, padrões e formatos abertos e livres**; **participação social**; **inovação** (incluindo **laboratórios de inovação**); **gestão por resultados**.
- **Governo como plataforma** e **dados abertos**: dados em **formato aberto, legível por máquina**; qualquer interessado pode **pedir a abertura de bases** de dados (art. 29 e ss.).
- **Prestação digital dos serviços públicos** por **plataformas de governo digital**, com **Base Nacional de Serviços Públicos** e **Carta de Serviços ao Usuário** atualizada. Avaliação de satisfação pelo usuário.
- **Identificação do cidadão**: o **número do CPF** é **suficiente** para identificação nos bancos de dados de serviços públicos (reforçado pela Lei 14.534/2023, que torna o CPF o número único de identificação).
- **Autosserviço**, **atos processuais em meio eletrônico**, assinatura eletrônica (Lei 14.063/2020: simples, **avançada**, **qualificada** — ICP-Brasil).
- **Laboratórios de inovação** abertos à participação de sociedade, academia e empresas.
- **Redes de conhecimento** e **Comitês de Governança Digital** nos órgãos.

## 6.5 Lei nº 14.133/2021 — Licitações e Contratos (substituiu a 8.666/1993, revogada em 30/12/2023)
### Princípios (art. 5º)
Legalidade, impessoalidade, moralidade, publicidade, eficiência, interesse público, probidade administrativa, igualdade, **planejamento**, transparência, eficácia, **segregação de funções**, motivação, **vinculação ao edital**, **julgamento objetivo**, segurança jurídica, razoabilidade, competitividade, proporcionalidade, celeridade, economicidade, **desenvolvimento nacional sustentável** (+ LINDB).

### Fases do processo licitatório (art. 17 — ordem)
1. **Preparatória** (planejamento: DFD, **ETP**, TR, estimativa de preço, matriz de riscos)
2. **Divulgação do edital** (no **PNCP** — Portal Nacional de Contratações Públicas)
3. **Apresentação de propostas e lances**
4. **Julgamento**
5. **Habilitação** (regra: **depois** do julgamento; pode ser invertida motivadamente)
6. **Recursal** (fase única)
7. **Homologação**

### Modalidades (art. 28) e critérios de julgamento (art. 33)
| Modalidade | Uso |
|---|---|
| **Pregão** | **Obrigatório** para **bens e serviços comuns** (inclusive serviços comuns de engenharia). Critério: **menor preço** ou **maior desconto** |
| **Concorrência** | Bens e serviços **especiais** e obras/serviços de engenharia. Critérios: menor preço, maior desconto, melhor técnica ou conteúdo artístico, **técnica e preço**, maior retorno econômico |
| **Concurso** | Trabalho técnico, científico ou artístico → **prêmio** |
| **Leilão** | **Alienação** de bens → **maior lance** |
| **Diálogo competitivo** (novo) | Objetos que envolvam **inovação tecnológica/técnica**, quando a Administração **não consegue definir a solução** sem dialogar com licitantes previamente selecionados |
> ⚠️ **Extintos**: **convite**, **tomada de preços** (e o RDC). Critérios: menor preço · maior desconto · melhor técnica ou conteúdo artístico · técnica e preço · maior lance · maior retorno econômico.

- **Procedimentos auxiliares** (art. 78): credenciamento, pré-qualificação, procedimento de manifestação de interesse (PMI), **sistema de registro de preços (SRP)**, registro cadastral.
- **Agente de contratação** (art. 8º): servidor **efetivo ou empregado público** dos quadros permanentes que conduz a licitação (no pregão, **pregoeiro**); **comissão de contratação** (mín. 3 membros) para bens/serviços especiais. **Gestor e fiscal** do contrato (art. 117).
- **ETP** (art. 18, § 1º): documento da fase preparatória que caracteriza o interesse público e a **melhor solução**. Elementos **obrigatórios** (§ 2º): **descrição da necessidade**, **estimativa das quantidades**, **estimativa do valor**, **justificativa do parcelamento ou não**, e **posicionamento conclusivo sobre a viabilidade**.
- **Termo de Referência** (art. 6º, XXIII): documento para contratação de **bens e serviços** — definição do objeto, fundamentação, descrição da solução, requisitos, modelo de execução e de gestão, critérios de medição e pagamento, forma de seleção do fornecedor, estimativas de valor, adequação orçamentária. (**Projeto básico** é para obras e serviços de engenharia.)

### Contratação direta
| **Inexigibilidade** (art. 74) — competição **inviável** | **Dispensa** (art. 75) — competição **possível**, mas a lei dispensa |
|---|---|
| Fornecedor/representante **exclusivo** | **Valor**: até **R$ 100 mil** (obras e serviços de engenharia/manutenção de veículos) e até **R$ 50 mil** (demais compras e serviços) — **valores do texto original, atualizados anualmente por decreto** (2025: R$ 125.451,15 e R$ 62.725,59 — confirmar valores de 2026) |
| Artista consagrado pela crítica ou opinião pública | Emergência ou calamidade pública (contrato até **1 ano**, vedada prorrogação) |
| **Serviços técnicos especializados de natureza predominantemente intelectual** com profissionais de **notória especialização** (vedada para publicidade) | Licitação **deserta/fracassada** (mantidas as condições) |
| **Credenciamento** | Contratação de **instituição de pesquisa/inovação**, entre outras hipóteses |
| Aquisição/locação de imóvel com características que condicionem a escolha | |

🧠 "**In**exigível = **in**viável".

### Contratos
- **Duração** (arts. 105–114): serviços e fornecimentos **contínuos** até **5 anos**, prorrogáveis até **10 anos**; contratos de **operação continuada de sistemas estruturantes de TI**: até **15 anos** (art. 114).
- **Alterações unilaterais**: acréscimos/supressões até **25%** do valor (até **50%** para acréscimos em reforma de edifício/equipamento).
- **Garantia**: até **5%** do valor (até **10%** em alta complexidade); modalidades: caução, seguro-garantia, fiança bancária, título de capitalização.
- **Matriz de riscos** (alocação de riscos entre as partes), **reajuste** e **repactuação**, **sanções** (advertência, multa, impedimento de licitar até 3 anos, declaração de inidoneidade de 3 a 6 anos).
- **PNCP**: divulgação obrigatória de editais, contratos e atas.

## 6.6 Instrução Normativa SGD/ME nº 94/2022 — contratação de soluções de TIC
- Dispõe sobre o processo de contratação de **soluções de TIC** pelos órgãos do **SISP** (Sistema de Administração dos Recursos de Tecnologia da Informação — esfera federal), sob a **Lei 14.133/2021**. Estados e municípios a usam como **referência** de boas práticas.
- **Três fases**: **(1) Planejamento da Contratação** → **(2) Seleção do Fornecedor** → **(3) Gestão do Contrato**.
- Pré-requisito: contratação **alinhada ao PDTIC** (ou ao Plano de Transformação Digital) e prevista no **Plano de Contratações Anual (PCA)**.

### Fase 1 — Planejamento da Contratação (artefatos, nesta ordem)
1. **Documento de Formalização da Demanda (DFD)** — elaborado pela **área requisitante**: necessidade, motivação, alinhamento ao PDTIC/PCA, indicação do integrante requisitante. Encaminhado à área de TIC.
2. **Instituição da Equipe de Planejamento da Contratação**, composta por:
   - **Integrante Requisitante** (da área demandante — conhece a necessidade de negócio);
   - **Integrante Técnico** (da área de **TIC** — aspectos técnicos);
   - **Integrante Administrativo** (da área administrativa — aspectos administrativos/licitatórios).
3. **Estudo Técnico Preliminar (ETP)** — necessidades e requisitos, **levantamento das soluções de mercado** (inclusive contratações de outros órgãos, **Software Público Brasileiro**, soluções em nuvem, soluções gratuitas), **análise comparativa de custos (custo total de propriedade — TCO)**, **escolha e justificativa da solução**, estimativa de custo, parcelamento, benefícios esperados e **declaração de viabilidade**.
4. **Análise de riscos → Mapa de Gerenciamento de Riscos** — elaborado no planejamento e **atualizado** em todas as fases (ao final do ETP, antes do TR, na seleção do fornecedor e na gestão do contrato): riscos do processo e da solução, probabilidade, impacto, ações de mitigação e de contingência, responsáveis.
5. **Termo de Referência (TR)** ou Projeto Básico — definição do objeto, justificativa, especificação técnica, **modelo de execução** (rotinas, prazos, papéis), **modelo de gestão** (critérios de aceitação, **níveis mínimos de serviço**, **Instrumento de Medição de Resultado — IMR**, sanções/glosas), forma de seleção, estimativa de preço, adequação orçamentária.

### Fase 2 — Seleção do Fornecedor
- Conduzida pela área administrativa, conforme a Lei 14.133 (em regra **pregão**, por serem em geral bens/serviços comuns de TIC); a área de TIC apoia na análise técnica das propostas e da **prova de conceito (PoC)**, se prevista.

### Fase 3 — Gestão do Contrato
| Papel | Responsabilidade |
|---|---|
| **Gestor do Contrato** | Coordena e gerencia a execução; encaminha sanções, pagamento, aditivos; assina **Termo de Recebimento Definitivo** |
| **Fiscal Técnico** | Fiscaliza **aspectos técnicos** (qualidade, níveis de serviço); emite **Termo de Recebimento Provisório** |
| **Fiscal Requisitante** | Fiscaliza do **ponto de vista do negócio** (atende à necessidade?) |
| **Fiscal Administrativo** | Fiscaliza **aspectos administrativos** (obrigações trabalhistas, previdenciárias, garantias, documentação) |

- Etapas: **reunião inicial** (com o preposto da contratada; **termo de compromisso** de sigilo e **termo de ciência**), emissão de **Ordens de Serviço/Fornecimento**, **monitoramento** (níveis de serviço, IMR), **recebimento provisório** → **avaliação da qualidade** → **recebimento definitivo**, **glosas/sanções**, **pagamento** (vinculado a **resultados**), **transição contratual** e **encerramento** (repasse de conhecimento, devolução de recursos, eliminação de dados).

### Vedações relevantes (IN 94/2022)
- Contratar **mais de uma solução de TIC em um único contrato** (deve-se avaliar o **parcelamento**).
- Que o **mesmo fornecedor** preste serviços de **execução** e de **fiscalização/apoio à fiscalização** do mesmo contrato.
- **Indicar marca** ou fornecedor, salvo justificativa técnica.
- **Remuneração por homem-hora ou por postos de trabalho**, **exceto** quando comprovadamente não for possível remunerar por **resultados/produtos** (justificativa no ETP). Preferência por **pagamento vinculado a resultados** (ex.: Unidade de Serviço Técnico — UST, pontos de função) com níveis de serviço.
- Previsão de serviços que **não** sejam de TIC no mesmo contrato, ou **gestão de processos internos** do órgão delegada ao fornecedor.

## 6.7 Elaboração de relatórios e especificações técnicas
- **Especificação técnica** (no TR): **clara, precisa, objetiva, mensurável**; descreve **requisitos funcionais e não funcionais**, **padrões** (abertos, interoperabilidade — e-PING), **níveis de serviço** (disponibilidade, tempo de resposta, prazo de atendimento), garantia e suporte, **requisitos de segurança e privacidade** (LGPD, criptografia, localização dos dados), capacitação, transferência de conhecimento, **critérios de aceitação** e de medição.
- **Evitar**: direcionamento (marca, característica exclusiva sem justificativa), excesso de detalhes que restrinjam a competição, requisitos ambíguos ("sistema rápido" → "tempo de resposta ≤ 2 s em 95% das requisições").
- **Relatório técnico**: título, **objetivo**, **contexto/escopo**, **metodologia**, **análise/diagnóstico**, **resultados**, **conclusões e recomendações**, anexos. Linguagem impessoal, objetiva; dados verificáveis; **Manual de Redação da Presidência** (clareza, concisão, impessoalidade, formalidade).

## ⚠️ Pegadinhas do bloco
1. **EDM** é o **único domínio de governança** do COBIT; os outros quatro são de gestão.
2. ITIL 4: **34 práticas = 14 + 17 + 3**; "processos" é termo da v3.
3. Incidente → **restaurar**; problema → **causa raiz**.
4. 14.133: habilitação **após** o julgamento (regra); **convite e tomada de preços extintos**; **diálogo competitivo** é novo.
5. **Inexigibilidade** = competição **inviável**; **dispensa** = viável, mas dispensada.
6. IN 94: equipe = **requisitante + técnico + administrativo**; gestão = **gestor + fiscais técnico, requisitante e administrativo**.
7. Lei 14.129 só vale para Estados/Municípios **que aderirem por ato próprio**.
8. TR = bens e serviços; **projeto básico** = obras e serviços de engenharia.

## Questões comentadas (estilo IDCAP)

**Q1.** No COBIT 2019, o domínio de governança e o domínio que trata da definição, aquisição e implementação de soluções de TI são, respectivamente:
(A) APO e DSS. (B) **EDM e BAI.** (C) MEA e BAI. (D) EDM e APO.
✅ **B.** (Questão similar cobrada pela IDCAP em 2025.)

**Q2.** Na ITIL 4, uma prática busca restaurar a operação normal do serviço o mais rápido possível; outra busca reduzir a probabilidade e o impacto de incidentes identificando suas causas reais. São, respectivamente:
(A) Problemas e incidentes. (B) **Incidentes e problemas.** (C) Requisições e mudanças. (D) Central de serviço e liberação.
✅ **B.**

**Q3.** Segundo a IN SGD/ME nº 94/2022, a Equipe de Planejamento da Contratação é composta pelos integrantes:
(A) gestor, fiscal técnico e fiscal administrativo. (B) **requisitante, técnico e administrativo.** (C) requisitante, jurídico e financeiro. (D) técnico, pregoeiro e gestor.
✅ **B.**

**Q4.** Na Lei 14.133/2021, a modalidade destinada a contratações em que a Administração busca soluções inovadoras, dialogando com licitantes previamente selecionados para desenvolver alternativas, é:
(A) concorrência. (B) pregão. (C) **diálogo competitivo.** (D) concurso.
✅ **C.**

**Q5.** A contratação de serviço técnico especializado de natureza predominantemente intelectual, com profissional de notória especialização, enquadra-se como:
(A) dispensa por valor. (B) **inexigibilidade de licitação.** (C) pregão eletrônico. (D) diálogo competitivo.
✅ **B.**

**Q6.** De acordo com a Lei 14.129/2021, é correto afirmar:
(A) Aplica-se automaticamente a todos os Estados e Municípios. (B) **Prevê a possibilidade de o cidadão demandar e acessar serviços públicos por meio digital, sem necessidade de solicitação presencial.** (C) Proíbe o atendimento presencial. (D) Exige certificado digital ICP-Brasil para todos os serviços.
✅ **B.** Estados e Municípios aderem por ato próprio; o atendimento presencial permanece possível.
