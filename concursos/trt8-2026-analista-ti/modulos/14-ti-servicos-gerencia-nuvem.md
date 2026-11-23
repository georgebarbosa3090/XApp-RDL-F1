# Módulo 14 — TI: Serviços de Rede, Servidores de Aplicação, Gerência, Monitoramento e Nuvem

> Edital: *serviços (e-mail, DNS, DHCP, Web Proxy); servidores de aplicação (JBoss EAP/WildFly) e web (Apache HTTP Server e IIS); desempenho, usuários, logs; SNMP, MIBs, QoS, métricas e avaliação de desempenho; Zabbix, Elasticsearch, Logstash, Kibana, Grafana, Prometheus, Fluentd; nuvem (arquitetura, pública e privada, IaaS/PaaS/SaaS, contêineres, Kubernetes, Docker, Serverless Framework).* Estimativa: 3–5 questões. A FCC cobrou **WildFly `add-user.sh`**, **DiffServ EF**, **HSRP**, **EIGRP**, **NIST SP 800-145** e nuvem pública.

## 1. Serviços de rede
### Correio eletrônico
- Componentes: **MUA** (cliente — Outlook, Thunderbird), **MTA** (transferência entre servidores — Postfix, Exchange; **SMTP**), **MDA** (entrega na caixa), **MSA** (submissão — porta **587**). Leitura: **POP3** / **IMAP**.
- Fluxo: MUA → (SMTP 587) → MSA/MTA → consulta **registro MX** do destino → (SMTP 25) → MTA destino → MDA → caixa → (IMAP/POP3) → MUA.
- **Autenticação de e-mail**: **SPF** (registro TXT lista **IPs autorizados** a enviar pelo domínio), **DKIM** (**assinatura** digital no cabeçalho, chave pública no DNS), **DMARC** (**política** — none/quarantine/reject — e relatórios, alinhando SPF e DKIM). Antispam: RBL/DNSBL, greylisting, filtros bayesianos.

### DNS e DHCP (serviço)
- DNS: servidor **autoritativo** (zonas primária/secundária, transferência de zona restrita) × **recursivo/cache** (restringir a recursão à rede interna — evita amplificação); **BIND** (`named.conf`), Windows DNS integrado ao AD; *split-horizon*; DNSSEC.
- DHCP: **escopo** (faixa), **exclusões**, **reservas** (IP fixo por MAC), **tempo de concessão**, opções (003 roteador, 006 DNS, 015 domínio), **relay agent**, failover; ataque *rogue DHCP* → **DHCP snooping** no switch.

### Web Proxy
| Tipo | Posição | Função |
|---|---|---|
| **Proxy direto (forward)** | Na frente dos **clientes** | Controle de acesso/filtro de conteúdo, **cache**, autenticação de usuários, registro de navegação (ex.: **Squid**, porta padrão **3128**) |
| **Proxy reverso** | Na frente dos **servidores** | Balanceamento de carga, **terminação TLS**, cache, WAF, ocultar a topologia interna (Nginx, HAProxy, Apache `mod_proxy`) |
| Transparente | Intercepta sem configuração no cliente | — |
- Configuração automática dos navegadores: arquivo **PAC** e protocolo **WPAD**.

## 2. Servidores de aplicação e web
### JBoss EAP / WildFly (Red Hat)
- **Servidor de aplicação Jakarta EE** (antigo Java EE). **WildFly** é o projeto comunitário; **JBoss EAP** é a versão com suporte comercial da Red Hat.
- **Modos**: **standalone** (instância independente — `bin/standalone.sh`, configuração **`standalone/configuration/standalone.xml`**) × **domain** (gerência centralizada de várias instâncias — **domain controller** e **host controllers**; `domain.xml`, `host.xml`; `bin/domain.sh`).
- **Perfis** de configuração: `default`, `ha` (cluster), `full` (com mensageria JMS), `full-ha` (`standalone-full-ha.xml`).
- **Subsistemas**: **Undertow** (web/servlets), **datasources** (pools JDBC), **Elytron** (segurança), **messaging-activemq** (JMS), **Infinispan** (cache), logging, transactions.
- **Usuários de gerenciamento**: a segurança da interface de gerenciamento vem **ativada**; antes de usar o console web ou a CLI remotamente, crie um usuário com o script **`add-user.sh`** (Windows: `add-user.bat`) **no diretório `bin`** — escolhe-se *Management User* (ManagementRealm) ou *Application User* (ApplicationRealm).
- **Portas padrão**: **8080** (HTTP das aplicações), **8443** (HTTPS), **9990** (console de gerenciamento web e HTTP management), 9993 (HTTPS de gerência).
- **Deploy**: copiar o **`.war`/`.ear`** para **`standalone/deployments`** (*deployment scanner* gera marcadores `.deployed`, `.failed`) ou via **CLI** `bin/jboss-cli.sh --connect` → `deploy app.war`, ou pelo console.
- Bind de interface: `-b 0.0.0.0` (público) e `-bmanagement` (gerência). Logs em `standalone/log/server.log`. *JBoss Modules* (classloading modular).

### Apache HTTP Server (httpd)
- Configuração principal: **RHEL/Oracle Linux: `/etc/httpd/conf/httpd.conf`** (+ `/etc/httpd/conf.d/*.conf`); **Debian/Ubuntu: `/etc/apache2/apache2.conf`** (+ `sites-available`/`sites-enabled`, `a2ensite`, `a2enmod`).
- Diretivas: `Listen 80`, `ServerName`, **`DocumentRoot`** (padrão `/var/www/html`), `<Directory>`, **`<VirtualHost *:80>`** (hosts virtuais **por nome** ou por IP), `AllowOverride` (habilita `.htaccess`), `Require all granted/denied`, `ErrorLog`, `CustomLog`, `LogLevel`.
- **Módulos**: `mod_ssl` (HTTPS), `mod_rewrite` (reescrita de URL), **`mod_proxy`** (`ProxyPass` / `ProxyPassReverse` — proxy reverso para Tomcat/WildFly), `mod_headers`, `mod_security` (WAF).
- **MPMs**: **prefork** (processos, sem threads), **worker** (processos + threads), **event** (padrão moderno — threads com tratamento eficiente de *keep-alive*).
- Logs (RHEL): `/var/log/httpd/access_log` e `error_log`. Testar configuração: **`apachectl configtest`** (ou `httpd -t`); aplicar: `systemctl reload httpd`.

### IIS (Internet Information Services — Windows)
- Gerenciado pelo **IIS Manager (`inetmgr`)**, **`appcmd.exe`** e PowerShell (módulo `WebAdministration`/`IISAdministration`).
- **Site** com **bindings** (protocolo + **IP** + **porta** + **nome de host**); site padrão em **`C:\inetpub\wwwroot`**.
- **Pools de aplicativos (application pools)**: **isolam** aplicações em processos de trabalho (**`w3wp.exe`**), com **identidade** própria (ApplicationPoolIdentity), versão do .NET CLR, pipeline (integrado/clássico) e **reciclagem** periódica.
- Configuração por aplicação em **`web.config`** (XML); global em `applicationHost.config`. Logs em **`%SystemDrive%\inetpub\logs\LogFiles`** (formato **W3C**). Extensões: URL Rewrite, **ARR** (proxy reverso/balanceamento). Autenticação: anônima, básica, **Windows** (Kerberos/NTLM).

### Análise de desempenho, usuários e logs
- Métricas de servidor: CPU, memória, disco (IOPS, latência), rede, threads/conexões, tempo de resposta, taxa de erros; ferramentas `top`, `vmstat`, `iostat`, `sar`, Monitor de Desempenho (perfmon) no Windows; **JVM** (heap, GC — `jstat`, `jconsole`, VisualVM).
- Logs: centralizar (syslog/**rsyslog**, journald, ELK/EFK), rotacionar (`logrotate`), sincronizar relógio (**NTP**), níveis (DEBUG, INFO, WARN, ERROR), não registrar dados sensíveis (LGPD).

## 3. Gerência de redes
### SNMP
| Versão | Segurança | Destaques |
|---|---|---|
| v1 | *Community string* em texto claro | Get, GetNext, Set, Trap |
| **v2c** | Community (texto claro) | Acrescenta **GetBulk** e **Inform** (trap com confirmação) |
| **v3** | **USM**: autenticação (HMAC-SHA) e **privacidade/criptografia** (AES); **VACM** (controle de acesso por visões) | Recomendado |
- Arquitetura: **gerente** (NMS — consulta e recebe traps) e **agente** (no dispositivo — responde e envia traps). **MIB**: base de informações hierárquica de objetos gerenciados, identificados por **OID** (árvore — ex.: `1.3.6.1.2.1` = mib-2; `1.3.6.1.4.1` = empresas privadas); **SMI** define a estrutura.
- Portas: **UDP 161** (agente recebe consultas) e **UDP 162** (gerente recebe traps).
- Operações: **Get** (ler), **GetNext**, **GetBulk**, **Set** (alterar), **Trap** (notificação assíncrona do agente), **Inform**, Response.
- Áreas da gerência (modelo **FCAPS** — ISO): **F**alhas, **C**onfiguração, **C**ontabilização (*Accounting*), **D**esempenho (*Performance*), **S**egurança.

### Tipos e níveis de serviço e QoS
- **SLA** (acordo de nível de serviço), **SLO**, **SLI**; disponibilidade (99,9% ≈ 8,76 h/ano de indisponibilidade).
- **Melhor esforço** (*best effort*) × **IntServ** (reserva de recursos fim a fim por fluxo, com **RSVP** — pouco escalável) × **DiffServ** (marcação por **classe** no campo **DSCP** de 6 bits do cabeçalho IP; cada roteador aplica um **PHB** — *Per-Hop Behavior* — escalável).
| PHB (DiffServ) | Uso |
|---|---|
| **EF — Expedited Forwarding** (DSCP **46**) | **Baixa perda, baixa latência, baixo jitter e banda garantida** — serviço *premium* fim a fim (**voz**) |
| **AF — Assured Forwarding** (AFxy: 4 classes × 3 níveis de descarte) | Entrega assegurada com prioridades de descarte (dados críticos) |
| **BE / Default** (DSCP 0) | Melhor esforço |
| CS (Class Selector) | Compatibilidade com IP Precedence |
- Mecanismos: **classificação e marcação**, **policiamento** (*policing* — descarta/remarca o excesso) × **modelagem** (*shaping* — enfileira e suaviza), **filas** (FIFO, **PQ** — prioridade estrita, WFQ, **CBWFQ** — banda por classe, **LLQ** — CBWFQ + fila de prioridade para voz), prevenção de congestionamento (**WRED**).

### Métricas e métodos de avaliação de desempenho
- **Métricas**: **vazão (*throughput*)**, **largura de banda**, **latência/atraso** (propagação + transmissão + processamento + fila), **jitter** (variação do atraso), **perda de pacotes**, **utilização**, **disponibilidade**, RTT, MOS (qualidade de voz).
- **Métodos de avaliação**: **medição/monitoramento** (sistema real — ativo: ping, traceroute, **iperf**; passivo: SNMP, NetFlow/sFlow/IPFIX, captura com Wireshark), **simulação** (modelos computacionais — NS-3), **modelagem analítica** (**teoria das filas** — M/M/1; Lei de Little), *benchmarks*.

### Redundância de gateway e roteamento (cobrados pela FCC)
- **HSRP** (Cisco) / **VRRP** (padrão aberto) / GLBP: redundância de **primeiro salto** — roteadores compartilham um **IP virtual** usado como gateway pelos hosts. No HSRP, o de **maior prioridade** (padrão 100) torna-se **ativo** e outro fica **standby**; com **preempção** habilitada, o roteador de maior prioridade **retoma o papel de ativo** ao voltar (força nova eleição após reinício/falha); sem preempção, o ativo atual permanece.
- **EIGRP** (Cisco): vetor de distância avançado, algoritmo **DUAL**; métrica composta por **K-values**: K1 = **banda**, K2 = carga, K3 = **atraso**, K4/K5 = confiabilidade. **Padrão: K1 = K3 = 1, demais 0** → métrica usa **banda e atraso**.
- **OSPF** (estado de enlace, Dijkstra, áreas — área 0 backbone, custo baseado na banda), **BGP** (vetor de caminho, entre sistemas autônomos — rota da internet), RIP (vetor de distância, métrica = saltos, máximo 15).

## 4. Ferramentas de monitoramento e log
| Ferramenta | Papel | Destaques |
|---|---|---|
| **Zabbix** | Monitoramento de infraestrutura (servidores, rede, VMs, aplicações) | **Agente Zabbix**, SNMP, IPMI, JMX; **itens**, **triggers** (condições de problema), ações/alertas, **templates**, **descoberta automática (LLD)**, **proxy Zabbix** (coleta distribuída); dados em MySQL/PostgreSQL; porta do agente **10050** (servidor **10051**) |
| **Prometheus** | Métricas de **séries temporais** (nuvem nativa, Kubernetes) | Modelo **pull** (*scraping* de `/metrics`), **PromQL**, **exporters** (node_exporter), **Alertmanager**, TSDB local; porta **9090**; *Pushgateway* para jobs curtos |
| **Grafana** | **Visualização** | Dashboards sobre várias fontes (Prometheus, Zabbix, Elasticsearch, Loki, InfluxDB, SQL); alertas; porta **3000**; não armazena métricas |
| **Elasticsearch** | Motor de **busca e análise** distribuído (baseado em **Lucene**) | **Índices**, documentos JSON, *shards* e réplicas, API REST (porta **9200**), busca *full-text* |
| **Logstash** | **Pipeline de processamento** de logs | **input → filter (ex.: `grok`, `mutate`, `date`) → output** |
| **Kibana** | **Visualização** dos dados do Elasticsearch | Discover, dashboards, Lens; porta **5601** |
| **Fluentd** | **Coletor/agregador unificado de logs** (projeto CNCF) | Plugins de entrada e saída, *tags*, buffer; muito usado em Kubernetes (**pilha EFK**: Elasticsearch + **Fluentd** + Kibana); **Fluent Bit** = versão leve |
| Beats (Filebeat, Metricbeat) | Agentes leves de coleta | Enviam para Logstash/Elasticsearch |
- **Pilha ELK** = Elasticsearch + Logstash + Kibana (+ Beats = *Elastic Stack*). **Observabilidade** = métricas + logs + traces (OpenTelemetry, Jaeger).

## 5. Computação em nuvem
### NIST SP 800-145 — 5 características essenciais, 3 modelos de serviço, 4 de implantação
| Características essenciais | Modelos de serviço | Modelos de implantação |
|---|---|---|
| **Autoatendimento sob demanda** (*on-demand self-service*) | **SaaS** — usa a aplicação do provedor | **Nuvem privada** — uso exclusivo de uma organização |
| **Amplo acesso à rede** (*broad network access*) | **PaaS** — implanta suas aplicações na plataforma do provedor | **Nuvem comunitária** — compartilhada por organizações com interesses comuns |
| **Pool de recursos** (*resource pooling*, multilocatário) | **IaaS** — provisiona processamento, armazenamento, rede; gerencia SO e aplicações | **Nuvem pública** — aberta ao público geral; pertence ao provedor |
| **Elasticidade rápida** (*rapid elasticity*) | | **Nuvem híbrida** — composição de duas ou mais (privada + pública), com portabilidade |
| **Serviço medido** (*measured service*) | | |
> Ex. FCC: "recursos pertencem e são operados por um **único provedor**, **compartilhados por vários locatários** pela internet, com **custo reduzido, fácil dimensionamento e baixa manutenção**" → **nuvem pública**.

- Arquitetura em nuvem: **regiões** e **zonas de disponibilidade**, alta disponibilidade e tolerância a falhas, **escalabilidade horizontal** (*auto scaling*), balanceadores, armazenamento de **objetos** (S3), **blocos** e **arquivos**, VPC/redes virtuais, **IAM**, **modelo de responsabilidade compartilhada**, **FinOps**; *well-architected* (excelência operacional, segurança, confiabilidade, eficiência de desempenho, otimização de custos, sustentabilidade).
- **Implantação e operação de aplicações em nuvem e contêineres**: imagens imutáveis, **Kubernetes** gerenciado (EKS, AKS, GKE) ou on-premises (Rancher/RKE2, OpenShift), **12-factor app** (configuração por variáveis de ambiente, processos *stateless*, logs como fluxo, paridade entre ambientes), *blue-green* e *canary deployments*, IaC (Terraform).
- **Serverless / FaaS**: funções executadas **sob demanda**, cobrança **por execução**, escala automática (até zero), sem gerenciar servidores; desvantagens: **cold start**, limites de tempo de execução, *vendor lock-in*. Exemplos: AWS Lambda, Azure Functions, Google Cloud Functions.
- **Serverless Framework**: ferramenta **open source (CLI)** para desenvolver e implantar aplicações serverless em vários provedores a partir do arquivo **`serverless.yml`** (define `service`, `provider` — ex.: aws, runtime, região —, `functions` com seus `handler`s e `events` — http, schedule, filas); comandos **`serverless deploy`** (`sls deploy`), `sls invoke`, `sls logs`, `sls remove`; gera a infraestrutura (na AWS, via CloudFormation).

## ⚠️ Pegadinhas
1. WildFly: **`bin/add-user.sh`**; console de gerência **9990**; deploy em **`standalone/deployments`**.
2. Apache RHEL: **`/etc/httpd/conf/httpd.conf`**; Debian: `/etc/apache2/apache2.conf`; teste com `apachectl configtest`.
3. IIS: **application pool** isola; `w3wp.exe`; `web.config`.
4. SNMP: agente **161**, traps **162**; **v3** tem autenticação e criptografia; GetBulk surgiu na **v2c**.
5. DiffServ **EF** = voz/premium (baixa perda, latência e jitter); AF = assegurado; DSCP tem **6 bits**.
6. EIGRP padrão: **K1 = K3 = 1** → banda e atraso.
7. Prometheus = **pull**; Grafana **não coleta**; Logstash = input→filter→output; Fluentd = coletor (EFK).
8. NIST 800-145: **5–3–4**; nuvem pública = um provedor, vários locatários.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** No WildFly, para habilitar o acesso ao console de administração, que por padrão exige autenticação, o administrador deve criar um usuário de gerenciamento executando:
(A) `jboss-cli.sh --adduser`. (B) **o script `add-user.sh`, localizado no diretório `bin`.** (C) o comando `useradd jboss`. (D) o arquivo `standalone.xml` com a tag `<user>`. (E) o script `domain.sh -u admin`.
✅ **B.**

**Q2.** Na arquitetura DiffServ, o comportamento por salto indicado para tráfego de voz, que requer baixa perda, baixa latência, baixo jitter e banda assegurada, é o:
(A) **EF (Expedited Forwarding).** (B) AF (Assured Forwarding). (C) BE (Best Effort). (D) CS0. (E) WRED.
✅ **A.**

**Q3.** No SNMP, a operação utilizada pelo agente para notificar o gerente, de forma assíncrona e sem confirmação, sobre um evento relevante é:
(A) Get. (B) GetBulk. (C) Set. (D) **Trap.** (E) Inform.
✅ **D.** (Inform também notifica, mas **com** confirmação.)

**Q4.** Na pilha EFK usada em clusters Kubernetes, o componente responsável por coletar e encaminhar os logs dos contêineres ao Elasticsearch é o:
(A) Kibana. (B) Logstash. (C) **Fluentd.** (D) Prometheus. (E) Grafana.
✅ **C.**

**Q5.** Segundo o NIST SP 800-145, constituem, respectivamente, uma característica essencial, um modelo de serviço e um modelo de implantação:
(A) PaaS, elasticidade rápida e nuvem híbrida. (B) **Serviço medido, IaaS e nuvem comunitária.** (C) Nuvem pública, SaaS e pool de recursos. (D) Amplo acesso à rede, nuvem privada e PaaS. (E) Multicloud, FaaS e nuvem pública.
✅ **B.**
