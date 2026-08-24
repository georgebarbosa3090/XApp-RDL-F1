# Testes e CI (Continuous Integration)

Como estipulado pelo padrÃ£o O-RAN Zero to Hero, o nÃ­vel de cobertura global alvo Ã© `>= 80%`.

## 1. Testes Automatizados com Pytest (`tests/`)
NÃ³s testamos as regras de negÃ³cio de forma agnÃ³stica Ã  rede (nÃ£o rodamos a xApp completa conectada para testar a heurística H-RDL, nÃ³s isolamos e "Mockamos" a API RMR usando `unittest.mock`).

Para rodar (supondo ambiente Python local):
```bash
make test
```
*(O comando farÃ¡ com que o PYTHONPATH seja injetado corretamente na pasta raiz).*

## 2. ValidaÃ§Ã£o EstÃ¡tica e de Descriptor
NÃ£o queremos mandar uma xApp para o RIC que falha na sintaxe do arquivo de *onboarding*.
Criamos validaÃ§Ã£o JSON Schema Draft-07 estrita e um Makefile correspondente:
```bash
make validate
```
Isto assegura que o arquivo `configs/xapp_descriptor.json` estÃ¡ totalmente em compliance e pronto para uso no AppMgr.

## 3. Coleta de EvidÃªncias Experimentais
O artigo O-RAN determina experimentos do cenÃ¡rio E1 ao E6 (Baseline sem RDL, prioridade fixa, Heurística H-RDL, injeÃ§Ã£o de falhas, etc).
Implementamos o script de coleta que agrupa magicamente os logs em pastas nomeadas:
```bash
./scripts/collect_evidence.sh EXPERIMENTO_E1
```
Esse comando agruparÃ¡:
- `metadata.json`
- `configuration.yaml`
- `container_image.txt`
- `kubectl_get_pods.txt`
- `xapp_logs.jsonl`

Isso permite gerar publicaÃ§Ãµes acadÃªmicas com reprodutibilidade cravada em log, extraindo exatamente a taxa de SLA Violations e Falsos Negativos do sistema.
