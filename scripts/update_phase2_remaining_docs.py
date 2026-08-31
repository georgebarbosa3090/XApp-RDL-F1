#!/usr/bin/env python3
"""
Atualiza os volumes 02, 04 e 06 da documentação da Fase 2
"""
import os

P1_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P2_DIR = os.path.abspath(os.path.join(P1_DIR, "..", "iqos-xapp-rdl-phase2"))

doc_02 = """# Volume 02: Infraestrutura de Cluster k3d, Rancher Dashboard e Operações O-RAN

**Documento:** Volume Temático 02  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Topologias k3d no WSL2, Configuração de Portas O-RAN, Near-RT RIC e Rancher Dashboard  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Topologias de Cluster k3d para O-RAN no WSL2

Executar a stack completa do **Near-RT RIC** e xApps no WSL2 exige uma gestão precisa de portas e limites de memória para suportar a coexistência com o simulador `ns-3`.

### Portas O-RAN Mapeadas no Cluster k3d:
* **Porta `36422/SCTP`:** Interface E2 (SCTP) para conexão do E2 Agent (gNodeB) ao E2Term do Near-RT RIC.
* **Portas `8080/TCP` e `8081/TCP`:** Endpoints HTTP `/health` e `/metrics` (Prometheus) da xApp RDL Fase 2.
* **Portas `4560/TCP` e `4561/TCP`:** Barramento RMR (RIC Message Router) de dados e rotas.
* **Portas `8082`, `8084`, `8086`:** Endpoints HTTP das 3 Reference xApps (`xslice`, `energy-saving`, `traffic-steering`).

```mermaid
graph LR
    subgraph Host["Host / WSL2"]
        K3D["Cluster k3d: rancher-lab"]
        NS3["ns-3 / 5G-LENA Simulator"]
    end

    NS3 -->|"SCTP:36422 (E2 Interface)"| K3D
    K3D -->|"HTTP:8080 / Health"| Host
    K3D -->|"HTTP:8081 / Metrics"| Host
```
"""

doc_04 = """# Volume 04: Operação, Troubleshooting e Diagnósticos da Fase 2 (CA-RDL / MARL)

**Documento:** Volume Temático 04  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Procedimento Operacional Padrão (SOP), Diagnóstico de Falhas, Streaming de Logs e Recuperação de Pods  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Procedimentos Operacionais e Diagnósticos

### 1.1. Verificar o Status dos Pods das xApps
```bash
make status-f2
# ou: kubectl get pods -n ricxapp -o wide
```

### 1.2. Inspecionar Logs do Motor MARL/MAPPO em Tempo Real
```bash
make logs-f2
# ou: kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2 -f
```

### 1.3. Validar Endpoints HTTP e Métricas Prometheus
```bash
make test-f2
```

### 1.4. Troubleshooting de Problemas Comuns
* **Pod em CrashLoopBackOff:** Verifique se as dependências PyTorch foram carregadas ou se a porta RMR está livre (`kubectl describe pod -n ricxapp -l app=ricxapp-iqos-xapp-rdl-f2`).
* **Timeout na Interface E2:** Certifique-se de que a porta SCTP `36422` está mapeada corretamente no cluster k3d.
"""

doc_06 = """# Volume 06: Observabilidade Service Mesh com Kiali e Injeção de Tráfego O-RAN

**Documento:** Volume Temático 06  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2: Context-Aware RDL (CA-RDL / MARL)  
**Escopo:** Métricas Prometheus, Telemetria Cognitiva MARL, Service Mesh Istio e Dashboard Kiali  
**Repositório Oficial:** [https://github.com/georgebarbosa3090/XApp-RDL-F2](https://github.com/georgebarbosa3090/XApp-RDL-F2)  

---

## 1. Métricas de Observabilidade Prometheus da Fase 2

A xApp RDL Fase 2 exporta métricas cognitivas e de governança na porta `8081`:

| Métrica Prometheus | Tipo | Descrição |
| :--- | :---: | :--- |
| `rdl_decision_latency_seconds` | Histogram | Tempo de inferência e arbitragem do motor MAPPO (meta < 50ms). |
| `rdl_conflicts_total` | Counter | Total de conflitos de rádio interceptados e mitigados. |
| `marl_actor_loss` | Gauge | Perda (Loss) da rede neural do Ator durante o treinamento online. |
| `marl_critic_loss` | Gauge | Perda (Loss) da rede neural do Crítico Centralizado. |
| `rdl_sla_compliance_ratio` | Gauge | Taxa percentual de cumprimento de SLA por fatia de rede. |

```mermaid
graph LR
    RDL["xApp RDL Fase 2<br/>(:8081/metrics)"] --> PROM["Prometheus Scraper"]
    PROM --> GRAFANA["Grafana / Kiali Dashboard"]
```
"""

def main():
    with open(os.path.join(P2_DIR, 'docs', '02_infraestrutura_cluster_k3d_e_rancher.md'), 'w', encoding='utf-8') as f:
        f.write(doc_02)
    with open(os.path.join(P2_DIR, 'docs', '04_operacao_troubleshooting_e_backup.md'), 'w', encoding='utf-8') as f:
        f.write(doc_04)
    with open(os.path.join(P2_DIR, 'docs', '06_observabilidade_kiali_e_injecao_trafego.md'), 'w', encoding='utf-8') as f:
        f.write(doc_06)
    print('[OK] Volumes 02, 04 e 06 atualizados com sucesso.')

if __name__ == '__main__':
    main()
