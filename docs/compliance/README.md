# Diretório de Conformidade e Integridade Experimental — docs/compliance/

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Escopo:** Documentos de conformidade normativa O-RAN ALLIANCE, perfis de implantação O-RAN SC, matriz de rastreabilidade, política de proveniência de dados e roadmap do O-RAN Release 5.

---

## Documentos do Diretório

1. **[Perfil de Compatibilidade Congelado (H-RDL F1 Profile)](HRDL_F1_COMPATIBILITY_PROFILE.md)**
   - Definição formal das versões congeladas da Fase 1 (`E2AP v02.03`, `E2SM-KPM v03.00`, `E2SM-RC v01.03`, O-RAN SC Release J, ns-3.48, 5G-LENA v5.1 e NORI).

2. **[Matriz de Rastreabilidade O-RAN (ORAN Traceability Matrix)](ORAN_TRACEABILITY_MATRIX.md)**
   - Mapeamento formal entre especificações O-RAN (WG2/WG3), codecs do H-RDL, suíte de testes e os 6 Gates de Evidência Experimental ($G_0$ a $G_6$).

3. **[Perfil de Implantação O-RAN SC (ORAN SC Implementation Profile)](ORAN_SC_IMPLEMENTATION_PROFILE.md)**
   - Especificação dos endpoints REST do Subscription Manager, portas RMR (`:4560`, `:38000`), tabelas de rotas e códigos de procedimento E2AP.

4. **[Política de Evidência Experimental e Proveniência (Experimental Evidence Policy)](EXPERIMENTAL_EVIDENCE_POLICY.md)**
   - Regras de integridade científica, firewall entre testes e experimentos, e definição de fontes elegíveis para publicação (`PUBLICATION_ELIGIBLE` vs `NON_PUBLICATION`).

5. **[Roadmap de Migração para O-RAN Release 5 (Migration to Release 5)](MIGRATION_RELEASE5.md)**
   - Planejamento de transição para KPM v08.00 e RC v10.00 na branch `feature/oran-release5-profile` após o encerramento da Fase 1.

6. **[Perfil de Compatibilidade da Fase 2 (CA-RDL F2 Profile)](CARDL_F2_COMPATIBILITY_PROFILE.md)**
   - Perfil estratégico da Fase 2 (Context-Aware RDL, especificações O-RAN Release 5, modelos MARL/MAPPO, GNN e cenários avançados $S_9 \dots S_{15}$).

7. **[Contrato de Sincronização Fase 1 e Fase 2 (Phase 1 / Phase 2 Sync Contract)](PHASE1_PHASE2_SYNC_CONTRACT.md)**
   - Contrato formal de interfaces, estabilidade de esquemas de dados (`RDLDecision`, `XAppAction`, `ConflictSet`), protocolo de fallback e diretrizes de repositório entre `XApp-RDL-F1` e `XApp-RDL-F2`.

