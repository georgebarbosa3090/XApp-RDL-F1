# Guia de Injeção de Tráfego O-RAN e Observabilidade Kiali Mesh

**Documento:** Guia Prático de Injeção Contínua de Tráfego  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Ambiente:** Istio Service Mesh / Kiali / Kubernetes no WSL2  
**Data:** 25/08/2026  

---

## 1. Por que o Kiali exige Injeção de Tráfego?

O **Kiali** é um monitor de telemetria em tempo real. Ele coleta métricas capturadas pelos proxies Envoy (sidecars) do Istio.
* Se a rede estiver ociosa (sem requisições trafegando no momento), o Kiali exibirá a mensagem `No traffic in selected time range`.
* Para visualizar as **arestas, nós e animações de tráfego verde fluindo no grafo**, é necessário gerar fluxo contínuo de pacotes.

---

## 2. Como Injetar Tráfego com 1 Comando

No terminal do seu servidor Ubuntu (`SAC-10806` ou WSL):

```bash
cd ~/XApp-RDL-F1

# Iniciar o gerador contínuo de tráfego O-RAN
make inject-traffic
```

*(Ou diretamente: `bash scripts/inject_traffic.sh`)*.

---

## 3. O que o Injetor de Tráfego faz:
1. Estabelece canal direto com o Service da xApp RDL no namespace `ricxapp`.
2. Envia requisições contínuas aos endpoints de saúde (`/health`, `/ready`) e coleta métricas Prometheus (`/metrics`).
3. Exibe em tempo real o contador de lotes e o status HTTP de cada pacote enviado.

---

## 4. Visualizando o Grafo no Kiali (Passo a Passo)

1. Em outro terminal, abra o dashboard do Kiali:
   ```bash
   make kiali-dashboard
   ```
2. Acesse no navegador: **`http://localhost:20001/kiali`**
3. Vá no menu lateral esquerdo -> **`Graph`** (Grafo).
4. No topo da tela:
   - **Select Namespaces:** Marque `ricxapp` (e `ricplt` se ativo).
   - **Display Options (menu suspenso *Display*):**
     - ✅ **Traffic Animation** (Ativa as bolinhas animadas de fluxo).
     - ✅ **Response Time** (Mostra a latência em ms de cada link).
     - ✅ **Request Rate** (Mostra a taxa de requisições/s).
5. O grafo exibirá instantaneamente a xApp **`ricxapp-iqos-xapp-rdl`** com tráfego animado e métricas ativas!
