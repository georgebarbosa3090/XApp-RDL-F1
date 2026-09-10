# Fontes Normativas e Especificações de Referência — XApp-RDL-F1

**Projeto:** xApp RDL (Resource and Decision Layer) — Near-RT RIC (O-RAN)  
**Data de Atualização:** 10 de Setembro de 2026  

---

## 1. O-RAN ALLIANCE — Especificações Normativas Primárias

1. **O-RAN.WG3.E2GAP-v03.00:** *Near-Real-time RAN Intelligent Controller Architecture & E2 General Aspects*.
2. **O-RAN.WG3.E2AP-v02.03 / v03.00:** *E2 Application Protocol (E2AP)* — Protocolo de sinalização e mensagens de procedimento básico (`RICsubscriptionRequest`, `RICindication`, `RICcontrolRequest`, `RICcontrolAcknowledge`, `RICcontrolFailure`, `E2setupRequest`).
3. **O-RAN.WG3.E2SM-KPM-v02.00 / v03.00:** *E2 Service Model for Key Performance Measurements (KPM)* — Estruturação de `IndicationHeader-Format1`, `IndicationMessage-Format1`, `MeasurementInfoList` e métricas 3GPP (`DRB.UEThpDl`, `RRU.PrbUsedDl`, `DRB.RlcSduDelayDl`).
4. **O-RAN.WG3.E2SM-RC-v01.00 / v01.03:** *E2 Service Model for RAN Control (RC)* — Definição de `RIC-ControlHeader-Format1`, `RIC-ControlMessage-Format1`, estilos de controle e parâmetros da RAN (`PRB_QUOTA`, `TX_POWER`, `HANDOVER`).

---

## 2. O-RAN Software Community (O-RAN SC) — Implementação de Referência

1. **ric-plt/xapp-frame-py:** Framework base Python para desenvolvimento de xApps com suporte a RMR, SDL, REST e Health Check.
   - Repositório: `https://github.com/o-ran-sc/ric-plt-xapp-frame-py`
2. **ric-plt/submgr:** Subscription Manager do Near-RT RIC responsável pelo gerenciamento de subscrições E2 e orquestração de rotas RMR para xApps consumidoras de KPM.
   - Repositório: `https://github.com/o-ran-sc/ric-plt-submgr`
3. **ric-app/rc:** Implementação oficial de referência para despacho e emissão de mensagens de controle E2SM-RC.
   - Repositório: `https://github.com/o-ran-sc/ric-app-rc`
4. **ric-plt/e2mgr:** E2 Manager para gerenciamento de inventário e estado de nós E2 (`GET /v1/nodeb/states`, `GET /v1/nodeb/{node}`).
   - Repositório: `https://github.com/o-ran-sc/ric-plt-e2mgr`

---

## 3. NORI & ns-3/5G-LENA — Co-Simulação e Emulação E2

1. **NORI (New Open RAN Interface):** Módulo open-source desenvolvido por consórcio brasileiro (UFPA/UFG/UFRJ) para acoplamento do simulador ns-3 ao Near-RT RIC via interface E2/E2AP real com SCTP.
   - Repositório: `https://github.com/lasseufpa/nori`
2. **5G-LENA (CTTC NR Module):** Módulo de simulação física e de enlace para redes 5G New Radio (Release 16/17) sobre o discrete-event simulator ns-3.48.
   - Documentação: `https://5g-lena.cttc.es/`

---

## 4. OpenRAN@Brasil Blueprint v3 — Infraestrutura e Implantação

1. **Blueprint v3:** Especificação padronizada de orquestração de infraestrutura de nuvem aberta (k3s, k3d, Rancher, Near-RT RIC, xApps e geradores de tráfego) para replicação de testes no contexto nacional.
   - Repositório: `https://github.com/LABORA-INF-UFG/openran-br-blueprint`
   - Wiki: `https://github.com/LABORA-INF-UFG/openran-br-blueprint/wiki/OpenRAN@Brasil-Blueprint-v3`
