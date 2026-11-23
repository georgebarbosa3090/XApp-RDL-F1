# Módulo 8 — Específicos 3: Gestão de Dados e Bancos de Dados

> Estimativa: 3 questões. A IDCAP cobra **modelagem (conceitual/lógica/física)**, **SQL**, **ANSI/SPARC**, **OLAP**, **NoSQL** e **DW/Data Mining**. O edital inclui o tema novo **bancos vetoriais para IA**.

## Mapa do edital (item 3)
3.1 Modelagem conceitual, lógica, física · 3.2 Normalização · 3.3 Relacional (PostgreSQL, MySQL), SQL, transações, ACID · 3.4 NoSQL, MongoDB · 3.5 Bancos vetoriais para IA · 3.6 DW e BI.

## Conceitos de SGBD
- **Arquitetura ANSI/SPARC (3 esquemas)**: **externo** (visões dos usuários) → **conceitual/lógico** (estrutura global) → **interno** (armazenamento físico). Na figura da IDCAP 2025, de baixo para cima: **interno, lógico (conceitual), externo**.
- **Independência de dados**: **lógica** (mudar o esquema conceitual sem afetar as visões externas — mais difícil) e **física** (mudar o armazenamento sem afetar o esquema conceitual).
- Linguagens: **DDL** (CREATE, ALTER, DROP, TRUNCATE), **DML** (SELECT, INSERT, UPDATE, DELETE), **DCL** (GRANT, REVOKE), **DTL/TCL** (COMMIT, ROLLBACK, SAVEPOINT).
> ⚠️ Algumas bancas classificam SELECT como **DQL**. TRUNCATE é **DDL** (remove todas as linhas, sem WHERE, geralmente sem rollback); DELETE é **DML**.

## 3.1 Modelagem de dados
| Nível | Foco | Artefato | Independe de SGBD? |
|---|---|---|---|
| **Conceitual** | Visão de negócio: entidades e relacionamentos | **DER** (Peter Chen, 1976) | Sim |
| **Lógico** | Tabelas, colunas, **chaves**, normalização | Modelo relacional | Depende do **modelo** (relacional), não do produto |
| **Físico** | Implementação: tipos de dados, índices, partições | **Scripts DDL** | Não (específico do SGBD) |

Ordem das etapas de um projeto de BD: levantamento de requisitos → **conceitual → lógico → físico** (IDCAP 2025).

### Elementos do MER/DER
- **Entidade** (retângulo): forte × **fraca** (depende de outra para ser identificada — retângulo duplo).
- **Atributo** (elipse): simples, **composto** (endereço = rua + nº), **multivalorado** (telefones — elipse dupla), **derivado** (idade a partir da data de nascimento — tracejada), **identificador/chave** (sublinhado).
- **Relacionamento** (losango) e **cardinalidade**: **1:1**, **1:N**, **N:N** (no modelo lógico, N:N vira uma **tabela associativa**).
- **Especialização/generalização** (herança), **agregação**.

### Modelo relacional — chaves e integridade
| Termo | Definição |
|---|---|
| **Superchave** | Conjunto de atributos que identifica unicamente uma tupla |
| **Chave candidata** | Superchave **mínima** |
| **Chave primária (PK)** | Candidata escolhida; **única e não nula** |
| **Chave alternativa** | Candidata não escolhida (UNIQUE) |
| **Chave estrangeira (FK)** | Referencia a PK de outra tabela → **integridade referencial** |
| **Chave substituta (surrogate)** | Artificial (ID autoincremento) |

- Integridade **de entidade** (PK não nula), **referencial** (FK válida), **de domínio** (tipo/faixa de valores). Ações: `ON DELETE CASCADE / SET NULL / RESTRICT`.
- Terminologia: **relação** = tabela; **tupla** = linha; **atributo** = coluna; **grau** = nº de colunas; **cardinalidade** = nº de linhas.

## 3.2 Normalização
| Forma normal | Regra | Elimina |
|---|---|---|
| **1FN** | Só valores **atômicos**; sem grupos repetitivos nem atributos multivalorados | Atributos multivalorados/compostos |
| **2FN** | 1FN + todo atributo não chave depende da **chave inteira** | **Dependência parcial** (só ocorre com PK composta) |
| **3FN** | 2FN + nenhum atributo não chave depende de outro não chave | **Dependência transitiva** |
| **FNBC (BCNF)** | Todo determinante é **chave candidata** | Anomalias residuais da 3FN |
| 4FN | Sem **dependências multivaloradas** | — |
| 5FN | Sem dependências de **junção** | — |

🧠 "**A chave, a chave inteira e nada além da chave**" (1FN, 2FN, 3FN).
- Objetivo: reduzir **redundância** e evitar **anomalias** de inserção, atualização e exclusão. **Desnormalização**: introduzir redundância de propósito para desempenho (comum em DW).
> ⚠️ Tabela com **PK simples** (um só atributo) que está na 1FN **já está na 2FN**.

## 3.3 SQL, transações e ACID
```sql
CREATE TABLE servidor (
  id SERIAL PRIMARY KEY,               -- PostgreSQL (MySQL: INT AUTO_INCREMENT)
  nome VARCHAR(100) NOT NULL,
  cpf CHAR(11) UNIQUE,
  salario NUMERIC(10,2) CHECK (salario > 0),
  setor_id INT REFERENCES setor(id)
);

SELECT s.setor_id, COUNT(*) AS qtd, AVG(salario) AS media
FROM servidor s
WHERE salario > 5000            -- filtra LINHAS (antes de agrupar)
GROUP BY s.setor_id
HAVING COUNT(*) > 3             -- filtra GRUPOS (depois de agrupar)
ORDER BY media DESC
LIMIT 10;                       -- SQL Server: TOP 10
```
- **Ordem lógica de execução**: **FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT**.
- `DISTINCT` remove duplicatas; `LIKE 'Mac%'` (% = qualquer sequência; `_` = um caractere); `IN`, `BETWEEN` (inclusivo), `IS NULL` (nunca `= NULL`).
- Funções de agregação: COUNT, SUM, AVG, MIN, MAX. `COUNT(*)` conta linhas; `COUNT(coluna)` ignora NULL.

| JOIN | Retorna |
|---|---|
| **INNER JOIN** | Só linhas com correspondência nas duas tabelas |
| **LEFT JOIN** | Todas da esquerda + correspondentes da direita (NULL se não houver) |
| **RIGHT JOIN** | Todas da direita + correspondentes |
| **FULL OUTER JOIN** | Todas de ambas |
| **CROSS JOIN** | Produto cartesiano |
| Self join | Tabela com ela mesma |

- `UNION` (remove duplicatas) × `UNION ALL` (mantém); `INTERSECT`, `EXCEPT`/`MINUS`.
- **Subconsultas**, `EXISTS`; **views** (tabela virtual), **índices** (aceleram leitura, pesam na escrita — B-tree padrão), **stored procedures**, **funções**, **triggers** (executados **automaticamente** em INSERT/UPDATE/DELETE — IDCAP 2025).
- `GRANT SELECT ON servidor TO analista;` / `REVOKE`.

### Transações e ACID
| Propriedade | Significado |
|---|---|
| **Atomicidade** | Tudo ou nada (COMMIT ou ROLLBACK) |
| **Consistência** | Leva o banco de um estado válido a outro, respeitando as restrições |
| **Isolamento** | Transações concorrentes não interferem (como se fossem sequenciais) |
| **Durabilidade** | Após o COMMIT, persiste mesmo com falha (log de transações / WAL) |

- **Anomalias de concorrência**: **leitura suja** (dirty read — ler dado não confirmado), **leitura não repetível** (mesma linha muda entre leituras), **leitura fantasma** (novas linhas aparecem).
- **Níveis de isolamento** (SQL padrão): **Read Uncommitted** (permite tudo) → **Read Committed** (evita leitura suja — padrão do PostgreSQL e SQL Server) → **Repeatable Read** (evita também a não repetível — padrão do MySQL/InnoDB) → **Serializable** (evita fantasmas — mais restritivo).
- Controle de concorrência: **bloqueios** (lock compartilhado/exclusivo, **2PL**), **MVCC** (multiversão — PostgreSQL, InnoDB), deadlock.

### PostgreSQL × MySQL
| | **PostgreSQL** | **MySQL** |
|---|---|---|
| Natureza | Objeto-relacional, muito aderente ao padrão SQL | Relacional, muito popular na web (LAMP) |
| Licença | PostgreSQL License (livre) | GPL / comercial (Oracle) |
| Destaques | **JSONB**, tipos avançados, CTEs, funções de janela, extensões (**PostGIS**, **pgvector**), MVCC nativo | Engines: **InnoDB** (padrão, transacional, ACID, FK) × MyISAM (sem transações) |
| Autoincremento | `SERIAL` / `IDENTITY` | `AUTO_INCREMENT` |
| Porta | **5432** | **3306** |
| Cliente | `psql` | `mysql` |

## 3.4 NoSQL e MongoDB
| Tipo | Modelo | Exemplos | Uso |
|---|---|---|---|
| **Chave-valor** | Par chave → valor | **Redis**, DynamoDB, Riak | Cache, sessões |
| **Documento** | Documentos JSON/BSON | **MongoDB**, **CouchDB**, **Couchbase** | Catálogos, conteúdo, APIs |
| **Colunar (família de colunas)** | Colunas agrupadas | **Cassandra**, HBase | Big data, escrita massiva |
| **Grafo** | Nós e arestas | **Neo4j**, Amazon Neptune | Redes sociais, fraudes, recomendações |

- Características: **esquema flexível** (schemaless), **escalabilidade horizontal** (sharding), alta disponibilidade (replicação), modelo **BASE** e **consistência eventual**, guiados pelo **teorema CAP**.
- **MongoDB**: banco de **documentos** em **BSON** (JSON binário); **banco → coleção → documento** (equivalem a banco → tabela → linha); cada documento tem `_id` (ObjectId); **replica set** (alta disponibilidade, um primário) e **sharding** (escala horizontal); **aggregation pipeline** (`$match`, `$group`, `$project`, `$sort`, `$lookup`); suporta índices e transações multi-documento (desde a 4.0). Porta **27017**.
```js
db.servidores.insertOne({ nome: "Ana", setor: "TI", skills: ["Python", "SQL"] })
db.servidores.find({ setor: "TI", salario: { $gt: 8000 } }, { nome: 1 })
db.servidores.updateOne({ nome: "Ana" }, { $set: { salario: 9000 } })
```
> ⚠️ NoSQL = "**Not Only SQL**" (não apenas SQL). Vários NoSQL **suportam** consultas parecidas com SQL e transações.

## 3.5 Bancos de dados vetoriais para IA (tema novo — prioridade A)
- **Embedding**: representação de um dado (texto, imagem, áudio) como **vetor numérico de alta dimensão** (ex.: 768 ou 1.536 dimensões), gerado por um modelo de IA, em que **itens semanticamente parecidos ficam próximos** no espaço vetorial.
- **Banco vetorial**: armazena embeddings e faz **busca por similaridade** (*k*-vizinhos mais próximos, **k-NN**), em vez de busca por igualdade exata.
- **Métricas de similaridade/distância**: **cosseno** (ângulo entre vetores — a mais usada para texto), **produto interno** (dot product), **distância euclidiana (L2)**, Manhattan (L1).
- **ANN (Approximate Nearest Neighbor)**: busca **aproximada**, que troca um pouco de precisão por muita velocidade. Índices: **HNSW** (grafos hierárquicos navegáveis — o mais comum), **IVF** (arquivos invertidos/clusters), **PQ** (quantização de produto, comprime vetores), LSH.
- **Exemplos**: **Pinecone** (gerenciado), **Milvus**, **Weaviate**, **Qdrant**, **Chroma**, **FAISS** (biblioteca do Meta, não é SGBD), **pgvector** (extensão do PostgreSQL), Elasticsearch/OpenSearch com k-NN, MongoDB Atlas Vector Search, Redis.
- **Uso principal**: **RAG** (ver Módulo 10) — o texto dos documentos é dividido em *chunks*, convertido em embeddings e indexado; a pergunta do usuário também vira embedding, e os trechos mais próximos são enviados ao LLM como contexto. Outros usos: busca semântica, recomendação, deduplicação, detecção de anomalias.
- **Busca híbrida**: combina busca vetorial (semântica) com busca por palavra-chave (BM25), com *re-ranking*. **Filtragem por metadados** (ex.: só documentos de 2026, só do órgão X).
> ⚠️ Banco vetorial ≠ banco de grafos. E embedding ≠ criptografia: embeddings podem vazar informação sensível (LGPD aplica-se aos dados de origem).

## 3.6 Data Warehouse e Business Intelligence
| | **OLTP** (transacional) | **OLAP** (analítico) |
|---|---|---|
| Objetivo | Operação do dia a dia | Apoio à **decisão** |
| Dados | Atuais, detalhados, **normalizados** | **Históricos**, consolidados, **desnormalizados** |
| Operações | INSERT/UPDATE frequentes, transações curtas | Consultas complexas, leitura predominante |

- **Data Warehouse (Inmon)**: coleção de dados **orientada por assunto, integrada, não volátil e variante no tempo**, para apoio à decisão.
- **Inmon** (top-down: DW corporativo normalizado → data marts) × **Kimball** (bottom-up: data marts dimensionais integrados por **dimensões conformadas** — barramento).
- **Data Mart**: subconjunto do DW para um departamento/assunto.
- **ETL** (Extract, Transform, Load — transforma antes de carregar, *staging area*) × **ELT** (carrega e transforma no destino — comum em nuvem/data lakes).
- **Data Lake**: dados **brutos** em qualquer formato (estruturados, semi e não estruturados), *schema-on-read*. **Lakehouse**: une data lake + recursos de DW.

### Modelagem dimensional
- **Tabela fato**: medidas numéricas do negócio (valor, quantidade) + FKs para dimensões; granularidade.
- **Tabela dimensão**: contexto descritivo (tempo, órgão, produto, local).
- **Esquema estrela (star)**: fato no centro e dimensões **desnormalizadas** ao redor. **Floco de neve (snowflake)**: dimensões **normalizadas** (subdimensões). **Constelação**: várias fatos compartilhando dimensões.
- **SCD (Slowly Changing Dimensions)**: tipo 1 (sobrescreve), **tipo 2 (nova linha com versão/vigência — guarda histórico)**, tipo 3 (coluna com valor anterior).

### Operações OLAP
| Operação | Efeito |
|---|---|
| **Drill-down** | Do resumo para o detalhe (ano → mês → dia) |
| **Roll-up** (drill-up) | Do detalhe para o resumo |
| **Slice** | Fixa **uma** dimensão (fatia) |
| **Dice** | Seleciona um **subcubo** filtrando várias dimensões |
| **Pivot** (rotação) | Troca linhas e colunas |
| Drill-across / drill-through | Entre cubos / até os dados de origem |

| Arquitetura OLAP | Armazenamento |
|---|---|
| **MOLAP** | Cubos **multidimensionais** pré-calculados (rápido) |
| **ROLAP** | Banco **relacional** (escalável) |
| **HOLAP** | Híbrido |
| **DOLAP** | **Desktop**: cubo baixado para a máquina do usuário (portabilidade) |

- **Data Mining**: descoberta de **padrões ocultos** em grandes volumes (KDD). Tarefas: **classificação**, **regressão**, **agrupamento (clustering)**, **regras de associação** (cesta de compras — Apriori), detecção de anomalias.
- **BI**: ferramentas (Power BI, Tableau, Metabase, Superset), dashboards, **KPIs**, relatórios. **Big Data — Vs**: Volume, Velocidade, Variedade (+ Veracidade, Valor).
- **Governança de dados**: qualidade, catálogo, metadados, linhagem, *data steward*; **DAMA-DMBOK**. Dados abertos (Lei 14.129/2021 e Decreto 8.777/2016).

## ⚠️ Pegadinhas do bloco
1. **WHERE** filtra linhas (antes); **HAVING** filtra grupos (depois do GROUP BY).
2. 2FN só é violada com **chave composta** (dependência parcial).
3. Modelo **lógico** independe do SGBD específico; **físico** depende.
4. **Star** = dimensões desnormalizadas; **snowflake** = normalizadas.
5. **Slice** = 1 dimensão; **dice** = várias.
6. Banco vetorial usa **similaridade**, não igualdade; **cosseno** é a métrica típica para texto.

## Questões comentadas (estilo IDCAP)

**Q1.** Em um modelo, uma tabela possui chave primária composta (matricula, cod_curso) e o atributo nome_aluno depende apenas de matricula. Essa tabela viola a:
(A) 1FN. (B) **2FN.** (C) 3FN. (D) FNBC.
✅ **B.** Dependência parcial da chave composta.

**Q2.** Em SQL, para listar setores com mais de cinco servidores, a cláusula que filtra o resultado após o agrupamento é:
(A) WHERE. (B) ORDER BY. (C) **HAVING.** (D) DISTINCT.
✅ **C.**

**Q3.** Uma propriedade das transações garante que todas as operações sejam concluídas ou nenhuma seja aplicada; outra garante que, após confirmadas, as alterações persistam mesmo em caso de falha. São, respectivamente:
(A) Consistência e isolamento. (B) **Atomicidade e durabilidade.** (C) Isolamento e durabilidade. (D) Atomicidade e consistência.
✅ **B.**

**Q4.** Em uma solução de IA generativa para consulta à legislação estadual, os documentos são convertidos em representações numéricas de alta dimensão e armazenados em um banco que permite recuperar os trechos semanticamente mais próximos da pergunta do usuário. Essas representações e a métrica de similaridade mais comum nesse contexto são, respectivamente:
(A) Hashes e distância de Hamming. (B) **Embeddings e similaridade do cosseno.** (C) Tokens e chave primária. (D) Índices B-tree e igualdade exata.
✅ **B.**

**Q5.** Operação OLAP que navega dos dados anuais para os dados mensais e depois diários:
(A) Roll-up. (B) **Drill-down.** (C) Slice. (D) Pivot.
✅ **B.**

**Q6.** Banco NoSQL orientado a documentos que armazena dados em BSON, organizados em coleções:
(A) Redis. (B) Cassandra. (C) **MongoDB.** (D) Neo4j.
✅ **C.**
