# Perfil de compatibilidade — H-RDL Fase 1

## 1. Camadas

| Camada | Referência | No projeto |
| :-- | :-- | :-- |
| Normativa | O-RAN ALLIANCE (E2AP, E2SM-KPM, E2SM-RC) | versões-alvo da xApp abaixo |
| Implementação de referência | O-RAN Software Community | Subscription Manager (REST), E2Term (RMR/SCTP), RMR, SDL |
| Simulação | ns-3 + 5G-LENA (+ NORI) | duas pilhas, abaixo |
| Contribuição | H-RDL | percepção por alvo, TVS/EEVS, Safety Guard, despacho |
| Evidência | política de proveniência e certificador | gates G0–G6 |

## 2. Versões-alvo da xApp RDL

```yaml
e2ap: v02.03
e2sm_kpm: v03.00
e2sm_rc: v01.03
oran_sc_release: J
decision_window_ms: 200
control_hysteresis_ms: 1000
control_timeout_s: 5
kpm_report_period_ms: 200
```

São **alvos**: os codecs da xApp são locais e não foram validados contra o ASN.1 oficial (o E2SM-RC local é um perfil simplificado, fora da norma). Ver [`../07_certificacao_e_achados.md`](../07_certificacao_e_achados.md).

## 3. Pilhas de simulação

Fonte: [`reproducibility/versions.lock`](../../reproducibility/versions.lock).

```yaml
native:              # backend NS3_5GLENA — cenários de conflito S0–S7, sem E2
  ns3: "3.48"        # d2add90b452d600cfb4859baed8e9ea633519447
  fiveg_lena: v5.1   # cedceadda17392c90587fb9400eb9b1f8c236713
nori:                # backend NORI_NS3 — única pilha com E2 real
  ns3: "3.42"        # ab4cce021d8f6b2458784704a10af810d3969f0f (fixado pelo Dockerfile do NORI)
  nr: 78b7179e3841c608c2021ffa88bea1906a1c7594
  nori: 8a30867c8105d328aa50a7daaab3bcb2b4603763
  e2sim: da6f82f286cdbb38af1178f82f85877b12c2f85b
  asn1c: 8b8028a80aa8f5545dfcaa9d357150ac0c475f70
  e2ap: v03.01
  e2sm_kpm: v03.00
  e2sm_rc: v03.01
  oran_sc_release: I
```

| Componente | Versão | Função |
| :-- | :-- | :-- |
| ns-3 (nativa) | 3.48 | simulador dos cenários de conflito |
| 5G-LENA (nativa) | v5.1 | camadas NR PHY/MAC |
| ns-3 (NORI) | 3.42 | versão exigida pelo NORI |
| 5G-LENA (NORI) | `78b7179` | commit fixado pelo NORI |
| NORI | `8a30867` | agente E2 (E2AP/E2SM v3.01), implantado via `deploy/helm/nori-ns3` |

## 4. Revisão de 2026-11-08

- O commit NORI `9b64c12` congelado anteriormente **não existe** em `github.com/lasseufpa/nori`; execuções que o declaram não correspondem a nenhuma versão real do NORI.
- O NORI não compila sobre ns-3.48 / 5G-LENA v5.1; por isso as pilhas foram separadas.
- O perfil E2 da xApp (v02.03 / RC v01.03) difere do NORI (v3.01). Um teste E2 real exige alinhar os codecs da xApp a v3.01.
- Versões mais novas das especificações (Release 5) ficam fora da Fase 1; ver [MIGRATION_RELEASE5.md](MIGRATION_RELEASE5.md).

## 5. Forma de citação recomendada

> A H-RDL Fase 1 visa compatibilidade com E2AP v02.03, E2SM-KPM v03.00 e E2SM-RC v01.03 (O-RAN SC Release J). A avaliação de decisão foi feita em ns-3.48 com 5G-LENA v5.1, com as ações aplicadas na RAN simulada; a interoperabilidade E2 com um E2 Node e um Near-RT RIC reais não foi demonstrada nesta fase.
