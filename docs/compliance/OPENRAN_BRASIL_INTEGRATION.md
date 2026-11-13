# Integração no testbed OpenRAN@Brasil (planejada)

**Situação:** planejamento. Nenhum gate abaixo foi executado. Depende do perfil srsRAN + Open5GS ([HRDL_F1_SRSRAN_TESTBED_PROFILE.md](HRDL_F1_SRSRAN_TESTBED_PROFILE.md)) e de um codec E2SM-RC normativo. Para o testbed UFPA do projeto GreenRAN, a pilha (OAI ou srsRAN) ainda será confirmada; o perfil específico, com os gates GR1–GR4, está em [GREENRAN_UFPA_TESTBED_PROFILE.md](GREENRAN_UFPA_TESTBED_PROFILE.md).

## 1. Arquitetura prevista

```text
   Open5GS (AMF / UPF)
          │ N2 / N3
          ▼
   srsRAN gNB ── agente E2 (E2AP / KPM / RC v03.00)
          │ E2 (SCTP)
          ▼
   Near-RT RIC (O-RAN SC): E2Term, Subscription Manager (REST :8088)
          │ RMR / REST
          ▼
   xApp RDL: SrsRanBackendAdapter, Perception, Reasoning, Safety Guard
```

## 2. Gates de testbed

Cada gate só é aprovado com artefatos brutos registrados conforme a [política de evidência](EXPERIMENTAL_EVIDENCE_POLICY.md).

| Gate | Etapa | Critério de aprovação | Artefatos esperados |
| :-: | :-- | :-- | :-- |
| TB0 | Congelamento | commits de srsRAN, Open5GS e O-RAN SC registrados | manifesto |
| TB1 | Núcleo + RAN | UE registra, abre sessão PDU e trafega (ping/iperf3) | logs do AMF, `ping.log` |
| TB2 | E2 Setup | E2 Setup Request/Response concluídos no E2Term | PCAP E2, log do E2Term |
| TB3 | KPM de referência | xApp de referência recebe Indications KPM válidas | JSON de indicações |
| TB4 | KPM na RDL-N1 | `SrsRanBackendAdapter` decodifica KPM real | log JSONL da xApp |
| TB5 | RC de referência | controle de PRB por xApp de referência com ACK | PCAP E2 |
| TB6 | RC da RDL-N1 | RIC Control da xApp RDL com ACK correlacionado | log JSONL + PCAP |
| TB7 | Arbitragem | propostas conflitantes de duas xApps resolvidas de forma reprodutível | `conflicts.jsonl`, `decisions.jsonl` |
| TB8 | Closed loop | KPM(t0) → decisão → RC → ACK → KPM(t1..t3) em ordem | log causal, `iperf.json` |
| TB9 | Comparação entre backends | mesmas decisões em NORI_NS3 e SRSRAN_OPEN5GS para as mesmas entradas | relatório comparativo |
| TB10 | Ilha física | execução com O-RU e UE comercial | manifesto do testbed |

## 3. Primeiro cenário sugerido: S1 (conflito direto de PRB)

S1 evita controle de potência, cujo suporte varia entre versões de firmware. Duas xApps propõem cotas de PRB incompatíveis para o mesmo alvo. A RDL-N1 agrupa as propostas por alvo na janela de 200 ms, descarta as que violam os limites do Safety Guard, escolhe **uma** ação por TVS/EEVS e a despacha como RIC Control. Não há divisão fixa de cotas: o valor aplicado é o da proposta vencedora, dentro dos limites configurados em `configs/`. A validação exige ACK correlacionado e três amostras KPM consecutivas após o controle (3 s com KPM a cada 1 s).

O comportamento correspondente na simulação está nos resultados de S1 em [`../06_metodologia_e_resultados.md`](../06_metodologia_e_resultados.md).
