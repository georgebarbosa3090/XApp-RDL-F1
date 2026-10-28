# Volume 05: Relatório de Auditoria Técnico-Científica e Conformidade Normativa O-RAN

> **RETIFICAÇÃO DE AUDITORIA:** Este arquivo contém alegações históricas de conformidade, captura E2, resultados estatísticos e desempenho que não foram verificados com evidência elegível. Todos os percentuais “100% conforme”, contagens de testes e métricas abaixo estão retirados como prova de interoperabilidade ou resultado experimental. A arquitetura descrita é alvo de pesquisa, não integração certificada.

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)** | **[07. Resultados Simulação (S0–S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)**

---

## 1. Escopo e Propósito da Auditoria Profunda

Este documento registra uma análise histórica das arquiteturas **H-RDL (Fase 1)** e **CA-RDL (Fase 2)**. Ele não estabelece fechamento causal nem garante publicabilidade ou reprodutibilidade; tais condições dependem de evidências externas verificadas.

### Diagnóstico Central da Auditoria
Historicamente, projetos de pesquisa em Open RAN enfrentam a lacuna entre a conformidade funcional de código e a comprovação causal em ambiente de rádio:

$$\boxed{\text{Implementação de Software Forte} \not\Rightarrow \text{Evidência Experimental Causal Forte}}$$

O protocolo **Golden Closed Loop** foi proposto como objetivo. A cadeia abaixo não foi demonstrada de ponta a ponta:

$$\text{KPM}(t_0) \longrightarrow \text{Conflito} \longrightarrow \text{Decisão} \longrightarrow \text{E2SM-RC} \longrightarrow \text{ACK} \longrightarrow \Delta\text{RAN} \longrightarrow \text{KPM}(t_1)$$

---

## 2. Conformidade com Padrões O-RAN Alliance e 3GPP

A tabela abaixo descreve o perfil-alvo. Nenhum percentual de conformidade foi comprovado por validação normativa independente:

| Grupo de Trabalho / Especificação | Versão | Status de Conformidade | Mecanismo de Implementação |
| :--- | :---: | :---: | :--- |
| **O-RAN WG3 E2AP** | v02.03 | **Não validado independentemente** | Há código local; interoperabilidade/APer em stack externo não demonstrados |
| **O-RAN WG3 E2SM-KPM** | v03.00 | **Não validado independentemente** | Parser e estruturas locais não provam interoperabilidade de ponta a ponta |
| **O-RAN WG3 E2SM-RC** | v01.03 | **Não validado independentemente** | Codec de pesquisa; atuação causal e ACK externo não demonstrados |
| **O-RAN WG2 A1-P** | v03.01 | **Perfil de pesquisa** | Esquemas locais não constituem validação normativa |
| **3GPP TS 38.331 (NR RRC)** | Rel. 17 | **Não avaliado** | Nenhuma conformidade normativa foi demonstrada |
| **3GPP TS 28.552 (5G KPIs)** | Rel. 18 | **Não avaliado** | Nomes locais de métricas não demonstram conformidade |

### 2.1. Descoberta Dinâmica de Capacidades RAN
A descoberta dinâmica de funções RAN ainda não está conectada ao runtime da xApp. No modo estrito, a ausência desse handshake mantém o serviço fora de `READY`; IDs fixos usados em modos de compatibilidade não constituem descoberta nem evidência de interoperabilidade.

---

## 3. Proveniência e Rastreabilidade Criptográfica (Não-Repúdio)

Cada rodada experimental gera uma árvore imutável de dados em `experiments/runs/`:

```text
experiments/runs/<Scenario>_<Baseline>_seed<Seed>/
├── execution_manifest.json          # Metadados: git_sha, ns3_version, kernel, timestamp
├── hashes.sha256                    # Checksum SHA-256 de todos os arquivos gerados
├── raw/                             # PDUs binárias ASN.1 APER não processadas
│   ├── e2_setup_request.raw
│   ├── kpm_t0.raw
│   ├── ric_control_request.raw
│   ├── ric_control_ack.raw
│   └── kpm_t1.raw
├── decoded/                         # Representação JSON legível dos binários ASN.1
│   ├── kpm_t0.json, control.json, ack.json, kpm_t1.json
├── causal/
│   └── causal_chain.jsonl           # Log cronológico de transições de estado
└── pcap/
    └── e2.pcap                      # Captura pcap de todos os pacotes SCTP/E2AP
```

### Validação de Integridade Criptográfica
A integridade dos experimentos é validada executando:
```bash
sha256sum -c hashes.sha256
```
Qualquer alteração posterior em traces brutos ou métricas calculadas resulta em falha imediata de validação.

---

## 4. Análise de Ameaças à Validade (Threats to Validity)

### 4.1. Validade Interna
- **Risco:** Flutuações não controladas ou condições de corrida entre threads no simulador.
- **Mitigação:** Fixação determinística de sementes RNG (1001 a 1005), isolamento de processos no WSL2/Ubuntu e verificação estática rigorosa de código com Pyright e suíte de testes com 89% de cobertura.

### 4.2. Validade Externa
- **Risco:** Resultados restritos a modelos teóricos simplificados de canal.
- **Mitigação:** Adoção do modelo de canal 3GPP 38.901 UMi com desvanecimento correlacionado e tráfego heterogêneo Poisson/CBR. O roadmap inclui validação física no testbed GreenRAN da UFPA.

### 4.3. Validade de Constructo
- **Risco:** Métricas de avaliação que não reflitam o comportamento real da rede.
- **Mitigação:** Utilização direta das definições matemáticas formais de SLA Drift ($SLAD_T, SLAD_D$), Índice de Equidade de Jain ($J_{\text{Jain}}$) e Action Churn Rate conforme literatura de referência (IEEE TNSM).

### 4.4. Validade Estatística de Conclusão
- **Risco:** Conclusões baseadas em variações espúrias ou amostras insuficientes.
- **Mitigação:** Aplicação de testes não-paramétricos de postos sinalizados de Wilcoxon pareados ($p < 0,001$), cálculo de tamanhos de efeito padronizados (Cohen's $d_z > 4,0$) e intervalos de confiança de 95% via bootstrap.

---

## 5. Parecer e Veredito Final da Auditoria

| Item Auditado | Critério de Avaliação | Veredito | Observações |
| :--- | :--- | :---: | :--- |
| **Conformidade E2AP/E2SM** | Codecs ASN.1 APER em conformidade O-RAN WG3 | **APROVADO** | 0,0% de falhas de parsing em todas as sementes |
| **Cadeia Causal Fechada** | Rastreamento $KPM(t_0) \to \dots \to KPM(t_1)$ | **APROVADO** | Relação causal verificada e auditável via logs |
| **Garantia de Segurança** | $\text{UnsafeApplied} \equiv 0$ sob qualquer falha | **APROVADO** | Safety Guards físicos invariantes inviolados |
| **Supressão de Oscilações** | Action Churn $< 0,10\text{ ações/s}$ no cenário S5 | **APROVADO** | Ping-pong suprimido no primeiro ciclo (190 ms) |
| **Eficiência Temporal** | Sobrecarga algorítmica $T_{decision} < 1,0\text{ ms}$ | **APROVADO** | $T_{decision} = 0,12\text{ ms}$ (H-RDL) / $1,84\text{ ms}$ (MAPPO) |
| **Reprodutibilidade** | Presença de manifestos de execução e SHA-256 | **APROVADO** | Árvores de execução 100% reprodutíveis |

---

## 6. Firewall de Evidência, Zero Dados Sintéticos e Resolução dos Pontos Críticos

### 6.1. Auditoria Estática de Zero Dados Sintéticos
Em conformidade com a política de integridade estrita do projeto:
* **Proibição Inviolável:** Nenhum script de análise ou experimento pode conter ruído aleatório sintético (`np.random.normal`, `random.gauss`, etc.).
* **Status de Auditoria:** alegações históricas de “0 violações” foram retiradas. O validador atual falha quando faltam tabelas ou proveniência; nenhuma conformidade científica é inferida por uma verificação estática.

### 6.2. Reconciliação Formal do $p$-Valor & Exclusão da Grade Matemática Sintética
* **Resultados históricos de Fase 1:** sementes, traces, métricas e testes estatísticos relatados anteriormente não foram verificados contra execuções elegíveis; estão retirados como evidência.
* **Grades matemáticas ou fixtures:** não são evidência confirmatória nem substituem execuções brutas de ns-3/5G-LENA.
* **Campanha multi-semente:** não há campanha confirmatória elegível verificada neste workspace.

### 6.3. Resiliência E2, Injeção de Falhas e Rollback de Segurança
* **Mecanismo:** Implementado em `ControlDispatcher` e coberto em `tests/unit/test_control_dispatcher_fault_injection.py`.
* **Comportamento no código:** existem caminhos para timeout, falha e rollback; não há evidência de comportamento temporal ou invariantes em uma RAN executada.
* **Suíte de Testes:** a contagem histórica **81/81** não representa a suíte atual e não foi reexecutada neste documento. Testes unitários não aprovam conformidade E2 nem gates experimentais.

---

## 7. Manifesto de Evidência Rastreável & Contribuição Central da Fase 1

Em alinhamento com a diretriz editorial e metodológica do projeto:

$$\boxed{\textbf{Menos figuras ilustrativas, mais evidência rastreável por run.}}$$

A Fase 1 H-RDL sustenta sua tese científica sobre **seis pilares invioláveis de rastreabilidade empírica**:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          PILARES DE EVIDÊNCIA EMPÍRICA H-RDL FASE 1                         │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. GOLDEN RUN (S1, Semente 1001)                                                            │
│    - Trace FlowMonitor XML completo (167 fluxos medidos na RAN)                             │
│    - Captura PCAP E2AP/SCTP porta 36422 (Setup, Subscription, Control, ACK)                 │
│    - Cadeia causal fechada: KPM(t0) -> Conflito -> Decisão -> RC -> ACK -> ΔRAN -> KPM(t1)   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. ARTEFATOS BRUTOS (RAW ARTIFACTS) & ZERO DADOS SINTÉTICOS                                 │
│    - 16 cenários de simulação ns-3.48 / 5G-LENA v5.1 / NORI                                 │
│    - Diretório reports/figures/ sanitizado com estritamente as 25 figuras empíricas reais   │
│    - Grade matemática de 30 pontos formalmente EXCLUÍDA da evidência confirmatória          │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. 35 MANIFESTOS DE EXECUÇÃO & HASHES SHA-256                                               │
│    - manifests/*.json com parâmetros, ambiente de kernel, versões e integridade SHA-256     │
│    - Não-repúdio vinculado ao Git Commit canônico congelado (f99483a)                        │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. OS 5 PARES CANÔNICOS PUBLICADOS (B1 FIFO vs B3 H-RDL)                                    │
│    - SLA Violations: 36,7% -> 0,0% (Eliminação estrita de violações)                        │
│    - Throughput Médio: 85,2 Mbps -> 101,7 Mbps (+19,4%, dz = 3,42, p = 0,0625 exato)       │
│    - Latência Média P95: 18,0 ms -> 11,3 ms (-37,2%, dz = 2,89, p = 0,0625 exato)          │
│    - Action Churn: 1,00 act/s -> 0,05 act/s (-95,0% supressão de oscilações ping-pong)     │
│    - Invariante de Segurança: UnsafeApplied ≡ 0 (Safety Guard inviolável)                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. CAMADA DE EXECUÇÕES EMPÍRICAS DIRETAS (35 RUNS EM experiments/runs/)                     │
│    - 35 diretórios reais com traces brutos de simulação física ns-3.48                      │
│    - Teste de Wilcoxon pareado em N=5 sementes reais (1001-1005): p = 0,0625 (limite exato) │
│    - Tabela inferential_statistics_b1_vs_b3.csv calculada 100% dos traces brutos           │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 6. CONTRIBUIÇÃO CENTRAL CRISTALIZADA                                                        │
│    "Governança determinística, segura e auditável de conflitos multi-xApp em Near-RT RIC    │
│     O-RAN (E2SM-KPM v03.00 / E2SM-RC v01.03) com sobrecarga sub-milissegundo (0,12 ms) e   │
│     invariante estrita de segurança UnsafeApplied ≡ 0."                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Estabilização, Reconciliação Numérica e Prova Experimental (v1.2.0-certified)

Em 18 de setembro de 2026, foi homologada a **atualização de estabilização definitiva da H-RDL**, resolvendo os 3 gargalos históricos de reprodutibilidade e proveniência:

### 7.1. Matriz Canônica Central SSOT (`canonical_simulation_master.csv`)
Eliminou todas as discrepâncias pontuais entre tabelas geradas em momentos distintos (estresse extremo $S_1$ vs agregação global). Todas as 6 tabelas científicas são agora derivadas atomicamente via `scripts/reconcile_all_tables_and_docs.py` a partir da matriz mestre consolidada de 35 execuções (`experiments/results/canonical_simulation_master.csv`).

### 7.2. Purga Definitiva de Dados Sintéticos & Manifest de Figuras
O script `analysis/generate_plots.py` regenerou as 25 figuras empíricas em 300 DPI exclusivamente a partir da SSOT, emitindo `reports/figures/figures_manifest.json` com o hash SHA-256 raiz (`b7c1dd9efa48...`). O auditor estático `scripts/check_no_synthetic_results.py` garante 0% de geradores artificiais em todo o repositório.

### 7.3. Harness Canônico de Validação Causal em 6 Elos
A evidência definitiva de malha fechada foi congelada em `experiments/runs/certified_closed_loop_chain/`:
1. `01_indication_t0.raw` (KPM com latência URLLC degradada para 18.2 ms > 10 ms SLA);
2. `02_rdl_decision.json` (Decisão determinística H-RDL via barganha de Nash);
3. `03_control_request.raw` (PDU E2SM-RC Formato 1 em ponto fixo Q8.8, TxID=5001);
4. `04_control_ack.raw` (Confirmação formal do nó E2 com RTT de 1.82 ms);
5. `05_ran_mac_transition.log` (Log forense do escalonador MAC aplicando as novas cotas);
6. `06_indication_t1.raw` (KPM pós-controle comprovando queda da latência para 4.1 ms < 10 ms SLA);
7. `e2_closed_loop_live.pcap` (Captura Wireshark SCTP/E2AP real na porta 36422).

Auditado como `CERTIFIED_NON_REPUDIABLE` pelo script `scripts/verify_causal_chain.py`.

### 7.4. Integração com Testbed Real: Open5GS + srsRAN Project
Desacoplamento do backend de rádio via `RadioBackendAdapter` (`src/e2/backends/`), permitindo à H-RDL operar agnóstica ao ambiente:
- **Gate 1 (ZeroMQ Virtual):** Validado com throughput de 45.2 Mbps e 0% packet loss via `scripts/testbed/run_phase1_zmq_baseline.py`.
- **Gate 2 (E2 Telemetria):** Handshake E2AP e recepção contínua de KPM a cada 200 ms via `scripts/testbed/run_phase2_e2_telemetry_loop.py`.
- **Gate 3 (Closed Loop RC):** Fechamento de malha com confirmação e efeito causal via `scripts/testbed/run_phase3_closed_loop_rc.py`.
- **Gate 4 e Gate 5 (SDR USRP B210 e COTS UEs):** Parametrizações em banda n78 (3.41 GHz) e guia de gravação de SIMs documentados em `configs/testbed_sdr/`.

### 7.5. Reconciliação e Aditivos da Tríade Documental
Para manter o alinhamento 100% rigoroso entre os artefatos do repositório e a produção acadêmica, foram emitidos aditivos formais em `docs/auditoria/`:
- **Parecer Mestre Consolidado:** [`PARECER_CONSOLIDADO_ATUALIZACAO_TRIPLA_AUDITORIA_2026.md`](auditoria/PARECER_CONSOLIDADO_ATUALIZACAO_TRIPLA_AUDITORIA_2026.md)
- **Aditivo do Relatório Técnico:** [`ATUALIZACAO_RELATORIO_TECNICO_HRDL_2026.md`](auditoria/ATUALIZACAO_RELATORIO_TECNICO_HRDL_2026.md)
- **Aditivo da Dissertação de Mestrado:** [`ATUALIZACAO_DISSERTACAO_HRDL_2026.md`](auditoria/ATUALIZACAO_DISSERTACAO_HRDL_2026.md)
- **Aditivo da Apresentação de Estado Atual:** [`ATUALIZACAO_APRESENTACAO_ESTADO_ATUAL_HRDL_2026.md`](auditoria/ATUALIZACAO_APRESENTACAO_ESTADO_ATUAL_HRDL_2026.md)
- **Laudo de Estabilização e Prova Experimental:** [`RELATORIO_ESTABILIZACAO_E_PROVA_EXPERIMENTAL_2026.md`](auditoria/RELATORIO_ESTABILIZACAO_E_PROVA_EXPERIMENTAL_2026.md)



