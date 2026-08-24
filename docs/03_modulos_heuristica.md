# Módulo de Raciocínio Heurístico (H-RDL)

## A Engenharia de Decisão (Fase 1)
A RDL centraliza as ações que antes as xApps fariam desenfreadamente. Como na Fase 1 não dependemos de Multi-Agent Reinforcement Learning (MARL), implementamos a estratégia H-RDL (*Heuristic Resource and Decision Layer*).

### Arquitetura de Raciocínio (agents/reasoning_agent.py)

Quando o PerceptionAgent monta o pacote da janela de 200 ms e envia para o ReasoningAgent, ele aciona os seguintes fluxos:

1. **Consulta Histórica (K-Nearest Neighbors simplificado):**
   - O orquestrador acessa o SDL.
   - Verifica se o conflito exato já ocorreu recentemente e se o resultado foi confiável (confidence >= 80%).
   - Reutiliza a decisão de forma instantânea para salvar ciclos computacionais.

2. **Heurística de Conflitos Diretos:**
   - Ocorre quando duas xApps (ex: *Energy-xApp* vs *QoS-xApp*) tentam modificar o mesmo parâmetro no mesmo nó, ao mesmo tempo.
   - É calculada a utilidade multiobjetivo de cada ação candidata:
     U(a) = w1*SLA_score + w2*Throughput_score + w3*Energy_score + w4*Stability_score + w5*Priority_score
   - A ação com maior Utilidade é escolhida. Em caso de empate, fallback para a tabela de prioridades absoluta (TVS/EEVS).

3. **Heurística de Conflitos Indiretos:**
   - Ocorre quando as xApps operam sobre parâmetros diferentes, mas que afetam a mesma métrica KPM de forma destrutiva.
   - A heurística monta permutações das ações compatíveis.
   - Um modelo de pontuação (mock prediction) pontua o subconjunto simulando o resultado agregado sobre o SLA:
     score(S) = w1*QoS(S) + w2*Energy(S) + w3*Fairness(S) - w4*Violations(S)
   - O subconjunto vencedor é selecionado.

### Safety Guard
Independente do fluxo heurístico, nenhuma decisão atinge o Encoder E2SM sem antes passar pelo RefinementAgent.
Ele bloqueia anomalias de sintaxe, limites físicos preestabelecidos e oscilações do tipo *Ping-Pong* em janelas muito curtas, sendo um muro de contenção rígido em uma infraestrutura crítica.
