# 05 — Conformidade O-RAN e auditoria

## 1. Versões de especificação

| Item | Perfil da xApp RDL | NORI oficial (pilha E2 do projeto) |
| :-- | :-- | :-- |
| E2AP | v02.03 (alvo) | v03.01 |
| E2SM-KPM | v03.00 (alvo) | v03.00 |
| E2SM-RC | v01.03 (alvo) | v03.01 |
| Near-RT RIC | O-RAN SC Release J (alvo) | O-RAN SC Release I |

As versões da xApp são **alvos de compatibilidade**, não certificações. A divergência com o NORI significa que um teste E2 real exige alinhar a xApp a v3.01. Detalhes em [`compliance/HRDL_F1_COMPATIBILITY_PROFILE.md`](compliance/HRDL_F1_COMPATIBILITY_PROFILE.md) e [`e2/version-matrix.md`](e2/version-matrix.md).

## 2. Estado por interface

| Interface | Implementação | Verificação |
| :-- | :-- | :-- |
| Subscrição E2SM-KPM | REST do Subscription Manager (`SubscriptionParams`) + callback `/ric/v1/subscriptions/response` | testes com SubMgr simulado; não testada contra SubMgr real |
| RIC Indication (KPM) | decodificador local | *golden vectors* gerados pelo próprio codec (circular) |
| RIC Control (RC) | codec local **não normativo**; envio RMR com MEID | testes com RMR simulado; um E2 Node conforme rejeitaria o formato |
| ACK / Failure / timeout | correlação por (nó, RAN Function, requestor, instância); rollback só em timeout | testes unitários |
| Descoberta E2 (RAN Function Definition) | não implementada | — |
| A1 | receptor de políticas não conectado à decisão | testes unitários |
| SDL | wrapper sobre `sdl_set`/`sdl_get` do `ricxappframe` | testes unitários |

O modo `O_RAN_INTEROP` bloqueia despacho e readiness enquanto o backend não declarar `protocol_interoperability_verified`.

## 3. Gates de evidência

Definidos em [`reproducibility/provenance_policy.yaml`](../reproducibility/provenance_policy.yaml) e avaliados por [`scripts/certification/certify_chain.py`](../scripts/certification/certify_chain.py).

| Gate | Exigência para `CERTIFIED` | Veredito atual |
| :-: | :-- | :-: |
| G0 | Manifestos completos e versões/commits iguais ao `versions.lock` | CERTIFIED (pilhas nativa e NORI) |
| G1 | Execução NORI elegível com E2 Setup, Subscription e Indication KPM externos, confirmados por dissecação independente do PCAP (R14) | CERTIFIED |
| G2 | Decisão H-RDL funcional (testes) | LOCAL_ONLY |
| G3 | RIC Control e ACK/Failure externos correlacionados | CERTIFIED (NORI com o patch `0001-rc-control-ack` do lock) |
| G4 | Cadeia KPM_t0 → decisão → RC → ACK → KPM_t1 com ordem temporal, Control decidido pelo H-RDL a partir do KPM_t0 (registro da xApp casado com o PCAP) e efeito na RAN coerente com as cotas por regra calibrada (`slice_effect.py`, veredito `CONSISTENT`) | CERTIFIED (3 execuções v5; ressalvas em [`07_preregistro_fase4_v5.md`](07_preregistro_fase4_v5.md)) |
| G5 | ≥ 30 sementes pareadas elegíveis por baseline B0–B3 com E2 | NOT_CERTIFIED |
| G6 | G4 e G5 certificados + reprodução independente | BLOCKED |

Regras do certificador por execução: manifesto presente; origem explícita e elegível; `run_id` que não corresponda a gerador estatístico; campos obrigatórios do backend; `run_status=SUCCESS` e `exit_code=0`; versões e commits iguais ao perfil do backend no lock; todos os arquivos com hash e hashes conferindo; grupos de evidência bruta exigidos (FlowMonitor e, no NORI, PCAP/RAW); FlowMonitor com fluxos recebidos; artefatos E2 por mensagem e correlação RC/ACK (só NORI); horários coerentes. No NORI, as mensagens E2 vêm da dissecação do PCAP em `experiments/e2_dissection/<run>/` ([`e2_pcap_dissect.py`](../scripts/certification/e2_pcap_dissect.py)): ela só vale se o hash do PCAP conferir, e só conta para G1–G4 quando o tshark concorda com o dissecador do projeto mensagem a mensagem (R14 `PASS`).

O que **não** conta como evidência: origens `SYNTHETIC`, `MOCK`, `CODEC_TEST`, `LOCAL_GENERATOR`, `CAUSAL_FIXTURE`, `DISCRETE_EVENT_SIMULATOR`, `EMULATED`, `MANUAL`, `ESTIMATED`, `DEMO_RUN`; execuções geradas por scripts com RNG estatístico; mensagens E2 impressas pelo código do cenário; hashes gerados pelo próprio pipeline (provam integridade, não execução); decodificação pelo codec local (autoconsistência).

## 4. Registro de achados e correções (novembro de 2026)

| # | Achado | Situação |
| :-: | :-- | :-- |
| 1 | `rmr_send` do `ricxappframe` não aceita MEID; o código passava o nó como `retries`, o que falharia em todo controle real | corrigido: transporte com `rmr_alloc_msg(..., meid=...)` |
| 2 | Subscrição enviada como JSON pelo RMR (`RIC_SUB_REQ`) | corrigido: API REST do SubMgr com callback de notificação |
| 3 | Codec E2SM-RC fora da norma | documentado; modo estrito bloqueado; correção depende do ASN.1 oficial |
| 4 | Guarda de *slew-rate* nunca atuava (consultava um método inexistente) | corrigido: lê o estado confirmado da Perception; falha fechado sem fonte |
| 5 | Detecção de conflitos par a par, O(n²), sujeita a DoS | corrigido: eventos agrupados por alvo |
| 6 | `/ready` respondia 200 em `SUBSCRIBING` | corrigido |
| 7 | Transações e históricos sem limpeza (vazamento de memória) | corrigido |
| 8 | Rollback reaproveitava RICrequestID, ignorava o backend e disparava após `RIC_CONTROL_FAILURE` | corrigido |
| 9 | Vencedor final escolhido por prioridade, sobrepondo a utilidade TVS; incumbente reenviada | corrigido: arbitragem em dois estágios |
| 10 | Uma ação insegura vetava ações legítimas no mesmo conflito (S7) | corrigido: Safety Guard por proposta antes da arbitragem |
| 11 | Conflitos entre células não detectados (S4, S5) | aberto (limitação do desenho) |
| 12 | Commit NORI `9b64c12` do lock não existe; NORI exige ns-3.42 e E2 v3.01 | corrigido no `versions.lock` (perfis `nori` e `native`) |
| 13 | 210 execuções `S1_B0..B6` geradas com `numpy.random` e rotuladas como ns-3 | identificado; classificado pelo certificador como sintético |
| 14 | Cenários S0–S8 não alteravam a RAN; S0 e S4–S7 sequer anexavam UEs | corrigido para S0–S7 (`rdl-nr-common.h`); S8 pendente |
| 15 | S8 imprime handshake E2 fixo (`TraceLifecycleE2`) | documentado; não é evidência |
| 16 | Cenários anulavam `--RngRun` com `SetSeed` próprio: sementes idênticas | corrigido no executor (`--seed`) |
| 17 | "Hashes divergentes" das execuções antigas eram conversão CRLF do Git | corrigido: `experiments/runs/** -text` |
| 18 | `scripts/setup_ns3.sh` recai em outras versões silenciosamente | documentado; instalação fixada no guia |
| 19 | `analysis/export_tables.py` contém resultados escritos à mão (ex.: 103,1 Mbps em S8) | aberto: não usar como fonte |
| 20 | 5G-LENA v5.1 aborta em handover em massa (SRS sobreposto) | contornado com `--disableSrs=true` em S2, S4, S5 |
| 21 | PCAP E2 do NORI sem dissecação: mensagens não separadas por papel | corrigido: dissecador próprio + confirmação do tshark 4.2.2 (R14) |
| 22 | Exemplos do NORI instalam FlowMonitor mas não o gravam (R9/R10) | corrigido: variante `nori-rc-slicing-flowmon` gerada em `scratch/` pelo chart |
| 23 | RtMgr da Release I tem o A1 Mediator fixo; sem ele, a rota da subscrição estoura o prazo do SubMgr | corrigido: A1 Mediator incluído na receita |
| 24 | NORI ignora o *Event Trigger* da subscrição e reporta a cada `E2Periodicity` (padrão 10 ms) | documentado; execuções usam `--ns3::E2Interface::E2Periodicity=1` |
| 25 | RAN function 4 do NORI anunciada no E2 Setup com o OID do E2SM-KPM v3, embora a descrição CCC declare outro OID | documentado |
| 26 | NORI aplica o RIC Control E2SM-RC mas nunca envia RIC Control Acknowledge (só a CCC confirma) | contornado: patch `0001-rc-control-ack` no chart, listado com sha256 no lock e verificado por R6 |
| 27 | Critério de G4 aceitava qualquer cadeia com os seis papéis, inclusive um Control fixo sem decisão | corrigido: G4 exige `decision_source=H_RDL` e disparo pelo KPM_t0, ligados ao PCAP por sha256 |
| 28 | tshark 4.2 não disseca E2SM-RC v3 (OID `…1.3.2.3`) | documentado: confirmação independente limitada ao E2AP do Control/ACK |
| 29 | Cotas de PRB do Control não restringiram a carga do cenário (vazão inalterada) | confirmado na fase 4: sob 300 Mb/s, teto 20 % reduz a URLLC, teto 40 % não reduz a eMBB |
| 30 | KPM do NORI: `DRB.UEThpDl` sempre 0 (estatística PDCP no LCID 4 sem dados) e `RRU.PrbUsedDl` por UE calculado por símbolos OFDM | documentado: efeito medido na série do FlowMonitor por fatia (`slice_series.csv`) |
| 31 | KPM do NORI: `RRU.PrbUsedDl` do nó acima dos PRBs disponíveis; sinal de congestionamento sempre verdadeiro | documentado |
| 32 | KPM do NORI: nomes de métrica com `_`, fora do alfabeto de `PrintableString` | contornado na leitura (tipo equivalente em APER); codificação estrita |
| 33 | Expectativa de efeito da fase 4 tomou a parte da vazão como parte dos PRBs; o teto escolhido pelo H-RDL não restringiu | resultado negativo registrado (G4 `NOT_CERTIFIED`); desenho v2 pré-registrado em [`07_preregistro_fase4_v2.md`](07_preregistro_fase4_v2.md) |
| 34 | Calibração da v2 com tetos 30/30 (soma 60 %) não restringiu nenhuma fatia; o teto do NORI parecia só limitar quando as cotas somam 100 % | calibração inválida; avaliações v2 não executadas, conforme o pré-registro |
| 35 | Calibração da v3 com cotas complementares (30/70 e 70/30): teto de 30 % não restringiu nenhuma fatia dentro da janela; hipótese da soma 100 % refutada | calibração inválida; avaliações v3 não executadas, conforme o pré-registro. A leitura "não linear" foi superada pelo achado 36 |
| 36 | O Control do NORI só tem efeito quando o tempo simulado alcança o relógio de parede do instante em que chegou (~12 s simulados depois): `ScheduleWithContext` a partir da thread do E2 no `RealtimeSimulatorImpl`. Com isso, a cota é linear (~3,8 Mb/s por ponto percentual) e independe da soma | v4 oficial: curva inválida pela janela pré-registrada, avaliações não executadas; achado exploratório registrado. Próximo desenho: janela ancorada no instante de aplicação |
| 37 | Roteiro de avaliação v5 verificava a prontidão da xApp no `kubectl logs`, que o k3s rotaciona; abortou a semente 3 antes de iniciá-la | corrigido (lê o arquivo de eventos persistente); semente 3 executada com a mesma semente, desvio declarado |

As auditorias anteriores estão em [`auditoria/`](auditoria/README.md) como registro histórico; os relatórios com números não verificados, em [`historico/`](historico/README.md).

## 5. Pendências para interoperabilidade

1. G5: campanha com E2 real e ≥ 30 sementes pareadas por baseline B0–B3, com o Control decidido por cada baseline (G4 certificado com o H-RDL na v5).
2. Implementar a descoberta E2 (RAN Function Definition) para o modo estrito.
3. Propor ao NORI o envio do RIC Control Acknowledge na função E2SM-RC, para dispensar o patch local.
4. Fechar o loop KPM → decisão → RC com efeito medido no KPM (G4).
5. Autenticar a identidade das xApps no transporte de propostas.
