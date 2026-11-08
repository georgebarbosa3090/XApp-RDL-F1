# Fontes de referência

## 1. O-RAN ALLIANCE (WG3)

| Documento | Uso no projeto |
| :-- | :-- |
| O-RAN.WG3.E2GAP | arquitetura do Near-RT RIC e aspectos gerais do E2 |
| O-RAN.WG3.E2AP v02.03 (alvo da xApp) e v03.01 (NORI) | procedimentos E2 Setup, Subscription, Indication, Control |
| O-RAN.WG3.E2SM-KPM v03.00 | formatos de Event Trigger, Action Definition e Indication |
| O-RAN.WG3.E2SM-RC v01.03 (alvo) e v03.01 (NORI) | Control Header/Message e estilos de controle |

## 2. O-RAN Software Community

| Componente | Repositório | Uso |
| :-- | :-- | :-- |
| xApp framework (Python) | `https://github.com/o-ran-sc/ric-plt-xapp-frame-py` | RMR, SDL, cliente REST de subscrição (versão 3.2.2) |
| Subscription Manager | `https://github.com/o-ran-sc/ric-plt-submgr` | API REST `/ric/v1/subscriptions` |
| E2 Manager | `https://github.com/o-ran-sc/ric-plt-e2mgr` | inventário de nós E2 |
| RMR | `https://github.com/o-ran-sc/ric-plt-lib-rmr` | transporte e MEID |
| RC xApp | `https://github.com/o-ran-sc/ric-app-rc` | referência de controle RC |

## 3. Simulação

| Componente | Repositório | Versão fixada |
| :-- | :-- | :-- |
| ns-3 | `https://gitlab.com/nsnam/ns-3-dev` | 3.48 (nativa), 3.42 (NORI) |
| 5G-LENA | `https://gitlab.com/cttc-lena/nr` | v5.1 (nativa), `78b7179` (NORI) |
| NORI | `https://github.com/lasseufpa/nori` | `8a30867` |
| e2sim | `https://github.com/o-ran-sc/sim-e2-interface` | `da6f82f` |

Commits completos em [`reproducibility/versions.lock`](../../reproducibility/versions.lock).

## 4. Testbed

| Item | Referência |
| :-- | :-- |
| OpenRAN@Brasil Blueprint v3 | `https://github.com/LABORA-INF-UFG/openran-br-blueprint` |
| srsRAN Project | `https://github.com/srsran/srsRAN_Project` |
| Open5GS | `https://github.com/open5gs/open5gs` |
