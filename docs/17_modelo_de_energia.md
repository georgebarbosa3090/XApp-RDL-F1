# 17. Modelo de energia: instrumentação no ns-3, modelo de potência da estação base e métrica por cenário

Status: **desenho**, escrito em 2026-11-12 durante a campanha 10. Nada aqui está implementado. Este arquivo só entra no git depois da campanha 10, porque o executor grava o HEAD em cada execução.

**Decisões do autor (2026-11-12):**
- Aprovados, para depois da campanha 10:
  - a correção **C17.1** (`P_SLEEP_W` de 4,3 W para 75 W, coerente com a macro de `P0_W = 130`);
  - o modo **`UniformPowerAllocBw`** na campanha de energia.
- **Ordem:** o pré-registro 12 espera o doc 16 e roda em malha fechada, com as xApps originais no laço. Não há exceção para malha aberta. O desenho do pré-registro (seção final) tem de ser ajustado a isso antes do registro.

Limite que este desenho resolve (artigo SBRC, seção Limitações): *"A energia não é medida, só aproximada por PRBs ativos e células ligadas; no 5G-LENA, a célula desligada é emulada por potência muito baixa."*

## 1. Decisões

1. **O ns-3 grava grandezas do simulador; o modelo de potência é aplicado depois, em Python.** O C++ não calcula watts. Ele grava, por célula e janela, contadores de ocupação de recursos, de potência de TX e de estado. Assim o mesmo dado serve a mais de um modelo, e um parâmetro corrigido não exige rodar o ns-3 de novo.
2. **Modelo principal: 3GPP TR 38.864 V18.1.0 (Release 18), cláusula 5.1.** É o modelo de potência de estação base NR que o 3GPP padronizou para avaliar economia de energia. Ele tem estados de sono com tempo e energia de transição e escala com a ocupação de RBs e símbolos. O texto foi conferido no documento original (seção 4.1).
3. **Modelo de robustez: EARTH (Auer et al., 2011).** É o modelo linear clássico, em watts. Uma conclusão sobre energia só entra num artigo se o sinal da diferença pareada B3 − B0 for o mesmo nos dois modelos (H13.3).
4. **A campanha de energia roda com potência por PSD constante (`UniformPowerAllocBw`), e não com o padrão do 5G-LENA (`UniformPowerAllocUsed`).** No padrão, a potência total de TX se concentra nos RBs usados. Um teto de PRB, então, não reduz a potência irradiada (seção 2.3).
5. **Métrica:** energia na janela de conflito em unidades relativas do TR (u.r.·s) e em joules do EARTH; economia percentual contra o B0, que é a métrica do próprio TR; e energia por bit entregue.
6. **O que continua modelo:** o consumo em watts e o sono real da célula. O gate GR4 do testbed mede o consumo (seção 6).

## 2. Ponto de partida (conferido no código e nas execuções)

### 2.1 O que a execução grava hoje

- `raw/rdl_kpi_timeseries.csv` (`RdlKpiSampler`, `simulations/ns3/rdl-nr-common.h`): `t_end_s,cell_id,rx_packets,rx_bytes,throughput_mbps,mean_delay_ms`, a cada `kpiPeriod` = 0,1 s (`scenario_rdl_multicell.cc`, `kpiPeriod = 0.1`).
  - A vazão é medida nos `UdpServer` dos UEs e atribuída à célula servidora do UE no instante da recepção.
  - **Lacuna:** `Flush()` só escreve as células que receberam pacotes na janela. Uma célula ociosa ou desligada não aparece. Para vazão isso não importa, porque a análise soma as células. Para energia importa: a célula ociosa consome.
  - Exemplo conferido: `experiments/runs/nr_G1_B3_seed9101/raw/rdl_kpi_timeseries.csv`, com 319 linhas de dados.
- `raw/rdl_actuation_log.csv` (`RdlActuation::Record`): `time_s,gnb,cell_id,parameter,value,ue,xapp_id,action_id,status,detail`. Por exemplo, `PRB_QUOTA` 80 → `RBG 85/106` no G1 com 20 MHz.
- Não há ocupação de PRB, potência de TX nem estado da célula por janela.

### 2.2 Como a célula "desligada" é emulada

`RdlActuation::Apply`, ramo `CELL_STATE` (`rdl-nr-common.h`):

- com valor 0, a potência de TX vai a `kSleepTxPowerDbm = -30.0` dBm e a potência anterior é guardada em `m_savedTxPower`;
- com valor 1, a potência é restaurada.

O 5G-LENA v5.1 não tem desligamento de célula. A célula a −30 dBm continua escalonando e transmitindo controle. Os UEs dela entram em falha de enlace (RLF, T310/N310) e se reconectam à vizinha (achado 57a, `docs/07`). Portanto:

- a energia de uma célula "desligada" **não pode** ser lida do simulador: ela é um estado do modelo, comandado pelo log de atuação;
- o simulador pode, sim, dizer se a célula "desligada" ainda transmitiu dados. O desenho grava esse **vazamento** (seção 3.2, `sleep_data_reg`) e o testa (H13.4).

### 2.3 Alocação de potência do 5G-LENA: um artefato que afeta energia e vazão

Conferido no código do 5G-LENA v5.1 instalado (`contrib/nr`, `nr_commit` `cedceadd`):

- O atributo `ns3::NrGnbPhy::PowerAllocationType` tem padrão `UniformPowerAllocUsed` (`nr-gnb-phy.cc`; `nr-phy.h`, `m_powerAllocationType`). Nenhum cenário do projeto o altera (busca por `PowerAllocation` em `simulations/ns3/` sem resultado).
- **`UniformPowerAllocUsed`:** PSD = P_TX ÷ (RBs ativos × largura do RB) (`NrSpectrumValueHelper::CreateTxPsdOverActiveRbs`). A potência total irradiada é P_TX sempre que algum RB é usado.
- **`UniformPowerAllocBw`:** PSD = P_TX ÷ (todos os RBs × largura) (`CreateTxPsdOverAllRbs`). A potência irradiada é proporcional aos RBs usados, como numa estação real com EPRE fixa.

Consequências:

1. **Energia:** no modo padrão, um teto de PRB não reduz a potência irradiada. Num modelo físico, a economia de um teto vem toda dos símbolos sem transmissão. Exemplo derivado dos parâmetros da seção 4, com demanda que ocuparia toda a banda e os 14 símbolos do slot:
   - modo BW, teto de 30 % contra 100 %: o TR Cat. 1/Set 2 cai de 200 para 137 u.r. (−31,5 %), e o EARTH (um TRX) cai de 224 para 158 W (−29,4 %);
   - modo USED: 0 % nos dois modelos.
2. **Vazão (ameaça à validade das campanhas com teto de PRB):** no modo USED, um teto concentra a potência nos RBs restantes. O ganho de PSD por RB é 10·log₁₀(1/teto): +5,2 dB com teto de 30 %, como no G1 (EnergySaver) e no S12. Isso **atenua a perda de vazão que o teto causaria** numa estação com EPRE fixa. Nenhum número já publicado está errado como medida *daquele* rádio simulado. A leitura "o teto do EnergySaver custa X % de vazão", porém, fica otimista. Isso entra na lista de correções (seção 8) e é quantificado no G1 (H13.6).

## 3. Instrumentação no ns-3 (`rdl-nr-common.h`)

### 3.1 Fontes de traço do 5G-LENA usadas (conferidas no código)

| Fonte | Classe | Assinatura | O que dá |
| :-- | :-- | :-- | :-- |
| `SlotDataStats` | `NrGnbPhy` | `(const SfnSf&, uint32_t scheduledUe, uint32_t usedReg, uint32_t usedSym, uint32_t availableRb, uint32_t availableSym, uint16_t bwpId, uint16_t cellId)` | por slot: REG de dados usados (1 REG = 1 RB × 1 símbolo), símbolos de dados, RBs disponíveis e UEs escalonados |
| `SlotCtrlStats` | `NrGnbPhy` | mesma | idem para o controle |
| `DlScheduling` | `NrGnbMac` | `NrSchedulingCallbackInfo` (`m_tbSize`, `m_numSym`, `m_mcs`, `m_rnti`) | bytes de TB DL por alocação |
| `UlScheduling` | `NrGnbMac` | idem | bytes de TB UL, para limitar a parcela UL (ver abaixo) |

- `NrGnbPhy::DoStartSlot()` chama `GenerateAllocationStatistics` em **todo** slot, inclusive nos vazios. Logo, a contagem de slots pelo traço é completa.
- **Limite:** `usedReg` soma as alocações DL e UL do slot (`GenerateAllocationStatistics` conta toda DCI de tipo `DATA`/`MSG3`, sem olhar `m_format`). Os cenários só têm tráfego UDP no downlink, e o UL de dados se reduz a sinalização. O desenho não altera o módulo `nr`, que está fixado por `nr_commit` no manifesto. Em vez disso, grava os bytes de TB UL e DL e testa a parcela UL (H13.5).
- A conexão é direta em cada PHY e MAC, com `TraceConnectWithoutContext` sobre `NrHelper::GetGnbPhy(dev, b)` e `NrHelper::GetGnbMac(dev, b)`. Não usa caminho de `Config` e não consome número aleatório.

### 3.2 Nova classe `RdlCellEnergySampler` e arquivo `raw/rdl_cell_state.csv`

Os contadores são **cumulativos e monotônicos**, por célula. Cada janela é a diferença entre dois fechamentos. É isso que permite dividir a classe com o docs/16 (seção 7).

Uma linha por célula e janela, **para todas as células, inclusive as ociosas e as desligadas**:

| Campo | Definição |
| :-- | :-- |
| `t_end_s`, `cell_id`, `gnb` | fim da janela (mesma grade do `rdl_kpi_timeseries.csv`), célula e índice do gNB |
| `slots`, `slot_s`, `sym_per_slot`, `avail_rb` | slots na janela, duração do slot (`GetSlotPeriod`), símbolos por slot (`GetSymbolsPerSlot`) e RBs da portadora (`GetRbNum`) |
| `data_reg`, `ctrl_reg` | Σ `usedReg` de dados e de controle |
| `data_sym`, `ctrl_sym` | Σ símbolos de dados e de controle usados |
| `active_slots` | slots com `data_reg` > 0 |
| `sched_ue_sum` | Σ UEs escalonados por slot (UEs médios = ÷ `slots`) |
| `ptx_dbm_min`, `ptx_dbm_max` | potência de TX configurada no PHY (`GetTxPower`), mínima e máxima na janela |
| `reg_ptx_mw` | Σ por slot de (`data_reg` + `ctrl_reg`) × P_TX [mW] |
| `sym_ptx_mw` | Σ por slot de (`data_sym` + `ctrl_sym`) × P_TX [mW] |
| `sleep_slots` | slots com a célula em sono emulado (`RdlActuation::IsSleeping`, seção 3.3) |
| `sleep_data_reg` | `data_reg` transmitido em sono emulado (vazamento) |
| `dl_tb_bytes`, `ul_tb_bytes` | Σ `m_tbSize` dos traços `DlScheduling` e `UlScheduling` |
| `connected_ues` | UEs com `NrUeRrc::CONNECTED_NORMALLY` e `GetCellId()` igual à célula, no fechamento |
| `power_alloc` | `used` ou `bw` (atributo efetivo do PHY) |

Os dois somatórios ponderados pela potência (`reg_ptx_mw` e `sym_ptx_mw`) cobrem os dois modos de alocação sem gravar dados por slot. Os dois modelos são afins na ocupação de cada slot (seção 4), então a soma na janela basta.

Esqueleto (o desenho; a assinatura de `MakeBoundCallback` com dois argumentos ligados se confirma na compilação):

```cpp
// ---- Energia (docs/17): contadores por célula; o modelo de potência é aplicado em Python ----
struct RdlCellCounters {            // cumulativos desde t = 0
  uint64_t slots{0}, activeSlots{0}, dataReg{0}, ctrlReg{0}, dataSym{0}, ctrlSym{0}, schedUe{0};
  uint64_t sleepSlots{0}, sleepDataReg{0}, dlTbBytes{0}, ulTbBytes{0};
  double regPtxMw{0.0}, symPtxMw{0.0}, ptxDbmMin{1e9}, ptxDbmMax{-1e9};
};

class RdlCellEnergySampler {
 public:
  RdlCellEnergySampler(NetDeviceContainer gnbDevs, NetDeviceContainer ueDevs,
                       const RdlActuation* actuation, double periodS, double simTime,
                       bool ownTimer = true);           // ownTimer=false: quem fecha a janela é o exportador do docs/16
  const RdlCellCounters& Cumulative(uint16_t cellId) const;   // leitura pelo RdlKpmExporter (docs/16)
  uint32_t ConnectedUes(uint16_t cellId) const;
  void CloseWindow();                                    // escreve uma linha por célula (diferenças) e guarda o fechamento
 private:
  void OnSlotData(const SfnSf&, uint32_t ue, uint32_t reg, uint32_t sym, uint32_t rb, uint32_t avSym,
                  uint16_t bwp, uint16_t cell);
  void OnSlotCtrl(const SfnSf&, uint32_t ue, uint32_t reg, uint32_t sym, uint32_t rb, uint32_t avSym,
                  uint16_t bwp, uint16_t cell);
  static void OnDlSched(RdlCellEnergySampler* self, uint16_t cell, NrSchedulingCallbackInfo info);
  static void OnUlSched(RdlCellEnergySampler* self, uint16_t cell, NrSchedulingCallbackInfo info);
  std::map<uint16_t, Ptr<NrGnbPhy>> m_phyByCell;  std::map<uint16_t, uint32_t> m_gnbByCell;
  std::map<uint16_t, RdlCellCounters> m_cum, m_lastClose;
  // ...
};
```

- **Custo:** um *callback* por slot e por célula, com aritmética inteira. Com SCS de 15 kHz (106 RBs a 20 MHz, como em `RBG 85/106` no G1), são 1000 slots/s por célula: no G1, 2 células × 30 s × 1000 = 60 mil chamadas. É desprezível perto da PHY. O custo real se mede no gate H13.0.

### 3.3 Mudanças pequenas fora da classe

- `RdlActuation`: um *getter* `bool IsSleeping(uint32_t gnb) const`, que devolve `m_savedTxPower.count(gnb) > 0`. É a única fonte do estado comandado. Não muda o comportamento.
- `scenario_rdl_multicell.cc` (e os demais cenários que forem usados): uma opção `--powerAllocation=used|bw`, com padrão `used`. O padrão reproduz as campanhas anteriores. Com `bw`, aplica-se `Config::SetDefault("ns3::NrGnbPhy::PowerAllocationType", EnumValue(NrSpectrumValueHelper::UNIFORM_POWER_ALLOCATION_BW))` antes de instalar os dispositivos. A instanciação do sampler fica logo depois do `RdlKpiSampler`.
- O cabeçalho do `rdl_kpi_timeseries.csv` **não muda**. A análise das execuções antigas continua lendo o mesmo formato.
- O executor certificado já copia todo `*.csv` do diretório de trabalho para `raw/` e o inclui nos hashes (`scripts/certification/run_ns3_certified.sh`, linhas 145–146). Também grava o sha256 do `rdl-nr-common.h` em `support_files_sha256`. Não é preciso mudar o executor.
- `run_native_campaign.sh` e `run_conflict_campaign.py` precisam repassar `--sim-arg` (o `run_conflict_experiment.py` já aceita), para que a campanha passe `--powerAllocation=bw`. O modo fica no `command` do manifesto e na coluna `power_alloc`.

## 4. Modelos de potência

### 4.1 Modelo principal: 3GPP TR 38.864 V18.1.0, cláusula 5.1

Conferido no texto do TR (arquivo `38864-i10.zip` do arquivo público do 3GPP, documento "3GPP TR 38.864 V18.1.0 (2023-03)"; Tabelas 5.1-1 a 5.1-5 e fórmula de escala da cláusula 5.1).

**Configurações de referência (Tab. 5.1-1):**

- Set 1: FR1 TDD, 100 MHz, SCS 30 kHz, 64 TxRU, 55 dBm;
- Set 2: FR1 FDD, 20 MHz, SCS 15 kHz, 32 TxRU, 49 dBm.

**Potência relativa (Tab. 5.1-3), em u.r.:**

| Estado | Cat. 1, Set 1 | Cat. 1, Set 2 | Cat. 2, Set 1 | Cat. 2, Set 2 |
| :-- | --: | --: | --: | --: |
| Deep sleep (P1) | 1 | 1 | 1 | 1 |
| Light sleep (P2) | 25 | 25 | 2,1 | 2,1 |
| Micro sleep (P3) | 55 | 50 | 5,5 | 5 |
| Active DL (P4) | 280 | 200 | 32 | 26 |
| Active UL (P5) | 110 | 90 | 6,5 | 5,8 |

**Transição (Tab. 5.1-4 e 5.1-5):**

- tempo total: Cat. 1, deep 50 ms e light 6 ms; Cat. 2, deep 10 s e light 640 ms;
- energia adicional, em u.r.·ms: Cat. 1, deep 1000 e light 90; Cat. 2, deep 17000 e light 1088;
- durante a transição, consome-se a potência do estado de sono;
- micro sleep tem transição imediata.

**Escala do DL (cláusula 5.1):**

- P^DL = P_static + s_a·[P_dyn,ante + (s_f·s_p/η)·P_dyn,joint];
- P_static = P3 na linha de base (opcional: 1,5·P3);
- P_dyn,ante = A·(P4 − P_static) e P_dyn,joint = (1 − A)·(P4 − P_static), com η = 1;
- A = 0,4 na linha de base (opcionais 0,1 e 0,7);
- s_a: fração de TxRU ativas; s_f: razão de banda; s_p: razão de PSD por TxRU contra a referência.

O TR lista a ocupação de RBs e de símbolos entre as bases de escala admitidas, soma a potência do slot símbolo a símbolo e expressa o ganho como redução percentual contra a linha de base na mesma duração.

**Mapeamento para os cenários (hipóteses de modelagem, declaradas):**

- **Set por banda:** 20 MHz e 10 MHz (G1, S9, S12 e S15) usam o Set 2. Os cenários com o padrão de 100 MHz (G2, S10, S11 e S13; `bandwidth = 100e6` em `scenario_rdl_multicell.cc`) usam o Set 1. No S12 (10 MHz), s_f é multiplicado por 10/20, porque a banda de RF é metade da do Set 2.
- **s_a = 1.** Os cenários usam uma antena isotrópica 1×1 por gNB (`RdlBuildNrNetwork`) e não adaptam antenas. A antena simulada representa o arranjo inteiro.
- **Referência de potência:** s_p = 1 na potência nominal do cenário, ou seja, P_ref = 43 dBm (`txPowerDbm = 43.0`). Sob uma ação `TX_POWER`, s_p = P_TX/P_ref.
- **Por símbolo:** um símbolo com transmissão DL consome P3 + A·Δ + (1 − A)·Δ·s_f·s_p, com Δ = P4 − P3. Um símbolo sem transmissão, numa célula ativa, consome P3 (micro sleep). Como a expressão é afim em s_f·s_p, a soma na janela usa só os contadores:

  E_k = (T_slot/N_sym)·[ S_tx·(P3 + A·Δ) + (1 − A)·Δ·X + (N_slot·N_sym − S_tx)·P3 ],

  com S_tx = `data_sym` + `ctrl_sym` e:
  - no modo `bw`: X = `reg_ptx_mw` ÷ (`avail_rb` × P_ref[mW]);
  - no modo `used`: X = `sym_ptx_mw` ÷ P_ref[mW].
- **Sono emulado:** uma célula com `sleep_slots` > 0 consome, nesses slots, o estado mais profundo cujo tempo total de transição é menor que a duração do episódio de sono, conforme o próprio TR exige. Exemplos: Cat. 1, deep sleep (50 ms < 10 s); Cat. 2, light sleep, porque o deep de 10 s não cabe num episódio de 10 s. A energia de transição E_i entra uma vez por episódio. O vazamento (`sleep_data_reg` > 0) não altera a conta, mas é relatado (H13.4).
- **UL:** os cenários são DL; a potência de recepção UL é desprezada, como o TR faz para FDD.
- **Sinais comuns** (SSB, SIB): o 5G-LENA não os modela como ocupação de recursos. A energia da célula ociosa fica, então, no piso de micro sleep (P3). O TR trata a transmissão de SSB e SIB1 como fonte de consumo. É uma subestimação conhecida.
- **Categorias:** a Cat. 1 é a principal; a Cat. 2 entra na robustez (H13.3). O TR dá valores para as duas categorias sem associá-las a um tipo de equipamento. A escolha da Cat. 1 se justifica pelos tempos de transição de 6–50 ms, compatíveis com janelas de conflito de 8–10 s.

### 4.2 Modelo de robustez: EARTH (Auer et al., 2011)

- **Forma:** P_in = N_TRX·(P0 + Δp·P_out) para 0 < P_out ≤ P_max, e P_in = N_TRX·P_sleep para P_out = 0.
- **Parâmetros:**

  | Tipo | N_TRX | P_max (W) | P0 (W) | Δp | P_sleep (W) |
  | :-- | --: | --: | --: | --: | --: |
  | Macro | 6 | 20 | 130 | 4,7 | 75 |
  | Micro | 2 | 6,3 | 56 | 2,6 | 39 |
  | Pico | 2 | 0,13 | 6,8 | 4,0 | 4,3 |

  Os valores são para LTE com 2×10 MHz e MIMO 2×2.
- **Conferência:** feita na Tabela I de uma fonte secundária (arXiv:1901.10021, que os atribui ao relatório EARTH D2.3 e ao artigo de Auer et al.). O artigo original está atrás de *paywall* (IEEE Xplore), **a confirmar na tabela do original antes de citar números**. Os metadados do artigo foram conferidos no Crossref (DOI 10.1109/MWC.2011.6056691).
- **Mapeamento:** cada célula simulada é **um TRX de macro** (N_TRX = 1), porque é setor único com antena única. P_max = 20 W = 43 dBm, exatamente a potência nominal dos cenários.
  - P_out médio da janela: `reg_ptx_mw`/(`avail_rb`·N_sym·N_slot) no modo `bw`; `sym_ptx_mw`/(N_sym·N_slot) no modo `used`.
  - Célula ativa: P0 + Δp·P_out. Célula em sono emulado: P_sleep. Sem energia de transição, porque o EARTH não a define.
- **Unidades:** joules, como Σ_k P_in,k × 0,1 s.
- **Diferença que importa entre os modelos** (derivada dos parâmetros acima): desligar uma célula ociosa economiza 1 − 75/130 = 42 % da energia dela no EARTH, 1 − 1/50 = 98 % no TR Cat. 1/Set 2 e 1 − 1/5 = 80 % no TR Cat. 2/Set 2. Um teto de PRB economiza parcelas parecidas nos dois modelos (seção 2.3). Logo, comparações entre "desligar célula" e "limitar PRB", centrais no GreenRAN, dependem do modelo. É por isso que existe a H13.3.

### 4.3 Parâmetros versionados

`simulations/ns3/energy/energy_models.json` (novo):

- os parâmetros das Tabelas 5.1-1 a 5.1-5, os valores de A, η e P_static, o mapeamento de Set por banda e a tabela do EARTH;
- para cada valor, a fonte (documento, tabela e versão);
- o sha256 do arquivo, gravado no relatório de análise.

Mudar um parâmetro é um commit com motivo, como na curva de calibração da Fase 2 (`cardl/marl/calibration.py`, `EXPECTED_SHA256`).

## 5. Métrica de energia e integração na análise

### 5.1 Métricas por execução (janela de conflito do catálogo, t0 < t ≤ t1, a mesma convenção de `window_stats`)

| Métrica | Definição | Unidade |
| :-- | :-- | :-- |
| `energy_conflict_tr1` | Σ células Σ janelas E_k, TR Cat. 1 | u.r.·s |
| `energy_conflict_tr2` | idem, TR Cat. 2 | u.r.·s |
| `energy_conflict_j` | Σ células Σ janelas P_in·0,1 s, EARTH | J |
| `energy_conflict_fullload_s` | `energy_conflict_tr1` ÷ P4 do Set: segundos equivalentes de célula a plena carga, para leitura | s |
| `bits_conflict` | 8 × Σ `rx_bytes` de `rdl_kpi_timeseries.csv` na janela (entregues à aplicação) | bit |
| `energy_per_bit_j` | `energy_conflict_j` ÷ `bits_conflict`; `None` se `bits_conflict` = 0 | J/bit (relatado em µJ/bit) |
| `energy_per_mbit_tr1` | `energy_conflict_tr1` ÷ (`bits_conflict`/10⁶) | u.r.·s/Mbit |
| `prb_occupancy_conflict` | Σ `data_reg` ÷ Σ(`avail_rb`·`sym_per_slot`·`slots`), por célula ativa | 0–1 |
| `sleep_time_s` | Σ `sleep_slots`·`slot_s` | s |
| `sleep_leak_reg` | Σ `sleep_data_reg` | REG |
| `ul_share` | Σ `ul_tb_bytes` ÷ Σ(`ul_tb_bytes` + `dl_tb_bytes`) | 0–1 |

A comparação entre baselines é pareada por semente:

- ΔE = E(B3) − E(Bx) nos três modelos;
- economia = 1 − E(B3)/E(B0), em %, a métrica do TR;
- Δ(J/bit).

### 5.2 Mudanças em `scripts/certification/analyze_conflict_runs.py`

- Novo módulo `scripts/certification/energy_model.py`:
  - dataclasses `Tr38864Model(category, set_by_bandwidth, A, eta, static_factor)` e `EarthModel(...)`;
  - `load_models(path)`, que confere o sha256;
  - `energy_window(cell_rows, model, t0, t1, sleep_episodes)`.
- `analyze_run()`:
  - se `raw/rdl_cell_state.csv` existir, calcula as métricas da tabela 5.1;
  - se não existir, devolve `None` nessas chaves. As execuções antigas continuam no relatório, com "—" nas colunas de energia;
  - os episódios de sono saem do `rdl_actuation_log.csv` (`CELL_STATE` `APPLIED`), cruzados com `sleep_slots`.
- `METRICS` ganha as colunas da tabela 5.1. `render()` ganha uma tabela de energia separada, por cenário × baseline e por modelo, com o modelo e o sha256 dos parâmetros no cabeçalho.
- O JSON do relatório inclui `energy_models_sha256` e `power_alloc` por execução.
- **Testes de unidade:**
  - célula ociosa a vida toda dá N_slot·T_slot·P3;
  - célula em sono dá P1 mais uma vez E1;
  - modo `used` dá a mesma energia com teto de 30 % e de 100 % quando todos os símbolos transmitem;
  - linhas sem `rdl_cell_state.csv` dão `None`.
- O nível 0, só com o log de atuação (o proxy atual do artigo: cota de PRB comandada e células ligadas), fica como coluna `energy_proxy_commanded`. Ele serve **só** para as campanhas sem instrumentação, rotulado como proxy.

## 6. O que continua modelo, e como o GR4 fecha isso

### 6.1 O que é medição no simulador e o que é modelo

| Grandeza | Situação depois deste desenho |
| :-- | :-- |
| Ocupação de RB e símbolos, por slot e célula | **medida no simulador** (traço do PHY) |
| Potência de TX configurada e radiada (modo `bw`) | **medida no simulador** (atributo do PHY e contadores) |
| UEs conectados e escalonados | **medidos no simulador** |
| Vazamento em sono emulado | **medido no simulador** |
| Consumo da estação (W, J, u.r.) | **modelo** (TR 38.864 e EARTH), com parâmetros publicados, não do equipamento |
| Sono real da célula, tempos e energia de transição | **modelo** (Tab. 5.1-4 e 5.1-5 do TR); no simulador, o sono é potência de −30 dBm |
| Consumo de CU/DU, transporte e refrigeração | **fora do modelo** |

O texto dos artigos troca então "energia aproximada por PRBs ativos" por "energia estimada pelo modelo do 3GPP TR 38.864 a partir da ocupação de recursos medida no simulador". Não se escreve "energia medida".

### 6.2 Gate GR4 (testbed, `docs/12` §6, item 6)

O GR4 só fecha com medição física. Desenho do gate, a pré-registrar com o laboratório:

1. **Medidor:** potência AC em linha em cada elemento que a decisão afeta (RU/SDR, servidor do DU/CU), com registro ≥ 1 Hz e exatidão declarada pelo fabricante. No servidor, também a energia de CPU por RAPL, quando houver. As séries vão para `raw/` da execução, com hash, pela mesma cadeia de certificação, e são sincronizadas por NTP com o relógio da xApp.
2. **Ocupação de PRB pelo E2:** medida KPM de uso de PRB DL do 3GPP TS 28.552 (`RRU.PrbUsedDl`, a confirmar na especificação e no perfil TB0 de cada agente E2). As medidas PEE (`PEE.AvgPower`, `PEE.Energy`) do TS 28.552 também ficam a confirmar na especificação e no suporte do agente. Os perfis srsRAN e OAI têm 14 e 15 campos pendentes (`docs/12`), e o TB0 não passa com pendência.
   - **Cuidado já documentado:** no NORI, o `RRU.PrbUsedDl` do nó passou dos PRBs disponíveis (225 de 139 a 100 Mb/s), e o `DRB.UEThpDl` sai sempre 0 (`docs/06` §5.4).
   - O GR4 confere, então, o uso de PRB do KPM contra o log do escalonador do agente antes de usá-lo no modelo. Se não bater, a ocupação vem do log do escalonador.
3. **Calibração do modelo para o equipamento** (o mesmo padrão da curva teto → vazão da Fase 2):
   - medir o consumo ocioso, a plena carga e em 3–5 níveis de teto de PRB;
   - ajustar P_static e a inclinação por mínimos quadrados;
   - fixar o arquivo de parâmetros do laboratório com sha256.
4. **Critério do GR4**, em execuções que não entraram no ajuste:
   - (a) a energia por janela prevista pelo modelo calibrado, a partir da ocupação medida por KPM, fica dentro de ±10 % da medida em ≥ 90 % das janelas;
   - (b) o sinal da diferença pareada B3 − B0 na energia medida coincide com o previsto em ≥ 4 de 5 pares.
5. **Limite que o testbed não resolve:** num testbed com SDR, a RU tem consumo quase estático e o DU em CPU domina. O GR4 valida a cadeia instrumentação → modelo → métrica e o sinal das decisões **naquele equipamento**, não os watts de uma macro. O desligamento de célula também depende de o agente expor um canal de desligamento ("canais de potência e desligamento" do perfil, pendentes).

## 7. Convivência com o docs/16 (malha fechada), que também altera `rdl-nr-common.h`

O docs/16 (§3.1, etapa E1) prevê ampliar o `RdlKpiSampler` com "uso de PRB, UEs conectados, estado (ligada, desligada) e potência" por célula, e criar o `RdlKpmExporter` e o modo `--control-socket`. Esses campos por célula são exatamente os deste desenho. Regras para as duas mudanças não colidirem:

1. **Uma fonte por grandeza.** O `RdlCellEnergySampler` é o único consumidor de `SlotDataStats`, `SlotCtrlStats`, `DlScheduling` e `UlScheduling`. O exportador do docs/16 lê `Cumulative(cellId)` e `ConnectedUes(cellId)` e calcula as diferenças da janela de decisão (0,2 s) por conta própria. Como os contadores são cumulativos, as duas cadências (0,1 s do CSV e 0,2 s do KPM) não interferem.
2. **Estado da célula:** a única fonte é `RdlActuation::IsSleeping`. O modo em passo travado do docs/16 reutiliza o `RdlActuation::Apply` atual, então o estado continua coerente.
3. **Fechamento da janela:** com `ownTimer = true` (modo cronograma), o sampler agenda o próprio `CloseWindow()`. No passo travado, o exportador do docs/16 pode chamar `CloseWindow()` na barreira, desde que o sampler seja criado com `ownTimer = false`. Nunca há dois temporizadores.
4. **Formato:** o `rdl_kpi_timeseries.csv` não muda de cabeçalho nos dois desenhos. O que for por UE ou por fatia (docs/16) vai para arquivos novos.
5. **Ordem:** este desenho entra primeiro, como etapa "E1a" do docs/16. O exportador consome a classe pronta, e o gate H13.0 (instrumentação neutra) vale também para o E1 do docs/16.
6. **Código:** um bloco delimitado (`// ---- Energia (docs/17) ----`) logo depois do `RdlKpiSampler`; o exportador do docs/16 vem depois dele. Cada mudança é um commit próprio, com o pré-registro que a usa, nunca durante campanha. O sha256 do `rdl-nr-common.h` no manifesto separa as execuções de cada versão.
7. **Conflito de sementes (achado ao ler o docs/16):** o rascunho do pré-registro 11 (docs/16 §9) usa as sementes 12001–12005, que o pré-registro 09 já usou (`experiments/runs/nr_{S2,S13,S15}_{B3,B3A}_seed12001..12005`). Sugestão: 16001–16005, livres em `experiments/runs/`.

## 8. Lista de correções (divergências achadas ao escrever este desenho)

| # | Onde | Divergência | Proposta |
| :-: | :-- | :-- | :-- |
| C17.1 | `src/core/reasoning.py` (`P_SLEEP_W = 4.3`, com `P0_W = 130.0` e `DELTA_P = 4.7`) | 4,3 W é o P_sleep da **pico** no EARTH; 130 W e 4,7 são da **macro**, cujo P_sleep é 75 W. Assim, s_energia(`CELL_STATE` = 0) = 1 − 4,3/130 = 0,967, em vez de 1 − 75/130 = 0,423. O sono pesa mais do que o próprio modelo citado indica. `N_TRX = 4` difere do 6 da macro (sem efeito, porque o escore é normalizado) | corrigir para o par coerente (macro) ou derivar do modelo do TR. Muda decisões do EEVS (G2, S9, S13): conferir no cronograma, sem ns-3, e pré-registrar antes de qualquer campanha |
| C17.2 | docstring de `Reasoning` | promete "Capacidade de Shannon com SINR real" e "Fila M/G/1 com curva sigmoide"; o código usa tabelas fixas (s_vazão = v/100, s_SLA por faixa de prioridade). O `docs/02` §4 descreve o código corretamente | corrigir a docstring |
| C17.3 | `rdl_kpi_timeseries.csv` (`RdlKpiSampler::Flush`) | só escreve células com pacotes na janela | documentar no `docs/03` e no cabeçalho; análises por célula não podem supor todas as células presentes |
| C17.4 | `rdl-nr-common.h` e `docs/03` | o modo de alocação de potência (`UniformPowerAllocUsed`, padrão) não está documentado; ele concentra a potência nos RBs usados (+5,2 dB por RB com teto de 30 %) | documentar; tratar como ameaça à validade nos artigos que usam teto de PRB no ns-3 (G1, S12) até a H13.6 quantificar |
| C17.5 | artigo SBRC, Limitações | "energia aproximada por PRBs ativos e células ligadas" | depois do pré-registro 12, trocar pelo texto da seção 6.1 e manter "não medida" até o GR4 |
| C17.6 | Fase 2 (`artigos/scripts/insights_complemento.py`, linha 9: `energy_ratio = min(100, teto_crit + teto_embb)/100`) | o "PRB ativo" da CA-RDL é a soma dos tetos, não a ocupação | no artigo da Fase 2, chamar de "soma dos tetos de PRB (proxy)" |

## 9. Referências novas (não inseridas no `references.bib`)

Marcadas **NOVA**. Metadados conferidos: o TR no próprio documento; o artigo do EARTH no Crossref. Os valores do EARTH ainda precisam ser conferidos na tabela do original.

```bibtex
% NOVA - conferida no documento original (38864-i10.docx, cabeçalho "3GPP TR 38.864 V18.1.0 (2023-03)")
@techreport{3gpp_tr38864,
  author      = {{3GPP}},
  title       = {Study on network energy savings for {NR} ({Release} 18)},
  institution = {3rd Generation Partnership Project (3GPP), Technical Specification Group Radio Access Network},
  type        = {Technical Report},
  number      = {TR 38.864},
  note        = {Version 18.1.0},
  year        = {2023},
  month       = mar,
  url         = {https://www.3gpp.org/ftp/Specs/archive/38_series/38.864/38864-i10.zip}
}

% NOVA - metadados do Crossref (DOI 10.1109/MWC.2011.6056691); valores da tabela de parâmetros a conferir no original
@article{auer2011earth,
  author  = {Auer, Gunther and Giannini, Vito and Desset, Claude and G{\'o}dor, Istv{\'a}n and
             Skillermark, Per and Olsson, Magnus and Imran, Muhammad Ali and Sabella, Dario and
             Gonzalez, Manuel J. and Blume, Oliver and Fehske, Albrecht},
  title   = {How Much Energy Is Needed to Run a Wireless Network?},
  journal = {IEEE Wireless Communications},
  volume  = {18},
  number  = {5},
  pages   = {40--49},
  year    = {2011},
  month   = oct,
  doi     = {10.1109/MWC.2011.6056691}
}
```

Grafias divergentes entre fontes (Crossref "Oliver Blume" e "Muhammad Imran"; repositório do imec "Olivier" e "Muhammad Ali"): conferir na página do artigo antes de submeter.

## 10. Etapas

| Etapa | Entrega | Gate |
| :-- | :-- | :-- |
| EN0 | campanha 10 concluída e analisada; nenhum commit antes | — |
| EN1 | `RdlCellEnergySampler`, `IsSleeping`, `--powerAllocation` e repasse de `--sim-arg` no executor de campanha | compila; H13.0 (instrumentação neutra) |
| EN2 | `energy_model.py`, `energy_models.json` e colunas em `analyze_conflict_runs.py`; testes de unidade | testes verdes; execuções antigas analisadas sem mudança nas colunas existentes |
| EN3 | piloto: G1 e G2 × B0 e B3 × semente 9103, modo `bw` (não confirmatório) | todas as colunas preenchidas; H13.4 e H13.5 avaliáveis; duração medida |
| EN4 | pré-registro 12 fechado e commitado antes da campanha | seção 11 |
| EN5 | campanha e análise; artigos atualizados só pelos scripts | — |

## 11. Rascunho do pré-registro 12 (não registrado)

Formato dos pré-registros 08–10. É fechado e commitado depois do piloto (EN3) e antes da campanha.

### 1. Objetivo

Estimar a energia que cada baseline gasta na janela de conflito dos cenários com ações de energia, com o modelo de potência do 3GPP TR 38.864 aplicado à ocupação de recursos medida no ns-3. Verificar se o sinal das diferenças se mantém num segundo modelo (EARTH).

### 2. Estado do código

- O commit deste pré-registro, o mesmo da execução, com `RdlCellEnergySampler`, `--powerAllocation`, `energy_model.py` e `energy_models.json` (sha256 citado aqui).
- O B3 usa a agregação do EEVS que for o padrão nesse commit (`mean` ou `additive`, conforme o merge de `eevs-aditivo-padrao`), declarada aqui.

### 3. Desenho

- **Cenários:** G1, G2, S9, S10, S12, S13 e S15, os que têm proposta de `energy_saving` no catálogo. S11 e S14 ficam fora: não têm ação de energia.
- **Baselines:** B0, B1, B2 e B3.
- **Modo de potência:** `--powerAllocation=bw` em todas as execuções. Somente no G1, também `used` (H13.6).
- **Sementes:** **13001 a 13005**, nunca rodadas (conferido em `experiments/runs/` em 2026-11-12), as mesmas para todos os baselines.
- **Execuções:** 7 × 4 × 5 = 140, mais 20 do G1 em `used`, num total de 160.
- **Duração estimada:** pelas estimativas do pré-registro 10 (S12 ≈ 37 min, S10 e S13 ≈ 25 min, G1 ≈ 6,5 min, S9, S15 e G2 < 2 min por execução), cerca de 35 h de CPU, ou cerca de 18 h de relógio com 2 em paralelo. O piloto corrige a estimativa, porque o modo `bw` muda a carga da PHY.
- **Comandos** (Ubuntu do WSL, em primeiro plano, no painel Terminal):

  ```bash
  bash scripts/run_native_campaign.sh --scenarios "G1 G2 S9 S10 S12 S13 S15" --baselines "B0 B1 B2 B3" \
    --seeds 13001-13005 --jobs 2 --sim-arg "--powerAllocation=bw"
  bash scripts/run_native_campaign.sh --scenarios "G1" --baselines "B0 B1 B2 B3" \
    --seeds 13001-13005 --jobs 2 --sim-arg "--powerAllocation=used" --run-suffix U
  ```

  `--sim-arg` e `--run-suffix` são opções novas do executor (etapa EN1). O sufixo evita colisão de `run_id` entre os dois modos (por exemplo `nr_G1_B3U_seed13001`; o padrão `B\d[A-Z]?` do analisador aceita).

### 4. Hipóteses e critérios

Comparação pareada por semente, na janela de conflito do catálogo. Modelo principal: TR 38.864 Cat. 1; robustez: Cat. 2 e EARTH.

| Hipótese | Cenário | Critério |
| :-- | :-- | :-- |
| H13.0 (gate, antes da campanha) | G1/B3 e S13/B0, semente 11001, modo `used` | `rdl_kpi_timeseries.csv` e `rdl_actuation_log.csv` com sha256 idêntico ao das execuções da campanha 10. Se falhar, a instrumentação não é neutra e a campanha não começa |
| H13.1a | G1 | `energy_conflict_tr1` do B3 ≥ a do B0 em ≥ 4/5 sementes. Justificativa: o B3 aplica o teto de 80 % do RANSlicer, e o B0 fica a maior parte de cada segundo no teto de 30 % do EnergySaver (cronograma da semente 9101: 20 ações aplicadas no B0, 9 no B3) |
| H13.1b | G1 | `energy_per_bit_j` e `energy_per_mbit_tr1` do B3 < as do B0 em ≥ 4/5 sementes. Justificativa: o consumo estático domina, e o B3 entrega mais bits (semente 9101: 30,30 contra 23,30 Mb/s, `p3_exploratorio_semente_unica.csv`) |
| H13.2a | G2 | `energy_conflict_tr1` do B0 (desliga as duas RUs) < a do B3 em ≥ 4/5 sementes |
| H13.2b | G2 | `energy_per_mbit_tr1` do B3 < a do B0 em ≥ 4/5 sementes (o B0 perde a cobertura; com `bits_conflict` = 0, o B0 conta como pior) |
| H13.3 (robustez entre modelos) | todos | o sinal de ΔE(B3 − B0) é o mesmo em TR Cat. 1, TR Cat. 2 e EARTH em ≥ 90 % dos pares (cenário, semente). Cenário em que isso falhar terá a conclusão de energia declarada dependente do modelo |
| H13.4 (consistência do sono emulado) | execuções com `CELL_STATE` = 0 aplicado | `sleep_leak_reg` ≤ 1 % dos REG da mesma célula no segundo anterior ao sono. Se falhar, a energia de sono daquela execução é relatada como limite inferior |
| H13.5 (UL desprezível) | todas | `ul_share` ≤ 1 % na janela de conflito. Se falhar, a ocupação é relatada como limite superior (DL + UL) |
| H13.6 (artefato da alocação de potência) | G1, `bw` × `used` | sem direção: diferença pareada de `thp_conflict` (B3 − B0) entre os modos, com IC 95 %. Quantifica quanto o modo `used` atenua a perda de vazão do teto de 30 % |

- **Descritivo, em todos os cenários e modelos:** `energy_conflict_*`, economia contra o B0 (%), `energy_per_bit_j`, `prb_occupancy_conflict`, `sleep_time_s`, `thp_conflict` e `delay_conflict_ms`, com IC 95 % e diferenças pareadas B3 − Bx.
- **Sem comparação de vazão com a campanha 10:** o modo `bw` muda o rádio. As vazões deste pré-registro são de outra configuração e não substituem as da campanha 10.

### 5. Regras de relato

- Execução com falha do ns-3 é repetida uma vez com a mesma semente (`--retry-failed`). Se falhar de novo, entra como falha.
- Interrupção (desligamento, falta de disco ou de memória): retomada com o mesmo comando; execuções incompletas são refeitas desde o início.
- A energia é sempre chamada de "estimada pelo modelo X a partir da ocupação medida no simulador", nunca de "medida".
- `energy_models.json` não muda depois do registro. Uma correção de parâmetro vira reanálise declarada como desvio, com as duas versões relatadas.
- Nada fixado aqui é alterado depois de ver os dados.

## 12. Fontes

- Código: `simulations/ns3/rdl-nr-common.h`, `simulations/ns3/scenario_rdl_multicell.cc`, `scripts/certification/analyze_conflict_runs.py`, `scripts/certification/run_ns3_certified.sh`, `src/core/reasoning.py`.
- 5G-LENA v5.1 instalado (`~/ns3-oran-workspace/ns-3-oran/contrib/nr`): `model/nr-gnb-phy.{h,cc}`, `model/nr-phy.h`, `model/nr-gnb-mac.{h,cc}`, `helper/nr-spectrum-value-helper.cc`.
- Execuções: `experiments/runs/nr_G1_B3_seed9101/` (formato dos arquivos), manifestos `nr_*_seed1100[1-5]` (durações parciais da campanha 10) e listagem das sementes usadas em `experiments/runs/`.
- Dados dos artigos: `artigos/dados/insights/p3_exploratorio_semente_unica.csv`.
- 3GPP TR 38.864 V18.1.0, cláusula 5.1 (texto conferido no documento do arquivo público do 3GPP).
- EARTH: Auer et al. (2011); valores conferidos na Tabela I de arXiv:1901.10021, a confirmar no original.
