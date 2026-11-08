# Implantação da xApp RDL — perfil OpenRAN@Brasil Blueprint v3

Manifestos Kubernetes para o namespace `ricxapp`, pensados para o testbed OpenRAN@Brasil. **Não foram aplicados contra uma plataforma Near-RT RIC em funcionamento**; servem de ponto de partida.

## 1. Arquivos

| Arquivo | Conteúdo |
| :-- | :-- |
| `config-map.yaml` | configuração da xApp e tabela de rotas RMR |
| `service.yaml` | serviços RMR (4560/4561) e HTTP (8080/8081) |
| `deployment.yaml` | Deployment com usuário não-root |
| `values.yaml` | valores equivalentes para o chart `deploy/helm/iqos-xapp-rdl` |

## 2. Serviços esperados da plataforma (`ricplt`)

| Serviço | Porta | Uso pela xApp |
| :-- | :-- | :-- |
| `service-ricplt-submgr-http` | 8088/TCP | subscrição REST (`SUBMGR_URL`) |
| `service-ricplt-e2term-rmr` | 38000/TCP | RIC Control e Indication via RMR |
| `service-ricplt-e2term-sctp` | 36422/SCTP | conexão dos E2 Nodes |
| `service-ricplt-e2mgr-http` | 3800/TCP | inventário de nós E2 |
| `service-ricplt-dbaas-tcp` | 6379/TCP | SDL (Redis) |

Serviços da xApp (`ricxapp`): `service-ricxapp-iqos-xapp-rdl-rmr` (4560 dados, 4561 rotas) e `service-ricxapp-iqos-xapp-rdl-http` (8080 com `/health/alive`, `/health/ready` e o callback `/ric/v1/subscriptions/response`; 8081 com métricas Prometheus).

## 3. Implantação

Num cluster k3s (ou no cluster do testbed) com a plataforma `ricplt` já instalada:

```bash
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -
```

```bash
kubectl apply -f deploy/openran-br-v3/config-map.yaml -f deploy/openran-br-v3/service.yaml -f deploy/openran-br-v3/deployment.yaml
```

```bash
kubectl get pods -n ricxapp -l app=iqos-xapp-rdl -o wide
```

Alternativa com Helm:

```bash
helm upgrade --install iqos-xapp-rdl deploy/helm/iqos-xapp-rdl -n ricxapp -f deploy/openran-br-v3/values.yaml
```

A prontidão (`/health/ready`) só fica verde depois que a subscrição KPM é confirmada pelo Subscription Manager; sem plataforma, o pod permanece não pronto.

## 4. Painéis opcionais

O `Makefile` tem alvos auxiliares para Rancher (`make rancher-connect URL=...`) e Kiali (`make kiali-dashboard`).
