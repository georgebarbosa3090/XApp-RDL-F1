# Matriz de versões E2

Atualizado em 2026-11-08.

## 1. Versões e situação dos codecs

| Item | Versão-alvo (xApp) | Código | Situação |
| :-- | :-: | :-- | :-- |
| E2AP | v02.03 | `src/e2/e2ap/` | codec local; testado contra vetores gerados por ele mesmo; não validado contra o ASN.1 oficial |
| E2SM-KPM | v03.00 | `src/e2/kpm/` | codec local; mesma ressalva |
| E2SM-RC | v01.03 | `src/e2/rc/` | perfil simplificado local, **fora da norma**; não interoperável sem substituição |
| RMR | ricxappframe 3.2.2 | `src/infrastructure/rmr_transport.py` | envio com MEID por mensagem; testado com RMR simulado |
| SDL | Redis | `src/infrastructure/sdl_repository.py` | testado localmente |
| NORI (E2 Node) | E2AP v03.01 / KPM v03.00 / RC v03.01 | `deploy/helm/nori-ns3` | pilha fixada; implantação pendente |
| ns-3 + 5G-LENA (nativa) | 3.48 + v5.1 | `simulations/ns3/` | em uso nos cenários S0–S7 (sem E2) |

O perfil da xApp (v02.03 / RC v01.03) **não coincide** com o do NORI (v3.01). O primeiro teste E2 real exige alinhar os codecs; ver [`../compliance/MIGRATION_RELEASE5.md`](../compliance/MIGRATION_RELEASE5.md).

## 2. Mapeamento de controle (RC)

```text
ação lógica da RDL-N1 ──RanFunctionCapabilityRegistry──▶ (estilo, ação, RAN Parameter ID) ──codec RC──▶ RIC Control Request
```

Valores padrão do registro (`src/e2/rc/capability_registry.py`). No modo estrito (`RDL_STRICT_ORAN=true`) esses padrões não são usados: a capacidade precisa ser registrada a partir da RAN Function do E2 Node, e a descoberta automática pela RAN Function Definition ainda não está implementada.

| Parâmetro | Estilo | Ação | Faixa (`control_parameter.py`) | Efeito na simulação nativa |
| :-- | :-: | :-: | :-- | :-- |
| `PRB_QUOTA` | 1 | 1 | 0–100 % (inteiro) | máscara de RBG no escalonador (`SetDlNotchedRbgMask`) |
| `SCHEDULER_WEIGHT` | 1 | 2 | 1–100 (inteiro) | não suportado (`UNSUPPORTED`) |
| `TX_POWER` | 2 | 1 | dBm, uma casa decimal | `NrGnbPhy::SetTxPower` |
| `HANDOVER` | 3 | 1 | célula-alvo | `NrHelper::HandoverRequest`, escalonado a cada 10 ms |

## 3. Identificadores

- OID E2SM-KPM: `1.3.6.1.4.1.53148.1.2.2.2`; OID E2SM-RC: `1.3.6.1.4.1.53148.1.2.2.3`.
- RAN Function IDs de exemplo: 2 (KPM) e 3 (RC). No modo estrito devem vir do E2 Setup.
