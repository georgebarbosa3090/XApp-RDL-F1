# Módulo 6 — Específicos 1: Engenharia, Arquitetura e Desenvolvimento de Software

> **Conhecimentos Específicos**: 20 questões × 2,5 = **50 pontos**. Estimativa: 3–4 questões deste bloco.

## Mapa do edital (item 1)
1.1 Ciclo de vida, requisitos, ágil (Scrum, Kanban) · 1.2 POO, SOLID, Clean Code · 1.3 Microsserviços, SOA, hexagonal, distribuídos · 1.4 Web e APIs (REST, GraphQL, JSON), Python (Django/Flask), Node.js · 1.5 Git · 1.6 Testes, TDD, BDD, qualidade · 1.7 Documentação e homologação.

## 1.1 Ciclo de vida e modelos de processo
| Modelo | Característica | Quando usar |
|---|---|---|
| **Cascata** (waterfall) | Fases sequenciais: requisitos → projeto → implementação → testes → implantação → manutenção | Requisitos estáveis |
| **Modelo em V** | Cada fase de desenvolvimento tem uma de teste correspondente | Sistemas críticos |
| **Incremental** | Entregas parciais funcionais | Entregar valor cedo |
| **Espiral** (Boehm) | Ciclos com **análise de riscos** em cada volta | Projetos grandes e arriscados |
| **Prototipação** | Protótipo para validar requisitos | Requisitos incertos |
| **RUP / Processo Unificado** | Fases: **Concepção, Elaboração, Construção, Transição**; iterativo; dirigido por casos de uso | — |
| **Ágil** | Iterativo, incremental, entregas curtas | Mudança frequente |

### Engenharia de requisitos
- **Etapas**: elicitação (levantamento) → análise/negociação → especificação → validação → gerenciamento.
- **Requisito funcional (RF)**: o que o sistema **faz** ("emitir certidão"). **Não funcional (RNF)**: **como**/restrições (desempenho, segurança, usabilidade, disponibilidade 99,9%).
- Técnicas de elicitação: entrevistas, questionários, workshops/JAD, observação (etnografia), **prototipação**, brainstorming, análise de documentos, **histórias de usuário** ("Como **<papel>**, quero **<ação>** para **<benefício>**"), critérios de aceitação.
- **INVEST** (boa história): Independente, Negociável, Valiosa, Estimável, Small (pequena), Testável.

### Manifesto Ágil (2001) — 4 valores
1. **Indivíduos e interações** mais que processos e ferramentas.
2. **Software em funcionamento** mais que documentação abrangente.
3. **Colaboração com o cliente** mais que negociação de contratos.
4. **Responder a mudanças** mais que seguir um plano.
+ **12 princípios** (entregas frequentes, mudanças bem-vindas, ritmo sustentável, simplicidade, equipes auto-organizáveis, reflexão periódica…).
> ⚠️ "Mais que" ≠ "em vez de": os itens da direita **também têm valor**.

### Scrum (Guia 2020)
| Elemento | Detalhe |
|---|---|
| **Papéis (accountabilities)** | **Product Owner** (maximiza valor, gerencia o Product Backlog), **Scrum Master** (líder-servidor, remove impedimentos, garante o Scrum), **Developers** (constroem o incremento) |
| Time | Pequeno, **10 pessoas ou menos**, sem sub-times nem hierarquia |
| **Eventos** | **Sprint** (≤ 1 mês, contém os demais) · **Sprint Planning** (≤ 8 h p/ sprint de 1 mês) · **Daily Scrum** (**15 min**) · **Sprint Review** (≤ 4 h) · **Sprint Retrospective** (≤ 3 h) |
| **Artefatos → compromissos** | Product Backlog → **Meta do Produto** · Sprint Backlog → **Meta da Sprint** · Incremento → **Definição de Pronto (DoD)** |
| Pilares | **Transparência, inspeção, adaptação** |
| Valores | Compromisso, foco, abertura, respeito, coragem |

> ⚠️ Guia 2020 eliminou o termo "Development Team" (agora **Developers**) e o "papel" virou **accountability**. Quem pode cancelar a Sprint: **só o Product Owner**.

### Kanban
- Visualizar o fluxo (quadro: **A fazer → Fazendo → Feito**), **limitar o WIP** (trabalho em progresso), gerenciar o fluxo, políticas explícitas, melhoria contínua. **Puxado (pull)**, sem iterações fixas.
- Métricas: **lead time** (do pedido à entrega), **cycle time** (do início do trabalho à entrega), throughput, **CFD** (diagrama de fluxo cumulativo).

| | Scrum | Kanban |
|---|---|---|
| Cadência | Sprints fixas | Fluxo contínuo |
| Papéis | PO, SM, Developers | Não prescreve |
| Limite | Escopo por sprint | **WIP por coluna** |
| Mudança | Evitada durante a sprint | A qualquer momento |

Outros: **XP** (programação em pares, TDD, integração contínua, refatoração, releases pequenos), **Lean** (eliminar desperdícios), **FDD**, **SAFe** (ágil em escala).

## 1.2 Orientação a objetos, SOLID e Clean Code
**4 pilares da POO**
| Pilar | Definição |
|---|---|
| **Abstração** | Modelar só o essencial do objeto |
| **Encapsulamento** | Esconder o estado interno; acesso via métodos (getters/setters); modificadores de acesso |
| **Herança** | Classe filha reaproveita atributos/métodos da classe pai ("é um") |
| **Polimorfismo** | Mesmo método, comportamentos diferentes. **Sobrescrita** (override, em tempo de execução) × **Sobrecarga** (overload, mesmo nome com parâmetros diferentes, em compilação) |

- Classe (molde) × objeto (instância). Classe **abstrata** (não instanciável) × **interface** (contrato).
- **Associação** (usa), **agregação** (todo-parte, parte existe sozinha — losango vazio na UML), **composição** (parte morre com o todo — losango cheio).
- **Modificadores (Java)**: `public` (todos), `protected` (pacote + subclasses), *default* (pacote), `private` (só a classe). (IDCAP 2025 cobrou essa ordem.)
- **Acoplamento baixo** e **coesão alta** = bom design.

### SOLID
| Letra | Princípio | Em uma frase |
|---|---|---|
| **S** | Single Responsibility (Responsabilidade Única) | Uma classe deve ter **um único motivo para mudar** |
| **O** | Open/Closed (Aberto/Fechado) | **Aberta para extensão, fechada para modificação** |
| **L** | Liskov Substitution | Subclasses devem poder **substituir** a classe base sem quebrar o programa |
| **I** | Interface Segregation | Muitas interfaces **específicas** são melhores que uma genérica ("não force o cliente a depender do que não usa") |
| **D** | Dependency Inversion | Dependa de **abstrações**, não de implementações (módulos de alto nível não dependem dos de baixo nível) |

### Clean Code (Robert C. Martin)
- Nomes **significativos e pronunciáveis**; funções **pequenas** que fazem **uma coisa**; poucos parâmetros; sem efeitos colaterais.
- Comentário não compensa código ruim — o código deve se explicar. **DRY** (Don't Repeat Yourself), **KISS**, **YAGNI**.
- **Regra do escoteiro**: deixe o código mais limpo do que encontrou. **Refatoração**: melhorar a estrutura sem mudar o comportamento.
- *Code smells*: método longo, classe grande (God class), código duplicado, muitos parâmetros.

## 1.3 Arquiteturas de software
| Arquitetura | Ideia | Prós / contras |
|---|---|---|
| **Monolito** | Uma única unidade implantável | Simples no início; escala mal |
| **Camadas (N-tier)** | Apresentação → negócio → dados | Separação; pode virar rígido |
| **MVC** | **Model** (dados/regras), **View** (interface), **Controller** (recebe entrada do usuário e coordena) | Cobrado pela IDCAP |
| **SOA** | Serviços reutilizáveis e interoperáveis, geralmente via **ESB** (barramento), contratos (WSDL/SOAP) | Componentes: **provedor, consumidor, registro (UDDI)**; serviço = implementação + **contrato** + interface |
| **Microsserviços** | Serviços **pequenos, independentes**, cada um com **seu banco**, implantação independente, comunicação via API/mensageria | Escala e autonomia; complexidade operacional (observabilidade, consistência eventual) |
| **Hexagonal (Ports and Adapters)** — Alistair Cockburn | **Núcleo de domínio** isolado; **portas** (interfaces) e **adaptadores** (BD, UI, APIs) nas bordas | Testabilidade, troca de tecnologia |
| **Orientada a eventos (EDA)** | Produtores publicam eventos; consumidores reagem; **broker** (Kafka, RabbitMQ) | Modelos: **pub/sub** e **streaming de eventos** (IDCAP 2025) |
| **Serverless** | Funções sob demanda (FaaS) | Sem gestão de servidor; cold start |

- Microsserviços — padrões: **API Gateway**, **Service Discovery**, **Circuit Breaker**, **Saga** (transações distribuídas), **Database per service**, **CQRS**, **Strangler Fig** (migração gradual do monolito).
- **Sistemas distribuídos** — **Teorema CAP**: em caso de **partição** de rede, escolhe-se entre **Consistência** e **Disponibilidade** (não dá para ter C, A e P ao mesmo tempo). **BASE** (Basically Available, Soft state, Eventual consistency) × **ACID**.
- Processamento **paralelo** (memória compartilhada) × **distribuído** (cada nó com sua memória, troca de mensagens) — IDCAP 2025.

## 1.4 Desenvolvimento web e APIs
### REST
- Estilo arquitetural (Roy Fielding, 2000). **Restrições**: cliente-servidor, **stateless** (sem estado no servidor entre requisições), cacheável, interface uniforme, sistema em camadas, código sob demanda (opcional).
| Verbo | CRUD | Idempotente? | Seguro? |
|---|---|---|---|
| **GET** | Read | Sim | Sim |
| **POST** | Create | **Não** | Não |
| **PUT** | Update (substitui) | Sim | Não |
| **PATCH** | Update parcial | Não (em geral) | Não |
| **DELETE** | Delete | Sim | Não |

| Código | Significado |
|---|---|
| 1xx | Informativo |
| **200** OK · **201** Created · **204** No Content | Sucesso |
| **301** permanente · **302** temporário · **304** Not Modified | Redirecionamento |
| **400** Bad Request · **401** Unauthorized (não autenticado) · **403** Forbidden (sem permissão) · **404** Not Found · **409** Conflict · **429** Too Many Requests | Erro do cliente |
| **500** Internal Server Error · **502** Bad Gateway · **503** Service Unavailable · **504** Gateway Timeout | Erro do servidor |

### GraphQL × REST × gRPC
| | REST | GraphQL | gRPC |
|---|---|---|---|
| Endpoint | Vários (por recurso) | **Um único** (`/graphql`) | Métodos RPC |
| Dados | Formato fixo (over/under-fetching) | **Cliente pede exatamente os campos** | Protobuf binário |
| Operações | Verbos HTTP | **Query** (leitura), **Mutation** (escrita), **Subscription** (tempo real) | Unário e streaming (HTTP/2) |
- **Webhook**: o servidor **chama** uma URL do cliente quando um evento ocorre (notificação "reversa"). (IDCAP 2025: gRPC × Webhook.)
- **JSON**: tipos — string, number, boolean, null, **object** `{}`, **array** `[]`. Chaves **entre aspas duplas**; **não** aceita comentários nem aspas simples.

### Python: Django × Flask
| | **Django** | **Flask** |
|---|---|---|
| Tipo | Framework "**baterias incluídas**" (full-stack) | **Microframework** minimalista |
| Padrão | **MTV** (Model-Template-View) | Livre |
| Recursos nativos | **ORM**, admin automático, autenticação, migrations, proteção CSRF | Roteamento + Jinja2 + Werkzeug; extensões (Flask-SQLAlchemy) |
| Comandos | `django-admin startproject`, `python manage.py runserver / makemigrations / migrate` | `flask run`, `@app.route("/")` |
| APIs | **Django REST Framework (DRF)** | Flask-RESTful |
- Python: listas `[]` mutáveis, tuplas `()` imutáveis, dicionários `{k: v}`, conjuntos `{}`; indentação define blocos; `def`, `class`, `self`; ambientes virtuais (`venv`), `pip`. FastAPI: APIs assíncronas com tipagem.

### Node.js
- Runtime JavaScript no servidor sobre o motor **V8**; **single-thread** com **event loop** e **I/O não bloqueante** (assíncrono) → ótimo para I/O intenso, ruim para CPU intensa.
- Gerenciador **npm** (`package.json`); framework **Express** (`app.get('/', (req, res) => …)`); `async/await`, Promises.

## 1.5 Git
| Comando | Função |
|---|---|
| `git init` / `git clone <url>` | Criar / copiar repositório |
| `git status` / `git log` / `git diff` | Estado / histórico / diferenças |
| `git add` → `git commit -m` | Staging → registrar no repositório local |
| `git push` / `git pull` (= fetch + merge) / `git fetch` | Enviar / trazer e mesclar / só trazer |
| `git branch` / `git checkout -b` / `git switch` | Ramos |
| `git merge` × `git rebase` | Mesclar com commit de merge × reaplicar commits (histórico linear) |
| `git stash` | Guardar alterações temporariamente |
| `git revert` × `git reset` | Novo commit que desfaz × move o ponteiro (reescreve histórico) |
| `git cherry-pick` | Aplicar um commit específico |
| `git tag` | Marcar versão |
- **3 áreas**: working directory → **staging area (index)** → repositório (.git). Git é **distribuído** (cada clone tem o histórico completo) — diferente do SVN (centralizado).
- Fluxos: **GitFlow** (main, develop, feature, release, hotfix), **trunk-based**, GitHub Flow. **Pull/Merge Request** = revisão de código.

## 1.6 Testes e qualidade
| Nível | Objetivo |
|---|---|
| **Unitário** | Menor parte isolada (função, método) — o **mais cedo** no ciclo |
| **Integração** | Módulos **juntos**, interfaces entre componentes |
| **Sistema** | Sistema completo vs requisitos |
| **Aceitação** (homologação/UAT) | Usuário valida se atende ao negócio |
| **Regressão** | Garantir que mudanças não quebraram o que funcionava |
| Desempenho / carga / estresse | Comportamento sob volume; além do limite |
| Fumaça (smoke) | Verificação rápida das funções críticas |

- **Caixa-preta** (funcional, sem ver o código: partição de equivalência, valor-limite) × **caixa-branca** (estrutural, cobertura de comandos/desvios/caminhos).
- **Pirâmide de testes**: muitos unitários (base), menos integração, poucos E2E/UI (topo).
- **Verificação** ("construímos o produto certo **corretamente**?") × **Validação** ("construímos o **produto certo**?").
- Dublês: **mock** (verifica interações), **stub** (respostas prontas), fake, spy.
- **TDD** (Kent Beck): **Red** (escreva um teste que falha) → **Green** (código mínimo para passar) → **Refactor** (melhore). (IDCAP 2025.)
- **BDD** (Dan North): comportamento em linguagem de negócio, **Gherkin**: **Dado** (Given) / **Quando** (When) / **Então** (Then); ferramentas **Cucumber**, Behave, SpecFlow. Etapas: descoberta, formulação (definição), automação (formalização) e entrega.
- **ATDD**: testes de aceitação definidos com o cliente antes do código.
- Ferramentas: **JUnit** (Java), **pytest/unittest** (Python), **Jest/Mocha** (JS), **Selenium** (automação web, livre), **Ranorex** (comercial), Cypress, JMeter (carga), **SonarQube** (qualidade/análise estática).
- **ISO/IEC 25010** (qualidade do produto, 2011 — 8 características): **adequação funcional, eficiência de desempenho, compatibilidade, usabilidade, confiabilidade, segurança, manutenibilidade, portabilidade**. (Versão 2023 tem 9: inclui *safety* e renomeia usabilidade para *interaction capability*.)
- Métricas: cobertura de código, complexidade ciclomática (McCabe = E − N + 2P), dívida técnica.

## 1.7 Documentação e homologação
- Documentos: **documento de requisitos / visão**, casos de uso, histórias de usuário, **diagramas UML**, documentação de API (**OpenAPI/Swagger**), manual do usuário, **README**, ADR (registro de decisões de arquitetura).
- **UML 2.x** — estruturais: **classes**, objetos, componentes, **implantação**, pacotes; comportamentais: **casos de uso**, **atividades**, **estados**, **sequência**, comunicação.
- **Homologação**: ambiente que **espelha produção**, onde o usuário/área demandante valida (testes de aceitação) antes da implantação. Ambientes: **desenvolvimento → teste/QA → homologação (staging) → produção**. Saída: **termo de aceite/homologação**.

## ⚠️ Pegadinhas do bloco
1. **POST não é idempotente**; PUT e DELETE são.
2. **401** = não autenticado; **403** = autenticado mas sem permissão.
3. Daily = **15 min**; sprint ≤ **1 mês**; só o **PO** cancela a sprint.
4. **Sobrecarga** (mesmo nome, parâmetros diferentes) ≠ **sobrescrita** (subclasse redefine).
5. Teste **unitário** é o **primeiro**; **integração** testa módulos juntos (IDCAP 2025).
6. Django = "baterias incluídas"; Flask = **micro**framework.
7. `git pull` = `fetch` + `merge`.

## 🧠 Memorize
- **SOLID**: "**S**ó **O** **L**ouco **I**gnora **D**esign".
- **TDD**: "Vermelho, Verde, Refatora" (semáforo).
- **BDD**: "**Dado–Quando–Então**".

## Questões comentadas (estilo IDCAP — 4 alternativas)

**Q1.** Em uma arquitetura, o núcleo de domínio é isolado de tecnologias externas: a comunicação ocorre por interfaces definidas pelo domínio, enquanto componentes nas bordas conectam banco de dados, interface web e APIs externas. Essa arquitetura e seus dois elementos são conhecidos, respectivamente, como:
(A) Arquitetura em camadas, controladores e modelos. (B) **Arquitetura hexagonal, portas e adaptadores.** (C) Microsserviços, gateways e brokers. (D) SOA, contratos e barramentos.
✅ **B.** Ports and Adapters (Cockburn).

**Q2.** No Scrum, um dos eventos tem duração máxima de 15 minutos, destinado aos Developers para inspecionar o progresso rumo à Meta da Sprint; outro é o evento em que o time inspeciona o incremento com as partes interessadas. Esses eventos são, respectivamente:
(A) Sprint Planning e Retrospective. (B) **Daily Scrum e Sprint Review.** (C) Daily Scrum e Retrospective. (D) Refinement e Sprint Review.
✅ **B.** Retrospectiva = melhoria do processo (pessoas, ferramentas); Review = inspeção do incremento com stakeholders.

**Q3.** Um princípio do SOLID determina que entidades de software devem estar abertas para extensão, mas fechadas para modificação; outro determina que objetos de uma subclasse devem poder substituir objetos da superclasse sem alterar a correção do programa. São, respectivamente:
(A) SRP e DIP. (B) **OCP e LSP.** (C) ISP e LSP. (D) OCP e DIP.
✅ **B.**

**Q4.** Em uma API REST, o método que deve ser usado para criar um novo recurso e o código de status que indica criação bem-sucedida são, respectivamente:
(A) PUT e 200. (B) **POST e 201.** (C) GET e 204. (D) PATCH e 202.
✅ **B.**

**Q5.** Sobre GraphQL, é correto afirmar:
(A) Exige um endpoint para cada recurso. (B) **Permite ao cliente especificar exatamente os campos desejados, por meio de queries, e alterar dados por mutations.** (C) Só funciona com XML. (D) É um banco de dados orientado a grafos.
✅ **B.** GraphQL é linguagem de consulta para APIs (não é banco de grafos — confusão comum com Neo4j).

**Q6.** Comando Git que reaplica os commits de um branch sobre outro, produzindo histórico linear:
(A) merge. (B) **rebase.** (C) revert. (D) stash.
✅ **B.**
