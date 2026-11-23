# Módulo 8 — TI: Processo de Desenvolvimento, Engenharia de Software e Governança

> Edital: *Métodos Ágeis (Scrum, Kanban, XP etc.); Engenharia de requisitos; Engenharia de Software; Gestão de Projetos e Governança de TI: PMBOK 8ª Edição; ITIL Version 5; COBIT 2019.* Estimativa: 4–6 questões. A FCC (TRT-15/2023) cobrou requisitos, RF × RNF, APF, BPMN, UML 2.5, CMMI, MPS.BR, padrões de projeto, testes e gerência de configuração.

## 1. Métodos ágeis
### Manifesto Ágil (2001)
**Indivíduos e interações** > processos e ferramentas · **Software em funcionamento** > documentação abrangente · **Colaboração com o cliente** > negociação de contratos · **Responder a mudanças** > seguir um plano. (Os itens da direita **têm valor**, os da esquerda têm **mais**.) + **12 princípios** (entrega contínua e cedo de valor, mudanças bem-vindas mesmo tarde, entregas frequentes de semanas a meses, trabalho diário conjunto, indivíduos motivados, conversa face a face, software funcionando como medida de progresso, **ritmo sustentável**, excelência técnica, **simplicidade** — maximizar o trabalho não feito, equipes **auto-organizáveis**, reflexão em intervalos regulares).

### Scrum (Guia 2020)
| | |
|---|---|
| **Pilares** | Transparência, inspeção, adaptação |
| **Valores** | Compromisso, foco, abertura, respeito, coragem |
| **Scrum Team** (≤ 10 pessoas) | **Product Owner** (maximiza valor; único responsável pelo **Product Backlog**), **Scrum Master** (eficácia do time; líder que serve), **Developers** (criam o incremento; responsáveis pelo **Sprint Backlog** e pela qualidade — DoD) |
| **Eventos** | **Sprint** (≤ 1 mês) · **Sprint Planning** (≤ 8 h: *por que* — Meta da Sprint; *o que*; *como*) · **Daily Scrum** (**15 min**, para os Developers) · **Sprint Review** (≤ 4 h, inspeciona o incremento com stakeholders) · **Sprint Retrospective** (≤ 3 h, melhora pessoas, interações, processos, ferramentas e DoD) |
| **Artefatos → compromissos** | Product Backlog → **Meta do Produto** · Sprint Backlog → **Meta da Sprint** · Incremento → **Definição de Pronto** |
| Cancelamento | Só o **Product Owner** cancela a Sprint (se a Meta da Sprint se tornar obsoleta) |
| Refinamento | Atividade contínua (não é evento) |

### Kanban
- Princípios/práticas: **visualizar o fluxo**, **limitar o WIP**, gerenciar o fluxo, **tornar políticas explícitas**, implementar ciclos de feedback, melhorar colaborativamente. Sistema **puxado** (*pull*).
- Métricas: **lead time** (pedido → entrega), **cycle time** (início do trabalho → entrega), **throughput**, **CFD** (diagrama de fluxo cumulativo). **Lei de Little**: WIP médio = throughput × lead time.

### XP — Extreme Programming (Kent Beck)
- **Valores**: comunicação, simplicidade, feedback, coragem, respeito.
- **Práticas**: **programação em pares**, **TDD**, **integração contínua**, **refatoração**, **design simples**, **propriedade coletiva do código**, **padrões de codificação**, **pequenos releases**, **jogo do planejamento**, **cliente presente**, **semana de 40 horas (ritmo sustentável)**, **metáfora**.
- Outros: **FDD** (Feature-Driven Development — 5 processos: modelo abrangente, lista de features, planejar por feature, projetar por feature, construir por feature), **Lean** (7 desperdícios), **Crystal**, **DSDM**, **SAFe** e **LeSS** (escala).

## 2. Engenharia de requisitos (Sommerville)
- **Requisitos funcionais (RF)**: o que o sistema **deve fazer** (serviços, reações a entradas). **Não funcionais (RNF)**: **restrições** sobre serviços ou funções — de **produto** (desempenho, confiabilidade, disponibilidade, segurança, usabilidade), **organizacionais** (padrões, processos), **externos** (legais, éticos). **De domínio**: derivados do domínio da aplicação.
  - Ex. FCC: "disponível de segunda a sexta, das 9h às 18h" e "indisponibilidade ≤ 5 s/dia" = **RNF**; "pesquisar processos por número" = **RF**; "implementar as condições de privacidade conforme normas do órgão" = **RNF** (externo/legal).
- **Processo**: **estudo de viabilidade** → **elicitação e análise** → **especificação** → **validação** → **gerenciamento de requisitos** (mudanças, **rastreabilidade**).
- **Elicitação e análise** (ciclo): **descoberta** → **classificação e organização** → **priorização e negociação** → **especificação/documentação**.
- Técnicas: entrevistas (fechadas/abertas), **cenários**, **casos de uso**, **etnografia** (observação), **prototipação**, JAD/workshops, brainstorming, questionários, análise de documentos, **histórias de usuário** (+ critérios de aceitação; **INVEST**).
- **Validação**: revisões, prototipação, geração de casos de teste. Verifica **validade, consistência, completude, realismo e verificabilidade**.
- **Documento de requisitos (SRS)**: IEEE 830 (substituída pela ISO/IEC/IEEE 29148).

## 3. Engenharia de software
### Modelos de processo
| Modelo | Característica |
|---|---|
| **Cascata** | Fases sequenciais (requisitos → projeto → implementação → testes → operação e manutenção); bom com requisitos estáveis |
| **Incremental** | Entregas parciais funcionais |
| **Espiral** (Boehm) | Iterações com **análise de riscos** (4 quadrantes: objetivos, riscos, desenvolvimento/validação, planejamento) |
| **Prototipação** | Protótipo descartável ou evolutivo para validar requisitos |
| **RUP/PU** | Fases **Concepção, Elaboração, Construção, Transição**; iterativo, dirigido por casos de uso, centrado na arquitetura |
| **V** | Cada fase de desenvolvimento tem um nível de teste correspondente |

### Testes
| Nível | Objetivo |
|---|---|
| **Unitário** | Menor unidade isolada (método/classe) |
| **Integração** | **Módulos funcionando juntos** (custo maior: várias partes em execução) |
| **Sistema / funcional** | Recursos e funcionalidades vs. especificação (**SRS**) |
| **Aceitação** | Usuário valida (alfa, beta, UAT) |
| **Regressão** | Mudanças não quebraram o que funcionava |
| Não funcionais | Desempenho, carga, estresse, segurança, usabilidade |
- **Caixa-preta** (partição de equivalência, valor-limite, tabela de decisão) × **caixa-branca** (cobertura de comandos, decisões/ramos, caminhos; **complexidade ciclomática** V(G) = E − N + 2 ou nº de decisões + 1).
- **TDD**: Red → Green → Refactor. **BDD**: Gherkin (*Given/When/Then* — Dado/Quando/Então). **ATDD**.
- **JUnit**: biblioteca distribuída como **.jar** no *classpath*. JUnit 3: classe de teste **herda de `junit.framework.TestCase`**, métodos `testXxx()`. JUnit 4: anotações `@Test`, `@Before`, `@After`, `@BeforeClass`. **JUnit 5 (Jupiter)**: `@Test`, `@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`, `@DisplayName`, `@ParameterizedTest`, `@Disabled`; `Assertions.assertEquals(esperado, atual)`, `assertThrows`.
- Dublês: **mock** (verifica interação — Mockito: `when(...).thenReturn(...)`, `verify(...)`), stub, fake, spy, dummy.

### Gerência de configuração (GCS)
- **Item de configuração (IC)**; **linha de base (baseline)**: versão **revisada e aprovada** formalmente de ICs, que só muda por **controle de mudanças** (no DevOps: configuração versionada no repositório, alterada via **pull/merge request revisado** — FCC chamou isso de "linha de base").
- Atividades: **identificação**, **controle de versão**, **controle de mudanças**, **auditoria de configuração**, **relato de status**.
- **Gitflow**: branches permanentes **main/master** e **develop**; de suporte, temporários: **feature**, **release**, **hotfix** (fazem merge e são removidos).

### Análise de Pontos de Função (IFPUG/APF)
| Função | Tipo | Baixa | Média | Alta |
|---|---|---:|---:|---:|
| **ALI** — Arquivo Lógico Interno | Dados (mantido pela aplicação) | 7 | 10 | 15 |
| **AIE** — Arquivo de Interface Externa | Dados (só referenciado; mantido por outra) | 5 | 7 | 10 |
| **EE** — Entrada Externa | Transação (altera ALI / controla) | 3 | 4 | 6 |
| **SE** — Saída Externa | Transação (com cálculo/dado derivado) | 4 | 5 | 7 |
| **CE** — Consulta Externa | Transação (recuperação sem cálculo) | 3 | 4 | 6 |
- Complexidade por **DER/TD** (tipos de dados), **RLR/TR** (registros lógicos) e **ALR/AR** (arquivos referenciados).
- **PF não ajustados (brutos)** = Σ(quantidade × peso). Ex.: 2 ALI baixos + 1 médio + 1 alto = 2×7 + 10 + 15 = **39**.
- Fator de ajuste (14 características gerais, VAF = 0,65 + 0,01 × TDI) — opcional no IFPUG atual. Contagem indicativa/estimativa (NESMA) usa pesos fixos (ALI 35, AIE 15). SISP: Roteiro de Métricas.

### UML 2.5 — 14 diagramas
| **Estrutura** (7) | **Comportamento** (7) |
|---|---|
| **Classes**, **objetos**, **componentes**, **implantação** (*deployment*), **pacotes**, estrutura composta, **perfil** | **Casos de uso**, **atividades**, **máquina de estados** + **interação**: **sequência**, **comunicação**, **visão geral de interação**, **tempo** |
> Ex. FCC: Deployment (E), Package (E), Use Case (C), Sequence (C) → **E, E, C, C**.

### BPMN 2.0 (o que cai)
- **Eventos** (círculos): **início** (borda fina), **intermediário** (borda dupla), **fim** (borda grossa); gatilhos: mensagem (envelope), temporizador (relógio), **erro** (raio), sinal, condicional, **escalonamento**, **compensação** (rebobinar), cancelamento, múltiplo, link, terminação. Evento **anexado à borda** da tarefa (*boundary*) = interrompe ou não a atividade.
- **Tarefas** (ícone no canto): **usuário** (pessoa), **serviço** (engrenagens), **script** (pergaminho), **manual** (mão), envio/recebimento (envelope), regra de negócio (tabela). Marcadores: **loop**, **múltiplas instâncias** (3 barras — paralelas ‖ ou sequenciais ≡), **subprocesso** (+), **compensação**.
- **Gateways** (losangos): **exclusivo (XOR, "X")**, **paralelo (AND, "+")**, **inclusivo (OR, "O")**, baseado em eventos, complexo.
- **Piscinas (pools)** e **raias (lanes)**; **fluxo de sequência** (dentro da pool) × **fluxo de mensagem** (entre pools, tracejado); artefatos e objetos de dados.

### Padrões de projeto (GoF — 23)
| Criacionais | Estruturais | Comportamentais |
|---|---|---|
| **Singleton** (instância única), **Factory Method** (subclasses decidem qual classe instanciar — desacopla criação), **Abstract Factory** (famílias de objetos), **Builder** (construção passo a passo), **Prototype** (clonagem) | **Adapter** (interface incompatível), **Facade** (interface simplificada), **Decorator** (adiciona responsabilidades dinamicamente), **Proxy** (substituto/controle de acesso), **Composite** (árvore parte-todo), **Bridge**, **Flyweight** | **Observer** (notifica dependentes — pub/sub), **Strategy** (algoritmos intercambiáveis), **Command**, **Template Method**, **Iterator**, **State**, **Chain of Responsibility**, **Mediator**, **Memento**, **Visitor**, **Interpreter** |
> Ex. FCC: código acoplado à classe `Entregador`; adicionar novo meio de entrega exige mudar tudo → **Factory Method** (criar objetos via método de fábrica com interface comum `Transporte`).

### POO
- **Encapsulamento**: esconder o estado (atributos privados + **getters/setters**) — "caixa-preta". **Herança**: filho herda do pai. **Polimorfismo**: **sobrescrita** (*override* — filho altera o comportamento de método herdado; dinâmico) e **sobrecarga** (*overload* — mesmo nome, parâmetros diferentes; estático). **Abstração**.
- **SOLID**: SRP, OCP, LSP, ISP, DIP (ver Módulo de Programação). Coesão alta, acoplamento baixo.

### Modelos de maturidade
- **CMMI-DEV v2.0** (2018): organizado em **Áreas de Categoria** (*Category Areas*): **Doing** (produzir, comprar e **entregar soluções de qualidade**), **Managing** (planejar e gerenciar o trabalho e a força de trabalho), **Enabling** (análise de causas, decisão, integridade do produto, comunicação), **Improving** (desenvolver, gerenciar e melhorar processos e ativos). Níveis de maturidade **0 a 5** e de capacidade **0 a 3**; avaliação por **práticas** (não mais metas/práticas genéricas e específicas da v1.3).
- **MR-MPS-SW** (Softex): níveis **G** (parcialmente gerenciado) → **F** → **E** → **D** → **C** → **B** → **A** (em otimização). **GPR** (Gerência de Projetos) e **REQ** começam no **G**; resultados evoluem nos níveis seguintes (no **B**, uso de **técnicas estatísticas e quantitativas** para gerenciar o projeto) (confirmar numeração dos resultados GPR na versão vigente do guia).

## 4. PMBOK — 8ª edição (PMI, novembro/2025)
| Elemento | 7ª ed. (2021) | **8ª ed. (2025)** |
|---|---|---|
| Princípios | 12 | **6** |
| Domínios de desempenho | 8 | **7** |
| Processos | (removidos) | **~40 processos**, organizados por **5 grupos/áreas de foco**: iniciação, planejamento, execução, monitoramento e controle, encerramento |

- **6 princípios**: (1) adotar **visão holística** (*holistic view*); (2) **foco no valor**; (3) **qualidade incorporada** (*embed quality*); (4) **liderança responsável** (*accountable leadership*); (5) **sustentabilidade integrada** (*integrate sustainability* — novidade); (6) construir **equipes empoderadas** (*empowered teams*).
- **7 domínios de desempenho**: **governança**, **escopo**, **cronograma**, **finanças**, **partes interessadas**, **recursos** e **riscos** — cada um com seus processos.
- Novidades: maior cobertura de **IA**, **PMO**, **aquisições**, análise de dados, abordagens **preditivas, adaptativas e híbridas**; publicado junto com o *Standard for Project Management*. (Fonte: PMI e materiais de mercado — confirmar nomenclatura oficial em português.)
- **Conceitos clássicos ainda cobrados**: projeto (temporário, resultado único); **TAP** (termo de abertura — autoriza o projeto, nomeia o gerente); **EAP** (decomposição em pacotes de trabalho); **caminho crítico** (folga zero); **EVM**: CPI = EV/AC, SPI = EV/PV, CV = EV − AC, SV = EV − PV, EAC = BAC/CPI; matriz RACI; estruturas funcional/matricial/projetizada; portfólio ⊃ programas ⊃ projetos.

## 5. ITIL (Version 5) — PeopleCert, 2026
- Anunciado em **janeiro/2026**; exame Foundation (Version 5) a partir de fevereiro/2026; **coexiste com o ITIL 4** por pelo menos 12 meses.
- Mantém base do ITIL 4: **sistema de valor**, **7 princípios orientadores** e **34 práticas**, com mudanças de enfoque:
  - **Produtos e serviços** tratados de forma integrada, no **ciclo de vida de ponta a ponta** (não mais domínios separados);
  - **Governança** com papel central no sistema de valor;
  - **Experiência** (cliente, usuário, colaborador) como eixo;
  - **IA incorporada** às práticas e módulo dedicado à **governança de IA**;
  - Trilhas avançadas: **ITIL Product, ITIL Service, ITIL Experience, ITIL Strategy, ITIL Transformation** (lançamento gradual).
- (Fontes: PeopleCert e parceiros credenciados — a FCC pode cobrar a base do ITIL 4; confirme a terminologia oficial em português.)

### Base ITIL 4 (continua válida)
- **7 princípios**: foco no valor · comece onde você está · progrida iterativamente com feedback · colabore e promova visibilidade · pense e trabalhe holisticamente · mantenha simples e prático · otimize e automatize.
- **4 dimensões**: organizações e pessoas · informação e tecnologia · parceiros e fornecedores · fluxos de valor e processos.
- **Cadeia de valor**: planejar · melhorar · engajar · desenho e transição · obter/construir · entregar e suportar.
- **34 práticas**: 14 gerais, 17 de gerenciamento de serviço, 3 técnicas.
- **Incidente** (restaurar o serviço o mais rápido possível) × **problema** (causa raiz; erro conhecido; *workaround*) × **requisição de serviço** × **mudança** (padrão, normal, emergencial; **autoridade de mudança**).
- SLA (cliente) × OLA (interno) × UC (fornecedor externo); central de serviço = ponto único de contato; CMDB.

## 6. COBIT 2019 (ISACA)
- Separa **governança** (**EDM** — Avaliar, Dirigir, Monitorar) de **gestão** (**APO** — Alinhar, Planejar, Organizar; **BAI** — Construir, Adquirir, Implementar; **DSS** — Entregar, Servir, Suportar; **MEA** — Monitorar, Avaliar, Analisar).
- **40 objetivos** de governança e gestão; **7 componentes** (processos; estruturas organizacionais; princípios, políticas e frameworks; informação; cultura, ética e comportamento; pessoas, habilidades e competências; serviços, infraestrutura e aplicações); **11 fatores de design**; **cascata de metas** (necessidades das partes interessadas → metas corporativas → metas de alinhamento → objetivos); **capacidade 0–5** (base CMMI); **áreas de foco** (ex.: segurança, DevOps, PME).
- **6 princípios do sistema de governança**: valor às partes interessadas; abordagem holística; sistema dinâmico; governança distinta da gestão; adaptado às necessidades; ponta a ponta. **3 do framework**: modelo conceitual; aberto e flexível; alinhado a padrões.

## ⚠️ Pegadinhas
1. Daily = **15 min**; só o **PO** cancela a Sprint; refinamento **não** é evento.
2. "Disponível das 9h às 18h" é **RNF**, mesmo descrevendo comportamento.
3. APF: **ALI** (mantido pela aplicação) × **AIE** (só referenciado); pesos 7-10-15 × 5-7-10.
4. UML: **pacotes e implantação são estruturais**; **sequência é comportamental (interação)**.
5. PMBOK 8: **6 princípios e 7 domínios** (7ª ed.: 12 e 8).
6. COBIT: só **EDM** é governança.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Considere os requisitos: I. O sistema deve emitir certidão de distribuição. II. O tempo de resposta das consultas não pode exceder 2 segundos. III. O sistema deve registrar a juntada de petições. IV. O sistema deve operar em conformidade com a LGPD. São requisitos funcionais e não funcionais, respectivamente:
(A) I e II; III e IV. (B) **I e III; II e IV.** (C) II e IV; I e III. (D) I, II e III; IV. (E) III; I, II e IV.
✅ **B.**

**Q2.** Na APF (IFPUG), uma aplicação mantém 3 ALI de complexidade baixa e referencia 2 AIE de complexidade média. A contribuição dessas funções de dados, em PF não ajustados, é:
(A) 31. (B) 25. (C) **35.** (D) 41. (E) 29.
✅ **C.** 3 × 7 + 2 × 7 = 21 + 14 = 35.

**Q3.** No PMBOK 8ª edição, a quantidade de princípios e de domínios de desempenho é, respectivamente:
(A) 12 e 8. (B) 10 e 5. (C) **6 e 7.** (D) 7 e 6. (E) 8 e 12.
✅ **C.**

**Q4.** Uma aplicação precisa permitir que novas formas de notificação (e-mail, SMS, push) sejam adicionadas sem alterar o código que solicita a criação dos objetos de notificação, delegando a subclasses a decisão de qual classe concreta instanciar. O padrão adequado é:
(A) Singleton. (B) Observer. (C) **Factory Method.** (D) Adapter. (E) Facade.
✅ **C.**

**Q5.** Na taxonomia da UML 2.5, são diagramas de comportamento:
(A) classes e pacotes. (B) componentes e implantação. (C) **atividades e sequência.** (D) objetos e perfil. (E) estrutura composta e casos de uso.
✅ **C.**
