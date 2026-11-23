# Módulo 12 — TI: Sistemas Operacionais (teoria, Linux e Windows Server)

> Edital: *processos e threads (alocação de CPU, comunicação e sincronização, deadlocks, starvation); gerenciamento de memória (alocação, segmentação, memória virtual, paginação); E/S (armazenamento secundário e terciário, desempenho e confiabilidade); Linux (Red Hat e Oracle Linux): instalação, configuração, administração, utilitários; Windows 11/10, Windows Server 2019, 2022 e 2025: Active Directory, PowerShell, WSUS.* Estimativa: 3–4 questões.

## 1. Processos e threads
- **Processo**: programa em execução, com espaço de endereçamento próprio, descrito pelo **PCB** (*Process Control Block*: PID, estado, registradores, contador de programa, informações de memória, arquivos abertos, prioridade).
- **Estados**: **novo → pronto → executando → (bloqueado/espera) → pronto … → terminado**. Transições: *dispatch* (pronto → executando), **preempção**/fim do quantum (executando → pronto), E/S (executando → bloqueado), conclusão da E/S (bloqueado → pronto).
- **Troca de contexto**: salvar o estado de um processo e carregar o de outro (custo sem trabalho útil).
- **Thread**: unidade de execução **dentro** de um processo; threads do mesmo processo **compartilham** memória (código, dados, arquivos), mas têm **pilha, registradores e contador de programa próprios**. Criação e troca mais baratas que processos.
  - Threads de **usuário** (gerenciadas por biblioteca; bloqueio de uma pode bloquear todas no modelo N:1) × de **núcleo** (escalonadas pelo SO). Modelos **1:1** (Linux, Windows), **N:1**, **M:N**.
- **Comunicação entre processos (IPC)**: memória compartilhada, **troca de mensagens**, *pipes* (`|`), *named pipes/FIFOs*, sockets, sinais (`kill -9` = SIGKILL, `-15` = SIGTERM), filas de mensagens.

### Escalonamento de CPU
| Algoritmo | Característica |
|---|---|
| **FCFS/FIFO** | Ordem de chegada; **não preemptivo**; efeito comboio |
| **SJF** (menor job primeiro) | **Menor tempo médio de espera** (ótimo); exige conhecer a duração; pode causar **starvation** dos longos |
| **SRTF** | SJF **preemptivo** (menor tempo restante) |
| **Prioridade** | Preemptivo ou não; risco de **starvation** → solução: **envelhecimento (*aging*)** |
| **Round Robin** | **Quantum** fixo, preemptivo, justo (sistemas de tempo compartilhado); quantum grande → FCFS; muito pequeno → excesso de trocas de contexto |
| **Filas multinível** (com realimentação) | Filas por prioridade/classe; processos podem mudar de fila |
- Métricas: utilização de CPU, *throughput*, **tempo de retorno** (*turnaround*), **tempo de espera**, **tempo de resposta**.

### Sincronização
- **Condição de corrida**: resultado depende da ordem de execução. **Seção crítica**: trecho que acessa recurso compartilhado.
- Requisitos: **exclusão mútua**, **progresso**, **espera limitada**.
- **Semáforo** (Dijkstra): inteiro com operações atômicas **`P`/`wait`/`down`** (decrementa; bloqueia se < 0) e **`V`/`signal`/`up`** (incrementa; acorda). **Binário** (mutex) × **contador**. **Mutex** (lock), **monitores** (sincronização na linguagem — `synchronized` do Java), variáveis de condição, *spinlocks*.
- Problemas clássicos: **produtor-consumidor** (buffer limitado), **leitores-escritores**, **jantar dos filósofos**.

### Deadlock (impasse) e starvation
- **4 condições necessárias (Coffman)** — todas simultâneas: **exclusão mútua**, **posse e espera** (*hold and wait*), **não preempção**, **espera circular**.
| Estratégia | Como |
|---|---|
| **Prevenção** | Negar uma das 4 condições (ex.: ordenar recursos para impedir espera circular; alocar tudo de uma vez) |
| **Evitação** | Só conceder recursos se o sistema permanecer em **estado seguro** — **algoritmo do banqueiro** |
| **Detecção e recuperação** | Grafo de alocação/espera; abortar processos ou preemptar recursos |
| **Ignorar** | "Algoritmo do avestruz" (comum em SOs de uso geral) |
- **Starvation** (inanição/esgotamento): processo **nunca obtém** o recurso (ex.: prioridade baixa sempre preterida), embora o sistema progrida — difere do deadlock, em que **ninguém** progride. Solução: **aging**.

## 2. Gerenciamento de memória
- **Endereço lógico** (gerado pelo processo) → **físico** (traduzido pela **MMU**).
- **Alocação contígua**: partições **fixas** (fragmentação **interna** — sobra dentro da partição) × **variáveis** (fragmentação **externa** — buracos entre partições; solução: **compactação**). Estratégias: **first-fit**, **best-fit** (menor buraco que caiba), **worst-fit**, next-fit.
- **Paginação**: memória lógica em **páginas** e física em **molduras/quadros** (*frames*) de **mesmo tamanho**; **tabela de páginas** por processo; **TLB** (cache de traduções). **Elimina fragmentação externa**, mas tem fragmentação interna (última página). Endereço = nº da página + deslocamento.
- **Segmentação**: divisão **lógica** (código, dados, pilha) em **segmentos de tamanhos variáveis** (base + limite); sofre fragmentação **externa**. **Segmentação paginada** combina ambas.
- **Memória virtual**: processos maiores que a RAM; páginas carregadas **sob demanda**; acesso a página ausente → **falta de página (page fault)** → busca no disco (*swap*).
| Substituição de páginas | Característica |
|---|---|
| **Ótimo (OPT)** | Substitui a que **demorará mais** a ser usada — teórico, referência |
| **FIFO** | A mais antiga; sofre **anomalia de Belady** (mais molduras podem gerar **mais** faltas) |
| **LRU** | A **menos recentemente usada** — boa aproximação do ótimo |
| **Segunda chance / Relógio** | FIFO com bit de referência |
| **NRU**, LFU | Não usada recentemente; menos frequentemente usada |
- **Thrashing**: o sistema passa mais tempo trocando páginas do que executando (pouca memória para o **conjunto de trabalho** — *working set*).

## 3. Entrada e saída e armazenamento
- Técnicas: **E/S programada** (*polling* — CPU espera), **por interrupção**, **DMA** (controlador transfere blocos direto para a memória, liberando a CPU). *Drivers*, *buffering*, *spooling* (impressão).
- **Armazenamento secundário**: HDD (tempo de acesso = **seek** + **latência rotacional** + transferência), **SSD** (sem partes móveis; *wear leveling*, TRIM).
- **Escalonamento de disco**: **FCFS**, **SSTF** (menor deslocamento — pode causar starvation), **SCAN** ("elevador": vai até o fim e volta), **C-SCAN** (circular: volta ao início sem atender), **LOOK/C-LOOK** (só até a última requisição).
- **Armazenamento terciário**: **fitas magnéticas** (LTO — backup e arquivamento, acesso sequencial, baixo custo), mídias ópticas, **bibliotecas robóticas (*tape libraries*)**.
- **Confiabilidade**: **RAID** 0 (striping, sem redundância), **1** (espelhamento), **5** (paridade distribuída, tolera 1 falha, mín. 3 discos), **6** (dupla paridade, tolera 2), **10** (espelhamento + striping). **MTBF** (tempo médio entre falhas), **MTTR** (tempo médio de reparo); **disponibilidade = MTBF / (MTBF + MTTR)**.
- **Desempenho**: IOPS, *throughput* (MB/s), latência; ferramentas `iostat`, `vmstat`, `iotop`.

## 4. Linux — Red Hat Enterprise Linux (RHEL) e Oracle Linux
- **Oracle Linux**: compatível binariamente com o RHEL; kernels **RHCK** (compatível com Red Hat) ou **UEK** (*Unbreakable Enterprise Kernel*); **Ksplice** (atualizações do kernel sem reinício).
- **Instalação**: instalador **Anaconda**; automação com **Kickstart** (arquivo `ks.cfg`); sistema de arquivos padrão **XFS**; particionamento com **LVM**.
| Tarefa | Comandos |
|---|---|
| Pacotes | **`dnf`** (RHEL 8+; sucessor do `yum`): `dnf install httpd`, `dnf update`, `dnf remove`, `dnf search`; **`rpm -qa`** (lista), `rpm -ivh pacote.rpm`; repositórios em `/etc/yum.repos.d/`; `subscription-manager` (RHEL) |
| Serviços (systemd) | `systemctl start/stop/restart/reload/status httpd`, **`systemctl enable --now httpd`** (habilita no boot e inicia), `systemctl list-units`; *targets* (`multi-user.target`, `graphical.target`) |
| Logs | **`journalctl -u httpd -f`**, `journalctl -b`; `/var/log/messages`, `/var/log/secure` |
| Firewall | **`firewalld`**: `firewall-cmd --permanent --add-service=http`, `--add-port=8080/tcp`, **`firewall-cmd --reload`**, `--list-all`, zonas |
| **SELinux** | Modos **enforcing / permissive / disabled**; `getenforce`, `setenforce 0` (permissive, temporário), `/etc/selinux/config` (permanente), `sestatus`; contextos: `ls -Z`, `chcon`, **`restorecon -Rv`**, `semanage fcontext`, `semanage port -a -t http_port_t -p tcp 8081`; booleanos `setsebool -P` |
| Usuários | `useradd`, `usermod -aG wheel joao` (grupo **wheel** = sudo no RHEL), `passwd`, `userdel -r`; `/etc/passwd`, **`/etc/shadow`** (hashes), `/etc/group`; `visudo` (`/etc/sudoers`) |
| Permissões | `chmod 750`, `chmod u+x`, `chown user:grupo`, `umask` (padrão 022 → arquivos 644, diretórios 755); **SUID (4)**, **SGID (2)**, **sticky bit (1)** — ex.: `/tmp` = 1777 |
| Discos/LVM | `lsblk`, `fdisk`/`parted`, `mkfs.xfs`, `mount`, **`/etc/fstab`**; LVM: `pvcreate` → `vgcreate` → `lvcreate` → `lvextend -r -L +10G` (`-r` redimensiona o FS; XFS cresce com `xfs_growfs`, **não encolhe**) |
| Rede | **`nmcli`** (NetworkManager), `nmtui`, `ip addr`, `ip route`, `ss -tulpn`, `hostnamectl set-hostname`, `/etc/hosts`, `/etc/resolv.conf` |
| Processos | `ps aux`, `top`/`htop`, `kill`, `nice`/`renice`, `jobs`, `bg`, `fg`, `nohup` |
| Agendamento | `crontab -e` (min hora dia mês dia-da-semana), `at`, *systemd timers* |
| Texto | `grep -r`, `find / -name "*.log" -mtime -1`, `awk`, `sed`, `cut`, `sort`, `uniq`, `wc`, `tail -f`, `less` |
| Recursos | `df -h`, `du -sh`, `free -h`, `uptime`, `vmstat`, `iostat`, `sar` |
| Arquivos | `tar -czvf a.tar.gz dir/`, `tar -xzvf`, `rsync -av`, `scp`, `ssh-keygen` |
- **Diretórios** (FHS): `/etc` (configuração), `/var` (logs, spool), `/home`, `/root`, `/usr/bin`, `/usr/sbin`, `/opt`, `/tmp`, `/boot`, `/dev`, `/proc` e `/sys` (virtuais).

## 5. Windows 10/11 e Windows Server 2019, 2022 e 2025
- **Windows 10** em suporte estendido/legado (fim do suporte padrão em **14/10/2025**; ESU pago); **Windows 11** exige TPM 2.0 e Secure Boot.
- **Windows Server**: instalação **Server Core** (sem GUI — menor superfície de ataque, gerenciado por PowerShell/**Windows Admin Center**) × **Desktop Experience**. Edições Standard e Datacenter. **Server Manager**, funções (*roles*) e recursos (*features*): **AD DS**, **DNS**, **DHCP**, **IIS**, **Hyper-V**, File and Storage Services, **WSUS**, Remote Desktop Services, AD CS (certificados).
- Novidades do **Windows Server 2025** (confirmar detalhes): **hotpatching** (atualizações sem reinício, via Azure Arc), melhorias no AD (banco com páginas de 32 KB, nível funcional novo), **SMB over QUIC** em todas as edições, segurança reforçada (SMB signing exigido por padrão), Hyper-V com suporte a GPU particionada.

### Active Directory Domain Services
| Conceito | Definição |
|---|---|
| **Domínio** | Limite administrativo e de replicação; banco **NTDS.dit** |
| **Árvore / Floresta** | Domínios com namespace contíguo / conjunto de árvores com **esquema e catálogo global comuns** (limite de segurança) |
| **OU** (unidade organizacional) | Contêiner para organizar objetos, **delegar administração** e **vincular GPOs** |
| **Controlador de domínio (DC)** | Servidor que autentica e replica o AD (multimestre); **RODC** = somente leitura |
| **Catálogo Global (GC)** | Cópia parcial de todos os objetos da floresta (porta **3268**) |
| **Sites** | Topologia física (sub-redes) para replicação e localização de DCs |
| **Relações de confiança** | Entre domínios/florestas (transitivas ou não; uni ou bidirecionais) |
- **Funções FSMO (5)**: de **floresta** — **Schema Master** e **Domain Naming Master**; de **domínio** — **RID Master** (pools de identificadores), **PDC Emulator** (senhas, sincronização de horário, bloqueios), **Infrastructure Master**.
- **Grupos**: tipos **segurança** × **distribuição**; escopos **local de domínio**, **global**, **universal**. Estratégia **AGDLP**: contas → grupos **G**lobais → grupos **D**omain **L**ocal → **P**ermissões.
- **GPO**: ordem de aplicação **LSDOU** — **L**ocal → **S**ite → **D**omínio → **O**U (a última aplicada prevalece, salvo *Enforced*/*Block Inheritance*); `gpupdate /force`, `gpresult /r`; configurações de **Computador** e de **Usuário**.
- Protocolos: **Kerberos** (porta 88 — tickets, **TGT**, KDC, exige sincronismo de relógio), **LDAP** (389) / LDAPS (636), DNS (registros **SRV** localizam DCs), NTLM (legado).

### PowerShell
- Cmdlets no padrão **Verbo-Substantivo**: `Get-Service`, `Start-Service`, `Get-Process`, `Stop-Process -Name notepad`, `Get-EventLog`/`Get-WinEvent`, `Get-ChildItem`, `Copy-Item`, `Restart-Computer`, `Test-NetConnection -Port 443`.
- **Pipeline de objetos** (não de texto): `Get-Service | Where-Object Status -eq 'Running' | Sort-Object Name | Select-Object Name, Status`.
- Ajuda e descoberta: **`Get-Help`**, **`Get-Command`**, **`Get-Member`** (propriedades e métodos do objeto).
- Módulo AD: `Get-ADUser -Filter *`, `New-ADUser`, `Add-ADGroupMember`, `Get-ADComputer`; `Install-WindowsFeature AD-Domain-Services -IncludeManagementTools`.
- **Execution Policy**: `Restricted` (padrão em clientes Windows), **`RemoteSigned`** (padrão no Windows Server), `AllSigned`, `Unrestricted`, `Bypass` — `Set-ExecutionPolicy RemoteSigned`.
- **Remoting** (WinRM, portas **5985** HTTP / **5986** HTTPS): `Enter-PSSession -ComputerName srv01`, `Invoke-Command -ComputerName srv01,srv02 -ScriptBlock { ... }`.
- Variáveis `$nome`, arrays `@()`, hashtables `@{}`, scripts `.ps1`, comparadores `-eq -ne -gt -lt -like -match`. PowerShell 7 (multiplataforma) × Windows PowerShell 5.1.

### WSUS (Windows Server Update Services)
- Função do Windows Server para **gerenciar e distribuir atualizações da Microsoft** na rede interna: **sincroniza** com o Microsoft Update (ou com um **servidor WSUS *upstream***), o administrador **aprova** atualizações por **grupos de computadores**, os clientes baixam do servidor local (economia de banda e controle).
- Clientes apontados via **GPO** ("Especificar o local do serviço de atualização na intranet da Microsoft"); **direcionamento no lado do cliente** (*client-side targeting*) ou no console.
- Hierarquia: servidor **upstream/downstream**; modo **réplica** (herda aprovações) × **autônomo**.
- Portas padrão (WSUS 2012+): **8530** (HTTP) e **8531** (HTTPS). Classificações: atualizações críticas, de segurança, de definição, *service packs*, *drivers*… Banco: WID ou SQL Server.
- A Microsoft anunciou (2024) que o WSUS está **descontinuado** (sem novos recursos), mas continua presente no Windows Server 2025; alternativas: Windows Update for Business, Intune, Azure Update Manager.

## ⚠️ Pegadinhas
1. **SJF** minimiza o tempo médio de espera; **Round Robin** usa quantum; **aging** combate starvation.
2. Deadlock exige as **4 condições** simultâneas; **banqueiro** = evitação.
3. Paginação → fragmentação **interna**; segmentação → **externa**. FIFO → **anomalia de Belady**.
4. DMA libera a CPU; SSTF pode causar starvation; SCAN = elevador.
5. RHEL: **`dnf`**, **`firewall-cmd --permanent` + `--reload`**, **SELinux** (`restorecon`), grupo **wheel**; XFS **não encolhe**.
6. FSMO: **Schema** e **Domain Naming** são de floresta; **RID, PDC, Infrastructure** de domínio. GPO: **LSDOU**.
7. PowerShell passa **objetos**; padrão no Server = **RemoteSigned**. WSUS: **8530/8531**.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Condição necessária para a ocorrência de deadlock na qual existe uma cadeia de processos em que cada um aguarda um recurso retido pelo próximo:
(A) exclusão mútua. (B) posse e espera. (C) não preempção. (D) **espera circular.** (E) inanição.
✅ **D.**

**Q2.** Algoritmo de substituição de páginas que pode apresentar a anomalia de Belady:
(A) LRU. (B) Ótimo. (C) **FIFO.** (D) Relógio com bit de referência e modificação. (E) LFU com envelhecimento.
✅ **C.**

**Q3.** Em um servidor RHEL 9 com firewalld, para liberar permanentemente o serviço HTTPS e aplicar a regra imediatamente, o administrador deve executar:
(A) `iptables -A INPUT -p tcp --dport 443 -j ACCEPT`. (B) **`firewall-cmd --permanent --add-service=https` seguido de `firewall-cmd --reload`.** (C) `systemctl enable https`. (D) `setenforce https`. (E) `ufw allow 443`.
✅ **B.**

**Q4.** No Active Directory, a função FSMO responsável por sincronizar o horário do domínio, processar alterações de senha prioritariamente e tratar bloqueios de conta é:
(A) Schema Master. (B) RID Master. (C) Infrastructure Master. (D) Domain Naming Master. (E) **PDC Emulator.**
✅ **E.**

**Q5.** No PowerShell, o cmdlet que exibe as propriedades e os métodos dos objetos que trafegam no pipeline é:
(A) Get-Help. (B) Get-Command. (C) **Get-Member.** (D) Select-Object. (E) Where-Object.
✅ **C.**
