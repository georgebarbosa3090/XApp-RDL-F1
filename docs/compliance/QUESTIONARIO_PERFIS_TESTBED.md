# Questionário para os laboratórios: perfis srsRAN (GERCOM) e OAI + FlexRIC (LACIS)

Rascunho de 12/11/2026, a enviar às equipes dos dois laboratórios. As respostas preenchem os campos `A_CONFIRMAR` de [`configs/testbed_ufpa/backends/srsran_gercom.yaml`](../../configs/testbed_ufpa/backends/srsran_gercom.yaml) (14 campos) e [`oai_lacis.yaml`](../../configs/testbed_ufpa/backends/oai_lacis.yaml) (15 campos). Enquanto houver um campo pendente, o gate TB0 (perfil congelado) não passa ([`src/e2/backends/testbed_profiles.py`](../../src/e2/backends/testbed_profiles.py)) e a xApp da bancada não envia controle.

A forma mais rápida de responder a maior parte das perguntas é uma **captura do E2 Setup**. Ela traz a versão do E2AP, as RAN Functions anunciadas (KPM e RC), seus identificadores e as definições de cada uma:

```bash
sudo tcpdump -i any -w e2_setup.pcap sctp
```

Inicie a captura antes de subir o gNB e encerre depois do E2 Setup Response. Abra o arquivo no Wireshark com o dissector E2AP. Enviar o `.pcap` junto com as respostas já basta para as perguntas 4 a 7 e 10 a 11.

**Antes de enviar,** leia [`VARREDURA_TESTBEDS_OPENRAN_BRASIL.md`](VARREDURA_TESTBEDS_OPENRAN_BRASIL.md). Ela cruza as 13 perguntas com o que o testbed nacional do OpenRAN@Brasil já publica e acrescenta três perguntas mais diretas:

- **GERCOM:** a instalação de vocês segue a do GT IQoS (srsRAN + OSC RIC + Open5GS)? Se sim, a configuração e o código desse trabalho já respondem às perguntas 3 a 9.
- **LACIS:** o OAI vai rodar com o FlexRIC ou com o OSC RIC? O testbed nacional usa o FlexRIC, e a integração com o OSC ainda é pendência. Isso define se a RDL precisa de uma ponte E42 ↔ RMR.
- **Os dois:** a ilha terá a coleta de energia por Zabbix que a ilha da RNP já usa (WGRS 2026)? Ela pode atender ao gate GR4.

## Perguntas

| # | Campo no perfil | Pergunta | Como obter |
| --: | :-- | :-- | :-- |
| 1 | `versions.*` | Versões exatas da pilha. srsRAN: srsRAN Project e Open5GS. OAI: gNB, agente E2 do FlexRIC e núcleo. | Tag e commit do repositório (`git describe --tags` e `git rev-parse HEAD`); versão do núcleo pelo binário ou pela imagem. |
| 2 | `versions.oai_gnb` (só OAI) | O gNB inclui as alterações de código do GreenRAN (RAN-CodeUpdates)? | Ramo ou commit usado. |
| 3 | `versions.near_rt_ric` | Qual Near-RT RIC: O-RAN SC (e qual release) ou o RIC do FlexRIC? | Muda a interface com as xApps: com o RIC do FlexRIC, as xApps usam a API E42, e não o RMR. |
| 4 | `e2.e2ap_version` | Versão do E2AP que o agente fala. | Captura do E2 Setup. |
| 5 | `e2.e2term_address` | Endereço e porta SCTP do E2Term que o gNB usa. | srsRAN: seção `e2` do `gnb.yml`. OAI: seção do agente E2 no arquivo de configuração do gNB. |
| 6 | `kpm.version`, `kpm.ran_function_id` | Versão do E2SM-KPM e RAN Function ID anunciado. | Captura do E2 Setup (RAN Function com short name `ORAN-E2SM-KPM`). |
| 7 | `kpm.metrics.*` | O gNB exporta `RRU.PrbUsedDl`, `RRU.PrbAvailDl`, `DRB.UEThpDl` e `DRB.RlcSduDelayDl`? Há métrica por fatia? | Definição da RAN Function KPM na captura, ou um relatório KPM de teste. |
| 8 | `kpm.metrics.ue_sst` | Como o KPM identifica a fatia do UE (S-NSSAI/SST no rótulo da medida, no filtro do UE ou de outra forma)? | Relatório KPM de um UE com fatia configurada. |
| 9 | `rc.version`, `rc.ran_function_id` | Versão do E2SM-RC e RAN Function ID anunciado. | Captura do E2 Setup (short name `ORAN-E2SM-RC`). |
| 10 | `rc.prb_quota.layout` | O agente aceita a cota de PRB por fatia pelo RC Control Style 2, Action 6 (*Slice-level PRB quota*)? Em qual leiaute: o aninhado da norma ou um plano? No OAI, usa o modelo de serviço de fatiamento próprio do FlexRIC? | Definição da RAN Function RC na captura, código do agente ou documentação da pilha. |
| 11 | `rc.prb_quota.param_ids` | IDs dos RAN Parameters que o agente espera. | Ver a nota sobre IDs logo abaixo. |
| 12 | `rc.tx_power` | Por qual canal se muda a potência de TX da célula (atividade A1.2 do GreenRAN): E2SM-RC, E2SM-CCC, O1/NETCONF ou configuração com reinício? | Equipe da pilha. |
| 13 | `rc.cell_state` | Por qual canal se liga e desliga a célula (atividade A1.3): E2SM-CCC, RC próprio, O1 ou outro? O desligamento é real ou por potência mínima? | Equipe da pilha. |

**Nota sobre os IDs (pergunta 11).** Na norma E2SM-RC (§8.4.3.6), os parâmetros da cota de PRB vêm aninhados com estes IDs, como no código original do xSlice ([`third_party/xapps/xslice-oran`](../../third_party/xapps/xslice-oran/)):

- RRM Policy Ratio List = 1 e Group = 2;
- RRM Policy = 3, Member List = 4 e Member = 5;
- PLMN Identity = 6, S-NSSAI = 7, SST = 8 e SD = 9;
- Min PRB Policy Ratio = 10, Max = 11 e Dedicated = 12.

O NORI usa um leiaute plano com outros IDs: list = 1, sst = 3, max = 4, min = 5 e dedicated = 6 ([`nori_ns3.yaml`](../../configs/testbed_ufpa/backends/nori_ns3.yaml)). Hoje o codec só aceita o leiaute plano. Se o agente usar o aninhado, o codec terá de ser estendido e testado com o agente real.

## Mensagem curta para enviar

> Para integrar as xApps do GreenRAN e a RDL à pilha de vocês, precisamos fechar o perfil do backend: as versões da pilha e do RIC, o endereço do E2Term e como o agente E2 anuncia KPM e RC. Também precisamos saber se o agente aceita a cota de PRB por fatia pelo E2SM-RC e por qual canal se mudam a potência e o estado da célula. A maior parte sai de uma captura do E2 Setup (`tcpdump -i any -w e2_setup.pcap sctp`, ligada antes de subir o gNB). Segue o questionário com 13 perguntas. Se puderem mandar o `.pcap`, o arquivo de configuração do gNB e as respostas das perguntas 1 a 3, 8 e 12 a 13, o resto conseguimos extrair daqui.

## Depois das respostas

1. Preencher os YAML e conferir com `python -c "from src.e2.backends.testbed_profiles import load_profile, pending_fields; print(pending_fields(load_profile('SRSRAN_PROJECT')))"` (lista vazia = TB0 passa).
2. Se a resposta da pergunta 10 for "aninhado" ou "modelo do FlexRIC", abrir a extensão do codec antes do TB5.
3. Atualizar a tabela de prontidão (`artigos/tabelas/p3_tab_prontidao_testbed.tex`, via `scripts/gerar_tabelas.py`) e o doc 12 §4.
