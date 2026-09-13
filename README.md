# xApp RDL (Resource and Decision Layer) — O-RAN Conflict Mitigation

<div align="center">

**Implementação experimental de uma xApp H-RDL para Near-RT RIC, com suporte em evolução às interfaces E2AP, E2SM-KPM e E2SM-RC.**  
*A interoperabilidade normativa ponta a ponta é validada incrementalmente contra O-RAN ALLIANCE, O-RAN SC (Release J), NORI (5G-LENA v5.1 / ns-3.48) e OpenRAN@Brasil Blueprint v3.*

</div>

---

### Navegação Multi-Fases do Projeto RDL (Resource and Decision Layer)

| Fase do Projeto | Descrição e Paradigma de Controle | Status de Implementação | Repositório Oficial |
| :---: | :--- | :---: | :---: |
| **Fase 1 (Atual)** | **RDL Determinística e Segura (H-RDL)**<br/>*Janela em lote (200ms), heurísticas TVS/EEVS, Safety Guards físicos e mapeamento formal E2AP/E2SM.* | **Implementada e Operacional** | [georgebarbosa3090/XApp-RDL-F1](https://github.com/georgebarbosa3090/XApp-RDL-F1) |
| **Fase 2** | **RDL Baseada em Contexto (CA-RDL)**<br/>*Aprendizado por Reforço Multiagente (MARL / MAPPO) e cognição contextual.* | **Ativa / Em Evolução** | [georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2) |
| **Fase 3** | **RDL Autônoma e Federada 6G (Zero-Touch)**<br/>*Inteligência distribuída, orquestração por intenção (Intent-Driven) e O-Cloud 6G.* | **Roadmap / Planejada** | *Em especificação futura* |

---

## 1. Visão Geral da Arquitetura (Fase 1: H-RDL)

A **xApp RDL (Resource and Decision Layer)** atua como o middleware central de governança no **Near-RT RIC**, interceptando e mitigando colisões geradas por **3 xApps de referência abertas da literatura**:

1. **xSlice (QoS & Slicing Optimizer) — [`peihaoY/xslice-oran`](https://github.com/peihaoY/xslice-oran):** Solicita cotas elevadas de PRBs (`PRB_QUOTA = 80%`, prioridade 90) para fatias URLLC/eMBB.
2. **Energy Saving (Green RAN Optimizer) — [`Orange-OpenSource/ns-O-RAN-flexric`](https://github.com/Orange-OpenSource/ns-O-RAN-flexric):** Solicita redução de potência (`TX_POWER = 20 dBm`, prioridade 65) e sono de células, colidindo com a garantia de QoS.
3. **Traffic Steering (Mobility Optimizer) — [`o-ran-sc/ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts):** Solicita migração e balanceamento de tráfego (`HANDOVER`, prioridade 80).

* **Agente de Percepção (`PerceptionAgent`):** Agrupa propostas de controle E2 em **janelas de decisão em lote ($\Delta t = 200\text{ ms}$)** e identifica conflitos diretos e indiretos entre as 3 xApps.
* **Agente de Raciocínio (`ReasoningAgent`):** Aplica funções de utilidade multiobjetivo fundamentadas em **modelos analíticos calibrados de rádio 5G** (capacidade espectral de Shannon com SINR real e overhead 3GPP, atraso sigmoide de fila $M/G/1$ e modelo linear de consumo elétrico Earth/3GPP).
* **Agente de Refinamento (`RefinementAgent`):** Garante a segurança física da rede (*Safety Guards*), aplicando *clamping* de potência ($P_{\text{tx}} \in [-10, 23]\text{ dBm}$), orçamento de PRBs ($\le 100\%$) e bloqueio de ping-pong ($\Delta t \ge 1000\text{ ms}$).
* **Camada E2 e Mapeadores Normativos (`src/e2/`):**
  * `e2ap/`: Serialização e parsing ASN.1 APER de `RICsubscriptionRequest`, `RICcontrolRequest`, `RICcontrolAcknowledge` e `RICcontrolFailure` (E2AP v02.03).
  * `kpm/`: Construtores normativos de `E2SM_KPM_EventTriggerDefinition` (Formato 1) e `E2SM_KPM_ActionDefinition` (Formato 1) com métricas 3GPP 28.552 (`DRB.UEThpDl`, `RRU.PrbTotDl`, `DRB.PacketLossRateDl`).
  * `rc/`: Mapeador `RCMapper` que traduz `RDLDecision` em `E2SM_RC_ControlHeader` e `E2SM_RC_ControlMessage` (Formato 1, Estilo 1) com tabela canônica de parâmetros RAN (`PRB_QUOTA`, `SCHEDULER_WEIGHT`, `TX_POWER`, `HANDOVER`).
* **Pipeline de Pass-Through de Ações Limpas:** Despacha imediatamente ações não conflitantes para as gNodeBs após validação de segurança.
* **Rastreamento Assíncrono de Transações E2:** Mapeia `transaction_id` para mensagens `RIC_CONTROL_REQ` e mede o RTT de controle via `RIC_CONTROL_ACK`.

![Fluxo funcional da arquitetura proposta para a xApp-RDL](docs/figures/01_arquitetura_e_modelagem/fig_fluxo_funcional_arquitetura_rdl.png)

### 1.1. Taxonomia de Origem das xApps (`origin_type`)

O ecossistema experimental classifica rigorosamente a procedência de cada xApp:

| Nome da xApp | Origem / Fonte | Tipo de Origem (`origin_type`) | Papel no Repositório |
| :--- | :--- | :---: | :--- |
| **Traffic Steering** | [O-RAN SC `ric-app-ts`](https://github.com/o-ran-sc/ric-app-ts) | `ORAN_SC_OFFICIAL` | Terceiros / Oficial O-RAN SC Release J |
| **KPIMON** | [O-RAN SC `ric-app-kpimon`](https://github.com/o-ran-sc/ric-app-kpimon) | `ORAN_SC_OFFICIAL` | Terceiros / Oficial O-RAN SC (Telemetria) |
| **xSlice (QoS Slicing)** | [peihaoY/xslice-oran](https://github.com/peihaoY/xslice-oran) (Yan et al., 2025) | `ACADEMIC_REIMPLEMENTATION` | Terceiros / Reimplementação Acadêmica |
| **Energy Saving** | [Orange-OpenSource/ns-O-RAN-flexric](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) | `LITERATURE_INSPIRED` | Terceiros / Inspirada na Literatura |
| **Load Balancer** | Proposta Experimental | `PROPOSED_EXPERIMENTAL` | Proposta / Referência H-RDL |
| **Beamformer** | Proposta Experimental | `PROPOSED_EXPERIMENTAL` | Proposta / Referência H-RDL |
| **ISAC Radar** | Proposta Experimental | `PROPOSED_EXPERIMENTAL` | Proposta / Referência H-RDL (6G ISAC) |
| **Rogue xApp** | Workload de Teste | `TEST_HARNESS` | Teste / Injeção de Falhas |
| **Bouncer** | Workload de Teste | `TEST_HARNESS` | Teste / Benchmark de Latência RMR |

*Consulte a documentação detalhada e o catálogo de figuras dos cenários S1–S15 em [`docs/figures/README.md`](docs/figures/README.md), [`docs/modelagem_cenarios_xapps_terceiros.md`](docs/modelagem_cenarios_xapps_terceiros.md), [`docs/topologia_espacial_e_cenarios_s1_s5.md`](docs/topologia_espacial_e_cenarios_s1_s5.md), [`docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md`](docs/analise_xapps_avancadas_cenarios_futuros_ntn_uav_v2x_iiot.md) e [`reference-xapps/README.md`](reference-xapps/README.md).*

### 1.2. Catálogo Oficial de Figuras dos Cenários Experimentais (S1–S15)

O repositório conta com um catálogo completo de figuras conceituais e de topologia espacial em alta resolução para a suíte de cenários S1 a S15:
- **S1 (EEVS):** Energy Saving vs. QoS — [`s1_eevs_energy_vs_qos_dark.png`](docs/figures/02_cenarios_e_topologias/s1_eevs_energy_vs_qos_dark.png)
- **S2 (TVS):** Traffic Steering vs. Slicing — [`s2_tvs_traffic_steering_dark.png`](docs/figures/02_cenarios_e_topologias/s2_tvs_traffic_steering_dark.png)
- **S3:** Multi-Slice Traffic Steering vs Slicing — [`s3_multi_slice_traffic_steering.png`](docs/figures/02_cenarios_e_topologias/s3_multi_slice_traffic_steering.png)
- **S7:** 5G-Advanced Channel Overlap & Multicarrier MIMO — [`s7_5ga_channel_overlap_mimo.png`](docs/figures/02_cenarios_e_topologias/s7_5ga_channel_overlap_mimo.png)
- **S8:** 6G ISAC Urban & Environmental Sensing — [`s8_6g_isac_urban_green_sensing.png`](docs/figures/02_cenarios_e_topologias/s8_6g_isac_urban_green_sensing.png)
- **S9:** NTN Orbital Handover — [`s9_ntn_orbital_handover.png`](docs/figures/02_cenarios_e_topologias/s9_ntn_orbital_handover.png)
- **S10:** UAV Swarm Stadium Coverage — [`s10_uav_swarm_stadium_coverage.png`](docs/figures/02_cenarios_e_topologias/s10_uav_swarm_stadium_coverage.png)
- **S11:** V2X Highway Ping-Pong Storm — [`s11_v2x_highway_pingpong_storm.png`](docs/figures/02_cenarios_e_topologias/s11_v2x_highway_pingpong_storm.png)
- **S12:** IIoT Zero-Jitter Robotic Slicing — [`s12_iiot_zero_jitter_robotic_slicing.png`](docs/figures/02_cenarios_e_topologias/s12_iiot_zero_jitter_robotic_slicing.png)
- **S13:** Disaster Rescue Heterogeneous Mesh — [`s13_disaster_rescue_heterogeneous_mesh.png`](docs/figures/02_cenarios_e_topologias/s13_disaster_rescue_heterogeneous_mesh.png)
- **S14:** Rural Agriculture 4.0 Sensing — [`s14_rural_agriculture_sensing.png`](docs/figures/02_cenarios_e_topologias/s14_rural_agriculture_sensing.png)
- **S15:** 6G Dense City Conflict Storm — [`s15_6g_dense_city_conflict_storm.png`](docs/figures/02_cenarios_e_topologias/s15_6g_dense_city_conflict_storm.png)



---

## 2. Estrutura do Repositório

```text
.
├── configs/                     # Descritores de configuração xApp (config-file.json, routes.rt)
├── deploy/                      # Manifestos de Implantação
│   ├── helm/                    # Helm Charts oficiais (RDL, xSlice, Energy Saving, Traffic Steering)
│   ├── kubernetes/              # Manifestos K8s puros (Near-RT RIC ricplt + 3 xApps + RDL ricxapp)
│   └── openran-br-v3/           # Perfil de Implantação OpenRAN@Brasil Blueprint v3 (Release J)
├── docs/                        # Portal de Documentação Técnica e Referências Normativas
│   ├── e2/                      # Matriz de Versões e Fontes Normativas O-RAN (E2AP/KPM/RC)
│   ├── README.md                # Índice e trilhas de leitura da documentação
│   └── 01 a 05                  # Volumes temáticos de arquitetura, cluster, deploy e operação
├── reference-xapps/             # Adaptadores leves das 3 xApps de referência abertas
├── reproducibility/             # Bloqueio de versões (versions.lock) e Runbook de reprodução
├── scripts/                     # Automação de Deploy, Testes e Reprodução
│   ├── reproduce_f1.sh          # Pipeline completo de reprodução determinística (Fase 1)
│   ├── deploy_helm.sh           # Pipeline Helm (Near-RT RIC -> 3 xApps -> RDL)
│   ├── deploy_k8s.sh            # Pipeline K8s/Kustomize equivalente
│   └── verify_3_xapps.sh        # Smoke test unificado de todas as xApps
├── simulations/                 # Cenários C++ de Co-Simulação no ns-3 NORI / 5G-LENA
│   └── ns3/                     # scenario_rdl_closed_loop_nori.cc (Closed-Loop E2 Report & Control)
├── src/                         # Código-Fonte Python da xApp RDL (Clean Architecture)
│   ├── conflict_types.py        # Contratos formais desacoplados (RDLDecision, XAppAction)
│   ├── rdl_xapp.py              # Ciclo de vida xApp e despacho via E2/RCMapper
│   ├── e2/                      # Pilha de protocolos E2 (e2ap/, kpm/, rc/)
│   ├── agents/                  # Agentes cognitivos (Perception, Reasoning, Refinement)
│   └── models/                  # Modelos analíticos físicos (Shannon, M/G/1, Earth)
├── tests/                       # Suíte de Testes Modulares (tests/codec, tests/unit, tests/integration)
└── Makefile                     # CLI unificada de operação, testes e benchmarks
```

---

## 3. Infraestrutura Leve com k3d, Rancher e Kiali

Para desenvolvimento ágil e validação de baixo consumo de recursos, o projeto suporta provisionamento de clusters Kubernetes leves via **k3d (K3s em Docker)** com exposição das portas padronizadas da arquitetura O-RAN:

### 3.1. Topologias de Cluster k3d Disponíveis

#### Opção 1: Single-Node (1 Servidor/Worker Unificado, ~450 MB RAM)
> *Ideal para desenvolvimento local rápido, CI/CD e máquinas com recursos limitados.*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

#### Opção 2: Dual-Node (1 Control-Plane + 1 Worker Node, ~900 MB RAM)
> *Separação física de pods entre plano de controle do cluster e nós de execução.*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  --agents 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

#### Opção 3: 3-Nodes / Multi-Node (1 Control-Plane + 2 Worker Nodes, ~1.5 GB RAM)
> *Topologia de produção: Isolamento estrito de namespaces (`ricplt` no worker-1 e `ricxapp` no worker-2).*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  --agents 2 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

### 3.2. Mapeamento de Portas e Serviços O-RAN

| Porta / Protocolo | Componente / Serviço | Namespace | Descrição Funcional |
| :---: | :---: | :---: | :--- |
| `36422/SCTP` | `service-ricplt-e2term-sctp` | `ricplt` | Terminação E2 (E2AP / E2SM-KPM / E2SM-RC) conectando gNBs/ns-3 |
| `38000/TCP` | `service-ricplt-e2term-rmr` | `ricplt` | Barramento RMR interno do E2 Termination |
| `6379/TCP` | `service-ricplt-dbaas-tcp` | `ricplt` | Banco de dados Redis SDL (Shared Data Layer) |
| `4560/TCP` | `service-ricxapp-iqos-xapp-rdl-rmr` | `ricxapp` | Canal de dados e despacho de ações RMR da xApp-RDL |
| `4561/TCP` | `service-ricxapp-iqos-xapp-rdl-rmr` | `ricxapp` | Canal de controle e distribuição de tabelas de rota RMR |
| `8080/TCP` | `service-ricxapp-iqos-xapp-rdl-http` | `ricxapp` | Healthcheck REST (`/health/alive`, `/health/ready`) |
| `8081/TCP` | `service-ricxapp-iqos-xapp-rdl-http` | `ricxapp` | Métricas Prometheus de Governança e Decisões RDL |
| `8443/TCP` | `rancher-server` | `cattle-system` | Dashboard Web e gestão centralizada de nós e workloads |
| `20001/TCP` | `kiali-dashboard` | `istio-system` | Visualização gráfica de topologia e tráfego Service Mesh |

---

## 4. Guia Rápido de Execução e Deploy

### Opção A: Implantação Rápida via Perfil OpenRAN@Brasil Blueprint v3 (`deploy/openran-br-v3/`)
Manifestos K8s puros e otimizados para o namespace `ricxapp` seguindo a especificação normativa da Release J / OpenRAN@Brasil:
```bash
# 1. Criar os namespaces oficiais se ainda não existirem
kubectl create namespace ricplt --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -

# 2. Aplicar ConfigMap e tabela de rotas RMR
kubectl apply -f deploy/openran-br-v3/config-map.yaml

# 3. Aplicar Serviços de Rede (RMR 4560/4561 + HTTP 8080/8081)
kubectl apply -f deploy/openran-br-v3/service.yaml

# 4. Aplicar o Deployment da xApp RDL
kubectl apply -f deploy/openran-br-v3/deployment.yaml

# 5. Validar o status da implantação
kubectl get pods,svc -n ricxapp -l app=iqos-xapp-rdl
```

### Opção B: Deploy Governança Completa Helm (Near-RT RIC + 3 Reference xApps + RDL)
```bash
make helm-deploy
```

### Opção C: Deploy Baseline (Near-RT RIC + 3 Reference xApps SEM RDL)
```bash
make helm-deploy-baseline
```

### Opção D: Validação e Smoke Test das 3 xApps de Referência
```bash
make test-3xapps
```

### Opção E: Suíte de Testes Modulares (11/11 PASS)
```bash
make test
```

### Opção F: Reprodução Determinística do Ambiente
```bash
make reproduce-f1
```

---

## 5. Observabilidade e Monitoramento

* **Rancher Dashboard:** Interface visual de gestão do cluster, nós e namespaces (`ricplt`, `ricxapp`):
  ```bash
  make rancher-stop       # (Opcional) Para e remove container anterior
  make rancher-start      # 1. Inicia o container do Rancher Server (:8443)
  make rancher-logs       # 2. Acompanha os logs (ou: docker logs -f rancher-server)
  make rancher-password   # 3. Obtém a Bootstrap Password inicial
  # 4. Acesse no navegador: URL: https://localhost:8443 (ou https://<IP_DO_HOST>:8443)
  make rancher-connect URL="https://localhost:8443/v3/import/c-m-xxxx_c-m-xxxx.yaml" # 5. Vincula o cluster
  ```
* **Kiali Service Mesh:** Para visualização em grafo animado do fluxo de dados entre xApps e o Near-RT RIC:
  ```bash
  make kiali-install      # Instala Istio e Kiali no c---

## 6. Política Rígida de Providência e Resultados Experimentais

$$
\boxed{
\text{Resultado científico válido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}
}
$$

A infraestrutura experimental **ns-3 / 5G-LENA v5.1 / NORI** está em validação atrelada à política estrita de **Zero Dados Sintéticos**. Resultados científicos somente serão publicados após aprovação automática dos gates de proveniência e interoperabilidade (**Gate 1 a Gate 4**).

### 6.1. Critérios dos Gates de Validação Experimental

| Gate | Descrição e Requisito de Aprovação | Condição de Bloqueio |
| :---: | :--- | :---: |
| **Gate 1** | **Interoperabilidade E2 KPM Real**<br/>Conexão SCTP/NORI $\to$ Near-RT RIC, subscrição aceita, `RICindication` `.raw` decodificado via APER e validação semântica com o FlowMonitor ($\epsilon < 5\%$). | **Obrigatório (`GATE_1_REQUIRED=true`)** |
| **Gate 2** | **Rastreabilidade e Providência Extrema**<br/>Verificação de hashes SHA256 do binário ns-3, sementes, FlowMonitor XML, logs e manifestos `execution_manifest.json`. | **Obrigatório** |
| **Gate 3** | **Controle E2SM-RC em Malha Fechada**<br/>Envio de `RICcontrolRequest` via APER e confirmação externa por `RICcontrolAcknowledge` sobre SCTP real. | **Obrigatório** |
| **Gate 4** | **Fechamento do Causal Loop RAN**<br/>Encadeamento de causa-efeito: $\text{KPM}(t_0) \to \text{H-RDL} \to \text{Control} \to \text{NORI} \to \text{ns-3} \to \text{State Change} \to \text{KPM}(t_1)$. | **Obrigatório** |

---

## 7. Reprodutibilidade e Validação de Providência em Um Comando

Para executar a verificação estrita de proveniência e integridade sem dados sintéticos:

```bash
# Auditoria estática de código contra geradores mock
python scripts/check_no_synthetic_results.py

# Validação do pipeline de proveniência de dados reais
python scripts/validate_provenance.py experiments/runs/gate1/seed-1001

# Suíte de testes funcionais e codecs de software (isolados de experiments/)
make test-unit
make test-codec
make test-integration
make test-interop
```

---

## 8. Perfis Normativos e Auditorias Técnicas

* **[Parecer Técnico de Resolução Integral da Nova Auditoria (2026)](auditoria/Nova_Auditoria_Tecnica_Interop_E2_Closed_Loop_2026.md)**
* **[Especificação do Perfil Normativo Congelado (F1 Frozen Profile)](docs/oran_compatibility_profile_frozen.md)**
* **[Manifesto Machine-Readable de Versões e Hashes](specs/oran/compatibility_profile.json)**
* **[Catálogo de Vetores Dourados APER](specs/golden_vectors/)**

---

<div align="center">

**Projeto xApp RDL — O-RAN Near-RT RIC Conflict Mitigation**  
*Desenvolvido em conformidade estrita com ETSI TS 104 039, O-RAN.WG3.E2AP e O-RAN Software Community Release I/J.*

</div>



