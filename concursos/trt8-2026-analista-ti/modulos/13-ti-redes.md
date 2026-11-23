# Módulo 13 — TI: Redes de Computadores

> Edital: *tipos e meios de transmissão; circuitos, pacotes e células; PAN, LAN, MAN, WAN, WPAN, WLAN, WMAN, WWAN; protocolos; elementos de interconexão; OSI e TCP/IP; IPv4 e IPv6, endereçamento, DNS e entidades de registro; TCP, UDP, IPSec, ARP, SSH, SMTP, HTTP, FTP, LDAP, DNS, DHCP, POP, IMAP; cabeamento estruturado (ABNT NBR 14565:2019); fibras monomodo e multimodo; IEEE 802.1Q, 802.1X, 802.3, STP e RSTP; 802.11ac, 802.11ax, 802.11be.* Estimativa: 4–5 questões — a FCC cobra **cálculo de sub-rede (IPv4 e IPv6)**, **NBR 14565** e **protocolos de enlace**.

## 1. Meios de transmissão e comutação
| Meio | Características |
|---|---|
| **Par trançado** (UTP sem blindagem; F/UTP, S/FTP blindados) | Trançado reduz **diafonia (crosstalk)** e interferência; conector **RJ-45**; até **100 m** por canal |
| Coaxial | Legado em LAN; ainda em TV a cabo/HFC |
| **Fibra óptica** | Luz por **reflexão total**; imune a interferência eletromagnética; longas distâncias |
| Sem fio | Rádio (Wi-Fi, celular), micro-ondas, satélite, infravermelho |

| Fibra | Núcleo | Fonte | Distância | Classes |
|---|---|---|---|---|
| **Monomodo (SMF)** | **~8–10 µm** (um único modo de propagação) | **Laser** | **Longas** (dezenas de km) | OS1, OS2 |
| **Multimodo (MMF)** | **50 ou 62,5 µm** (vários modos → **dispersão modal**) | **LED / VCSEL** | **Curtas** (centenas de metros) | OM1 a OM5 |

| Comutação | Funcionamento | Exemplo |
|---|---|---|
| **Circuitos** | Caminho **dedicado** estabelecido antes da comunicação; recursos reservados; atraso constante | Telefonia tradicional (PSTN) |
| **Pacotes** | Dados divididos em pacotes de tamanho variável, roteados independentemente (*store-and-forward*); compartilhamento estatístico | Internet (IP) |
| **Células** | Pacotes de **tamanho fixo e pequeno** — **ATM: 53 bytes (5 de cabeçalho + 48 de dados)**; comutação rápida em hardware, QoS | ATM |

## 2. Tipos de redes por abrangência
| Sigla | Abrangência | Tecnologias |
|---|---|---|
| **PAN / WPAN** | Pessoal (poucos metros) | USB / **Bluetooth (IEEE 802.15.1)**, **Zigbee (802.15.4)**, NFC |
| **LAN / WLAN** | Local (prédio, campus) | **Ethernet (802.3)** / **Wi-Fi (802.11)** |
| **MAN / WMAN** | Metropolitana (cidade) | Metro Ethernet, fibra / **WiMAX (802.16)** |
| **WAN / WWAN** | Longa distância (países) | MPLS, links dedicados, SD-WAN / **celular (4G LTE, 5G)**, satélite |

## 3. Elementos de interconexão
| Equipamento | Camada OSI | Função |
|---|---|---|
| **Repetidor / hub** | **1 (física)** | Regenera/repete o sinal para todas as portas; hub = **um único domínio de colisão** |
| **Bridge / switch** | **2 (enlace)** | Encaminha **quadros por endereço MAC** (tabela CAM); **cada porta é um domínio de colisão**; um domínio de **broadcast** (salvo VLANs) |
| **Roteador** | **3 (rede)** | Encaminha **pacotes por IP** entre redes; **separa domínios de broadcast** |
| Switch L3 | 2 e 3 | Comutação + roteamento entre VLANs |
| **Gateway** | 4 a 7 (todas) | Interliga redes com **protocolos diferentes**, traduzindo (ex.: gateway de aplicação) |
| Access point | 2 | Ponte entre rede sem fio e cabeada |

## 4. Modelo OSI × TCP/IP
| OSI | TCP/IP | PDU | Exemplos |
|---|---|---|---|
| 7 Aplicação · 6 Apresentação · 5 Sessão | **Aplicação** | Dados/mensagem | HTTP, DNS, SMTP, FTP, SSH, LDAP, DHCP, SNMP |
| 4 Transporte | **Transporte** | **Segmento** (TCP) / datagrama (UDP) | TCP, UDP |
| 3 Rede | **Internet** | **Pacote** | IP, ICMP, IPsec, OSPF, BGP, EIGRP |
| 2 Enlace · 1 Física | **Acesso à rede** (enlace + física) | **Quadro** / bits | Ethernet, Wi-Fi, ARP*, PPP |

### TCP × UDP
- **TCP**: orientado à conexão (**three-way handshake: SYN → SYN+ACK → ACK**; encerramento com FIN/ACK), **confiável** (números de sequência, ACKs, retransmissão), **controle de fluxo** (janela deslizante) e **de congestionamento** (*slow start*, *congestion avoidance*), entrega **ordenada**. Flags: SYN, ACK, FIN, **RST** (reinicia/aborta), PSH, URG.
- **UDP**: sem conexão, sem garantia, **cabeçalho de 8 bytes**, baixa latência — DNS (consultas), DHCP, SNMP, TFTP, VoIP/RTP, streaming, **QUIC** (HTTP/3).

## 5. Endereçamento IPv4
- 32 bits; classes (legado): A (1–126, /8), B (128–191, /16), C (192–223, /24), D (multicast 224–239), E (240–255). **127.0.0.0/8** = loopback; **169.254.0.0/16** = APIPA; **0.0.0.0** = rota padrão / "este host".
- **Privados (RFC 1918)**: **10.0.0.0/8**, **172.16.0.0/12**, **192.168.0.0/16**. **CGNAT**: 100.64.0.0/10. **NAT/PAT** traduz privados para público.
- **Hosts por sub-rede = 2^(32−n) − 2**. Tamanho do bloco no octeto de interesse = **256 − valor da máscara** nesse octeto.

**Sub-rede — método rápido** (ex.: 192.168.15.0/24 segmentada com máscara 255.255.255.192 = /26):
- Bloco = 256 − 192 = **64** → sub-redes: **.0, .64, .128, .192** (4 sub-redes de 62 hosts).
- **4ª sub-rede = 192.168.15.192/26** (hosts .193 a .254; broadcast .255).
- Para um host, ache o múltiplo do bloco imediatamente abaixo: 192.168.15.**100**/26 → rede .64, broadcast .127.
- **VLSM**: sub-redes de tamanhos diferentes (aloque da maior para a menor); /30 (ou /31) para enlaces ponto a ponto.

## 6. IPv6
- **128 bits**, **8 grupos de 16 bits** em hexadecimal separados por `:`. Abreviação: omitir **zeros à esquerda** em cada grupo e substituir **uma única** sequência de grupos zerados por **`::`**. Ex.: `2001:0db8:0000:0000:0000:ff00:0042:8329` → `2001:db8::ff00:42:8329`.
- Tipos: **unicast global** (2000::/3), **link-local** (**fe80::/10**, obrigatório em toda interface), **unique local** (fc00::/7 — equivalente a privado), **multicast** (**ff00::/8**), **anycast**; **loopback `::1`**; não especificado `::`. **Não há broadcast**.
- Cabeçalho base **fixo de 40 bytes**, com **cabeçalhos de extensão**; **sem checksum** no cabeçalho; **fragmentação só na origem** (PMTUD); campo **Flow Label**; *Hop Limit* (equivale ao TTL).
- **NDP** (ICMPv6) substitui o ARP (mensagens RS, RA, NS, NA, Redirect); autoconfiguração **SLAAC** (prefixo do RA + identificador de interface — EUI-64 ou aleatório) e/ou **DHCPv6**.
- Transição: **pilha dupla (dual stack)**, **túneis** (6to4, 6in4, Teredo), **tradução** (NAT64/DNS64).
- **Sub-redes IPv6** — a partir de um /48, há 16 bits (49 a 64) para sub-redes /64. Ex. FCC: dividir **2001:db8:acad::/48** em **4** sub-redes (mesmo número das sub-redes IPv4 /26) → usam-se **2 bits** (prefixo **/50**); o 4º grupo varia nos 2 bits mais altos: **0000, 4000, 8000, c000** → **4ª sub-rede = 2001:db8:acad:c000::/50**.

## 7. DNS e entidades de registro
- Hierarquia: **raiz (.)** → **TLDs** (genéricos .com, .org; de país **.br**) → domínios → subdomínios. Servidores **raiz** (13 identidades lógicas, A–M, com anycast), **TLD**, **autoritativos** (primário/secundário) e **resolvedores recursivos** (cache, TTL).
- Consulta **recursiva** (cliente → resolvedor) × **iterativa** (resolvedor → raiz → TLD → autoritativo). Transporte: **UDP 53**; **TCP 53** para respostas grandes e **transferência de zona** (AXFR completa, IXFR incremental).
- Registros: **A** (IPv4), **AAAA** (IPv6), **CNAME** (alias), **MX** (servidor de e-mail, com prioridade), **NS** (servidores autoritativos), **PTR** (reverso — `in-addr.arpa` / `ip6.arpa`), **SOA** (início de autoridade: serial, refresh, retry, expire, TTL mínimo), **TXT** (SPF, DKIM, DMARC, verificações), **SRV** (serviços — ex.: localizar DCs do AD), **CAA** (ACs autorizadas a emitir certificados).
- **DNSSEC**: assinaturas digitais (RRSIG, DNSKEY, DS) garantem **autenticidade e integridade** das respostas (não confidencialidade). DoH/DoT: DNS sobre HTTPS/TLS (privacidade).
- **Entidades de registro**: **ICANN** (coordenação global de nomes e números) e **IANA** (raiz, alocação de blocos aos **RIRs**); RIR da América Latina: **LACNIC**; no Brasil, o **NIC.br** (braço executivo do **CGI.br**) opera o **Registro.br** (registro de domínios **.br**) e distribui endereços IP/ASN; **gov.br** e **jus.br** são domínios de categoria restrita a órgãos públicos.

## 8. Protocolos do edital
| Protocolo | Porta | Destaques |
|---|---|---|
| **HTTP** | 80 (HTTPS 443) | Sem estado; métodos; HTTP/1.1 (conexões persistentes), **HTTP/2** (binário, **multiplexação**, compressão de cabeçalhos HPACK), **HTTP/3** (sobre **QUIC/UDP**) |
| **FTP** | **21** (controle) e **20** (dados no modo ativo) | **Ativo**: servidor conecta ao cliente (problema com NAT/firewall) × **passivo**: cliente abre as duas conexões; texto claro → use **SFTP** (sobre SSH, porta 22) ou **FTPS** |
| **SSH** | 22 | Acesso remoto seguro; autenticação por senha ou **chave pública**; túneis (*port forwarding*); SCP/SFTP |
| **SMTP** | 25 (relay entre servidores), **587** (submissão com STARTTLS), 465 (SMTPS) | Envio; comandos HELO/EHLO, MAIL FROM, RCPT TO, DATA |
| **POP3** | 110 / **995** (SSL) | Baixa as mensagens (em geral remove do servidor) |
| **IMAP** | 143 / **993** (SSL) | Sincroniza; mensagens ficam no servidor (pastas, vários dispositivos) |
| **LDAP** | **389** / LDAPS **636** | Acesso a diretórios (AD, OpenLDAP); DN, árvore (dc, ou, cn); operações bind, search, add, modify |
| **DNS** | 53 UDP/TCP | Ver acima |
| **DHCP** | 67 (servidor) / 68 (cliente) UDP | **DORA**: Discover → Offer → Request → Ack; **concessão (lease)**; **relay agent** (*ip helper*) leva o broadcast a outra sub-rede; opções (gateway, DNS, domínio) |
| **ARP** | — (camada 2/3) | Descobre o **MAC** a partir do IP (requisição em **broadcast**, resposta unicast); cache ARP; **ARP spoofing** (ataque MITM); RARP (inverso, obsoleto) |
| **IPsec** | IKE: **UDP 500**; NAT-T **UDP 4500** | Segurança na **camada de rede**: **AH** (protocolo IP **51** — integridade e autenticação da origem, **sem confidencialidade**) e **ESP** (protocolo IP **50** — **confidencialidade** + integridade); modos **transporte** (protege a carga útil — host a host) e **túnel** (encapsula o pacote inteiro — VPN site a site); **SA** (associação de segurança), **IKEv2** |

## 9. Cabeamento estruturado — ABNT NBR 14565:2019
- **Subsistemas**: **cabeamento de backbone de campus** (entre edifícios), **cabeamento de backbone de edifício** (entre andares) e **cabeamento horizontal** (do distribuidor de piso às tomadas).
- **Elementos funcionais**: **distribuidor de campus (CD)**, **distribuidor de edifício (BD)**, **distribuidor de piso (FD)**, **ponto de consolidação (CP)** opcional, **tomada de telecomunicações (TO)**, **tomada multiusuário (MUTO)**, **área de trabalho**. Também: sala de equipamentos, sala de telecomunicações, infraestrutura de entrada.
- **Distâncias (cobre)**: **canal horizontal máximo = 100 m** = **até 90 m de enlace permanente** (cabo fixo) + **até 10 m** de cordões (*patch cords*) somados nas duas pontas.
- **MUTO** (cobrado pela FCC): atende **no máximo 12 áreas de trabalho**; os cordões da área de trabalho podem chegar a **20 m** (com redução do comprimento do cabo horizontal para manter o canal dentro do limite); deve ficar em local permanente e acessível.
- **Ponto de consolidação**: a pelo menos **15 m** do distribuidor de piso; no máximo um por enlace.
| Categoria do componente | Classe do canal | Banda | Aplicação típica |
|---|---|---|---|
| Cat 5e | D | 100 MHz | 1 Gbps |
| **Cat 6** | **E** | **250 MHz** | 1 Gbps (10 Gbps até ~55 m) |
| **Cat 6A** | **EA** | **500 MHz** | **10GBASE-T até 100 m** |
| Cat 7 / 7A | F / FA | 600 / 1000 MHz | Blindados |
| Cat 8.1 / 8.2 | I / II | 2000 MHz | 25/40GBASE-T até **30 m** (data centers) |
- Pinagem **T568A** (1-2 verde, 3-6 laranja) e **T568B** (1-2 laranja, 3-6 verde); cabo direto (mesmo padrão nas pontas) × crossover. Certificação de enlaces (atenuação, NEXT, perda de retorno). (Confirme no texto da norma requisitos mínimos de categoria por ambiente.)

## 10. Padrões IEEE de enlace
### IEEE 802.3 (Ethernet)
- Acesso **CSMA/CD** (half-duplex; em full-duplex não há colisões). **Quadro**: preâmbulo (7) + SFD (1) + MAC destino (6) + MAC origem (6) + EtherType/tamanho (2) + **dados (46 a 1500 bytes — MTU)** + **FCS (4, CRC)** → quadro de **64 a 1518 bytes** (1522 com tag 802.1Q). **Jumbo frames** ~9000.
- Padrões: **802.3u** (Fast Ethernet, 100BASE-TX), **802.3ab** (1000BASE-T, cobre), **802.3z** (1000BASE-SX/LX, fibra), **802.3an** (10GBASE-T), 802.3ae (10 Gb fibra), **802.3af/at/bt** (**PoE** ~15,4 W / **PoE+** ~30 W / **PoE++** 60–90 W), **802.3ad** (agregação de enlaces **LACP**, hoje 802.1AX).
- Endereço **MAC**: 48 bits; 24 primeiros = **OUI** (fabricante); `FF:FF:FF:FF:FF:FF` = broadcast.

### IEEE 802.1Q (VLAN)
- Insere uma **tag de 4 bytes** no quadro: TPID `0x8100` + **PCP (3 bits — prioridade 802.1p, QoS)** + DEI (1 bit) + **VID (12 bits → 4096 valores; 1–4094 utilizáveis)**.
- Porta **access** (uma VLAN, sem tag) × **trunk** (várias VLANs, com tag); **VLAN nativa** trafega **sem tag** no trunk. Comunicação **entre VLANs** exige **roteamento** (roteador ou switch L3 — *router-on-a-stick*).

### IEEE 802.1X (controle de acesso à rede por porta — NAC)
- Papéis: **suplicante** (dispositivo do usuário) → **autenticador** (switch ou AP) → **servidor de autenticação** (**RADIUS**). Até autenticar, a porta só permite tráfego **EAPOL** (EAP sobre LAN).
- Métodos EAP: **EAP-TLS** (certificados nos dois lados — o mais forte), **PEAP** e EAP-TTLS (túnel TLS + senha), EAP-FAST. Base do **WPA2/WPA3-Enterprise**.

### Spanning Tree (STP — IEEE 802.1D) e Rapid STP (802.1w)
- Objetivo: **evitar loops** de camada 2 em topologias com redundância (tempestades de broadcast, instabilidade da tabela MAC), bloqueando portas redundantes.
- **Eleição da root bridge**: menor **Bridge ID** = **prioridade (padrão 32768, múltiplos de 4096)** + **MAC**. Cada switch não raiz escolhe sua **porta raiz** (menor custo até a raiz); cada segmento tem uma **porta designada**; as demais ficam **bloqueadas**.
- **BPDUs** a cada **2 s** (hello). Timers: hello 2 s, **forward delay 15 s**, **max age 20 s** → convergência **30 a 50 s**.
| | **STP (802.1D)** | **RSTP (802.1w)** |
|---|---|---|
| Estados das portas | **Blocking, Listening, Learning, Forwarding** (+ Disabled) | **Discarding, Learning, Forwarding** |
| Papéis | Root, Designated, (Blocked) | Root, Designated, **Alternate** (backup da porta raiz), **Backup** |
| Convergência | 30–50 s | **Rápida** (poucos segundos ou menos) — handshake proposta/acordo, **portas de borda (edge)** ≈ PortFast |
- **MSTP (802.1s)**: várias instâncias de spanning tree mapeadas a grupos de VLANs. Proteções: BPDU Guard, Root Guard.

## 11. Redes sem fio IEEE 802.11
| Padrão | Nome comercial | Faixas | Destaques | Taxa teórica |
|---|---|---|---|---|
| 802.11n | Wi-Fi 4 | 2,4 e 5 GHz | MIMO, canais de 40 MHz | 600 Mbps |
| **802.11ac** | **Wi-Fi 5** | **5 GHz** | **MU-MIMO (downlink)**, canais até **160 MHz**, **256-QAM**, *beamforming* | ~6,9 Gbps |
| **802.11ax** | **Wi-Fi 6 / 6E** | 2,4 e 5 GHz (**6E: + 6 GHz**) | **OFDMA**, MU-MIMO **uplink e downlink**, **1024-QAM**, **TWT** (economia de energia), **BSS Coloring** (reduz interferência) — foco em **ambientes densos** | ~9,6 Gbps |
| **802.11be** | **Wi-Fi 7** | 2,4, 5 e 6 GHz | Canais de **320 MHz**, **4096-QAM**, **MLO (Multi-Link Operation** — usa várias faixas simultaneamente), latência menor | ~46 Gbps |
- Acesso ao meio: **CSMA/CA** (evita colisões; RTS/CTS para o problema do terminal oculto). SSID, BSS/ESS, *roaming*; canais não sobrepostos em 2,4 GHz: **1, 6 e 11**.

## ⚠️ Pegadinhas
1. Hub = 1 domínio de colisão; switch = 1 por porta; **roteador separa broadcast**.
2. ATM: células de **53 bytes**.
3. Hosts = 2^(32−n) − 2; bloco = 256 − máscara. 4ª sub-rede /26 de 192.168.15.0 = **.192**.
4. IPv6: `::` **uma vez**; link-local **fe80::/10**; **sem broadcast**; NDP no lugar do ARP; cabeçalho de 40 bytes sem checksum.
5. IPsec **AH = 51 (sem cifra)**; **ESP = 50 (com cifra)**.
6. NBR 14565: canal **100 m = 90 + 10**; **MUTO: até 12 áreas, cordão até 20 m**.
7. STP: root = **menor** Bridge ID; RSTP tem **discarding**, **alternate** e **backup**.
8. 802.1X: suplicante–autenticador–**RADIUS**. 802.1Q: VID de **12 bits**.
9. Wi-Fi 6 = **OFDMA** e TWT; Wi-Fi 6**E** = **6 GHz**; Wi-Fi 7 = **MLO** e 320 MHz.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** A rede 172.20.32.0/20 foi dividida em sub-redes /23. O número de sub-redes obtidas e o endereço de broadcast da terceira sub-rede são, respectivamente:
(A) 4 e 172.20.37.255. (B) **8 e 172.20.37.255.** (C) 8 e 172.20.35.255. (D) 16 e 172.20.37.255. (E) 8 e 172.20.39.255.
✅ **B.** /20 → /23 = 3 bits = 8 sub-redes de 512 endereços (2 no 3º octeto): .32–.33, .34–.35, **.36–.37** → broadcast 172.20.37.255.

**Q2.** No IPv6, a forma abreviada correta de `2001:0db8:0000:0000:0001:0000:0000:0001` é:
(A) `2001:db8::1::1`. (B) **`2001:db8::1:0:0:1`** (ou `2001:db8:0:0:1::1`). (C) `2001:db8:0:1:1`. (D) `2001:db8::11`. (E) `2001:0db8::0001::0001`.
✅ **B.** `::` só pode aparecer **uma vez** (A e E inválidas); C e D perdem grupos.

**Q3.** No protocolo IPsec, o cabeçalho que provê integridade e autenticação da origem, mas não confidencialidade, é o:
(A) ESP. (B) IKE. (C) **AH.** (D) ISAKMP. (E) SA.
✅ **C.**

**Q4.** No IEEE 802.1X, o elemento que intermedeia a autenticação, normalmente um switch ou ponto de acesso, e repassa as mensagens EAP ao servidor RADIUS é o:
(A) suplicante. (B) **autenticador.** (C) servidor de autenticação. (D) controlador de domínio. (E) proxy reverso.
✅ **B.**

**Q5.** No RSTP (IEEE 802.1w), a porta que fornece um caminho alternativo para a root bridge, pronta para assumir caso a porta raiz falhe, recebe o papel de:
(A) designated. (B) backup. (C) edge. (D) **alternate.** (E) disabled.
✅ **D.** (Backup = redundância para uma porta designada no mesmo segmento.)

**Q6.** Recurso introduzido no IEEE 802.11be (Wi-Fi 7) que permite a um dispositivo transmitir e receber simultaneamente em múltiplas faixas e canais:
(A) OFDMA. (B) TWT. (C) BSS Coloring. (D) **MLO (Multi-Link Operation).** (E) MU-MIMO downlink.
✅ **D.**
