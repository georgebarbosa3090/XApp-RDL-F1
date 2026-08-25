# Volume 06: Observabilidade Service Mesh com Kiali e Injeção de Tráfego O-RAN

**Documento:** Volume Temático 06  
**Projeto:** xApp RDL (Resource and Decision Layer)  
**Escopo:** Checklist de Dependências, Istio Service Mesh, Kiali Dashboard e Injetor Contínuo de Tráfego  
**Data de Consolidação:** 25/08/2026  

---

## 1. Auditoria Consolidada de Dependências

| Camada | Componente | Status | Validação |
| :--- | :--- | :---: | :--- |
| **Infra / Host** | WSL2 (Ubuntu 20.04) / Docker | ✅ OK | Docker Engine e containerd operacionais no host `SAC-10806`. |
| **Cluster K8s** | k3d (`rancher-lab`) | ✅ OK | Nós `server-0` e `agent-0` ativos com portas O-RAN expostas. |
| **Gerenciador** | Rancher Dashboard v2.14 | ✅ OK | Painel web ativo em `https://127.0.0.1:8443`. |
| **Near-RT RIC** | Namespaces `ricplt` e `ricxapp` | ✅ OK | Isolamento de plataforma e aplicações. |
| **xApp RDL (Fase 1)** | RMRXapp + FastAPI + Prometheus | ✅ OK | **10/10 Testes Unitários Passando (100% Green)**. |
| **xApp RDL (Fase 2)** | Pipeline Cognitivo MARL / MAPPO | ✅ OK | **10/10 Testes Unitários Passando (100% Green)**. |

---

## 2. Observabilidade com Kiali (Recurso Opcional)

O **Kiali** é uma ferramenta de observabilidade avançada baseada no **Istio Service Mesh** que gera uma **topologia gráfica animada em tempo real** das mensagens trafegando entre xApps e o Near-RT RIC.

### 2.1. Como Instalar e Abrir o Kiali (Automatizado):
```bash
cd ~/XApp-RDL-F1

# 1. Instalar Istio e Kiali automaticamente
make kiali-install

# 2. Abrir o Dashboard no navegador
make kiali-dashboard
```

---

## 3. Injeção Contínua de Tráfego O-RAN

Como o Kiali é um monitor de telemetria em tempo real, ele necessita de tráfego contínuo para desenhar as setas e animações no grafo.

### 3.1. Como Iniciar o Gerador de Tráfego:
```bash
# Executar em um terminal separado do WSL:
make inject-traffic
```

### 3.2. Como Visualizar o Grafo Animado no Kiali:
1. Acesse: **`http://localhost:20001/kiali`**
2. Vá no menu **Graph** (Grafo) à esquerda.
3. No seletor de namespaces, marque **`ricxapp`** e **`ricplt`**.
4. No menu suspenso **Display**, ative:
   - ✅ **`Traffic Animation`** (Bolinhas verdes animadas indicando o fluxo de dados).
   - ✅ **`Response Time`** (Latência em milissegundos de cada conexão).
   - ✅ **`Request Rate`** (Taxa de requisições por segundo - RPS).
