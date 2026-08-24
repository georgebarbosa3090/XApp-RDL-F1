# RDL (Resource and Decision Layer) xApp

## O Problema
Na arquitetura **O-RAN (Open Radio Access Network)**, as xApps (aplicações do Near-RT RIC) operam de forma isolada e simultânea para gerenciar os nós de rádio. O problema intrínseco dessa arquitetura é o **Conflito de Controle**.
O que acontece se uma `QoS-xApp` decide aumentar a potência e os recursos de rádio (PRB) de uma célula para garantir throughput para um usuário VIP, mas simultaneamente uma `Energy-Savings-xApp` decide diminuir a potência dessa exata mesma célula para economizar energia? 

A antena receberá requisições de controle contraditórias simultaneamente (`RIC_CONTROL_REQUEST`), o que resultará em oscilação agressiva (*ping-pong effect*) e degradação fatal de SLAs, podendo até mesmo desligar a rede. O AppMgr nativo da O-RAN não orquestra as variáveis internas de rádio.

## A Solução (RDL)
A **xApp RDL (Resource and Decision Layer)** é uma camada proposta de Orquestração Cognitiva (via RDP) que se posiciona de forma agnóstica como um árbitro entre o Near-RT RIC e as demais xApps.
O seu princípio fundamental baseia-se em **não permitir que xApps mandem comandos diretamente para a rádio-base**. 

Na arquitetura da RDL:
1. As xApps tradicionais mudam de arquitetura: em vez de serem ativadoras, passam a ser apenas calculadoras de intenções. Elas disparam suas propostas estritas em formato JSON (`RDL_ACTION_PROPOSAL`) para a malha RMR.
2. A **RDL intercepta as propostas**.
3. O Módulo de Inteligência Artificial MAPPO (Multi-Agent Proximal Policy Optimization) funde o pedido de todas as xApps com o real estado de telemetria da antena (KPMs). 
4. A RDL decide matematicamente a ação ótima de compromisso, valida limites físicos (Safety Guard) e despacha um único comando O-RAN oficial.

Esta abordagem unificada garante estabilidade e foi documentada detalhadamente no paper O-RAN *"Zero to Hero"*.
