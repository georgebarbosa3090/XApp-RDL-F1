# R2 — Super Revisão de Conhecimentos Específicos (TI)

> **20 questões, 50 pontos.** Tabelas-mãe dos 6 blocos do edital.

## 1. Engenharia de Software
| Tema | Resumo |
|---|---|
| Scrum | PO (valor, backlog) · SM (líder-servidor) · Developers · Sprint ≤ 1 mês · Daily **15 min** · Review (incremento) · Retro (processo) · DoD · só o PO cancela a sprint |
| Kanban | fluxo contínuo, **limite de WIP**, puxado, lead/cycle time |
| Manifesto Ágil | indivíduos > processos · software > documentação · colaboração > contrato · mudança > plano |
| POO | abstração, **encapsulamento**, herança, **polimorfismo** (sobrescrita ≠ sobrecarga) |
| SOLID | **S**RP uma razão p/ mudar · **O**CP aberto extensão/fechado modificação · **L**SP substituição · **I**SP interfaces específicas · **D**IP depender de abstrações |
| Arquiteturas | MVC · SOA (ESB, contrato) · **microsserviços** (banco próprio, Saga, API Gateway, Circuit Breaker) · **hexagonal** (portas e adaptadores) · EDA (pub/sub, broker) · CAP |
| REST | GET/PUT/DELETE idempotentes · POST não · 201 criado · 401 não autenticado · 403 proibido · 404 · 500 |
| GraphQL | endpoint único, query/mutation/subscription, cliente escolhe campos |
| Django × Flask | baterias incluídas (ORM, admin, MTV) × microframework |
| Node.js | V8, event loop, I/O não bloqueante, npm, Express |
| Git | add → commit → push · pull = fetch + merge · rebase linear · revert (novo commit) × reset |
| Testes | unitário (1º) → integração → sistema → aceitação · regressão · caixa-preta × branca |
| TDD / BDD | **Red-Green-Refactor** · **Dado-Quando-Então** (Gherkin, Cucumber) |
| Qualidade | ISO 25010 (adequação funcional, eficiência, compatibilidade, usabilidade, confiabilidade, segurança, manutenibilidade, portabilidade) |

## 2. DevOps, Nuvem, SO, Redes
| Tema | Resumo |
|---|---|
| CI / Delivery / Deployment | build+teste a cada commit / pronto p/ produção com **aprovação manual** / **automático** |
| GitLab CI × Jenkins | `.gitlab-ci.yml` (stages, jobs, script, artifacts, runners) × `Jenkinsfile` (agents, plugins) |
| IaC | Terraform (provisionamento, declarativo, state) · Ansible (configuração, agentless, YAML) |
| Docker | imagem → contêiner · FROM, RUN, COPY, CMD, ENTRYPOINT, EXPOSE · compartilha kernel · portabilidade |
| Kubernetes | **Pod** (menor unidade) · Deployment · Service · Ingress · ConfigMap/Secret · **etcd** (estado) · **scheduler** · kubelet |
| Nuvem | IaaS (eu: SO+app) · PaaS (eu: app+dados) · SaaS (só uso) · pública/privada/**híbrida**/comunitária · 5 características NIST |
| Linux | chmod 755 = rwxr-xr-x · /etc config · /var/log logs · systemctl · ps/kill · grep |
| Windows Server | AD DS (domínio, OU, GPO, Kerberos, LDAP 389), DNS, DHCP, IIS, Hyper-V |
| OSI | Aplicação, Apresentação, Sessão, **Transporte** (TCP/UDP), **Rede** (IP, roteador), **Enlace** (MAC, switch, VLAN), Física |
| Portas | 21 FTP · **22 SSH** · 23 Telnet · 25 SMTP · **53 DNS** · 67/68 DHCP · **80 HTTP** · 110 POP3 · 143 IMAP · 161 SNMP · 389 LDAP · **443 HTTPS** · **587 SMTP-TLS** · **3389 RDP** · 3306 MySQL · 5432 PostgreSQL |
| IPv4 | privados **10/8, 172.16/12, 192.168/16** · hosts = 2^(32−n) − 2 · /26 = 64 end., 62 hosts |
| IPv6 | **128 bits**, 8 grupos × 16 bits, 4 hex, ":" · "::" uma vez · sem broadcast |
| Protocolos | DNS (A, AAAA, MX, CNAME, PTR) · DHCP (DORA) · ARP (IP→MAC) · SNMP (gerente, agente, MIB, GET/SET/TRAP) · SIP (VoIP) |
| Virtualização | hipervisor **tipo 1** (ESXi, Hyper-V, KVM) × **tipo 2** (VirtualBox) |
| Backup | full · **incremental** (desde o último qualquer; restaura full + todos) · **diferencial** (desde o último full; restaura full + último) · **3-2-1** · RPO (dados) × RTO (tempo) · RAID ≠ backup |
| Observabilidade | métricas + logs + traces · **Zabbix** (agentes, templates, triggers) · **Prometheus** (pull, PromQL, exporters) · **Grafana** (dashboards) · SLI → SLO → SLA |

## 3. Dados
| Tema | Resumo |
|---|---|
| ANSI/SPARC | externo · conceitual/lógico · interno |
| Modelagem | **conceitual** (DER) → **lógico** (tabelas, chaves) → **físico** (SGBD, DDL) |
| Normalização | 1FN atômico · 2FN sem dependência **parcial** · 3FN sem **transitiva** · FNBC determinante é chave |
| SQL | FROM → WHERE → GROUP BY → **HAVING** → SELECT → ORDER BY · INNER/LEFT/RIGHT/FULL JOIN · trigger automático |
| ACID | Atomicidade (tudo ou nada) · Consistência · Isolamento · Durabilidade |
| Isolamento | Read Uncommitted → Read Committed → Repeatable Read → Serializable |
| PostgreSQL × MySQL | 5432, JSONB, pgvector, MVCC × 3306, InnoDB |
| NoSQL | chave-valor (Redis) · documento (**MongoDB**, CouchDB) · colunar (Cassandra) · grafo (Neo4j) · BASE, CAP |
| Vetorial | **embeddings**, similaridade **cosseno**, ANN, **HNSW**, pgvector, Pinecone, Milvus, Chroma, FAISS → RAG |
| DW/BI | DW orientado a assunto, integrado, não volátil, variante no tempo · ETL × ELT · fato × dimensão · **estrela** (desnormalizada) × floco de neve · drill-down/roll-up/slice/dice/pivot · MOLAP/ROLAP/HOLAP/DOLAP · Data Mining |

## 4. Segurança, LGPD e leis
| Tema | Resumo |
|---|---|
| CID + A + N | confidencialidade, integridade, disponibilidade, autenticidade, não repúdio |
| ISO 27001 × 27002 | requisitos SGSI, **certificável** × guia de controles · 2022: **93 controles, 4 temas** (37 org., 8 pessoas, 14 físicos, 34 tecnol.) |
| IAM | AAA · MFA (fatores diferentes) · RBAC/ABAC · menor privilégio · Zero Trust · SSO (SAML, OIDC) |
| OAuth 2.0 | **autorização** · resource owner, client, **authorization server**, resource server · Authorization Code + PKCE · OIDC = autenticação (ID token JWT) |
| OWASP 2021 | A01 Broken Access Control · A02 Crypto · **A03 Injection (inclui XSS)** · A04 Insecure Design · A05 Misconfig · A06 Componentes · A07 Auth · A08 Integridade · A09 Logging · A10 SSRF |
| SAST × DAST | código, cedo, caixa-branca × execução, caixa-preta |
| Riscos | modificar · reter · evitar · compartilhar · avaliação = identificação + análise + avaliação |
| Incidentes | NIST 800-61: preparação → detecção/análise → contenção/erradicação/recuperação → pós-incidente · CSF 2.0: **Governar**, Identificar, Proteger, Detectar, Responder, Recuperar |
| Cripto | simétrica AES (rápida) × assimétrica RSA/ECC · assinatura = hash + **privada do remetente** · hash SHA-256 · A1 = 1 ano |
| PNSI × PNCiber | Dec. 9.637/2018 (adm. federal, **CGSI**, GSI) × Dec. 11.856/2023 (País, **CNCiber**, GSI, multissetorial) |
| LGPD | controlador decide · operador executa · encarregado = canal · **10 princípios** · **10 bases** (art. 7º) · sensíveis sem legítimo interesse e crédito · art. 18 direitos · **art. 20 revisão automatizada** · art. 48 incidente (3 dias úteis) · multa até **2% / R$ 50 mi** · **órgão público não leva multa** · anonimizado fora |
| LAI | sem motivo · **20 + 10 dias** · recurso 10 dias · reservada **5**, secreta **15**, ultrassecreta **25** · pessoais **100 anos** |
| Marco Civil | neutralidade · conexão **1 ano** · aplicação **6 meses** · art. 19 ordem judicial (STF 2025 relativizou) · art. 21 nudez: notificação |

## 5. Inteligência Artificial
| Tema | Resumo |
|---|---|
| ML | supervisionado (classificação, regressão) · não supervisionado (clustering, PCA) · reforço (agente, recompensa) |
| Métricas | precisão (evitar FP) · **recall** (evitar FN) · F1 · overfitting × underfitting |
| PLN | tokenização, stemming × lematização, NER, sentimento, Transformer (atenção, 2017), BERT × GPT |
| LLM | próximo token · pré-treino → fine-tuning → RLHF · tokens · janela de contexto · **temperatura** · alucinação |
| Prompts | zero-shot · **few-shot** · **chain-of-thought** · persona · system prompt · ReAct · formato de saída |
| RAG | chunking → embeddings → banco vetorial → busca por similaridade → prompt aumentado → resposta com fontes · **não altera pesos** |
| Agentes | LLM + ferramentas + memória + planejamento · MCP · human-in-the-loop |
| Riscos | **prompt injection** (direta/indireta) · vazamento · poisoning · excessive agency · improper output · alucinação |
| Governança | NIST AI RMF (Govern, Map, Measure, Manage) · ISO/IEC 42001 · PL 2.338/2023 (risco excessivo/alto) · EBIA · LGPD (base legal, RIPD, art. 20) · transparência e supervisão humana |

## 6. Governança e Contratações
| Tema | Resumo |
|---|---|
| COBIT 2019 | **EDM** (governança) · APO · BAI · DSS · MEA · 40 objetivos · 7 componentes · 6 princípios |
| ITIL 4 | SVS · 4 dimensões · **7 princípios** · cadeia de valor (planejar, melhorar, engajar, desenho e transição, obter/construir, entregar e suportar) · **34 práticas (14+17+3)** · incidente (restaurar) × problema (causa raiz) |
| Projetos | PMBOK 6: iniciação, planejamento, execução, monitoramento e controle, encerramento · 10 áreas · PMBOK 7: 12 princípios, 8 domínios · TAP, EAP, caminho crítico, CPI = EV/AC, SPI = EV/PV |
| PDTIC | diagnóstico, planejamento e gestão de TIC · SWOT · GUT · alinhado ao PEI · contratações alinhadas a ele |
| Lei 14.129 | governo digital, plataforma, dados abertos, linguagem clara, interoperabilidade, presencial mantido, CPF suficiente · Estados **aderem por ato próprio** |
| Lei 14.133 | fases: preparatória → edital → propostas/lances → julgamento → **habilitação** → recursal → homologação · pregão (comuns), concorrência, concurso, leilão, **diálogo competitivo** · convite e TP extintos · inexigibilidade (inviável) × dispensa · ETP (art. 18) · TR · contínuos 5 → 10 anos · TI estruturante até 15 · PNCP |
| IN 94/2022 | Planejamento → Seleção → Gestão · **DFD** → Equipe (**requisitante, técnico, administrativo**) → **ETP** → **Mapa de Riscos** → **TR** · Gestão: **gestor + fiscais técnico, requisitante, administrativo** · vedado: várias soluções num contrato, marca, homem-hora/posto (salvo justificativa), mesmo fornecedor executar e fiscalizar |
