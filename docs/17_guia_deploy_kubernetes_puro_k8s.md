# Guia de Deploy Nativo em Kubernetes (K8s Puro / Kustomize)

**Documento:** Guia de Implantação sem Helm  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Ambiente:** Qualquer Cluster Kubernetes Padrão (k3d, Kubeadm, Minikube, MicroK8s, EKS, GKE, Bare-Metal)  
**Data:** 25/08/2026  

---

## 1. Visão Geral

Para ambientes ou operadores que preferem **manifestos declarativos puros do Kubernetes** sem a necessidade do gerenciador de pacotes Helm, a pasta [deploy/kubernetes/](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1/deploy/kubernetes/) fornece a stack completa estruturada com suporte ao **Kustomize** (`kubectl apply -k`).

---

## 2. Estrutura dos Manifestos Kubernetes (`deploy/kubernetes/`)

```text
deploy/kubernetes/
├── kustomization.yaml       # Orquestrador Kustomize
├── namespace.yaml           # Cria os namespaces ricplt e ricxapp
├── configmap.yaml           # Configurações JSON e rotas RMR (routes.rt)
├── deployment.yaml          # Pod da xApp RDL com probes HTTP e portas RMR
├── service-http.yaml        # Service ClusterIP para portas 8080 (health) e 8081 (metrics)
└── service-rmr.yaml         # Service ClusterIP para portas 4560 (data) e 4561 (route)
```

---

## 3. Deploy com 1 Único Comando

### Opção A: Via Make (Automatizado com Build e Import k3d)
```bash
cd ~/XApp-RDL-F1
make k8s-deploy
```

### Opção B: Via Script Bash
```bash
cd ~/XApp-RDL-F1
bash scripts/deploy_k8s.sh
```

### Opção C: Diretamente com Kubectl Kustomize
```bash
# 1. Aplicar todos os manifestos de uma vez
kubectl apply -k deploy/kubernetes/

# 2. Acompanhar a subida do Pod
kubectl rollout status deployment/ricxapp-iqos-xapp-rdl -n ricxapp --timeout=60s
```

---

## 4. Testes e Monitoramento Pós-Deploy

```bash
# 1. Testar os endpoints de saúde e Prometheus
make k8s-test

# 2. Ver logs estruturados em tempo real
make logs

# 3. Inspecionar Pods e Serviços
kubectl get all -n ricxapp
```

---

## 5. Remoção Completa (*Uninstall*)

Para remover todos os componentes do cluster:

```bash
make k8s-uninstall
# ou
kubectl delete -k deploy/kubernetes/
```
