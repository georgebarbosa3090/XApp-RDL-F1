# Relatório Experimental e Rastreabilidade do ns-3 FlowMonitor (Cenários S0 a S15)

## 1. Proveniência e Conformidade Estrita com o FlowMonitor

Este relatório é compilado diretamente a partir dos artefatos XML e CSV gerados pelo módulo `FlowMonitor` do simulador **ns-3.48 / 5G-LENA v5.1 / NORI** durante a execução da suíte de cenários.

* **Diretório de Traces Brutos:** `C:\Users\george.barbosa\.gemini\antigravity\scratch\iqos-xapp-rdl-phase1\experiments\results\s0_s15_simulations`
* **Total de Arquivos XML Encontrados:** 0
* **Total de Arquivos CSV Encontrados:** 0

---

## 2. Tabela Consolidada de Métricas Físicas por Cenário

| Cenário / Arquivo | Fluxos Monitorados | Pacotes TX | Pacotes RX | Pacotes Perdidos | PDR (%) | Latência Média (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| *Nenhum XML de FlowMonitor detectado ainda no diretório de resultados* | - | - | - | - | - | - |

---

## 3. Detalhamento dos Fluxos por Cenário

---

## 4. Instruções para Regeneração dos Traces

Para reexecutar a suíte no ns-3 e reprocessar este documento:

```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh all
python3 scripts/generate_ns3_flowmonitor_markdown_report.py
```

---

## 5. Como Sincronizar e Subir os Resultados para o GitHub

Após rodar os testes ou simulações, você pode subir todos os resultados usando qualquer uma das opções abaixo:

### Opção A: Via Atalho Make (Recomendado)
```bash
make push-results
```

### Opção B: Manual via Git
```bash
git add experiments/results/ docs/
git commit -m "chore(sim): update ns-3 FlowMonitor experimental traces and reports"
git push origin main
```
