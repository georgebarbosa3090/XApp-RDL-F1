# Perfil de Compatibilidade da Fase 2 — CA-RDL F2 Compatibility Profile

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 2 (CA-RDL Context-Aware & MARL)  
**Documento:** `CARDL_F2_COMPATIBILITY_PROFILE.md`  
**Status:** **EM CONSTRUÇÃO / DEFINIÇÃO ESTRATÉGICA (Fase 2 Target)**  
**Escopo:** Definição formal das versões normativas, especificações O-RAN ALLIANCE Release 5, aprendizado por reforço multiagente (MAPPO/MARL), motores de contexto (Knowledge Graph) e cenários avançados $S_9 \dots S_{15}$ para a Fase 2.

---

## 1. Visão Geral e Relação com a Fase 1 (H-RDL)

A Fase 2 (**CA-RDL**) expande a camada de mediação determinística congelada na Fase 1 (**H-RDL**) introduzindo cognição contextual, grafos de conhecimento (*Knowledge Graphs - KG*) e Aprendizado por Reforço Multiagente (**MAPPO / GNN**).

$$\boxed{\text{Fase 1 (H-RDL Determinístico)} \quad \xrightarrow[\text{Contrato de Segurança}]{} \quad \text{Fase 2 (CA-RDL Context-Aware & MARL)}}$$

- A Fase 1 provê o **lower bound** de segurança física (Safety Guards determinísticos, mitigação contra estouro de PRBs, anti-ping-pong e limites de potência em dBm).
- A Fase 2 atua sobre o espaço de soluções viáveis refinado pela Fase 1, otimizando a distribuição de recursos sob incerteza temporal e cenários dinâmicos complexos.

---

## 2. Parâmetros do CA-RDL F2 Profile

```yaml
profile_name: "CA-RDL F2 Compatibility Profile"
status: "ACTIVE_EVOLUTION"
phase1_compatibility_layer: "H-RDL Core 1.1.x (Deterministic Safety Fallback)"
e2ap_target_version: "v03.01"
e2sm_kpm_target_version: "v08.00"
e2sm_rc_target_version: "v10.00"
oran_sc_release_target: "Empirically Validated Release (Post-J)"
ns3_version: "3.48"
lena_version: "v5.1"
nori_commit: "9b64c12"
decision_window_ms: 200
marl_algorithm: "MAPPO (Multi-Agent PPO) + GNN Context Engine"
target_scenarios: "S9 a S15 (NTN, UAV, V2X, IIoT, ISAC)"
```

---

## 3. Matriz de Evolução de Especificações Normativas

| Componente | Fase 1 (H-RDL Frozen) | Fase 2 (CA-RDL Target) | Escopo de Expansão no CA-RDL |
| :--- | :---: | :---: | :--- |
| **E2AP** | `v02.03` | `v03.01` | Suporte a mensagens estendidas de controle e tratamento robusto de erros. |
| **E2SM-KPM** | `v03.00` | `v08.00` | Mapeamento de KPIs 3GPP 28.552 estendidos, fatias dinâmicas e telemetria NTN/V2X. |
| **E2SM-RC** | `v01.03` | `v10.00` | Estilos adicionais de controle, MIMO massivo, beamforming dinâmico e handover guiado por contexto. |
| **Cognição** | Regras TVS/EEVS | MAPPO + GNN + KG | Arbitragem aprendida e otimização contextual de utilidade multiobjetivo. |
| **Cenários** | $S_0 \dots S_8$ | $S_9 \dots S_{15}$ | Redes não-terrestres (NTN), drones (UAV), veículos (V2X), IIoT de ultra-baixa latência e ISAC. |

---

## 4. Garantia de Retrocompatibilidade e Não-Contaminação

1. **Separação Estrita de Repositórios e Branches:**
   - O código principal da Fase 1 reside em `XApp-RDL-F1` (`georgebarbosa3090/XApp-RDL-F1`).
   - O código de exploração MARL da Fase 2 reside em `XApp-RDL-F2` (`georgebarbosa3090/XApp-RDL-F2`).
2. **Safety Guard Barrier:**
   - Em nenhuma hipótese uma política MARL da Fase 2 pode violar as restrições impostas pelo `RefinementAgent` da Fase 1.
   - Qualquer ação proposta pelo modelo MARL que falhe na verificação determinística do `RefinementAgent` é rejeitada ou ajustada (*clamped*) para o valor seguro.

---

## 5. Portões de Qualidade e Conformidade Estrita (F2-G0 .. F2-G12)

| Portão | Nome do Portão | Descrição do Critério de Aceitação Normativo | Status de Maturidade |
| :--- | :--- | :--- | :---: |
| **F2-G0** | Zero Sintético | Zero dados sintéticos em publicação; proveniência validada por hash SHA-256. | **UNIT_VALIDATED (Software Firewall PASS)**<br/>*Scientific Data Provenance: PENDING (ns-3)* |
| **F2-G1** | Cobertura de Testes | Suíte de testes unitários e de integração (84/84 PASS, 73% stmts covered). | **UNIT_VALIDATED (84/84 PASS)**<br/>*Measured Statement Coverage: 73% (Target >85% PENDING)* |
| **F2-G2** | Determinismo Estrito | Inicializações determinísticas e sementes fixadas para reprodutibilidade. | **UNIT_VALIDATED** |
| **F2-G3** | Integridade de Codificação | Ausência total de caracteres UTF-8 BOM (`U+FEFF`) no código-fonte. | **IMPLEMENTED** |
| **F2-G4** | Constantes RMR / E2AP | RMR Message Types alinhados com E2AP v03.01 (12040 REQ, 12041 ACK, 12042 FAIL). | **IMPLEMENTED** |
| **F2-G5** | Dimensões MARL Canônicas | Dimensões unificadas do espaço MARL (6 agentes, 60 observações, 7 ações). | **IMPLEMENTED** |
| **F2-G6** | RMR Resiliente e Dry-Run | Respeito estrito a `control.dry_run`, tratamento APER raw e sem leak em dry-run. | **LOCALLY_INTEGRATED** |
| **F2-G7** | Proveniência E2AP/E2SM | Rastreabilidade dos provedores de protocolo com validação de manifesto. | **LOCALLY_INTEGRATED** |
| **F2-G8** | Tipagem Estrita e Pyright | Código limpo sem exceções de importação ou erros de tipagem no Pyright. | **NOT VERIFIED (Missing in CI)** |
| **F2-G9** | Conformidade de API MARL | Assinaturas de métodos unificadas em `MAPPOAgent` e `MAPPOCoordinator`. | **IMPLEMENTED** |
| **F2-G10** | Sincronização F1-F2 | Validação automatizada e sincronia bidirecional entre H-RDL F1 e CA-RDL F2. | **LOCALLY_INTEGRATED** |
| **F2-G11** | Convergência MARL | Manifesto de treinamento e salvamento de checkpoints (`actor.pt`, `training_manifest.json`). | **UNIT/ALGORITHMIC PIPELINE PASS**<br/>*RAN Environmental Convergence: PENDING* |
| **F2-G12** | Blueprint OpenRAN-BR v3 | Compatibilidade com o perfil OpenRAN@Brasil Blueprint v3. | **PROFILE READY**<br/>*External Validation: PENDING* |


