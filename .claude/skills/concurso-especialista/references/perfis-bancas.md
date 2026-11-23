# Perfis de cobrança das bancas

> Heurísticas. Confirme sempre com provas recentes da própria banca.

## IDCAP — análise real (PPSA 2025, Analista de TI: Desenvolvimento, Infraestrutura, Segurança; 180 questões lidas)
**Formato**: múltipla escolha com **4 alternativas (A–D)**, uma correta. 60 questões, 4h30 (PPSA). Na SEAD-AP 2026: 50 questões + discursiva.

**Estilo de enunciado (≈80% das questões de TI)**: parágrafo longo que *descreve* dois ou três conceitos e termina com
"*Esses X são conhecidos, respectivamente, como:*". Ou seja, a banca cobra **reconhecer o nome pela definição** e **a ordem**.
- Estratégia: identifique cada definição, nomeie-a mentalmente, depois procure a alternativa com a **ordem certa**. Distratores costumam trocar a ordem ou um dos termos.

**Outros formatos que aparecem**:
- Rastreio de algoritmo em pseudocódigo (passagem por valor × referência, `enquanto`/`para`, valores booleanos).
- Saída de código JavaScript / HTML+CSS (cores de fundo, HSL).
- SQL (`SELECT DISTINCT ... WHERE`), trigger, arquitetura ANSI/SPARC (interno, conceitual/lógico, externo).
- Redes: CIDR/sub-rede (último endereço, máscara /26), faixas privadas RFC 1918, IPv6 (128 bits, 8 blocos de 16 bits, 4 hex, ":"), portas (DNS 53, HTTPS 443, SMTP TLS 587), T-568A, OSI (enlace = VLAN/switch L2), SNMP (GET/SET, agente, MIB), SIP, QoS (jitter, perda), Wi-Fi 5 (802.11ac), Wi-Fi 6E (6 GHz, 9,6 Gb/s, OFDMA), USB 2.0 = 480 Mbps / 3.2 = 20 Gbps.
- Segurança: CID (confidencialidade), malwares (keylogger, rootkit), sniffer/Wireshark, IDS/IPS (NIDS, HIDS, WIPS), DLP, CASB, SOAR, UEBA, mTLS, IPSec, SNMPv3, AES × RSA, certificado A1 (1 ano), controles gerencial/operacional/técnico, segurança física × lógica, ataques (phishing, força bruta, DoS/DDoS).
- Normas/frameworks: ISO 27001 (gestão) × 27002 (controles); ISO 27005 (tratamento: modificar, reter, evitar, compartilhar); ISO 22301 (PDCA, SGCN); ISO 31000; NIST CSF (Identificar, Proteger, Detectar, Responder, Recuperar + Governar no 2.0); NIST SP 800-61 (contenção, erradicação e recuperação); COBIT 2019 (EDM, APO, BAI, DSS, MEA); ITIL 4 (34 práticas: 14 gerais, 17 de serviço, 3 técnicas).
- Engenharia de software: testes unitário × integração, TDD (Red-Green-Refactor), BDD (Descoberta, Definição/Formulação, Formalização/Automação, Entrega), MVC, SOA (contrato do serviço), microsserviços (domínio × integração), EDA pub/sub, REST verbs, gRPC × Webhook, prototipação, MVP Concierge, Design Thinking (storyboard), ISO 25010 (usabilidade, eficiência), cascata, Scrum × Kanban, Docker, Git, GitLab CI (`.gitlab-ci.yml`, `stages`, `artifacts`, `paths`), Kafka (brokers, ZooKeeper).
- Dados: modelagem conceitual → lógica → física, DER (N:N), OLAP (MOLAP, ROLAP, HOLAP, DOLAP), Data Mining × Data Warehouse, NoSQL (CouchDB, Couchbase, MongoDB).
- Legislação: LGPD (princípios: livre acesso, segurança…; ANPD; anonimização), LAI (reservado 5 anos, secreto 15, ultrassecreto 25 prorrogável uma vez pela CMRI).
- Informática de usuário: atalhos do Microsoft 365. ⚠️ A banca já usou atalhos da versão em inglês (Ctrl+A/Ctrl+B) — leia o enunciado e as alternativas com atenção.

**Português (IDCAP)**: texto jornalístico; antônimo/sinônimo em contexto, pontuação sem alterar sentido, conjugação (futuro do pretérito, imperfeito do subjuntivo), morfologia de locuções ("à medida que" = locução conjuntiva), conotação × denotação, transitividade verbal, colocação pronominal, concordância (sujeito do verbo).

## FGV
- Enunciados longos, casos práticos, alternativas parecidas (5). Lei seca com detalhes.
- TI: cenário → tecnologia/prática adequada; SQL prático; IN SGD 94/2022; segurança; IA.

## Cebraspe
- Certo/Errado; uma errada anula uma certa. Palavra que invalida o item.
- TI: profundidade conceitual, normas ISO, redes, governança.

## FCC
- Literalidade de normas e leis. Código e SQL. ITIL/COBIT literal.

## Vunesp
- Conteúdo tradicional; informática de usuário (atalhos, menus) muito cobrada.

## Cesgranrio / IBFC / AOCP / Quadrix
- Cesgranrio: conceitual + cálculo. IBFC/AOCP: conceitual, listas. Quadrix: C/E e lei seca.

## Pegadinhas universais
1. Troca de número (prazos, quantidades, percentuais).
2. Inversão de pares (controlador × operador; IaaS × PaaS; TCP × UDP; NIDS × HIDS).
3. Ordem trocada no "respectivamente".
4. Versão desatualizada (ITIL v3 × 4; ISO 27002:2013 × 2022; Lei 8.666 × 14.133; OWASP 2017 × 2021 × 2025).
5. Extrapolação ("sempre", "somente", "em nenhuma hipótese").
6. Exceções (dispensa × inexigibilidade; dados anonimizados fora da LGPD).
