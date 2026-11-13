# Perfil de testbed srsRAN + Open5GS (planejado)

**Situação:** planejamento. Os adaptadores existem no código, mas nunca foram executados contra um srsRAN gNB ou um Open5GS reais. Nenhum item deste documento é evidência.

## 1. Papel

Complementar à simulação: validar a interoperabilidade E2 com software de RAN real (srsRAN Project) e núcleo 5G (Open5GS), antes do testbed físico OpenRAN@Brasil.

```yaml
profile: HRDL_F1_SRSRAN_TESTBED_PROFILE
backend: SRSRAN_OPEN5GS
srsran_version: 24.10.1   # ef4b0749a12a3b1a8347ae01c937a621603b4069 (versions.lock)
open5gs_version: v2.7.0   # 83e35bb2de7e67646fdba849580184422b10006a
e2ap: v03.00
e2sm_kpm: v03.00
e2sm_rc: v03.00
kpm_reporting_period_ms: 1000
decision_window_ms: 200
```

## 2. Componentes no código

| Item | Arquivo |
| :-- | :-- |
| Adaptador de backend | `SrsRanBackendAdapter` em `src/infrastructure/ran_backend_adapter.py` |
| Adaptador E2 (socket) | `src/e2/backends/srsran_e2_adapter.py` |
| Configurações de testbed | `configs/testbed_zmq/`, `configs/testbed_sdr/` |
| Roteiros por fase | removidos em 2026-11-09 (nunca rodaram com proveniência); a reescrever no padrão de `scripts/certification/` |

## 3. Mapeamento de controle previsto

| Parâmetro RDL-N1 | Estilo RC | Ação RC | Observação |
| :-- | :-: | :-: | :-- |
| `PRB_QUOTA` | 2 (slice) | 6 (alocação de PRB) | conforme o agente E2 do srsRAN |
| `HANDOVER` | 3 (mobilidade) | 1 | a confirmar na versão do srsRAN |

O codec E2SM-RC atual da xApp é um perfil simplificado e precisaria ser substituído por um codec v3.00 normativo antes de qualquer teste.

## 4. Observação de efeito

Com KPM a cada 1 s, a avaliação de uma decisão exige pelo menos três amostras estáveis (3 s) após o controle.

## 5. Pendências

1. Codec E2SM-RC v3.00 normativo.
2. Escrever e executar os roteiros do testbed com captura PCAP e manifesto, pelo mesmo padrão de proveniência (`reproducibility/provenance_policy.yaml`, backend `SRSRAN_OPEN5GS`).
3. Registrar versões reais de srsRAN, Open5GS e O-RAN SC por execução.
