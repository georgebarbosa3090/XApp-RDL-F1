# Automação Completa de Build, Importação k3d e Deploy Helm

**Documento:** Guia de Automação de CI/CD Local  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Ambiente:** Cluster k3d / Kubernetes Near-RT RIC no WSL2  
**Data:** 25/08/2026  

---

## 1. Visão Geral

Para eliminar comandos manuais repetitivos e evitar erros de `ImagePullBackOff` ou esquecimento de parâmetros, foi criado um pipeline 100% automatizado em comando único (`make helm-deploy` ou `bash scripts/deploy_helm.sh`).

### O Pipeline Executa Automaticamente:
1. **Rebuild da Imagem Docker:** Compilação multi-stage com cache inteligente.
2. **Auto-Importação k3d:** Identifica todos os containers de nós do cluster k3d e carrega a imagem no `containerd` de cada um via streaming (`docker save | ctr images import`).
3. **Provisionamento de Namespaces:** Criação segura dos namespaces `ricplt` e `ricxapp`.
4. **Lint & Package Helm:** Validação estrutural do chart e geração do pacote `.tgz`.
5. **Helm Upgrade / Install:** Deploy com `image.pullPolicy=Never`, `useFakeSdl=true` e `rmrWaitForReady=false`.
6. **Rollout Wait:** Aguarda ativamente o Pod atingir o estado `1/1 Ready` e exibe o status final.

---

## 2. Como Executar com 1 Único Comando

No terminal do seu servidor Ubuntu (`SAC-10806` ou WSL):

```bash
cd ~/XApp-RDL-F1

# Executar o deploy completo automatizado
make helm-deploy
```

*(Ou alternativamente rodar direto o script: `bash scripts/deploy_helm.sh`)*.

---

## 3. Comandos Úteis no Makefile

| Comando | Descrição |
| :--- | :--- |
| **`make helm-deploy`** | Executa o pipeline completo (Build + Import k3d + Package + Deploy + Wait). |
| **`make helm-test`** | Faz port-forward automático e testa o `/health` (HTTP 200) e `/metrics` (Prometheus). |
| **`make logs`** | Acompanha os logs estruturados da xApp RDL em tempo real no Kubernetes. |
| **`make status`** | Exibe o status da release Helm e a lista de Pods ativos no namespace `ricxapp`. |
| **`make helm-uninstall`** | Remove completamente a release e os serviços da xApp do Kubernetes. |

---

## 4. Teste Automatizado dos Endpoints

Após o deploy, teste a saúde e métricas com:

```bash
make helm-test
```
