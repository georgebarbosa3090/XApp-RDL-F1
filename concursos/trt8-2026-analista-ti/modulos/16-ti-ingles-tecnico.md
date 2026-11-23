# Módulo 16 — Inglês Técnico

> O edital inclui **"Inglês técnico"** dentro de TI. A FCC costuma apresentar um trecho de documentação, artigo técnico ou norma em inglês e perguntar **ideia principal**, **sentido de termos** e **referência pronominal**. Estimativa: 0–2 questões.

## 1. Estratégia de leitura
1. Leia **primeiro as perguntas**; depois faça *skimming* (ideia geral: título, primeira frase de cada parágrafo) e *scanning* (busca de informação específica).
2. Use os **cognatos** (*architecture, protocol, authentication*) e o seu conhecimento de TI — o contexto técnico resolve a maior parte.
3. Cuidado com os **falsos cognatos** e com **conectores** que mudam o sentido.

## 2. Falsos cognatos frequentes em TI
| Inglês | Significa | Não é |
|---|---|---|
| **actually** | na verdade | atualmente (*currently*) |
| **eventually** | finalmente, por fim | eventualmente (*occasionally*) |
| **pretend** | fingir | pretender (*intend*) |
| **library** | biblioteca | livraria (*bookstore*) |
| **data** | dados | data (*date*) |
| **support** | suportar = dar suporte/apoiar | aguentar (*stand*) |
| **assume** | supor, presumir | assumir um cargo (*take over*) |
| **sensible** | sensato | sensível (*sensitive*) |
| **realize** | perceber | realizar (*accomplish*) |
| **push** | empurrar/enviar | puxar (*pull*) |
| **legacy** | legado (sistema antigo) | — |
| **deprecated** | obsoleto, desaconselhado | depreciado (contábil) |
| **issue** | problema, questão; emitir (certificado) | — |
| **release** | versão lançada; liberar | — |
| **deploy** | implantar | — |
| **override** | sobrescrever | — |
| **thread** | linha de execução; tópico | — |

## 3. Conectores
| Função | Conectores |
|---|---|
| Adição | and, also, moreover, furthermore, in addition, besides |
| Contraste | but, however, nevertheless, although, though, whereas, while, despite / in spite of |
| Causa | because, since, as, due to, owing to |
| Consequência/conclusão | so, therefore, thus, hence, consequently, as a result |
| Condição | if, unless (= a menos que), provided that, as long as |
| Exemplo | for instance, for example, such as, e.g. |
| Explicação | that is, i.e., namely |

## 4. Verbos modais em normas e RFCs (RFC 2119 — muito útil para a RFC 9700!)
| Termo | Sentido |
|---|---|
| **MUST / REQUIRED / SHALL** | Obrigatório |
| **MUST NOT / SHALL NOT** | Proibido |
| **SHOULD / RECOMMENDED** | Recomendado (pode haver exceções justificadas) |
| **SHOULD NOT / NOT RECOMMENDED** | Desaconselhado |
| **MAY / OPTIONAL** | Opcional |
> Ex.: "The resource owner password credentials grant **MUST NOT** be used." → **não deve ser usado** (proibido).

## 5. Vocabulário essencial
**Desenvolvimento**: *build, deploy, rollback, branch, merge, pull request, commit, release, bug, fix, patch, workaround, backlog, sprint, stakeholder, requirement, feature, framework, endpoint, payload, header, query, token, scope, grant, claim*.
**Infra/segurança**: *throughput, latency, bandwidth, failover, load balancer, availability, backup, restore, breach, threat, vulnerability, exploit, mitigation, hardening, least privilege, encryption, hash, key pair, certificate, revocation, audit trail, compliance*.
**Sufixos/prefixos**: *-able* (possível: *scalable*), *-less* (sem: *serverless, stateless*), *un-/in-/dis-* (negação: *unauthorized, insecure, disable*), *re-* (novamente: *redeploy*), *-ize* (tornar: *virtualize*), *pre-/post-*, *multi-*, *over-* (excesso: *overload*), *under-* (insuficiente).

## 6. Gramática que ajuda na interpretação
- **Voz passiva** é comum em textos técnicos: "*Tokens are issued by the authorization server*" (tokens **são emitidos** pelo servidor de autorização).
- **Referência pronominal**: *it/its* (singular), *they/their/them* (plural), *which/that* (que), *whose* (cujo), *this/these* (retomam a ideia anterior).
- **Grupos nominais**: lê-se **de trás para frente** — "*container orchestration platform*" = plataforma **de orquestração de contêineres**; "*single sign-on authentication service*" = serviço de autenticação de login único.

## Questão comentada (inédita, estilo FCC)
*"Refresh tokens issued to public clients MUST be sender-constrained or use refresh token rotation. Otherwise, an attacker who steals a refresh token could obtain new access tokens indefinitely."*

**Q1.** De acordo com o trecho:
(A) clients públicos estão proibidos de receber refresh tokens.
(B) **refresh tokens de clients públicos devem estar vinculados ao remetente ou ser rotacionados, para evitar que um atacante obtenha novos tokens indefinidamente.**
(C) a rotação de refresh tokens é opcional para clients confidenciais e proibida para públicos.
(D) access tokens devem ser rotacionados a cada requisição.
(E) o atacante só consegue novos tokens se tiver a senha do usuário.
✅ **B.** *MUST* = obrigatório; *otherwise* = caso contrário.
