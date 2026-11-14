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
  - por UE: célula servidora, SINR servidora, SINR e RSRP das vizinhas, vazão e atraso;
  - por fatia: vazão, atraso e PRB usados (o xSlice usa 3 fatias).
  
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

## 5. Mapeamento dos `xapp_id` do catálogo

| `xapp_id` | Cenários | Fonte da proposta em malha fechada | Situação |
| :-- | :-- | :-- | :-- |
| `xslice` | S0, S1, S2, S3, S6, S7, S8, S12, S14 | xSlice original (C e GNNRL) | só `PRB_QUOTA`; o `TX_POWER` do S3 não existe no original |
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
| Derivados (a) | **Controle pareado.** Nos cenários em que o derivado e o original propõem o mesmo parâmetro, o cenário roda também com o derivado no papel do original, com as mesmas sementes e baselines: xSlice com `PRB_QUOTA` e Traffic Steering com `HANDOVER`. O objetivo é medir quanto a reimplementação se afasta do original e se os números já publicados (campanhas 01 a 10, cujo catálogo reproduz o papel dos derivados) continuam valendo. O Energy Saving não tem par direto: o derivado propõe `TX_POWER`, e o original, `HANDOVER` e `CELL_STATE`. Para a comparação ser justa, o derivado passa a ler o KPM do ns-3 pelo mesmo adaptador, sem mudar a regra de decisão documentada. As execuções com derivado são marcadas no manifesto (`xapp_impl: derivado`) e nunca contam como execução com o original. Cenários, métrica de afastamento e critério ficam no pré-registro 11, ou num 11b. |
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
| Entrada | KPM por UE: SINR servidor e das vizinhas | **nenhuma telemetria**: bateria, solar e ambiente vêm de variáveis de ambiente | KPM por célula (carga em %, UEs) e política A1 21001 |
| Decisão | célula com no máximo 1 UE registrado → handover dos UEs → `CELL_OFF` | **constante**: `TX_POWER` de 18, 20 ou 21 dBm conforme o ambiente e a bateria configurados, a cada 2,5 s, em todos os nós | carga atual **e** carga esperada na próxima hora (perfil sazonal) abaixo do limiar, dentro da janela de economia, com vizinha capaz de absorver |
| Ações | `HANDOVER` por UE e `CELL_STATE = 0` | só `TX_POWER` (os "modos" de sono são rótulos, sem ação diferente) | `HANDOVER` (evacuação), `CELL_STATE` 0 e 1, `TX_POWER` com carga moderada |
| Destino do handover | por UE, a vizinha de maior SINR (exige 5 amostras e mais de −10 dB) | não faz handover | por célula, a vizinha **menos carregada** que fica abaixo do limiar de despertar, sem olhar o sinal do UE |
| Religar célula | **não existe** | não se aplica | existe: fim da janela, vizinha sobrecarregada ou carga esperada alta (prioridade 85) |
| Confirma a evacuação antes de desligar | conta handovers *enviados* como concluídos; ou espera 30 s | não se aplica | **não**: no período seguinte ao handover, propõe o desligamento mesmo que ainda haja UEs |
| Coordenação | nenhuma (controla o E2 direto) | RMR 30000 para a RDL, sem tratar recusas | RMR 30000, `defer_ok`, `ttl_ms` e volta a `ACTIVE` se a RDL recusar |
| Limites de escala | 20 UEs por célula, 10 células, registro que nunca é limpo | nenhum | nenhum |
| Tempo | `time()` e `sleep(5)` (relógio simulado na malha fechada) | `time.sleep(2.5)` | `hour_of(t)`, por padrão o horário **local de parede** |

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
7. **Regras de relato:** iguais às do pré-registro 10 (`--retry-failed` uma vez; retomada depois de interrupção). Acrescenta-se uma regra: o relato separa as falhas de xApp das falhas do ns-3.

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

- **xApps reais no RIC:** RANSlicer-GreenRAN, a derivada do xSlice e a `embb_throughput` como xApps do Near-RT RIC (charts Helm), assinando o KPM do gNB do NORI pelo SubMgr (`RicKpmSource`) e enviando propostas pelo RMR 30000.
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
