# Varredura dos testbeds do OpenRAN@Brasil e o questionário dos perfis

Levantamento de 12/11/2026 em fontes públicas do programa OpenRAN@Brasil (RNP, CPQD) e em trabalhos feitos no testbed. O objetivo é responder antecipadamente, onde for possível, as 13 perguntas de [`QUESTIONARIO_PERFIS_TESTBED.md`](QUESTIONARIO_PERFIS_TESTBED.md).

Nenhuma resposta daqui fecha um campo `A_CONFIRMAR`: elas descrevem o testbed nacional, não a instalação de cada laboratório. Servem para fazer perguntas mais precisas e para antecipar riscos. Com o testbed nacional, o laboratório pode confirmar ou corrigir cada uma.

## 1. Ilhas e participantes

| Ilha | Situação | Fonte |
| :-- | :-- | :-- |
| CPQD, Campinas (SP) | operacional desde a Fase 1 | [Sobre][sobre]; [Leonardo e Daniel, WRNP][wrnp1] |
| RNP, Rio de Janeiro (RJ) | operacional desde a Fase 1; ligada a Campinas por 10 Gb/s (397 km) | [WRNP][wrnp1] |
| UFG, Goiânia (GO) | operacional até junho de 2026 (previsão da página); hospeda HADES 5G e MEI5GO | [Sobre][sobre] |
| PoP-PA e UFPA (Norte) | novo hospedeiro, coordenação Aldebaro Klautau; hospeda o **GreenRAN** | [Resultado final, 18/03/2026][resultado] |
| UFRN (Nordeste) | novo hospedeiro, coordenação Augusto Neto; hospeda o Sentinel-5GO | [Resultado final][resultado] |
| PoP-RS, UFRGS, Unisinos, UFCSPA, PUC-RS (Sul) | novo hospedeiro, coordenação César Hass; hospeda o OpenHealth5G | [Resultado final][resultado] |
| UnB (Centro-Oeste) | sandbox regulatório | [Workshop da Fase 3][workshop3] |

- **Requisitos para hospedar uma ilha:** pelo menos 10 Gb/s de ligação com a RNP, climatização, energia e espaço para antenas ([chamada][chamada]; [workshop da Fase 3][workshop3]).
- **Acesso ao testbed:** só para fins científicos, de pesquisa e de educação, mediante uma proposta avaliada pela equipe do programa ([Utilize o testbed][utilize]).

## 2. O que o testbed oferece (Anexo IV, setembro de 2025)

A fonte mais detalhada é o [Anexo IV da chamada da Fase 3, "Capacidade do testbed"][anexo4]:

| Item | OAI RAN | srsRAN Project |
| :-- | :-- | :-- |
| Duplexação e banda | TDD e FDD; SCS de 15 e 30 kHz em n78; 10 a 100 MHz; MIMO 4x4 | TDD e FDD em todas as bandas FR1; até 100 MHz (TDD) e 50 MHz (FDD); MIMO 4x4; 3GPP Rel. 17 |
| Split | F1 (CU/DU) | 7.2x para RUs, 8 para USRP; CU/DU separados |
| Near-RT RIC | FlexRIC | OSC RIC e FlexRIC |
| E2SM-KPM | REPORT Style 4 | Styles 1 a 5 |
| E2SM-RC | CONTROL Style 1; REPORT Styles 1 e 4 | **CONTROL Style 2** |
| Slicing | não listado | listado |
| O1/NETCONF | a testar | a desenvolver |
| Implantação | Kubernetes (Helm ou KPT) | Kubernetes (Helm ou KPT) |

O anexo também lista o que falta desenvolver:
- **OAI:** interoperabilidade com as RUs Foxconn, integração com o OSC RIC, mais métricas KPM e outros estilos de KPM e RC.
- **srsRAN:** interoperabilidade com CU/DU de outros fornecedores, mais métricas KPM, outros estilos de RC e a interface O1.

Outras peças do testbed:
- **Pilha comercial:** a da Radisys, avaliada pelo CPQD. A CU fala E2AP e a OAM usa YANG/NETCONF ([Anexo IV][anexo4]).
- **RU:** Foxconn RPQN 7801e, em testes de interoperabilidade com CU/DU do OAI ([nota OAI][oai]). Na Fase 2 está em desenvolvimento uma O-RU nacional baseada no Evenstar: n78, 4T4R, 20 W por antena ([proposta Fyuz 2024][fyuz]).
- **Núcleos:** Open5GS e OAI-CN, com o Free5GC planejado. A integração do núcleo OAI com CU/DU do srsRAN chegou a cerca de 1 Gb/s de downlink ([nota OAI][oai]).
- **Ambiente de xApps:** o [OpenRAN@Brasil Blueprint][blueprint] (UFG, UTFPR, Unisinos, UFPA) é uma VM com o Near-RT RIC do OSC e o e2sim. O README não diz a release do RIC nem as versões de E2AP e E2SM.

## 3. Trabalhos já feitos no testbed

| Trabalho | Pilha usada | Interesse para o GreenRAN | Fonte |
| :-- | :-- | :-- | :-- |
| GT IQoS (UFPA, coord. André Riker): xApp classificadora e gerenciadora de fatias | versão final em **srsRAN + OSC RIC + Open5GS**, depois de testar vários RICs e pilhas | A xApp troca a fatia do UE mudando o SST da sessão PDU **no núcleo**, e não por cota de PRB via RC. Entradas: vazão UL/DL e PRBs (KPM). Mesmo grupo da reunião do GreenRAN. | [III Workshop Open RAN Brasil][iqos]; [minicurso SBrT 2025][minicurso] |
| CPQD: implantação e testes de RICs | µONOS-RIC (ONF), OSC RIC e FlexRIC | Monitoramento com kpimon-go e e2-sim; slicing pelas xApps RSM (ONF) e `xapp_slice_moni_ctrl` (FlexRIC). Registra que o Non-RT RIC ainda não estava maduro para testes. | [WTestbeds 2023][wtestbeds] |
| Observabilidade no testbed da RNP (WGRS 2026) | srsRAN, com proxies Zabbix | Coleta métricas de **consumo de energia**, tráfego e hardware de antena em RU, DU e CU. Pode ser o caminho para o gate GR4. | [WGRS 2026][wgrs] |
| GERCOM (NOMS 2025, demo) | Open5GS e srsRAN em clusters Kubernetes diferentes, com Nephio | Mesma equipe do perfil srsRAN; mostra a pilha que o laboratório já opera. | [GERCOM][gercom-noms] |
| GT FAIR-5G (UFPB) | testes de vulnerabilidade e incidentes em 5G (inundação, ataques a fatias) | Ponto de partida para o grupo de segurança. | [minicurso SBrT 2025][minicurso] |
| NORI (SBrT) | ns-3 com o Near-RT RIC do OSC, sobre a infraestrutura do OpenRAN@Brasil | É a bancada de referência da RDL ([`nori_ns3.yaml`](../../configs/testbed_ufpa/backends/nori_ns3.yaml)). | [SBrT 4946][nori] |

## 4. Cruzamento com o questionário

**Legenda:** **indicativo** = o testbed nacional responde, falta o laboratório confirmar; **aberto** = nenhuma fonte responde; **risco** = a fonte aponta uma lacuna que afeta a RDL.

| # | Pergunta | srsRAN (GERCOM) | OAI + FlexRIC (LACIS) |
| --: | :-- | :-- | :-- |
| 1 | Versões da pilha e do núcleo | aberto (nenhuma fonte dá tag ou commit); núcleo indicativo: Open5GS (GT IQoS, demo NOMS) | aberto; núcleo indicativo: OAI-CN ou Open5GS |
| 2 | RAN-CodeUpdates do GreenRAN | não se aplica | aberto |
| 3 | Qual Near-RT RIC | indicativo: **OSC RIC** (GT IQoS, Blueprint) | **risco:** o testbed usa **FlexRIC** com o OAI, e a integração do OAI com o OSC RIC ainda precisa melhorar (Anexo IV). Com FlexRIC, as xApps falam E42 e não RMR, e a RDL não entra sem ponte. |
| 4 | Versão do E2AP | aberto | aberto |
| 5 | Endereço do E2Term | depende da instalação | depende da instalação |
| 6 | Versão do KPM e RAN Function ID | indicativo: KPM Styles 1 a 5 (v3.00 em trabalho externo, [xDevSM][xdevsm]); ID aberto | indicativo: só REPORT Style 4; ID aberto |
| 7 | Métricas KPM | indicativo: o srsRAN expõe mais métricas que o OAI ([xDevSM][xdevsm]); conferir os nomes 3GPP | **risco:** o próprio testbed lista o aumento das métricas KPM como pendência |
| 8 | Fatia do UE no KPM | aberto; o GT IQoS identifica a fatia pelo SST no núcleo, não pelo KPM | aberto |
| 9 | Versão do RC e RAN Function ID | indicativo: RC CONTROL Style 2; ID aberto | indicativo: CONTROL Style 1 e REPORT 1 e 4; ID aberto |
| 10 | Cota de PRB por fatia (Style 2, Action 6) | indicativo positivo: Style 2 é o estilo da cota de PRB e o srsRAN lista slicing. Confirmar a Action 6 e o leiaute (aninhado ou plano). | **risco:** sem RC Style 2; o slicing passa pelo SM próprio do FlexRIC (`xapp_slice_moni_ctrl`). O codec da RDL não cobre isso. |
| 11 | IDs dos RAN Parameters | aberto (depende do leiaute) | depende da resposta 10 |
| 12 | Canal de potência de TX | **risco:** O1 ainda a desenvolver; nenhuma fonte cita E2SM-CCC | **risco:** O1/NETCONF ainda a testar |
| 13 | Canal de liga/desliga de célula | **risco:** idem; provavelmente configuração com reinício | **risco:** idem |

## 5. Consequências para o GreenRAN e a RDL

1. **srsRAN com OSC RIC é o caminho mais curto** para a RDL no testbed. É a combinação que o GT IQoS e o Blueprint já usam, e o srsRAN anuncia RC CONTROL Style 2. O ponto a confirmar é se a Action 6 vem no leiaute aninhado da norma, que o codec ainda não aceita.
2. **No OAI, a RDL depende de uma escolha do laboratório.** Uma opção é o OSC RIC, com integração ainda imatura. A outra é o FlexRIC, que exige uma ponte E42 ↔ RMR ou rodar a RDL como xApp do FlexRIC. Essa mesma ponte aparece no desenho das xApps originais em malha fechada (doc 16), porque o xSlice e o Energy Saving originais são xApps do FlexRIC.
3. **Potência e desligamento de célula (atividades A1.2 e A1.3) não têm canal no testbed hoje.** Nenhuma pilha aberta oferece O1 pronto, e nenhuma fonte cita E2SM-CCC. Isso afeta diretamente a xApp2-EnergySaver: no testbed, ela começaria só com a cota de PRB, ou com a reconfiguração da célula fora do laço E2.
4. **A medição de energia já existe em parte.** A observabilidade com Zabbix da ilha da RNP (WGRS 2026) coleta consumo de energia de RU, DU e CU, e pode alimentar o gate GR4. Vale perguntar à ilha da UFPA se terá o mesmo.
5. **Há trabalho anterior do próprio grupo para aproveitar.** O GT IQoS da UFPA já integrou uma xApp de fatiamento ao OSC RIC com srsRAN no testbed. O código e a configuração desse trabalho respondem às perguntas 3 a 9 para o srsRAN mais rápido que qualquer captura.

## 6. O que nenhuma fonte responde

- Versões exatas (tags e commits) de srsRAN, OAI, FlexRIC e do OSC RIC, e as versões de E2AP, KPM e RC.
- RAN Function IDs e IDs dos RAN Parameters.
- Leiaute da cota de PRB no srsRAN.
- Equipamentos da ilha Norte (PoP-PA/UFPA).

Não foi possível ler:
- o relatório de disseminação da Fase 3 (PDF acima de 10 MB);
- os artigos da IEEE Communications Magazine e do MobiCom 2024 sobre o testbed (acesso negado pela ACM);
- o artigo SBrT 4799 (conexão recusada).

Esses documentos podem trazer parte do que falta.

## 7. Testbed sem fatiamento: propostas (2026-11-12)

**Informe:** em 2026-11-12, a equipe do GreenRAN informou que o testbed **não terá suporte a fatiamento** (slicing). A reunião do grupo já tinha registrado que a ilha OpenRAN não traz fatiamento nativo e que ele exigiria desenvolvimento interno ou colaboração com outros grupos.

**Ainda falta confirmar:**

- o que exatamente falta: várias fatias no gNB (lista de S-NSSAI), a cota de PRB por fatia do RC (Style 2, Action 6) ou a métrica KPM por fatia;
- em qual equipamento: a ilha do GreenRAN, a pilha comercial ou o srsRAN do GERCOM;
- se o núcleo aceita mais de um S-NSSAI, com QoS ou AMBR por fatia.

**O que muda para a RDL:** a arbitragem não depende de fatiamento, porque a cota por fatia é só um dos cinco parâmetros controlados (`src/e2/rc/control_parameter.py`). Ficam afetados:

- o papel do xSlice e o xApp1-RANSlicer, que é um entregável do GreenRAN;
- os cenários com `PRB_QUOTA` por fatia: S0, S1, S2, S6, S7, S8, S12, S14 e G1;
- o gate TB7, que previa a arbitragem entre o RANSlicer e o EnergySaver.

Somado à falta de canal de potência e de desligamento (§5, item 3), o testbed pode ficar sem nenhuma alavanca de energia nem de fatia via E2.

| # | Proposta | Como funciona | Custo e risco |
| :-- | :-- | :-- | :-- |
| P1 | Fatia no núcleo (5GC) | A xApp ou a rApp decide a fatia, e a troca acontece no núcleo, pelo SST/S-NSSAI da sessão PDU. Cada fatia tem seu DNN, sua UPF e um AMBR/QoS próprio no Open5GS. É o que o GT IQoS da UFPA já fez em srsRAN, OSC RIC e Open5GS (§3). A RDL ganha um parâmetro `SLICE_ASSIGN` e um atuador para o núcleo. | Médio. Reaproveita trabalho do grupo. A troca leva segundos (reanexa a sessão), então o laço fica mais perto do Non-RT/A1 do que da janela de 200 ms. |
| P2 | Fatia lógica no escalonador | A fatia vira um grupo de UEs. A cota do RANSlicer se traduz em pesos ou prioridades por UE (5QI/ARP/GBR ou `SCHEDULER_WEIGHT`, que já está no catálogo da RDL). | Baixo na RDL. Depende de o srsRAN aceitar controle por UE via RC, o que não está confirmado. |
| P3 | Teto de PRB da célula, sem fatias | Mesma semântica do ns-3, onde o `PRB_QUOTA` é uma máscara de RBGs da célula inteira (`simulations/ns3/rdl-nr-common.h`), e não uma cota por fatia. No testbed, vira a ação de cota do RC com uma única fatia padrão ou o limite de PRB da célula. O conflito entre energia e capacidade continua. | Baixo. Exige que o RC aceite a cota, mesmo com uma fatia só. |
| P4 | Desenvolver o fatiamento na pilha aberta | O srsRAN lista fatiamento (§2). No OAI, ele passa pelo SM próprio do FlexRIC. Coincide com os entregáveis de código de fatiamento junto com a ASSE. | Alto e longo. É contribuição do grupo ao projeto, não da RDL. |
| P5 | Separar a evidência | O fatiamento na RAN é avaliado no ns-3 em malha fechada, com o xSlice original e o RANSlicer ([doc 16](../16_xapps_originais_malha_fechada.md)). O testbed valida a cadeia real com parâmetros sem fatia, e o TB7 passa a ser a arbitragem entre o EnergySaver e o Traffic Steering. | Baixo, desde que os artigos digam onde cada coisa foi medida. |
| P6 | Fatias em outro laboratório | OAI + FlexRIC (LACIS), com `xapp_slice_moni_ctrl`. | Exige a ponte E42 ↔ RMR (doc 16). |

**Recomendação:**

- **P3 imediatamente:** mantém o conflito de PRB sem fatias.
- **P1 junto com o GT IQoS:** preserva o entregável do RANSlicer, com fatia real no núcleo.
- **P5 como regra de relato nos artigos.**
- **P2 como complemento**, se o srsRAN aceitar controle por UE.
- **P4 fica como objetivo de longo prazo do projeto.**

Se a única coisa que falta for a cota por fatia, o P3 sozinho resolve a maior parte.

## Fontes

[sobre]: https://openranbrasil.org.br/sobre/
[utilize]: https://openranbrasil.org.br/utilize-o-testbed/
[oai]: https://openranbrasil.org.br/openranbrasil-avanca-em-inovacao-com-suporte-a-pilha-open-source-openairinterface-oai/
[workshop3]: https://openranbrasil.org.br/openranbrasil-avanca-para-fase-de-aplicacoes-e-realiza-workshop-presencial-da-fase-3/
[resultado]: https://openranbrasil.org.br/wp-content/uploads/2026/02/resultadosFinais-ChamadaOpenRAN-Aplicacao-Hospedeiros_VF.pdf
[chamada]: https://www.rnp.br/chamadas-publicas/chamada-publica-para-expansao-do-testbed-do-openranbrasil/
[anexo4]: https://plataforma.rnp.br/arquivos/documents/Anexo%20IV%20-%20Capacidades%20do%20Testbed.pdf?VersionId=rHnosLDConXIm0762LSbRQIkM1MmcoVc
[fyuz]: https://www.rnp.br/wp-content/uploads/2024/09/Proposal-OpenRAN@Brasil-Fyuz-2024-Updated-Version-2.pdf
[wrnp1]: https://indico.rnp.br/event/106/contributions/890/attachments/344/549/OpenRAN_-_Leonardo__Daniel.pdf
[iqos]: https://indico.rnp.br/event/129/contributions/911/attachments/305/475/III-Workshop-OpenRAN_1.pdf
[minicurso]: https://www.sbrt.org.br/sbrt2025/wp-content/uploads/2025/10/Minicurso-OpenRAN-SBrT.pdf
[wtestbeds]: https://sol.sbc.org.br/index.php/wtestbeds/article/download/24813/24634/
[wgrs]: https://sol.sbc.org.br/index.php/wgrs/article/view/42567
[gercom-noms]: https://gercom.ufpa.br/advancing-open-ran-deployment-and-management-on-the-openran-brasil-testbed/
[blueprint]: https://github.com/LABORA-INF-UFG/openran-br-blueprint
[nori]: https://biblioteca.sbrt.org.br/articlefile/4946.pdf
[xdevsm]: https://arxiv.org/pdf/2409.16754

- Sobre o programa: <https://openranbrasil.org.br/sobre/>
- Utilize o testbed: <https://openranbrasil.org.br/utilize-o-testbed/>
- Suporte ao OAI (05/08/2025): <https://openranbrasil.org.br/openranbrasil-avanca-em-inovacao-com-suporte-a-pilha-open-source-openairinterface-oai/>
- Workshop da Fase 3 (10/04/2026): <https://openranbrasil.org.br/openranbrasil-avanca-para-fase-de-aplicacoes-e-realiza-workshop-presencial-da-fase-3/>
- Resultado final da chamada (18/03/2026): <https://openranbrasil.org.br/wp-content/uploads/2026/02/resultadosFinais-ChamadaOpenRAN-Aplicacao-Hospedeiros_VF.pdf>
- Chamada pública de expansão: <https://www.rnp.br/chamadas-publicas/chamada-publica-para-expansao-do-testbed-do-openranbrasil/>
- Anexo IV, capacidade do testbed (09/2025): <https://plataforma.rnp.br/arquivos/documents/Anexo%20IV%20-%20Capacidades%20do%20Testbed.pdf?VersionId=rHnosLDConXIm0762LSbRQIkM1MmcoVc>
- Proposta Fyuz 2024: <https://www.rnp.br/wp-content/uploads/2024/09/Proposal-OpenRAN@Brasil-Fyuz-2024-Updated-Version-2.pdf>
- Visão geral, WRNP (Leonardo Ribeiro e Daniel Marques): <https://indico.rnp.br/event/106/contributions/890/attachments/344/549/OpenRAN_-_Leonardo__Daniel.pdf>
- Visão geral, WRNP maio/2026 (Gustavo Araújo): <https://indico.rnp.br/event/155/contributions/1254/attachments/543/834/16.00-16.30_OpenRAN-Brasil_-_WRNP.pdf>
- GT IQoS, III Workshop Open RAN Brasil: <https://indico.rnp.br/event/129/contributions/911/attachments/305/475/III-Workshop-OpenRAN_1.pdf>
- Minicurso Open RAN, SBrT 2025: <https://www.sbrt.org.br/sbrt2025/wp-content/uploads/2025/10/Minicurso-OpenRAN-SBrT.pdf>
- Deployment e testes de RICs no testbed (WTestbeds 2023, CPQD): <https://sol.sbc.org.br/index.php/wtestbeds/article/download/24813/24634/>
- Observabilidade no testbed (WGRS 2026): <https://sol.sbc.org.br/index.php/wgrs/article/view/42567>
- Demo NOMS 2025 (GERCOM): <https://gercom.ufpa.br/advancing-open-ran-deployment-and-management-on-the-openran-brasil-testbed/>
- OpenRAN@Brasil Blueprint: <https://github.com/LABORA-INF-UFG/openran-br-blueprint>
- NORI (SBrT): <https://biblioteca.sbrt.org.br/articlefile/4946.pdf>
- xDevSM (arXiv 2409.16754, trabalho externo ao programa): <https://arxiv.org/pdf/2409.16754>
