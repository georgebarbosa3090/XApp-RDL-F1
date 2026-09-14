# Volume 11: Relatório de Execução e Validação Experimental dos Cenários S0 a S15

> **Navegação do Projeto:** [Vol 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md) | [Vol 10: Estudo Científico](10_estudo_cientifico_xapps_relacoes_conflitos_e_normas.md) | **[Vol 11: Validação S0 a S15]**

**Documento:** Volume Temático 11 — Relatório Consolidado de Execução e Benchmark dos Cenários S0 a S15  
**Projeto:** xApp RDL (Resource and Decision Layer) — Fases 1 (H-RDL) e 2 (CA-RDL)  
**Autor:** George Alexandro F. Barbosa (PPGC/UFPA)  
**Data:** Setembro de 2026  
**Status:** Resultados Empíricos Validados (100% dos 16 Cenários Aprovados em H-RDL e CA-RDL)

---

## 1. Resumo Executivo da Campanha Experimental

A suíte experimental completa, composta por **16 cenários formais de controle e mitigação de conflitos (S0 a S15)**, foi executada e validada em três paradigmas operacionais:
1. **Baseline Descoordenado (Sem RDL):** Ações das xApps são aplicadas diretamente na RAN sem mediação.
2. **H-RDL (Fase 1 — Heurística Determinística):** Mediação por janela em lote ($\Delta t = 200\text{ ms}$), modelos analíticos 5G (Shannon, $M/G/1$, Earth) e barreiras físicas (*Safety Guards*).
3. **CA-RDL (Fase 2 — Cognitivo Multi-Agente):** Mediação por Aprendizado por Reforço Multi-Agente (MAPPO) com grafos contextuais heterogêneos (GNN / GraphSAGE) e *Shielded RL*.

---

## 2. Segmentação Temática dos Cenários de Validação

Para assegurar clareza metodológica e permitir tanto execuções integradas quanto avaliações segmentadas, a suíte de 16 cenários é estruturada em dois grupos tecnológicos formais:

### 2.1. Grupo 1: Redes Terrestres Tradicionais e Slicing 5G (S0 a S8)

Focado na governança de rádio em redes celulares terrestres 3GPP Rel-15/16/17, multiplexação de fatias de rede (eMBB/URLLC), eficiência energética e resiliência da interface E2.

| ID | Nome do Cenário | Tipo de Conflito O-RAN | Impacto Técnico no Baseline | Resolução H-RDL / CA-RDL |
| :--- | :--- | :--- | :--- | :--- |
| **S0** | *Clean Control Baseline* | Sem conflito (Ortogonal) | Operação nominal sem intervenção. | Pass-through limpo de ações ortogonais sem interferência. |
| **S1** | *Direct PRB Resource Collision* | Direto (`PRB_QUOTA` overlap) | Sobrealocação ($110\%$) causa descarte massivo de pacotes. | Eliminação da colisão com clamp estrito em $100\%$ ($F_1 = 1.0$). |
| **S2** | *Energy Saving vs QoS (EEVS)* | Indireto (`TX_POWER` vs Throughput) | Redução de potência colapsa vazão de dados em $52\%$. | Arbitragem de Shannon: vazão $\ge 24.5\text{ Mbps}$ com $18\%$ de economia. |
| **S3** | *Multi-Slice TVS Trade-off* | Indireto (`HO_MARGIN` vs QCI SLA) | Latência URLLC degrada para $> 35\text{ ms}$ (quebra de SLA). | Proteção estrita de URLLC ($< 5\text{ ms}$) com equidade Jain $J = 0.88$. |
| **S4** | *TS vs Energy Saving* | Cruzado (Offloading vs Sleep) | Desvio de $14$ sessões para célula desligada (*dropped calls*). | Coordenação espacial impede envio de tráfego para célula adormecida. |
| **S5** | *Ping-Pong Suppression* | Temporal (Oscilação de Handover) | Taxa de ping-pong de $48\%$, gerando sinalização excessiva. | Histerese temporal ($\Delta t \ge 1000\text{ ms}$) suprime $> 85\%$ das trocas. |
| **S6** | *Conflict Storm L0-L4* | Múltiplo Concorrente (50 ações) | Sobrecarga de buffer no RIC com latência de resposta $> 450\text{ ms}$. | Processamento em lote mantendo latência $< 50\text{ ms}$ (tempo real). |
| **S7** | *Fault Injection & Adversarial* | Injeção de Falhas / Comandos Ilegais | Risco de dano físico e saturação de RF ($P_{\text{tx}} = 100\text{ dBm}$). | Escudo de segurança L0-L4 bloqueia $100\%$ das ações perigosas. |
| **S8** | *NORI Closed-Loop Causal Proof* | Fechamento de Malha E2 | Inconsistência assíncrona entre telemetria e ação de controle. | Fechamento causal validado com telemetria KPM e confirmação RC ACK. |

---

### 2.2. Grupo 2: Redes Avançadas 5G-Advanced e 6G (S9 a S15)

Focado em cenários tridimensionais, redes não-terrestres (NTN), mobilidade extrema, sensoriamento e comunicação integrados (ISAC), automação industrial determinística e segurança zero-trust.

| ID | Nome do Cenário | Domínio Tecnológico 6G | Impacto Técnico no Baseline | Resolução H-RDL / CA-RDL |
| :--- | :--- | :--- | :--- | :--- |
| **S9** | *NTN Orbital Handover & Doppler* | Satélites LEO / NTN 3GPP | Efeito Doppler e handover inadequado causam queda de enlace. | Janela de histerese adaptada ($\Delta t = 3000\text{ ms}$) alinhada à órbita. |
| **S10**| *UAV Swarm Battery Emergency* | Drones e gNodeBs Aéreas | Queda abrupta de drone por bateria causa apagão em 25 UEs. | Descarregamento proativo e seguro de tráfego antes da exaustão. |
| **S11**| *High-Speed V2X Platooning* | Comunicações Veiculares C-V2X | Latência interveicular $> 20\text{ ms}$ quebra sincronismo do comboio. | Handover preditivo sem interrupção para comboios a 120 km/h. |
| **S12**| *IIoT Zero-Jitter Robotic Slicing*| Automação Industrial e TSN | Jitter de robótica $> 15\text{ ms}$ causa descalibração de braço fabril. | Preempção determinística estrita garantindo jitter $< 0.8\text{ ms}$. |
| **S13**| *Emergency SAGIN Disaster Rescue*| Redes Espaço-Ar-Solo (SAGIN) | Telemetria de resgate bloqueada por congestionamento civil. | Prioridade humanitária estrita sobrepõe tráfego convencional. |
| **S14**| *ISAC Radar-Comm Beamforming* | Sensoriamento e Comunicação ISAC | Cegueira de radar ou perda de $60\%$ na capacidade de comunicação. | Otimização multiobjetivo de Pareto dividindo feixes espectrais. |
| **S15**| *Rogue NTN Feeder Hijacking* | Segurança O-RAN Zero-Trust | Saturação de transponder satelital e sequestro malicioso de feeder. | Rejeição instantânea pelo Cross-Tier Shield e isolamento do atacante. |

---

## 3. Matriz Consolidada de Resultados e Desempenho

| ID | Cenário | Baseline (Sem RDL) | H-RDL (Fase 1) | CA-RDL (Fase 2) | Latência de Decisão | Métrica Chave Obtida |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **S0** | Clean Control Baseline | **PASS** | **PASS** | **PASS** | $0.03\text{ ms}$ | Interferência = 0.0 |
| **S1** | Direct PRB Resource Collision | **FAIL** | **PASS** | **PASS** | $0.05\text{ ms}$ | $F_1 = 1.0$ (Cota contida em 100%) |
| **S2** | Energy Saving vs QoS (EEVS) | **FAIL** | **PASS** | **PASS** | $0.07\text{ ms}$ | Throughput $\ge 24.5\text{ Mbps}$ (-18% Energia) |
| **S3** | Multi-Slice TVS Trade-off | **FAIL** | **PASS** | **PASS** | $0.02\text{ ms}$ | Latência URLLC $< 5\text{ ms}$ ($J = 0.88$) |
| **S4** | TS vs Energy Saving | **FAIL** | **PASS** | **PASS** | $0.04\text{ ms}$ | 0 Chamadas Caídas (*Zero Drops*) |
| **S5** | Ping-Pong Suppression | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | $> 85\%$ de trocas espúrias suprimidas |
| **S6** | Conflict Storm L0-L4 | **FAIL** | **PASS** | **PASS** | $5.81\text{ ms}$ | Envelope Near-RT mantido ($< 50\text{ ms}$) |
| **S7** | Fault Injection & Adversarial | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | 100% de comandos ilegais rejeitados |
| **S8** | NORI Closed-Loop Causal Proof | **FAIL** | **PASS** | **PASS** | $0.00\text{ ms}$ | Eficácia Causal $CRE = 100\%$ |
| **S9** | NTN Orbital Handover & Doppler | **FAIL** | **PASS** | **PASS** | $0.02\text{ ms}$ | Handover orbital estável em janela LEO |
| **S10**| UAV Swarm Battery Emergency | **FAIL** | **PASS** | **PASS** | $0.02\text{ ms}$ | Offloading térmico/bateria sem quedas |
| **S11**| High-Speed V2X Highway Platooning| **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | Comboio sincronizado com atraso $< 5\text{ ms}$ |
| **S12**| IIoT Zero-Jitter Robotic Slicing | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | Jitter determinístico $< 0.8\text{ ms}$ |
| **S13**| Emergency SAGIN Disaster Rescue | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | Tráfego humanitário com preempção total |
| **S14**| ISAC Radar-Comm Beamforming | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | Divisão espectral na fronteira de Pareto |
| **S15**| Rogue NTN Feeder Hijacking | **FAIL** | **PASS** | **PASS** | $0.01\text{ ms}$ | Isolamento topológico de xApp maliciosa |

---

## 4. Roteiro de Execução das Simulações e Validações

O ambiente foi projetado para oferecer três modalidades de execução, garantindo flexibilidade operacional:

### 4.1. Modo 1: Automatizado em Lote (All-in-One)
Executa toda a suíte de 16 cenários sequencialmente de ponta a ponta:

Execução do validador formal Python:
```bash
/home/george/.venv-rdl/bin/python scripts/validate_all_scenarios_s0_s15.py --group all
```

Execução em lote de todas as co-simulações C++ no ns-3:
```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh all
```

---

### 4.2. Modo 2: Execução por Grupo Tecnológico (5G vs 6G)
Permite particionar a carga computacional e analisar separadamente redes terrestres e redes avançadas:

Execução apenas do Grupo 1 (Redes Terrestres Tradicionais e Slicing 5G — S0 a S8):
```bash
/home/george/.venv-rdl/bin/python scripts/validate_all_scenarios_s0_s15.py --group 5g
```

Execução no ns-3 apenas do Grupo 1:
```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh 5g
```

Execução apenas do Grupo 2 (Redes Avançadas 5G-Advanced e 6G — S9 a S15):
```bash
/home/george/.venv-rdl/bin/python scripts/validate_all_scenarios_s0_s15.py --group 6g
```

Execução no ns-3 apenas do Grupo 2:
```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh 6g
```

---

### 4.3. Modo 3: Execução Modular Cenário a Cenário (Individual)
Recomendado para inspeção minuciosa de traces, depuração de parâmetros E2SM e preservação de recursos de CPU/RAM em máquinas limitadas:

Validação individual de um cenário específico via Python:
```bash
/home/george/.venv-rdl/bin/python scripts/validate_all_scenarios_s0_s15.py --scenario S1
```

Execução de um cenário de co-simulação C++ individual no ns-3:
```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh S1
```

Execução de cenário 6G específico (exemplo ISAC Radar-Comm):
```bash
bash simulations/ns3/run_all_s0_s15_simulations.sh S14
```

---

## 5. Conclusão

* **H-RDL (Fase 1):** Aprovado com **100% de sucesso (16/16 cenários)**, assegurando determinismo, conformidade aos padrões O-RAN WG2/WG3 e latência de decisão inferior a $10\text{ ms}$ mesmo sob condições extremas de estresse (*Conflict Storm*).
* **CA-RDL (Fase 2):** Aprovado com **100% de sucesso (16/16 cenários)**, demonstrando adaptação contínua e generalização em ambientes heterogêneos 5G-Adv/6G sob a supervisão do *Safety Shield*.
* **Resiliência:** Em 15 dos 16 cenários, o *Baseline Descoordenado* entra em falha crítica ou violação de SLA, comprovando a necessidade imperativa da camada RDL em redes abertas inteligentes.

---

-> **[Volume 01: Arquitetura Core](01_arquitetura_e_modelagem_matematica.md)** | **[Volume 10: Estudo Científico das xApps](10_estudo_cientifico_xapps_relacoes_conflitos_e_normas.md)** | [Portal de Documentação](README.md)
