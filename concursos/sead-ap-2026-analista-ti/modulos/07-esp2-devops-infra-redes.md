# Módulo 7 — Específicos 2: DevOps, DevSecOps, Nuvem, SO, Redes e Observabilidade

> Bloco mais extenso do edital (8 subitens). Estimativa: 4–5 questões. A IDCAP cobra muito **redes** (portas, CIDR, OSI, IPv6) e **conceitos de nuvem/contêiner**.

## Mapa do edital (item 2)
2.1 CI/CD (GitLab CI, Jenkins), automação, IaC · 2.2 Docker, Kubernetes · 2.3 Nuvem (IaaS, PaaS, SaaS; pública, híbrida) · 2.4 Linux e Windows Server · 2.5 Redes (OSI, TCP/IP, protocolos) · 2.6 Virtualização · 2.7 Backup e continuidade · 2.8 Monitoramento (Zabbix, Prometheus, Grafana).

## 2.1 DevOps, CI/CD e IaC
- **DevOps**: cultura + práticas que unem **desenvolvimento e operações** para entregar mais rápido e com qualidade. Princípios: **colaboração**, automação, melhoria contínua, foco no cliente, responsabilidade compartilhada. Modelo **CALMS**: Culture, Automation, Lean, Measurement, Sharing.
- **As Três Maneiras** (The DevOps Handbook): **fluxo** (dev → ops), **feedback** (ops → dev), **aprendizado e experimentação contínuos**.
- **DevSecOps**: segurança **integrada desde o início** (*shift-left*): SAST, DAST, SCA (dependências), varredura de imagens, gestão de segredos no pipeline.
- **Métricas DORA**: frequência de deploy, **lead time para mudanças**, **taxa de falha de mudanças**, **tempo de restauração (MTTR)**.

| Termo | Definição |
|---|---|
| **Integração Contínua (CI)** | Integrar código ao repositório várias vezes ao dia, com **build e testes automatizados** a cada commit |
| **Entrega Contínua (Continuous Delivery)** | Código sempre **pronto** para produção; o deploy em produção exige **aprovação manual** |
| **Implantação Contínua (Continuous Deployment)** | Todo commit aprovado nos testes vai **automaticamente** para produção |

> ⚠️ Delivery = **botão manual** para produção. Deployment = **automático**.

### GitLab CI × Jenkins
| | **GitLab CI/CD** | **Jenkins** |
|---|---|---|
| Configuração | Arquivo **`.gitlab-ci.yml`** na raiz do repositório (YAML) | **`Jenkinsfile`** (Groovy — pipeline declarativo ou scripted) |
| Execução | **GitLab Runners** | Controller (master) + **agents** (nós) |
| Estrutura | **stages** (build, test, deploy) → **jobs**; `script`, `artifacts` (+ `paths`), `cache`, `only/rules`, `variables`, `image` | `pipeline { agent any; stages { stage('Build') { steps { … } } } }` |
| Natureza | Integrado ao GitLab (SCM + CI) | Servidor open source, extensível por **plugins** |

```yaml
stages: [build, test, deploy]
build:
  stage: build
  script: [ "docker build -t app ." ]
  artifacts:
    paths: [ "dist/" ]
```

### Infraestrutura como Código (IaC)
| Ferramenta | Tipo | Abordagem |
|---|---|---|
| **Terraform** (HashiCorp, HCL) | **Provisionamento** multinuvem | **Declarativa**; *state file*; `init → plan → apply → destroy` |
| **Ansible** | **Gerência de configuração** | **Agentless** (via SSH), playbooks em **YAML**, módulos idempotentes |
| Puppet / Chef | Gerência de configuração | Com agente (pull) |
| CloudFormation / ARM / Bicep | Provisionamento nativo AWS / Azure | Declarativa |
- **Declarativa** (diz o **estado desejado**) × **imperativa** (diz os **passos**). **Idempotência**: executar várias vezes produz o mesmo resultado. **Infraestrutura imutável**: substitui em vez de alterar.

## 2.2 Contêineres e orquestração
| | **Máquina virtual** | **Contêiner** |
|---|---|---|
| Isola | Hardware (via hipervisor), **SO convidado completo** | Processo; **compartilha o kernel** do host |
| Tamanho / boot | GB / minutos | MB / segundos |
| Isolamento | Mais forte | Menor (namespaces e cgroups) |

### Docker
- **Imagem** (modelo imutável, em **camadas**) → **contêiner** (instância em execução). **Dockerfile** → `docker build`. Registro: **Docker Hub**, Harbor.
- Instruções do Dockerfile: `FROM`, `RUN`, `COPY`, `ADD`, `WORKDIR`, `ENV`, `EXPOSE` (documenta a porta), `CMD` (comando padrão, sobrescrevível), `ENTRYPOINT` (executável fixo), `USER`, `VOLUME`.
- Comandos: `docker run -d -p 8080:80 nginx` (porta host:contêiner), `docker ps`, `docker images`, `docker exec -it <id> bash`, `docker logs`, `docker stop/rm`, `docker pull/push`.
- **Volumes** (persistência), **redes** (bridge, host, overlay). **Docker Compose** (`docker-compose.yml`): múltiplos contêineres.
- Vantagens: **portabilidade** ("roda igual em qualquer lugar" — IDCAP 2025), leveza, consistência entre ambientes.
- **CaaS** (Container as a Service): nuvem que oferece orquestração e runtime de contêineres (IDCAP 2025).

### Kubernetes (K8s)
| Objeto | Função |
|---|---|
| **Pod** | **Menor unidade implantável**; 1+ contêineres que compartilham rede e armazenamento |
| **Deployment** | Gerencia réplicas de pods (via ReplicaSet), **rolling update** e rollback |
| **ReplicaSet** | Mantém o nº desejado de pods |
| **Service** | IP/DNS estável e balanceamento para pods (ClusterIP, **NodePort**, **LoadBalancer**) |
| **Ingress** | Roteamento HTTP/HTTPS externo (host/path) |
| **ConfigMap / Secret** | Configuração / dados sensíveis |
| **Namespace** | Isolamento lógico |
| **StatefulSet** | Apps com estado (bancos) |
| **DaemonSet** | Um pod por nó (agentes de log/monitoramento) |
| **PersistentVolume / PVC** | Armazenamento persistente |
| **HPA** | Escala automática horizontal por CPU/métricas |

- **Control plane**: **kube-apiserver** (porta de entrada), **etcd** (armazenamento chave-valor do estado do cluster), **kube-scheduler** (decide em qual nó o pod roda), **kube-controller-manager**. **Nós (workers)**: **kubelet** (agente), **kube-proxy** (rede), container runtime (containerd).
- `kubectl get pods`, `kubectl apply -f deploy.yaml`, `kubectl scale`, `kubectl logs`.
- **Helm**: gerenciador de pacotes (charts) do K8s.

## 2.3 Computação em nuvem
**NIST — 5 características essenciais**: **autoatendimento sob demanda**, **amplo acesso pela rede**, **pool de recursos** (multilocação), **elasticidade rápida**, **serviço medido** (pague pelo uso).

| Modelo de serviço | Cliente gerencia | Provedor gerencia | Exemplos |
|---|---|---|---|
| **IaaS** | SO, middleware, aplicação, dados | Hardware, rede, virtualização | AWS EC2, Azure VMs, Google Compute Engine |
| **PaaS** | Aplicação e dados | Até o runtime/SO | Heroku, Azure App Service, Google App Engine |
| **SaaS** | Só uso/configuração | Tudo | Microsoft 365, Gmail, Salesforce |
| FaaS (serverless) | Funções | Infra e escala | AWS Lambda, Azure Functions |

| Modelo de implantação | Definição |
|---|---|
| **Pública** | Infra do provedor, compartilhada por vários clientes |
| **Privada** | Exclusiva de uma organização (on-premises ou hospedada) |
| **Híbrida** | Combinação de pública + privada, com portabilidade entre elas |
| **Comunitária** | Compartilhada por organizações com interesses comuns (ex.: órgãos públicos) |
| Multicloud | Vários provedores públicos |

- **Responsabilidade compartilhada**: o provedor cuida da segurança **"da" nuvem**; o cliente, da segurança **"na" nuvem** (dados, identidades, configurações).
- Escalabilidade **vertical** (scale up: mais CPU/RAM) × **horizontal** (scale out: mais instâncias). Elasticidade = escalar **automaticamente** conforme demanda.
- CapEx (investimento) → **OpEx** (despesa operacional).

## 2.4 Sistemas operacionais
### Linux
| Comando | Função | | Comando | Função |
|---|---|---|---|---|
| `ls -la` | listar (inclui ocultos) | | `chmod 755 arq` | permissões |
| `cd`, `pwd` | navegar, diretório atual | | `chown user:grupo arq` | dono |
| `cp`, `mv`, `rm -r` | copiar, mover, remover | | `ps aux`, `top`, `kill -9 PID` | processos |
| `mkdir`, `touch` | criar diretório, arquivo | | `df -h`, `du -sh`, `free -h` | disco, uso, memória |
| `cat`, `less`, `head`, `tail -f` | ver arquivos | | `grep`, `find`, `awk`, `sed` | buscar/processar texto |
| `sudo`, `su` | privilégio | | `systemctl start/enable nginx` | serviços (systemd) |
| `ip a`, `ss -tulpn`, `ping` | rede | | `tar -czvf`, `apt`/`yum`/`dnf` | compactar, pacotes |

- **Permissões** `rwx` = 4 + 2 + 1. `chmod 755` → dono rwx (7), grupo r-x (5), outros r-x (5). `chmod 644` → rw-r--r--.
- Diretórios: `/etc` (configuração), `/var/log` (logs), `/home`, `/root`, `/bin` `/usr/bin` (binários), `/tmp`, `/dev` (dispositivos), `/proc` (processos, virtual), `/boot`. Apache no Debian/Ubuntu: `/etc/apache2/` (`apache2.conf`); no RHEL: `/etc/httpd/conf/httpd.conf`.
- `cron` (agendamento: `min hora dia mês dia-da-semana`), `/etc/passwd`, `/etc/shadow` (hashes de senha).

### Windows Server
- **Active Directory Domain Services (AD DS)**: serviço de diretório; **domínio**, **árvore**, **floresta**, **OU** (unidade organizacional), **controlador de domínio (DC)**; autenticação **Kerberos**; consultas via **LDAP** (389/636).
- **GPO** (Group Policy): políticas aplicadas a usuários/computadores (ordem **LSDOU**: Local, Site, Domínio, OU).
- Funções: **DNS**, **DHCP**, **IIS** (servidor web), **Hyper-V** (hipervisor), File Server, **WSUS** (atualizações), Remote Desktop Services. **PowerShell** para automação.
- Grupos de segurança: escopo **local de domínio, global, universal**.

## 2.5 Redes de computadores
### Modelo OSI × TCP/IP
| # | OSI | Função | Protocolos / equipamentos | TCP/IP |
|---|---|---|---|---|
| 7 | **Aplicação** | Interface com o usuário/app | HTTP, HTTPS, DNS, SMTP, FTP, SSH, SNMP, DHCP | **Aplicação** |
| 6 | Apresentação | Formato, **criptografia**, compressão | TLS*, JPEG, ASCII | Aplicação |
| 5 | Sessão | Controle de diálogo/sessão | RPC, NetBIOS | Aplicação |
| 4 | **Transporte** | Fim a fim, portas, segmentos | **TCP, UDP** | **Transporte** |
| 3 | **Rede** | **Endereçamento lógico e roteamento** (pacotes) | **IP**, ICMP, IPsec, OSPF, BGP · **roteador** | **Internet** |
| 2 | **Enlace** | Endereço físico (**MAC**), quadros, **VLAN** | Ethernet, Wi-Fi, ARP*, PPP · **switch**, bridge | **Acesso à rede** |
| 1 | Física | Bits, sinais, cabos | RJ-45, fibra · **hub**, repetidor | Acesso à rede |

🧠 OSI de cima para baixo: "**A**ula **A**presentada **S**em **T**empo **R**esulta **E**m **F**racasso" (Aplicação, Apresentação, Sessão, Transporte, Rede, Enlace, Física).

### TCP × UDP
| TCP | UDP |
|---|---|
| **Orientado à conexão** (three-way handshake: **SYN → SYN-ACK → ACK**) | Sem conexão |
| Confiável: confirmação, retransmissão, ordenação, controle de fluxo e congestionamento | Não confiável, sem garantia de entrega/ordem |
| Mais lento | Mais rápido, menor overhead |
| HTTP/HTTPS, SSH, SMTP, FTP | **DNS** (consultas), **DHCP**, VoIP, streaming, SNMP, TFTP |

### 🔢 Portas que caem
| Porta | Serviço | | Porta | Serviço |
|---|---|---|---|---|
| 20/21 | FTP (dados/controle) | | 110 / 995 | POP3 / POP3S |
| **22** | **SSH** (e SFTP/SCP) | | 143 / 993 | IMAP / IMAPS |
| 23 | Telnet (inseguro) | | 161/162 (UDP) | **SNMP** / traps |
| **25** | SMTP | | **389** / 636 | LDAP / LDAPS |
| **53** | **DNS** (UDP e TCP) | | **443** | **HTTPS** |
| 67/68 (UDP) | DHCP | | 445 | SMB |
| **80** | **HTTP** | | **587** | SMTP com STARTTLS (submissão) |
| 123 (UDP) | NTP | | **3389** | RDP |
| 3306 / 5432 | MySQL / PostgreSQL | | 1433 / 27017 | SQL Server / MongoDB |

### Endereçamento IPv4
- 32 bits, 4 octetos. **Classes** (legado): A 1–126 (/8), B 128–191 (/16), C 192–223 (/24), D multicast (224–239), E experimental. 127.0.0.0/8 = **loopback**.
- **Privados (RFC 1918)**: **10.0.0.0/8**, **172.16.0.0/12** (172.16–172.31), **192.168.0.0/16**. APIPA: 169.254.0.0/16.
- **NAT**: traduz endereços privados para público(s) — **PAT** (NAT overload) usa portas.
- **Sub-redes (CIDR)**: hosts válidos = **2^(32−n) − 2**.

| Máscara | CIDR | Endereços | Hosts válidos |
|---|---|---|---|
| 255.255.255.0 | /24 | 256 | 254 |
| 255.255.255.128 | /25 | 128 | 126 |
| 255.255.255.192 | **/26** | 64 | 62 |
| 255.255.255.224 | /27 | 32 | 30 |
| 255.255.255.240 | /28 | 16 | 14 |
| 255.255.255.248 | /29 | 8 | 6 |
| 255.255.255.252 | /30 | 4 | 2 (links ponto a ponto) |

> **Exemplo resolvido** (padrão IDCAP 2025): IP 182.243.109.100/26. Blocos de 64 no 4º octeto: 0, 64, 128, 192. 100 está no bloco **64–127** → rede **182.243.109.64/26**, broadcast (último endereço) **182.243.109.127**, hosts **.65 a .126**.

### IPv6
- **128 bits**, **8 grupos de 16 bits**, cada grupo com **4 dígitos hexadecimais**, separados por **":"** (IDCAP 2025).
- Abreviação: zeros à esquerda podem ser omitidos; **uma única** sequência de grupos zerados vira **"::"**. Ex.: `2001:0db8:0000:0000:0000:0000:0000:0001` → `2001:db8::1`. Loopback `::1`.
- Sem broadcast (usa **multicast** e **anycast**); **NDP** substitui o ARP; autoconfiguração **SLAAC**; IPsec nativo no projeto.

### Protocolos de aplicação essenciais
| Protocolo | Função |
|---|---|
| **DNS** | Resolve nomes em IPs. Registros: **A** (IPv4), **AAAA** (IPv6), **CNAME** (apelido), **MX** (e-mail), **NS**, **PTR** (reverso), **TXT** (SPF, DKIM), SOA |
| **DHCP** | Atribui IP automaticamente — **DORA**: Discover, Offer, Request, Acknowledge |
| **ARP** | Descobre o **MAC** a partir do IP |
| **ICMP** | Mensagens de controle/erro (**ping**, traceroute) |
| **SNMP** | Gerência de rede: **gerente**, **agente**, **MIB** (base de informações), OIDs; operações **GET**, **SET**, **TRAP**; v3 com autenticação e criptografia |
| **SIP** | Sinalização de VoIP (estabelece, modifica e encerra sessões) |
| **NTP** | Sincronização de relógio |
| **SSH** | Acesso remoto seguro (substitui Telnet) |
| **TLS** | Criptografia de transporte (HTTPS) — versões seguras: **1.2 e 1.3** |

- **Equipamentos**: hub (camada 1, repete para todos), **switch** (camada 2, encaminha por MAC; switch L3 roteia), **roteador** (camada 3, interliga redes por IP), **firewall**, **access point**.
- **VLAN** (802.1Q): segmenta logicamente a rede em camada 2. **VPN**: túnel criptografado sobre rede pública (IPsec, SSL/TLS, WireGuard).
- **Wi-Fi**: 802.11n (Wi-Fi 4), **802.11ac (Wi-Fi 5, 5 GHz)**, **802.11ax (Wi-Fi 6/6E — 6E adiciona 6 GHz; até ~9,6 Gb/s; OFDMA)**, 802.11be (Wi-Fi 7). Segurança: WEP (quebrado) → WPA → **WPA2 (AES)** → **WPA3 (SAE)**.
- **Cabeamento**: par trançado UTP (Cat5e: 1 Gbps; Cat6: 1 Gbps/10 Gbps até 55 m; Cat6a: 10 Gbps até 100 m), conector **RJ-45**; limite de **100 m** por segmento. **T-568A** (pinos 1→8): **branco-verde, verde, branco-laranja**, azul, branco-azul, **laranja**, branco-marrom, marrom (pinos 1-2-3-6 = BV-V-BL-L, cobrado pela IDCAP). **T-568B**: **branco-laranja, laranja, branco-verde**, azul, branco-azul, **verde**, branco-marrom, marrom (troca os pares verde e laranja). Cabo **direto**: mesmo padrão nas duas pontas; **crossover**: A numa ponta e B na outra.
- **Fibra**: monomodo (longas distâncias, laser) × multimodo (curtas, LED).
- Topologias: **estrela** (mais usada — falha de um cabo afeta só aquele nó), barramento, anel, malha (redundância).
- **QoS**: largura de banda, **latência** (atraso), **jitter** (variação do atraso), **perda de pacotes**.

## 2.6 Virtualização
- **Hipervisor (VMM)**: software que cria e gerencia VMs, alocando CPU, memória e armazenamento.

| Tipo | Onde roda | Exemplos |
|---|---|---|
| **Tipo 1 (bare-metal / nativo)** | Direto no **hardware** | VMware ESXi, Microsoft Hyper-V, Xen, KVM, Proxmox VE |
| **Tipo 2 (hospedado)** | Sobre um **SO hospedeiro** | VirtualBox, VMware Workstation, Parallels |

- Virtualização **completa** (SO convidado sem modificação, com suporte de hardware Intel VT-x/AMD-V) × **paravirtualização** (SO convidado modificado, mais desempenho).
- Tipos: de **servidor**, de **rede** (SDN, VLAN, NFV), de **armazenamento** (pool de discos visto como um único dispositivo), de **desktop** (VDI), de aplicação.
- Recursos: **snapshot**, **migração ao vivo** (vMotion / Live Migration), **alta disponibilidade (HA)**, templates, overcommit.

## 2.7 Backup e continuidade de serviços
| Tipo | Copia | Restauração | Marca o arquivo (bit de arquivamento)? |
|---|---|---|---|
| **Completo (full)** | Tudo | Mais rápida (1 conjunto) | Sim (limpa) |
| **Incremental** | Alterado desde o **último backup de qualquer tipo** | Último full + **todos** os incrementais | Sim (limpa) |
| **Diferencial** | Alterado desde o **último full** | Último full + **último** diferencial | **Não** |

- Incremental: backup mais **rápido** e menor; restauração mais **lenta**. Diferencial: cresce a cada dia; restauração mais simples.
- **Regra 3-2-1**: **3** cópias, em **2** mídias diferentes, **1** fora do local (offsite). Variante **3-2-1-1-0**: +1 **offline/imutável** (contra ransomware), **0** erros nos testes de restauração.
- **RPO** (Recovery Point Objective): **quanto de dados** pode ser perdido (tempo entre backups). **RTO** (Recovery Time Objective): **em quanto tempo** o serviço deve voltar.
- **RAID**: 0 (striping, sem redundância, desempenho), **1** (espelhamento), **5** (paridade distribuída, mín. 3 discos, tolera 1 falha), **6** (dupla paridade, tolera 2), **10** (espelhamento + striping). ⚠️ RAID **não é backup**.
- Sites de contingência: **hot site** (pronto, minutos), **warm site** (parcial, horas), **cold site** (só infraestrutura, dias).
- **ISO 22301** (Gestão de Continuidade de Negócios — SGCN, ciclo **PDCA**); **BIA** (Análise de Impacto no Negócio) define processos críticos, RTO/RPO; **PCN** (Plano de Continuidade de Negócios), **PRD/DRP** (Plano de Recuperação de Desastres).
- Armazenamento: **DAS** (direto), **NAS** (arquivos pela rede — NFS/SMB), **SAN** (rede dedicada de **blocos** — Fibre Channel/iSCSI).

## 2.8 Monitoramento e observabilidade
- **Monitoramento**: verifica se o sistema está funcionando (métricas conhecidas, alertas). **Observabilidade**: capacidade de entender o estado interno a partir das saídas — **3 pilares: métricas, logs e traces** (rastreamento distribuído). Padrão aberto: **OpenTelemetry**.

| Ferramenta | Destaque |
|---|---|
| **Zabbix** | Monitoramento de **infraestrutura** open source (servidores, redes, VMs); **agentes** Zabbix, SNMP, IPMI; **templates**, **triggers** (condições de alerta), itens, hosts, dashboards; armazena em banco relacional (MySQL/PostgreSQL) |
| **Prometheus** | Coleta **métricas de séries temporais** pelo modelo **pull** (raspagem — *scraping* — de endpoints `/metrics` via HTTP); linguagem **PromQL**; **exporters** (node_exporter); **Alertmanager**; ideal para Kubernetes/nuvem nativa |
| **Grafana** | **Visualização**: dashboards e painéis sobre várias fontes de dados (Prometheus, Zabbix, Elasticsearch, Loki, InfluxDB); alertas. **Não coleta** métricas por si |
| Nagios | Monitoramento clássico com **plugins** |
| ELK / EFK | Elasticsearch + Logstash/Fluentd + Kibana — **logs** |
| Jaeger / Zipkin | **Traces** distribuídos |

- Métodos: **RED** (Rate, Errors, Duration — serviços), **USE** (Utilization, Saturation, Errors — recursos), **Golden Signals** do Google SRE (**latência, tráfego, erros, saturação**).
- **SLI** (indicador medido) → **SLO** (objetivo interno, ex.: 99,9%) → **SLA** (acordo contratual com penalidades). **Error budget** = 100% − SLO.
- Disponibilidade 99,9% ≈ 8,76 h de indisponibilidade por ano; 99,99% ≈ 52,6 min/ano.

## ⚠️ Pegadinhas do bloco
1. Continuous **Delivery** (deploy manual em produção) × **Deployment** (automático).
2. **Pod** é a menor unidade do Kubernetes — não o contêiner.
3. Prometheus usa **pull**; Grafana **só visualiza**.
4. Contêiner **compartilha o kernel**; VM tem SO completo.
5. Hipervisor **tipo 1** = bare-metal (ESXi, Hyper-V); **tipo 2** = hospedado (VirtualBox).
6. **Diferencial** = desde o último **full**; **incremental** = desde o último backup **qualquer**.
7. DNS usa **UDP 53** (e TCP 53 em transferência de zona e respostas grandes).
8. **Switch** = camada 2 (enlace, MAC, VLAN); **roteador** = camada 3.

## 🧠 Memorize
- **IaaS/PaaS/SaaS**: "**I**nfra eu configuro o SO; **P**lataforma eu só subo o código; **S**oftware eu só uso".
- Backup: "**D**iferencial **D**epende só do full".
- 3-2-1: "três cópias, duas mídias, uma longe".

## Questões comentadas (estilo IDCAP)

**Q1.** No Kubernetes, a menor unidade implantável, que pode conter um ou mais contêineres compartilhando rede e armazenamento, e o objeto que expõe esses elementos com IP estável e balanceamento de carga são, respectivamente:
(A) Node e Ingress. (B) **Pod e Service.** (C) Deployment e ConfigMap. (D) Namespace e Pod.
✅ **B.**

**Q2.** Uma prática garante que todo código aprovado na esteira automatizada seja implantado em produção sem intervenção humana; outra garante que o código esteja sempre pronto para implantação, que depende de aprovação manual. São, respectivamente:
(A) Integração contínua e implantação contínua. (B) **Implantação contínua (deployment) e entrega contínua (delivery).** (C) Entrega contínua e integração contínua. (D) Infraestrutura como código e entrega contínua.
✅ **B.**

**Q3.** O endereço de broadcast da sub-rede à qual pertence o host 10.20.30.77/27 é:
(A) 10.20.30.63. (B) **10.20.30.95.** (C) 10.20.30.127. (D) 10.20.30.255.
✅ **B.** /27 → blocos de 32: 64–95. Rede 10.20.30.64, broadcast .95.

**Q4.** Uma ferramenta coleta métricas por raspagem periódica de endpoints HTTP e possui linguagem de consulta própria; outra é voltada à criação de dashboards a partir de diversas fontes de dados. São, respectivamente:
(A) Zabbix e Nagios. (B) **Prometheus e Grafana.** (C) Grafana e Prometheus. (D) Jenkins e Kibana.
✅ **B.**

**Q5.** Um órgão faz backup completo no domingo e, nos demais dias, copia apenas os arquivos alterados desde o último backup completo. Para restaurar os dados na quinta-feira, serão necessários:
(A) todos os backups de segunda a quinta. (B) **o backup completo de domingo e o backup de quinta-feira.** (C) apenas o backup de quinta-feira. (D) o backup completo e o de segunda-feira.
✅ **B.** Esquema diferencial.

**Q6.** Os protocolos DNS, HTTPS e SMTP com TLS (submissão) utilizam, por padrão, as portas:
(A) 53, 80 e 25. (B) **53, 443 e 587.** (C) 25, 443 e 110. (D) 67, 443 e 993.
✅ **B.** (Mesma questão cobrada pela IDCAP em 2025.)
