# Perfil-alvo da Fase 2 (CA-RDL)

**Situação:** definição. O código e os gates da Fase 2 vivem no repositório `georgebarbosa3090/XApp-RDL-F2`; este documento registra apenas o que a Fase 1 assume sobre ela. Nenhum status de gate da Fase 2 é verificado neste repositório.

## 1. Relação com a Fase 1

A Fase 2 acrescenta contexto (grafo de conhecimento) e arbitragem aprendida (MAPPO com GNN) sobre a H-RDL. A Fase 1 permanece como barreira de segurança: toda ação proposta pela Fase 2 passa pelo `Refinement` da Fase 1 (limites, histerese, slew-rate) e é rejeitada se violá-lo.

## 2. Alvos declarados

```yaml
phase1_layer: H-RDL (Refinement como barreira obrigatória)
e2ap: v03.01
e2sm_kpm: v08.00
e2sm_rc: v10.00
decision_window_ms: 200
marl: MAPPO + GNN
scenarios: S9–S15 (NTN, UAV, V2X, IIoT, ISAC)
simulation_stack: a definir; se usar E2 com NORI, a pilha fixada em reproducibility/versions.lock (profile.nori)
```

A versão anterior deste documento citava o commit NORI `9b64c12`, que não existe no repositório oficial do NORI; ver [HRDL_F1_COMPATIBILITY_PROFILE.md](HRDL_F1_COMPATIBILITY_PROFILE.md).

## 3. Evolução das especificações

| Item | Fase 1 | Fase 2 (alvo) |
| :-- | :-: | :-: |
| E2AP | v02.03 | v03.01 |
| E2SM-KPM | v03.00 | v08.00 |
| E2SM-RC | v01.03 (perfil local simplificado) | v10.00 |
| Arbitragem | TVS/EEVS determinístico | MAPPO + GNN + KG, com a H-RDL como reserva |
| Cenários | S0–S7 | S9–S15 |

## 4. Requisitos que a Fase 1 impõe à Fase 2

1. Mesma política de evidência ([EXPERIMENTAL_EVIDENCE_POLICY.md](EXPERIMENTAL_EVIDENCE_POLICY.md)): nada sintético em resultados.
2. Uso dos tipos de [`src/conflict_types.py`](../../src/conflict_types.py) sem quebrar os campos da Fase 1 (ver [PHASE1_PHASE2_SYNC_CONTRACT.md](PHASE1_PHASE2_SYNC_CONTRACT.md)).
3. Toda ação passa pelo `Refinement` antes do despacho.
