# Load Balancer Reference xApp (O-RAN SC lb-xapp)

## Visão Geral
A **Load Balancer xApp** gerencia o balanceamento dinâmico de carga entre células e portadoras de rádio através da definição de limiares de ocupação de PRB e redistribuição de tráfego.

## Parâmetros de Controle
- `LOAD_THRESHOLD`: Limiar de ocupação percentual de PRB para disparo de offload (faixa: 0.0 a 1.0, padrão: 0.75).
