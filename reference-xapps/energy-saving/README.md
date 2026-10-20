# Energy Saving Reference xApp (Orange / FlexRIC — GreenRAN Edition)

## Referência Científica e Projeto Base
* **Repositório Oficial Upstream:** [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric)
* **Aplicação Original:** `xapp_es_with_cell_util` (Energy Saving under Cell Utilization, Wadud et al., 2024)
* **Ambiente Original:** Near-RT RIC FlexRIC / Simulação ns-3 / O-RAN SC E2.
* **Programa Estratégico:** **Projeto GreenRAN** (*Open RAN Sustentável para o Agro e Campi Inteligentes* / OpenRAN@Brasil - UFPA / RNP / MCTI).

---

## Adequações ao Projeto GreenRAN (UFPA / Agro 4.0 & Smart Campus)

A versão original da literatura aplicava corte cego de potência (`TX_POWER: 20 dBm`) ou desligamento abrupto de células sem ciência das fatias em operação ou da topologia do canal de propagação. Para o **GreenRAN**, foram introduzidas as seguintes capacidades:

1. **Consciência de Fontes Renováveis e Bateria (*State-of-Charge* - SoC):**
   * Em nós remotos de fazendas experimentais (Agro 4.0 / Embrapa), a xApp monitora o nível de bateria (`battery_soc_ratio`) e a geração solar instantânea (`solar_power_watts`).
   * Quando $\text{SoC} < 35\%$ e a insolação for nula (noite/chuva), entra em modo de contingência ecológica severa.
2. **Proteção de Cobertura Rural (*Rural Coverage Guard*):**
   * Impede que a atenuação de potência crie buracos de cobertura (*coverage holes*) em enlaces com alto *path loss*, protegendo a conectividade de tratores e sensores distantes. O piso de potência é limitado respeitando o pior SINR de borda.
3. **Respeito aos Limites Físicos COTS do Testbed GreenRAN:**
   * Limita a potência máxima a $23\text{ dBm}$ (200 mW) para operação segura sobre as USRPs N310 / B210 no laboratório e ilha UFPA, evitando sobrecarga ou queima de front-ends de RF.
4. **Modos Granulares de Economia de Energia:**
   * `TX_POWER_REDUCTION`: Ajuste fino e contínuo de ganho de transmissão.
   * `MICRO_SLEEP_AND_THROTTLING`: Desativação rápida de símbolos OFDM em slots vazios (3GPP Rel-18), mantendo canais de sincronismo e radiodifusão (SSB).
   * `CARRIER_MICRO_SLEEP`: Desativação de portadoras secundárias de agregação (CA) durante a madrugada no Campus universitário.
5. **Salvaguarda de SLA para Fatias Críticas:**
   * Emite a flag `prohibit_urllc_degradation: true`, instruindo a H-RDL a vetar qualquer economia de energia que degrade a latência do maquinário autônomo.

---

## Interface de Interceptação H-RDL / GreenRAN

* **MsgType:** `RDL_ACTION_PROPOSAL` (30000 / 20010)
* **Estrutura do Payload Emitido:**
```json
{
  "xapp_id": "energy_saving_orange",
  "node_id": "gnb_01",
  "parameter": "TX_POWER",
  "value": 21.0,
  "priority": 65,
  "greenran_env": "AGRO_RURAL_OFFGRID",
  "action_strategy": "MODERATE_POWER_SCALING",
  "energy_target_kwh": 0.28,
  "telemetry_context": {
    "battery_soc_ratio": 0.75,
    "solar_power_watts": 120.0,
    "rural_coverage_guard_active": true,
    "prohibit_urllc_degradation": true
  },
  "timestamp": 1729427400.456
}
```

---

## Variáveis de Ambiente e Configuração

| Variável | Padrão | Descrição |
| :--- | :---: | :--- |
| `GREENRAN_ENV` | `AGRO_RURAL_OFFGRID` | Ambiente de operação: `AGRO_RURAL_OFFGRID` ou `CAMPUS_SMART_GRID`. |
| `BATTERY_SOC_PERCENT` | `75.0` | Nível inicial de carga da bateria (0 a 100%). |
| `SOLAR_PANEL_CONNECTED` | `true` | Indica presença de sistema fotovoltaico conectado. |
| `SOLAR_POWER_WATTS` | `120.0` | Geração solar instantânea simulada ou reportada (W). |
| `RURAL_COVERAGE_GUARD` | `true` | Ativa a trava de segurança de cobertura mínima para áreas rurais. |
| `MAX_ALLOWED_TX_POWER` | `23.0` | Limite superior de segurança em dBm (bancada USRP indoor). |
| `HTTP_PORT` | `8084` | Porta da API REST FastAPI (`/health`, `/ready`, `/metrics`). |
| `METRICS_PORT` | `8085` | Porta de telemetria Prometheus. |

---

## Endpoints HTTP e Métricas Prometheus

* **Liveness:** `GET :8084/health` (retorna status, ambiente GreenRAN, SoC e geração solar).
* **Readiness:** `GET :8084/ready`
* **Última Proposta:** `GET :8084/proposals/latest`
* **Prometheus:** `GET :8084/metrics`
  * `es_proposals_total`: Contador categorizado por estratégia, nó e ambiente GreenRAN.
  * `es_tx_power_target_dbm`: Potência de transmissão alvo solicitada.
  * `es_battery_soc_ratio`: Nível de carga da bateria do nó remoto off-grid.
  * `es_solar_power_watts`: Potência solar instantânea.
  * `es_estimated_energy_saved_ratio`: Economia percentual estimada de energia.
