# Módulo 9 — Específicos 4: Segurança da Informação, Cibersegurança, LGPD e Legislação

> Bloco com **mais leis nomeadas** no edital → prioridade máxima. Estimativa: 4–5 questões. Também é tema provável da **discursiva**.

## Mapa do edital (item 4)
4.1 CID · 4.2 ISO/IEC 27001 e 27002 · 4.3 IAM (AD, OAuth 2.0, SSO) · 4.4 OWASP Top 10, SAST/DAST · 4.5 Riscos, incidentes, criptografia · 4.6 Decreto 9.637/2018 (PNSI) e Decreto 11.856/2023 (PNCiber) · 4.7 LGPD (Lei 13.709/2018) · 4.8 LAI (Lei 12.527/2011) e Marco Civil (Lei 12.965/2014).

## 4.1 Princípios de segurança
| Princípio | Garante | Ameaça típica | Controle típico |
|---|---|---|---|
| **Confidencialidade** | Só pessoas **autorizadas** acessam | Vazamento, sniffing | Criptografia, controle de acesso |
| **Integridade** | Informação **não alterada** indevidamente | Adulteração | Hash, assinatura digital |
| **Disponibilidade** | Acesso **quando necessário** | DoS/DDoS, ransomware | Redundância, backup |
| Autenticidade | Origem/identidade verdadeira | Spoofing | Certificado, assinatura |
| Não repúdio (irretratabilidade) | Autor não pode negar a autoria | — | **Assinatura digital** |

> 🧠 **CIDAN**: **C**onfidencialidade, **I**ntegridade, **D**isponibilidade, **A**utenticidade, **N**ão repúdio (CID em inglês = CIA).

- **Segurança física** (protege equipamentos e instalações: acesso, energia, incêndio) × **lógica** (protege dados e sistemas: senhas, firewall, criptografia) — IDCAP 2025.
- **Controles**: **gerenciais/administrativos** (políticas, treinamento), **operacionais** (executados por pessoas: backup, guarda), **técnicos/lógicos** (hardware/software: firewall, criptografia) — IDCAP 2025. Por função: **preventivos, detectivos, corretivos**, dissuasivos, compensatórios.

## 4.2 ABNT NBR ISO/IEC 27001 e 27002 (versões 2022)
| | **27001:2022** | **27002:2022** |
|---|---|---|
| Natureza | **Requisitos** do **SGSI** (Sistema de Gestão de Segurança da Informação) | **Código de prática / guia** de **controles** |
| Certificável? | **Sim** (organizações são certificadas nela) | **Não** |
| Estrutura | Cláusulas **4 a 10** (requisitos) + **Anexo A** (lista de controles) | Detalha cada controle: propósito, orientação |
| Em uma palavra | **Gestão** | **Controles** |

- **Cláusulas da 27001** (estrutura harmonizada ISO, ciclo **PDCA**): 4 Contexto da organização · 5 **Liderança** (política de SI) · 6 **Planejamento** (avaliação e tratamento de riscos, objetivos) · 7 Apoio (recursos, competência, conscientização, comunicação, informação documentada) · 8 **Operação** · 9 **Avaliação de desempenho** (monitoramento, **auditoria interna**, **análise crítica pela direção**) · 10 **Melhoria** (não conformidade, ação corretiva, melhoria contínua).
- **Declaração de Aplicabilidade (SoA)**: documento que lista os controles do Anexo A, se são aplicáveis e a justificativa.
- **Anexo A / 27002:2022**: **93 controles** em **4 temas**: **Organizacionais (37)**, **Pessoas (8)**, **Físicos (14)**, **Tecnológicos (34)**. Atributos: tipo de controle (preventivo, detectivo, corretivo), propriedades (CID), conceitos de cibersegurança (identificar, proteger, detectar, responder, recuperar).
- **11 controles novos (2022)**: inteligência de ameaças; segurança para uso de **serviços em nuvem**; prontidão de TIC para continuidade; monitoramento da segurança física; **gestão de configuração**; **exclusão de informações**; **mascaramento de dados**; **prevenção de vazamento de dados (DLP)**; atividades de monitoramento; **filtragem web**; **codificação segura**.
> ⚠️ Versão **2013**: **114 controles** em **14 seções** (A.5 a A.18). A 2022 tem **93 em 4 temas**.

- Família: **27005** (gestão de riscos de SI), **27701** (privacidade — extensão para PII), **27017** (controles para nuvem), **27018** (PII em nuvem pública), **27035** (incidentes), **22301** (continuidade), **31000** (riscos em geral).

## 4.3 Gestão de identidades e acessos (IAM)
- **AAA**: **Autenticação** (quem é você?) → **Autorização** (o que pode fazer?) → **Auditoria/Accounting** (o que fez?).
- **Fatores de autenticação**: algo que você **sabe** (senha, PIN), **tem** (token, celular, certificado), **é** (biometria). **MFA** = dois ou mais fatores **de categorias diferentes** (senha + PIN **não** é MFA).
- **Modelos de controle de acesso**: **DAC** (discricionário — o dono decide), **MAC** (obrigatório — rótulos/níveis de classificação), **RBAC** (baseado em **papéis/funções**), **ABAC** (baseado em **atributos**: usuário, recurso, contexto, horário).
- **Princípios**: **menor privilégio**, **necessidade de conhecer** (need-to-know), **segregação de funções**, revisão periódica de acessos, ciclo de vida (*joiner-mover-leaver*). **PAM**: gestão de acessos privilegiados (cofre de senhas, sessão gravada).
- **Zero Trust**: "**nunca confie, sempre verifique**" — não há rede interna confiável; verificação contínua de identidade, dispositivo e contexto; microssegmentação.
- **Active Directory**: diretório da Microsoft (domínios, OUs, GPOs), autenticação **Kerberos** (tickets — TGT; KDC) e NTLM (legado); protocolo **LDAP**. **Microsoft Entra ID** (antigo Azure AD): IAM em nuvem (SAML, OIDC, OAuth).
- **SSO (Single Sign-On)**: um login para vários sistemas. Protocolos: **SAML 2.0** (XML, corporativo — IdP e SP), **OpenID Connect**, Kerberos. Ex. público: **Login gov.br** (contas bronze, prata, ouro).

### OAuth 2.0 (RFC 6749) — **autorização delegada**
| Papel | Quem é |
|---|---|
| **Resource Owner** | O usuário dono dos dados |
| **Client** | A aplicação que quer acessar em nome do usuário |
| **Authorization Server** | Emite os tokens após autenticar e obter consentimento |
| **Resource Server** | A API que guarda os recursos e aceita o **access token** |

- **Fluxos (grants)**: **Authorization Code** (+ **PKCE** — recomendado para web, mobile e SPA), **Client Credentials** (máquina a máquina, sem usuário), **Device Code** (TVs, CLI), Refresh Token. **Implicit** e **Resource Owner Password** são **desaconselhados** (OAuth 2.1).
- **Access token** (curta duração) + **refresh token** (obtém novo access token) + **scopes** (escopos de permissão).
- **OAuth 2.0 é autorização, não autenticação.** A camada de **autenticação/identidade** é o **OpenID Connect (OIDC)**, que adiciona o **ID Token** (um **JWT**).
- **JWT**: `header.payload.signature` em Base64URL. É **assinado** (integridade), **não criptografado** por padrão — não coloque dados sensíveis no payload (JWE criptografa).

## 4.4 Segurança em aplicações
### OWASP Top 10 — 2021 (versão mais cobrada) e 2025 (atual)
| # | **2021** | **2025** |
|---|---|---|
| A01 | **Broken Access Control** (quebra de controle de acesso) | Broken Access Control |
| A02 | **Cryptographic Failures** (falhas criptográficas) | **Security Misconfiguration** |
| A03 | **Injection** (SQL, comandos, **XSS** entra aqui) | **Software Supply Chain Failures** (cadeia de suprimentos — novo) |
| A04 | **Insecure Design** (design inseguro — novo em 2021) | Cryptographic Failures |
| A05 | **Security Misconfiguration** | Injection |
| A06 | **Vulnerable and Outdated Components** | Insecure Design |
| A07 | **Identification and Authentication Failures** | Authentication Failures |
| A08 | **Software and Data Integrity Failures** (novo em 2021) | Software or Data Integrity Failures |
| A09 | **Security Logging and Monitoring Failures** | Security Logging and Alerting Failures |
| A10 | **Server-Side Request Forgery (SSRF)** (novo em 2021) | **Mishandling of Exceptional Conditions** (novo) |

> ⚠️ Na 2021, **XSS foi incorporado a Injection (A03)**. Em 2021, Broken Access Control **subiu para 1º**. Na 2025, SSRF foi incorporado a Broken Access Control. Se a questão não disser a versão, pense na **2021**.

| Vulnerabilidade | Prevenção |
|---|---|
| **SQL Injection** | **Consultas parametrizadas / prepared statements**, ORM, validação de entrada, menor privilégio no BD |
| **XSS** (refletido, armazenado, baseado em DOM) | **Codificação/escape da saída**, validação, **CSP** (Content Security Policy), cookies HttpOnly |
| **CSRF** | Tokens anti-CSRF, cookie **SameSite**, reautenticação |
| Broken Access Control / **IDOR** | Checar autorização no servidor a cada requisição; negar por padrão |
| Falhas de autenticação | MFA, limitar tentativas, senhas com hash forte (**bcrypt, Argon2**, com **salt**) |
| SSRF | Lista de permissões de destinos, bloquear IPs internos/metadados |

### Testes de segurança de aplicações
| Técnica | Como | Quando | Ferramentas |
|---|---|---|---|
| **SAST** (estático) | Analisa o **código-fonte**/binário **sem executar** — **caixa-branca** | **Cedo** (IDE, commit, CI) | SonarQube, Semgrep, Checkmarx, Fortify |
| **DAST** (dinâmico) | Ataca a aplicação **em execução**, de fora — **caixa-preta** | Homologação/produção | **OWASP ZAP**, Burp Suite, Nikto |
| IAST | Agente instrumentado durante a execução | Testes | Contrast |
| **SCA** | Analisa **dependências de terceiros** (CVEs, licenças), gera **SBOM** | CI | OWASP Dependency-Check, Snyk, Dependabot |
| RASP | Proteção em tempo de execução, dentro da app | Produção | — |
| Pentest | Teste de invasão manual/autorizado | Periódico | Kali, Metasploit |

- SAST: encontra falhas cedo, mas gera **falsos positivos** e não vê configuração em execução. DAST: encontra falhas reais em execução, independe da linguagem, mas chega **tarde** e não aponta a linha do código.
- **Secure SDLC / shift-left**, **threat modeling** (STRIDE: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege), **WAF** (firewall de aplicação web, camada 7).

## 4.5 Riscos, incidentes e criptografia
### Gestão de riscos (ISO 31000 e ISO/IEC 27005)
- **Risco** = efeito da incerteza nos objetivos ≈ **probabilidade × impacto**. Uma **ameaça** explora uma **vulnerabilidade** de um **ativo**, causando **impacto**.
- **Processo**: comunicação e consulta · escopo, contexto e critérios · **processo de avaliação de riscos** (= **identificação + análise + avaliação**) · **tratamento** · monitoramento e análise crítica · registro e relato.
- **ISO 31000** — estrutura (framework): **liderança e comprometimento** no centro; **integração, concepção, implementação, avaliação e melhoria** (IDCAP 2025 cobrou "implementação e avaliação").

| Tratamento do risco | Exemplo |
|---|---|
| **Modificar / mitigar / reduzir** | Implantar controles (MFA, backup) |
| **Reter / aceitar** | Risco dentro do apetite; decisão consciente |
| **Evitar** | Não realizar a atividade |
| **Compartilhar / transferir** | **Seguro**, terceirização |
- **Risco inerente** (antes dos controles) × **residual** (após). **Apetite** a risco × tolerância.

### Resposta a incidentes
- **Incidente de segurança**: evento adverso, confirmado ou suspeito, que compromete CID.
- **NIST SP 800-61 (rev. 2)** — 4 fases: **1. Preparação · 2. Detecção e Análise · 3. Contenção, Erradicação e Recuperação · 4. Atividades pós-incidente (lições aprendidas)**. A rev. 3 (2025) alinhou-se às funções do CSF 2.0.
- **NIST CSF 2.0 (2024)** — 6 funções: **Governar (Govern — nova)**, **Identificar**, **Proteger**, **Detectar**, **Responder**, **Recuperar**. (CSF 1.1 tinha 5, sem Governar.)
- Equipes: **ETIR** (Equipe de Tratamento e Resposta a Incidentes) / **CSIRT**; no governo federal, **CTIR Gov** (GSI/PR). Cadeia de custódia e preservação de evidências.
- Ferramentas: **SIEM** (correlação de logs e eventos — Splunk, Wazuh, QRadar), **SOAR** (orquestração e **automação** de resposta), **UEBA** (análise de **comportamento** de usuários e entidades), **EDR/XDR** (detecção nos endpoints), **IDS** (detecta e alerta — passivo) × **IPS** (detecta e **bloqueia** — inline): **NIDS/NIPS** (rede), **HIDS/HIPS** (host), WIPS (sem fio). Detecção por **assinatura** × por **anomalia**. **Honeypot**. **DMZ**.

### Ataques que caem
| Ataque | Descrição |
|---|---|
| **Phishing** / spear phishing / whaling | Mensagem fraudulenta / direcionada / a executivos |
| **Engenharia social** | Explora a confiança humana |
| **Força bruta** / credential stuffing | Tentativa exaustiva / senhas vazadas reutilizadas |
| **DoS / DDoS** | Esgota recursos; DDoS usa **botnet** |
| **Man-in-the-Middle** | Intercepta comunicação |
| **Ransomware** | Criptografa e extorque (dupla extorsão: vaza também) |
| **Zero-day** | Explora falha sem correção conhecida |
| **APT** | Ameaça persistente avançada (longo prazo, alvo específico) |
| Sniffing | Captura tráfego (Wireshark, tcpdump) |

### Criptografia
| | **Simétrica** | **Assimétrica** |
|---|---|---|
| Chaves | **Uma** chave secreta compartilhada | **Par**: pública + privada |
| Velocidade | **Rápida** | Lenta |
| Problema | **Distribuição** segura da chave | Desempenho |
| Algoritmos | **AES** (128/192/256), 3DES, ChaCha20 (DES: obsoleto) | **RSA**, **ECC** (curvas elípticas), **Diffie-Hellman** (troca de chaves), DSA/ECDSA |

- **Confidencialidade**: cifrar com a **chave pública do destinatário**; só a privada dele decifra.
- **Assinatura digital**: **hash** da mensagem cifrado com a **chave privada do remetente**; qualquer um verifica com a pública → garante **autenticidade, integridade e não repúdio** (**não** garante confidencialidade).
- **Criptografia híbrida** (TLS): assimétrica para trocar uma chave de sessão + simétrica para os dados.
- **Hash**: função **unidirecional**, saída de **tamanho fixo**, efeito avalanche. **SHA-256/SHA-3** (seguros) × MD5, SHA-1 (inseguros — colisões). **HMAC** = hash + chave (integridade + autenticidade).
- **Certificado digital X.509**: vincula chave pública a uma identidade, assinado por uma **AC**. **ICP-Brasil**: AC Raiz = **ITI**. Tipos: **A1** (arquivo em software, validade de **1 ano**), **A3** (token/cartão/nuvem, validade maior — até 5 anos). Revogação: **LCR/CRL** e **OCSP**.
- **Esteganografia**: esconde a existência da mensagem (em imagem, áudio). Criptografia **pós-quântica** (NIST 2024: ML-KEM, ML-DSA).

## 4.6 Políticas nacionais
### Decreto nº 9.637/2018 — Política Nacional de Segurança da Informação (PNSI)
- Âmbito: **administração pública federal**. Abrange: **segurança cibernética**, **defesa cibernética**, **segurança física e proteção de dados organizacionais**, e ações para assegurar **disponibilidade, integridade, confidencialidade e autenticidade** da informação.
- **GSI/PR** (Gabinete de Segurança Institucional da Presidência): coordenação. Institui o **Comitê Gestor da Segurança da Informação (CGSI)**.
- **Instrumentos**: **Estratégia Nacional de Segurança da Informação (ENSI)** — organizada em **módulos**, como a **E-Ciber** (Estratégia Nacional de Segurança Cibernética, Decreto 10.222/2020) — e **planos nacionais**.
- Deveres dos órgãos: implementar a PNSI; elaborar **Política de Segurança da Informação (POSIN)**; designar **gestor de segurança da informação**; instituir **comitê de segurança da informação**; criar **equipe de tratamento e resposta a incidentes (ETIR)**; capacitar servidores.

### Decreto nº 11.856/2023 — Política Nacional de Cibersegurança (PNCiber)
- Finalidade: orientar a atividade de **segurança cibernética no País** (escopo mais amplo que a PNSI: inclui setor privado e sociedade).
- Cria o **Comitê Nacional de Cibersegurança (CNCiber)**, **coordenado pelo GSI/PR**, com representantes do governo, **sociedade civil, academia e setor empresarial** (caráter multissetorial).
- **Princípios** (síntese): soberania nacional e priorização dos interesses nacionais; garantia dos direitos fundamentais (**liberdade de expressão, proteção de dados, privacidade, acesso à informação**); prevenção de incidentes e ataques, especialmente a **infraestruturas críticas** e serviços essenciais; resiliência; educação e desenvolvimento tecnológico; cooperação entre órgãos e entes; cooperação técnica internacional.
- **Instrumentos**: **Estratégia Nacional de Cibersegurança** e **Plano Nacional de Cibersegurança**.
- Objetivos: desenvolver produtos/serviços/tecnologias nacionais; garantir confidencialidade, integridade, autenticidade e disponibilidade das soluções e dados; proteger infraestruturas críticas; promover **cultura de cibersegurança**; **combater crimes cibernéticos**; cooperação internacional.
> ⚠️ **PNSI (2018)** → segurança da **informação** na **administração federal**, comitê **CGSI**. **PNCiber (2023)** → **cibersegurança no País**, comitê **CNCiber**. Ambos com o **GSI** à frente.

## 4.7 LGPD — Lei nº 13.709/2018 (com alterações da Lei 13.853/2019)
### Aplicação (arts. 3º e 4º)
- Aplica-se a qualquer tratamento por **pessoa natural ou jurídica, de direito público ou privado**, **inclusive nos meios digitais**, se: o tratamento for realizado no Brasil; tiver por objetivo oferta de bens/serviços ou tratamento de dados de indivíduos no Brasil; ou os dados tiverem sido coletados no Brasil.
- **Não se aplica** (art. 4º): tratamento por pessoa natural para fins **exclusivamente particulares e não econômicos**; fins exclusivamente **jornalísticos, artísticos** ou **acadêmicos** (acadêmico: aplicam-se arts. 7º e 11); fins exclusivos de **segurança pública, defesa nacional, segurança do Estado, investigação e repressão de infrações penais** (lei específica); dados vindos do exterior sem comunicação/compartilhamento com agentes brasileiros.

### 🔢 Definições (art. 5º)
| Termo | Definição |
|---|---|
| **Dado pessoal** | Informação relacionada a pessoa natural **identificada ou identificável** |
| **Dado pessoal sensível** | Origem **racial ou étnica**, **convicção religiosa**, **opinião política**, filiação a **sindicato** ou organização religiosa, filosófica ou política, dado de **saúde** ou **vida sexual**, dado **genético** ou **biométrico** |
| **Dado anonimizado** | Titular **não** pode ser identificado (meios técnicos razoáveis) → **fora da LGPD** (art. 12), salvo se a anonimização for revertida |
| **Pseudonimização** | Dado só pode ser associado ao titular com **informação adicional** mantida separadamente → **continua sendo dado pessoal** |
| **Titular** | Pessoa natural a quem os dados se referem |
| **Controlador** | Quem **toma as decisões** sobre o tratamento |
| **Operador** | Quem **realiza o tratamento em nome** do controlador |
| **Encarregado (DPO)** | Pessoa indicada pelo controlador e operador como **canal de comunicação** entre controlador, titulares e ANPD |
| **Agentes de tratamento** | **Controlador e operador** (o encarregado **não** é agente de tratamento) |
| **Consentimento** | Manifestação **livre, informada e inequívoca** para finalidade determinada |
| **Tratamento** | Toda operação: coleta, produção, recepção, classificação, utilização, acesso, reprodução, transmissão, distribuição, processamento, arquivamento, armazenamento, eliminação… |
| **RIPD** | Relatório de Impacto à Proteção de Dados Pessoais |
| **ANPD** | Autoridade Nacional de Proteção de Dados — **autarquia de natureza especial** (Lei 14.460/2022) |

### Princípios (art. 6º) — boa-fé + **10 princípios**
1. **Finalidade** (propósitos legítimos, específicos, explícitos e informados)
2. **Adequação** (compatibilidade com a finalidade informada)
3. **Necessidade** (mínimo necessário — minimização)
4. **Livre acesso** (consulta facilitada e gratuita pelo titular)
5. **Qualidade dos dados** (exatidão, clareza, atualização)
6. **Transparência** (informações claras e acessíveis)
7. **Segurança** (medidas técnicas e administrativas contra acessos não autorizados e situações acidentais ou ilícitas)
8. **Prevenção** (evitar danos)
9. **Não discriminação** (vedado tratamento discriminatório ilícito ou abusivo)
10. **Responsabilização e prestação de contas** (demonstrar a adoção de medidas eficazes)

🧠 "**FAN LQ TSP NR**" → **F**inalidade, **A**dequação, **N**ecessidade, **L**ivre acesso, **Q**ualidade, **T**ransparência, **S**egurança, **P**revenção, **N**ão discriminação, **R**esponsabilização.

### Bases legais — dados pessoais (art. 7º — **10 hipóteses**)
I **consentimento** · II **cumprimento de obrigação legal ou regulatória** · III pela **administração pública**, para **execução de políticas públicas** · IV **estudos por órgão de pesquisa** (anonimização sempre que possível) · V **execução de contrato** ou procedimentos preliminares, a pedido do titular · VI **exercício regular de direitos** em processo judicial, administrativo ou arbitral · VII **proteção da vida** ou da incolumidade física · VIII **tutela da saúde** (por profissionais de saúde, serviços de saúde ou autoridade sanitária) · IX **legítimo interesse** do controlador ou de terceiro · X **proteção do crédito**.

### Dados sensíveis (art. 11)
- Com **consentimento específico e destacado**, para finalidades específicas; ou **sem consentimento** quando indispensável para: obrigação legal; **políticas públicas** pela administração; estudos por órgão de pesquisa; exercício regular de direitos; proteção da vida; tutela da saúde; **garantia da prevenção à fraude e à segurança do titular** em processos de identificação e autenticação.
> ⚠️ Para dados **sensíveis** **NÃO existem** as bases **legítimo interesse** e **proteção do crédito**.

- **Crianças** (art. 14): no **melhor interesse**; consentimento **específico e em destaque** de **pelo menos um dos pais** ou responsável.

### Direitos do titular (art. 18)
Confirmação da existência de tratamento · **acesso** · **correção** · anonimização, bloqueio ou eliminação de dados desnecessários/excessivos · **portabilidade** · eliminação dos dados tratados com consentimento · informação sobre **compartilhamento** · informação sobre a possibilidade de **não consentir** e consequências · **revogação do consentimento**. + **Art. 20**: **revisão de decisões tomadas unicamente com base em tratamento automatizado** (perfis, crédito, IA).

### Poder público (arts. 23 a 32)
- Tratamento para **finalidade pública**, na persecução do **interesse público**, para executar **competências legais**; deve **informar** as hipóteses de tratamento (transparência) e **indicar encarregado**.
- **Uso compartilhado** entre órgãos para políticas públicas e atribuições legais (art. 26); transferência a entes privados é **vedada**, salvo exceções (execução descentralizada, dados acessíveis publicamente, previsão legal/contratos, prevenção de fraudes).
- A ANPD pode solicitar aos órgãos **RIPD** e sugerir padrões.

### Agentes, segurança e incidentes
- Controlador e operador devem manter **registro das operações** (art. 37). A ANPD pode exigir do controlador o **RIPD** (art. 38). O operador segue as **instruções do controlador** (art. 39).
- **Encarregado** (art. 41): aceitar reclamações e comunicações dos titulares; receber comunicações da ANPD; orientar funcionários e contratados; executar demais atribuições.
- **Segurança** (art. 46): medidas técnicas e administrativas; **privacy by design e by default** (desde a concepção).
- **Incidente** (art. 48): o **controlador** deve comunicar à **ANPD e ao titular** o incidente que possa acarretar **risco ou dano relevante**. A **Resolução CD/ANPD nº 15/2024** fixou o prazo de **3 dias úteis** a partir do conhecimento.
- **Responsabilidade**: controlador e operador respondem por danos; operador responde **solidariamente** quando descumprir a lei ou as instruções do controlador.

### Sanções (art. 52) — aplicadas pela ANPD
Advertência · **multa simples de até 2% do faturamento** da pessoa jurídica no Brasil, **limitada a R$ 50 milhões por infração** · multa diária · publicização da infração · bloqueio dos dados · eliminação dos dados · suspensão parcial do funcionamento do banco de dados · suspensão do exercício da atividade de tratamento · proibição parcial ou total da atividade.
> ⚠️ **Órgãos e entidades públicas NÃO recebem multas** (simples ou diária) — podem receber advertência, publicização, bloqueio, eliminação, suspensões e proibição (art. 52, § 3º).

## 4.8 LAI e Marco Civil
### Lei de Acesso à Informação — Lei nº 12.527/2011
- Abrange **União, Estados, DF e Municípios**, os três Poderes, Tribunais de Contas, MP, administração indireta e **entidades privadas sem fins lucrativos** que recebam recursos públicos (quanto a esses recursos).
- **Publicidade é a regra; sigilo, a exceção.**
- **Transparência ativa** (art. 8º): divulgar na internet, independentemente de pedido (estrutura, repasses, despesas, licitações e contratos, programas, FAQ). Municípios com **até 10 mil habitantes** são dispensados da divulgação **na internet**.
- **Transparência passiva** — pedido de acesso: **qualquer interessado**, por qualquer meio legítimo, com identificação; **é vedado exigir os motivos** do pedido (art. 10, § 3º). Serviço gratuito (salvo custo de reprodução).

| 🔢 Prazos LAI | |
|---|---|
| Resposta | **Imediata**; se não for possível, **até 20 dias**, **prorrogáveis por mais 10** (com justificativa) |
| Recurso contra negativa | **10 dias** da ciência, à autoridade hierarquicamente superior, que decide em **5 dias** |

| Classificação (art. 24) | Prazo máximo de restrição |
|---|---|
| **Ultrassecreta** | **25 anos** (prorrogável **uma única vez**, por igual período, pela **Comissão Mista de Reavaliação de Informações — CMRI**) |
| **Secreta** | **15 anos** |
| **Reservada** | **5 anos** |
| **Informações pessoais** (art. 31) | Acesso restrito por até **100 anos**, **independentemente de classificação** |

🧠 "**5 – 15 – 25**" (Reservada, Secreta, Ultrassecreta) e "**20 + 10**" para responder.
- Órgãos devem manter o **SIC** (Serviço de Informação ao Cidadão). No Executivo federal, a plataforma é o **Fala.BR** e há recurso à **CGU**.

### Marco Civil da Internet — Lei nº 12.965/2014
- **Fundamentos e princípios**: liberdade de expressão, **privacidade**, proteção de dados pessoais, **neutralidade de rede**, estabilidade e segurança da rede, natureza participativa.
- **Neutralidade de rede** (art. 9º): tratar **de forma isonômica** quaisquer pacotes, sem distinção por conteúdo, origem, destino, serviço, terminal ou aplicação. Exceções (regulamentadas pelo Decreto 8.771/2016): requisitos técnicos indispensáveis e priorização de **serviços de emergência**.
- **Direitos do usuário** (art. 7º): inviolabilidade da intimidade e da vida privada; **sigilo do fluxo e das comunicações armazenadas** (salvo ordem judicial); não suspensão da conexão, salvo por débito; informações claras nos contratos; não fornecimento de dados pessoais a terceiros sem consentimento.
- **Jurisdição** (art. 11): aplica-se a lei brasileira se ao menos **um ato de coleta, armazenamento, guarda ou tratamento** ocorrer no Brasil.

| 🔢 Guarda de registros | Quem | Prazo |
|---|---|---|
| **Registros de conexão** (art. 13) | **Provedor de conexão** | **1 ano**, sob sigilo |
| **Registros de acesso a aplicações** (art. 15) | **Provedor de aplicação** (PJ, com fins econômicos) | **6 meses**, sob sigilo |
> ⚠️ O **provedor de conexão é proibido** de guardar registros de acesso a aplicações (art. 14). Fornecimento dos registros: só com **ordem judicial**.

- **Responsabilidade por conteúdo de terceiros**: provedor de **conexão** não responde (art. 18). Provedor de **aplicação** (art. 19, texto da lei): responde se, **após ordem judicial específica**, não remover o conteúdo. **Exceção** (art. 21): **nudez ou atos sexuais privados** divulgados sem autorização → responde se não remover após **notificação extrajudicial** do participante.
- **Atualização jurisprudencial (STF, junho/2025, Temas 533 e 987)**: o art. 19 foi declarado **parcialmente inconstitucional**. Em síntese: para conteúdos ilícitos em geral, o provedor de aplicação pode responder após **notificação extrajudicial** (regime do art. 21); para **crimes contra a honra**, mantém-se a exigência de ordem judicial; há **dever de cuidado** para conteúdos gravíssimos (terrorismo, ataques à democracia, pornografia infantil etc.). Questões de **letra da lei** continuam cobrando a redação do art. 19.
- Sanções (art. 12): advertência, **multa de até 10% do faturamento** do grupo no Brasil, suspensão temporária e proibição das atividades.

## ⚠️ Pegadinhas do bloco
1. **27001 = gestão/certificável**; **27002 = controles/guia**. 2022 = **93 controles, 4 temas**.
2. **OAuth 2.0 = autorização**; **OIDC = autenticação**.
3. **SAST = código, cedo, caixa-branca**; **DAST = execução, caixa-preta**.
4. Assinatura digital usa a **chave privada do remetente** e **não** garante confidencialidade.
5. LGPD: **encarregado não é agente de tratamento**; dados **anonimizados** estão fora da LGPD; **pseudonimizados** não.
6. Sensíveis: **sem** legítimo interesse e **sem** proteção do crédito.
7. **Órgão público não leva multa** da LGPD.
8. LAI: **20 + 10 dias**; **5–15–25 anos**; pessoais **100 anos**; **não precisa justificar** o pedido.
9. Marco Civil: conexão **1 ano**; aplicação **6 meses**.

## Questões comentadas (estilo IDCAP)

**Q1.** Segundo a LGPD, a pessoa natural ou jurídica a quem competem as decisões referentes ao tratamento de dados pessoais e aquela que realiza o tratamento em seu nome são, respectivamente:
(A) Operador e controlador. (B) **Controlador e operador.** (C) Encarregado e operador. (D) Controlador e encarregado.
✅ **B.**

**Q2.** Não constitui hipótese de tratamento de dado pessoal **sensível** prevista na LGPD:
(A) cumprimento de obrigação legal. (B) proteção da vida. (C) **legítimo interesse do controlador.** (D) tutela da saúde.
✅ **C.**

**Q3.** De acordo com a LAI, os prazos máximos de restrição de acesso das informações classificadas como reservadas e secretas são, respectivamente:
(A) 5 e 10 anos. (B) **5 e 15 anos.** (C) 10 e 25 anos. (D) 15 e 25 anos.
✅ **B.**

**Q4.** No OAuth 2.0, o componente que emite tokens de acesso após autenticar o proprietário do recurso e obter sua autorização é o:
(A) Resource Server. (B) Client. (C) **Authorization Server.** (D) Resource Owner.
✅ **C.**

**Q5.** Uma técnica analisa o código-fonte sem executá-lo, permitindo identificar vulnerabilidades nas fases iniciais; outra testa a aplicação em execução, simulando ataques externos. São, respectivamente:
(A) DAST e SAST. (B) **SAST e DAST.** (C) SCA e IAST. (D) RASP e DAST.
✅ **B.**

**Q6.** Segundo o Marco Civil da Internet, o provedor de conexão deve manter os registros de conexão pelo prazo de:
(A) 6 meses. (B) **1 ano.** (C) 2 anos. (D) 5 anos.
✅ **B.**

**Q7.** Na ABNT NBR ISO/IEC 27002:2022, os controles estão organizados em quatro temas:
(A) Físicos, lógicos, humanos e jurídicos. (B) **Organizacionais, pessoas, físicos e tecnológicos.** (C) Preventivos, detectivos, corretivos e dissuasivos. (D) Planejar, executar, verificar e agir.
✅ **B.**
