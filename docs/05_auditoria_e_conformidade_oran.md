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
| G0 | Manifestos completos e versões/commits iguais ao `versions.lock` | CERTIFIED (pilha nativa) |
| G1 | Execução NORI elegível com E2 Setup, Subscription e Indication KPM externos | NOT_CERTIFIED |
| G2 | Decisão H-RDL funcional (testes) | LOCAL_ONLY |
| G3 | RIC Control e ACK/Failure externos correlacionados | BLOCKED |
| G4 | Cadeia KPM_t0 → decisão → RC → ACK → KPM_t1 com ordem temporal | BLOCKED |
| G5 | ≥ 30 sementes pareadas elegíveis por baseline B0–B3 com E2 | BLOCKED |
| G6 | G4 e G5 certificados + reprodução independente | BLOCKED |

Regras do certificador por execução: manifesto presente; origem explícita e elegível; `run_id` que não corresponda a gerador estatístico; campos obrigatórios do backend; `run_status=SUCCESS` e `exit_code=0`; versões e commits iguais ao perfil do backend no lock; todos os arquivos com hash e hashes conferindo; grupos de evidência bruta exigidos (FlowMonitor e, no NORI, PCAP/RAW); FlowMonitor com fluxos recebidos; artefatos E2 por mensagem e correlação RC/ACK (só NORI); horários coerentes.

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

As auditorias anteriores estão em [`auditoria/`](auditoria/README.md) como registro histórico; os relatórios com números não verificados, em [`historico/`](historico/README.md).

## 5. Pendências para interoperabilidade

1. Gerar codecs E2AP/E2SM a partir do ASN.1 oficial (v3.01, compatível com o NORI) e validá-los com um dissector independente (`tshark`).
2. Implementar a descoberta E2 (RAN Function Definition) para o modo estrito.
3. Implantar a bancada NORI e um Near-RT RIC Release I; capturar E2 Setup, Subscription, Indication, Control e ACK.
4. Fechar o loop KPM → decisão → RC com efeito medido no KPM (G4).
5. Autenticar a identidade das xApps no transporte de propostas.
