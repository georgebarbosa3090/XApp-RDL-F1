# Relatório de Certificação Experimental — xApp RDL, Fase 1 (H-RDL)

- Data (UTC): 2026-11-08 (verificações executadas entre 01:33Z e 01:40Z)
- Ramo: `fix/e2-transport-and-arbitration`, HEAD `8e6dd82`
- Certificado gerado pelo certificador: `reports/certification/certificate_20261108T013327Z.{json,md}`
- Política aplicada: `reproducibility/provenance_policy.yaml`; versões de referência: `reproducibility/versions.lock`

**Cadeia closed-loop validada: NÃO**

Resumo: o simulador ns-3.48 / 5G-LENA v5.1 / NORI **não está instalado** no WSL (`Ubuntu`). Por isso nenhuma simulação foi executada nesta certificação. Não existe nenhuma execução elegível em `experiments/runs/`: as 210 execuções `S1_B0..B6_seed1001..1030` são suspeitas de origem sintética e a única outra execução (`certified_closed_loop_chain`) é uma fixture causal (`CAUSAL_FIXTURE`), que não pode ser publicada. Os 71 diretórios de FlowMonitor avulsos não têm manifesto e não comprovam E2. Nenhum gate de interoperabilidade (G1, G3, G4) foi certificado.

---

## 1. Ambiente e versões reais

| Item | Esperado (`versions.lock`) | Encontrado | Situação |
| :-- | :-- | :-- | :-- |
| Distribuição WSL | Ubuntu 22.04 LTS | Ubuntu 24.04.1 LTS (kernel 6.6.87.2-microsoft-standard-WSL2) | Diverge do lock |
| Usuário / HOME WSL | — | `george` / `/home/george` | — |
| `NS3_DIR` | `~/ns3-oran-workspace/ns-3-oran` | variável não definida; diretório **inexistente** | **Ausente** |
| ns-3 | 3.48 | não encontrado (`ns3`, `VERSION` ausentes) | **Ausente** |
| 5G-LENA (`contrib/nr`) | v5.1 | não encontrado | **Ausente** |
| NORI (`contrib/oran`) | `9b64c12` | não encontrado | **Ausente** |
| `libe2sim` | necessário para o NORI | não encontrada em `/usr/local/lib` | **Ausente** |
| Near-RT RIC (O-RAN SC Release J) | J | não verificado (sem simulador, sem alvo E2) | Não verificado |
| `tshark` | necessário para R14 | ausente no WSL e no Windows | **Ausente** |
| CMake | ≥ 3.25.2 | 3.28.3 | OK |
| GCC | ≥ 11.4.0 | 13.3.0 | OK |

Busca adicional: `find` em `/opt`, `/usr/local`, `/root`, `/home` e `/srv` (profundidade 7) não encontrou nenhum checkout `ns-3*`, executável `ns3`, `libns3*`, diretório `contrib`, 5G-LENA ou NORI. O único diretório relacionado é `/home/george/XApp-RDL-F2/simulations/ns3`, que contém fontes de cenário, não um simulador.

Consequência: conforme as regras de operação, **não rodei** `scripts/setup_ns3.sh` e **não executei** `scripts/certification/run_ns3_certified.sh` para `scenario_rdl_closed_loop_nori`, semente 1001 (o executor sairia com código 69, "ns-3 não encontrado").

## 2. Execuções e classificação

### 2.1 `experiments/runs/` (211 diretórios)

| Classe (certificador) | Qtde | Execuções | Motivos principais |
| :-- | --: | :-- | :-- |
| `SYNTHETIC_SUSPECT` | 210 | `S1_B0..B6_seed1001..1030` (30 sementes × 7 baselines) | Os run_id seguem o molde de `scripts/run_b0_b6_campaign_30seeds.py`, que gera métricas com `np.random.RandomState` / `rng.normal` / `rng.uniform` (L169–L218). Manifesto sem `source`, `run_status`, `exit_code`, `command`, `started_at_utc` e `finished_at_utc`. Nenhum FlowMonitor XML. Hashes divergentes em `execution_manifest.json`, `analysis/metrics.json` e `causal/causal_chain.jsonl`, ou seja, os arquivos foram alterados depois do registro dos hashes. Em 35 execuções há artefatos E2 `.raw` e PCAP, mas a decodificação com o codec local falha (`bitlen overflow: 640, max 336`) e o PCAP não foi dissecado de forma independente. O manifesto declara Ubuntu 20.04 e GCC 9.4.0, ambiente que não corresponde ao WSL atual. |
| `NON_PUBLICATION_SOURCE` | 1 | `certified_closed_loop_chain` | `provenance_category=CAUSAL_FIXTURE`, `status=LOCAL_INTEGRATION_FIXTURE`, `external_evidence=false`, `publication_eligible=false`. Os `.raw` têm de 12 a 17 bytes e o PCAP tem 397 bytes. Apesar do nome, não é uma execução certificada. |
| `ELIGIBLE` | **0** | — | — |

Não existe `experiments/runs/gate1/`.

### 2.2 FlowMonitor avulsos — `experiments/results/ns3_runs/`

Esses resultados **não são evidência E2**: o FlowMonitor isolado não comprova KPM, controle RC nem closed loop.

| Métrica | Valor |
| :-- | --: |
| Diretórios de execução | 71 |
| Com `flowmonitor.xml` | 69 |
| Com `run_status.json` | 18 (16 `completed`, 2 `failed`, ambos de `closed_loop_nori`) |
| Com manifesto (`execution_manifest.json`) ou `hashes.sha256` | **0** |
| Com artefato E2 (`.raw` / `.pcap`) | **0** |
| Entradas de fluxo, total | 968 |
| Fluxos com `rxPackets > 0` | 718 |
| Conteúdos distintos (SHA-256 de `flowmonitor.xml`) | 15 |
| Fluxos distintos, após deduplicar arquivos idênticos | 217 (101 com `rxPackets > 0`) |

Certificabilidade: **nenhum** desses diretórios é certificável. Faltam manifesto, versões registradas, comando, semente, código de saída e hashes, e o ambiente em que rodaram não foi registrado. Eles foram produzidos por `simulations/ns3/run_all_s0_s15_simulations.sh`, que não grava proveniência e que, ao final, executa `git add`, `git commit` e `git push origin main` automaticamente.

Cobertura por cenário:

| Cenário | Diretórios | Fluxos (total) | `rxPackets > 0` | Observação |
| :-- | --: | --: | --: | :-- |
| S0 `no_conflict` | 11 | 0 | 0 | `FlowStats` vazio em todas as execuções |
| S1 `direct_prb_conflict` | 6 | 144 | 144 | 6 arquivos byte-idênticos (24 fluxos) |
| S2 `energy_vs_qos` | 7 | 182 | 182 | 7 arquivos idênticos (26 fluxos) |
| S3 `tvs_conflict` | 7 | 252 | 252 | 7 arquivos idênticos (36 fluxos) |
| S4 `ts_vs_energy` | 5 | 0 | 0 | `FlowStats` vazio |
| S5 `temporal_pingpong` | 5 | 0 | 0 | `FlowStats` vazio |
| S6 `conflict_storm` | 5 | 0 | 0 | `FlowStats` vazio |
| S7 `fault_injection` | 5 | 0 | 0 | `FlowStats` vazio |
| S8 `closed_loop_nori` | 5 | 108 | 108 | 2 execuções falharam sem XML. Os 3 XML são **byte-idênticos ao de S3 `tvs_conflict`** (SHA-256 `6f2f16156c3c…`) |
| S9–S15 (6G/NTN) | 15 | 282 | 32 | Pares/trios de arquivos idênticos |

Anomalia relevante para S8: os FlowMonitor atribuídos a `closed_loop_nori` são idênticos, byte a byte, aos de `tvs_conflict`. O fonte de S8 grava `flowmonitor_s8_traffic.xml`, enquanto `tvs_conflict.cc` e `energy_vs_qos.cc` gravam ambos o nome genérico `flowmonitor_results.xml`, que também está na lista de busca do script de lote. Sem manifesto, não é possível atribuir esses arquivos ao cenário S8 com segurança. Eles devem ser tratados como de origem indeterminada.

## 3. Cenários de conflito S0–S7

O mapa de projeto anterior considerava ausentes os `.cc` de S0–S7. **Esse dado está desatualizado**: todos os oito fontes existem e estão versionados em `simulations/ns3/` (últimas alterações nos commits `0eee0d7` e `5dc5d48`, de 2026-11-04).

| ID | Arquivo | Existe | Execução elegível em `experiments/runs/` | FlowMonitor avulso |
| :-- | :-- | :-: | :-: | :-- |
| S0 | `scenario_rdl_no_conflict.cc` (270 linhas) | Sim | **Não** | 11, todos sem fluxos |
| S1 | `scenario_rdl_direct_prb_conflict.cc` (287) | Sim | **Não** (as 210 `S1_*` são `SYNTHETIC_SUSPECT`) | 6, com fluxos |
| S2 | `scenario_rdl_energy_vs_qos.cc` (368) | Sim | **Não** | 7, com fluxos |
| S3 | `scenario_rdl_tvs_conflict.cc` (415) | Sim | **Não** | 7, com fluxos |
| S4 | `scenario_rdl_ts_vs_energy.cc` (232) | Sim | **Não** | 5, sem fluxos |
| S5 | `scenario_rdl_temporal_pingpong.cc` (236) | Sim | **Não** | 5, sem fluxos |
| S6 | `scenario_rdl_conflict_storm.cc` (243) | Sim | **Não** | 5, sem fluxos |
| S7 | `scenario_rdl_fault_injection.cc` (232) | Sim | **Não** | 5, sem fluxos |

O que falta: nenhuma execução elegível, isto é, capturada pelo executor com proveniência e com E2 externo, para nenhum dos oito cenários. Em S0 e S4–S7, todas as execuções avulsas registraram `FlowStats` vazio. Assim, nem a camada de tráfego desses cenários produziu métricas mensuráveis. A instalação de aplicações/fluxos nesses fontes precisa ser revisada pelo pesquisador. Os cenários declaram `enableE2` e `ricIp:ricPort` (127.0.0.1:36422), mas nenhum artefato E2 foi capturado em qualquer execução.

## 4. Cadeia closed-loop, elo a elo

| # | Elo | Evidência elegível | Status | Observações |
| :-: | :-- | :-- | :-- | :-- |
| 1 | KPM_t0 (RIC Indication E2SM-KPM antes do controle) | Nenhuma | **NÃO EVIDENCIADO** | Fixture: `01_indication_t0.raw` (17 bytes, `CAUSAL_FIXTURE`). S1 sintéticas: `raw/kpm_t0.raw` com decodificação falha e hash divergente. |
| 2 | Decisão H-RDL (janela de 200 ms, arbitragem TVS→EEVS) | Nenhuma em execução elegível | **LOCAL_ONLY** | 195 testes unitários passando (G2). Não há log de decisão em execução com RAN real ou simulada com E2. |
| 3 | RIC Control Request (E2SM-RC) | Nenhuma | **NÃO EVIDENCIADO** | O próprio cabeçalho de `scenario_rdl_closed_loop_nori.cc` declara que o cenário "não aplica E2SM-RC nem fecha um loop de controle RDL->RAN". |
| 4 | RIC Control ACK / Failure | Nenhuma | **NÃO EVIDENCIADO** | Não há correlação RICrequestID/RANFunctionID em execução elegível. Nas S1, `R12.rc_correlation` falha em todas as 210. |
| 5 | Transição MAC (efeito do controle no escalonador) | Nenhuma | **NÃO EVIDENCIADO** | A fixture contém um log de texto (`05_ran_mac_transition.log`) que não foi produzido por uma execução do ns-3. O cenário S8 não aplica controle algum. |
| 6 | KPM_t1 (Indication após o controle, com efeito medido) | Nenhuma | **NÃO EVIDENCIADO** | O `causal_effect` da fixture (18,2→4,1 ms) não tem valor experimental. |

Elo inicial que falha: **elo 1 (KPM_t0)**. Não há sequer uma Indication KPM externa. Os elos 3–5 falhariam de qualquer forma, porque o cenário closed-loop atual não implementa a aplicação de E2SM-RC.

Alerta adicional: `scenario_rdl_closed_loop_nori.cc` (função `TraceLifecycleE2`, linhas 92–99) imprime por `std::cout` mensagens fixas de E2 Setup, Subscription e SCTP, com tempos fixos. Essas linhas não indicam troca real de mensagens e não podem ser citadas como evidência de E2.

## 5. Veredito por gate

| Gate | Veredito | Motivo |
| :-: | :-: | :-- |
| G0 | **NOT_CERTIFIED** | Nenhum manifesto registra todos os campos exigidos pela política. Não há ambiente ns-3/5G-LENA/NORI para obter versões reais. Os manifestos S1 declaram as versões do lock sem que elas existam no ambiente. |
| G1 | **NOT_CERTIFIED** | Nenhuma execução elegível com E2 Setup, Subscription e RIC Indication KPM externos (NORI). |
| G2 | **LOCAL_ONLY** | `pytest`: 195 passed, 1 warning (saída 0). Cobre a decisão determinística local e não certifica interoperabilidade. |
| G3 | **BLOCKED** | Depende de G1. Sem RIC Control e ACK externos correlacionados. |
| G4 | **BLOCKED** | Nenhuma cadeia closed-loop elegível. Fixture e execuções sintéticas não contam. |
| G5 | **BLOCKED** | Sementes elegíveis por baseline: B0=0, B1=0, B2=0, B3=0 (exigido: ≥ 30 pareadas por baseline). |
| G6 | **BLOCKED** | Requer G4 e G5 certificados e reprodução independente. |

Validadores complementares:

| Validador | Saída | Resultado |
| :-- | :-: | :-- |
| `scripts/certification/certify_chain.py` | 2 | G4 não certificado |
| `scripts/validate_provenance.py` | 1 | 210 execuções `PROVENANCE_INVALID` (sem `source`/`provenance_category`) e 1 `DEV/LOCAL` (`CAUSAL_FIXTURE`) |
| `scripts/verify_provenance_and_integrity.py` | 1 | 20 ocorrências de geradores estatísticos, sendo 12 em `scripts/run_b0_b6_campaign_30seeds.py` (uso efetivo) e 8 em `code_analyzer_validator.py` (padrões regex do próprio analisador, falso positivo) |
| `scripts/validate_experiment_tree.py --check-gate1` | 1 | `experiments/runs/gate1/` ausente; Gate 1 pendente |
| `scripts/check_no_synthetic_results.py` | 0 | Política YAML legível. O próprio script avisa que é uma varredura estática limitada e que **não** certifica a proveniência |

## 6. Limites desta certificação

- Nenhuma simulação foi executada, porque o simulador está ausente. Os vereditos refletem apenas os artefatos existentes no repositório.
- Não foi possível dissecar os PCAPs de forma independente, porque `tshark` está ausente. A decodificação com o codec local do projeto, que é um perfil E2SM-RC simplificado e não o ASN.1 oficial v1.03, só demonstra autoconsistência.
- Os hashes do pipeline comprovam integridade, não execução.
- O ambiente em que os FlowMonitor avulsos foram gerados não foi registrado. Não é possível confirmar versões de ns-3, 5G-LENA ou NORI para eles.
- Esta certificação não avaliou a corretude do código de produção (`src/`), além de registrar que a suíte de testes passa.
- Execuções feitas depois de 2026-11-08T01:40Z não estão cobertas.

## 7. Próximos passos concretos para obter evidência elegível

1. **Instalar o simulador**, com autorização do pesquisador, porque o processo é demorado e baixa código externo: `wsl -d Ubuntu -- bash scripts/setup_ns3.sh`. Em seguida, conferir as versões reais (`cat $NS3_DIR/VERSION` = 3.48; `git -C $NS3_DIR/contrib/nr describe --tags` = v5.1; `git -C $NS3_DIR/contrib/oran rev-parse --short HEAD` = `9b64c12`) e a presença de `libe2sim`. O setup cai silenciosamente para branches padrão e remove o NORI quando falta a `libe2sim`.
2. **Instalar `tshark`** no WSL, para dissecar os PCAPs com `-d sctp.port==36422,e2ap` (critério R14).
3. **Subir o Near-RT RIC O-RAN SC Release J** (E2Term 6.0.4, SubMgr 0.9.1, E2Mgr 5.4.9) e implantar a xApp RDL conforme `reproducibility/runbook.md` e `deploy/`, com captura de PCAP na porta SCTP 36422 em um diretório a ser passado em `--e2-trace-dir`.
4. **Corrigir o cenário S8** (decisão do pesquisador): implementar no `scenario_rdl_closed_loop_nori.cc` a recepção e a aplicação real do RIC Control E2SM-RC no escalonador NR, e remover ou rotular as mensagens fixas de `TraceLifecycleE2`. Sem isso, os elos 3–5 continuam impossíveis de evidenciar.
5. **Executar S8, semente 1001**, pelo executor com proveniência: `wsl -d Ubuntu -- bash /mnt/c/Users/georg/.antigravity-ide/XApp-RDL-F1/scripts/certification/run_ns3_certified.sh --scenario scenario_rdl_closed_loop_nori --seed 1001 --baseline B3 --e2-trace-dir <dir> -- --enableE2=true --simTime=10`, e depois rodar `certify_chain.py --run <run_id>`.
6. **Cenários S0–S7**: revisar por que S0 e S4–S7 geram `FlowStats` vazio. Dar nomes únicos aos FlowMonitor de `energy_vs_qos.cc` e `tvs_conflict.cc` (hoje ambos gravam `flowmonitor_results.xml`). Rodar esses cenários **somente** pelo executor certificado. O `run_all_s0_s15_simulations.sh` não grava manifesto e faz commit e push automáticos em `main`.
7. **Campanha G5**: no mínimo 30 sementes pareadas elegíveis por baseline B0–B3 (≥ 120 execuções), todas pelo executor certificado, com estatística pareada (IC95% t-Student, Wilcoxon, Cohen dz) somente depois de atingir N ≥ 30 pares.
8. **Higiene de evidências**: segregar ou rotular as 210 execuções `S1_B*` como sintéticas e renomear `certified_closed_loop_chain`, cujo nome sugere uma certificação inexistente. Alinhar o `versions.lock` (Ubuntu 22.04) ao ambiente efetivo (Ubuntu 24.04.1, GCC 13.3.0, CMake 3.28.3) ou provisionar o ambiente do lock.
9. **G6**: depois de G4 e G5, repetir a campanha em uma segunda máquina ou com outro operador, a partir dos manifestos, para a reprodução independente.

## 8. Comandos executados (código de saída)

| Comando | Saída |
| :-- | :-: |
| `wsl -d Ubuntu -- bash envcheck.sh` (verificação de `NS3_DIR`, `VERSION`, `contrib/nr`, `contrib/oran`, SO, CMake, GCC, `tshark`) | 0 (simulador ausente) |
| `wsl -d Ubuntu -- bash envcheck2.sh` (busca ampla por ns-3/5G-LENA/NORI/`libe2sim`) | 0 (nada encontrado) |
| `run_ns3_certified.sh … scenario_rdl_closed_loop_nori --seed 1001` | não executado (simulador ausente) |
| `PYTHONIOENCODING=utf-8 uv run --no-sync python scripts/certification/certify_chain.py` | 2 |
| `PYTHONIOENCODING=utf-8 uv run --no-sync python scripts/validate_provenance.py` | 1 |
| `PYTHONIOENCODING=utf-8 uv run --no-sync python scripts/verify_provenance_and_integrity.py` | 1 |
| `PYTHONIOENCODING=utf-8 uv run --no-sync python scripts/validate_experiment_tree.py --check-gate1` | 1 |
| `PYTHONIOENCODING=utf-8 uv run --no-sync python scripts/check_no_synthetic_results.py` | 0 |
| `uv run --no-sync pytest -q -p no:cacheprovider` | 0 (195 passed) |
| `git status --short` (antes e depois) | 0 (nenhum arquivo versionado alterado; nada a reverter) |

---

## Errata e atualização (2026-11-08, 02:22 UTC)

1. **Hashes "divergentes" das execuções `S1_B*`:** a divergência era um artefato da conversão de fim de linha do Git no Windows (`core.autocrlf=true`), não alteração dos arquivos. Os bytes originais armazenados no Git conferem com `hashes.sha256` (por exemplo, `S1_B3_seed1001`: 3/3 arquivos OK com `sha256sum -c`). O repositório passou a marcar `experiments/runs/** -text` em `.gitattributes`. As 210 execuções **continuam** classificadas como `SYNTHETIC_SUSPECT` (geradas por `scripts/run_b0_b6_campaign_30seeds.py` com RNG estatístico); 35 delas têm arquivos fora do manifesto de hashes. As menções a "hash divergente" na seção 3 e no elo 1 da seção 5 devem ser lidas com esta correção.
2. **Pilha nativa instalada:** ns-3.48 (`d2add90`) + 5G-LENA v5.1 (`cedcead`) compilados no WSL; os cenários S0–S8 compilam.
3. **Primeiras execuções reais com proveniência:** `S1_native_traffic_seed1001` e `S1_native_traffic_seed1002` (S1, 10 s, backend `NS3_5GLENA`): 20 fluxos de usuário, perda de 0,025 % e atraso médio de 4,99 ms em ambas, com saídas distintas por semente. **G0: CERTIFIED** para a pilha nativa (certificado `certificate_20261108T022204Z`).
4. **Limitação dos cenários:** nenhum cenário S0–S8 altera parâmetros da RAN (`conflictStart`/`conflictEnd` não agendam eventos). Os resultados são de tráfego NR de base e não medem conflitos nem a H-RDL. Além disso, os cenários anulam `--RngRun` com `SetSeed(--seed)`; o executor passou a usar `--seed`.
5. Os demais vereditos não mudaram: G1 NOT_CERTIFIED, G2 LOCAL_ONLY, G3–G6 BLOCKED. **Cadeia closed-loop validada: NÃO.**
