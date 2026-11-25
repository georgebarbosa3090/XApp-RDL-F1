# Módulo 2 — Raciocínio Lógico Matemático (estilo FGV)

> **Peso**: 10 questões. **Acerto dos aprovados em Canaã: 54,8%**, e só **44,5% na faixa do corte**. Foi a matéria que mais separou quem passou de quem ficou fora das vagas.
> A FGV cobra **matemática básica com contexto** (preço, cópias, funcionários, corrida). Lógica formal aparece **1 vez por prova, no máximo** (Caraguatatuba Q14).

## 1. Ferramentas que resolvem 80% das questões

| Ferramenta | Fórmula / método | Questão real |
|---|---|---|
| **Porcentagem** | *x% de N = x/100 · N*; aumento de i% → ×(1+i); desconto de i% → ×(1−i) | Canaã Q12: 5% = R$ 36 → preço 720 → paga **684** |
| **Porcentagem de porcentagem** | Multiplique as taxas | Carag. Q15: 20% × 70% = **14%** do total = 7 → total **50** |
| **Juros simples** | J = C · i · t (sobre o **saldo financiado**) | Canaã Q18: saldo 120, juros 4,80 → **4%** (não sobre o preço total!) |
| **Razão** | a:b com total T → partes T·a/(a+b) e T·b/(a+b) | SJC Q18: 5:7 de 60 → 25 mulheres |
| **Regra de três** | Direta: mais tempo → mais cópias | Carag. Q16: 270/min → 90 por 20 s → ×5 = **450** |
| **Velocidade** | d = v · t (cuidado com min → h) | SJC Q16: 0,75 × 4 + 0,5 × 11 = 8,5 km |
| **Sistemas** | Substituição | Carag. Q17: b + v = 125 e 4b + 6v = 600 → b = 75 |
| **Inequação** | Isole x mantendo os três lados | Canaã Q11: 17 < 3x − 4 < 20 → 7 < x < 8 |
| **Frações de um todo** | "⅓ do **restante**" = ⅓ × (1 − parte já usada) | Canaã Q15 |
| **Proporcionalidade linear** | ΔY/ΔX constante | SJC Q23: 3 a cada 4 → ΔX = −12 → ΔY = −9 |

## 2. Estatística básica

- **Média** = soma ÷ quantidade. *Acrescentar um elemento*: nova soma − soma antiga (Canaã Q16: 6×7 − 5×6 = **12**).
- **Maximizar um valor com média fixa**: os demais ficam no **mínimo possível** (SJC Q22: 400 − (1+…+7) = **372**).
- **Mediana**: ordene; com n par, faça a média dos dois centrais (Canaã Q20).
- **Moda**: o valor mais frequente.

## 3. Conjuntos e contagem

- **União**: n(A∪B) = n(A) + n(B) − n(A∩B) (Canaã Q17).
- Com subgrupos (meninos × meninas), **resolva cada grupo separadamente** (SJC Q24).
- **Princípio da casa dos pombos / pior caso**: imagine o azar máximo (Canaã Q14: 3 azuis + 2 pretas = 5 → a 6ª é vermelha).
- **Garantir vitória**: teste o placar mínimo contra o **melhor rival possível** (SJC Q21: 15 pontos).
- **Princípio multiplicativo**: etapas independentes → multiplique.

## 4. Probabilidade

P = casos favoráveis ÷ casos possíveis.

- **Dois dados** = 36 casos. Somas: 7 (6 casos), 8 (5), 9 (4), 10 (3), 11 (2), 12 (1). Carag. Q11: soma > 8 → 10/36 = **5/18**.
- **Sem reposição**: conte os pares (SJC Q25: soma ímpar exige o 5 → 3 de 6 pares = **1/2**).

## 5. Geometria e plano cartesiano

| Figura | Área / perímetro |
|---|---|
| Retângulo | A = b·h; P = 2(b + h) |
| Triângulo | A = b·h/2 → um triângulo com a base de um retângulo e o vértice no lado oposto tem **metade** da área do retângulo (Carag. Q18) |
| Paralelogramo | A = base × altura (SJC Q19: 7 × 3 = 21) |
| Triângulo retângulo | Pitágoras; trio **3-4-5** (Carag. Q12) |
| Soma dos ângulos internos | 180° (Canaã Q19: 90° + 15° + **75°**) |

**Distância entre pontos**: d = √(Δx² + Δy²). Se o segmento é horizontal ou vertical, basta subtrair as coordenadas.

**Retângulos de área fixa** (Canaã Q13): liste os pares de divisores (1×24, 2×12, 3×8, 4×6) e calcule o perímetro de cada um.

## 6. Sequências

- **Regra recursiva**: para achar o **1º termo**, **inverta** a operação (Carag. Q13: x → (x + 5)/3 até não dar inteiro).
- **Ciclos**: dois ciclos de tamanhos a e b voltam juntos ao início no **MMC(a, b)** (SJC Q20: MMC(6, 4) = 12).

## 7. Lógica proposicional (o mínimo seguro)

| Estrutura | Equivalente | Negação |
|---|---|---|
| p → q | **~q → ~p** (contrapositiva) · **~p ∨ q** | **p ∧ ~q** |
| p ∧ q | — | ~p ∨ ~q |
| p ∨ q | ~p → q | ~p ∧ ~q |
| Todo A é B | — | **Algum** A **não** é B |
| Nenhum A é B | — | Algum A é B |

> ⚠️ A **recíproca** (q → p) e a **inversa** (~p → ~q) **não** são equivalentes a p → q. Carag. Q14: "Se é domingo, estudo inglês ou alemão" ≡ "**Se não estudo inglês e não estudo alemão, não é domingo**".

## 8. Checklist de armadilhas FGV

- [ ] A porcentagem é **sobre qual base**? (preço total × saldo; total × subgrupo)
- [ ] As unidades estão compatíveis? (minutos × horas; segundos × minutos; metros × km)
- [ ] A pergunta exclui alguém? ("**sem contar** Luiza" → 25 − 1)
- [ ] A pergunta pede o **mínimo para garantir** (pior caso) ou o **possível**?
- [ ] Na tabela, você ordenou os dados antes de achar a mediana?
