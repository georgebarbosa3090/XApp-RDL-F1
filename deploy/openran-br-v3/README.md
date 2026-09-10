# Perfil de Implantação OpenRAN@Brasil Blueprint v3 (Release J / Blueprint v3)

<div align="center">

**Manifestos de Implantação Kubernetes e Configurações de Rede para o namespace `ricxapp`**  
*Homologado em conformidade com consórcio OpenRAN@Brasil (LABORA/UFG, CPQD, INATEL, UFPA PCT)*

</div>

---

## 1. Topologias de Cluster k3d Recomendadas

Para implantação e validação rápida em ambiente local/WSL2 ou bare-metal:

### Opção 1: Single-Node (1 Servidor/Worker Unificado, ~450 MB RAM)
> *Ideal para desenvolvimento local rápido, CI/CD e máquinas com recursos limitados.*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

### Opção 2: Dual-Node (1 Control-Plane + 1 Worker Node, ~900 MB RAM)
> *Separação física de Pods entre o plano de controle do cluster e os nós de execução da rede.*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  --agents 1 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

### Opção 3: 3-Nodes / Multi-Node (1 Control-Plane + 2 Worker Nodes, ~1.5 GB RAM)
> *Topologia de produção: Isolamento estrito de namespaces (`ricplt` no worker-1 e `ricxapp` no worker-2).*

```bash
k3d cluster create rdl-cluster \
  --servers 1 \
  --agents 2 \
  -p "36422:36422/sctp@server:0" \
  -p "8080-8087:8080-8087@server:0" \
  -p "4560-4561:4560-4561@server:0"
```

---

## 2. Topologia de Namespaces e Serviços

* **Namespace da Plataforma (`ricplt`):**
  * `service-ricplt-e2term-sctp`: Porta `36422/SCTP` (Terminação E2 conectando gNBs/ns-3)
  * `service-ricplt-e2mgr-http`: Porta `3800/TCP` (E2 Manager REST)
  * `service-ricplt-submgr-http`: Porta `8088/TCP` (Subscription Manager)
  * `service-ricplt-e2term-rmr`: Porta `38000/TCP` (E2 Termination RMR)
  * `service-ricplt-dbaas-tcp`: Porta `6379/TCP` (Redis SDL - Shared Data Layer)

* **Namespace das Aplicações (`ricxapp`):**
  * `service-ricxapp-iqos-xapp-rdl-rmr`: Portas `4560/TCP` (Canal de Dados) / `4561/TCP` (Tabelas de Rota RMR)
  * `service-ricxapp-iqos-xapp-rdl-http`: Portas `8080/TCP` (Health `/health/alive`, `/health/ready`) / `8081/TCP` (Métricas Prometheus)

---

## 3. Instruções de Implantação Passo a Passo

```bash
# 1. Garantir existência do namespace ricxapp
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -

# 2. Aplicar ConfigMap e Tabelas de Rota RMR
kubectl apply -f deploy/openran-br-v3/config-map.yaml

# 3. Aplicar Serviços de Rede e Exposição de Portas
kubectl apply -f deploy/openran-br-v3/service.yaml

# 4. Aplicar Deployment da xApp RDL (com SecurityContext não-root)
kubectl apply -f deploy/openran-br-v3/deployment.yaml

# 5. Verificar Status e Prontidão dos Pods
kubectl get pods -n ricxapp -l app=iqos-xapp-rdl -o wide
```

---

## 4. Gestão Visual via Rancher Dashboard e Kiali Service Mesh

```bash
# Importar cluster no Rancher Server (https://localhost:8443)
make rancher-connect URL="https://localhost:8443/v3/import/c-m-xxxx_c-m-xxxx.yaml"

# Visualizar topologia e tráfego de rede no Kiali Dashboard (http://localhost:20001/kiali)
make kiali-dashboard
```
