# Conformidade e evidência

| Documento | Conteúdo | Situação |
| :-- | :-- | :-- |
| [HRDL_F1_COMPATIBILITY_PROFILE.md](HRDL_F1_COMPATIBILITY_PROFILE.md) | Versões de especificação e pilhas de simulação da Fase 1 | atualizado em 2026-11-08 |
| [EXPERIMENTAL_EVIDENCE_POLICY.md](EXPERIMENTAL_EVIDENCE_POLICY.md) | O que conta como evidência, como é registrada e verificada | atualizado em 2026-11-08 |
| [ORAN_TRACEABILITY_MATRIX.md](ORAN_TRACEABILITY_MATRIX.md) | Requisito → código → teste → evidência, com o nível real de verificação | atualizado em 2026-11-08 |
| [ORAN_SC_IMPLEMENTATION_PROFILE.md](ORAN_SC_IMPLEMENTATION_PROFILE.md) | Integração com o O-RAN SC: SubMgr REST, RMR, MEID | atualizado em 2026-11-08 |
| [HRDL_F1_SRSRAN_TESTBED_PROFILE.md](HRDL_F1_SRSRAN_TESTBED_PROFILE.md) | Perfil planejado para srsRAN + Open5GS | planejamento; não executado |
| [OPENRAN_BRASIL_INTEGRATION.md](OPENRAN_BRASIL_INTEGRATION.md) | Plano de integração no testbed OpenRAN@Brasil (gates TB0–TB10) | planejamento; não executado |
| [GREENRAN_UFPA_TESTBED_PROFILE.md](GREENRAN_UFPA_TESTBED_PROFILE.md) | Papel da H-RDL no GreenRAN (testbed UFPA), o que já está no código, perguntas ao hospedeiro e gates GR1–GR4 | código pronto em 2026-11-10; nenhum gate executado |
| [MIGRATION_RELEASE5.md](MIGRATION_RELEASE5.md) | Roteiro de migração para versões mais novas das especificações | planejamento |
| [CARDL_F2_COMPATIBILITY_PROFILE.md](CARDL_F2_COMPATIBILITY_PROFILE.md) | Perfil-alvo da Fase 2 | definido no repositório XApp-RDL-F2 |
| [PHASE1_PHASE2_SYNC_CONTRACT.md](PHASE1_PHASE2_SYNC_CONTRACT.md) | Contrato de dados e de segurança entre as fases | especificação |

A fonte normativa do que é verificado é o certificador (`scripts/certification/certify_chain.py`) aplicado à política (`reproducibility/provenance_policy.yaml`) e ao lock de versões (`reproducibility/versions.lock`). Os documentos desta pasta descrevem e justificam essas regras; não substituem os vereditos.
