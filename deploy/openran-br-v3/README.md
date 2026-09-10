# Perfil de Implantação OpenRAN@Brasil Blueprint v3

Este diretório contém os manifestos de implantação e parâmetros de configuração alinhados à especificação do **OpenRAN@Brasil Blueprint v3** (LABORA/UFG e consórcio OpenRAN@Brasil).

---

## 1. Topologia de Namespaces e Serviços

* **Namespace da Plataforma (`ricplt`):**
  * `service-ricplt-e2mgr-http`: Porta `3800` (E2 Manager)
  * `service-ricplt-submgr-http`: Porta `8088` (Subscription Manager)
  * `service-ricplt-e2term-rmr`: Porta `38000` (E2 Termination RMR)
  * `service-ricplt-dbaas-tcp`: Porta `6379` (Redis SDL)
* **Namespace das Aplicações (`ricxapp`):**
  * `service-ricxapp-iqos-xapp-rdl-rmr`: Porta `4560` (Data) / `4561` (Route)
  * `service-ricxapp-iqos-xapp-rdl-http`: Porta `8080` (Health) / `8081` (Metrics Prometheus)

---

## 2. Instruções de Implantação

```bash
# 1. Aplicar ConfigMap e Rotas RMR
kubectl apply -f deploy/openran-br-v3/config-map.yaml

# 2. Aplicar Services
kubectl apply -f deploy/openran-br-v3/service.yaml

# 3. Aplicar Deployment
kubectl apply -f deploy/openran-br-v3/deployment.yaml

# 4. Verificar Status dos Pods
kubectl get pods -n ricxapp -l app=iqos-xapp-rdl
```
