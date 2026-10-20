# xSlice Reference xApp (QoS & Slicing Optimizer — GreenRAN Edition)

## Referência Científica e Projeto Base
* **Repositório Oficial Upstream:** [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran)
* **Artigo / Trabalho Base:** *xSlice: Near-Real-Time Resource Slicing for QoS Optimization in 5G O-RAN* (Yan et al., IEEE CAMAD)
* **Ambiente Original:** Near-RT RIC FlexRIC / OAI RAN / Testbed com UEs reais.
* **Programa Estratégico:** **Projeto GreenRAN** (*Open RAN Sustentável para o Agro e Campi Inteligentes* / OpenRAN@Brasil - UFPA / RNP / MCTI).

---

## Adequações ao Projeto GreenRAN (UFPA / Agro 4.0 & Smart Campus)

A versão original da xApp solicitava uma cota fixa de 80% dos PRBs sem consciência da fonte de energia ou da severidade do enlace. Para o **GreenRAN**, foram introduzidas as seguintes capacidades:

1. **Alocação Elástica Orientada a Demanda (*Dynamic Slicing*):**
   * Em vez de reservar rigidamente 80% de PRBs (o que esgotaria desnecessariamente baterias em nós rurais), o módulo calcula a cota dinamicamente a partir do perfil de carga e do cenário ativo.
2. **Suporte a Múltiplos Perfis Heterogêneos de Fatias:**
   * `URLLC_AGRO_CRITICAL`: Maquinário autônomo, colheitadeiras e drones de monitoramento (latência $< 10\text{ ms}$, disponibilidade $> 99.99\%$). Alocação prioritária entre $50\%$ e $85\%$.
   * `MMTC_SOIL_SENSORS`: Telemetria de sensores de solo, umidade e microclima da Amazônia Oriental (Embrapa). Transmissão em rajadas curtas com cota compacta ($15\%$ a $25\%$).
   * `EMBB_CAMPUS`: Tráfego acadêmico do Campus da UFPA (Mirante do Rio, ITEC), seguindo regime circadiano (alta demanda diurna de 08h às 18h, baixa noturna).
3. **Metadados de Consciência Ecológica (*Energy Budget Awareness*):**
   * Emite na proposta JSON os campos `eco_compliant`, `flexibility_ratio` e `recommended_bwp_id` para permitir que o mediador H-RDL reduza a largura de banda ativa (*BWP switching*) quando a carga permitir.
4. **Proteção de Limiar Mínimo de SINR:**
   * Sinaliza ao mediador H-RDL a restrição de SINR mínimo ($SINR_{min} \ge 5\text{ dB}$ para URLLC) para barrar cortes destrutivos de potência da `EnergySaver`.

---

## Interface de Interceptação H-RDL / GreenRAN

* **MsgType:** `RDL_ACTION_PROPOSAL` (30000 / 20010)
* **Estrutura do Payload Emitido:**
```json
{
  "xapp_id": "xslice_oran",
  "node_id": "gnb_01",
  "parameter": "PRB_QUOTA",
  "value": 66.25,
  "priority": 90,
  "slice_type": "URLLC",
  "greenran_profile": "URLLC_AGRO_CRITICAL",
  "energy_budget_awareness": {
    "eco_compliant": true,
    "flexibility_ratio": 0.40,
    "recommended_bwp_id": 0,
    "min_required_sinr_db": 5.0
  },
  "timestamp": 1729427400.123
}
```

---

## Variáveis de Ambiente e Configuração

| Variável | Padrão | Descrição |
| :--- | :---: | :--- |
| `GREENRAN_PROFILE` | `URLLC_AGRO_CRITICAL` | Perfil de operação: `URLLC_AGRO_CRITICAL`, `MMTC_SOIL_SENSORS`, `EMBB_CAMPUS`. |
| `ECO_AWARE_MODE` | `true` | Ativa a emissão de metadados ecológicos para negociação com a H-RDL. |
| `DYNAMIC_SLICING_ENABLED`| `true` | Habilita cálculo dinâmico de PRBs com base em carga em vez de cota estática. |
| `TARGET_NODES` | `gnb_01,gnb_02` | Lista de gNodeBs alvo na topologia. |
| `HTTP_PORT` | `8082` | Porta da API REST FastAPI (`/health`, `/ready`, `/metrics`). |
| `METRICS_PORT` | `8083` | Porta de telemetria Prometheus. |

---

## Endpoints HTTP e Métricas Prometheus

* **Liveness:** `GET :8082/health` (retorna status, perfil GreenRAN e modo eco).
* **Readiness:** `GET :8082/ready`
* **Última Proposta:** `GET :8082/proposals/latest`
* **Prometheus:** `GET :8082/metrics`
  * `xslice_proposals_total`: Contador categorizado por fatia, nó e perfil GreenRAN.
  * `xslice_prb_quota_requested_ratio`: Cota de PRBs solicitada no MAC scheduler.
  * `xslice_sla_satisfaction_ratio`: Índice preditivo de satisfação de SLA.
  * `xslice_eco_saving_compliance_ratio`: Grau de flexibilidade da fatia para modos de economia.
