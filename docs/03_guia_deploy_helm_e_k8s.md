# Volume 03: Guia de Deploy do Near-RT RIC, das 3 Reference xApps e da xApp RDL (Helm & K8s)

> **Navegação Sequencial:** [Vol 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md) -> [Vol 02: Infraestrutura & Rancher](02_infraestrutura_cluster_k3d_e_rancher.md) -> **[Vol 03: Deploy & Observabilidade Kiali]** -> [Vol 04: Testes, ns-3 & Benchmarks](04_testes_simulacao_ns3_e_benchmarks.md) -> [Vol 05: Conformidade O-RAN](05_relatorios_conformidade_e_governanca.md) -> [Vol 06: Operação & Troubleshooting](06_operacao_troubleshooting_e_backup.md)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Escopo:** Sequência de Deploy Near-RT RIC (`ricplt`), Implantação das 3 Reference xApps (`xSlice`, `Energy Saving`, `Traffic Steering`) no `ricxapp`, Modos Baseline vs Governança e Validação de Observabilidade  
**Data de Consolidação:** 28/08/2026  

---

## 1. Visão Geral da Arquitetura de Implantação

O pipeline de implantação orquestra os componentes em dois namespaces isolados com dependência estrita de ordem:

```mermaid
flowchart TD
    subgraph STAGE1["Etapa 1: Infraestrutura Near-RT RIC (Namespace: ricplt)"]
        REDIS["Redis DBAAS (:6379)<br/>Shared Data Layer"]
        E2TERM["E2Term SCTP/RMR (:36422 / :38000)"]
        SUBMGR["Subscription Manager (:4560)"]
    end

    subgraph STAGE2["Etapa 2: Workloads Concorrentes (Namespace: ricxapp)"]
        XSLICE["1. xSlice QoS xApp<br/>(peihaoY/xslice-oran)<br/>HTTP :8082 | Metrics :8083"]
        ES["2. Energy Saving xApp<br/>(Orange-OpenSource/ns-O-RAN-flexric)<br/>HTTP :8084 | Metrics :8085"]
        TS["3. Traffic Steering xApp<br/>(o-ran-sc/ric-app-ts)<br/>HTTP :8086 | Metrics :8087"]
    end

    subgraph STAGE3["Etapa 3: Arbitragem & Governança (Namespace: ricxapp)"]
        RDL["4. xApp RDL (Fase 1: H-RDL)<br/>Arbitrador TVS/EEVS & Safety Guards<br/>HTTP :8080 | Metrics :8081 | RMR :4560"]
    end

    STAGE1 -->|Plataforma Pronta| STAGE2
    STAGE2 -.->|Modo Baseline (Sem RDL)| NS3_BASELINE["Conflitos Diretos na RAN (Sem Governança)"]
    STAGE2 -->|Modo Governança (Com RDL)| STAGE3
    STAGE3 -->|Decisões Arbitradas E2SM-RC| E2TERM
```

---

## 2. As 3 Reference xApps da Literatura Integradas

| xApp | Projeto Base / Repositório | Porta HTTP / Métricas | Parâmetro Emitido (`RDL_ACTION_PROPOSAL`) |
| :--- | :--- | :---: | :--- |
| **1. xSlice (QoS & Slicing)** | [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran) | `:8082` / `:8083` | `PRB_QUOTA = 80%` (Prioridade: 90 / Fatias URLLC) |
| **2. Energy Saving (ES)** | [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) | `:8084` / `:8085` | `TX_POWER = 20 dBm` (Prioridade: 65 / Green RAN) |
| **3. Traffic Steering (TS)** | [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts) | `:8086` / `:8087` | `HANDOVER = UE-07 -> gNB-02` (Prioridade: 80) |

---

## 3. Deploy via Helm (Padrão O-RAN)


### 3.1. Modo Baseline (Near-RT RIC + 3 Reference xApps SEM RDL)
Implanta a plataforma Near-RT RIC e as 3 xApps concorrentes isoladas, sem o arbitrador RDL, para fins de coleta de dados de referência e validação de conflitos:
```bash
make helm-deploy-baseline
```
### 3.2. Modo Governança Completa (Near-RT RIC + 3 Reference xApps + RDL)
Implanta a plataforma Near-RT RIC, as 3 xApps concorrentes e a camada de arbitragem RDL:
```bash
make helm-deploy
```
---

## 4. Deploy Kubernetes Puro / Kustomize

### 4.1. Modo Baseline (Sem RDL):
```bash
make k8s-deploy-baseline
```

### 4.2. Modo Governança (Com RDL):
```bash
make k8s-deploy
```
---

## 5. Validação Automatizada e Smoke Test (`make test-3xapps`)

O repositório disponibiliza um verificador em tempo real que abre conexões e valida a saúde e as métricas Prometheus de todas as xApps ativas:

```bash
make test-3xapps
# Ou diretamente:
bash scripts/verify_3_xapps.sh
```

**Saída Esperada no Terminal:**
```text
======================================================================
   Validação e Smoke Test das xApps O-RAN no namespace 'ricxapp'
======================================================================

[1/4] Listando Pods em execucao no namespace ricxapp...
NAME                                       READY   STATUS    RESTARTS   AGE
ricxapp-qos-xslice-5c49d8c977-ab12         1/1     Running   0          45s
ricxapp-energy-saving-6d8b9487c-ef34       1/1     Running   0          45s
ricxapp-traffic-steering-747d95b5cb-xy56   1/1     Running   0          45s
ricxapp-iqos-xapp-rdl-84cfbb996b-zw78      1/1     Running   0          40s

[2/4] Validando 1. xSlice QoS xApp (peihaoY/xslice-oran)...
  -> Healthcheck /health: {"status":"UP","xapp":"xslice_oran","role":"QoS_Slicing"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"xslice_oran","parameter":"PRB_QUOTA","value":80.0,"priority":90}
  -> Metricas Prometheus: xslice_proposals_total 12.0

[3/4] Validando 2. Energy Saving xApp (Orange-OpenSource/ns-O-RAN-flexric)...
  -> Healthcheck /health: {"status":"UP","xapp":"energy_saving_orange","role":"Energy_Saving"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"energy_saving_orange","parameter":"TX_POWER","value":20.0,"priority":65}
  -> Metricas Prometheus: es_proposals_total 10.0

[4/4] Validando 3. Traffic Steering xApp (o-ran-sc/ric-app-ts)...
  -> Healthcheck /health: {"status":"UP","xapp":"traffic_steering_oransc","role":"Traffic_Steering"}
  -> Proposta Recente /proposals/latest: {"xapp_id":"traffic_steering_oransc","parameter":"HANDOVER","priority":80}
  -> Metricas Prometheus: ts_proposals_total 8.0

[EXTRA] Validando 4. xApp RDL (Resource and Decision Layer - Fase 1)...
  -> Healthcheck /health: {"status":"UP","ready":true}
  -> Metricas Prometheus: rdl_decisions_total 30.0

======================================================================
   Verificação Concluída com SUCESSO!
======================================================================
```

---

## 6. Observabilidade Service Mesh (Kiali & Rancher)

```bash
# Instalar Service Mesh Istio e Dashboard Kiali:
make kiali-install

# Abrir painel Kiali (http://localhost:20001/kiali):
make kiali-dashboard

# Iniciar gerador de tráfego para visualizar grafo animado:
make start-traffic
```

---

-> **[Volume 04: Testes, Simulação no ns-3 NORI e Benchmarks](04_testes_simulacao_ns3_e_benchmarks.md)**
