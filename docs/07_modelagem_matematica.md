# Modelagem Matemática do Orquestrador H-RDL (Fase 1)

Este documento detalha a modelagem matemática utilizada pelo orquestrador heurístico determinístico (H-RDL) para a detecção e resolução de conflitos entre xApps no O-RAN Near-RT RIC.

## 1. Janela de Decisão (Decision Window) e Definição de Propostas

Em vez de reagir a cada intenção individual de forma imediatista (First-Come-First-Served), a RDL agrupa as intenções em uma janela de tempo fixa (ex: $T = 200 \text{ ms}$).

O conjunto de propostas capturadas na janela de tempo $t$ é dado por:
$$ P = \{p_1, p_2, \ldots, p_n\} $$

Onde cada proposta $p_i$ é definida pela tupla:
$$ p_i = (xApp_i, node_i, param_i, value_i, priority_i) $$

Simultaneamente, a RDL possui a observação do estado da rede (métricas KPM) no instante $t$:
$$ K_t = \{throughput, delay, PRB, SINR, energy, \ldots\} $$

## 2. Modelagem do Conflito Direto

Ocorre um **Conflito Direto** quando duas ou mais propostas no conjunto $P$ tentam alterar o mesmo $param_i$ de um mesmo $node_i$, simultaneamente. 

A RDL gera um conjunto de ações candidatas $A = \{a_1, a_2, \ldots, a_m\}$ para resolver o conflito. O algoritmo heurístico calcula a utilidade de cada ação individual $a \in A$ baseado em uma função aditiva de pesos:

$$ U(a) = w_{SLA} \cdot \Phi_{SLA}(a) + w_{T} \cdot \Phi_{Throughput}(a) + w_{E} \cdot \Phi_{Energy}(a) + w_{Stab} \cdot \Phi_{Stability}(a) + w_{P} \cdot \Phi_{Priority}(a) $$

Onde:
- **$\Phi_{SLA}(a)$**: Estimativa de cumprimento do Acordo de Nível de Serviço (SLA).
- **$\Phi_{Throughput}(a)$**: Ganho ou penalidade em vazão (Throughput).
- **$\Phi_{Energy}(a)$**: Eficiência energética ($Energy$).
- **$\Phi_{Stability}(a)$**: Estabilidade / Prevenção de oscilação em malha de controle.
- **$\Phi_{Priority}(a)$**: Peso baseado na prioridade predefinida da xApp emissora.
- **$w_i$**: São os coeficientes de calibração que definem a política global (ex: $w_{SLA} = 0.35, w_{T} = 0.25$, etc). Somatório igual a 1.

A decisão ótima para o conflito direto é a ação que maximiza a utilidade:
$$ a^* = \arg\max_{a \in A} U(a) $$

## 3. Modelagem do Conflito Indireto

Ocorre um **Conflito Indireto** quando as xApps tentam modificar parâmetros diferentes (ex: $param_{TX\_POWER}$ e $param_{PRB\_QUOTA}$), mas que, de forma sistêmica, impactam os mesmos Indicadores Chave de Desempenho (KPIs).

O algoritmo avalia **subconjuntos de ações** compatíveis $S \subseteq P$. 
O espaço combinatório é dado por $2^n - 1$ subconjuntos possíveis (desconsiderando o conjunto vazio).

A função de score de um subconjunto $S$ é calculada da seguinte forma:

$$
score(S) = 
\begin{cases} 
-\infty & \text{se } S \text{ contém incompatibilidade física direta} \\
w_{Q} \cdot QoS(S) + w_{E} \cdot Energy(S) + w_{F} \cdot Fairness(S) - w_{V} \cdot Violations(S) & \text{caso contrário}
\end{cases}
$$

Onde as funções (QoS, Energy, Fairness, Violations) são *mocks/proxies* determinísticos que estimam o impacto sistêmico baseado nas regras implementadas.

O subconjunto vencedor é:
$$ S^* = \arg\max_{S \subseteq P} score(S) $$

## 4. Safety Guard e Execução Final

Mesmo que a função de utilidade classifique $a^*$ ou $S^*$ como a melhor resposta analítica, o vetor de controle precisa passar pela validação física do **Safety Guard**.

A política de proteção pode ser modelada como uma função indicadora booleana de segurança:
$$ safety(a) \in \{true, false\} $$

A ação que será despachada e convertida no payload `E2SM-RC` será:

$$
a_{exec} = 
\begin{cases} 
a^*, & \text{se } safety(a^*) = true \\
\text{rollback ou } a_{suboptimal}, & \text{se } safety(a^*) = false
\end{cases}
$$

Esse estrangulamento final garante a resiliência (Zero to Hero) em infraestruturas críticas (e.g. bloqueando potência irrealista de transmissão, prevenindo a queda do link com o UE).
