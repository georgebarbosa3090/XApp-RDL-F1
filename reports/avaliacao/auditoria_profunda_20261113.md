# Auditoria profunda do projeto RDL (Fases 1 e 2) — 2026-11-13

Escopo: `XApp-RDL-F1` (ramo `malha-fechada`, HEAD `b8ac56e6` no início da auditoria; `main` em `51adada9`), `XApp-RDL-F2` (`main`, HEAD `639d6b0`) e a pasta de artigos (fora dos repositórios), esta só para conferir números. Auditoria só de leitura: nenhum arquivo dos repositórios foi alterado, exceto este relatório. Caminhos sem prefixo são relativos à raiz de `XApp-RDL-F1`. Os de F2 levam o prefixo `XApp-RDL-F2/`, e os dos artigos, `artigos/`.

**Nota de contexto.** Outras sessões trabalharam no mesmo ramo durante a auditoria: `cb770c8a`, `5d7065b5` e uma renomeação de `src/greenran/xapp1_ranslicer.py` e `src/greenran/xapp2_energysaver.py`, ainda não commitada. As linhas citadas valem para os arquivos como estavam quando foram lidos (a partir de `b8ac56e6`).

**Convenção:**
- **[V] verificado:** conferido diretamente no arquivo e na linha, no commit ou na saída de um comando citado.
- **[I] inferido:** dedução a partir do que foi verificado. Não foi executado nem observado.

## Resumo executivo

1. **Ciência.** A disciplina de pré-registro é o ponto mais forte do projeto [V]: 10 pré-registros, hipóteses refutadas relatadas e desvios datados. O certificador de 13/11 dá G0, G1, G3, G4 (85 cadeias) e G5 como `CERTIFIED`, G2 como `LOCAL_ONLY` e G6 como `NOT_CERTIFIED` [V].
2. **Números dos artigos.** Os números centrais dos três artigos batem com os CSVs gerados por script [V]. Há duas exceções de redação. O SBRC conta o S15 como terceiro cenário com penalidade de atraso, mas ele reproduz o S9 semente a semente. O artigo IEEE da F1 atribui à média do EEVS uma penalidade que o próprio texto explica pela regra de handover [V].
3. **Maior ameaça científica: pseudorreplicação** [V]. Em vários cenários a semente não muda topologia nem tráfego: S4, S12 (valores idênticos nas 5 sementes) e S8/G5 (desvio-padrão menor que 0,01 Mb/s). Além disso, H11.3 e H11.4 decorrem por construção do catálogo em malha aberta. "5/5" e "30 pares" contam em parte repetições determinísticas.
4. **Defeito de implantação** [V]. O chart Helm da RDL usa `RDL_MODE=governance`. Esse modo não é reconhecido e cai no `MockRMRXapp`, que não envia nem recebe RMR. A RDL implantada pelo chart não tem nenhuma entrada de propostas. O único caminho E2 real é a kpm-probe, que embute o H-RDL e cujo código vive dentro do chart, sem testes.
5. **Decisão nova do autor: toda xApp lê KPM e emite RC pela RDL.** Hoje nenhuma das quatro xApps de `reference-xapps/` lê KPM [V]. As do GreenRAN leem KPM, mas emitem JSON pelo RMR 30000, não E2SM-RC [V]. Na malha fechada o B3 decide dentro do orquestrador, sem passar pelo RMR [V].
6. **Testes [V].** Em `tests/unit` da F1, 385 passam e 1 é pulado; a cobertura é de 87,1 % em `src/` e de 66,0 % em `scripts/`. Os 13 testes da F2 passam.
7. **Engenharia [V].** Pacote Python chamado `src`; `RDLxApp` com 1373 linhas e E/S no construtor; baselines B0–B2 em quatro lugares; relógio por *monkeypatch* nos experimentos; cerca de 30 variáveis de ambiente lidas de forma dispersa; Pyright quase todo desligado.
8. **Reprodutibilidade e documentação [V].** O manifesto nativo grava o SHA curto, sem indicar árvore suja; as 262 execuções NORI não têm `repo_git_sha` no manifesto; o `versions.lock` declara um SO que nenhuma execução usa. Há 9 trechos de documentação defasados (`docs/06`, `docs/07`, `docs/16`, README dos pré-registros, README da F2).
9. **Prioridades:** modo do chart (R1), documentação (R2), proveniência (R3), pseudorreplicação (R5), pipeline com relógio injetado e baselines únicos (R7, R8), e RC interceptado (12040) como entrada canônica da RDL (R12).
10. **Correções do mesmo dia:** R1–R6, R8, R14 e R18 feitos; R7, R11, R13, R15 e R17 parciais; R9, R10, R12, R16, R19 e R20 pendentes, cada um com o motivo (seção 6).

---

## 1. Ciência e evidência

### 1.1 Pré-registros 01–10 e desvios

**Pontos fortes [V]:**
- **A ordem foi respeitada.** Os commits de pré-registro vêm antes dos de dados: por exemplo, `3962e97d` → `9852924f`, `6bb7773f` → `b2e5589c` e `392fb7f0` (desvios do G5 declarados antes das sementes de reposição).
- **Resultados negativos ficam publicados:**
  - 01–03: calibração ou curva inválida;
  - 06: H6.4 refutada;
  - 08: H9.2 e H9.3 refutadas (`docs/preregistros/README.md:14-22`).
- **Os desvios são datados e explicados:**
  - 04: semente abortada (`docs/preregistros/04_fase4_v5.md:78`);
  - 05: aspas perdidas entre o PowerShell e o WSL (`05_fase4_v6.md:105`);
  - 07: reposições (`07_campanha_g5_s8.md:78`);
  - 08: semente sem efeito no S4 (`08_conflitos_entre_celulas_s4_s5.md:61`);
  - 09: commits durante a campanha (`09_eevs_aditivo.md:54`);
  - 10: exclusão do S14 por critério fixado antes da rodada curta e a interrupção das 17h25 (`10_campanha_s9_s15_g1_g2.md:14-23`).

**Lacunas:**
- **[V] Mudança de código entre o registro e a execução do pré-registro 10, não declarada.**
  - O §2 diz que o commit do pré-registro é "o mesmo da execução" (`10_campanha_s9_s15_g1_g2.md:11`).
  - O critério de exclusão entrou em `5ae0232f`, e as 160 execuções gravam `d0cbd8f`.
  - Entre os dois, 12 arquivos mudaram em `src/` e `scripts/`, com 905 inserções: A1 com dono por campo, `src/greenran/`, `src/rdl_xapp.py` e `src/main.py` (`git diff --stat 5ae0232f d0cbd8f`).
  - Nenhuma mudança tocou `src/core/` nem `simulations/ns3/conflicts/catalog.json`.
  - [I] Impacto provável nulo nas decisões do B3, mas falta a frase de desvio.
- **[V] A campanha 10 rodou com EEVS `mean`, como o pré-registro manda.** `bf9730ab` (padrão aditivo) não é ancestral de `d0cbd8f` e só entrou na `main` pelo merge `87f80113`, em 13/11.
- **[V] O README dos pré-registros está defasado.** A linha 10 ainda diz "agendada para 2026-11-12 9h" (`docs/preregistros/README.md:23`), embora os resultados estejam anexados (`8761f728`).

### 1.2 Gates G0–G6 e certificação

O certificado mais recente é `reports/certification/certificate_20261113T051926Z.md:9-17` [V]:

| Gate | Veredito | Evidência |
| :-: | :-: | :-- |
| G0 | CERTIFIED | 676 execuções com manifesto e versões do lock |
| G1 | CERTIFIED | 256 execuções com KPM e subscrição |
| G2 | LOCAL_ONLY | decisão coberta só por testes |
| G3 | CERTIFIED | 236 execuções com RC e ACK correlacionados |
| G4 | CERTIFIED | 85 cadeias KPM_t0 → decisão → RC → ACK → KPM_t1 |
| G5 | CERTIFIED | 30 pares; B3 com 122 execuções de cadeia |
| G6 | NOT_CERTIFIED | falta a reprodução independente |

Classificação das execuções: 671 `ELIGIBLE` e 5 `INCOMPLETE_EVIDENCE`.

**Pontos fortes [V]:**
- O dissecador próprio só conta quando o tshark concorda mensagem a mensagem (R14).
- O hash prova integridade, não execução, e o certificador diz isso explicitamente (`docs/07_certificacao_e_achados.md:44`).
- As origens sintéticas são vetadas, e a auditoria `scripts/check_no_synthetic_results.py` roda no CI.

**Limites:**
- **[V] R7 dá `WARN` em todas as execuções.** O lock declara `Ubuntu 22.04 LTS` (`reproducibility/versions.lock:88`). Os manifestos nativos registram 24.04.1 e os NORI 20.04.6 (`certificate_20261113T051926Z.md`, seções S1 e nori_S0).
- **[V] A confirmação independente do RC é parcial.** O tshark 4.2 não disseca o E2SM-RC v3 (`docs/07_certificacao_e_achados.md:77`, achado 28). O conteúdo do Control (as cotas) só é confirmado pelo codec do próprio projeto. O E2AP do Control/ACK é confirmado.
- **[V] O G4 mede o efeito no FlowMonitor, não no KPM.** O KPM do NORI não traz vazão por UE (`docs/07_certificacao_e_achados.md:124`).
- **[V] `docs/07` está defasado em relação ao certificador:**
  - `docs/07_certificacao_e_achados.md:38` ainda diz "G4 CERTIFIED (3 execuções v5)";
  - as linhas 9 e 20 dizem que o RC da xApp é v01.03 e "não normativo" e que "um E2 Node conforme rejeitaria o formato", mas o G3 foi certificado com o codec v3 compilado do ASN.1 do NORI (`src/e2/v3/codec.py`; `pyproject.toml:35`, extra `e2v3`).

### 1.3 Malha aberta × malha fechada (doc 16)

- **[V] Malha aberta.** As decisões de todas as campanhas nativas são calculadas **antes** de o ns-3 rodar (`docs/16_xapps_originais_malha_fechada.md:21-26`), e nenhuma xApp roda como processo. O doc 06 lista isso como ameaça (`docs/06_metodologia_e_resultados.md:254-255`), e os artigos também.
- **[V] Malha fechada: estado atual.** O orquestrador e o passo travado estão no commit `13a68e44` (E0–E1). O shim FlexRIC (`xapps-originais/`) e o `scripts/closed_loop/flexric_driver.py` entraram durante esta auditoria (`cb770c8a`), sem efeito nas conclusões abaixo.
- **[V] Divergência entre o desenho e a implementação.** O critério de pronto 2 do doc 16 é "xApp → 30000 → RDL → ação → ns-3 → KPM → xApp" (`docs/16_xapps_originais_malha_fechada.md:17`). No orquestrador, porém, o B3 decide dentro do processo, por `HrdlStream`: `scripts/closed_loop/orchestrator.py:55-67` chama `rce.HrdlStream()` e `stream.decide`. Não há RMR, registro de xApps, janela adaptativa, governança nem interceptação. [I] A cadeia certificável na malha fechada ainda é "proposta → pipeline", e não o caminho de produção.
- **[V] O status do doc 16 está defasado.** `docs/16_xapps_originais_malha_fechada.md:3` diz "Nada aqui está implementado" e "este arquivo só entra no git nesse momento", mas o arquivo está no git (`7056e8a2`, `b8ac56e6`) e E0–E1 estão implementados.

### 1.4 Ameaças à validade não declaradas ou subdeclaradas

1. **Pseudorreplicação [V].**
   - S4: a semente não altera topologia nem tráfego (achado 54, `docs/07_certificacao_e_achados.md:103`).
   - S12: B0 = 9,406 Mb/s e B3 = 18,254 Mb/s, "igual em todas as sementes" (`10_campanha_s9_s15_g1_g2.md:71`), os mesmos valores da rodada curta 9102 (`:16-19`).
   - S8/G5: desvio-padrão entre sementes menor que 0,01 Mb/s (`07_campanha_g5_s8.md:106`).
   - S11 e S15: contagens idênticas em todas as sementes (8 contra 2 handovers; 10 contra 0 ações inseguras, `10_campanha_s9_s15_g1_g2.md:69-70`).
   - O artigo IEEE da F1 declara isso para o S4 (`artigos/ieee_fase1_hrdl/main.tex:303`), mas não para S12, S8 e S11.
   - O G5 exige "≥ 30 sementes pareadas" sem definir qual é a unidade de replicação.
2. **Hipóteses verdadeiras por construção [I, a partir de V].**
   - Em malha aberta, H11.4 (S15: `unsafe_applied = 0` no B3) decorre do *default-deny* do Safety Guard sobre um cronograma fixo, e H11.3 (S11: menos handovers) da regra `HANDOVER_PING_PONG` sobre um cronograma fixo.
   - São testes funcionais, executados no simulador, que confirmam o comportamento esperado. Não são evidência de efeito na RAN.
   - Só H11.1, H11.2 e H11.5 medem uma resposta do rádio.
3. **Baselines pouco discriminativos [V].**
   - B1 e B2 dão resultados idênticos em todos os cenários da campanha 10 (`10_campanha_s9_s15_g1_g2.md:85`).
   - No S12 e no G1, B1 = B2 = B3 nas métricas de rádio (`:84`).
   - No ambiente do MAPPO, B1 = B2 = B3 (`artigos/dados/insights/p2_cardl_tradeoff.csv`, linhas B1–B3; `artigos/ieee_fase2_cardl/main.tex:188`).
4. **Força estatística do critério "≥ 4 de 5" [cálculo analítico, não é número do projeto].** Num teste de sinais unilateral com p = 0,5, 4/5 ou mais ocorre ao acaso com probabilidade 6/32, e 5/5 com 1/32. Os pré-registros não dizem que o critério é heurístico.
5. **Viés de desenho de cenário [I].** O mesmo autor escreve o catálogo, as hipóteses, os baselines e a xApp. A lista de ameaças do `docs/06_metodologia_e_resultados.md:252-259` não menciona isso.
6. **Latência fria na bancada [V].** A mediana é 3,18 ms, mas o p99 é 17,6 ms, acima do limite inferior de 10 ms do laço quase em tempo real (`artigos/ieee_fase1_hrdl/main.tex:326`). O resumo dá só a faixa de medianas, "0.35--3.2 ms" (`:33`).

### 1.5 Números dos artigos contra a evidência

| Afirmação | Fonte conferida | Resultado |
| :-- | :-- | :-- |
| F1: "certified on 85 chains" (`main.tex:33`) | `certificate_20261113T051926Z.md:15` | [V] confere |
| F1: G1 256, G3 236 (`main.tex:223,225`) | mesmo certificado, linhas 12 e 14 | [V] confere |
| F1: decisão 0,354 ms (mediana nativa), p95 1,11, p99 1,87, máx. 3,54; 1090 janelas (`main.tex:326`) | `artigos/dados/insights/p1_latencia_resumo.csv`, linha `TODAS` | [V] confere |
| F1: "No out-of-bounds action … 131 H-RDL runs, against 100 in 90" (`main.tex:33,321`) | `p1_inseguras_por_baseline.csv`: B3 116 + B3A 15 = 131; B1 e B2 100 em 90 | [V] confere |
| F1: atraso −43 ms contra B0 e −12 a −16 ms contra FIFO e prioridade, 5/5 (`main.tex:33`) | `p1_efeito_pareado.csv`, C1/S6: −43,05; −11,77; −16,36; 5/5 | [V] confere |
| F1 e SBRC, campanha 10: G2 1,79 contra 0,22; G1 23,0 → 5,6 ms; S11 8 → 2; S12 9,41 → 18,25 (`main.tex:309`) | `p3_pr10_descritivo.csv` e pré-registro 10 §6 | [V] confere |
| F1: a média do EEVS causa a penalidade de atraso nos cenários de handover (`main.tex:311`) | o mesmo parágrafo atribui S9 e S10 à regra `HANDOVER_INTO_REDUCED_CELL` | [V] **inconsistência interna de atribuição** |
| SBRC: "delay penalties in three handover scenarios" (`sbrc_greenran/main.tex:29,33,153`) | S15/B3 = S9/B3 byte a byte (`10_campanha_s9_s15_g1_g2.md:83`; `p3_pr10_descritivo.csv`, linhas S9/B3 e S15/B3 iguais) | [V] **conta duas vezes a mesma configuração**; o IEEE da F1 diz isso (`main.tex:311`), o SBRC não |
| F2: recompensa 68,19 contra 67,05; −11 % de PRBs; −56 % de mudanças; 1,0 % de violações; semente com 34 % excluída (`ieee_fase2_cardl/main.tex`, resumo) | `p2_cardl_tradeoff.csv` e `p2_cardl_validacao.csv` | [V] confere |
| F2: "exceeds H-RDL" | B1 = B2 = B3 no mesmo ambiente | [V] o corpo declara isso (`main.tex:188`); o resumo não diz que o ganho também é sobre FIFO e prioridade |
| F2: modelo avaliado contra o "H-RDL" | o manifesto `XApp-RDL-F2/experiments/training/mappo_seed101/training_manifest.json` registra a F1 em `a0cb21eb`; o pin atual é `9fefbff6` (`XApp-RDL-F2/pyproject.toml:18`) | [V] deriva entre a evidência e o pin, não declarada |
| F2 README: "não supera a H-RDL" (`XApp-RDL-F2/README.md:36`) | `XApp-RDL-F2/docs/15_treino_mappo_calibrado.md:33` e o artigo dizem que a semente 101 supera | [V] **README defasado** |

Os números conferem. As correções são de redação e de enquadramento.

---

## 2. Arquitetura O-RAN

### 2.1 Interfaces

| Interface | Implementação | Estado |
| :-- | :-- | :-- |
| E2AP + E2SM-KPM v3.00 | codec v3 (`src/e2/v3/codec.py`, 469 linhas, compilado do ASN.1 do NORI); subscrição pelo SubMgr REST | [V] real só pela kpm-probe (G1) |
| E2SM-RC v3.01, Style 2 / Action 6 | idem; despacho em `src/e2/control_dispatcher.py` (530 linhas) | [V] real só pela kpm-probe (G3/G4); patch `0001-rc-control-ack` no NORI |
| Descoberta E2 (RAN Function Definition) | não implementada | [V] `docs/07_certificacao_e_achados.md:22`; o modo estrito fica bloqueado (`src/rdl_xapp.py:406-414`) |
| RMR | `ricxappframe`, se presente; senão `MockRMRXapp` (`src/rdl_xapp.py:20-49`) | ver 2.2 |
| A1 | HTTP em 127.0.0.1 (`src/rdl_xapp.py:179`) e RMR 20010–20012 (`src/interfaces/a1_rmr.py`); A1-PMS 2.8.0 com adaptador (`deploy/helm/a1pms/files/a1_osc_adapter.py`) | [V] política publicada pelo rApp chegou ao mediador (achado 56); sem autenticação (pendência 5 de `docs/07`) |
| Proposta das xApps | JSON próprio pelo RMR 30000 / 30001 | [V] mensagem específica do projeto, fora da norma O-RAN |
| Interceptação do 12040 | `src/governance/interception.py` | [V] testada só com RMR simulado (`docs/11_governanca_hierarquica_xapps.md:92`) |

### 2.2 Defeito: a RDL implantada pelo chart não tem RMR

O defeito, verificado em cinco pontos [V]:
1. `deploy/helm/iqos-xapp-rdl/values.yaml:32` e `scripts/deploy_helm.sh:133` definem `RDL_MODE=governance`.
2. `src/rdl_xapp.py:121-123` só reconhece `O_RAN_INTEROP` e seus sinônimos. `GOVERNANCE` vira um modo não estrito.
3. Em `src/rdl_xapp.py:252-267`, todo modo diferente de `O_RAN_INTEROP` instancia o `MockRMRXapp`.
4. O `MockRMRXapp.rmr_send` devolve `False` com um aviso, e os *callbacks* registrados nunca disparam (`src/rdl_xapp.py:28-48`).
5. O servidor HTTP não aceita propostas (`src/observability/health_server.py:54-124`): só `GET` e o *callback* de subscrição.

**Consequência [I]:** a RDL do chart sobe `READY` (`src/rdl_xapp.py:454-456`), mas não recebe propostas, Indications nem A1 por RMR, e não envia RIC Control. Os níveis 1 a 3 da governança (`docs/11`) nunca rodaram de ponta a ponta com RMR real. O doc 11 admite isso para a interceptação, mas não diz que a própria RDL do chart está sem transporte.

O caminho E2 real é a **kpm-probe** (`deploy/helm/xapp-kpm-probe/files/kpm_probe.py`, 592 linhas). Ela embute o H-RDL em modo catálogo e é um segundo controlador autorizado na NetworkPolicy (`deploy/helm/ric-governance/values.yaml:21`). O código dela fica dentro do chart, fora de `src/`, fora da cobertura, e não é citado por nenhum teste (`grep kpm_probe tests` não acha nada) [V].

### 2.3 Governança (doc 11)

**Pontos fortes [V]:**
- O desenho em quatro níveis mais o quinto aspecto da A1 está bem fundamentado (`docs/11_governanca_hierarquica_xapps.md:9-16`).
- A NetworkPolicy foi verificada no cluster: pod não autorizado recusado, kpm-probe aceita (`:70-75`).
- A precedência por campo da A1 trata o conflito entre rApps, pouco coberto na literatura (achado 64).

**Fragilidades:**
- **[V] A confiança do proponente vem só de um rótulo.** `networkpolicy-rdl.yaml` aceita qualquer pod do namespace `ricxapp` com `rdl.governance/proposer: "true"`, e qualquer pessoa que implante algo nesse namespace pode pôr o rótulo. A identidade forte depende do registro por origem RMR, que o próprio doc 11 diz ser forjável (`:49`).
- **[V] Portas abertas sem restrição:**
  - as portas 4561, 8080 e 8081 da RDL aceitam qualquer origem (`deploy/helm/ric-governance/templates/networkpolicy-rdl.yaml`, regra final);
  - o 8080 expõe `/governance`, `/rejections`, `/decisions` e `/kg` sem autenticação (`src/observability/health_server.py:83-124`);
  - não há política de *egress*.
- **[V] O conflito implícito cobre poucos parâmetros.** Só `CELL_STATE` e `PRB_QUOTA` são verificados; `TX_POWER`, `SCHEDULER_WEIGHT` e `HANDOVER` ficam de fora (`docs/11_governanca_hierarquica_xapps.md:114-130`).
- **[V] O nó é fixo no código.** `gnb_01` aparece no ponto de entrada da RDL (`src/rdl_xapp.py:436-467`), e [I] a subscrição só atende um nó.

### 2.4 xApps próprias, derivadas e originais diante da decisão nova do autor

Decisão: **toda xApp do projeto tem de ler KPM e emitir RC pela RDL.**

| Grupo | Lê KPM? | Emite o quê? | Situação diante da decisão |
| :-- | :-- | :-- | :-- |
| `reference-xapps/` (xSlice, ES, TS, Rogue; 913 linhas) | **não** (`reference-xapps/README.md:3`) | JSON pelo RMR 30000 (`common/rdl_transport.py`) | [V] não cumpre; o ES derivado emite `TX_POWER` constante (tabela do `docs/16`, trecho acrescentado em 13/11) |
| `src/greenran/` (xApp1-RANSlicer, xApp2-EnergySaver) | sim, pelo `RicKpmSource`, não verificado com RAN (`src/greenran/common.py:11-13`) | JSON pelo RMR 30000 | [V] cumpre a metade KPM; não emite RC |
| Catálogo (`simulations/ns3/conflicts/catalog.json`) | — | propostas fixas | [V] fonte de todas as campanhas até a 10 |
| Originais (xSlice C, ES Orange C, ric-app-ts C++) | KPM do ns-3 pelo shim e42 / adaptador | E2SM-RC ou gRPC RC, convertidos em 30000 pelo adaptador | [V] desenho do doc 16 §3; E0–E1 implementados |
| kpm-probe | KPM v3 real | RC v3.01 real, direto ao E2Term | [V] cumpre, mas fora da RDL de produção |

**Recomendação de arquitetura (R12) [I]:**
- **Entrada canônica.** O caminho único de entrada da RDL deve ser o **E2SM-RC interceptado (12040)**, que é o formato padrão e o que as originais já emitem. Hoje ele é o nível 2 da governança.
- **O RMR 30000** fica como otimização interna ou é aposentado. Hoje há duas entradas com semânticas e validações diferentes (`_action_proposal_handler` e `_intercepted_control_handler`, `src/rdl_xapp.py:592` e `:872`).
- **As xApps próprias** passam a assinar KPM pelo SubMgr (o código comum já existe em `src/greenran/common.py:195-236`) e a emitir RC.
- **As derivadas** passam a ler KPM ou são declaradas apenas geradoras de carga de conflito, como o próprio `docs/16` sugere (trecho acrescentado em 13/11, item 5).

---

## 3. Engenharia de software

### 3.1 Estrutura de módulos e acoplamento

- **[V] O pacote se chama `src`.** O `pyproject.toml:51` empacota `src` e `src.*`. Na F2, o `.venv` instala um pacote de topo `site-packages/src` (`import src; src.__file__`). [I] Qualquer outra dependência com pacote `src` colide.
- **[V] Uma classe "deus".** `src/rdl_xapp.py` tem 1373 linhas:
  - o construtor sobe servidores HTTP nas portas 8080 e 8081 (`:181-188`);
  - `health.run()` é chamado duas vezes (`:186`, `:318`);
  - `_process_action_group` tem cerca de 280 linhas (`:1009-1291`).
- **[V] `src` depende de um diretório que não é pacote.** `src/greenran/common.py:27-30` insere `reference-xapps/common` no `sys.path`. O `docker/Dockerfile` copia `reference-xapps/` para a imagem da RDL para compensar (linha do `COPY --chown=xapp:xapp reference-xapps/`). [I] Uma *wheel* da F1 instalada pela F2 a partir do git quebra ao importar `src.greenran`.
- **[V] Os experimentos dependem de internos.** `HrdlStream`:
  - troca o `time` dos módulos `refinement` e `perception` por *monkeypatch* (`scripts/certification/run_conflict_experiment.py:163-164`);
  - substitui `dispatcher.dispatch_control` e `reasoning.resolve`;
  - chama o método privado `_process_action_group` (`:199`);
  - instancia o `RDLxApp` completo, inclusive os servidores HTTP (`:166`).

  O orquestrador da malha fechada herda tudo isso (`scripts/closed_loop/orchestrator.py:44,59`).
- **[V] Diretórios mortos.** `src/coordination`, `src/domain` e `src/simulation` estão vazios no disco (o achado 58 os removeu do git).

### 3.2 Duplicação

- **[V] Os baselines B0–B2 existem em quatro implementações:**
  - `scripts/certification/run_conflict_experiment.py:100-131`;
  - `scripts/closed_loop/orchestrator.py:52-80` (com outra semântica de B0: "apply-all-at-window-close");
  - `src/closed_loop/catalog_loop.py:117-170` (B0 "apply-on-arrival");
  - `XApp-RDL-F2/cardl/marl/baselines.py:1-67`.
- **[V] Três xApps de energia com funções diferentes e o mesmo nome de papel:** o ES derivado, a xApp2-EnergySaver e o ES Orange original. A tabela comparativa do `docs/16` (trecho acrescentado em 13/11) já documenta isso. Falta decidir qual é a de referência.
- **[V] Dois caminhos de decisão com E2.** A kpm-probe (`src/closed_loop/hrdl_slice_loop.py`, `catalog_loop.py`) e o `RDLxApp` de produção cobrem as mesmas responsabilidades: subscrição, decodificação e despacho.

### 3.3 Testes

| Medida | Valor | Fonte |
| :-- | :-- | :-- |
| `tests/unit` na F1 | 385 passam, 1 pulado, 235,75 s | [V] `pytest -q tests/unit` nesta auditoria |
| Cobertura de `src/` (só testes unitários, instruções + ramos) | 87,1 % | [V] calculada da saída do `--cov` |
| Cobertura de `scripts/` | 66,0 % | [V] idem |
| Arquivos com 0 % | `check_no_synthetic_results.py`, `validate_experiment_tree.py`, `verify_provenance_and_integrity.py`, `generate_golden_vectors.py`, `run_pyright_check.py`, `verify_coverage.py`, `scripts/closed_loop/flexric_driver.py` (ainda não rastreado quando os testes rodaram) | [V] |
| `scripts/closed_loop/orchestrator.py` | 33 % | [V] |
| `src/rdl_xapp.py`, `src/e2/control_dispatcher.py`, `src/e2/v3/codec.py` | 83 %, 81 %, 78 % | [V] |
| Testes da F2 | 13 passam, 113,75 s | [V] |

**Lacunas [V]:**
- O gate de cobertura usa `source = src` (`.coveragerc:4`): `scripts/`, `rapps/`, `reference-xapps/` e a kpm-probe ficam fora.
- O `.coveragerc:6` omite `src/core/marl/*`, que não existe mais.
- Seis arquivos de teste estão soltos em `tests/` (por exemplo, `tests/test_rollback_timeout.py`), fora da divisão unit / integration / interoperability.
- Os *golden vectors* são circulares, gerados pelo próprio codec (`docs/07_certificacao_e_achados.md:19`).
- Não há teste de integração da malha fechada com RMR real nem do chart (`helm template`).
- Aviso de sintaxe em `tests/unit/test_kg_export.py:30` (escape inválido `"\ "`).

### 3.4 CI (`.github/workflows`)

- **[V] A instalação do RMR falha em silêncio.** O CI baixa pacotes do Debian *stretch* com `|| true` (`.github/workflows/ci.yml:31-35`). Se o download falhar, o CI segue sem RMR.
- **[V] A suíte roda duas vezes:** primeiro por pasta, depois inteira com cobertura (`ci.yml:57-78`).
- **[V] Ferramentas instaladas e não usadas.** `ruff` e `mypy` estão nas dependências de teste (`pyproject.toml:44,47`), mas o CI não os executa.
- **[V] O `uv.lock` existe, mas o CI usa `pip install` sem *lock*.**
- **[V] O CI não valida os charts.** Não há `helm lint` nem `helm template`, só `docker build` (`ci.yml:93-102`).
- **[V] Gatilhos limitados.** Os dois workflows disparam só em `main` e nos PRs para `main`: os commits do ramo `malha-fechada` não passam pelo CI.
- **[V] F2:**
  - o CI instala a F1 pelo pin do `pyproject` (`XApp-RDL-F2/.github/workflows/ci.yml:19-22`);
  - o workflow de prontidão científica falha de propósito até haver evidência elegível (`scientific-readiness-f2.yml:3-4`). É um bom desenho.

### 3.5 Reprodutibilidade

- **[V] O SHA gravado é curto e sem indicação de árvore suja.** `repo_git_sha` usa `rev-parse --short` e, em falha, devolve `"unknown"` em silêncio (`scripts/certification/run_conflict_experiment.py:278-291`). A F2 já grava `git_dirty` (`XApp-RDL-F2/cardl/marl/train.py:43-62`). [I] Uma execução feita com mudança não commitada no driver fica indistinguível. Esse é o caso da execução em andamento `experiments/runs/cl_e2_S11_B3M_es_seed16901`, com `orchestrator.py` modificado e `flexric_driver.py` não rastreado no momento da execução (os dois entraram depois, em `cb770c8a`).
- **[V] Contagem de `repo_git_sha` nos manifestos:**
  - 677 manifestos em 678 diretórios de execução;
  - sem `repo_git_sha`: 262, todos `nori_*`;
  - com `d0cbd8f`: 160 (campanha 10).

  O commit das execuções NORI está em `experiments/xapp_logs/<run>/kpm_probe_events.jsonl` (`src_commit`, SHA completo). O G0 não confere esse campo.
- **[V] Execução sem manifesto.** `experiments/runs/cl_e2_S11_B3M_es_seed16901` (em andamento, de outra sessão) não tem manifesto. Se for commitada assim, entra como incompleta.
- **[V] A deriva do pin da F2:**
  - o pin aponta a `9fefbff6` (`XApp-RDL-F2/pyproject.toml:18`), presente em `origin/main`;
  - o `.venv` local da F2, porém, tem a F1 instalada a partir da cópia de trabalho, sem modo editável (`direct_url.json` aponta para um `file://` local, sem commit), na versão `1.1.0`;
  - [I] os testes locais da F2 não rodam contra o pin.
  - Os *checkpoints* foram treinados na F1 `a0cb21eb` (manifesto de treino). O commit `6c72ac3` acrescenta "treino determinístico", mas só altera `experiments/training/selection.json`: os modelos não foram retreinados com esse código.
- **[V] Versão estática.** O `pyproject.toml:7` (F1) e a imagem do chart (`values.yaml:5`) estão em `1.1.0` desde agosto. Os dois repositórios não têm *tags* de versão.

### 3.6 Empacotamento (Helm, Docker, pyproject)

- **[V] Gerado a cada renderização:** `rolloutTimestamp: {{ now }}` (`deploy/helm/iqos-xapp-rdl/templates/deployment.yaml:15`). Todo `helm upgrade` reinicia o pod, e o *template* não é reprodutível.
- **[V] Imagem por *tag* local, sem *digest*** (`values.yaml:3-6`). Faltam `readOnlyRootFilesystem` e `seccompProfile` no `securityContext` (`values.yaml:24-28`).
- **[V] `docker/docker-compose.yml` está obsoleto:** inalterado desde `ea641a6f` (agosto), com `memgraph/memgraph-platform:latest` sem versão. Contraria a regra "Helm, não Docker". O `Dockerfile` continua necessário para a imagem.
- **[V] As dependências do `pyproject` só têm piso** (`>=`). O `uv.lock` não é usado no Dockerfile nem no CI.

### 3.7 Documentação: consistência com o código

Trechos defasados [V]:
1. `docs/preregistros/README.md:23`: campanha 10 "agendada".
2. `docs/07_certificacao_e_achados.md:9,20`: RC v01.03 e "não normativo", embora o G3 esteja certificado com o v3.
3. `docs/07_certificacao_e_achados.md:38`: G4 "3 execuções", contra 85 cadeias no certificador.
4. `docs/07_certificacao_e_achados.md:128`: pendência "EEVS com utilidade por média", já resolvida pelo achado 66.
5. `docs/07_certificacao_e_achados.md:130`: campanha 10 "agendada".
6. `docs/06_metodologia_e_resultados.md:249`: "Conflitos entre células não são detectados", já resolvido pelo achado 52. O doc 06 termina no §5.8 e não traz os resultados dos pré-registros 08, 09 e 10.
7. `docs/16_xapps_originais_malha_fechada.md:3`: status "nada implementado".
8. `XApp-RDL-F2/README.md:34-36`: estado em 10/11 e "não supera a H-RDL".
9. `reproducibility/versions.lock:88`: SO que nenhuma execução usa.

**Pontos positivos [V]:**
- `docs/02` já descreve o EEVS aditivo como padrão e o risco dele (`docs/02_modelo_de_decisao_h_rdl.md:163-164`).
- Os docs são escritos com a separação "verificado / não verificado" (por exemplo, `docs/11:92`).

### 3.8 Segurança

- **[V] Caminhos locais no próprio script de redação.** O `scripts/certification/redact_local_paths.py:64-67`, rastreado, contém caminhos absolutos de clones antigos com o nome de usuário. Fora isso, `git grep` não acha caminhos locais nos arquivos rastreados (exceto um *log* de terceiros em `third_party/xapps/xslice-oran/README.md:285`).
- **[V] Senhas padrão do upstream.** `deploy/helm/a1pms/files/application.yaml:51,112,114` mantém `policy_agent` no *keystore* e no *truststore*. O Neo4j, ao contrário, gera a senha aleatória e a guarda num `Secret` (`deploy/helm/kg-neo4j/templates/secret.yaml:2-14`), o que é bom.
- **[V] A1 e propostas sem autenticação** (pendência 5 de `docs/07_certificacao_e_achados.md:125`). Ver também 2.3.
- **[V] Cópias de segurança na pasta de trabalho.** Há `src.rar`, `scripts.rar`, `tests.rar`, `specs.rar` e `configs.rar` na raiz da F1, ignorados pelo `.gitignore`. [I] Expõem código antigo se a pasta for compartilhada.

### 3.9 Qualidade do código

- **[V] Tipagem fraca.** O `pyrightconfig.json` está no modo `basic`, com cerca de 20 regras desligadas (`reportOptionalMemberAccess`, `reportArgumentType`, `reportAttributeAccessIssue` etc.). Na prática a verificação pega só variáveis indefinidas, retornos e chamadas.
- **[V] Configuração dispersa.** Há 43 leituras de `os.getenv`/`os.environ` em `src/`, com cerca de 30 variáveis distintas. `RDLxApp.__init__` lê a maior parte delas diretamente (`src/rdl_xapp.py:117-246`). Existe `src/infrastructure/config_manager.py` (73 linhas), e o `pydantic` já é dependência, mas não há um esquema único validado na partida.
- **[V] Tratamento de erros amplo.** `src/` tem 59 `except Exception` e nenhum `except:` nu. O import do `ricxappframe` captura `(ImportError, OSError, Exception)` (`src/rdl_xapp.py:14`) e pode esconder erros reais de inicialização.
- **[V] *Logging* consistente.** O `structlog` é usado, e não há `print` em `src/`.

### 3.10 Dívida técnica (síntese)

| Item | Onde | Custo de carregar |
| :-- | :-- | :-- |
| `RDLxApp` monolítica e com E/S no construtor | `src/rdl_xapp.py` | todo experimento sobe servidores HTTP; testes frágeis |
| Relógio por *monkeypatch* | `run_conflict_experiment.py:163-164` | estado global; quebra com threads |
| Pacote `src` e `sys.path` | `pyproject.toml:51`, `src/greenran/common.py:27-30` | *wheel* inconsistente; risco de colisão |
| Baselines em quatro lugares | ver 3.2 | semânticas divergentes entre bancada, nativo e F2 |
| kpm-probe fora de `src` | `deploy/helm/xapp-kpm-probe/files/kpm_probe.py` | único E2 real sem testes |
| Duas entradas de proposta | `src/rdl_xapp.py:592,872` | validações duplicadas; atrito com a decisão nova |
| Documentação defasada | ver 3.7 | leitura errada do estado do projeto |

---

## 4. Melhorias já feitas

**Contagem de commits [V]:**
- F1: 583 commits; 63 na `main` desde 08/11 e 27 desde 10/11.
- F2: 364 commits; 12 desde 10/11.

| Data | Melhoria | Commit |
| :-- | :-- | :-- |
| 08/11 | Primeiro E2 Setup real NORI ↔ Near-RT RIC Release I no k3s | `52dea32e` |
| 08/11 | Dissecação E2AP independente e subscrição KPM real (G1) | `c3ab9cdf` |
| 08/11 | RIC Control E2SM-RC v3.01 com ACK correlacionado (G3) | `df2f7b15` |
| 08/11 | Cadeia de pré-registros v2 → v5, com calibrações inválidas relatadas | `3962e97d` … `6bb7773f` |
| 08/11 | G4 certificado (desenho v5) | `b2e5589c` |
| 08/11 | S0–S8 na bancada NORI; caminhos locais redigidos | `189de768`, `e17ea6c2` |
| 09/11 | Desenho v6: 30/30 `CONSISTENT`; regra v6 no G4 sem efeito retroativo | `4481b1c1`, `1d9e53b4` |
| 09/11 | Limpeza de dados sintéticos e scripts legados | `c7c14c98` |
| 09/11 | Desenho v7: H6.4 refutada | `db3d83c6` |
| 09/11 | G5 certificado (S8 × B0–B3 × 30 sementes), com desvios declarados antes | `392fb7f0`, `cdce38ba` |
| 09/11 | Observabilidade (InfluxDB + Grafana); causa raiz das quedas do WSL | `7c9345b6`, `d4677442` |
| 10/11 | Conflitos entre células, `CELL_STATE`, A1 ligada à decisão | `ff09d32c` |
| 10/11 | Pré-registro 08; percepção no relógio simulado | `08a67474` |
| 10/11 | Grafo de conhecimento, caminho crítico, A1 por RMR, SMO (A1-PMS), S9–S15 / G1–G2 sobre NR | `a0cb21eb`, `48fab8eb` |
| 10/11 | F2: saneamento (dados sintéticos removidos), núcleo da F1 como dependência, MAPPO calibrado | `1ab2a1e`, `8037ae9`, `c7dab7e` (F2) |
| 11/11 | Registro de recusas, aviso à xApp (30001), adiamento, caminho crítico com intervalo próprio | `3a7f81a1` |
| 11/11 | CI verde: Pyright, auditorias de proveniência, Gate 1, cobertura ≥ 85 % | `b5fc7644`, `d3882412`, `35eded2e` |
| 11/11 | Governança hierárquica (4 níveis), xApps por RMR, pré-registros 09/10 | `082849d3` |
| 11/11 | Histórico do grafo no Neo4j (chart `kg-neo4j`) | `cddf572a` |
| 11/11 | Dono e precedência por campo na A1 (conflito entre rApps) | `083c8e69` |
| 11/11 | xApps GreenRAN, rApp-ResourceOptimizer, perfis srsRAN/OAI, código original de terceiros e autoria | `ab4301fa` |
| 11/11 | Pré-registro 09: H10.1–H10.3 confirmadas | `054147e6` |
| 11/11 | F2: seleção de modelo por critério fixado e gate de reserva | `6c72ac3` (F2) |
| 12/11 | Mudança de pasta do repositório; redação dos clones antigos | `3e987504` |
| 12/11 | Pré-registro 10: desvio do S14 registrado antes do início | `d0cbd8fe` |
| 13/11 | Pré-registro 10: H11.1–H11.5 confirmadas, 160/160 `SUCCESS`, commit único | `8761f728` |
| 13/11 | EEVS aditivo como padrão (merge), com B3M para reproduzir as campanhas anteriores | `87f80113` |
| 13/11 | Desenhos do modelo de energia (doc 17) e da calibração de pesos (doc 18) | `3f8d7147` |
| 13/11 | Co-simulação em passo travado e orquestrador da malha fechada (E0–E1) | `13a68e44`, `b8ac56e6` |
| 13/11 | F2: pin da F1 em `9fefbff6` | `639d6b0` (F2) |

**Leitura [I]:**
- De 08 a 11/11, o projeto passou de evidência sintética a uma cadeia E2 real certificada até o G5.
- De 10 a 13/11, o foco mudou para governança, GreenRAN e a transição para malha fechada.
- Os achados 45 a 66 de `docs/07` registram correções feitas com rastreabilidade: o problema, a correção e o teste ou execução que a confirma.

---

## 5. Recomendações priorizadas (impacto × esforço)

Prioridade: **P1** = alto impacto e baixo esforço; **P2** = alto impacto e esforço médio; **P3** = impacto médio ou esforço alto.

| # | Prio. | Ação | Arquivo:linha | Impacto | Esforço |
| :-: | :-: | :-- | :-- | :-: | :-: |
| R1 | P1 | Tratar `RDL_MODE=governance` como modo com RMR real (não estrito) ou trocar o padrão do chart; falhar na partida se o modo for desconhecido; teste que renderiza o chart e confere o transporte | `src/rdl_xapp.py:121-123,252-267`; `deploy/helm/iqos-xapp-rdl/values.yaml:32`; `scripts/deploy_helm.sh:133` | Alto | Baixo |
| R2 | P1 | Atualizar os 9 trechos defasados da seção 3.7; acrescentar ao doc 06 os §5.9–5.11 (pré-registros 08–10) | ver 3.7 | Alto | Baixo |
| R3 | P1 | Gravar o SHA completo e `repo_dirty` nos manifestos e falhar (não usar `"unknown"`) fora do modo de teste; copiar `src_commit` para o manifesto NORI; o G0 passa a exigir os dois | `scripts/certification/run_conflict_experiment.py:278-291`; modelo em `XApp-RDL-F2/cardl/marl/train.py:43-62`; `scripts/run_nori_scenario.sh:30` | Alto | Baixo |
| R4 | P1 | Artigos: no SBRC, "duas configurações" (o S15 reproduz o S9); no IEEE da F1, separar a penalidade da média (S2, pré-registro 09) da regra de handover (S9, S10); citar o p99 de 17,6 ms no resumo; no resumo da F2, dizer que B1 = B2 = B3 | `artigos/sbrc_greenran/main.tex:29,33,153`; `artigos/ieee_fase1_hrdl/main.tex:33,311`; `artigos/ieee_fase2_cardl/main.tex` (resumo) | Alto | Baixo |
| R5 | P1 | Declarar a pseudorreplicação (S4, S12, S8/G5, S11, S15) nas ameaças e nos artigos; nos próximos pré-registros, definir a unidade de replicação e usar posições e tráfego dependentes da semente (correção prevista no achado 54); chamar H11.3 e H11.4 de verificações funcionais | `docs/06_metodologia_e_resultados.md:252-259`; `docs/07_certificacao_e_achados.md:103`; `docs/16` §9 (rascunho do pré-registro 11) | Alto | Baixo |
| R6 | P1 | CI: instalação do RMR que falha fechada, com fonte atual em vez de *stretch*; rodar a suíte uma só vez; adicionar `ruff` e `helm lint`/`helm template` para todos os charts; usar o `uv.lock`; disparar também em PRs de `malha-fechada` | `.github/workflows/ci.yml:31-35,57-78,93-102` | Médio | Baixo |
| R7 | P2 | Extrair um `DecisionPipeline` puro (Perception → Reasoning → Refinement) com relógio injetado; `RDLxApp` sem E/S no construtor (servidores só no `start()`); `HrdlStream` e o orquestrador usam a API pública | `src/rdl_xapp.py:181-188,318,1009-1291`; `run_conflict_experiment.py:141-210`; `src/core/perception.py`, `src/core/refinement.py` (uso de `time`) | Alto | Médio |
| R8 | P2 | Módulo único de baselines (`src/core/baselines.py`) com a semântica de B0 explícita por parâmetro (na chegada ou no fechamento da janela), usado pelo executor nativo, pelo orquestrador, pelo `catalog_loop` e pela F2 | ver 3.2 | Alto | Médio |
| R9 | P2 | Renomear o pacote `src` (por exemplo, `hrdl`), com um *shim* de compatibilidade por uma versão; levar `rdl_transport` para dentro do pacote; tirar `reference-xapps/` da imagem da RDL; versionar e criar *tags* a cada pin da F2 | `pyproject.toml:7,51`; `src/greenran/common.py:27-30`; `docker/Dockerfile` (`COPY reference-xapps`) | Alto | Médio |
| R10 | P2 | Levar a kpm-probe para `src/closed_loop/kpm_probe.py`, com testes de unidade (reprodução de um `kpm_probe_events.jsonl` real) e o chart só com o *entrypoint* | `deploy/helm/xapp-kpm-probe/files/kpm_probe.py` | Alto | Médio |
| R11 | P2 | Configuração tipada (`pydantic` Settings) reunindo as cerca de 30 variáveis, com validação na partida e uma tabela de variáveis gerada para `docs/04` | `src/rdl_xapp.py:117-246`; `src/infrastructure/config_manager.py` | Médio | Médio |
| R12 | P2 | Decisão nova (KPM e RC pela RDL): RC interceptado (12040) como entrada canônica; as xApps próprias e as do GreenRAN assinam KPM pelo SubMgr e emitem E2SM-RC; as derivadas leem KPM ou passam a se chamar "geradoras de conflito"; na malha fechada, o B3 recebe pelo RMR um processo `RDLxApp` (critério de pronto 2 do doc 16) | `src/rdl_xapp.py:592,872`; `src/governance/interception.py`; `reference-xapps/*`; `src/greenran/common.py:195-236`; `scripts/closed_loop/orchestrator.py:55-67` | Alto | Alto |
| R13 | P3 | Endurecer a NetworkPolicy e o pod: rótulo e *namespace* e registro com identidade forte; restringir 8080 e 8081; políticas de *egress*; `readOnlyRootFilesystem`, `seccompProfile: RuntimeDefault`; imagem por *digest*; remover o `rolloutTimestamp: now` | `deploy/helm/ric-governance/templates/networkpolicy-rdl.yaml`; `deploy/helm/iqos-xapp-rdl/values.yaml:3-6,24-28`; `templates/deployment.yaml:15` | Médio | Médio |
| R14 | P3 | Remover o `docker/docker-compose.yml` (obsoleto, `:latest`) | `docker/docker-compose.yml` | Baixo | Baixo |
| R15 | P3 | F2: instalar a F1 localmente no commit do pin (`uv pip install "xapp-rdl-f1 @ git+…@9fefbff6"` ou modo editável num *worktree* nesse commit); retreinar os *checkpoints* com o código determinístico e o pin atual, ou declarar a deriva `a0cb21eb` → `9fefbff6`; atualizar o README | `XApp-RDL-F2/pyproject.toml:18`; `XApp-RDL-F2/README.md:34-36`; `XApp-RDL-F2/experiments/training/*/training_manifest.json` | Médio | Médio |
| R16 | P3 | Pyright: religar aos poucos `reportOptionalMemberAccess`, `reportArgumentType` e `reportAttributeAccessIssue`; trocar os 59 `except Exception` por exceções específicas nos caminhos de E2 e A1 | `pyrightconfig.json`; `src/` | Médio | Médio |
| R17 | P3 | Cobertura: incluir `scripts/` no gate com meta própria; testar o orquestrador com `ReplayDriver` de ponta a ponta; remover o `omit` obsoleto; reorganizar os testes soltos em `tests/`; corrigir o escape em `test_kg_export.py:30` | `.coveragerc:4-6`; `scripts/closed_loop/orchestrator.py`; `tests/test_*.py` | Médio | Baixo |
| R18 | P3 | Tirar os caminhos pessoais do script de redação (lê-los de um arquivo local não rastreado ou de uma variável de ambiente); trocar `policy_agent` por `Secret` no chart do A1-PMS | `scripts/certification/redact_local_paths.py:64-67`; `deploy/helm/a1pms/files/application.yaml:51,112,114` | Médio | Baixo |
| R19 | P3 | Autenticar a identidade das xApps (proposta e interceptação) e o receptor A1 (R1/CAPIF ou mTLS no *service mesh*) | pendência 5 de `docs/07_certificacao_e_achados.md:125` | Alto | Alto |
| R20 | P3 | G6: pacote de reprodução independente (*runbook* mais imagem da pilha nativa), com reprodução por terceiro de uma campanha (por exemplo, o pré-registro 09) | `reproducibility/runbook.md`; `scripts/run_native_campaign.sh` | Alto | Alto |

**Ordem sugerida [I]:**
1. **Antes de nova campanha e da submissão dos artigos:** R1, R2, R3, R4 e R5, que são baratos e afetam a leitura da evidência.
2. **Junto com a malha fechada (doc 16):** R7, R8 e R10. Sem eles, cada baseline e cada relógio continua divergindo entre a bancada, o nativo e a malha fechada.
3. **Em seguida:** R12, que depende de R7 e R10, depois R9 e R6.
4. **O resto entra conforme o testbed GreenRAN:** R13 e R19 antes de qualquer RAN real.

---

## 6. Situação após as correções (2026-11-13, mesmo dia)

A pedido do autor, as recomendações foram verificadas uma a uma e corrigidas onde a correção cabia sem decisão nova do autor, sem execução na bancada e sem retreino. Esta sessão não fez commits. Parte das correções (código, testes, charts, `versions.lock` e certificador) entrou no commit `e6bebdf0`, feito às 13:48 por outra sessão junto com a renomeação para RDL-N1/RDL-N2; a mensagem desse commit não as descreve. O restante (CI, `.coveragerc`, `.gitignore`, testes movidos, remoção do compose, redação, A1-PMS, parte dos docs, pré-registros, esta seção e o README da F2) está sem commit. Os achados 67 a 70 de `docs/07` registram as correções.

**Dois problemas novos encontrados ao corrigir [V]:**
- O despacho da `RDLxApp` (`ControlDispatcher` + `src/e2/rc_encoder.py`) ainda usa o codificador RC não normativo; só a kpm-probe e a interceptação usam o codec v3. Mesmo com o RMR real (R1), a RDL do chart não comanda o NORI sozinha. Registrado em `docs/07` §1 e na pendência 11; entra no R12.
- Ao mover os testes soltos para `tests/unit/`, `test_rollback_timeout.py` passaria a ser ignorado pelo padrão `*rollback*` do `.gitignore` (a exceção só cobria `tests/`). Acrescentada a exceção `!tests/unit/*rollback*`.
- `tests/unit/test_closed_loop.py` (commit `13a68e44`) tinha o mesmo nome de `tests/interoperability/test_closed_loop.py`. Sem pacotes de teste, `pytest tests/` parava na coleta, e a etapa de suíte completa do CI antigo também falharia nesse ramo. Renomeado para `test_closed_loop_orchestrator.py`.

| # | Situação | O que foi feito | O que falta e por quê |
| :-: | :-- | :-- | :-- |
| R1 | **feito** | `parse_rdl_mode` com `OFFLINE_SIMULATION`, `GOVERNANCE` e `O_RAN_INTEROP`; `GOVERNANCE` usa o RMR real e falha sem `ricxappframe`; modo desconhecido impede a partida; `RDL_E2_NODE` no lugar do `gnb_01` fixo; `RDL_SERVE_HTTP`; testes em `tests/unit/test_rdl_mode.py`; `docs/02` §2 e README | verificar na bancada; o despacho RC da `RDLxApp` ainda é o não normativo (ver acima) |
| R2 | **feito** | os 9 trechos da seção 3.7: README dos pré-registros, `docs/07` §1, §2, §3 e §5, `docs/06` (achado 2 e novo §4.4 com os pré-registros 08–10), `docs/16` (status), README da F2, `versions.lock` (SO por perfil) e `.coveragerc` | — |
| R3 | **feito para as próximas execuções** | manifesto nativo com `repo_git_sha_full`, `repo_dirty`, `repo_dirty_paths` (`run_ns3_certified.sh`); `decision_log` com SHA completo e `repo_dirty`, e aviso em vez de `unknown` silencioso (`run_conflict_experiment.py`); manifesto NORI com `repo_git_sha` e `xapp_src_commit` (`run_nori_scenario.sh`, `deploy/helm/nori-ns3/files/run.sh`); regra informativa R15 no certificador (661 PASS, 17 WARN nas execuções de calibração e curva); testes em `tests/unit/test_provenance_commit.py` | os manifestos antigos não são reescritos (os hashes dependem deles); o manifesto NORI só muda depois de reimplantar o chart `nori-ns3` |
| R4 | **feito** | IEEE F1 (inglês e português): atribuição da penalidade de atraso corrigida (S9/S10 pela regra de handover; S15 = S9; custo da média no S13), p99 de 17,6 ms no resumo, pseudorreplicação nas ameaças; SBRC: "duas configurações" nos dois resumos e no corpo, pseudorreplicação nas limitações; F2: B1 = B2 = B3 no resumo. Os quatro compilam sem erro | o SBRC passou de 14 para 15 páginas: conferir o limite da chamada |
| R5 | **feito** | ameaças no `docs/06` §7, achado 70 em `docs/07`, ressalvas anotadas no pré-registro 10 §6 (inclusive o código entre o registro e a execução) e nos artigos | aplicar nos próximos pré-registros (unidade de replicação, sementes que mudam posições e tráfego) |
| R6 | **feito, não executado no GitHub** | `ci.yml`: ruff (E9, F63, F7, F82) em job próprio, `helm lint` + `helm template` de todos os charts, RMR com falha fechada (fonte conferida: responde 200), suíte rodada uma vez, gatilho em todo push | adotar o `uv.lock` no CI (o lock não é usado em lugar nenhum hoje; exige conferir se está sincronizado) |
| R7 | **parcial** | relógio injetável (`Perception.clock`, `Refinement.clock`), sem *monkeypatch* do módulo `time`; `RDLxApp.process_actions` público; `RDLxApp(serve_http=False)` nos executores | extrair um `DecisionPipeline` sem a `RDLxApp` inteira e tirar o resto da E/S do construtor; a `RDLxApp` continua com cerca de 1400 linhas |
| R8 | **feito na F1** | `src/core/baselines.py` usado pelo executor nativo, pelo orquestrador e pela bancada; `tests/unit/test_baselines.py`; regressão `tests/integration/test_schedule_replay.py`: os cronogramas de B0 (101), B1 (90), B2 (90), B3 (106) e B3A (15) registrados são reproduzidos byte a byte | F2 (`cardl/marl/baselines.py`): depende de commitar a F1 e mover o pin |
| R9 | **não feito** | — | renomear o pacote `src` muda todos os imports da F1 e da F2 e o pin; com outras sessões editando a mesma pasta, só com o trabalho delas commitado |
| R10 | **não feito** | — | mover a kpm-probe para `src/` exige reimplantar e validar na bancada NORI |
| R11 | **parcial** | `RDL_E2_NODE` e `RDL_SERVE_HTTP` documentados no README | configuração tipada única: refatoração do construtor da `RDLxApp`, melhor junto do R7 |
| R12 | **não feito** | o problema do despacho RC foi registrado | decisão de arquitetura do autor (entrada canônica 12040, xApps próprias emitindo E2SM-RC, B3 da malha fechada pelo RMR) |
| R13 | **parcial, não verificado no cluster** | `seccompProfile: RuntimeDefault`, `readOnlyRootFilesystem` com `/tmp` em `emptyDir` (cache do ASN.1 em `/tmp`), *digest* opcional da imagem, sem `rolloutTimestamp: now`; NetworkPolicy: 4561 só do `ricplt`, 8080/8081 só dos namespaces consumidores; `helm lint` e `helm template` limpos | políticas de *egress*; identidade forte do proponente (R19); verificar sondas e consumidores na bancada |
| R14 | **feito** | `docker/docker-compose.yml` removido (sem referências; continua no histórico do git) | — |
| R15 | **parcial** | README da F2 atualizado (seleção, ganho também sobre FIFO e prioridade, treino em `a0cb21eb`; entre `a0cb21eb` e o pin só o EEVS mudou no `reasoning.py`, não o TVS usado pelo B3 do ambiente) | retreinar no pin atual muda a evidência dos artigos: decisão do autor; o `.venv` local da F2 continua com a F1 da cópia de trabalho |
| R16 | **não feito** | — | o Pyright não está instalado no `.venv` nem no WSL; religar regras sem poder rodar seria às cegas |
| R17 | **parcial** | `omit` obsoleto removido; testes soltos movidos para `tests/unit/`; escape corrigido em `test_kg_export.py`; nome duplicado resolvido; testes de baselines e da regressão de decisão | `scripts/` continua fora do gate de cobertura |
| R18 | **feito** | o script de redação não grava mais nomes de usuário (padrões com qualquer usuário; 6 testes passam); a senha `policy_agent` do A1-PMS documentada como a do keystore público da imagem, sem uso na bancada (HTTP 8081) | trocar o keystore por um próprio fora da bancada |
| R19 | **não feito** | — | autenticação (R1/CAPIF ou mTLS) depende do SMO/infraestrutura |
| R20 | **não feito** | — | reprodução independente exige um terceiro |

**Testes depois das correções [V]:** `pytest tests/` (codec, unit, integration e interoperability numa só execução, como o CI novo): 478 passam, 1 pulado; cobertura de `src/` com ramos de 86,29 % (mínimo de 85 %). `ruff --select E9,F63,F7,F82`: sem erros. `helm lint` e `helm template` dos 9 charts: sem erros. Os quatro artigos compilam.

---

## Apêndice: o que foi executado nesta auditoria

- `git log`, `git diff --stat`, `git merge-base` e `git grep` nos dois repositórios, só leitura.
- `.venv/Scripts/python.exe -m pytest -q tests/unit` na F1, com `--cov=src --cov=scripts` (efeito colateral: o arquivo `.coverage`, ignorado pelo git, foi regravado). E `pytest -q` na F2.
- Leitura e contagem por *scripts* dos manifestos em `experiments/runs/*/execution_manifest.json`, de `experiments/xapp_logs/*/kpm_probe_events.jsonl` e dos CSVs em `artigos/dados/insights/`.
- Nada foi instalado, nenhuma campanha ou simulação foi executada, e nenhum arquivo dos repositórios foi alterado além deste relatório.
