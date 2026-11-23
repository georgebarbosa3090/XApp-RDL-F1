# Módulo 15 — TI: Segurança da Informação

> Edital: *ABNT NBR ISO/IEC 27001:2024 e 27002:2022; ABNT NBR ISO/IEC 27701:2026; LGPD; OWASP Top 10:2025, desenvolvimento seguro e programação defensiva; firewall, WAF, UTM, DMZ, Proxy, NAC, antivírus e antispam; IDS e IPS; monitoramento de tráfego, sniffer; segurança de redes sem fio (EAP, WEP, WPA legados; WPA2 e WPA3); VPN, VPN-SSL, ZTNA; interpretação de pacotes; ataques e ameaças; códigos maliciosos; DoS e DDoS; criptografia simétrica e assimétrica; certificados e assinaturas digitais; hashes; controle de acesso (AAA, RBAC, MFA); TLS 1.2 e 1.3 e limitações do SSL.* Estimativa: 5–7 questões. A FCC cobrou ISO 27002 (controle de acesso), ISO 27701 (registro de tratamento), NIST SSDF, CIS Controls, vírus de boot, filtro de pacotes, WPA2 e RPO.

## 1. Normas ISO/IEC
### ABNT NBR ISO/IEC 27001 (2022 + Emenda 1:2024)
- Especifica **requisitos** para **estabelecer, implementar, manter e melhorar continuamente** um **SGSI**; é a norma **certificável**. Estrutura harmonizada: cláusulas **4 Contexto · 5 Liderança · 6 Planejamento · 7 Apoio · 8 Operação · 9 Avaliação de desempenho · 10 Melhoria** (ciclo **PDCA**).
- A **Emenda 1:2024** incluiu a consideração de **mudanças climáticas** na análise do contexto (cláusulas 4.1 e 4.2) — a "27001:2024" do edital corresponde à versão com essa emenda (confirmar edição ABNT).
- **Anexo A**: **93 controles** (mesma lista da 27002:2022). **Declaração de Aplicabilidade (SoA)**: controles necessários, justificativas de inclusão/exclusão e status.
- Processo de riscos: definir critérios → **identificar** → **analisar** → **avaliar** → **tratar** (plano de tratamento) — detalhado na **ISO/IEC 27005**.

### ABNT NBR ISO/IEC 27002:2022
- **Código de prática**: orientação para implementar os controles. **93 controles em 4 temas**: **Organizacionais (37)**, **Pessoas (8)**, **Físicos (14)**, **Tecnológicos (34)**. **11 novos**: inteligência de ameaças; SI para uso de serviços em nuvem; prontidão de TIC para continuidade; monitoramento da segurança física; gestão de configuração; exclusão de informação; mascaramento de dados; prevenção de vazamento de dados; atividades de monitoramento; filtragem da web; codificação segura.
- **Atributos** de cada controle: tipo (**preventivo, detectivo, corretivo**), propriedades de SI (C, I, D), conceitos de segurança cibernética (identificar, proteger, detectar, responder, recuperar), capacidades operacionais, domínios de segurança.
- Ex. FCC: sobre **controle de acesso**, a 27002:2022 recomenda **definir uma política específica por tema** (*topic-specific policy*) sobre controle de acesso; as regras podem ter **diferentes granularidades** e **elementos dinâmicos**; acesso físico usa crachás, biometria, portas — senha/MFA/SSO são de acesso **lógico**.

### ABNT NBR ISO/IEC 27701:2026 (adoção da ISO/IEC 27701:2025)
- **Sistema de Gestão de Informações de Privacidade (PIMS)**.
- **Edição 2019**: era **extensão** da 27001/27002 (exigia um SGSI). Ex. FCC: a subseção **7.2.8** (registros de tratamento de DP) sugeria manter um **inventário ou lista das atividades de tratamento** de dados pessoais.
- **Edição 2025 (ABNT 2026)**: passou a ser **norma independente (standalone)** — o PIMS pode ser implementado e **certificado sem depender da 27001**; segue a **estrutura harmonizada** (cláusulas 4 a 10, como as demais normas de sistema de gestão) e mantém **controles para controladores e operadores de DP** em anexos (confirmar numeração na edição ABNT). Alinha-se à LGPD/GDPR (papéis de **controlador** e **operador**).

## 2. LGPD (Lei 13.709/2018) — essencial
- **Dado pessoal** (identificado/identificável) × **sensível** (origem racial/étnica, religião, opinião política, filiação sindical/religiosa/filosófica/política, saúde, vida sexual, genético, biométrico) × **anonimizado** (fora da LGPD, salvo reversão) × pseudonimizado (continua pessoal).
- **Agentes de tratamento**: **controlador** (decide) e **operador** (trata em nome do controlador); **encarregado** = canal com titulares e ANPD (não é agente de tratamento).
- **10 princípios** (art. 6º): finalidade, adequação, necessidade, livre acesso, qualidade dos dados, transparência, segurança, prevenção, não discriminação, responsabilização e prestação de contas.
- **10 bases legais** (art. 7º): consentimento; obrigação legal/regulatória; **execução de políticas públicas** pela administração; estudos por órgão de pesquisa; contrato; **exercício regular de direitos em processo judicial**, administrativo ou arbitral; proteção da vida; tutela da saúde; legítimo interesse; proteção do crédito. Sensíveis (art. 11): **sem** legítimo interesse e proteção do crédito; inclui prevenção à fraude em autenticação.
- **Direitos do titular** (art. 18) e **revisão de decisões automatizadas** (art. 20). **Poder público** (arts. 23–32): finalidade pública, competências legais, transparência, encarregado. **Judiciário**: Resolução CNJ 363/2021 (medidas de adequação dos tribunais à LGPD).
- **Segurança e incidentes**: art. 46 (medidas técnicas e administrativas, *privacy by design*), art. 48 (comunicar à **ANPD e ao titular** incidente com risco ou dano relevante — **3 dias úteis**, Res. CD/ANPD 15/2024); **RIPD**.
- **Sanções** (art. 52): advertência, multa de até **2% do faturamento** (limite **R$ 50 milhões por infração**), multa diária, publicização, bloqueio, eliminação, suspensões, proibição — **órgãos públicos não sofrem multa**.

## 3. Segurança de aplicações
### OWASP Top 10:2025
| # | Categoria | Observação |
|---|---|---|
| A01 | **Broken Access Control** (quebra de controle de acesso) | Continua em 1º; **incorpora SSRF** |
| A02 | **Security Misconfiguration** (configuração incorreta) | Subiu (era A05) |
| A03 | **Software Supply Chain Failures** (falhas na cadeia de suprimentos de software) | **Nova**; amplia "componentes vulneráveis e desatualizados" |
| A04 | **Cryptographic Failures** | Era A02 |
| A05 | **Injection** (SQL, comandos, **XSS**…) | Era A03 |
| A06 | **Insecure Design** | Era A04 |
| A07 | **Authentication Failures** | Era "Identification and Authentication Failures" |
| A08 | **Software or Data Integrity Failures** | — |
| A09 | **Security Logging and Alerting Failures** | Ênfase em **alertas** |
| A10 | **Mishandling of Exceptional Conditions** (tratamento inadequado de condições excepcionais) | **Nova** — erros, exceções, *fail-open* |
> 2021 (anterior): A01 Broken Access Control · A02 Cryptographic Failures · A03 Injection · A04 Insecure Design · A05 Security Misconfiguration · A06 Vulnerable and Outdated Components · A07 Identification and Authentication Failures · A08 Software and Data Integrity Failures · A09 Security Logging and Monitoring Failures · A10 SSRF.

### Desenvolvimento seguro e programação defensiva
- **Princípios** (Saltzer & Schroeder / OWASP): **menor privilégio**, **defesa em profundidade**, **falhar de forma segura** (*fail-safe defaults* — negar por padrão), **minimizar a superfície de ataque**, **separação de funções**, **economia de mecanismo** (simplicidade), **mediação completa** (verificar toda requisição), *open design* (segurança não depende de segredo do projeto), **não confiar em entradas/serviços externos**, segurança por padrão (*secure by default*), corrigir a causa raiz.
- **Programação defensiva**: **validar todas as entradas** (lista de permissão — *allowlist*; tipo, tamanho, formato, faixa), **codificar saídas** conforme o contexto (HTML, JS, URL, SQL), **consultas parametrizadas**, **tratar exceções** sem expor detalhes internos (mensagens genéricas ao usuário, detalhes no log), **asserções** e verificação de pré/pós-condições, checar retornos de funções, evitar funções inseguras (`strcpy`, `gets`), **gerenciar recursos** (fechar conexões — try-with-resources), não armazenar segredos no código, registrar eventos de segurança.
- **NIST SSDF (SP 800-218, v1.1)** — 4 grupos de práticas: **PO** (*Prepare the Organization*), **PS** (*Protect the Software* — PS.1: proteger todas as formas de código contra acesso e alteração não autorizados: **repositórios protegidos, controle de versão, commits assinados, criptografia/assinatura para integridade de executáveis**), **PW** (*Produce Well-Secured Software* — validação de entradas, revisão de código, testes), **RV** (*Respond to Vulnerabilities*).
- **Testes**: **SAST** (código, caixa-branca, cedo), **DAST** (em execução, caixa-preta), **IAST**, **SCA** (dependências e SBOM), pentest, *threat modeling* (STRIDE).
- **CIS Controls v8** (18 controles; funções de segurança **Identificar, Proteger, Detectar, Responder, Recuperar**): Controle 01 — inventário de ativos corporativos: "estabelecer e manter inventário detalhado" (**identificar**), "endereçar ativos não autorizados" (**responder**), "usar ferramenta de descoberta ativa" (**detectar**).

## 4. Sistemas de proteção
| Sistema | Função |
|---|---|
| **Firewall filtro de pacotes (stateless)** | Camada **3/4**; regras por **IP de origem/destino, porta, protocolo, interface e direção** (entrada/saída); não guarda estado — ACLs |
| **Firewall stateful** (de estado) | Mantém **tabela de conexões**; permite respostas de conexões estabelecidas |
| **Firewall de aplicação / proxy** | Camada 7; inspeciona o conteúdo do protocolo |
| **NGFW** | Stateful + IPS + controle por **aplicação e usuário** + inspeção TLS |
| **WAF** | Firewall de **aplicação web** (camada 7) — protege contra **SQL injection, XSS** etc. (ModSecurity + OWASP CRS); geralmente como proxy reverso |
| **UTM** | **Tudo em um**: firewall, IPS, antivírus, antispam, filtro de conteúdo web, VPN — simplifica, mas é ponto único de falha |
| **DMZ** | **Rede de perímetro** entre a internet e a rede interna, onde ficam os servidores expostos (web, e-mail, DNS externo); arquiteturas: *screened subnet* (dois firewalls ou firewall com três interfaces), *bastion host*, *dual-homed host* |
| **Proxy** | Intermedia o acesso (forward/reverso), cache, filtro, autenticação |
| **NAC** | **Controle de admissão na rede**: autentica (802.1X) e verifica a **conformidade (postura)** do dispositivo — antivírus, patches — antes de conceder acesso; quarentena |
| **Antivírus/EDR** | Detecção por **assinatura**, **heurística**, **comportamento**, *sandbox*; **EDR/XDR** (detecção e resposta em endpoints) |
| **Antispam** | Filtros bayesianos, **RBL/DNSBL**, *greylisting*, **SPF/DKIM/DMARC**, reputação |

### IDS × IPS
| | **IDS** | **IPS** |
|---|---|---|
| Ação | **Detecta e alerta** (passivo) | **Detecta e bloqueia** (ativo) |
| Posição | Fora do fluxo (porta espelhada/SPAN, TAP) | **Em linha (*inline*)** |
| Risco | Não impede o ataque | Falso positivo **bloqueia tráfego legítimo** |
- **NIDS/NIPS** (rede) × **HIDS/HIPS** (host — logs, integridade de arquivos — OSSEC, Wazuh) × WIDS/WIPS (sem fio).
- Detecção por **assinatura** (padrões conhecidos — não detecta *zero-day*) × por **anomalia/comportamento** (desvio do normal — detecta o novo, mas gera mais **falsos positivos**). Ferramentas: **Snort**, **Suricata**, Zeek. **SIEM** correlaciona eventos; **SOAR** automatiza respostas.

## 5. Monitoramento de tráfego, sniffer e interpretação de pacotes
- **Sniffer**: captura pacotes colocando a interface em **modo promíscuo** (em Wi-Fi, *monitor mode*); em redes comutadas, usa-se **espelhamento de porta (SPAN)** ou TAP. Ferramentas: **Wireshark** (gráfico), **tcpdump** (linha de comando), tshark.
- Filtros: **de captura** (sintaxe BPF — `tcp port 443`, `host 10.0.0.5`) × **de exibição** do Wireshark (`http`, `ip.addr == 10.0.0.5`, `tcp.flags.syn == 1 && tcp.flags.ack == 0`, `dns`).
- **Interpretação**: Ethernet (MACs, EtherType 0x0800 = IPv4, 0x86DD = IPv6, 0x0806 = ARP) → IP (versão, **TTL** — 64 Linux, 128 Windows; protocolo 6 = TCP, 17 = UDP, 1 = ICMP; origem/destino) → TCP (portas, **número de sequência**, ACK, **flags**, janela) → aplicação.
  - **SYN** sem ACK = início de conexão; muitos SYN sem conclusão = **SYN flood** ou varredura; **RST** = conexão recusada/abortada (porta fechada); **FIN** = encerramento.
  - Protocolos em **texto claro** (HTTP, FTP, Telnet, POP3, SMTP sem TLS) expõem **senhas** ao sniffer — use TLS/SSH.
- **Tráfego de serviços e programas**: identificar por portas/protocolos (DNS 53, HTTPS 443, SMB 445, RDP 3389), volume e padrão (NetFlow/IPFIX); tráfego anômalo (exfiltração por DNS, *beaconing* de botnet).

## 6. Segurança de redes sem fio
| Protocolo | Criptografia | Situação |
|---|---|---|
| **WEP** | **RC4** com **IV de 24 bits** (reuso de IV), CRC-32 | **Quebrado** — legado |
| **WPA** | **TKIP** (ainda RC4, chave por pacote) + MIC (Michael) | Legado (transição) |
| **WPA2** (802.11i) | **AES-CCMP** (cifragem AES em modo **CTR** + integridade **CBC-MAC**) | Padrão por anos; vulnerável ao **KRACK** (2017, corrigido por patches); modos **Personal (PSK)** e **Enterprise (802.1X/EAP + RADIUS)** |
| **WPA3** | **SAE** (*Simultaneous Authentication of Equals* — "Dragonfly") no lugar do PSK: resistente a **ataque de dicionário offline** e com **sigilo direto (forward secrecy)**; **PMF obrigatório** (quadros de gerenciamento protegidos); **Enterprise 192 bits** (GCMP-256); **OWE / Enhanced Open** (criptografia em redes abertas) | Recomendado |
- **EAP**: *framework* de autenticação usado no 802.1X (EAP-TLS, PEAP, EAP-TTLS); **LEAP** (Cisco) é legado e inseguro.
- **Ameaças sem fio**: ***evil twin*** (AP falso com o mesmo SSID), *rogue AP*, **desautenticação** (*deauth*, mitigada por PMF), *war driving*, quebra de PSK fraca (captura do *handshake* de 4 vias), **WPS** (PIN vulnerável a força bruta — desabilitar), *jamming*, *bluejacking/bluesnarfing* (Bluetooth).

## 7. VPN, VPN-SSL e ZTNA
- **VPN**: túnel **criptografado** sobre rede pública. **Site a site** (IPsec entre gateways) × **acesso remoto** (cliente → rede).
- **IPsec VPN**: camada 3; AH/ESP, IKE; exige cliente/configuração; dá acesso **à rede**.
- **VPN-SSL/TLS**: sobre **HTTPS (443)** — atravessa firewalls/NAT facilmente; modos **portal (*clientless*, pelo navegador)** e **túnel** (cliente leve, acesso a mais protocolos). Ex.: OpenVPN, AnyConnect, GlobalProtect. **WireGuard**: VPN moderna, enxuta, sobre UDP.
- **ZTNA (Zero Trust Network Access)**: aplica **Zero Trust** ("nunca confie, sempre verifique"): o usuário recebe acesso **apenas a aplicações específicas**, **não à rede inteira**, após verificação contínua de **identidade, dispositivo e contexto**; aplicações ficam **invisíveis** (não expostas) a quem não está autorizado (*software-defined perimeter*); reduz o **movimento lateral**. Compõe o **SASE/SSE** (com SWG, CASB, FWaaS).

## 8. Ataques, ameaças e códigos maliciosos
### Negação de serviço
| Tipo | Exemplos | Mitigação |
|---|---|---|
| **Volumétrico** | UDP flood, ICMP flood, **amplificação/reflexão** (DNS, NTP, memcached, SSDP — *IP spoofing* da vítima) | *Scrubbing*/CDN, *anti-DDoS* do provedor, *rate limiting*, BCP 38 (anti-spoofing) |
| **De protocolo** | **SYN flood** (esgota a tabela de conexões semiabertas), Ping of Death, Smurf | **SYN cookies**, firewalls stateful |
| **De aplicação (camada 7)** | HTTP flood, **Slowloris** (conexões lentas mantidas abertas) | WAF, limites de conexão/tempo |
- **DoS** = uma origem; **DDoS** = muitas origens (geralmente **botnet**).

### Outros ataques
- **MITM**: ARP spoofing/poisoning, **DNS spoofing/cache poisoning**, SSL stripping, evil twin. **Sequestro de sessão**, *replay*.
- **Engenharia social**: **phishing**, *spear phishing* (direcionado), *whaling* (executivos), *smishing* (SMS), *vishing* (voz), *pretexting*, *baiting*, *tailgating*.
- **Senhas**: força bruta, **dicionário**, *credential stuffing* (senhas vazadas), *password spraying* (uma senha comum em muitas contas), *rainbow tables* (derrotadas por **salt**).
- Varreduras (**Nmap**), *zero-day*, **APT**, ataques à cadeia de suprimentos, injeções (SQLi, XSS, comandos), **SSRF**, **CSRF**.

### Códigos maliciosos
| Malware | Característica |
|---|---|
| **Vírus** | Precisa de **hospedeiro** e de execução para se propagar; **vírus de boot** infecta o **registro mestre de inicialização (MBR)** e setores de boot de mídias removíveis, afetando a inicialização do SO (ex. FCC: problema após abrir anexo de e-mail → **vírus**) |
| **Worm** | Propaga-se **sozinho** pela rede, explorando vulnerabilidades |
| **Cavalo de Troia** | Aparenta ser legítimo e executa funções ocultas |
| **Ransomware** | **Criptografa** dados e exige resgate (dupla extorsão: também ameaça vazar) |
| **Rootkit / bootkit** | Esconde a presença e mantém acesso privilegiado (bootkit atua na inicialização) |
| **Backdoor** | Acesso remoto oculto |
| **Spyware / keylogger / screenlogger** | Espionagem; captura de teclas / telas |
| **Bot / botnet** | Máquinas controladas por **C2** (comando e controle) — DDoS, spam |
| **Adware** | Propaganda indesejada |
| **Fileless** | Reside na memória e usa ferramentas legítimas (PowerShell, WMI) |
| **Cryptojacking** | Usa recursos da vítima para minerar criptomoedas |

## 9. Criptografia, hashes, assinaturas e certificados
| | **Simétrica** | **Assimétrica** |
|---|---|---|
| Chaves | **Uma** chave secreta compartilhada | **Par**: **pública** e **privada** |
| Desempenho | **Rápida** (grandes volumes) | Lenta |
| Problema | **Distribuição** da chave; n(n−1)/2 chaves para n pessoas | Desempenho; autenticidade da chave pública (→ certificados) |
| Algoritmos | **AES** (128/192/256 — bloco de 128 bits), ChaCha20 (fluxo), 3DES (legado), DES (quebrado), RC4 (quebrado) | **RSA**, **ECC** (chaves menores com segurança equivalente), **Diffie-Hellman/ECDH** (**troca de chaves**), DSA/ECDSA, EdDSA (assinatura) |
- Modos de operação de bloco: **ECB** (inseguro — padrões visíveis), CBC (exige IV aleatório), CTR, **GCM** (**AEAD** — confidencialidade + integridade).
- **Hash**: função **unidirecional**, saída de **tamanho fixo**, **resistente a colisões**, efeito avalanche — **SHA-256/SHA-512**, **SHA-3**; **MD5** e **SHA-1** são inseguros (colisões). **HMAC** (hash + chave → integridade + autenticidade). Senhas: **bcrypt, scrypt, Argon2, PBKDF2** (lentos, com **salt**).
- **Assinatura digital**: calcula-se o **hash** do documento e cifra-se com a **chave privada do signatário**; verifica-se com a **chave pública** → **autenticidade, integridade e não repúdio** (**não** confidencialidade). Confidencialidade: cifrar com a **chave pública do destinatário**. **Envelope digital**: chave simétrica de sessão cifrada com a pública do destinatário.
- **Certificado digital (X.509)**: vincula uma **chave pública** a uma identidade, **assinado por uma Autoridade Certificadora (AC)**. Campos: versão, número de série, emissor, **validade**, titular (*subject*), chave pública, extensões (uso da chave, SAN), assinatura da AC.
- **PKI/ICP**: AC raiz → ACs intermediárias → certificados finais (**cadeia de confiança**); **AR** (Autoridade de Registro — valida a identidade). **ICP-Brasil**: AC Raiz operada pelo **ITI**; tipos **A1** (gerado e armazenado em **software**, validade de **1 ano**) e **A3** (em **hardware** — token, cartão inteligente ou HSM/nuvem —, validade maior, até 5 anos), além de A2/A4 e de sigilo (S). **Revogação**: **LCR/CRL** (lista publicada) e **OCSP** (consulta online).

## 10. Controle de acesso
- **AAA**: **autenticação** (quem é), **autorização** (o que pode), **auditoria/contabilização** (o que fez). Protocolos: **RADIUS** (UDP 1812/1813; cifra só a senha), **TACACS+** (TCP 49; cifra todo o pacote; separa AAA — comum para administrar equipamentos de rede), Kerberos, LDAP.
- **Fatores**: o que você **sabe** (senha), **tem** (token, celular, certificado em cartão), **é** (biometria) — **MFA** = **fatores de categorias diferentes** (senha + PIN não é MFA). OTP: **TOTP** (baseado em tempo) e HOTP (contador); **FIDO2/WebAuthn** (passkeys — resistente a phishing).
- Modelos: **DAC** (o dono decide — ACLs), **MAC** (rótulos e níveis definidos centralmente), **RBAC** (permissões atribuídas a **papéis/funções**; usuários recebem papéis — facilita gestão e **segregação de funções**), **ABAC** (atributos do usuário, recurso e contexto).
- Princípios: **menor privilégio**, **necessidade de conhecer**, **segregação de funções**, revisão periódica, gestão de acessos privilegiados (**PAM**).

## 11. TLS 1.2, TLS 1.3 e as limitações do SSL
| | **TLS 1.2** (2008, RFC 5246) | **TLS 1.3** (2018, RFC 8446) |
|---|---|---|
| Handshake | **2-RTT** | **1-RTT**; retomada **0-RTT** (com risco de *replay*) |
| Troca de chaves | RSA estático ou (EC)DHE | **Somente (EC)DHE** → **sigilo direto (PFS) obrigatório**; **removida a troca por RSA** |
| Cifras | Muitas suítes (inclusive CBC, RC4 em versões antigas) | Só **AEAD**: **AES-GCM**, **ChaCha20-Poly1305** (e AES-CCM) — **5 suítes** |
| Removidos | — | **RC4, 3DES, CBC, MD5, SHA-1**, compressão, renegociação, DH estático |
| Privacidade | Certificado do servidor trafega em claro | Mensagens do handshake após o *ServerHello* são **cifradas** (inclusive o certificado) |
- **SSL 2.0 e 3.0** estão **proibidos/obsoletos**: SSL 3.0 vulnerável ao **POODLE** (2014); SSLv2 ao **DROWN**. **TLS 1.0 e 1.1** foram **descontinuados** (RFC 8996, 2021) — ataques **BEAST** (CBC no TLS 1.0) e **CRIME** (compressão). **Heartbleed** (2014) foi uma falha de **implementação** (OpenSSL), não do protocolo.
- Boas práticas: **TLS 1.2 + 1.3 apenas**, suítes AEAD com ECDHE, **HSTS**, certificados válidos com cadeia completa, OCSP stapling, **mTLS** para comunicação entre serviços.

## ⚠️ Pegadinhas
1. 27001 = **requisitos/certificável**; 27002 = **controles** (93, em 4 temas); 27701:2025 = **PIMS standalone**.
2. OWASP **2025**: A02 **Misconfiguration**, A03 **Supply Chain** (nova), A10 **Exceptional Conditions** (nova); SSRF foi para A01.
3. Filtro de pacotes = **camada 3**, IP/porta/interface/direção, **sem estado**; WAF = camada 7.
4. IDS **detecta**; IPS **bloqueia** (inline). Assinatura não pega zero-day; anomalia gera falso positivo.
5. WEP = RC4/IV 24 bits; WPA = TKIP; **WPA2 = AES-CCMP + CBC-MAC**; **WPA3 = SAE + PMF**.
6. ZTNA = acesso **por aplicação**, nunca à rede toda.
7. Assinatura digital: **privada do signatário**; confidencialidade: **pública do destinatário**.
8. TLS 1.3: **1-RTT, PFS obrigatório, só AEAD**, sem RSA estático; SSL 3.0 = POODLE.
9. Vírus de **boot** → MBR; worm se propaga sozinho.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Um firewall que opera na camada de rede, controla o acesso com base nos endereços IP de origem e destino, portas, na interface atravessada e na direção do tráfego, sem manter informações sobre o estado das conexões, é do tipo:
(A) UTM. (B) WAF. (C) stateful. (D) **filtro de pacotes.** (E) proxy de aplicação.
✅ **D.**

**Q2.** Protocolo de segurança sem fio que substitui a chave pré-compartilhada pelo SAE, oferecendo resistência a ataques de dicionário offline e sigilo direto:
(A) WEP. (B) WPA-TKIP. (C) WPA2-PSK. (D) **WPA3.** (E) EAP-MD5.
✅ **D.**

**Q3.** No TLS 1.3, em comparação com o TLS 1.2:
(A) a troca de chaves por RSA estático tornou-se obrigatória. (B) o handshake completo passou a exigir 3 RTTs. (C) **todas as suítes de cifra usam criptografia autenticada (AEAD) e o sigilo direto é obrigatório.** (D) o algoritmo RC4 passou a ser o padrão. (E) a compressão foi tornada obrigatória.
✅ **C.**

**Q4.** Abordagem que concede ao usuário remoto acesso apenas a aplicações específicas, após verificar continuamente identidade, dispositivo e contexto, sem colocá-lo na rede interna como um todo:
(A) VPN IPsec site a site. (B) DMZ. (C) **ZTNA.** (D) NAT. (E) VLAN.
✅ **C.**

**Q5.** Na OWASP Top 10:2025, a categoria que ocupa a primeira posição é:
(A) Injection. (B) Security Misconfiguration. (C) Software Supply Chain Failures. (D) **Broken Access Control.** (E) Cryptographic Failures.
✅ **D.**

**Q6.** Para garantir autenticidade, integridade e não repúdio de um documento eletrônico, o remetente deve:
(A) cifrar o documento com a chave pública do destinatário. (B) **gerar o hash do documento e cifrá-lo com a sua chave privada.** (C) cifrar o documento com uma chave simétrica e enviá-la por e-mail. (D) calcular o MD5 e enviá-lo junto. (E) compactar o documento com senha.
✅ **B.**
