# Comunicação com o OSC Near-RT RIC

Este documento aborda a camada de E2 e Infraestrutura que liga a RDL aos canos do O-RAN. Todos os módulos dessa casca estão isolados nos diretórios `src/e2/` e `src/infrastructure/`.

## 1. Descoberta e Subscrição
Diferente da versão primária da RDL que escutava tudo de forma passiva, a versão Zero to Hero implementa um fluxo ativo O-RAN:
- `e2_manager_client.py`: Usa requisições REST GET em `/v1/nodeb/states` para descobrir se existem E2 Nodes conectados. Ele ignora antenas desconectadas e mapeia os `RANFunctionID`.
- `subscription_manager.py`: Com o Node descoberto, a RDL envia um `RIC_SUBSCRIPTION_REQUEST` forjado na API do SubMgr para assinar oficialmente a telemetria KPM, fornecendo o "Event Trigger" correto.

## 2. Decodificação ASN.1
A rede de Rádio utiliza ASN.1 APER (compactado em hexadecimal). Se olharmos cruamente, é lixo binário.
O processo de unpack foi estritamente fatiado:
- `e2ap_decoder.py`: Descasca a cebola externa. Extrai os bytes brutos referentes ao `RICindicationHeader` e ao `RICindicationMessage`. Ele joga fora lixo indesejado do envelope `E2AP`.
- `kpm_decoder.py`: Pega os bytes já filtrados e traduz as medições para as variáveis legíveis `KpmMeasurement` (DRB.UEThpDl, etc).
  - **Aviso:** Se o RDL estiver operando em modo produção (`RDL_MODE=production`), não existem simulações (Mocks). Falhar a conversão ASN.1 gera erro instantâneo e log, sem fabricar "pacotes fake".

## 3. RMR: Routing Manager e Mensagens
O roteamento ocorre na porta 4560, gerida pelo `ricxappframe`.
As mensagens de entrada/saída (e seus Enums) trafegam via tabelas de rota dinâmicas inseridas na inicialização (veja `render_routes.sh`).
- **Entradas (`rxMessages`):** `12050 (RIC_INDICATION)`, `12011 (RIC_CONTROL_ACK)`, `12012 (RIC_CONTROL_FAILURE)`, `30000 (RDL_ACTION_PROPOSAL)`.
- **Saídas (`txMessages`):** `12010 (RIC_CONTROL_REQUEST)`.
