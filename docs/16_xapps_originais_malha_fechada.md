# 16. xApps originais em malha fechada nas simulações de cenário

Status (2026-11-13): **em implementação.** Desenho escrito em 2026-11-12, durante a campanha 10, e commitado depois dela. Implementado: co-simulação em passo travado e orquestrador (E0–E1, `13a68e44`), shim `libe42_shim` e driver das xApps originais do FlexRIC (E2, `cb770c8a`). Pendente: TS, pré-registro 11 e a cadeia pelo RMR (critério 2 abaixo): hoje o orquestrador decide o B3 no próprio processo (`RDLxApp.process_actions`), sem o RMR 30000, o registro de xApps e a janela.

## 1. Decisão

Decisão do autor em 2026-11-12:

- Toda campanha e toda simulação de cenário (S\*, G\*) executa obrigatoriamente os processos das xApps, para que a simulação seja real e a cadeia completa possa ser verificada.
- Nas campanhas, as três reimplementações em Python de `reference-xapps/` (`qos-xslice`, `energy-saving` e `traffic-steering`) dão lugar ao código original de `third_party/xapps/`, compilado sem alterar a lógica de decisão.
- **Revisão de 2026-11-12 (D5):** os derivados em Python dos originais **ficam no repositório**, junto com os charts, os testes e a documentação deles. Só deixam de ser a fonte das propostas nas campanhas de cenário. Isso anula a remoção prevista antes. Eles ganham dois papéis (seção 7, "Derivados"): controle pareado contra os originais e ponte para o testbed com OSC RIC.
- Um adaptador fino substitui o RIC:
  - entrega ao código original os KPM medidos no ns-3;
  - converte o controle que sai (E2SM-RC ou gRPC RC) em proposta `RDL_ACTION_PROPOSAL` (RMR 30000) para a RDL.
Pronto quando:

1. os cenários S\* e G\* rodam com os processos das xApps no laço;
2. o teste de cadeia passa: xApp → 30000 → RDL → ação → ns-3 → KPM → xApp;
3. a documentação de `reference-xapps/` diz que os derivados em Python não geram as propostas das campanhas.

## 2. Ponto de partida: malha aberta

- `scripts/certification/run_conflict_experiment.py` monta as propostas a partir do `catalog.json` (`expand_proposals`). Com isso, `decide()` aplica B0–B3 e produz o cronograma **antes** de o ns-3 rodar.
- O ns-3 lê o cronograma (`RdlActuation`, `simulations/ns3/rdl-nr-common.h`) e agenda cada ação com `Simulator::Schedule`. Nenhum KPM volta para quem decide.
- O `RdlKpiSampler` grava só por célula, a cada período: pacotes, bytes, vazão e atraso médio. Não há SINR por UE, vizinhas, uso de PRB nem métricas por fatia, que as xApps originais exigem (seção 4).
- Nenhuma xApp roda como processo em nenhuma campanha (`reference-xapps/README.md` §2, `docs/03` §4).

## 3. Arquitetura alvo: co-simulação por janela

```
 ns-3 (5G-LENA)                     orquestrador (Python, WSL)                  processos das xApps
 ─────────────                      ──────────────────────────                  ───────────────────
 a cada 200 ms simulados:
   RdlKpmExporter ──KPM(JSON)──►  recebe KPM da janela k
   (pausa o ns-3, bloqueante)         │
                                      ├─► adaptador FlexRIC (shim e42) ──► xSlice / ES Orange (C original)
                                      ├─► adaptador O-RAN SC (RMR, gRPC)  ──► ric-app-ts (C++ original)
                                      ├─► xApps próprias (GreenRAN, Rogue) via RMR
                                      │        ◄── RC Control / gRPC RC ──┘
                                      │   adaptadores → RMR 30000 (RDL_ACTION_PROPOSAL)
                                      ▼
                                   barreira da janela (todas as xApps responderam ou esgotou o prazo)
                                   baseline B0 | B1 | B2 | B3 (RDL-N1 real, RMR 30000/30001)
   RdlActuation ◄──ações(JSON)──   ações da janela k
   aplica e retoma o ns-3
```

### 3.1 Interface ns-3 ↔ orquestrador

- **Novo modo em `rdl-nr-common.h`:** `--control-socket=<caminho>`, com um socket Unix em passo travado (*lockstep*). O modo atual, com `--action-schedule`, continua para reproduzir as campanhas anteriores.
- **No fechamento de cada janela** (`decision_window_s` = 0,2 s), um evento do `Simulator` faz o seguinte:
  1. serializa o KPM da janela;
  2. escreve no socket e **bloqueia** na leitura das ações;
  3. aplica as ações com o `RdlActuation::Apply` atual, no mesmo instante simulado.
  
  Como o simulador é de eventos discretos, o tempo de parede gasto pelas xApps não afeta o tempo simulado.
- **KPM por janela** (amplia o `RdlKpiSampler`):
  - por célula: vazão, atraso, pacotes, uso de PRB, UEs conectados, estado (ligada, desligada) e potência;
  - por UE: célula servidora, SINR servidora, SINR e RSRP das vizinhas, vazão e atraso; desde 2026-11-21, também a fatia (`sst`, como o `DRB.NetworkSlicing.SST`), declarada pelo cenário com `RdlActuation::SetUeSst` (S1, S2, S3; `--ueGroupSst` no `scenario_rdl_multicell`). UE sem fatia declarada reporta SST 1 (§10.16);
  - por fatia: vazão, atraso e PRB usados, agregados pelo orquestrador a partir do `sst` de cada UE (o xSlice usa 3 fatias).
  
  Todas as fontes já existem no 5G-LENA: traces de PHY/MAC e RRC.
- **Registro:** o KPM enviado e as ações recebidas vão para `raw/` da execução e entram nos hashes. Para refazer a decisão de uma execução, basta ler o registro, sem rodar as xApps de novo.

### 3.2 Tempo

- O orquestrador entrega a cada xApp o tempo simulado no KPM.
- **Relógio de parede no ES Orange:** ele usa `time(NULL)` (`SHUTDOWN_TIMEOUT_SEC = 30`). Para não alterar o código, o processo roda com `libfaketime` (apt), num relógio que o orquestrador avança junto com o tempo simulado (modo de arquivo de tempo do `FAKETIME`).
- **Limite dos cenários curtos:** os cenários com 10–60 s simulados mal chegam aos 30 s do ES. Isso é limite do original e será relatado, não ajustado.

### 3.3 Barreira por janela e determinismo

- **xApps FlexRIC:** o shim chama os *callbacks* de indicação na própria thread. Quando o *callback* volta, os controles da janela já saíram.
- **TS:** o adaptador manda as entradas da janela e espera um destes dois desfechos:
  - o gRPC de controle;
  - uma marca de "janela sem controle", que o adaptador emite quando o TS responde ao 30003 com o 30004 e não envia gRPC dentro do prazo (ver a seção 4.3).
- **Prazo:** cada xApp tem um prazo de parede por janela, com valor inicial de 2 s. Se ele esgotar, a janela segue sem as propostas daquela xApp e o fato fica registrado (`xapp_timeout`).
- **Determinismo:**
  - as xApps assíncronas podem tornar a execução variar entre repetições;
  - o PPO do xSlice aprende em linha e usa aleatoriedade própria, que deve ser semeada pelo orquestrador quando o código permitir;
  - o piloto mede isso repetindo a mesma semente duas vezes (pré-registro 11, §5).
  - **Resultado (semente 16904, B3, 2026-11-18):** `scripts/run_closed_loop_pilot.sh --repeat 2` rodou os nove cenários do piloto (G1, G2, S9–S15) duas vezes, com todas as xApps do cenário, o TS original e a cadeia E2. `scripts/closed_loop/comparar_determinismo.py --seed 16904` deu **9 de 9 pares idênticos**: nenhuma janela diverge em KPM, propostas, decisão ou ações, e os arquivos da cadeia E2, da atuação e da série de KPI são iguais byte a byte. A barreira por janela e o prazo por xApp bastam para tornar a malha fechada determinística nesses cenários, inclusive com o TS em processo separado. Pelo §5 do pré-registro 11, a variância vem só das sementes, e o número de sementes não precisa crescer por não determinismo. Relatório em `reports/avaliacao/determinismo_seed16904/`. O xSlice original (PPO em linha) ainda não entrou na malha fechada e terá de ser medido quando entrar.

## 4. Adaptador de cada original

### 4.1 xSlice (peihaoY/xslice-oran, commit `87db3bd`)

- **Achado de 2026-11-12:** o `xapp_xslice.c` copiado só **aplica** a decisão.
  - Ele lê quatro inteiros de `flexric/trandata/slice_ctrl.bin`: os PRB dedicados das 3 fatias e uma marca de prontidão.
  - Monta um RC Control formato 1 `RRM_Policy_Ratio_List`, com 3 fatias, SST "1" e mínimo, dedicado e máximo.
  - Grava o KPM por UE em `flexric/trandata/KPM_UE.txt`, com período de 10 ms.
  - **A decisão é do agente DRL** (PPO com GCN) da pasta `GNNRL/` do mesmo repositório, que não foi copiada para `third_party/`. Rodar o xSlice original exige também o `GNNRL/` e o PyTorch no WSL.
- **Adaptador:** biblioteca `libe42_shim` com a mesma API de `src/xApp/e42_xapp_api.h`: `init_xapp_api`, `e2_nodes_xapp_api`, `report_sm_xapp_api`, `rm_report_sm_xapp_api`, `control_sm_xapp_api` e `try_stop_xapp_api`. Ela é compilada contra os cabeçalhos das SM do próprio fork, para que as estruturas `rc_sm` e `kpm_sm` sejam idênticas às do original.
  - **Indicações:** KPM e MAC da janela. O shim chama o *callback* uma vez por período de 10 ms dentro da janela, ou seja, 20 indicações por janela de 200 ms.
  - **Controle:** do RRM ratio dedicado da fatia alvo sai `PRB_QUOTA` (em %), com `xapp_id = "xslice"`.
- **Caminhos:** o original usa `flexric/trandata/` relativo ao diretório de trabalho. O orquestrador cria essa árvore no diretório de cada execução e não altera o código.

### 4.2 Energy Saving Orange (FlexRIC, ramo `oie-ric-taap-xapps`, commit `f56d448`)

- **Entradas:** indicações KPM v3, a cada 100 ms, com SINR por UE na célula servidora e nas vizinhas.
- **Lógica:**
  - marca para desligamento a célula com até 1 UE conectado;
  - faz o handover desses UEs para a vizinha de maior SINR (RC Handover Control, 8.4.4.1);
  - depois desliga a célula (estado `CELL_OFF`/`CELL_SLEEP`), com 30 s de espera.
- **Adaptador:** o mesmo `libe42_shim`, compilado contra os cabeçalhos deste ramo.
  - **Controle de handover:** vira `HANDOVER`, com o valor igual ao índice da célula de destino.
  - **Desligamento:** vira `CELL_STATE` = 0.
  - **Origem:** `xapp_id = "energy_saving"`, ou `energy_saving_ru0`/`energy_saving_ru1` quando há uma instância por RU, como no G2.
- **Consequência:** o original só propõe `HANDOVER` e `CELL_STATE`. Os papéis de `energy_saving` com `TX_POWER` ou `PRB_QUOTA` no catálogo (S0, S1, S3, S4, S6, S10, S12, S15 e G1) não existem no original. Ver a seção 5.

### 4.3 Traffic Steering (o-ran-sc/ric-app-ts, commit `beb44e0`)

- **Dependências:** `ricxfcpp` (xapp-frame-cpp), `rmr_si`, rapidjson, gRPC/protobuf (`rc_objects`, gerado do `rc.proto` em `ext/protobuf` do repositório completo) e curl. A cópia em `third_party/` traz só `src/ts_xapp` e `src/utils`, então o build exige o repositório completo no mesmo commit.
- **Fluxo do original:**
  1. a xApp AD informa a anomalia de UE (30003);
  2. o TS envia a lista de UEs ao QP (`TS_UE_LIST`, 30000) e responde ao AD (30004);
  3. o QP devolve a vazão prevista por célula (`TS_QOE_PREDICTION`, 30002);
  4. se uma vizinha supera a servidora acima do limiar (A1 tipo 20008, `threshold`, pela msg 20010), o TS pede o handover por gRPC (`SendRICControlReqServiceGrpc`) à RC xApp.
- **Adaptador (implementado em `scripts/closed_loop/ts_driver.py`, E3 concluída em 2026-11-13):**
  - **caminho de controle:** o TS tem dois caminhos originais, gRPC para a RC xApp e REST (`ts_control_api: rest`, o padrão do descritor do próprio repositório). O adaptador usa o REST: o descritor original é copiado com o `ts_control_ep` apontando para um servidor HTTP do adaptador, que recebe o `HandOff` (`ue`, `fromCell`, `toCell`) e o converte em proposta `HANDOVER` do UE, com `xapp_id = "traffic_steering"` e `xapp_impl: original`. A lógica de decisão do TS não muda; o gRPC fica para o testbed, com a RC xApp;
  - **papel do AD (D3, regra escolhida pelo autor em 2026-11-14: taxa oferecida):** a cada janela, vão ao TS pelo 30003, no formato do AD original, os UEs conectados cuja vazão média entregue na janela deslizante de `anomaly_window_s` (1 s) ficou abaixo de `anomaly_frac` (50 %) da taxa oferecida pela aplicação do cenário (`--packetSize` × 8 ÷ `intervalMs` do grupo em `--ueGroups`; `ue_offered_mbps` no orquestrador). A regra não depende do volume de tráfego do cenário, e a janela de 1 s absorve a granularidade de 1 ou 2 pacotes por janela de 200 ms. Antes de `min_observation_s` (1 s) nada é enviado. Os modos `absoluto` e `relativo` ficam no driver só para comparação (§8.1);
  - **papel do QP (D3):** para cada UE da lista 30000, devolve pelo 30002 a vazão **medida** na servidora (primeira célula, como o TS exige) e, nas vizinhas, a medida escalada pela capacidade de Shannon, com o SINR da vizinha estimado por SINR servidor + (RSRP vizinha − RSRP servidora). A estimativa é a mesma do shim do ES (§8) e é declarada no relato;
  - **política A1:** o adaptador envia o 20010 (tipo 20008, `threshold` em %) no início da execução;
  - **RMR:** `librmr_si` do O-RAN SC carregada por `ctypes`, com tabelas de rotas estáticas por processo (`RMR_SEED_RT`, `RMR_RTG_SVC=-1`).
- **Build (`xapps-originais/ts/build.sh`, sem `sudo` e sem download novo):**
  - RMR e o **núcleo** do xapp-frame-cpp (messaging, json, alarm, metrics, config, xapp). Os módulos `rest-client` (cpprest) e `rest-server` (Pistache) do framework não são usados pelo TS, que tem o próprio cliente REST com curl, e ficam fora, como no shim do FlexRIC;
  - o repositório traz `rc.pb.*` e `rc.grpc.pb.*` gerados por um protoc antigo, incompatível com o protobuf 3.21 do Ubuntu. Numa cópia de build, só esse código gerado é regenerado a partir do `rc.proto` original; o `sha256` do `ts_xapp.cpp` é conferido no original e na cópia;
  - o link usa `--copy-dt-needed-entries`, porque o gRPC do Ubuntu separa a `libgpr` e o CMake original só lista `grpc++`.
- **Teste:** `tests/integration/test_ts_original.py` (no WSL, pelo `scripts/closed_loop/run_test_wsl.py`). Com três UEs, o TS recebe a A1 (limiar 5 %), é consultado só pelos dois UEs anômalos, pede `HandOff` apenas do UE cuja vizinha é melhor e mantém o outro ("serving cell is the best one").
- **Colisão do RMR 30000:** o TS usa 30000 (`TS_UE_LIST`) e a RDL usa 30000 (`RDL_ACTION_PROPOSAL`).
  - **Regra:** cada processo tem a própria tabela de rotas (`RMR_SEED_RT`). Na do TS, 30000 vai **só** para o endpoint QP do adaptador. Na do adaptador, 30000 vai para a RDL. O TS não tem rota para a RDL.
  - **Defesa extra:** a RDL já valida o esquema da proposta e o registro de xApps no modo estrito. Uma `TS_UE_LIST` que chegue à RDL é recusada e registrada.
  - **Teste:** um teste de integração verifica que nenhuma mensagem do TS chega à porta da RDL.
  - **Na malha fechada (E3):** a RDL recebe as propostas do orquestrador, não pelo RMR. A tabela do TS tem uma única rota, 30000 → adaptador, então a colisão não ocorre. A regra acima continua valendo para o testbed.

### 4.4 xApps próprias que ficam

- **GreenRAN:** RANSlicer-GreenRAN e EnergySaver-GreenRAN (`src/greenran/`), com KPM do orquestrador e proposta pelo `rdl_transport` (RMR).
- **Rogue:** `reference-xapps/rogue-xapp/`, idem.
- **URLLC Slice Guard** (`src/xapps/proprias.py`, `UrllcSliceGuard`; desde 2026-11-21, §10.16): faz o papel `xslice` do catálogo enquanto o xSlice original não estiver integrado (§4.1). Até 2026-11-21, esse papel era da derivada `XSliceDerivada` (`xapp_id` `xslice`, `xapp_impl: derivado`). Ela passou a ser declarada como xApp própria, com nome próprio, porque não reproduz a decisão do xSlice, que é de um agente PPO com GCN.

## 5. Mapeamento dos `xapp_id` do catálogo

| `xapp_id` | Cenários | Fonte da proposta em malha fechada | Situação |
| :-- | :-- | :-- | :-- |
| `xslice` | S0, S1, S2, S3, S6, S7, S8, S12, S14 | xSlice original (C e GNNRL); **hoje a URLLC Slice Guard** (própria, `xapp_id` `urllc_slice_guard`; §4.4 e §10.16) | só `PRB_QUOTA`; o `TX_POWER` do S3 não existe no original; o original não está integrado |
| `traffic_steering` | S2, S4, S5, S9, S10, S11, S13, S15, G2 | ric-app-ts original | `HANDOVER` |
| `energy_saving` | S0, S1, S3, S4, S6, S9, S10, S12, S13, S15, G1 | ES Orange original | só `HANDOVER` e `CELL_STATE` (ver 4.2); no G1, decidir entre o ES Orange e a EnergySaver-GreenRAN (D1) |
| `energy_saving_ru0/ru1` | G2 | duas instâncias do ES Orange, ou a EnergySaver-GreenRAN | D1 |
| `ranslicer` | G1 | RANSlicer-GreenRAN (própria) | pronta para adaptar |
| `rogue_xapp` | S7, S15 | rogue-xapp (própria) | pronta para adaptar |
| `fault_injector` | S13 | evento do cenário ns-3, não é xApp | sai das propostas e vira falha agendada |
| `load_balancer` | S5, S6, S11 | sem original | D2 |
| `beamformer` | S6 | sem original | D2 |
| `isac_radar` | S6, S14 | sem original | D2 |
| `embb_throughput` | S8 | sem original | D2 |
| `cco` (só na malha fechada, `extra_roles`) | S4, S6 | CCO própria (§10.17) | `TX_POWER` |
| `ue_scheduler` (só na malha fechada, `extra_roles`) | S1 | escalonador por UE próprio (§10.17) | `SCHEDULER_WEIGHT`, com `--scheduler=pf` |
| `mro` (só na malha fechada, `extra_roles`) | S5 | MRO própria (§10.17) | `A3_OFFSET`, com `--handoverAlgo=mro` |

Quando a xApp roda de verdade, o conflito de cada cenário deixa de ser montado à mão: ele aparece ou não conforme o que as xApps propõem diante do KPM. O catálogo passa a fixar a topologia, o tráfego, as xApps presentes e os parâmetros delas (limiar A1, fatias), e não mais as propostas.

## 6. Dependências a baixar

Todas vão para o Ubuntu do WSL. O disco virtual (`ext4.vhdx`) fica no C:, que tinha 46 GB livres em 12/11/2026. O WSL tem 5 GB de RAM. Antes de baixar, peço permissão ao autor com o nome, a origem e o tamanho medido, e confiro o espaço livre.

| Item | Origem | Tamanho | Para quê |
| :-- | :-- | :-- | :-- |
| xslice-oran no commit `87db3bd` (árvore FlexRIC do fork e `GNNRL/`) | github.com/peihaoY/xslice-oran | a medir (API do GitHub) | cabeçalhos das SM e agente PPO/GCN |
| flexric, ramo `oie-ric-taap-xapps`, commit `f56d448` | gitlab.eurecom.fr/mosaic5g/flexric | a medir | cabeçalhos das SM do ES Orange |
| ric-app-ts completo no commit `beb44e0` (com `ext/protobuf`) | github.com/o-ran-sc/ric-app-ts | a medir | `rc.proto` e build do TS |
| RMR (`rmr`, `rmr-dev`, .deb) | o-ran-sc (packagecloud) | ~1–2 MB | transporte RMR |
| xapp-frame-cpp (`ricxfcpp`, .deb) | o-ran-sc (packagecloud) | ~1–2 MB | arcabouço do TS |
| apt: `build-essential cmake libsctp-dev libpcre2-dev rapidjson-dev libcurl4-openssl-dev libgrpc++-dev libprotobuf-dev protobuf-compiler-grpc libfaketime` | Ubuntu | ~300–500 MB instalados (estimativa) | build e relógio do ES |
| PyTorch CPU e dependências do `GNNRL/` | PyPI | ~200–800 MB (estimativa) | agente do xSlice |

Se o pip, o git, o ns-3 e os builds disputarem a RAM com uma campanha, nada disso roda durante campanha.

## 7. Decisões do autor (2026-11-12)

| # | Decisão |
| :-- | :-- |
| D1 | No G1 e no G2, a economia de energia fica com a **EnergySaver-GreenRAN**. O ES Orange original fica nos cenários S. |
| D2 | `load_balancer`, `beamformer`, `isac_radar` e `embb_throughput` viram **xApps próprias**, com lógica documentada, que leem o KPM e propõem pela 30000. S5, S6, S8, S11 e S14 continuam. |
| D3 | AD e QP são **emulados no adaptador**: anomalia quando a vazão do UE cai abaixo de um limiar fixado no pré-registro, e predição igual à vazão medida no ns-3. |
| D4 | O PPO do xSlice parte de um **modelo pré-treinado** em execuções de aquecimento pré-registradas, com sementes separadas, e fica congelado nas campanhas. |
| D5 | Os cenários que perdem o conflito (S3 com `TX_POWER` do xSlice; S0, S3, S4 e S10 com `TX_POWER` do ES) **mudam de parâmetro**: o conflito é refeito com `PRB_QUOTA`, `HANDOVER` ou `CELL_STATE`, que os originais propõem. A definição desses cenários muda e entra no pré-registro 11. Os derivados em Python dos originais ficam no repositório (seção 1). |
| Ordem | Os pré-registros 12 (energia, doc 17) e 13 (calibração, doc 18) **esperam este desenho** e rodam já em malha fechada, sem exceção à regra. |
| Sementes | O pré-registro 11 usa **16001 a 16005**. As 12001 a 12005 já foram rodadas no pré-registro 09. |
| Derivados (a) | **Controle pareado.** Nos cenários em que o derivado e o original propõem o mesmo parâmetro, o cenário roda também com o derivado no papel do original, com as mesmas sementes e baselines: xSlice com `PRB_QUOTA` e Traffic Steering com `HANDOVER`. O objetivo é medir quanto a reimplementação se afasta do original e se os números já publicados (campanhas 01 a 10, cujo catálogo reproduz o papel dos derivados) continuam valendo. O Energy Saving não tem par direto: o derivado propõe `TX_POWER`, e o original, `HANDOVER` e `CELL_STATE`. Para a comparação ser justa, o derivado passa a ler o KPM do ns-3 pelo mesmo adaptador, sem mudar a regra de decisão documentada. As execuções com derivado são marcadas no manifesto (`xapp_impl: derivado`) e nunca contam como execução com o original. Cenários, métrica de afastamento e critério ficam no pré-registro 11, ou num 11b. **Revisão de 2026-11-21 (§10.16):** o papel `xslice` não tem mais derivado. A URLLC Slice Guard é declarada como xApp própria (`xapp_impl: propria`), e o controle pareado fica só para o Traffic Steering. |
| Derivados (b) | **Ponte para o testbed.** No laboratório com srsRAN e OSC RIC (perfil GERCOM; ver `docs/compliance/VARREDURA_TESTBEDS_OPENRAN_BRASIL.md` §5), os originais do xSlice e do ES, que são xApps do FlexRIC, não rodam. Os derivados, que falam RMR com a RDL e já têm charts Helm, levam esses papéis à bancada real, inclusive no gate TB7 (arbitragem entre duas xApps reais). O papel vale até existir uma ponte E42 ↔ RMR. No laboratório com OAI e FlexRIC, rodam os originais. **Ressalva (2026-11-12):** a equipe informou que o testbed não terá fatiamento. Sem fatias, o papel do xSlice na bancada depende das propostas P1 (fatia no núcleo) ou P3 (teto de PRB da célula) da [varredura dos testbeds, §7](compliance/VARREDURA_TESTBEDS_OPENRAN_BRASIL.md). |
| ES Orange nos cenários S (2026-11-13) | **Defeito no original:** em `add_UE` (linha 177 de `xapp_es_with_cell_util.c`), `numOfConnectedUEs` soma 1 a cada indicação, e não a cada UE novo. Com relatórios periódicos, a célula com um único UE conta 2 na segunda indicação, e o critério "no máximo 1 UE", verificado a cada 5 s, nunca é atendido. A xApp recebe e registra o KPM pelo shim, mas não emite controle. O teste `tests/integration/test_shim_es_orange.py` demonstra o defeito. **Decisão do autor:** o papel de energia nos cenários S fica com a **EnergySaver-GreenRAN**, como no G1 e no G2 (D1). O ES Orange fica documentado e fora das campanhas, sem correção, porque a regra é não alterar o original. |

Texto original das perguntas:

- **D1.** No G1 e no G2, o papel de "energy saving" fica com o ES Orange original ou com a EnergySaver-GreenRAN, que é própria e foi feita para esses cenários?
- **D2.** Para `load_balancer`, `beamformer`, `isac_radar` e `embb_throughput`, que não têm original:
  - (a) xApp própria, com lógica documentada;
  - (b) procurar um original público;
  - (c) tirar o papel dos cenários S5, S6, S8, S11 e S14.
- **D3.** No TS, como fazer o papel do AD e do QP:
  - (a) rodar os originais `ric-app-ad` e `ric-app-qp` do O-RAN SC, que são modelos treinados em dados próprios e precisam de mais downloads;
  - (b) emular no adaptador: anomalia quando a vazão do UE cai abaixo de um limiar fixado no pré-registro, e "predição" igual à vazão medida.
- **D4.** No xSlice, o PPO aprende em linha. Ele parte do zero em cada execução, ou de um modelo pré-treinado em execuções de aquecimento, que também precisam de pré-registro?
- **D5.** Os cenários que perdem o conflito com os originais, como S3 (`TX_POWER` do xSlice) e S0, S3, S4 e S10 (`TX_POWER` do ES), saem, mudam de parâmetro ou ficam como controle sem conflito?

### 7.1 xApps do FlexRIC no RIC Near-RT do O-RAN SC (decisão de 2026-11-13)

- **Pergunta:** o xSlice e o ES Orange só rodam no FlexRIC, ou podem rodar no RIC Near-RT do OSC?
- **O Traffic Steering** (`ric-app-ts`) já é xApp do OSC (RMR, xapp-frame-cpp, A1).
  - **No OSC:** depende das xApps QP (predição) e AD (anomalia) e da RC xApp (`ric-app-rc`), que recebe o handover por gRPC e envia o RIC Control pelo E2.
  - **Na simulação, nenhuma das três precisa ser instalada:** pela D3, o adaptador emula a AD e a QP e faz o papel de servidor gRPC da RC xApp. As campanhas 01 a 10 também não as usaram, porque nenhuma xApp rodava: as propostas vinham do catálogo.
  - **No testbed:** só serão necessárias se o TS original rodar no OSC de verdade.
- **O xSlice e o ES Orange** são xApps do FlexRIC (API E42, `src/xApp/e42_xapp_api.h`, e SMs do FlexRIC). Como estão, não rodam no OSC.
- **Decisão: biblioteca shim com a mesma API E42 (`libe42_shim`) e dois backends.**
  - **Backend ns-3 (simulação):** atende as chamadas da API com o KPM do orquestrador (§3) e converte o controle E2SM-RC que sai em proposta 30000.
  - **Backend OSC (testbed srsRAN do GERCOM):**
    - a subscrição passa pelo Subscription Manager do OSC;
    - as indicações chegam por RMR 12050;
    - o controle sai por RMR 12040, em E2SM-RC, interceptado pela RDL (nível 2, doc 11).
  - **O que não muda:** o código e a lógica de decisão das xApps ficam intactos. Os codificadores ASN.1 de KPM e RC do próprio FlexRIC seguem as normas O-RAN e são reaproveitados nos dois backends.
  - **Efeito colateral:** resolve a "ponte E42 ↔ RMR" que hoje obriga os derivados em Python a fazerem os papéis de xSlice e ES na bancada (Derivados (b)).
  - **Ordem:** o backend ns-3 vem primeiro (etapa E2). O backend OSC vem depois, com o testbed.
- **Alternativa registrada (não escolhida): portar o transporte.**
  - **O que é:** reescrever as partes E42 dessas xApps com xapp-frame-cpp e RMR.
  - **Por que não:** funciona, mas altera o código original, que deixa de ser "sem modificação" e perde a conferência por sha256 do `SOURCE.md`.

**O que precisa ser instalado no backend testbed (OSC com srsRAN, perfil GERCOM)**

Na simulação, nada da lista abaixo é instalado: o orquestrador e os adaptadores fazem esses papéis (§3, §4 e D3). No testbed, cada xApp original que rodar no OSC de verdade exige:

| Para rodar | O que instalar no OSC (mesma release do RIC da bancada, Release I) | Papel |
| :-- | :-- | :-- |
| Traffic Steering (`ric-app-ts`) | **xApp QP** (`ric-app-qp`) | recebe a lista de UEs do TS (`TS_UE_LIST`, 30000) e devolve a vazão prevista por célula (`TS_QOE_PREDICTION`, 30002) |
| | **xApp AD** (`ric-app-ad`) | detecta a anomalia de UE e avisa o TS (`TS_ANOMALY_UPDATE`, 30003) |
| | **xApp RC** (`ric-app-rc`) | recebe o handover do TS por gRPC (`SendRICControlReqServiceGrpc`) e envia o RIC Control pelo E2 (E2SM-RC) |
| | **coleta de KPM e base de séries temporais** (por exemplo kpimon-go e InfluxDB, que a QP e a AD leem) | sem ela, a QP e a AD não têm dados de entrada |
| | **política A1 tipo 20008** (`threshold`) pelo A1 Mediator ou pelo A1-PMS | limiar do TS |
| | **rotas RMR** separando o 30000 do TS (para a QP) do 30000 da RDL (`RDL_ACTION_PROPOSAL`) | evita a colisão descrita em §4.3 |
| xSlice e ES Orange (FlexRIC) | **backend OSC do `libe42_shim`** (§7.1) e as xApps compiladas contra ele | API E42 sobre o Subscription Manager (subscrição), RMR 12050 (indicação) e RMR 12040 (controle E2SM-RC) |
| | **agente PPO/GCN do xSlice** (`GNNRL/`, PyTorch) e o banco SQLite no esquema do FlexRIC, alimentado pelo shim | decisão do xSlice |
| | **agente E2 do srsRAN com E2SM-KPM e E2SM-RC** anunciados no E2 Setup | KPM de entrada e RC Control de saída (gates TB1–TB6) |
| Todas | **RDL e governança** (chart `ric-governance`, NetworkPolicy, interceptação do 12040, nível 2 do doc 11) | o controle das xApps passa pela RDL antes de chegar ao E2 |

Alternativa para o TS no testbed: rodar o mesmo adaptador da simulação no lugar da QP, da AD e da RC xApp, alimentado pelo KPM real. O TS continua original, mas a QP e a AD emuladas (D3) também passam a valer no testbed, e isso tem de ser dito no relato.

**Limites no testbed, para decisão posterior do autor** (valem para qualquer caminho acima):

| xApp | O que precisa | Situação no testbed (varredura, §2, §5 e §7) | Consequência |
| :-- | :-- | :-- | :-- |
| xSlice | cota de PRB por fatia do RC (Style 2, RRM Policy Ratio) | a equipe informou que **não haverá fatiamento** | sem fatias, o xSlice não tem o que controlar. Só funciona com a proposta P3 (teto da célula com uma fatia só, tratado como teto de PRB da célula) ou depois de o fatiamento existir (P4) |
| ES Orange | handover (RC, Handover Control 8.4.4.1) e desligamento de célula | o handover é RC padrão. O **desligamento de célula não tem canal** no srsRAN nem no OAI hoje: O1/NETCONF ainda está a desenvolver ou a testar, e nenhuma fonte cita E2SM-CCC | no testbed, o ES original propõe handovers que chegam à RAN. O desligamento é recusado na atuação (`UNSUPPORTED`) até haver canal |
| TS | QP, AD e RC xApp no OSC | o OSC é o RIC indicado para o srsRAN | instalar a QP, a AD e a RC xApp do OSC, ou usar o mesmo adaptador da simulação |

## 8. Etapas

**Estado em 2026-11-13:**
- **E0 concluída.** Fontes no commit fixado em `~/xapps-originais/` no WSL (fora do repositório): xslice-oran, FlexRIC no ramo da Orange, ric-app-ts, RMR, xapp-frame-cpp e ric-app-rc. Os 16 sha256 do `SOURCE.md` conferem. Os pacotes apt foram instalados.
- **E1 concluída para o S9.**
  - **O que existe:** o modo de malha fechada no `rdl-nr-common.h`, ligado por `RDL_CONTROL_SOCKET` (os cenários não mudaram), e o `scripts/closed_loop/orchestrator.py`.
  - **Resultado:** com o driver de reprodução do catálogo e o B3M, a série de KPI e o log de atuação do S9 (semente 11001) ficaram idênticos byte a byte aos da execução `nr_S9_B3_seed11001` da campanha 10.
  - **Manifesto e hashes:** o manifesto grava `control_mode: closed_loop`, e o `raw/closed_loop_log.jsonl` entra nos hashes.
- **Achado da E0:** o agente GNNRL do xSlice (`GNNRL/env.py`) lê o banco SQLite que as xApps de monitoramento do FlexRIC gravam (`xapp_db_`) e o arquivo `trandata/KPM_UE.txt`, e escreve `trandata/slice_ctrl.bin`. Por isso o backend ns-3 do shim também precisa gravar esse banco, no esquema do FlexRIC.

**Desenho detalhado da E2, a partir da leitura dos `main()` (2026-11-13):**

- **Uso da API E42 pelas duas xApps:**
  - `init_xapp_api` e em seguida `sleep(1)`;
  - `e2_nodes_xapp_api`, de que elas esperam os nós com as RAN Functions já decodificadas. A definição do KPM (`kpm_ran_function_def_t`) precisa trazer a lista de estilos de relatório e os nomes das métricas, porque a subscrição é montada a partir dela (`gen_kpm_subs`, estilo 4 com condição de casamento);
  - `report_sm_xapp_api` para o KPM (ID 2). O xSlice subscreve também MAC (142), RLC (143), PDCP (144) e GTP (148);
  - `control_sm_xapp_api` para o RC (`SM_RC_ID`);
  - `rm_report_sm_xapp_api` e `try_stop_xapp_api` no fim.
- **Nomes de métrica do ES Orange:** ele procura `L3servingSINR3gpp_cell_*` e `L3neighSINRListOf_UEID_*`, os nomes do agente E2 do ns-O-RAN. O backend ns-3 do shim gera esses nomes a partir do SINR servidor e da RSRP das vizinhas que o KPM do orquestrador já traz.
- **Relógio:** as duas xApps usam `sleep(1)` e `sleep(5)`, e o ES usa `time(NULL)` com espera de 30 s.
  - **Decisão:** em vez da `libfaketime`, usar uma biblioteca de pré-carga própria (`librdl_simclock.so`, via `LD_PRELOAD`). Ela sobrepõe `time`, `clock_gettime`, `gettimeofday`, `sleep`, `usleep` e `nanosleep` com o tempo simulado que o orquestrador publica.
  - **Efeito:** um `sleep(5)` bloqueia até o tempo simulado avançar 5 s. O código das xApps não muda.
  - **Por que não a `libfaketime`:** ela desloca ou escala o relógio, mas não sabe bloquear até o tempo simulado avançar.
- **Barreira por janela:** a janela fecha quando todas as threads da xApp estão bloqueadas num `sleep` simulado com prazo futuro e os *callbacks* de indicação terminaram. O controle emitido nesse intervalo vira proposta com o carimbo da janela.
- **Laço do xSlice:** ele faz espera ativa sobre `trandata/slice_ctrl.bin` até a marca de prontidão (quarto inteiro igual a 0), sem `sleep`, e quem escreve a marca é o agente GNNRL. A barreira do xSlice, portanto, inclui o agente:
  - a janela fecha depois que o agente grava a decisão e a xApp a envia;
  - a espera ativa é detectada pela leitura do arquivo, que a pré-carga também observa (`fopen`/`fread` de `slice_ctrl.bin`).
- **Banco do GNNRL:** o shim grava o SQLite no esquema que as xApps de monitoramento do FlexRIC usam (`xapp_db_`), com as tabelas de KPM e MAC que o `GNNRL/env.py` lê.

**Achados da leitura do código original (2026-11-13), que limitam o que cada xApp faz nos cenários:**

- **xSlice: falta um arquivo no repositório.** O `xapp_xslice.c` inclui `src/util/e.h`, que não existe no repositório no commit `87db3bd`. Do jeito que foi publicado, o código não compila.
  - **Correção de build, não de lógica:** copiamos o `src/util/e.h` do FlexRIC da Orange (commit `f56d448`, 26 linhas, só as macros `ecalloc` e `emalloc`) para a árvore do fork. Nenhum arquivo existente é alterado.
- **xSlice, o que o laço faz:**
  1. lê três PRB dedicados em `trandata/slice_ctrl.bin`, em espera ativa até a marca de prontidão;
  2. monta um RC Control (Style 2, Action 6, `RRM_Policy_Ratio` com 3 fatias) e o envia a todos os nós;
  3. espera de novo, em espera ativa, até a marca voltar a 0 e a regrava como 1.
  
  Quem escreve a decisão é o agente GNNRL. A cada passo, ele lê a tabela `MAC_UE` do SQLite do FlexRIC (`dl_curr_tbs`, `dl_sched_rb`, `pusch_snr`, `pucch_snr`, `wb_cqi`, `dl_mcs1`, `ul_mcs1`, `phr`, `dl_bler`, `ul_bler`) e o `trandata/KPM_UE.txt`. Esse arquivo é gravado pelo *callback* de KPM do xSlice com `DRB.PdcpSduVolumeDL/UL`, `DRB.RlcSduDelayDl`, `DRB.UEThpDl/Ul` e `RRU.PrbTotDl/Ul` por UE.
  
  **O KPM do ns-3 precisa ganhar estatísticas de MAC por UE** (MCS, TBS, RBs, BLER, SINR), vindas do traço `RxPacketTraceUe` do 5G-LENA. CQI, PHR e SNR de uplink não existem no cenário só de downlink: serão derivados do SINR ou declarados ausentes, com o critério documentado.
- **ES Orange, o que o laço faz:** a cada 5 s, marca para desligar toda célula com **no máximo 1 UE registrado**. Os UEs são registrados quando aparecem no KPM e nunca são removidos. Para a célula marcada, ele:
  1. faz o handover de cada UE para a vizinha de maior SINR, exigindo ao menos 5 amostras e SINR acima de −10 dB;
  2. envia `CELL_OFF` (RC, estilo `ENERGY_STATE`), quando os handovers terminaram ou depois de 30 s.
  
  **Consequência:** em células com muitos UEs (S9, S10, S13, com 20 ou mais por célula), o ES original não age. O conflito só aparece se o cenário tiver uma célula com 0 ou 1 UE. Pela regra do pré-registro (§9, item 6), isso é resultado, e o cenário não é ajustado para forçá-lo.
- **ES Orange, limites de tamanho do código:**
  - os vetores têm no máximo 20 UEs por célula (índice = ID do UE) e 10 células;
  - o ID da célula de destino vai como um caractere de '1' a '9'.
  
  O shim atribui a cada UE um ID local da célula (0 a 19) e mapeia de volta para o UE global no controle. Com mais de 20 UEs numa célula, o shim só reporta os 20 primeiros, e isso é registrado no log da execução.
- **Como os limites do ES Orange foram resolvidos sem alterar o código (2026-11-13):**
  - **20 UEs por célula:** o shim reporta cada UE com um ID local da célula (0 a 19) e corta em 20 por célula. O corte não muda nenhuma decisão. O ES só age em célula com no máximo 1 UE registrado, e uma célula com mais de 20 UEs chegaria a 20 registros de qualquer forma, então nunca seria candidata. Os UEs além do 20º só ficariam visíveis numa célula que o ES ignora.
  - **IDs locais ambíguos no controle:** o handover do ES traz só o ID local e a célula de destino. O driver resolve a origem entre as células, diferentes do destino, em que esse ID local foi reportado na última janela, e escolhe a de menos UEs. É a única que pode ser candidata, pelo critério de no máximo 1 UE. Se houver empate, o controle é registrado como ambíguo e não vira proposta.
  - **10 células e ID da célula como caractere:** os cenários têm no máximo 4 gNBs (IDs de célula de 1 a 4). O shim recusa, com erro, um cenário com mais de 9 células.
  - **Fica como característica do original, e é relatado:** o registro de UEs nunca é esvaziado. Um UE que saiu da célula continua contando para o critério de no máximo 1 UE.

**Comparação: ES Orange original × xApps próprias de energia (2026-11-13)**

O projeto tem duas xApps próprias com a função de economia de energia:
- a derivada em Python `reference-xapps/energy-saving/energy_saving_xapp.py`, inspirada no ES Orange;
- a EnergySaver-GreenRAN (`src/greenran/energysaver_greenran.py`, doc 12 §3).

| Aspecto | ES Orange (original, C) | Derivada (`reference-xapps/energy-saving`) | EnergySaver-GreenRAN (GreenRAN) |
| :-- | :-- | :-- | :-- |
| Entrada | KPM por UE: SINR servidor e das vizinhas | **desde 2026-11-13:** carga da célula no KPM (`EnergySavingDerivada`, `src/xapps/derivadas.py`). Até então, nenhuma telemetria: bateria, solar e ambiente vinham de variáveis de ambiente | KPM por célula (carga em %, UEs) e política A1 21001 |
| Decisão | célula com no máximo 1 UE registrado → handover dos UEs → `CELL_OFF` | **desde 2026-11-13:** carga abaixo de 10 % propõe `TX_POWER` 30 dBm, e acima de 40 % restaura 43 dBm, uma proposta por mudança de estado. Até então, **constante**: 18, 20 ou 21 dBm conforme o ambiente e a bateria, a cada 2,5 s, em todos os nós | carga atual **e** carga esperada na próxima hora (perfil sazonal) abaixo do limiar, dentro da janela de economia, com vizinha capaz de absorver |
| Ações | `HANDOVER` por UE e `CELL_STATE = 0` | só `TX_POWER` (os "modos" de sono são rótulos, sem ação diferente) | `HANDOVER` (evacuação), `CELL_STATE` 0 e 1, `TX_POWER` com carga moderada |
| Destino do handover | por UE, a vizinha de maior SINR (exige 5 amostras e mais de −10 dB) | não faz handover | por célula, a vizinha **menos carregada** que fica abaixo do limiar de despertar, sem olhar o sinal do UE |
| Religar célula | **não existe** | não se aplica | existe: fim da janela, vizinha sobrecarregada ou carga esperada alta (prioridade 85) |
| Confirma a evacuação antes de desligar | conta handovers *enviados* como concluídos; ou espera 30 s | não se aplica | **não**: no período seguinte ao handover, propõe o desligamento mesmo que ainda haja UEs |
| Coordenação | nenhuma (controla o E2 direto) | RMR 30000 para a RDL, sem tratar recusas | RMR 30000, `defer_ok`, `ttl_ms` e volta a `ACTIVE` se a RDL recusar |
| Limites de escala | 20 UEs por célula, 10 células, registro que nunca é limpo | nenhum | nenhum |
| Tempo | `time()` e `sleep(5)` (relógio simulado na malha fechada) | `time.sleep(2.5)` | `hour_of(t)`, por padrão o horário **local de parede** |

**Descrição:** comparação feita em 2026-11-12 e 2026-11-13, com o código de cada xApp nessas datas. A coluna da derivada foi corrigida em 2026-11-21, depois do "Comparativo xApps originais e próprias" (seção 4.8), porque descrevia a versão anterior a 13/11. As melhorias da EnergySaver-GreenRAN feitas depois (destino pela cobertura, confirmação da evacuação, permanência mínima, redução de potência a partir da potência medida; §10.16) estão no docstring de `src/greenran/energysaver_greenran.py`.

**Onde as xApps próprias são melhores que o original:**
1. **A EnergySaver-GreenRAN decide com critério de carga e previsão.** O original usa "no máximo 1 UE já visto", que nunca diminui. A EnergySaver-GreenRAN olha a carga atual, a carga esperada para a próxima hora e a capacidade da vizinha, e respeita um mínimo de células ativas.
2. **A EnergySaver-GreenRAN religa células.** O original nunca religa, e uma célula desligada fica assim até o fim.
3. **A EnergySaver-GreenRAN coordena com a RDL:** trata a recusa (30001), usa `defer_ok` e `ttl_ms`, e tem prioridades distintas para desligar (65) e religar (85).
4. **A EnergySaver-GreenRAN não tem limites de escala nem estado obsoleto.**
5. **A derivada** só é melhor em integração (RMR 30000, métricas Prometheus, charts Helm). Na lógica, não reproduz a função do original: não lê KPM, não faz handover nem desliga célula.

**Onde as xApps próprias podem melhorar** (o item 1 aproveita o ponto forte do original):
1. **EnergySaver-GreenRAN: escolher o destino da evacuação pelo sinal do UE, não só pela carga da vizinha.** O original escolhe, por UE, a vizinha de maior SINR, com amostras mínimas e piso de −10 dB. Na malha fechada o KPM já traz o SINR servidor e a RSRP das vizinhas por UE (§3.1). Com isso a EnergySaver-GreenRAN pode recusar uma vizinha sem cobertura para algum UE, ou dividir a evacuação entre vizinhas.
2. **EnergySaver-GreenRAN: confirmar a evacuação antes de propor `CELL_STATE = 0`.** Hoje ela passa de `EVACUATING` a `SLEEP` no período seguinte, sem conferir se a célula ficou vazia. Basta exigir `total_ues == 0` no KPM ou um prazo; sem isso, os UEs que restarem entram em falha de enlace.
3. **EnergySaver-GreenRAN: histerese e tempo mínimo de permanência.** Isso evita alternar sono e despertar com carga perto do limiar, e evita repetir a mesma proposta de `TX_POWER` a cada período.
4. **EnergySaver-GreenRAN: usar o tempo simulado, não o de parede.** A hora padrão vem de `time.localtime`. Na malha fechada, a hora tem de vir do `t` do KPM, como `hour_of` já permite injetar.
5. **Derivada: ler o KPM, ou deixar explícito que é só gerador de carga de conflito.** Os campos `telemetry_context` e `prohibit_urllc_degradation` não mudam a decisão da RDL. O "coverage guard" é um piso fixo de 18 dBm, não o pior SINR de borda que o README promete. Ou o README passa a dizer isso, ou a derivada passa a usar o KPM.
6. **Derivada: tratar a recusa da RDL (30001) e o `retry_after_ms`.** Hoje ela reenvia a mesma proposta a cada 2,5 s.

Nenhuma dessas melhorias muda a campanha pré-registrada sem novo registro. Elas entram, se o autor quiser, como versão nova da EnergySaver-GreenRAN, avaliada com as mesmas sementes.

**Ainda sobre o ES Orange:**

- **ES Orange, nomes e SINR:**
  - ele espera `L3servingSINR3gpp_cell_<c>_UEID_<u>` (SINR servidor, em dB) e `L3neighSINRListOf_UEID_<u>_of_Cell_<c>` (SINR por vizinha, seguido do ID da vizinha);
  - o 5G-LENA dá o SINR da célula servidora e a RSRP das vizinhas;
  - o shim estima o SINR da vizinha como SINR servidor + (RSRP da vizinha − RSRP servidora), supondo a mesma interferência mais ruído. É uma aproximação, declarada no relato.

| Etapa | Entrega | Gate |
| :-- | :-- | :-- |
| E0 | permissão para os downloads, fontes no commit exato, `SOURCE.md` atualizado | hashes conferidos |
| E1 | `RdlKpmExporter` e modo `--control-socket` no `rdl-nr-common.h`; orquestrador com xApp nula | ns-3 em passo travado reproduz o modo de cronograma com as mesmas ações (mesmo `thp_conflict`) |
| E2 | `libe42_shim`; xSlice e ES Orange compilados sem alteração | `sha256` dos `.c` igual ao do `SOURCE.md`; a indicação chega e o controle vira proposta |
| E3 | adaptador O-RAN SC (QP, AD e destino do controle REST) e rotas RMR isoladas | **concluída em 2026-11-13** (§4.3): o TS original compila e decide em `tests/integration/test_ts_original.py`; o 30000 do TS só tem rota para o adaptador |
| E4 | GreenRAN e Rogue no orquestrador; `fault_injector` como evento | todas as xApps do catálogo atendidas ou decididas (D1–D5) |
| E5 | teste de cadeia (`tests/integration/test_cadeia_malha_fechada.py`) | xApp → 30000 → RDL → ação → ns-3 → KPM → xApp em S8, S11 e G2 |
| E6 | os derivados em Python ficam (D5) e ganham leitura de KPM pelo adaptador, para o controle pareado. Atualizar `reference-xapps/README.md`, `docs/03` e o relatório de adequação: nas campanhas de cenário, as propostas vêm dos originais. Os `third_party/xapps/*` passam para `xapps-originais/` com os adaptadores. | testes verdes; nenhuma campanha usa os derivados como fonte de propostas |
| E7 | piloto e pré-registro 11 commitado antes da campanha | seção 9 |
| E8 | artigos: trocar "xApps de terceiros usadas como referência" pela execução dos originais | números só pelos scripts |

### 8.1 Piloto exploratório da E7 (semente 16901, 2026-11-13/14)

- **O que rodou:** `scripts/run_closed_loop_pilot.sh`, nove cenários (G1, G2, S9–S15) × B0/B3, todas as xApps do cenário lendo o KPM e o rApp-ResourceOptimizer com A1 no laço. O TS ainda era a derivada (o original entrou depois, na E3). Tabelas geradas por `scripts/closed_loop/analisar_piloto.py` em `reports/avaliacao/piloto_malha_fechada_seed16901/`.
- **Desvios:**
  - o commit `9f31e260` (só o script do piloto) entrou depois do início do G2/B0;
  - o WSL caiu às 19:07 de 13/11 com o piloto e o build do TS rodando juntos (falta de memória). O G1/B0 parou em t = 20 s e foi refeito do início pelo próprio script. Build e piloto passaram a rodar em sequência;
  - o G2/B3 que o script pulou era de uma execução anterior (commit `fd2cb0f`, antes das correções da EnergySaver e do refinamento) e não vale para o piloto: precisa ser refeito.
- **Achados:**
  1. **Conflito direto orgânico quase ausente; conflito indireto presente.** Nenhuma janela teve duas xApps no mesmo gNB e recurso. Em sequência (xApps diferentes no mesmo recurso até 5 s), só três casos: EnergySaver × `fault_injector` no S13 (estado da célula) e EnergySaver × Rogue no S15 (potência). Já a própria RDL, nos B3, detectou e resolveu 20 conflitos pela EEVS: 17 indiretos (parâmetros diferentes que afetam os mesmos KPIs) e 3 entre células (contagem do painel `scripts/closed_loop/resumo_campanha.py`, 14/11; a primeira versão deste relato olhava só o mesmo recurso). Em S9, S10, S11, S12 e S14, B0 e B3 tiveram exatamente as mesmas ações e KPIs. Pela regra do §9 (item 6), isso é resultado e é relatado; o cenário não é ajustado para forçar conflito.
  2. **Oscilação do RANSlicer-GreenRAN** no G1/B0 (PRB_QUOTA alternando a cada janela). No B3, a RDL não selecionou a maior parte dessas propostas. Corrigido na xApp (banda morta sempre, teto que só sobe com SLA em risco, intervalo mínimo de 2 s por célula, recusa devolve o teto de referência); `tests/unit/test_greenran_xapps.py`.
  3. **S9 e S10 sem nenhuma proposta:** carga baixa e RSRP das vizinhas abaixo do piso de cobertura da EnergySaver (−110 dBm), e nenhuma vizinha 3 dB melhor para a derivada do TS.
- **Mudanças depois do piloto:** TS original no papel `traffic_steering` (`closed_loop.json`), com a derivada em `--derivado traffic_steering` para o controle pareado; o log do processo de cada xApp original vai para `logs/xapp_<papel>.log` da execução.
- **Primeira execução com o TS original e ns-3 (S9/B3, 14/11, interrompida em t ≈ 7 s; `experiments/runs_failed/cl_e3_S9_B3_ts_seed16901__interrompida_20261114`):**
  - a cadeia fecha: AD emulado → TS original → QP emulado → `HandOff` por REST → proposta → RDL → handover aplicado no ns-3;
  - com o AD absoluto (0,2 Mbps), os 40 UEs do S9 ficam anômalos em toda janela, porque o tráfego por UE é leve. O TS pediu cerca de 14 handovers por janela, e o B3 da RDL-N1 custa cerca de 1,4 s por proposta neste ambiente: cerca de 20 s de tempo real por janela, inviável para a campanha;
  - nos KPMs do piloto, o modo absoluto marca todos os UEs em 100 % das janelas no S9 e no G2. O modo relativo (`anomaly_mode: relativo`, vazão abaixo de 50 % da média móvel do próprio UE, como a "Degradation" do AD original) zera o G2, mas no S9 ainda marca anomalia em 77 % das janelas, porque com 1 ou 2 pacotes por janela de 200 ms a vazão é ruidosa;
  - **decisão do autor (14/11): taxa oferecida** (`anomaly_mode: oferta`, 50 % em janela deslizante de 1 s; §4.3). Nos KPMs do piloto, as anomalias coincidem com eventos da rede: até 16 UEs no S13 quando o `fault_injector` desliga uma célula e até 39 no S15 quando a Rogue derruba a potência. S9, S10, S11 e G2 ficam praticamente limpos (S9: anomalia em 10 % das janelas, média de 0,1 UE). As variações 50 %/2 s e 30 %/1 s dão o mesmo quadro. Os valores entram no pré-registro 11.
- **2ª rodada do piloto (semente 16902, commit `46d89b0`, 14/11, 18 execuções com `SUCCESS`; painel em `reports/avaliacao/painel_cl_piloto_16902/`):** com o TS original, a correção do RANSlicer e o AD pela taxa oferecida.
  - RANSlicer no G1/B0: de 151 para 16 propostas e de 131 para 11 inversões. Sobra um ciclo lento (a cada 2 s, cerca de 7 pontos): reduzir o teto sem risco põe a fatia em risco, e ele sobe de novo. Corrigido depois com histerese assimétrica (`ranslicer_down_hold_s`: só reduz após 10 s sem risco);
  - TS original: 91 anomalias enviadas pelo AD emulado, 1324 predições do QP, 415 pedidos de HandOff e 909 manutenções na servidora;
  - a RDL resolveu 32 conflitos pela EEVS (29 indiretos e 3 entre células);
  - **efeito de malha fechada no S13 e no S15:** no B3, a RDL não seleciona a maior parte dos handovers do TS, os UEs seguem degradados e o TS volta a pedir (197 e 162 propostas no B3, contra 35 e 33 no B0). O TS original não trata recusa, porque no RIC ele não recebe resposta da RDL; é comportamento do original e é relatado.
- **Gate da E3 com ns-3 (`experiments/runs/cl_e3_S9_B3_ts_seed16901`, 14/11):** S9/B3 completo com o TS original e a regra da taxa oferecida, `SUCCESS` em cerca de 2 min de tempo real. O TS pediu 22 handovers (e manteve o UE em 11 consultas), a RDL selecionou 5 e o ns-3 aplicou os 5. Tabela em `reports/avaliacao/gate_e3_ts_seed16901/`.

## 9. Rascunho do pré-registro 11 (não registrado)

O pré-registro é fechado e commitado depois do piloto e antes da campanha, com o mesmo formato dos pré-registros 08–10.

1. **Objetivo:** medir B0–B3 com as xApps originais em malha fechada, ou seja, com as propostas geradas pelas xApps diante do KPM do ns-3, e não fixadas no catálogo.
2. **Estado do código:** o commit do pré-registro, o mesmo da execução. O manifesto grava também os hashes dos binários das xApps e dos adaptadores.
3. **Desenho:**
   - os cenários que ficarem depois de D1–D5;
   - os baselines B0, B1, B2 e B3;
   - as sementes 16001 a 16005, nunca rodadas, as mesmas para todos os baselines (as 12001 a 12005 já foram usadas no pré-registro 09);
   - a duração, estimada pelo piloto;
   - um comando novo, `scripts/run_closed_loop_campaign.sh`, em primeiro plano no painel Terminal.
4. **Verificação da cadeia (primária, em todas as execuções):**
   - em toda janela houve KPM entregue, resposta ou `xapp_timeout` de cada xApp e decisão registrada;
   - toda proposta aceita aparece aplicada no `rdl_actuation_log.csv`.
   
   Critério: 100 % das execuções com a cadeia completa e `xapp_timeout` < 1 % das janelas.
5. **Determinismo:** no piloto, uma execução por cenário é repetida com a mesma semente. Se as propostas ou as ações divergirem, a divergência é relatada e passa a fazer parte da variância. Nesse caso, a análise usa mais sementes, e esse número é fixado aqui antes da campanha.
6. **Hipóteses:** a direção de cada uma é fixada depois do piloto e antes da campanha, comparando B3 com B0 de forma pareada por semente, confirmada em ≥ 4 de 5 sementes. Candidatas:
   - G2: `thp_conflict` maior no B3;
   - S11: menos handovers aplicados no B3;
   - S15: `unsafe_applied = 0` no B3.
   
   Se a xApp original não gerar o conflito no cenário, isso é um resultado e é relatado. O cenário não é ajustado para forçar o conflito.
6a. **Ablação do slew-rate (decisão do autor, 18/11):** braço **B3S** = B3 com `enforce_slew_rate` ligado (no máximo 3 dB em `TX_POWER` e 30 pontos em `PRB_QUOTA` em relação ao último valor confirmado, lido da Percepção; recusa o salto maior, que volta à xApp como recusa). Mesmos cenários e sementes do B3, comparação pareada B3S × B3. Na malha fechada o estado confirmado é o último controle despachado; com a cadeia E2 o ACK dele chega na Indication seguinte. Medidas: ações recusadas pelo slew-rate, vazão e atraso na janela, oscilações e, nos cenários de energia, a demora para atingir o alvo. A variante que divide o salto em degraus de até 3 dB / 30 pontos fica fora deste pré-registro.
7. **Regras de relato:** iguais às do pré-registro 10 (`--retry-failed` uma vez; retomada depois de interrupção). Acrescenta-se uma regra: o relato separa as falhas de xApp das falhas do ns-3.
8. **Declarações (acrescentadas em 2026-11-21, depois do "Comparativo xApps originais e próprias"; §10.16):**
   - **Uma só xApp original.** Na malha fechada roda uma única xApp original de terceiros, o `ric-app-ts` (commit `beb44e0`), com a lógica de decisão sem alteração, adaptador E2 e AD e QP emulados (§4.3). As demais são próprias (`xapp_impl: propria`) ou derivadas (`derivado`). O texto usa a fórmula "lógica da xApp não modificada com adaptador E2", no singular.
   - **Prioridades fixadas pelo projeto:** TS 80 (o original não tem prioridade; quem a fixa é o adaptador); eMBB Throughput 60, abaixo da RANSlicer (90), o que torna previsível o resultado do TVS entre as duas.
   - **Hora fixa da EnergySaver:** `hour: 2` no `closed_loop.json`, sempre dentro da janela de economia (22 h a 6 h). Isso favorece a ação de energia e é declarado. Variar a hora entre execuções é uma extensão, e não está neste desenho.
   - **ISAC Radar:** gerador periódico de carga de sensoriamento (teto de 40 % a cada 5 s, prioridade 85), sem medida de demanda de radar.
   - **Load Balancer:** parâmetros fixados antes da rodada valendo: condição A3 com CIO de 3 dB, tempo de disparo de 640 ms, 30 pontos de desequilíbrio, até 4 UEs por pedido, 5 s entre pedidos, ramo de teto de PRB desligado.
   - **Contagem de conflitos:** resoluções com a Rogue (teste de segurança) ou com o `fault_injector` (evento do cenário) ficam fora das contagens de conflito entre xApps legítimas. O painel as mostra à parte.
   - **Execução:** só como projeto multinível (RDL-N1 e RDL-N2 juntas, Non-RT RIC, grafo, Safety Guard, cadeia E2), com 5 sementes e com o painel do §10.4 como saída.

## 10. Ciclo da cadeia igual ao NORI S8 (decisão do autor de 2026-11-14: híbrido A + C)

O ciclo de referência é o da bancada NORI S8 (apresentação de 10/11, fluxo 01/10–10/10): E2 Setup → subscrição KPM → KPM_t0 → proposta → decisão da RDL → RIC Control Request E2SM-RC → ACK/Failure/timeout → KPM_t1 → verificação do efeito, com hashes e contagem das mensagens no encerramento. A cadeia E2 real só existe no NORI, que tem um único gNB, dois UEs e só atua cota de PRB (docs/01, docs/03). Os cenários da malha fechada (G1, G2, S9–S15) têm de 2 a 4 gNBs e usam handover, potência e estado de célula. Por isso o ciclo é seguido de duas formas, e o pré-registro 11 declara qual cobre o quê.

### 10.1 A: mesmo ciclo no ns-3.48 multicelular (todos os cenários da malha fechada)

| Etapa NORI S8 | Na malha fechada (A) | Evidência por execução |
| :-- | :-- | :-- |
| E2 Setup | o HELLO do ns-3 vira um `E2SetupRequest`/`Response` por gNB (nó `gnb_<i>`), com as RAN Functions KPM (2) e RC (3) e os parâmetros RC atuáveis | `raw/e2_chain.jsonl` (`e2_setup`) |
| Subscrição KPM | cada xApp do cenário assina o KPM de cada nó (período = janela de decisão), com `RICrequestID` próprio | `subscription` |
| KPM_t0 (Indication) | a cada janela, uma Indication por nó, numerada, entregue às xApps assinantes | `indication` / `kpm_t0` |
| Proposta | a proposta da xApp no esquema do RMR 30000 | `proposal` |
| Decisão | `RDLDecision` com identificador de correlação gravado **antes** do despacho | `decision` |
| RIC Control Request | uma por ação, com `RICrequestID`, RAN Function 3 e cabeçalho e mensagem E2SM-RC codificados pelo codec da RDL (`src/e2/rc_encoder.py`, `src/e2/e2ap/control.py`); grava o hex e o sha256 dos bytes e decodifica de volta antes de entregar ao ns-3 | `control_request` |
| ACK / Failure | o ns-3 devolve o resultado de cada controle na Indication seguinte: `APPLIED` e `NO_EFFECT` → `RICcontrolAcknowledge`; `REJECTED_*` e `UNSUPPORTED` → `RICcontrolFailure` com a causa; sem resultado em 5 s simulados → `timeout`. `RICrequestID` duplicado com controle pendente é recusado | `control_ack` / `control_failure` / `control_timeout` |
| KPM_t1 | a primeira Indication do nó depois do ACK, com a verificação do estado aplicado: `PRB_QUOTA` → utilização de PRB e vazão da célula; `TX_POWER` → `tx_power_dbm`; `CELL_STATE` → `sleeping`; `HANDOVER` → célula servidora do UE | `kpm_t1` |
| Encerramento | contagem dos papéis `e2_setup`, `subscription`, `kpm_t0`, `control_request`, `control_ack`, `kpm_t1` (os mesmos do `scripts/certification/e2_pcap_dissect.py`), conferência de hashes e veredito da cadeia | `scripts/closed_loop/verificar_cadeia.py` |

- **Limite declarado:** sem SCTP, RIC e RMR; o transporte continua sendo o socket Unix em passo travado. Os bytes E2AP/E2SM-RC são do codec local, que, como no NORI, ainda não foi validado contra o ASN.1 oficial: provam autoconsistência, não interoperabilidade.
- **Critério da cadeia (fail-closed):** toda execução precisa de `e2_setup` para cada gNB, `subscription` para cada xApp × nó, Indication em toda janela, e todo `control_request` com `control_ack`, `control_failure` ou `control_timeout`; todo ACK de ação com efeito esperado precisa de `kpm_t1` com o estado aplicado.

### 10.2 C: malha fechada na bancada NORI com E2 real (S8)

- **xApps reais no RIC:** RANSlicer-GreenRAN, a derivada do xSlice (hoje URLLC Slice Guard, §10.16) e a `embb_throughput` como xApps do Near-RT RIC (charts Helm), assinando o KPM do gNB do NORI pelo SubMgr (`RicKpmSource`) e enviando propostas pelo RMR 30000.
- **RDL:** a `kpm-probe` ganha o modo `RC_DECISION=xapps`. Ela junta as propostas que chegam entre duas Indications (período E2 de 1 s), decide com o baseline da execução (B0–B3; B3 = RDL-N1) e envia o E2SM-RC pelo RMR 12040. O resto da cadeia é a do NORI: ACK, KPM_t1, PCAP dissecado pelo tshark e efeito por fatia.
- **Limites conhecidos antes de rodar:** o KPM do NORI traz `DRB.UEThpDl` sempre 0 (docs/01), então as xApps que leem vazão por UE veem zero; a decisão delas fica apoiada em PRB e atraso. A memória do WSL (5 GB) não comporta a bancada NORI e o ns-3.48 juntos: C e A rodam em sequência.

### 10.3 Ordem

1. A: módulo da cadeia (`scripts/closed_loop/e2_chain.py`) e verificador, em arquivos novos (feito enquanto a 2ª rodada do piloto roda);
2. A: resultado por controle no `rdl-nr-common.h` e integração no orquestrador, **depois** da 2ª rodada do piloto (que usa esses arquivos);
3. C: modo `xapps` da `kpm-probe`, charts das três xApps e uma execução S8 B0/B3;
4. pré-registro 11 com as duas coberturas declaradas.

### 10.4 Painel de fim de campanha (pedido do autor, 2026-11-14, para relato e workshop)

`scripts/closed_loop/resumo_campanha.py` roda no fim de cada campanha (e do piloto), mostra o painel no terminal e grava `painel.md` e `painel.json` em `reports/avaliacao/painel_<campanha>_<semente>/`. Ele lê só os artefatos de cada execução. Campo que a execução não registra aparece como "não registrado", nunca como zero.

| Bloco | O que mostra | Fonte |
| :-- | :-- | :-- |
| Execuções | cenário × baseline × semente, status, duração, commits | manifesto |
| Rede | gNBs, UEs registrados (conectados), handovers observados no KPM, ping-pong (volta à célula em ≤ 5 s), janelas com célula dormindo, mudanças de potência | `closed_loop_log.jsonl` (KPM) |
| Mensagens | Indications KPM, propostas das xApps (RMR 30000) por xApp e parâmetro, recusas devolvidas, políticas A1 por tipo e caminho (rApp-ResourceOptimizer → A1 → RDL, RANSlicer, EnergySaver, TS) | `closed_loop_log.jsonl` |
| Cadeia E2 | E2 Setup, subscrições, KPM_t0, decisões, RIC Control Request, ACK, Failure (por causa), timeout, KPM_t1 e veredito | `e2_chain.jsonl` + `verificar_cadeia.py` |
| Conflitos | mesma janela e em sequência, pares e recursos, resoluções da RDL por estratégia (TVS/EEVS) e por tipo (direto, indireto, entre células), oscilações (inversões em TX_POWER e PRB_QUOTA) | log de janelas e de atuação |
| Controle da RAN | ações por parâmetro e status, ajustes por gNB | `rdl_actuation_log.csv` |
| Regras e grafo | janelas decididas por regra do baseline, consultas e escritas no grafo de conhecimento | decisão por janela (o grafo passa a contar consultas depois da 2ª rodada do piloto) |
| xApps originais | TS: anomalias (30003), predições (30002), HandOff REST, mantidos na servidora, A1 20008 | `logs/xapp_traffic_steering.log` |
| KPIs | vazão e atraso médios por execução | `rdl_kpi_timeseries.csv` |

### 10.5 Estado em 2026-11-14

- **A integrado e verificado.** O orquestrador liga a cadeia com `--xapps completo` (`--cadeia-e2 auto|on|off`); o `rdl-nr-common.h` devolve o resultado de cada controle (`control_outcomes`) e a cota de PRB em vigor (`prb_quota`) na Indication seguinte, só com o socket aberto (o modo cronograma e o gate E1 não mudam). Gate `scripts/closed_loop/gate_cadeia_e2.sh` (semente 16903): G2/B3 e S15/B0 com `CADEIA_COMPLETA`, 47 Control Requests, 47 ACK e 47 KPM_t1 com o efeito confirmado no KPM; painel em `reports/avaliacao/gate_cadeia_e2_seed16903/`.
- **Mudança de comportamento:** ação que o codec E2SM-RC não codifica não é despachada e volta à xApp como recusa (`control_failure`, causa `codec`). No S15/B0, as 4 propostas da Rogue a 45 dBm (o perfil RC vai até 43 dBm) deixaram de ser aplicadas, como aconteceria numa E2 real.
- **Grafo de conhecimento:** passa a contar consultas e escritas públicas (`KnowledgeGraph.op_totals`; `kg_queries` e `kg_writes` no registro de cada decisão do B3). Achado: nas decisões por janela a RDL grava no grafo (ações, conflitos e decisões), mas só o caminho sob demanda (`_contended`) o consulta; o painel mostra o número real.
- **RANSlicer-GreenRAN:** histerese assimétrica (`ranslicer_down_hold_s` = 10 s) contra o ciclo lento da 2ª rodada.
- **C:** a `kpm-probe` ganhou o modo `RC_DECISION=xapps` (declara RX 30000 e TX 30001 no AppMgr, junta as propostas, decide a cada Indication completa com `src/closed_loop/xapps_loop.py` e devolve `RDL_ACTION_RESULT` às recusadas). Falta implantar as três xApps proponentes no RIC (release Helm com a mesma imagem e o pacote `src/` da `kpm-probe`, `SUBMGR_URL` e `KPM_NODES` apontando o gNB do NORI) e rodar o S8 B0/B3, sem o ns-3 rodando ao mesmo tempo (memória do WSL).

### 10.6 C executado: S8 na bancada NORI com xApps reais e E2 real (2026-11-18)

Execuções `nori_S8_B0_xapps_seed9205` e `nori_S8_B3_xapps_seed9206` (commit `0a0bdb2`; eventos das xApps em `experiments/xapp_logs/<execução>/`, dissecação em `experiments/e2_dissection/<execução>/`).

- **Cadeia E2 real completa nas duas**, no PCAP e confirmada pelo tshark: E2 Setup → 2 subscrições KPM (a da `kpm-probe` e a própria das proponentes) → Indications → RIC Control Request E2SM-RC → ACK → KPM_t1. Hashes conferidos.
- **xApps reais:** em cada execução, as proponentes receberam 80 Indications pela própria subscrição, tomaram 120 decisões (40 KPMs × 3 xApps) e enviaram 3 propostas pelo RMR 30000: RANSlicer-GreenRAN 35 % e depois 90 % (prioridade 90) e `embb_throughput` 80 % (prioridade 60). A derivada do xSlice não propôs: o KPM do NORI não traz atraso por UE.
- **B0:** os 3 pedidos foram à RAN, na ordem (cotas eMBB 35, 80 e 90 %); 3 Control Requests e 3 ACKs no PCAP.
- **B3:** a RDL-N1 detectou o conflito direto (RANSlicer × `embb_throughput` em PRB) e o resolveu pelo TVS, escolhendo o RANSlicer (90 %). Um Control Request, ACK correlacionado em 1,9 ms; a `embb_throughput` recebeu `NOT_SELECTED` pelo RMR 30001.
- **Efeito na RAN (B3):** com a eMBB em 90 % e a URLLC em 10 %, a vazão da URLLC caiu de 129,5 para 37,5 Mb/s (−71 %). O RANSlicer pede o máximo porque o KPM do NORI traz vazão por UE sempre 0 (ele se vê sempre em risco), e nenhuma xApp defende a URLLC, porque o xSlice depende do atraso, que o KPM do NORI não mede. A RDL arbitrou corretamente entre o que lhe foi proposto; o dano vem da entrada degenerada. É o limite já previsto no §10.2, agora medido.
- **ACKs perdidos no B0 (investigado e corrigido em 18/11, commit `6409530`):** a `kpm-probe` registrou só 1 dos 3 ACKs do PCAP. Com duas xApps registradas, o RtMgr do Release I gera uma linha `mse|12041|-1` (e `12042`) por xApp, e o E2Term entrega cada ACK a uma delas: os ACKs 2 e 3 foram às proponentes. Elas agora repassam os bytes originais à `kpm-probe` pela rota 30000 (`relay_control_outcome`), que os processa como recebidos e registra `relayed_by`; o sha256 continua casando com o PCAP, e a latência do ACK passa a incluir o salto extra (3 a 53 ms).
- **Reexecução depois da correção** (`nori_S8_B0_xapps_seed9207` e `nori_S8_B3_xapps_seed9208`): cadeia completa no PCAP com concordância do tshark; 4 de 4 ACKs recebidos e correlacionados pela `kpm-probe` (nesta rodada, todos chegaram pelo repasse). No B3, a RDL decidiu duas vezes: 35 % com as duas primeiras propostas e 90 % quando chegou o novo pedido do RANSlicer, e a URLLC caiu de novo para 37,5 Mb/s. A verificação de efeito do certificador avalia só o primeiro Control e por isso dá `INCONSISTENT` quando um segundo Control muda as cotas na janela medida; a leitura correta do efeito é pela série por fatia.
- **Operação:** a subscrição das proponentes precisa diferir da subscrição da `kpm-probe` (métricas em ordem inversa). Fundida, o RtMgr do Release I gerava duas linhas `mse|12050|<id>`, uma por endpoint, e o RMR entregava as Indications só à `kpm-probe`. Depois de reinícios do WSL, reiniciar o RtMgr e as xApps antes de rodar.

### 10.7 S0–S7 em malha fechada: o que mudou para rodar (2026-11-18)

O artigo do RDL-N1 passou a cobrir só S0–S8 (decisão do autor de 18/11). Para rodar S0–S7 com as xApps lendo o KPM:

- **Taxa oferecida no HELLO do ns-3:** S2, S4 e S5 não têm `--ueGroups`, de onde o orquestrador calculava a taxa oferecida de cada UE para o AD emulado do TS original. Agora o `RdlActuation` (`rdl-nr-common.h`) soma, no HELLO da malha fechada, `PacketSize × 8 ÷ Interval` dos `UdpClient` cujo destino é o IP de cada UE (`ue_offered_mbps`), em qualquer programa, inclusive os que instalam o tráfego sem `RdlInstallDownlinkUdp` (S1–S3). O `TsOriginalDriver` usa essa taxa; a calculada pelo catálogo fica como reserva, e o modo `oferta` só recusa a execução se não houver nenhuma das duas (`tests/integration/test_ts_original.py`).
- **Fatia de cada UE sem `--ueGroups`:** `closed_loop.json` aceita `ue_sst_cycle` e `ue_sst_counts`, tirados das classes de tráfego que o próprio programa ns-3 define:
  - S2 (`scenario_rdl_tvs_conflict.cc`): UE i com i mod 3 = 0 URLLC, 1 eMBB, 2 mMTC;
  - S3 (`scenario_rdl_energy_vs_qos.cc`): UEs 0–9 URLLC, 10–19 de fundo.

  S0, S1 e S4–S7 não têm classe URLLC no programa: todos os UEs ficam na fatia eMBB, e o xSlice, que protege a URLLC, não tem o que proteger. Isso é resultado da malha fechada e é relatado, não corrigido no cenário.
- **B3S no orquestrador:** `--baseline B3S` liga o `enforce_slew_rate` do Refinement (item 6a do pré-registro 11); `tests/unit/test_closed_loop_orchestrator.py` confere que o B3S recusa um salto de +40 pontos de PRB que o B3 aplica.
- **Rodada:** `bash scripts/run_closed_loop_pilot.sh --scenarios "S0 S1 S2 S3 S4 S5 S6 S7" --baselines "B0 B3" --seed 16905 --prefix cl_s0s7`. S0–S7 são oito programas ns-3: o script compila cada um uma vez, em sequência, antes da primeira execução, e todas as execuções usam `--no-build`.
- **Resultado (semente 16905, 18/11, commit `ce3fef8`, 58 min; painel em `reports/avaliacao/painel_cl_s0s7_16905/`):** 16 de 16 execuções com `SUCCESS` e cadeia E2 completa (65 Control Requests, 65 ACKs, 9 Failures).
  - Sem o catálogo, 86 propostas ao todo e **nenhuma em S0, S1, S4 e S5**: a EnergySaver não achou célula para desligar (S0, S1, S4), o TS original fez 1560 predições e manteve todo UE na servidora (S4, S5; 0 HandOff), e o Load Balancer não viu desequilíbrio (S5).
  - S2: um teto do xSlice, aplicado pelos dois baselines. S3: três tetos do xSlice e uma redução de potência da EnergySaver; o B3 resolveu dois conflitos indiretos pelo EEVS sem descartar ação.
  - **S6:** a tempestade das xApps tem 26 propostas (ISAC, EnergySaver, Load Balancer; Beamformer e xSlice não propuseram), contra 80 no catálogo. Com a RDL: 16 conflitos resolvidos (3 TVS, 13 EEVS), 3 recusas, 21 ações contra 26, 0 oscilações contra 3, vazão 15,3 → 17,7 Mb/s, atraso 141,6 → 138,1 ms (uma semente).
  - **S7:** a rogue fez 13 propostas; no B0 as 9 fora dos limites viraram Failure no codec E2SM-RC, no B3 o Safety Guard as recusou antes da arbitragem. A RAN recebeu as mesmas 4 ações nos dois.
  - Leitura: em malha fechada, o conflito do catálogo só aparece onde o tráfego e a topologia do programa fazem as xApps agirem. Para o pré-registro 11, os cenários S1, S2, S4 e S5 precisam de tráfego que exercite as xApps (UEs URLLC, carga desigual, vizinha melhor), ou serão relatados como sem conflito.

### 10.8 Tráfego e canal de S1, S2, S4 e S5 para a malha fechada (2026-11-18)

A rodada da §10.7 mostrou por que S1, S4 e S5 não tiveram proposta:

- **Canal:** os programas de S0–S7 usavam as fábricas de canal padrão do 5G-LENA, e todo UE media a mesma RSRP em todas as células (−34,06 dBm). Por isso o TS original nunca via vizinha melhor. O S9, que usa o canal 3GPP UMa, tem RSRP diferentes por célula.
- **Tráfego:** não havia sobrecarga nem desequilíbrio entre células (S4, S5), e S1, S4 e S5 não tinham classe URLLC.
- **Energia:** a EnergySaver precisa da topologia de vizinhas para evacuar uma célula e espera 30 s antes de pô-la para dormir. S0–S7 não têm vizinhas no catálogo, e o S4 durava 30 s.

O ajuste mantém o catálogo e a malha aberta como estavam. Cada programa ganhou opções cujo padrão é o comportamento anterior; o `closed_loop.json` passa os valores da malha fechada (`ns3_args`) e as vizinhas (`topology`), e o orquestrador repassa os dois ao ns-3 e às xApps quando `--xapps completo`:

| Cenário | Programa | Opções na malha fechada | Para quê |
|---|---|---|---|
| S1 | `scenario_rdl_direct_prb_conflict.cc` | `--channel=UMa --urllcUes=6`; `ue_sst_counts [[6,2],[14,1]]` | 6 UEs URLLC (128 B a cada 1 ms) dão à xApp do papel `xslice` (hoje a URLLC Slice Guard) uma fatia a proteger |
| S2 | `scenario_rdl_tvs_conflict.cc` | `--channel=UMa`; vizinhas gNB0↔gNB1 | RSRP diferentes por célula para o TS |
| S4 | `scenario_rdl_ts_vs_energy.cc` | `--channel=UMa --heavyIntervalMs=1 --ueRhoMax=170 --simTime=60`; vizinhas | macro sobrecarregada (30 UEs a 1024 B/1 ms), UEs ao alcance da small cell (a 200 m) e tempo para a permanência mínima da EnergySaver |
| S5 | `scenario_rdl_temporal_pingpong.cc` | `--channel=UMa --udpIntervalMs=1 --ueBoxXmin=20 --ueBoxXmax=90`; vizinhas | 24 UEs a 512 B/1 ms concentrados perto da gNB0 (gNBs em x = 0 e 150 m), para haver desequilíbrio de carga |

`--channel` aplica `ConfigureFactories (canal, "Default", "ThreeGpp")` antes de atribuir os canais às bandas; vazio, mantém as fábricas padrão.

**Validação (só B0, semente 16906, prefixo `cl_ajuste`, código ainda sem commit; execuções exploratórias):**

- S1: xSlice limitou o eMBB a 25 % (t = 1,2 s) e a EnergySaver baixou a potência da mesma célula para 30 dBm (t = 5,2 s): conflito indireto entre proteção da URLLC e economia de energia. 3 propostas, 3 ações.
- S2: xSlice (tetos de 25 % e 80 %) e três handovers do TS original na gNB1, o par TVS do cenário. 7 propostas, 7 ações.
- S4: o TS original passou a transferir UEs da macro sobrecarregada para a small cell (9 handovers; 523 anomalias e 2524 predições nos quatro cenários) e a EnergySaver baixou a potência da small cell para 30 dBm (t = 5,2 s). A vazão subiu de 171 para 194 Mb/s e o atraso caiu de 18,7 para 8,8 ms. A EnergySaver não pôs a célula para dormir: com os UEs vindos da macro, a carga da small cell nunca ficou abaixo de 15 %. 10 propostas, 10 ações, 60 s simulados em cerca de 3 h.
- S5: o TS fez 5 handovers em t = 1,8 s e depois manteve os UEs; o Load Balancer não propôs, porque as duas células ficaram saturadas (uso de PRB 100 % e 92 %, diferença de 8 pontos, abaixo dos 30 pontos da regra).
- Painel `reports/avaliacao/painel_cl_ajuste_16906/`: 4 de 4 com `SUCCESS` e cadeia E2 completa, 25 propostas e 25 ações (17 handovers, 6 cotas de PRB, 2 potências), 285 min.

**Leitura.** O canal 3GPP e o tráfego fazem as xApps agirem nos quatro cenários (antes, S1, S4 e S5 não tinham proposta), mas as ações de xApps diferentes caem em janelas diferentes ou não disparam as regras da RDL: no S1 e no S2, xSlice, EnergySaver e TS agem com segundos de distância; no S4, a redução para 30 dBm fica acima do limiar de 10 dBm da regra de handover para célula reduzida; no S5, só o TS age. Sem conflito, o B3 tende a repetir o B0. As execuções `cl_ajuste` são exploratórias (código sem commit no manifesto) e não entram em painel de resultado.

### 10.9 Alvo por UE no handover e segundo ajuste do S5 (2026-11-19)

**Alvo por UE.** A RDL arbitra por alvo (nó, parâmetro), e o `XAppAction` não tinha o UE. Na malha fechada, o TS original pede um handover por UE; na mesma célula e na mesma janela, esses pedidos viravam propostas repetidas do alvo (gNB, `HANDOVER`): só um passava, e a histerese de 1 s barrava os seguintes. O B1 e o B2 já usavam (gNB, parâmetro, UE) como alvo (`_target` em `scripts/certification/run_conflict_experiment.py`), e só o B3 diferia. Agora:

- `XAppAction.ue_id` (opcional) e `target_parameter()` em `src/conflict_types.py`: o handover de um UE identificado tem alvo próprio (`HANDOVER#ue<i>`); sem UE (`None` ou negativo), o alvo é o parâmetro, como antes.
- A chave do alvo vale na Percepção (deduplicação, conflito direto, registro das ações confirmadas), no pipeline (`target_of`, incumbente, despacho), no Reasoning (opções do EEVS, incompatibilidade física) e no Refinement (histerese e slew-rate). Os KPIs de um alvo continuam os do parâmetro (`base_parameter`), e handovers de UEs diferentes não formam conflito indireto entre si.
- As regras entre células não mudam: o ping-pong e o handover para célula reduzida olham células, não UEs.
- O `HrdlStream` passa o UE da proposta quando ele é ≥ 0. Os handovers do catálogo não têm UE, então as campanhas em malha aberta decidem como antes (os testes que comparam o cronograma do `HrdlStream` com o do executor continuam passando).
- Testes: `tests/unit/test_closed_loop_orchestrator.py` (três UEs na mesma janela passam no B3 e no B1; histerese por UE; sem UE, um só alvo; ping-pong entre UEs de duas xApps continua detectado). Suíte de unidade: 493 passaram.

**S5.** Com x de 20 a 90 m, as duas células saturaram (uso de PRB 100 % e 92 %) e o Load Balancer, que pede 30 pontos de diferença, não propôs. Os UEs passam a ficar entre x = 10 e 60 m (gNBs em 0 e 150 m): a gNB0 satura, a gNB1 fica quase vazia, o Load Balancer transfere usuários para a gNB1 e o TS pode trazê-los de volta (o ping-pong que o cenário estuda).

**Validação (S5, B0 e B3, semente 16906, prefixo `cl_ajuste2`, commit `f5983ea`, 79 min; painel `reports/avaliacao/painel_cl_ajuste2_16906/`).** As duas execuções terminaram com `SUCCESS` e cadeia E2 completa (34 controles, 34 ACKs). O Load Balancer passou a agir: transferiu usuários da gNB0 para a gNB1 em t = 1,2 s e abriu tetos de PRB depois; o TS fez 22 handovers e, em t = 1,8--2,0 s, trouxe 9 UEs de volta à gNB0. O KPM registrou 46 handovers e 18 retornos à célula de origem em até 5 s, nos dois baselines. A RDL detectou 19 conflitos (2 entre células, de ping-pong, e 17 indiretos entre os tetos do Load Balancer e os handovers já confirmados), todos resolvidos pelo EEVS sem descartar ação. O B3 aplicou as mesmas 17 ações do B0, com a mesma vazão (79,9 Mb/s) e o mesmo atraso (8,9 ms).

**Por que a RDL não evitou o ping-pong.** O handover do Load Balancer (prioridade 70) chegou sozinho e foi aplicado. Quando o TS (prioridade 80) pediu a volta, a regra de ping-pong formou o conflito entre a proposta nova e a ação já confirmada, e o EEVS, que pondera prioridade e não estabilidade, escolheu o TS. A ação confirmada não pode ser desfeita, então a volta passou e o ping-pong aconteceu. Na malha aberta, o catálogo do S5 envia os handovers do TS antes dos do Load Balancer, e a mesma regra recusava o segundo; em malha fechada, a ordem se inverteu. Os conflitos indiretos entre um teto de PRB e handovers confirmados há segundos também são espúrios: a ação confirmada já não compete. Evitar o ping-pong exige que a RDL proteja a ação recém-confirmada (por exemplo, recusar o handover inverso dentro da janela de 5 s salvo prioridade claramente maior), uma mudança de projeto do RDL-N1 que ainda não foi feita.

### 10.10 Proteção da ação recente no ping-pong (2026-11-19)

Decisão do autor depois da validação da §10.9: a RDL passa a proteger o handover recém-confirmado.

- **Ping-pong com ação confirmada.** Num conflito entre células formado pela regra de ping-pong (`ConflictEvent.rule`), se um dos lados é um handover já confirmado, a volta proposta dentro da janela de 5 s é recusada (motivo: perdeu a arbitragem, com o handover confirmado como vencedor), salvo se a prioridade dela superar a do confirmado em pelo menos `pingpong_override_margin` pontos (padrão 20, configurável nas regras entre células). O confirmado é mantido sem novo controle. Os demais membros do conflito seguem para o EEVS. Antes, o EEVS ponderava só prioridade e deixava passar a volta de uma xApp de prioridade um pouco maior (TS 80 contra Load Balancer 70), que não pode desfazer a ação já aplicada.
- **Conflito indireto com handover confirmado.** Um handover confirmado é um evento passado, não um estado do nó. Ele continua nas regras entre células (ping-pong, célula reduzida), mas não forma mais conflito indireto com propostas posteriores do mesmo nó (no S5, 17 conflitos desse tipo, todos resolvidos sem efeito).
- **Malha aberta.** Os cronogramas do B3 e do B3A nos 18 cenários do catálogo (36 cronogramas) são idênticos antes e depois da mudança: as campanhas registradas decidem como antes.
- **Testes.** `tests/unit/test_closed_loop_orchestrator.py`: volta do TS (80) recusada contra o handover do Load Balancer (70) em menos de 5 s e aceita depois de 5 s; volta com prioridade 95 aceita; teto de PRB depois de um handover confirmado sem conflito indireto. Suíte de unidade: 501 passaram.

**Validação (S5, B0 e B3, semente 16906, prefixo `cl_ajuste3`, commit `69e241b`, 72 min; painel `reports/avaliacao/painel_cl_ajuste3_16906/`).** As duas execuções terminaram com `SUCCESS` e cadeia E2 completa. O B0 repetiu a §10.9 (17 ações, 79,9 Mb/s, 8,9 ms). No B3, a proteção recusou as voltas do TS, mas o resultado piorou: 246 propostas, 9 ações aplicadas, 107 handovers no KPM, 73,1 Mb/s e 10,3 ms. A causa está no Load Balancer, não na regra:

- o pedido de handover do Load Balancer é por célula, sem UE, e o ns-3 o executa movendo **todos** os UEs da célula: 24 UEs da gNB0 para a gNB1 em t = 1,2 s e 18 de novo em t = 8,0, 15,2, 22,4 e 29,6 s (5 s de espera entre pedidos), para uma célula longe da maioria deles;
- cada novo handover do Load Balancer abre outra janela de proteção de 5 s, e o TS, que não recebe a recusa, repete os pedidos de volta a cada janela (por isso as 246 propostas); quase todos foram recusados;
- os UEs ficaram na célula de sinal fraco, e a RDL protegeu, de forma correta segundo a regra, uma ação ruim e recorrente.

Leitura: a proteção da ação recente faz o que promete (a volta dentro de 5 s é recusada), mas, em malha fechada, protege também a ação de uma xApp mal calibrada. O Load Balancer do projeto precisa transferir só parte dos UEs (os de melhor sinal na vizinha, o suficiente para reduzir a diferença de carga), com um pedido por UE, antes de qualquer rodada valendo.

### 10.11 Load Balancer transfere só parte dos UEs (2026-11-19)

Decisão do autor depois da validação da §10.10. O Load Balancer do projeto (`src/xapps/proprias.py`) pedia o handover da célula sem UE, e o ns-3 movia todos os UEs para a vizinha (24 de uma vez no S5). Agora, quando a diferença de carga passa de 30 pontos e o KPM traz RSRP por UE:

- escolhe os UEs de menor diferença de RSRP entre a servidora e a vizinha, só os que estão a até `lb_max_rsrp_gap_db` = 10 dB;
- transfere a fração `diferença / (2 × carga)` dos UEs da célula (metade da diferença de carga), ao menos um e no máximo `lb_max_ues` = 4;
- faz um pedido de handover por UE (campo `ue`), que a RDL arbitra com o alvo por UE da §10.9 e a proteção da §10.10;
- sem nenhum UE que ouça a vizinha o bastante, não propõe; sem RSRP por UE no KPM (perfis sem essa medida), mantém o handover da célula.

Isso muda também o S6 em malha fechada, onde o Load Balancer participa da tempestade. Testes: `tests/unit/test_xapps_kpm.py` (quatro UEs de menor diferença de RSRP, um pedido por UE e espera de 5 s; nenhum pedido quando nenhum UE ouve a vizinha).

**Validação (S5, B0 e B3, semente 16906, prefixo `cl_ajuste4`, commit `93e4c31`, 77 min; painel `reports/avaliacao/painel_cl_ajuste4_16906/`).** As duas execuções terminaram com `SUCCESS` e cadeia E2 completa. O Load Balancer transferiu 4 UEs em t = 1,2 s e mais 4 em t = 8,2 s; o KPM não registrou nenhum retorno à célula de origem em até 5 s, nos dois baselines (antes, 18). No B0, o TS devolveu 3 UEs em t = 8,4 s; no B3, a proteção da §10.10 recusou essas voltas, e o TS, que não recebe a recusa, as repetiu (33 propostas, 9 ações). Vazão de 84,0 Mb/s (B0) e 84,3 Mb/s (B3), atraso de 10,9 e 11,1 ms: com o Load Balancer movendo poucos UEs de bom sinal, a rede ficou melhor que na §10.9 (79,9 Mb/s) nos dois baselines, e a diferença entre eles é desprezível nesta semente.

**Registro da proteção.** As recusas da proteção não passavam pelo Reasoning, e o painel do B3 mostrava "nenhum conflito". Agora cada uma entra no log de decisão como uma resolução de estratégia `PINGPONG_GUARD` (regra, envolvidas e vencedora), contada no painel junto com TVS e EEVS (`RDLxApp.guard_events`, lido pelo `HrdlStream`).

### 10.12 Rodada S1, S2, S4 e S5 com B0 e B3 (semente 16907, 2026-11-20)

**Execução.** Prefixo `cl_s1245`, commit `725889f`, 8 execuções, 1703 min; painel `reports/avaliacao/painel_cl_s1245_16907/`. Todas terminaram com `SUCCESS` e cadeia E2 completa (71 controles, 71 ACKs, nenhuma falha). Nenhuma janela teve conflito direto (mesmo gNB e recurso) e não houve oscilação de potência ou de teto de PRB.

| cenário | propostas B0/B3 | ações B0/B3 | vazão B0/B3 (Mb/s) | atraso B0/B3 (ms) | resoluções da RDL no B3 |
|---|---|---|---|---|---|
| S1 | 3/3 | 3/3 | 140,703/140,703 | 10,982/10,982 | 2 EEVS (indiretos, as duas ações mantidas) |
| S2 | 8/8 | 8/8 | 131,024/131,024 | 12,508/12,508 | 2 EEVS (indiretos, as duas ações mantidas) |
| S4 | 7/7 | 7/7 | 167,411/167,411 | 8,110/8,110 | nenhuma |
| S5 | 21/129 | 21/14 | 93,385/93,173 | 7,569/9,092 | 64 `PINGPONG_GUARD` |

**S1, S2 e S4.** Os conflitos que apareceram foram indiretos (teto de PRB do xSlice contra potência do Energy Saver no S1; handovers do TS contra o teto do xSlice no S2), e o EEVS manteve as duas ações. A RDL aplicou exatamente o que o B0 aplicou, e o ns-3, com a mesma semente e as mesmas ações, produziu as mesmas medidas. Nesses três cenários, em malha fechada, as xApps não chegaram a disputar o mesmo recurso; a RDL não mudou nem atrapalhou nada.

**S5: a proteção do ping-pong segurou UEs numa célula ruim.** Os registros (`raw/rdl_actuation_log.csv` e `raw/closed_loop_log.jsonl` das duas execuções) mostram o ciclo:

- a cada ~5 s (t = 1,2; 6,2; 11,4; 16,6; 21,6; 26,6 s), o Load Balancer transfere os UEs 2 e 14 da célula 1 para a 2 (em t = 1,2 s também os UEs 7 e 23, que ficam bem na célula 2);
- os UEs 2 e 14 ouvem a célula 2 **pior** que a célula 1 (em t = 3,4 s: RSRP de −129,1 contra −122,6 dBm no UE 2 e −133,3 contra −130,0 dBm no UE 14; SINR de −7,7 e −8,0 dB). Eles passam no filtro do Load Balancer porque a diferença de RSRP está dentro de `lb_max_rsrp_gap_db` = 10 dB, mas o filtro não exige que a vizinha seja melhor;
- **no B0**, o TS devolve o UE 14 à célula 1 de 0,2 a 0,6 s depois (o UE 2 só no primeiro ciclo); nos ciclos seguintes, o UE 2 perde a conexão cerca de 2,2 s depois do handover (`connected: false`, célula 0 no KPM) e se restabelece na célula 1;
- **no B3**, a proteção da §10.10 recusa todas as voltas do TS (64 janelas com `PINGPONG_GUARD`; das 129 propostas, 115 foram recusadas, e o TS as repetiu a cada janela). Os dois UEs ficam na célula 2 até perderem a conexão (t = 3,6; 8,6; 13,8; 19,0; 24,0; 29,0 s) e voltam à célula 1 pelo restabelecimento, não pelo handover.

Efeito: vazão igual (−0,2 %), atraso médio 20 % maior no B3 (9,09 contra 7,57 ms). O atraso médio da célula 2 subiu de 8,2 para 11,7 ms; o do UE 2 subiu de 32,9 para 44,0 ms, e o do UE 14 caiu de 119,9 para 90,0 ms. O KPM contou 26 handovers nos dois baselines, porque no B3 as voltas pelo restabelecimento substituem as voltas pelo TS.

**Leitura.** A proteção faz o que a regra diz: a volta dentro de 5 s é recusada. Mas a ação protegida era ruim para dois dos quatro UEs, e só a xApp que corrige (o TS) via isso no KPM. Com uma semente, o resultado é um caso, não uma estimativa. Duas correções possíveis, ainda não decididas:

1. **Load Balancer:** só transferir UEs cuja vizinha não seja pior que a servidora por mais que uma margem pequena (por exemplo, RSRP da vizinha ≥ RSRP da servidora − 3 dB), em vez de aceitar 10 dB de diferença em qualquer sentido.
2. **RDL:** deixar a volta passar quando o KPM mostra que o UE protegido está em condição ruim na célula de destino (SINR abaixo de um limiar), mesmo dentro dos 5 s.

A primeira corrige a origem e não muda a RDL; a segunda torna a proteção sensível ao estado do UE e vale para qualquer xApp mal calibrada.

### 10.13 Load Balancer não transfere UE para vizinha muito mais fraca (2026-11-20)

Decisão do autor depois da §10.12: a correção 1. Em `src/xapps/proprias.py`, `lb_max_rsrp_gap_db` passa de 10 para 3 dB: o Load Balancer só escolhe UEs cuja vizinha seja no máximo 3 dB mais fraca que a servidora (RSRP da servidora − RSRP da vizinha ≤ 3 dB). O resto da §10.11 não muda (menor diferença primeiro, metade da diferença de carga, no máximo 4 UEs, um pedido por UE, espera de 5 s). A RDL não muda.

O valor de 3 dB é uma escolha do projeto, na ordem do offset usual do evento A3 de handover; não vem de uma norma. Com 10 dB, o filtro aceitava UEs que ouvem a vizinha bem pior e perdiam a conexão lá; com 0 dB (só vizinha melhor), quase nenhum UE de borda seria transferido.

**O que se espera no S5 (semente 16907), lido do KPM registrado, não simulado.** Em t = 1,2 s, as diferenças dos UEs da célula 1 eram −0,1 dB (UE 23), 2,7 (UE 7), 3,3 (UE 14) e 6,5 (UE 2); com o novo limite, só os UEs 23 e 7 seriam transferidos, e os dois ficaram bem na célula 2 nas execuções da §10.12. Nos ciclos seguintes (t = 6,2 s em diante) nenhum UE da célula 1 ficava dentro de 3 dB, então o ciclo de transferência, recusa da volta e perda de conexão não deveria se repetir. A confirmação exige uma nova execução do S5 com B0 e B3.

**Validação (S5, B0 e B3, semente 16907, prefixo `cl_lb3`, sobre o commit `725889f` com a mudança ainda não commitada (`repo_dirty`; o código executado é o do commit `b5e34b9`, feito depois da rodada), 56 min; painel `reports/avaliacao/painel_cl_lb3_16907/`).** As duas execuções terminaram com `SUCCESS` e cadeia E2 completa. O Load Balancer transferiu só os UEs 23 e 7 em t = 1,2 s e não propôs mais nada; o TS não pediu nenhuma volta. O KPM registrou 4 handovers (2 por execução) e nenhum retorno à célula de origem em até 5 s (antes, 25 na rodada da §10.12). A RDL não teve conflito a resolver, e o B3 aplicou as mesmas 2 ações do B0.

| S5, semente 16907 | vazão B0 / B3 (Mb/s) | atraso B0 / B3 (ms) | ações B0 / B3 | propostas B0 / B3 |
|---|---|---|---|---|
| antes (§10.12, limite de 10 dB) | 93,385 / 93,173 | 7,569 / 9,092 | 21 / 14 | 21 / 129 |
| depois (limite de 3 dB) | 94,771 / 94,771 | 5,429 / 5,429 | 2 / 2 | 2 / 2 |

Leitura: o ciclo de transferência ruim, recusa da volta e perda de conexão desapareceu, e a rede ficou melhor nos dois baselines (atraso 28 % menor que o B0 anterior). Mas, com o Load Balancer bem calibrado, o S5 em malha fechada deixou de produzir o conflito de ping-pong que o cenário estuda: não sobra nada para a RDL arbitrar, e B0 e B3 são idênticos. Para que o S5 volte a exercitar a RDL, o conflito precisa vir das xApps lendo uma rede em que transferir e devolver sejam ambos razoáveis (por exemplo, UEs de borda com RSRP próximo nas duas células e carga que oscile), e não de uma xApp mal calibrada. Isso é uma decisão de cenário, ainda não tomada.

**Testes.** `tests/unit/test_xapps_kpm.py`: o teste da §10.11 passa a usar diferenças de −2 a 7 dB; um teste novo reproduz os UEs 2, 14 e 7 do S5 (só o 7 é transferido). Em `tests/unit/test_closed_loop_completo.py`, o KPM sintético passa a ter vizinhas 1 a 3 dB mais fracas (antes, 6 dB ou mais), para que o Load Balancer ainda proponha no S5 e no S11. Suíte de unidade: 499 passaram, 1 ignorado.

### 10.14 S5 com as duas células carregadas: varredura da faixa dos UEs (proposta P1, 2026-11-20)

Decisão do autor depois da §10.13: buscar um S5 em que transferir e devolver sejam ambos justificados pelas regras das próprias xApps, sem mudar código, alargando a faixa em x dos UEs (closed_loop.json usa `--ueBoxXmax=60`) para que a célula 2 receba carga. A faixa é sobreposta pelo `--sim-arg` do orquestrador. Scripts novos: `scripts/closed_loop/varrer_s5_faixa.sh` (uma execução e um painel por limite, prefixo `cl_p1x<limite>`) e `scripts/closed_loop/avaliar_pingpong.py` (critério abaixo).

**Critério de conflito legítimo** (`avaliar_pingpong.py`, sobre `raw/rdl_actuation_log.csv` e o KPM da janela da decisão): handover do Load Balancer justificado se a carga da origem menos a do destino for ≥ 30 pontos; do TS, se o UE estiver mal atendido (vazão média em 1 s abaixo de 50 % da taxa oferecida) e ouvir o destino mais forte. Uma volta é o mesmo UE voltando à célula de origem por handover pedido em até 5 s. A execução cumpre o critério com ao menos uma volta em que as duas ações eram justificadas e nenhuma perda de conexão (`connected: false`) em até 3 s depois de um handover pedido.

**Varredura com B0** (semente 16907, commit `fdfc9e9`, sem mudança de código; cerca de 30 min por execução; painéis `reports/avaliacao/painel_cl_p1x<limite>_16907/`). Todas terminaram com `SUCCESS` e cadeia E2 completa.

| faixa x (m) | handovers aplicados | voltas justificadas | perdas de conexão após handover | uso de PRB célula 1 / 2 (%) | vazão (Mb/s) | atraso (ms) | critério |
|---|---|---|---|---|---|---|---|
| 10–70 | 3 | 0 | 1 | 96,6 / 49,5 | 95,472 | 5,741 | não |
| 10–75 | 13 | 0 | 11 | 96,6 / 45,3 | 94,425 | 5,775 | não |
| 10–80 | 5 | 0 | 0 | 89,5 / 73,4 | 93,552 | 5,756 | não |
| 10–85 | 14 | 8 | 0 | 87,1 / 53,3 | 92,057 | 6,643 | sim |

Descrição: cada linha é uma execução do S5 com B0; as colunas de handover e conexão vêm do critério acima, e as de vazão e atraso, do painel. A posição de cada UE é sorteada dentro da faixa, então mudar o limite muda a posição de todos os UEs: as linhas são distribuições diferentes, não uma escala de carga.

- **10–70 e 10–75 m:** o UE 14, transferido pelo Load Balancer, perde a conexão na célula 2 de forma intermitente (12 e 11 janelas) e volta à célula 1 pelo restabelecimento; em 10–75 m o TS e o Load Balancer o reenviam à célula 2 a cada ~2,5 s. É um ciclo por perda de conexão, não um conflito legítimo.
- **10–80 m:** nenhuma volta; o UE 10 fica sem conexão a execução inteira, sem handover envolvido.
- **10–85 m:** a cada ~5 s (t = 6,2; 11,4; 16,6; 21,6; 26,6 s) o Load Balancer transfere o UE 14 da célula 1 para a 2, e o TS o devolve 0,2 s depois. O UE ouve a célula 2 2,5 dB mais fraca (−130,3 contra −127,8 dBm), dentro do limite da §10.13; as cargas eram 90 % e 25 %. As duas ações cumprem a regra de quem as pediu.

**O TS devolve um UE que estava melhor.** Em 10–85 m, na célula 1 o UE 14 recebia 1,35 Mb/s dos 4,1 oferecidos, com atraso de ~60 ms; nos 0,2 s na célula 2, 3,93 Mb/s e 4,6 ms (SINR de −5,7 dB). O TS decide pela vazão média do último 1 s, que ainda é quase toda da célula 1, e vê o UE mal atendido e a célula 1 mais forte. O critério usa a mesma média, então conta como justificadas voltas que, medidas depois, pioraram o UE.

**B3 em 10–85 m** (mesma semente e commit, cerca de 30 min). `SUCCESS`, cadeia E2 completa.

| S5, faixa 10–85 m | propostas | ações | vazão (Mb/s) | atraso (ms) | resoluções da RDL | UE 14: vazão (Mb/s) / atraso (ms) | UE 14: janelas sem conexão |
|---|---|---|---|---|---|---|---|
| B0 | 15 | 15 | 92,057 | 6,643 | nenhuma | 1,331 / 64,1 | 0 |
| B3 | 12 | 9 | 93,049 | 6,441 | 1 EEVS, 2 `PINGPONG_GUARD` | 2,758 / 27,7 | 7 |

Descrição: vazão e atraso da rede vêm do painel; as colunas do UE 14 são médias das janelas a partir de t = 1 s em `raw/closed_loop_log.jsonl`.

- **t = 11,6 s, proteção correta:** a RDL recusa a volta do UE 14 pedida pelo TS (handover do Load Balancer confirmado em t = 11,4 s). O UE fica na célula 2 recebendo toda a taxa oferecida (4,1 Mb/s, 4,5 ms), perde a conexão por uma janela em t = 13,8 s (SINR de −5,7 dB, abaixo do limiar de −5 dB do 5G-LENA) e se restabelece na própria célula 2. Nos ciclos seguintes o TS não pede mais a volta. Os outros UEs da célula 2 quase não mudam (vazão média de 4,017 para 4,013 Mb/s, atraso de 6,0 para 6,3 ms).
- **t = 6,2 s, falso positivo:** a RDL recusa as transferências dos UEs 2 e 14 pelo Load Balancer porque em t = 1,8 s o TS tinha movido os UEs 4 e 18 no sentido oposto. A regra `HANDOVER_PING_PONG` (`src/core/inter_cell.py`, `pair_conflict`) compara só o par de células e o sentido, não o UE, embora as ações tragam o UE desde a §10.9 (`XAppAction.ue_id`). Por isso o B3 começa o ciclo em t = 11,4 s, e não em 6,2 s.

**Leitura.** A faixa 10–85 m dá ao S5 o conflito que ele estuda: duas xApps, cada uma pela sua regra, empurrando o mesmo UE de borda em sentidos opostos. Nesse caso a proteção da RDL favoreceu a ação certa (a vazão do UE 14 dobrou e o atraso caiu 57 %, com a rede igual ou melhor), ao custo de perdas de conexão curtas que o UE recupera na mesma célula. Pelo critério, o B3 não cumpre (4 perdas de conexão após handover), mas o critério foi feito para escolher a faixa, não para julgar o baseline. A volta do TS era errada porque ele mede pelo passado, e não porque a RDL errou. Com uma semente, é um caso. O falso positivo de t = 6,2 s é um defeito da regra entre células, corrigido logo abaixo.

**Correção: o ping-pong exige o mesmo UE quando os dois handovers trazem o UE** (decisão do autor depois da rodada acima). A §10.9 manteve as regras entre células olhando só células, porque o Load Balancer pedia o handover da célula inteira, sem UE; desde a §10.11 o Load Balancer e o TS pedem um handover por UE. Em `src/core/inter_cell.py` (`pair_conflict`), dois handovers em sentidos opostos entre o mesmo par de células só formam `HANDOVER_PING_PONG` se o UE for o mesmo; se algum dos dois não tiver UE (`ue_id` ausente ou negativo, como os handovers do catálogo), vale o par de células, como antes. A proteção da §10.10 não muda: a volta do mesmo UE dentro de 5 s continua recusada. As campanhas em malha aberta não mudam, porque os handovers do catálogo não têm UE.

Testes em `tests/unit/test_closed_loop_orchestrator.py`: o teste da §10.9 que esperava ping-pong entre UEs diferentes passa a esperar o contrário, e mantém a detecção para o mesmo UE e para um lado sem UE. Um teste novo reproduz t = 1,8 e 6,2 s do B3 em 10–85 m: as transferências dos UEs 2 e 14 passam, e a volta do UE 14 pelo TS em t = 6,4 s é recusada. Os dois testes falham com a regra antiga. Suíte de unidade: 500 passaram, 1 ignorado.

**Validação da correção (S5, B3, faixa 10–85 m, semente 16907, prefixo `cl_p1uex85`, sobre o commit `fdfc9e9` com a correção ainda não commitada, 33 min; painel `reports/avaliacao/painel_cl_p1uex85_16907/`).** `SUCCESS`, cadeia E2 completa. O binário do S5 já trazia a opção de UEs em movimento da §10.15 com velocidade 0, que não muda a saída. O rApp de governança estava ligado (padrão do B3 desde a §10.15), mas não publicou nenhuma A1 20000; só a 20001, como antes. Em t = 6,2 s, as transferências dos UEs 2 e 14 pelo Load Balancer passaram; em t = 6,4 s, a volta do UE 14 pelo TS foi recusada (`PINGPONG_GUARD`, o único da execução). Nos ciclos seguintes (t = 11,4 a 26,6 s), o Load Balancer volta a transferir o UE 14 e o TS não pede mais a volta.

| S5, faixa 10–85 m | propostas | ações | vazão (Mb/s) | atraso (ms) | `PINGPONG_GUARD` | UE 14: vazão (Mb/s) / atraso (ms) | UE 14: janelas sem conexão | UE 2 a partir de 6,4 s: vazão (Mb/s) / atraso (ms) |
|---|---|---|---|---|---|---|---|---|
| B0 | 15 | 15 | 92,057 | 6,643 | 0 | 1,331 / 64,1 | 0 | 4,095 / 4,5 |
| B3, regra por célula | 12 | 9 | 93,049 | 6,441 | 2 | 2,758 / 27,7 | 7 | 3,723 / 11,6 |
| B3, regra por UE | 11 | 10 | 93,517 | 6,318 | 1 | 3,159 / 17,7 | 9 | 4,095 / 4,7 |

Descrição: vazão e atraso da rede vêm dos painéis; as colunas dos UEs são médias das janelas em `raw/closed_loop_log.jsonl` (UE 14 a partir de t = 1 s, UE 2 a partir de t = 6,4 s, depois da primeira transferência). Uma execução por linha, mesma semente.

Leitura: sem o falso positivo, o UE 2 vai para a célula 2 em t = 6,2 s, como no B0, e fica lá bem atendido (antes, só em 11,4 s, e o atraso médio dele triplicava). O UE 14 passa mais tempo na célula 2: vazão maior e atraso menor que nos outros dois, ao custo de mais janelas sem conexão (9 contra 7; o SINR dele na célula 2 continua −5,7 dB). A rede teve a maior vazão e o menor atraso dos três. Pelo critério de `avaliar_pingpong.py`, o B3 não cumpre (5 perdas de conexão após handover), pelo mesmo motivo do B3 anterior. Com uma semente, é um caso.

### 10.15 S5 com UEs em movimento (proposta P3) e primeira rodada com RDL-N1 e RDL-N2 juntas (2026-11-21)

Proposta P3: em vez de alargar a faixa (§10.14), fazer parte dos UEs andar entre as duas células, para que a borda mude com o tempo e transferir e devolver sejam ambos justificados em momentos diferentes. A mesma rodada estreia o baseline `N12` (RDL-N1 e RDL-N2 juntas, decisão do autor de 2026-11-20; docs/16 da Fase 2).

**Mobilidade no cenário** (`simulations/ns3/scenario_rdl_temporal_pingpong.cc`). Opções novas: `--ueSpeed` (m/s; padrão 0), `--ueMovingFraction` (0,5), `--ueMoveXmin` (10) e `--ueMoveXmax` (140). Com `ueSpeed` ≤ 0 o cenário é o de antes (posição fixa). Com `ueSpeed` > 0, os primeiros `round(fração × N)` UEs recebem um `WaypointMobilityModel` e vão e voltam em x entre os dois limites até o fim da simulação, com y fixo; os de índice par começam indo para o gNB 2, os de índice ímpar para o gNB 1. O cenário imprime a trajetória de cada UE e a posição final (`[RDL-MOB]`).

- **Defeito contornado no ns-3.48.** Chamar `GetPosition` antes de inserir os pontos faz `WaypointMobilityModel::Update` marcar o ponto inicial com t = −1 s. O primeiro trecho então começa em −1 s: o UE salta para a frente no início e anda mais devagar que o pedido até o primeiro ponto. O cenário insere o ponto inicial em t = 0 antes dos demais.
- **Regressão.** Com `ueSpeed` = 0, o `flowmonitor` e o `rdl_kpi_timeseries.csv` saíram idênticos byte a byte aos do binário anterior. Com `ueSpeed` = 5, as posições finais impressas coincidiram com a trajetória declarada, com diferença de até 0,009 m (12 de 24 UEs em movimento).

**Rodada** (S5, faixa 10–60 m do `closed_loop.json`, 5 m/s, metade dos UEs andando, semente 16907, prefixo `cl_p3v5`; commit `fdfc9e9` com árvore suja, incluindo a mobilidade, a correção do ping-pong por UE da §10.14 e o N12; cerca de 31 min por execução; script `scripts/closed_loop/rodar_s5_p3.sh`; painel `reports/avaliacao/painel_cl_p3v5_16907/`). As três terminaram com `SUCCESS` e cadeia E2 completa. Governança do Non-RT RIC ligada no B3 e no N12.

| S5, P3 | propostas | ações | handovers pedidos | voltas em 5 s (justificadas) | perdas de conexão após handover | vazão (Mb/s) | atraso (ms) | resoluções da RDL |
|---|---|---|---|---|---|---|---|---|
| B0 | 32 | 32 | 28 | 12 (12) | 0 | 90,039 | 10,317 | nenhuma |
| B3 | 26 | 25 | 22 | 8 (8) | 0 | 90,320 | 9,227 | 13 EEVS (indiretos) |
| N12 | 26 | 25 | 22 | 8 (8) | 0 | 90,320 | 9,227 | 13 EEVS (indiretos), todos pela RDL-N2 |

Descrição: handovers, voltas e perdas vêm de `avaliar_pingpong.py` (critério da §10.14); vazão e atraso, do painel. Nos três, o critério da §10.14 é cumprido. Por grupo (`avaliar_mobilidade.py`), os UEs que andam tiveram 1 perda de conexão com reconexão na outra célula nos três baselines; a parcela de janelas (UE × janela) mal atendidas desses UEs foi 12,4 % no B0 e 11,6 % no B3 e no N12, e a dos UEs fixos, 11,4 % nos três.

**De onde vem a diferença.** Até t = 26,4 s, os três baselines receberam as mesmas propostas e aplicaram as mesmas ações, inclusive um vaivém do UE 6 pelo próprio TS (célula 2 para 1 em t = 26,0 s, 1 para 2 em t = 26,4 s). Em t = 26,6 s o TS pede de novo a volta do UE 6 à célula 1. No B0 ela é aplicada, e o TS segue alternando o UE até o fim: 5 handovers do UE 6 de t = 26,6 a 29,6 s. No B3 e no N12, a volta é recusada pelo limite de frequência do Safety Guard (1 s entre controles no mesmo alvo; o mesmo controle, handover do UE 6 a partir do gNB 2, tinha sido aplicado em t = 26,0 s). Não foi a proteção do ping-pong, que só vale entre xApps diferentes. O TS repete o pedido em t = 27,0 s, exatamente 1 s depois, ele passa, e o UE fica na célula 1 até o fim. O motivo foi obtido reproduzindo as decisões do B3 fora do ns-3 com as propostas registradas: as decisões coincidiram em todas as janelas, e a única recusa foi `Control frequency exceeded` para esse alvo. O registro da execução não guarda o motivo de uma recusa sem conflito; isso fica como melhoria do log.

| S5, P3, a partir de t = 26,6 s | UE 6: vazão (Mb/s) | UE 6: atraso (ms) | vazão da rede (Mb/s) |
|---|---|---|---|
| B0 | 0,434 | 221,5 | 88,06 |
| B3 e N12 | 1,216 | 86,9 | 90,29 |

Descrição: médias das 17 janelas de 0,2 s a partir de t = 26,6 s em `raw/closed_loop_log.jsonl`; nenhum dos dois ficou sem conexão nesse trecho.

**RDL-N1 e RDL-N2 juntas.** Os 13 conflitos da execução N12 foram indiretos (handover do TS contra o teto de PRB do Load Balancer na mesma célula), com C(c, s) = 2,2, e todos subiram à RDL-N2 (1 pela complexidade, 12 pela complexidade e pela recorrência no grafo, com 1 a 5 conflitos no mesmo alvo em 5 s). A RDL-N2 devolveu os 13 à RDL-N1 com o motivo `conflito INDIRECT fora do escopo do MAPPO`, e a decisão final foi a do B3. O Non-RT RIC entregou a A1 20002 uma vez e a 20001 três vezes; a governança não publicou A1 20000, porque não houve rejeição que mudasse o relatório.

**Leitura.** Com UEs em movimento, o S5 volta a ter decisões de handover em sequência, todas justificadas pelas regras das xApps, mas o conflito entre xApps diferentes no mesmo UE (o da §10.14) não apareceu: as voltas foram do próprio TS, e o que as separou foi o limite de frequência do Safety Guard, que vale igual no B3 e no N12. Nesse único episódio, segurar a volta por 0,4 s e encerrar o vaivém deixou o UE 6 melhor e a rede igual ou melhor. Com uma semente e um episódio, é um caso. O N12 ficou idêntico ao B3, como esperado: o MAPPO só conhece disputas diretas de teto de PRB, e no S5 não houve nenhuma (docs/16 da Fase 2, §3). As rodadas não são evidência de publicação.

### 10.16 Campanha `cl_n12` abortada e correções das xApps pelo comparativo (2026-11-21)

**Campanha abortada.** A `cl_n12` (S0–S7 × B0, B3, N12, semente 16908) foi interrompida a pedido do autor depois de 12 execuções concluídas (S0 a S3). A execução `cl_n12_S4_B0_completo_seed16908` foi interrompida no meio, depois de cerca de 3 h 16 min, e ficou sem manifesto. As 13 pastas continuam em `experiments/runs`, mas usam as xApps de antes desta seção. Pela regra nova do autor, elas saem aos poucos, à medida que as campanhas novas as substituírem.

**Correções, na ordem do "Comparativo xApps originais e próprias"** (relatório na pasta `reports` do workspace, fora do repositório):

| xApp ou componente | Problema | Correção |
| :-- | :-- | :-- |
| xSlice derivado → **URLLC Slice Guard** | Sem histerese, o teto oscilava 25 → 80 → 25 % a cada ~1,4 s no S2 (atraso protegido de ~9 ms, limite de 10 ms). Sem tratar recusa, parava de propor depois da primeira recusa (S2/B3: 5 propostas, contra 25 no B0). O nome sugeria uma reimplementação do xSlice, cuja decisão é de um PPO com GCN | xApp própria `UrllcSliceGuard` (`src/xapps/proprias.py`, `xapp_id` `urllc_slice_guard`, `xapp_impl: propria`), no papel `xslice` do catálogo. Relaxa só com o atraso abaixo de 0,7 × limite por 5 janelas, e esse número dobra se relaxar recriar o risco (até 40). A recusa devolve a célula ao estado anterior. A xApp de implantação (`reference-xapps/urllc-slice-guard`, chart `xapp-urllc-slice-guard`) perdeu a carga simulada, os perfis fixos e as métricas de valor constante, e o chart passou a configurar o KPM (`SUBMGR_URL`, `KPM_NODES`) |
| Fatia de cada UE | O orquestrador injetava a fatia a partir do `closed_loop.json` (`ue_sst_*`) | O ns-3 reporta a fatia no KPM por UE (`sst`) e no hello (`ue_sst`), como o `DRB.NetworkSlicing.SST` (`RdlActuation::SetUeSst`). S1, S2 e S3 a declaram no próprio programa, e o `scenario_rdl_multicell` ganhou `--ueGroupSst`, que o orquestrador passa a partir de `ue_sst_groups`. `ue_slice` prefere o valor do KPM, e o mapa do `closed_loop.json` só vale para registros antigos |
| EnergySaver-GreenRAN | Nos cenários do ns-3 a gNB transmite com o padrão do 5G-LENA (`NrGnbPhy::TxPower` = 4 dBm). A "redução" fixa para 30 dBm era um aumento de 26 dB, e foi isso o que as 25 propostas de `TX_POWER` das rodadas S0–S7 fizeram. Uma recusa de `TX_POWER` deixava a célula marcada como reduzida | Com a potência em vigor no KPM (`tx_power_dbm`), o alvo fica ao menos 3 dB abaixo dela (`es_tx_power_min_step_db`), e não há proposta se isso não for uma redução. A restauração volta à potência medida antes. A recusa desfaz a marcação |
| Beamformer | Nominal e máximo iguais (43 dBm): nunca propunha | Nominal = primeira potência medida no KPM (sem a medida, 37 dBm); máximo = nominal + 6 dB, até 43 dBm; a potência atual vem do KPM |
| RANSlicer-GreenRAN | No NORI a vazão por UE vem sempre 0, e a xApp se via sempre em risco e pedia o máximo (§10.6) | Vazão eMBB 0 com PRB em uso é medida ausente: a célula não é decidida nem entra na média da eficiência |
| Load Balancer | Calibrado ao longo das rodadas do S5, sem critério reconhecível; o ramo de teto de PRB gerava conflitos espúrios com o TS (13 no N12 do P3) | Condição A3 com CIO de 3 dB mantida por 640 ms (`lb_ttt_s`, valor de `TimeToTrigger` do TS 38.331), com o TTT recomeçando quando a condição cai. Ramo de teto de PRB desligado por padrão (`lb_open_cap_enabled`) |
| Painel (`resumo_campanha.py`) | Resoluções com a Rogue e com o `fault_injector` inflavam a contagem de conflitos (25 de 32 no B3 do piloto 16902) | Bloco de conflitos com "resoluções entre xApps legítimas" e "com xApp de teste ou evento" separadas |
| docs/16 | A tabela de energia (§8) descrevia a derivada de antes de 13/11; o rascunho do pré-registro 11 (§9) não declarava a hora fixa, as prioridades do projeto, o ISAC periódico nem a única xApp original | Coluna corrigida; item 8 de declarações no §9 |

**Descrição:** uma linha por problema apontado no comparativo, com a correção feita no código. Os números da coluna "Problema" vêm do comparativo e dos registros citados nele; nenhuma execução nova foi feita depois das correções.

**Testes.** Há testes novos para:
- a histerese no padrão do S2;
- a duplicação das janelas exigidas;
- a nova proposta depois de uma recusa;
- a fatia lida do KPM;
- o tempo de disparo do Load Balancer;
- o ramo de teto de PRB desligado;
- o Beamformer com a potência medida;
- a EnergySaver, que nunca sobe a potência ao reduzir;
- a vazão 0 da RANSlicer.

As suítes `tests/unit` e `tests/integration` passam (524 testes), com uma exceção. `test_schedule_replay.py::test_registered_native_schedules_are_reproduced` falha nos cronogramas `nr_S15_B3` (seeds 11001–11005, 12001–12005 e 9101). A falha já existia no commit `39bee5c`, antes destas correções, e foi conferida num worktree desse commit. A causa ainda não foi investigada.

**ns-3.** Os 10 cenários foram recompilados com a fatia no KPM, e todos compilam. Até esta seção, nenhuma simulação rodou com o código novo.

**Regras do autor para as próximas rodadas:**
- só como projeto multinível, com RDL-N1 e RDL-N2 juntas e todos os componentes;
- 5 sementes;
- saída pelo painel do §10.4, como na apresentação;
- a cada campanha concluída, atualizar os documentos e eliminar aos poucos os dados de antes destas correções.

### 10.17 Pendências resolvidas e xApps novas: CCO e escalonador por UE (2026-11-21)

**Pendências da §10.16:**

| Pendência | Causa | Resolução |
| :-- | :-- | :-- |
| `test_schedule_replay.py` falhava nos B3 do S15 (malha aberta) | A bisseção apontou o commit `69e241b` (§10.10): um handover já confirmado deixou de formar conflito indireto com propostas posteriores do mesmo nó. Com isso, as cotas de PRB do Energy Saving que vinham depois do handover do TS passaram, e antes o EEVS as descartava. A mudança foi intencional, mas os cronogramas registrados (sementes 9101, 11001–11005 e 12001–12005) são anteriores a ela | Exceção documentada no teste: para essas execuções, ele confere que o cronograma atual contém o registrado e que as ações a mais são só cotas de PRB de xApps que não pediram o handover |
| `repo_dirty: true` em execuções sem mudança de código | O checkout do Windows grava CRLF, e o git do WSL, sem normalizar, via os arquivos como alterados (56 no código, 147 na árvore toda na `cl_n12`) | `core.autocrlf=true` na consulta do executor (`run_ns3_certified.sh`) e do `run_conflict_experiment.py`. Conferido no WSL: 56 → 2, e os 2 eram as próprias edições |
| Recusa sem conflito não ficava registrada (§10.15) | O registro da janela só guardava as resoluções de conflito | O `HrdlStream` captura cada entrada do registro de propostas não atendidas e grava `rejections` (proposta, motivo, detalhe e vencedora) no registro da janela. Teste: a volta do UE 6 aparece com `HYSTERESIS` e `Control frequency exceeded` |
| Venv da F2 importava uma cópia antiga da F1 | O venv tinha a F1 instalada do commit fixado `9fefbff6` | A F1 local foi instalada em modo editável (`uv pip install -e ../XApp-RDL-F1`), como manda o README da F2 |

**Descrição:** uma linha por pendência deixada na §10.16, com a causa encontrada e a correção. Os números de arquivos alterados vêm do `git status` no WSL.

**xApps novas** (do relatório "Candidatas a xApps do escopo", na pasta `reports` do workspace):

| xApp | Parâmetro | Regra | Cenários | Conflito que cria |
| :-- | :-- | :-- | :-- | :-- |
| CCO (`CoverageCapacityOptimizer`, `xapp_id` `cco`) | `TX_POWER` | Com mais de 20 % dos UEs na borda (SINR < 0 dB ou RSRP < −115 dBm), sobe a potência 3 dB, até a potência medida no início mais 6 dB. Com cobertura folgada (nenhum UE na borda e 5º percentil do SINR > 10 dB), volta um passo em direção a ela. No máximo uma proposta a cada 2 s por célula; prioridade 75 | S4 e S6 (`extra_roles`) | direto com a EnergySaver e com o Beamformer em `TX_POWER`: o par CCO × ES da triagem de Wadud et al. |
| Escalonador por UE (`UeFairnessScheduler`, `xapp_id` `ue_scheduler`) | `SCHEDULER_WEIGHT` | Índice de Jain da vazão eMBB abaixo de 0,6 → peso 20 (mais justiça). Acima de 0,9 com carga acima de 80 % → peso 100 (PF clássico). Uma proposta por mudança de modo; a recusa devolve o modo anterior; prioridade 65 | S1 (`extra_roles`, com `--scheduler=pf`) | indireto com a URLLC Slice Guard e a EnergySaver (`SCHEDULER_WEIGHT` e `PRB_QUOTA` afetam `DRB.UEThpDl`): o par fatiamento × escalonamento de Sinha et al. |

**Descrição:** as duas xApps próprias acrescentadas ao escopo, com a regra de decisão, os cenários em que entram e o tipo de conflito que geram com as xApps existentes. Nenhuma das duas tem código público de referência; são declaradas como `xapp_impl: propria`.

**ns-3:**
- `SCHEDULER_WEIGHT` passou a ser aplicado: o peso de 1 a 100 vira o índice de justiça do PF (0,01 a 1), e o KPM da célula reporta `scheduler_weight`.
- A classe `RdlSchedulerOfdmaPF` (`rdl-nr-common.h`) é o OFDMA-PF do 5G-LENA, com os UEs já criados também atualizados, porque o atributo `FairnessIndex` só valia para UEs novos.
- O S1 ganhou `--scheduler=rr|pf`, com padrão `rr`, o escalonador anterior. A malha fechada usa `pf`.
- Com o escalonador Round Robin, a ação volta como `UNSUPPORTED`.

**MRO** (`MobilityRobustnessOptimizer`, `xapp_id` `mro`; autorizada pelo autor em 21/11):

| Peça | O que foi feito |
| :-- | :-- |
| Parâmetro na RDL | `A3_OFFSET` (dB, 0 a 10, uma casa decimal) no catálogo (`control_parameter.py`, `param_id` 6), no Safety Guard, no codificador E2SM-RC (escala 10) e na cadeia E2 da malha fechada. Fica sem capacidade padrão registrada, como o `CELL_STATE`: num nó real o despacho só ocorre depois que o nó anunciar o parâmetro. A percepção liga `A3_OFFSET` a `DRB.UEThpDl` e `RRU.PrbUsedDl`, os mesmos KPIs do `HANDOVER`, e por isso detecta o conflito indireto com o Load Balancer e o TS |
| ns-3 | `RdlMroHandoverAlgorithm` (`rdl-nr-common.h`). O UE relata o A3 sem margem (TTT de 256 ms, relatório a cada 240 ms), e a gNB só pede o handover se a vizinha superar a servidora pela margem da célula, que a RDL muda durante a simulação. O A3 do 5G-LENA não serve para isso, porque fixa a histerese na configuração de medição enviada ao UE no início. O KPM da célula reporta `a3_offset_db`. Fica ligado por `--handoverAlgo=mro` no S5 (`RdlBuildNrNetwork`, parâmetro novo, com padrão `none`) |
| xApp | Por célula de origem, numa janela de 10 s, conta ping-pongs (volta em até 5 s), handovers prematuros (perda de conexão em até 3 s depois de sair) e tardios (perda ainda na célula e volta por outra). A cada 5 s, mais prematuros que tardios (por 2) sobe a margem 1 dB, até 10 dB; o inverso desce, até 0. Prioridade 70 |
| Cenário | S5 da malha fechada com metade dos UEs andando a 5 m/s (P3, §10.15) e `--handoverAlgo=mro`. Os handovers passam a acontecer também sem pedido das xApps, e a MRO disputa com o Load Balancer e o TS: o par MRO × MLB do ACCoRD |

**Descrição:** as peças acrescentadas para a MRO, da RDL ao ns-3. A mudança no S5 (mobilidade e handover automático) vale para todos os braços das campanhas novas.

**Originais baixadas** (autorização do autor em 21/11; em `~/xapps-originais/` no WSL, fora do repositório):

| Original | Commit | O que a integração exige |
| :-- | :-- | :-- |
| `o-ran-sc/ric-app-ad` | `350a975` (2026-10-14) | Modelo Isolation Forest treinado pelo próprio código (`ad_train.py`) sobre o conjunto da Viavi que acompanha o repositório (`ue.csv`), com 31 colunas: RSRP, RSRQ e SINR da servidora e de 5 vizinhas, posição x e y, uso de PRB, vazão-alvo e vazão. A regra de causa compara cada UE com o próprio histórico de 20 s. O KPM do ns-3 não traz RSRQ nem posição e tem no máximo 3 vizinhas, e os valores do ns-3 (RSRP perto de −130 dBm) estão fora da faixa do conjunto da Viavi (cerca de −90 dBm). **Decisão necessária:** treinar com o próprio código sobre o `ue.csv` (original, mas fora do domínio) ou sobre execuções de aquecimento do ns-3 pré-registradas e congeladas, como a D4 do xSlice |
| `o-ran-sc/ric-app-qp` | `9c6dfa7` (2026-10-14) | Modelo de série temporal por célula treinado sobre `cells.csv` (dados da Viavi), com a mesma questão de domínio do AD |
| `usnistgov/ns3-oran` | `5e60f2d` (2026-05-26) | Os módulos de lógica (`oran-lm-lte-2-lte-*`) e os relatores são só LTE: não leem dispositivos NR do 5G-LENA. Usá-los exige escrever relatores NR e um adaptador para o RIC do módulo. A versão é para o ns-3.42, e o projeto usa o 3.48 |
| xSlice original (`GNNRL/`) | `87db3bd` (já em `~/xapps-originais`) | Venv `~/.venvs/gnnrl` instalado: torch 2.5.1+cpu, torch_geometric 2.8.1, gym 0.26.2. Falta o que o §4.1 já listava: estatísticas de MAC por UE no ns-3 (MCS, TBS, RBs, BLER), o SQLite no esquema do FlexRIC alimentado pelo shim e o modelo pré-treinado da D4 |

**Descrição:** o estado de cada original baixada, com o commit clonado e o que falta para ela rodar na malha fechada. Nenhuma delas roda ainda. As três primeiras exigem uma decisão sobre os dados de treino ou de adaptação antes de qualquer código de integração.

**Validação curta das peças novas** (não é campanha: uma semente, 16999, no modo multinível N12, com todos os componentes; execuções `val_*`, fora do commit, a apagar com a regra de limpeza):

| Execução | Tempo simulado | O que confirmou |
| :-- | :-- | :-- |
| `val_S1_N12_pf_seed16999` | 8 s | <ul><li>A fatia está no KPM de 20 dos 20 UEs (6 URLLC e 14 eMBB, como o cenário declara).</li><li>A URLLC Slice Guard limitou a eMBB a 25 % (t = 1,2 s).</li><li>O escalonador por UE pediu peso 20, e o ns-3 aplicou `FairnessIndex` = 0,2 no PF e reportou `scheduler_weight` = 20 (t = 1,4 s).</li><li>A EnergySaver reduziu a potência de 4 para 1 dBm, e não mais para 30 dBm (t = 5,2 s).</li></ul>`SUCCESS` |
| `val_S5_N12_mro_seed16999` | 15 s | <ul><li>A margem do A3 começa em 3 dB nas duas células.</li><li>A MRO a subiu para 4 dB na gNB0 (t = 12,6 s), e o KPM passou a reportar 4,0.</li><li>Houve 10 mudanças de célula para 9 handovers pedidos pelas xApps (8 do TS, 1 do Load Balancer): ao menos um handover foi automático.</li><li>A RDL resolveu 3 conflitos indiretos.</li></ul>`SUCCESS` |

**Descrição:** cada linha é uma execução curta feita para conferir que as peças novas funcionam no ns-3 e na cadeia completa. Os números vêm da conferência por script ao fim de cada execução (`closed_loop_log.jsonl` e `rdl_actuation_log.csv`). As execuções não medem desempenho e não entram em nenhum resultado.
