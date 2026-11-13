# 16. xApps originais em malha fechada nas simulações de cenário

Status: **desenho**, escrito em 2026-11-12 durante a campanha 10. Nada aqui está implementado. A implementação começa depois da campanha 10 e das pendências dela: `--retry-failed`, análise do pré-registro 10 e merge de `eevs-aditivo-padrao`. Este arquivo só entra no git nesse momento, porque o executor grava o HEAD em cada execução.

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
                                   baseline B0 | B1 | B2 | B3 (H-RDL real, RMR 30000/30001)
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
  - as xApps assíncronas podem tornar a execução não determinística;
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
- **Adaptador:**
  - **papel do AD:** a regra de anomalia fica em aberto (seção 7, D3);
  - **papel do QP:** devolve a vazão **medida** no ns-3 por célula para cada UE da lista;
  - **servidor gRPC RC:** o handover vira `HANDOVER`, com `xapp_id = "traffic_steering"`;
  - **política A1:** o orquestrador envia o 20010 com o `threshold` do cenário no início da execução.
- **Colisão do RMR 30000:** o TS usa 30000 (`TS_UE_LIST`) e a RDL usa 30000 (`RDL_ACTION_PROPOSAL`).
  - **Regra:** cada processo tem a própria tabela de rotas (`RMR_SEED_RT`). Na do TS, 30000 vai **só** para o endpoint QP do adaptador. Na do adaptador, 30000 vai para a RDL. O TS não tem rota para a RDL.
  - **Defesa extra:** a RDL já valida o esquema da proposta e o registro de xApps no modo estrito. Uma `TS_UE_LIST` que chegue à RDL é recusada e registrada.
  - **Teste:** um teste de integração verifica que nenhuma mensagem do TS chega à porta da RDL.

### 4.4 xApps próprias que ficam

- **GreenRAN:** xApp1-RANSlicer e xApp2-EnergySaver (`src/greenran/`), com KPM do orquestrador e proposta pelo `rdl_transport` (RMR).
- **Rogue:** `reference-xapps/rogue-xapp/`, idem.

## 5. Mapeamento dos `xapp_id` do catálogo

| `xapp_id` | Cenários | Fonte da proposta em malha fechada | Situação |
| :-- | :-- | :-- | :-- |
| `xslice` | S0, S1, S2, S3, S6, S7, S8, S12, S14 | xSlice original (C e GNNRL) | só `PRB_QUOTA`; o `TX_POWER` do S3 não existe no original |
| `traffic_steering` | S2, S4, S5, S9, S10, S11, S13, S15, G2 | ric-app-ts original | `HANDOVER` |
| `energy_saving` | S0, S1, S3, S4, S6, S9, S10, S12, S13, S15, G1 | ES Orange original | só `HANDOVER` e `CELL_STATE` (ver 4.2); no G1, decidir entre o ES Orange e a xApp2 do GreenRAN (D1) |
| `energy_saving_ru0/ru1` | G2 | duas instâncias do ES Orange, ou a xApp2 do GreenRAN | D1 |
| `ranslicer` | G1 | xApp1-RANSlicer (própria) | pronta para adaptar |
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
| D1 | No G1 e no G2, a economia de energia fica com a **xApp2-EnergySaver do GreenRAN**. O ES Orange original fica nos cenários S. |
| D2 | `load_balancer`, `beamformer`, `isac_radar` e `embb_throughput` viram **xApps próprias**, com lógica documentada, que leem o KPM e propõem pela 30000. S5, S6, S8, S11 e S14 continuam. |
| D3 | AD e QP são **emulados no adaptador**: anomalia quando a vazão do UE cai abaixo de um limiar fixado no pré-registro, e predição igual à vazão medida no ns-3. |
| D4 | O PPO do xSlice parte de um **modelo pré-treinado** em execuções de aquecimento pré-registradas, com sementes separadas, e fica congelado nas campanhas. |
| D5 | Os cenários que perdem o conflito (S3 com `TX_POWER` do xSlice; S0, S3, S4 e S10 com `TX_POWER` do ES) **mudam de parâmetro**: o conflito é refeito com `PRB_QUOTA`, `HANDOVER` ou `CELL_STATE`, que os originais propõem. A definição desses cenários muda e entra no pré-registro 11. Os derivados em Python dos originais ficam no repositório (seção 1). |
| Ordem | Os pré-registros 12 (energia, doc 17) e 13 (calibração, doc 18) **esperam este desenho** e rodam já em malha fechada, sem exceção à regra. |
| Sementes | O pré-registro 11 usa **16001 a 16005**. As 12001 a 12005 já foram rodadas no pré-registro 09. |
| Derivados (a) | **Controle pareado.** Nos cenários em que o derivado e o original propõem o mesmo parâmetro, o cenário roda também com o derivado no papel do original, com as mesmas sementes e baselines: xSlice com `PRB_QUOTA` e Traffic Steering com `HANDOVER`. O objetivo é medir quanto a reimplementação se afasta do original e se os números já publicados (campanhas 01 a 10, cujo catálogo reproduz o papel dos derivados) continuam valendo. O Energy Saving não tem par direto: o derivado propõe `TX_POWER`, e o original, `HANDOVER` e `CELL_STATE`. Para a comparação ser justa, o derivado passa a ler o KPM do ns-3 pelo mesmo adaptador, sem mudar a regra de decisão documentada. As execuções com derivado são marcadas no manifesto (`xapp_impl: derivado`) e nunca contam como execução com o original. Cenários, métrica de afastamento e critério ficam no pré-registro 11, ou num 11b. |
| Derivados (b) | **Ponte para o testbed.** No laboratório com srsRAN e OSC RIC (perfil GERCOM; ver `docs/compliance/VARREDURA_TESTBEDS_OPENRAN_BRASIL.md` §5), os originais do xSlice e do ES, que são xApps do FlexRIC, não rodam. Os derivados, que falam RMR com a RDL e já têm charts Helm, levam esses papéis à bancada real, inclusive no gate TB7 (arbitragem entre duas xApps reais). O papel vale até existir uma ponte E42 ↔ RMR. No laboratório com OAI e FlexRIC, rodam os originais. **Ressalva (2026-11-12):** a equipe informou que o testbed não terá fatiamento. Sem fatias, o papel do xSlice na bancada depende das propostas P1 (fatia no núcleo) ou P3 (teto de PRB da célula) da [varredura dos testbeds, §7](compliance/VARREDURA_TESTBEDS_OPENRAN_BRASIL.md). |

Texto original das perguntas:

- **D1.** No G1 e no G2, o papel de "energy saving" fica com o ES Orange original ou com a xApp2-EnergySaver do GreenRAN, que é própria e foi feita para esses cenários?
- **D2.** Para `load_balancer`, `beamformer`, `isac_radar` e `embb_throughput`, que não têm original:
  - (a) xApp própria, com lógica documentada;
  - (b) procurar um original público;
  - (c) tirar o papel dos cenários S5, S6, S8, S11 e S14.
- **D3.** No TS, como fazer o papel do AD e do QP:
  - (a) rodar os originais `ric-app-ad` e `ric-app-qp` do O-RAN SC, que são modelos treinados em dados próprios e precisam de mais downloads;
  - (b) emular no adaptador: anomalia quando a vazão do UE cai abaixo de um limiar fixado no pré-registro, e "predição" igual à vazão medida.
- **D4.** No xSlice, o PPO aprende em linha. Ele parte do zero em cada execução, ou de um modelo pré-treinado em execuções de aquecimento, que também precisam de pré-registro?
- **D5.** Os cenários que perdem o conflito com os originais, como S3 (`TX_POWER` do xSlice) e S0, S3, S4 e S10 (`TX_POWER` do ES), saem, mudam de parâmetro ou ficam como controle sem conflito?

## 8. Etapas

| Etapa | Entrega | Gate |
| :-- | :-- | :-- |
| E0 | permissão para os downloads, fontes no commit exato, `SOURCE.md` atualizado | hashes conferidos |
| E1 | `RdlKpmExporter` e modo `--control-socket` no `rdl-nr-common.h`; orquestrador com xApp nula | ns-3 em passo travado reproduz o modo de cronograma com as mesmas ações (mesmo `thp_conflict`) |
| E2 | `libe42_shim`; xSlice e ES Orange compilados sem alteração | `sha256` dos `.c` igual ao do `SOURCE.md`; a indicação chega e o controle vira proposta |
| E3 | adaptador O-RAN SC (QP, AD e servidor gRPC RC) e rotas RMR isoladas | o teste de isolamento do 30000 passa |
| E4 | GreenRAN e Rogue no orquestrador; `fault_injector` como evento | todas as xApps do catálogo atendidas ou decididas (D1–D5) |
| E5 | teste de cadeia (`tests/integration/test_cadeia_malha_fechada.py`) | xApp → 30000 → RDL → ação → ns-3 → KPM → xApp em S8, S11 e G2 |
| E6 | os derivados em Python ficam (D5) e ganham leitura de KPM pelo adaptador, para o controle pareado. Atualizar `reference-xapps/README.md`, `docs/03` e o relatório de adequação: nas campanhas de cenário, as propostas vêm dos originais. Os `third_party/xapps/*` passam para `xapps-originais/` com os adaptadores. | testes verdes; nenhuma campanha usa os derivados como fonte de propostas |
| E7 | piloto e pré-registro 11 commitado antes da campanha | seção 9 |
| E8 | artigos: trocar "xApps de terceiros usadas como referência" pela execução dos originais | números só pelos scripts |

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
