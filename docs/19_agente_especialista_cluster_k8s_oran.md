# Agente Especialista: Operador de Cluster K8s & O-RAN no WSL2

**Documento:** Especificação do Agente Especialista  
**Skill:** `07-k8s-oran-cluster-operator`  
**Escopo:** Gestão autônoma de Kubernetes (k3d, k3s, Kubeadm), Rancher Dashboard, Near-RT RIC e xApps no WSL2  
**Data:** 25/08/2026  

---

## 1. Perfil do Agente

O agente **`07-k8s-oran-cluster-operator`** é o **Especialista em Engenharia de Infraestrutura e Operações de Cluster (Cluster SRE)** para o ecossistema O-RAN no ambiente WSL2 / Linux.

### Capacidades e Ações Autônomas:
1. **Manipulação Direta do Cluster:**
   - Criação e recriação de clusters k3d com portas O-RAN mapeadas (`SCTP 36422`, `HTTP 8080/8081`, `RMR 4560/4561`).
   - Importação contínua de imagens Docker para os nós containerd (`ctr images import`).
2. **Correção Automática de Problemas no Rancher:**
   - Diagnóstico e resolução de `CrashLoopBackOff` e `ErrImageNeverPull`.
   - Ajuste automático de rede Docker (`docker network connect`) e sincronização de `server-url`.
3. **Deploy Contínuo de xApps:**
   - Empacotamento Helm automatizado e deploy declarativo via Kustomize.
   - Sondas de liveness/readiness e testes de métricas Prometheus.

---

## 2. Como Acionar o Agente

O agente pode ser acionado automaticamente sempre que houver necessidade de operar, diagnosticar ou corrigir qualquer elemento da infraestrutura Kubernetes, Rancher ou xApp.
