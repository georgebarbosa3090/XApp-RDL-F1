# Política de evidência experimental

Fonte normativa: [`reproducibility/provenance_policy.yaml`](../../reproducibility/provenance_policy.yaml), aplicada por [`scripts/certification/certify_chain.py`](../../scripts/certification/certify_chain.py).

## 1. Regra de ouro

Um resultado é válido se, e somente se, vem de uma execução identificada e bem-sucedida, com evidência bruta externa ao código de análise e proveniência verificável.

## 2. Origens

| Elegíveis para publicação | Não elegíveis |
| :-- | :-- |
| `NS3_FLOWMONITOR`, `NORI_E2`, `SRSRAN_E2`, `OPEN5GS_CORE`, `OPENRANBR_TESTBED`, `UE_TRAFFIC_TRACE`, `E2_PCAP`, `HRDL_RUNTIME`, `ORAN_SC_RIC`, `SYSTEM_RESOURCE_TRACE` | `SYNTHETIC`, `MOCK`, `CODEC_TEST`, `LOCAL_GENERATOR`, `CAUSAL_FIXTURE`, `DISCRETE_EVENT_SIMULATOR`, `EMULATED`, `MANUAL`, `ESTIMATED`, `DEMO_RUN` |

Além das origens declaradas, o certificador classifica como sintética qualquer execução cujo identificador corresponda ao molde de um script que gera valores com RNG estatístico (é o caso das 210 execuções `S1_B0..B6_seed1001..1030`).

Também não são evidência: mensagens de protocolo impressas pelo código do cenário; hashes gerados pelo próprio pipeline (provam integridade, não execução); decodificação pelo codec local (prova autoconsistência); FlowMonitor sozinho para afirmações sobre KPM, controle RC ou closed loop.

## 3. Registro

Toda execução elegível é produzida por um executor com proveniência e fica em `experiments/runs/<run_id>/`:

| Item | Obrigatório |
| :-- | :-- |
| `execution_manifest.json` | origem, backend, cenário, semente, comando, `run_status`, `exit_code`, início e fim (UTC), versões e commits lidos dos checkouts |
| `logs/` | saída completa |
| `raw/` | evidência bruta do backend: FlowMonitor (`.xml`) na pilha nativa; FlowMonitor e PCAP/RAW E2 na pilha NORI |
| `hashes.sha256` | SHA-256 de todos os arquivos |

Executores: [`run_ns3_certified.sh`](../../scripts/certification/run_ns3_certified.sh) (nativa) e `/scripts/run.sh` no pod `nori-ns3` (NORI). Execuções nunca são sobrescritas nem editadas; execuções interrompidas não são evidência; falhas ficam preservadas em `experiments/runs_failed/`.

## 4. Separação entre testes e experimentos

Nada produzido por `tests/` é copiado para `experiments/` ou `reports/`. Tabelas e figuras são derivadas por leitura dos arquivos de `experiments/runs/`, citando os `run_id`. `experiments/runs/** -text` em `.gitattributes` preserva os bytes para que os hashes confiram em qualquer sistema.

## 5. Auditorias automáticas

- `scripts/certification/certify_chain.py` — vereditos por execução e por gate.
- `scripts/check_no_synthetic_results.py` — procura geradores aleatórios em scripts de resultados.
- `scripts/verify_provenance_and_integrity.py`, `scripts/validate_provenance.py`, `scripts/validate_experiment_tree.py --check-gate1` — validadores complementares.
