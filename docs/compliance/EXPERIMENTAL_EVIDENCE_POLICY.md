# Política de Evidência Experimental e Proveniência — Experimental Evidence Policy

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Documento:** `EXPERIMENTAL_EVIDENCE_POLICY.md`  
**Escopo:** Diretrizes de integridade científica, separação de fontes de dados, proibição de contaminação e firewall entre suítes de testes e experimentos de publicação.

---

## 1. A Regra de Ouro de Proveniência Científica

$$\boxed{\text{resultado científico válido} \iff \text{ns-3 + 5G-LENA + NORI + E2 real}}$$

Nenhum resultado derivado exclusivamente de modelos emulados locais, mocks em Python, vetores estáticos de teste ou execuções de demonstração pode ser incorporado às tabelas e figuras publicáveis da dissertação ou de artigos científicos.

---

## 2. Categorização Rígida das Fontes de Dados

### 2.1. Fontes Elegíveis para Publicação (`PUBLICATION_ELIGIBLE`)

| Fonte de Dados | Descrição / Origem | Nível de Evidência |
| :--- | :--- | :---: |
| **`NS3_FLOWMONITOR`** | Traces nativos XML do FlowMonitor 5G-LENA (ns-3.48). | **L5 / L6 (Científico)** |
| **`NORI_E2`** | Mensagens E2AP/E2SM (KPM e RC) de/para a E2SIM NORI. | **L5 / L6 (Científico)** |
| **`HRDL_RUNTIME`** | Telemetria bruta e logs de decisão da xApp RDL em execução real. | **L5 / L6 (Científico)** |
| **`REAL_RIC_LOG`** | Logs brutos de roteamento e sinalização do Near-RT RIC (O-RAN SC). | **L5 / L6 (Científico)** |
| **`SYSTEM_RESOURCE_TRACE`** | Métricas do sistema operacional (CPU, Memória, RTT RMR). | **L5 / L6 (Científico)** |

### 2.2. Fontes NÃO Elegíveis para Publicação (`NON_PUBLICATION`)

| Fonte de Dados | Função no Projeto | Elegibilidade para Artigo |
| :--- | :--- | :---: |
| `DISCRETE_EVENT_SIMULATOR` | Modelo discreto Python para depuração local e testes unitários. | **PROIBIDO ($\times$)** |
| `EMULATED` / `SYNTHETIC` | Workloads gerados sinteticamente sem rádio 5G. | **PROIBIDO ($\times$)** |
| `MOCK` / `CODEC_TEST` | Round-trip local de codecs ASN.1 APER. | **PROIBIDO ($\times$)** |
| `DEMO_RUN` | Execução didática em tempo real para bancas (`--demoMode=realtime`). | **PROIBIDO ($\times$)** |
| `LOCAL_GENERATOR` | Geradores locais sem traces físicos. | **PROIBIDO ($\times$)** |

---

## 3. Firewall entre Suítes de Testes e Experimentos

A arquitetura do projeto estabelece um firewall estrito entre o ambiente de testes de software e o ambiente de experimentos científicos:

```text
                  tests/ ───────────────────X───────────────────> experiments/
            (Unit / Integration / Codec)                   (Raw Traces / Scientific Publication)
```

- **Regra do Firewall:** Nenhum dado ou métrica gerada durante a execução de `tests/` pode ser copiada, vinculada ou exportada para `experiments/results/`, `statistics/`, `figures/` ou diretórios de publicação.
- **Métricas Derivadas Exclusivas:** Todas as figuras e tabelas finais devem ser derivadas por parsers read-only dos arquivos brutos salvos em `experiments/runs/` (como `flowmonitor.xml`, `conflicts.jsonl`, `decisions.jsonl` e `causal.jsonl`).

---

## 4. Auditoria Automatizada e Sincronização

A integridade desta política é verificada continuamente por auditoria estática via [`scripts/check_no_synthetic_results.py`](file:///c:/Users/georg/XApp-RDL-F1/scripts/check_no_synthetic_results.py) e pelas configurações do [`reproducibility/provenance_policy.yaml`](file:///c:/Users/georg/XApp-RDL-F1/reproducibility/provenance_policy.yaml).
