# Migração para versões mais novas das especificações (planejada)

**Situação:** planejamento; nada iniciado.

## 1. Princípios

1. Os experimentos da Fase 1 continuam ligados ao perfil-alvo E2AP v02.03 / E2SM-KPM v03.00 / E2SM-RC v01.03 e às pilhas de `reproducibility/versions.lock`.
2. Trabalho de migração acontece em branch própria e não altera execuções já registradas.
3. A migração só faz sentido depois de existir um codec normativo validado contra o ASN.1 oficial (pendência da Fase 1).

## 2. Etapas

| Etapa | De | Para | Motivo |
| :-- | :-: | :-: | :-- |
| Alinhar ao NORI | E2AP v02.03, RC v01.03 local | E2AP v03.01, KPM v03.00, RC v03.01 | primeiro teste E2 real com a pilha NORI já fixada |
| Release 5 | v03.x | E2SM-KPM v08.00, E2SM-RC v10.00 | alvo da Fase 2 |
| O-RAN SC | Release J (alvo) / I (NORI) | release validado contra o perfil escolhido | compatibilidade da plataforma |

## 3. Tarefas

- [ ] Gerar codecs a partir do ASN.1 oficial (asn1c ou equivalente) para a versão escolhida.
- [ ] Validar contra PCAPs reais do NORI (`profile.nori`).
- [ ] Atualizar `ControlDispatcher` e `KpmDecoder` mantendo a interface usada por `RDLxApp`.
- [ ] Repetir G1–G4 com a nova versão.
