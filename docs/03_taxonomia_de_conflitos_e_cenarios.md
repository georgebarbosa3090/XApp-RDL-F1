# Volume 03: Taxonomia de Conflitos Multi-xApp e Portfólio de Cenários (S0 a S15)

> **Navegação da Documentação Consolidada:**  
> **[01. Arquitetura & Modelagem](01_arquitetura_e_modelagem.md)** | **[02. Guia Operacional & Deploy](02_guia_operacional_deploy_e_simulacao.md)** | **[03. Taxonomia de Conflitos & Cenários](03_taxonomia_de_conflitos_e_cenarios.md)** | **[04. Relatório Científico Mestre](04_relatorio_cientifico_mestre_rdl.md)** | **[05. Auditoria & Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)** | **[06. Roadmap & Futuro 6G](06_roadmap_e_pesquisa_futura_6g.md)**

---

## 1. Taxonomia Unificada de Conflitos em Open RAN

A desagregação do plano de controle no Near-RT RIC permite que múltiplas xApps operem de forma autônoma sobre a mesma infraestrutura de rádio. Esta coexistência engendra 5 classes fundamentais de conflitos:

```
                              ┌─────────────────────────────────────────┐
                              │     TAXONOMIA DE CONFLITOS O-RAN        │
                              └────────────────────┬────────────────────┘
                                                   │
         ┌───────────────────┬─────────────────────┼─────────────────────┬───────────────────┐
         │                   │                     │                     │                   │
┌────────▼────────┐ ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐ ┌────────▼────────┐
│ Conflito Direto │ │Conflito Indireto│   │Conflito Implíct.│   │Conflito Temporal│ │ Conflict Storm  │
│(Mesmo Parâmetro)│ │(Coupled Slices) │   │(Grafo Semântico)│   │ (Ping-Pong/Osc) │ │(Carga > 50 act/s│
└─────────────────┘ └─────────────────┘   └─────────────────┘   └─────────────────┘ └─────────────────┘
```

### 1.1. Conflito Direto (Direct Collision)
Ocorre quando duas ou mais xApps emitem solicitações simultâneas para alterar o mesmo parâmetro de rádio no mesmo nó (`cell_id`) com valores incompatíveis.
- **Exemplo Clássico:** *xSlice* solicita `PRB_QUOTA = 80%` para a fatia URLLC enquanto *Energy Saving* solicita `PRB_QUOTA = 30%` ou corte de potência para a mesma célula.
- **Resolução H-RDL:** Arbitragem determinística ponderada pela criticidade de SLA (TVS/EEVS).

### 1.2. Conflito Indireto (Indirect / Coupled Conflict)
Ocorre quando xApps atuam em parâmetros formalmente distintos, mas que compartilham o mesmo gargalo físico de canal ou interferem no mesmo KPI.
- **Exemplo Clássico:** *Traffic Steering* migra UEs para uma célula vizinha para aliviar carga, provocando saturação oculta de buffer RLC e elevação do atraso HOL em fatias URLLC pré-existentes.
- **Resolução CA-RDL:** Modelagem contextual com inferência de dependência de fatias.

### 1.3. Conflito Implícito e Semântico (Semantic / Implicit Conflict)
Ocorre quando parâmetros de camadas diferentes possuem correlação cruzada não óbvia (e.g., tilt elétrico de antena vs limiares de handover A3-Offset).
- **Resolução CA-RDL:** Rastreamento estrutural via Grafo de Conhecimento (*Knowledge Graph*).

### 1.4. Conflito Temporal (Parameter Flipping / Ping-Pong)
Ocorre quando o fechamento de malha reativo induz um ciclo infinito de decisões opostas entre xApps antagônicas ($40\% \to 70\% \to 40\% \to 70\%$).
- **Resolução H-RDL:** Introdução de janela de resfriamento proativa (*Cooling Window* $\ge 1000\text{ ms}$) e memória de estados.

### 1.5. Tempestade de Conflitos (Conflict Storm)
Ocorre sob sobrecarga extrema da interface de controle ($\ge 50\text{ propostas/s}$), demandando agregação em lote e poda computacional para evitar saturação do Near-RT RIC.

---

## 2. Portfólio Completo de Cenários Experimentais (S0 a S15)

A suíte experimental engloba 16 cenários modelados no simulador ns-3.48 / 5G-LENA / NORI:

| Cenário ID | Denominação do Cenário | Classe de Conflito | xApps Envolvidas | Parâmetros de Rádio Impactados |
| :---: | :--- | :--- | :--- | :--- |
| **S0** | Baseline Pass-Through | Sem Conflito | Single xApp | Operação nominal em linha de base |
| **S1** | Colisão Direta de PRB | Direto | xSlice × Energy Saving | `PRB_QUOTA` (URLLC vs eMBB) |
| **S2** | Trade-Off Potência vs QoS | Direto / Indireto | Energy Saving × QoS | `TX_POWER` vs `MCS_TARGET` |
| **S3** | Multi-Slice TVS Coupling | Indireto | xSlice (URLLC) × xSlice (eMBB) | Particionamento de Recursos BWP |
| **S4** | Traffic Steering vs Green RAN | Indireto / Semântico| Traffic Steering × Energy Saving | `HANDOVER_TRIGGER` vs `TX_POWER` |
| **S5** | Ping-Pong Temporal Cíclico | Temporal | xSlice × Energy Saving | Oscilação contínua de `PRB_QUOTA` |
| **S6** | Conflict Storm (Sobrecarga) | Concorrência Extrema| 5 xApps Sintéticas | 50 propostas simultâneas por segundo |
| **S7** | Injeção de Falhas na Interface E2 | Resiliência E2 | xApp RDL × E2 Termination | Timeouts SCTP e perda de ACK |
| **S8** | Closed-Loop Co-Simulação NORI | Malha Fechada E2 | xApp RDL × Agente E2 C++ | Telemetria KPM $\leftrightarrow$ Controle RC |
| **S9** | Handover Orbital NTN | Doppler / Mobilidade | NTN Mobility × QoS | Compensação Doppler e Handover LEO |
| **S10** | Enxame de VANTs Conectados | Restrição de Energia| UAV Trajectory × Energy | Potência de Transmissão e Bateria UAV |
| **S11** | Pelotão V2X em Rodovia | Ultra-Baixa Latência| V2X Safety × Platoon Mgmt | Sidelink / Latência $< 5\text{ ms}$ |
| **S12** | IIoT / TSN Jitter Zero | Sincronismo Crítico | TSN Slicing × Industrial QoS | Escalonamento Determinístico de Slots |
| **S13** | SAGIN Resgate em Desastres | Multi-Domínio | Space-Air-Ground Federation | Alocação Híbrida Satélite-UAV-Terrestre |
| **S14** | ISAC Radar vs Comunicações | Interferência Espectral| ISAC Sensing × eMBB Comm | Forma de Onda Compartilhada e Feixes |
| **S15** | Rogue NTN Feeder Hijacking | Segurança Zero-Trust| Security Guard × Rogue Feeder | Isolamento e Quarentena de Ações |

---

## 3. Detalhamento dos Cenários Canônicos e Avançados

### 3.1. Cenário S1: Conflito Direto de Cotas de PRB
- **Topologia:** 1 gNodeB Tri-Setor ($f_c = 3,5\text{ GHz}$, $BW = 100\text{ MHz}$), 30 UEs (10 URLLC, 20 eMBB).
- **Dinâmica do Conflito:** A xApp de QoS solicita alocação de 80% dos PRBs para a fatia 1. Simultaneamente, a xApp de Economia de Energia solicita redução de cota para 30% a fim de desativar amplificadores.
- **Resultado RDL:** A H-RDL arbitra a cota ótima em 60%, garantindo 100% dos SLAs de latência ($\le 5\text{ ms}$) e vazão sem degradação do sistema.

### 3.2. Cenário S5: Ping-Pong Temporal e Supressão de Churn
- **Dinâmica:** Sem coordenação (B0), a cada 200 ms as xApps reagem às métricas KPM da rodada anterior, alternando cotas entre 40% e 70%, gerando *Action Churn* de 1,00 ação/s e instabilidade crônica de rádio.
- **Atuação RDL:** O mecanismo de *Cooling Window* estabiliza a decisão em $t = 190\text{ ms}$, reduzindo o Churn para 0,05 ações/s com 0 reversões.

### 3.3. Cenário S9 a S15: Cenários Avançados 5G-Adv/6G
- **S9 (NTN):** Modela satélites LEO em órbita polar a 600 km, corrigindo desvios Doppler de até $\pm 40\text{ kHz}$ com handover proativo entre feixes.
- **S11 (V2X):** Garante prioridade absoluta para mensagens de alerta de frenagem de emergência (*Cooperative Awareness Messages* - CAM) sob densidade veicular elevada.
- **S15 (Zero-Trust):** Detecta desvios estatísticos de propostas de controle maliciosas (Rogue xApps) e aplica quarentena automática sem comprometer a estabilidade da RAN.

---

## 4. Integração com xApps de Referência Abertas

A camada RDL é validada contra 3 xApps de código aberto consolidadas na literatura O-RAN:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          xApps DE REFERÊNCIA ABERTAS                        │
├──────────────────────────┬──────────────────────────┬───────────────────────┤
│ xSlice (QoS & Slicing)   │ Energy Saving (GreenRAN) │ Traffic Steering (TS) │
│ Repositório:             │ Repositório:             │ Repositório:          │
│ peihaoY/xslice-oran      │ Orange / ns-O-RAN-flexric│ o-ran-sc/ric-app-ts   │
├──────────────────────────┼──────────────────────────┼───────────────────────┤
│ Solicita: PRB_QUOTA      │ Solicita: TX_POWER / SLEEP│ Solicita: HANDOVER   │
│ Prioridade: 90 (Alta)    │ Prioridade: 65 (Média)   │ Prioridade: 80 (Alta) │
└──────────────────────────┴──────────────────────────┴───────────────────────┘
```
