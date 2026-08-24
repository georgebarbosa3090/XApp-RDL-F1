# Módulos Core do Sistema

Este diretório contém os guias detalhados sobre as lógicas de domínio e coordenação da RDL (pastas `src/domain/` e `src/coordination/`).

## 1. O Domínio: `domain/`
O domínio define o vocabulário da aplicação usando as rigorosas `dataclasses` (Pydantic).
- `proposals.py`: Modela a `ActionProposal`, um documento estrito que toda xApp vizinha deve respeitar ao falar com a RDL (Schema V1.0).
- `conflicts.py`: Define os Enums de Conflito (`DIRECT`, `INDIRECT`, `RESOURCE`, `TEMPORAL`, `POLICY`, `OBJECTIVE`) estabelecidos pelo RDP O-RAN.
- `decisions.py`: A `Decision` é o veredito imutável da RDL após um embate entre xApps.

## 2. A Coordenação: `coordination/`
A lógica de coordenação é o músculo que faz o meio de campo entre o mundo inteligente dos Agentes e o protocolo RMR.
- `control_dispatcher.py`: Recebe a Decisão, utiliza o `E2SMRCEncoder` para traduzi-la, gera um `control_request_id` único, persiste esse ID no Redis SDL e atira a ordem na rede através do RMR para a antena final.
- Ele também captura os `RIC_CONTROL_ACK` e os `RIC_CONTROL_FAILURE`, usando esse id para fechar o ciclo de confirmação (Tracking).

## 3. O Ponto de Entrada: `main.py`
O arquivo `main.py` levanta o Uvicorn (`health_server`), aciona o `ConfigManager` (lendo as configurações validadas pelo Pydantic), conecta as peças no `RDLxApp` e dispara o ciclo assíncrono.
