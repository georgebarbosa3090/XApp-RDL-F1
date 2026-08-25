# Volume 03: Guia de Implantação e Automação de Deploy (Helm e Kubernetes Puro)

**Documento:** Volume Temático 03  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Escopo:** Empacotamento Helm, Deploy Declarativo Kustomize/K8s, Pipelines Automatizados e Onboarding DMS  
**Data de Consolidação:** 25/08/2026  

---

## 1. Visão Geral das Estratégias de Deploy

A xApp RDL suporta duas modalidades oficiais de implantação no Kubernetes Near-RT RIC:

1. **Modalidade Helm Chart (Padrão O-RAN / Produção):** Utiliza a estrutura declarativa `deploy/helm/iqos-xapp-rdl` gerenciada via Helm CLI v3 ou AppMgr DMS.
2. **Modalidade Kubernetes Puro / Kustomize (Desenvolvimento / K8s Nativo):** Utiliza os manifestos puros em `deploy/kubernetes/` aplicados diretamente com `kubectl apply -k`.

---

## 2. Estrutura do Helm Chart (`deploy/helm/iqos-xapp-rdl/`)

```text
deploy/helm/iqos-xapp-rdl/
├── Chart.yaml                  # Metadados do Chart (versão 1.1.0 / 2.0.0)
├── values.yaml                 # Parâmetros configuráveis (portas, recursos, sondas)
└── templates/
    ├── _helpers.tpl            # Nomes e labels padronizados
    ├── deployment.yaml         # Pod da xApp com healthcheck e security context
    ├── service-http.yaml       # Serviços HTTP (porta 8080 health / 8081 metrics)
    └── service-rmr.yaml        # Serviços RMR (portas 4560 data / 4561 route)
```

### 2.1. Deploy Helm Automatizado em 1 Comando
Para compilar a imagem, carregar nos nós do k3d, validar sintaxe, empacotar e fazer o deploy:

```bash
cd ~/XApp-RDL-F1
make helm-deploy
```

*(Ou diretamente: `bash scripts/deploy_helm.sh`)*.

### 2.2. Comandos Manuais de Helm
```bash
# 1. Validar sintaxe
helm lint deploy/helm/iqos-xapp-rdl

# 2. Empacotar em .tgz
helm package deploy/helm/iqos-xapp-rdl

# 3. Fazer o deploy no namespace ricxapp
helm upgrade --install ricxapp-iqos-xapp-rdl ./iqos-xapp-rdl-1.1.0.tgz \
  --namespace ricxapp \
  --create-namespace \
  --set image.pullPolicy=Never \
  --set env.useFakeSdl="true" \
  --set env.rmrWaitForReady="false"
```

---

## 3. Estrutura de Kubernetes Puro (`deploy/kubernetes/`)

Para operadores que não utilizam Helm, a pasta `deploy/kubernetes/` disponibiliza a stack completa com suporte ao **Kustomize**:

```text
deploy/kubernetes/
├── kustomization.yaml       # Orquestrador Kustomize
├── namespace.yaml           # Cria os namespaces ricplt e ricxapp
├── configmap.yaml           # Configurações JSON e rotas RMR (routes.rt)
├── deployment.yaml          # Pod da xApp RDL com probes HTTP e portas RMR
├── service-http.yaml        # Service ClusterIP para portas 8080 e 8081
└── service-rmr.yaml         # Service ClusterIP para portas 4560 e 4561
```

### 3.1. Deploy K8s Nativo em 1 Comando
```bash
make k8s-deploy
# ou diretamente:
kubectl apply -k deploy/kubernetes/
```

---

## 4. Onboarding no O-RAN DMS / AppMgr (Opcional)

Em clusters com a plataforma Near-RT RIC completa e `dms_cli` configurado:

```bash
# 1. Onboarding do descriptor da xApp
dms_cli onboard configs/config-file.json configs/schema.json

# 2. Instalar a xApp via DMS
dms_cli install --xapp-chart-name iqos-xapp-rdl --version 1.1.0 --namespace ricxapp

# 3. Checar status no DMS
dms_cli status iqos-xapp-rdl
```

---

## 5. Tabela de Comandos de Operação e Testes

| Ação Desejada | Comando Make | Comando Equivalente Kubectl / Helm |
| :--- | :--- | :--- |
| **Deploy Helm Completo** | `make helm-deploy` | `bash scripts/deploy_helm.sh` |
| **Deploy K8s Puro** | `make k8s-deploy` | `kubectl apply -k deploy/kubernetes/` |
| **Testar Endpoints** | `make helm-test` | `curl http://localhost:8080/health` |
| **Ver Logs da xApp** | `make logs` | `kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -f` |
| **Status dos Pods** | `make status` | `kubectl get pods -n ricxapp -o wide` |
| **Desinstalar xApp** | `make helm-uninstall` | `helm uninstall ricxapp-iqos-xapp-rdl -n ricxapp` |
