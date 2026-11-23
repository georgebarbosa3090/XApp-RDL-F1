# Módulo 11 — TI: Banco de Dados, Ciência de Dados, IA e BI

> Edital: *MER; normalização; SQL (DML, DDL, DCL); gerência de transações; tuning; SQL, PL/pgSQL e PL/SQL; PostgreSQL 15, 16, 17 e 18; Oracle 19c; MySQL 8; NoSQL. Ciência de Dados e IA: estatística e análise de dados; Big Data; machine learning supervisionado e não supervisionado; avaliação de modelos; IA generativa, ética e governança; DataOps, MLOps; BI: pipeline de dados, orquestração, integração, ETL.* Estimativa: 5–7 questões. A FCC (TRT-15/2023) cobrou **comandos exatos** de Oracle e MySQL (índice, buffer cache, buffer pool).

## 1. Modelagem e normalização (revisão rápida)
- **MER/DER** (Chen): entidade (forte/fraca), atributo (simples, composto, multivalorado, derivado, chave), relacionamento e **cardinalidade** (1:1, 1:N, N:N — vira tabela associativa no modelo relacional), especialização/generalização, agregação.
- Níveis: **conceitual** (DER) → **lógico** (tabelas, chaves) → **físico** (tipos, índices, SGBD específico).
- **Normalização**: **1FN** (valores atômicos, sem grupos repetitivos) · **2FN** (sem dependência **parcial** da chave composta) · **3FN** (sem dependência **transitiva**) · **FNBC** (todo determinante é chave candidata) · **4FN** (sem dependências multivaloradas) · **5FN** (sem dependências de junção). Objetivo: eliminar redundância e **anomalias** de inserção, atualização e exclusão.

## 2. SQL — categorias e comandos
| Categoria | Comandos |
|---|---|
| **DDL** (definição) | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME`, `COMMENT` |
| **DML** (manipulação) | `SELECT`*, `INSERT`, `UPDATE`, `DELETE`, `MERGE` |
| **DCL** (controle) | **`GRANT`**, **`REVOKE`** |
| **DTL/TCL** (transação) | `COMMIT`, `ROLLBACK`, `SAVEPOINT`, `SET TRANSACTION` |
*Algumas classificações separam o `SELECT` como **DQL**. `TRUNCATE` é DDL (não dispara triggers de linha; no Oracle e MySQL faz commit implícito; no PostgreSQL é transacional).

```sql
-- Índice (Oracle, PostgreSQL e MySQL) — cobrado pela FCC
CREATE INDEX idx_ano_processo ON processo (ano);
CREATE UNIQUE INDEX uk_numero ON processo (numero);
-- Controle de acesso
GRANT SELECT, INSERT ON processo TO analista;
REVOKE INSERT ON processo FROM analista;
GRANT SELECT ON processo TO analista WITH GRANT OPTION;   -- pode repassar o privilégio
-- MERGE (upsert) — Oracle; PostgreSQL 15+
MERGE INTO processo p USING carga c ON (p.numero = c.numero)
WHEN MATCHED THEN UPDATE SET situacao = c.situacao
WHEN NOT MATCHED THEN INSERT (numero, situacao) VALUES (c.numero, c.situacao);
-- PostgreSQL também tem: INSERT ... ON CONFLICT (numero) DO UPDATE SET ...;  MySQL: INSERT ... ON DUPLICATE KEY UPDATE ...
```
- **Ordem lógica**: FROM → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT/FETCH.
- **Limitar linhas**: PostgreSQL/MySQL `LIMIT 10 OFFSET 20`; Oracle 12c+ e padrão SQL `FETCH FIRST 10 ROWS ONLY` (antes, `ROWNUM`); SQL Server `TOP 10`.
- **Funções de janela**: `ROW_NUMBER() OVER (PARTITION BY vara ORDER BY data)`, `RANK`, `DENSE_RANK`, `LAG`, `LEAD`, `SUM() OVER`.
- **CTE**: `WITH ativos AS (SELECT ...) SELECT ... FROM ativos;` — **recursiva** com `WITH RECURSIVE` (PostgreSQL/MySQL 8).
- JOINs (INNER, LEFT, RIGHT, FULL, CROSS, self), `UNION` × `UNION ALL`, `INTERSECT`, `EXCEPT` (Oracle: `MINUS`), subconsultas correlacionadas, `EXISTS`, views (e **views materializadas** — PostgreSQL `REFRESH MATERIALIZED VIEW`).

## 3. Gerência de transações
- **ACID**: Atomicidade, Consistência, Isolamento, Durabilidade (garantida por **log de transações** — WAL no PostgreSQL, *redo log* no Oracle/InnoDB).
- **Anomalias**: leitura suja, leitura não repetível, leitura fantasma (+ *lost update*, *write skew*).
| Nível (SQL padrão) | Leitura suja | Não repetível | Fantasma |
|---|:-:|:-:|:-:|
| Read Uncommitted | possível | possível | possível |
| **Read Committed** | evitada | possível | possível |
| **Repeatable Read** | evitada | evitada | possível* |
| **Serializable** | evitada | evitada | evitada |
*No PostgreSQL, Repeatable Read (*snapshot isolation*) também evita fantasmas.
- **Padrões**: **PostgreSQL = Read Committed**; **Oracle = Read Committed** (oferece só Read Committed e Serializable, além de Read Only); **MySQL/InnoDB = Repeatable Read**; SQL Server = Read Committed.
- **Concorrência**: **bloqueios** (compartilhado S / exclusivo X; granularidade linha/página/tabela), **2PL** (fase de crescimento e de encolhimento; estrito: libera no commit), **MVCC** (multiversão — leitores não bloqueiam escritores: PostgreSQL, Oracle, InnoDB), *timestamps*. **Deadlock**: o SGBD detecta (grafo de espera) e aborta uma vítima. `SELECT ... FOR UPDATE` (bloqueio pessimista); controle **otimista** por coluna de versão.
- `SAVEPOINT sp1; ... ROLLBACK TO SAVEPOINT sp1;`

## 4. Tuning de banco de dados
- **Plano de execução**: PostgreSQL **`EXPLAIN`** / **`EXPLAIN ANALYZE`** (executa e mostra tempos reais) / `EXPLAIN (ANALYZE, BUFFERS)`; Oracle **`EXPLAIN PLAN FOR ...`** + `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);`, AWR/ADDM, SQL Tuning Advisor; MySQL `EXPLAIN`, `EXPLAIN ANALYZE` (8.0.18+).
- Operações: *Seq Scan* / *Full Table Scan* × *Index Scan* × *Index Only Scan* × *Bitmap Heap Scan*; junções *Nested Loop*, *Hash Join*, *Merge Join*.
- **Estatísticas atualizadas**: PostgreSQL `ANALYZE` (e **autovacuum**); Oracle `DBMS_STATS.GATHER_TABLE_STATS('ESQUEMA','PROCESSO')`; MySQL `ANALYZE TABLE`.
- **PostgreSQL e MVCC**: `UPDATE`/`DELETE` deixam **tuplas mortas** → **`VACUUM`** recupera o espaço para reutilização (`VACUUM FULL` reescreve a tabela e devolve espaço ao SO, com bloqueio exclusivo); **autovacuum** automatiza; evita *transaction ID wraparound*.
- **Índices**: **B-tree** (padrão — igualdade e faixa), **Hash** (igualdade), **GIN** (arrays, **JSONB**, *full-text*), **GiST** (geométricos, faixas), **BRIN** (tabelas enormes com dados correlacionados à ordem física, ex.: datas), índices **parciais** (`WHERE ativo`), de **expressão** (`ON (lower(email))`), **cobertura** (`INCLUDE`); Oracle **bitmap** (baixa cardinalidade, DW) e *function-based*; MySQL InnoDB: chave primária **clusterizada**.
- Boas práticas: evitar função sobre coluna indexada no WHERE (anula o índice), `SELECT *` desnecessário, `LIKE '%texto'`; usar paginação por chave; particionamento (range, list, hash); *connection pooling* (PgBouncer, HikariCP).

### Parâmetros de memória (cobrado!)
| SGBD | Parâmetro | Função |
|---|---|---|
| **PostgreSQL** | `shared_buffers` | Cache de páginas compartilhado (≈ 25% da RAM, ponto de partida) |
| | `work_mem` | Memória **por operação** de ordenação/hash |
| | `maintenance_work_mem` | VACUUM, CREATE INDEX |
| | `effective_cache_size` | Estimativa de cache do SO (só influencia o otimizador) |
| | `max_connections`, `wal_buffers` | — |
| **Oracle 19c** | **`DB_CACHE_SIZE`** | **Buffer cache** (blocos de dados) na **SGA** |
| | `SHARED_POOL_SIZE` | *Library cache* (SQL parseado) e *dictionary cache* |
| | `LOG_BUFFER` | *Redo log buffer* |
| | `SGA_TARGET`, `PGA_AGGREGATE_TARGET`, `MEMORY_TARGET` | Gerência automática de memória |
| **MySQL 8 (InnoDB)** | **`innodb_buffer_pool_size`** | Cache de dados e índices do InnoDB (principal parâmetro) |
| | `innodb_log_file_size` / `innodb_redo_log_capacity` | Redo log |

```sql
-- Oracle: alterar e persistir no SPFILE (vale após reinício); SCOPE = MEMORY | SPFILE | BOTH
ALTER SYSTEM SET DB_CACHE_SIZE = 2G SCOPE = SPFILE;
-- MySQL 8: na instância em execução (dinâmico, em bytes) / persistindo entre reinícios
SET GLOBAL innodb_buffer_pool_size = 5368709120;      -- 5 GB
SET PERSIST innodb_buffer_pool_size = 5368709120;     -- grava em mysqld-auto.cnf
-- PostgreSQL: grava em postgresql.auto.conf; shared_buffers exige reinício
ALTER SYSTEM SET work_mem = '64MB';
SELECT pg_reload_conf();
```

## 5. PL/pgSQL e PL/SQL
### PL/pgSQL (PostgreSQL)
```sql
CREATE OR REPLACE FUNCTION total_por_ano(p_ano INT)
RETURNS INTEGER
LANGUAGE plpgsql AS $$
DECLARE
    v_total INTEGER;
BEGIN
    SELECT count(*) INTO v_total FROM processo WHERE ano = p_ano;
    IF v_total = 0 THEN
        RAISE NOTICE 'Nenhum processo em %', p_ano;
    END IF;
    RETURN v_total;
EXCEPTION
    WHEN others THEN RAISE EXCEPTION 'Erro: %', SQLERRM;
END;
$$;

-- Trigger: função que RETORNA TRIGGER + CREATE TRIGGER
CREATE FUNCTION trg_auditoria() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.atualizado_em := now();     -- NEW/OLD; TG_OP = 'INSERT' | 'UPDATE' | 'DELETE'
    RETURN NEW;                     -- em BEFORE, retornar NULL cancela a operação na linha
END; $$;
CREATE TRIGGER t_processo BEFORE UPDATE ON processo
    FOR EACH ROW EXECUTE FUNCTION trg_auditoria();
```
- **Procedures** (PostgreSQL 11+): `CREATE PROCEDURE ... ; CALL proc();` — podem fazer `COMMIT` dentro. Funções retornam valor e são chamadas em `SELECT`.
- Laços: `FOR r IN SELECT ... LOOP ... END LOOP;`, `WHILE`, `FOREACH` (arrays); `RETURN QUERY`, `RETURNS TABLE(...)`, `SETOF`; `%TYPE` e `%ROWTYPE` também existem.

### PL/SQL (Oracle)
```sql
DECLARE
    v_numero processo.numero%TYPE;         -- mesmo tipo da coluna
    r_proc   processo%ROWTYPE;             -- registro com a estrutura da linha
    CURSOR c_ativos IS SELECT * FROM processo WHERE situacao = 'ATIVO';
BEGIN
    SELECT numero INTO v_numero FROM processo WHERE id = 10;
    FOR r IN c_ativos LOOP                  -- cursor FOR: abre, busca e fecha automaticamente
        DBMS_OUTPUT.PUT_LINE(r.numero);
    END LOOP;
EXCEPTION
    WHEN NO_DATA_FOUND THEN DBMS_OUTPUT.PUT_LINE('Não encontrado');      -- SELECT INTO sem linhas
    WHEN TOO_MANY_ROWS THEN DBMS_OUTPUT.PUT_LINE('Mais de uma linha');   -- SELECT INTO com várias
    WHEN OTHERS THEN RAISE_APPLICATION_ERROR(-20001, 'Erro: ' || SQLERRM); -- códigos -20000 a -20999
END;
/
```
- Blocos **anônimos** × **nomeados** (procedures, functions, **packages** = *specification* + *body*, triggers). Cursores **implícitos** (`SQL%ROWCOUNT`, `SQL%FOUND`) e **explícitos** (`OPEN/FETCH/CLOSE`, `%NOTFOUND`). Triggers usam **`:NEW`** e **`:OLD`**; `BEFORE/AFTER`, `FOR EACH ROW`, `INSTEAD OF` (views). Exceções pré-definidas: `NO_DATA_FOUND`, `TOO_MANY_ROWS`, `ZERO_DIVIDE`, `DUP_VAL_ON_INDEX`, `VALUE_ERROR`, `INVALID_CURSOR`.
- `BULK COLLECT` e `FORALL` (processamento em lote — menos trocas de contexto SQL/PL/SQL).

## 6. Versões cobradas
| Versão | Novidades principais |
|---|---|
| **PostgreSQL 15** (2022) | Comando **`MERGE`**; **revogado o privilégio CREATE de PUBLIC no schema `public`**; compressão **LZ4/Zstandard** (WAL e backup); melhorias na replicação lógica (filtros de linha e de coluna); `UNIQUE NULLS NOT DISTINCT` |
| **PostgreSQL 16** (2023) | Replicação lógica **a partir de standby**; visão **`pg_stat_io`**; construtores **SQL/JSON** (`JSON_ARRAY`, `JSON_OBJECT`, `IS JSON`); paralelismo em FULL/RIGHT JOIN; novo papel `pg_create_subscription` |
| **PostgreSQL 17** (2024) | **Backup incremental** (`pg_basebackup --incremental` + `pg_combinebackup`); **`JSON_TABLE`**; `MERGE ... RETURNING`; VACUUM com menos memória; `pg_createsubscriber`; failover de slots de replicação lógica |
| **PostgreSQL 18** (set/2025) | **Subsistema de E/S assíncrona** (`io_method`); função **`uuidv7()`**; **colunas geradas virtuais** (padrão); **autenticação OAuth**; **skip scan** em índices B-tree multicoluna; `OLD`/`NEW` no `RETURNING`; restrições temporais (`WITHOUT OVERLAPS`); `pg_upgrade` preserva estatísticas; *checksums* de dados habilitados por padrão no `initdb`; senha MD5 obsoleta |
| **Oracle 19c** | Versão de **suporte de longo prazo**; arquitetura **multitenant** (**CDB** contêiner com **PDBs** plugáveis); **indexação automática** (Autonomous/Exadata); estatísticas em tempo real; *SQL Quarantine*; tabelas particionadas híbridas; Active Data Guard com redirecionamento de DML |
| **MySQL 8** | **CTEs** (inclusive recursivas) e **funções de janela**; **papéis (roles)**; dicionário de dados transacional; autenticação padrão **`caching_sha2_password`**; charset padrão **utf8mb4**; índices **invisíveis** e **descendentes**; `SET PERSIST`; melhorias em JSON; InnoDB como engine padrão |

- Conceitos Oracle: **instância** (SGA + processos de background: DBWn, LGWR, CKPT, SMON, PMON, ARCn) × **banco** (datafiles, control files, redo log files); **tablespaces** (SYSTEM, SYSAUX, UNDO, TEMP, USERS); **SPFILE** (binário) × PFILE (texto); RMAN (backup); Data Guard; `SYS`/`SYSTEM`; esquema = usuário.

## 7. NoSQL
| Tipo | Exemplos | Uso |
|---|---|---|
| Chave-valor | **Redis**, DynamoDB | Cache, sessões, filas |
| Documento | **MongoDB** (BSON, coleções), CouchDB, Couchbase | Conteúdo, catálogos, APIs |
| Colunar (família de colunas) | **Cassandra**, HBase | Escrita massiva, séries temporais |
| Grafo | **Neo4j** (Cypher) | Relacionamentos, fraudes |
| Busca | **Elasticsearch** | Busca textual, logs |
- **CAP** (em partição: consistência × disponibilidade); **BASE** (Basically Available, Soft state, Eventual consistency); escalabilidade **horizontal** (*sharding*), replicação, esquema flexível. PostgreSQL com **JSONB** cobre muitos casos documentais.

## 8. Ciência de dados e estatística
- **Descritiva** (resumir: média, mediana, moda, desvio padrão, quartis, boxplot — *outliers* além de 1,5 × IQR) × **inferencial** (amostra → população: intervalos de confiança, **testes de hipótese**, p-valor; erro tipo I = rejeitar H₀ verdadeira; tipo II = não rejeitar H₀ falsa).
- **Correlação de Pearson** (−1 a 1; linear; **correlação não implica causalidade**); regressão linear (mínimos quadrados, R²).
- **Processo**: CRISP-DM (entendimento do negócio → entendimento dos dados → **preparação** → modelagem → avaliação → implantação); limpeza (nulos, duplicatas, outliers), normalização/padronização, *feature engineering*, codificação de categóricas (*one-hot*).
- Ferramentas: Python (**pandas**, NumPy, **scikit-learn**, Matplotlib), R (`read.csv()`, `data.frame`, `summary()`), Jupyter, SQL.

## 9. Big Data — ferramentas e arquiteturas
- **Vs**: Volume, Velocidade, Variedade, Veracidade, Valor.
- **Hadoop**: **HDFS** (armazenamento distribuído — NameNode/DataNodes, blocos replicados, padrão 3 réplicas), **MapReduce** (processamento em lote: map → shuffle → reduce), **YARN** (gerência de recursos); Hive (SQL sobre Hadoop), HBase.
- **Apache Spark**: processamento **em memória** (até 100× mais rápido que MapReduce em certos casos), **RDD** (imutável, distribuído, tolerante a falhas pela linhagem), **DataFrame/Dataset**, **avaliação preguiçosa** (*transformações* lazy × *ações* disparam a execução), Spark SQL, Structured Streaming, MLlib.
- **Kafka** (streaming de eventos), **Flink** (stream processing), **Airflow** (orquestração de pipelines em **DAGs**).
- **Data Lake** (dados brutos, *schema-on-read*), **Data Warehouse** (estruturado, *schema-on-write*), **Lakehouse** (Delta Lake, Apache Iceberg — transações ACID sobre o lake). Arquitetura **medallion**: bronze (bruto) → silver (limpo) → gold (agregado para negócio).
- **Arquitetura Lambda** (camada **batch** + camada **speed/streaming** + camada de **serving**) × **Kappa** (só streaming, reprocessa pelo log).

## 10. Machine learning
| Supervisionado (dados rotulados) | Não supervisionado (sem rótulos) |
|---|---|
| **Classificação** (categoria): regressão **logística**, árvores de decisão, **random forest**, gradient boosting (XGBoost), **SVM**, **k-NN**, **Naive Bayes**, redes neurais | **Agrupamento**: **k-means**, DBSCAN, hierárquico |
| **Regressão** (valor contínuo): linear, ridge/lasso, árvores de regressão, SVR | **Redução de dimensionalidade**: **PCA**, t-SNE; **regras de associação** (Apriori); **detecção de anomalias**; autoencoders |
- Por **reforço**: agente, ambiente, recompensa (Q-learning). **Semissupervisionado** e **autossupervisionado** (pré-treino de LLMs).
- Ex. FCC/2023: prever se uma decisão será **favorável ou desfavorável** (classe binária) → **regressão logística**. CNN = imagens; k-means = agrupamento; SVR = regressão; autoencoder = compressão/anomalia.

### Avaliação de modelos
- Divisão **treino / validação / teste**; **validação cruzada k-fold**; evitar **vazamento de dados** (*data leakage*).
- **Overfitting** (alta variância: ótimo no treino, ruim no teste) × **underfitting** (alto viés). Remédios: regularização (L1/L2, dropout), mais dados, *early stopping*, modelo mais simples.
- **Matriz de confusão** → **acurácia** (VP+VN)/total · **precisão** VP/(VP+FP) · **recall/sensibilidade** VP/(VP+FN) · **especificidade** VN/(VN+FP) · **F1** (média harmônica de precisão e recall) · **ROC/AUC** (TPR × FPR em vários limiares). Classes desbalanceadas → precisão/recall/F1, não acurácia.
- Regressão: **MAE**, **MSE**, **RMSE**, **R²**.
- Agrupamento: coeficiente de **silhueta**, método do cotovelo (k-means).

## 11. IA generativa, ética e governança
- **LLM** (Transformer, autoatenção), tokens, **janela de contexto**, **temperatura**, **alucinação**; **engenharia de prompts** (zero-shot, few-shot, chain-of-thought); **RAG** (recupera trechos de uma base — embeddings em banco vetorial, ex.: **pgvector** no PostgreSQL — e os injeta no prompt; reduz alucinação, não altera pesos) × **fine-tuning** (altera pesos); **agentes** (LLM + ferramentas + memória).
- **Riscos**: prompt injection (direta/indireta), vazamento de dados, viés/discriminação, alucinação, *data poisoning*, uso indevido de dados pessoais (**LGPD**).
- **Ética e governança**: transparência, explicabilidade, **supervisão humana**, não discriminação, segurança, privacidade, responsabilização; **NIST AI RMF** (Govern, Map, Measure, Manage); **ISO/IEC 42001** (sistema de gestão de IA); **PL 2.338/2023** (abordagem por risco).
- **Judiciário**: **Resolução CNJ nº 615/2025** (substituiu a Res. 332/2020) — governança e uso de IA no Poder Judiciário: classificação por **risco**, **supervisão humana** obrigatória das decisões, transparência, auditabilidade, proteção de dados, vedações a usos de risco excessivo e regras para uso de IA generativa por magistrados e servidores (confirmar detalhes no texto). Plataforma **Sinapses** (CNJ) para modelos de IA do Judiciário.

## 12. DataOps, MLOps e BI
- **DataOps**: práticas **ágeis + DevOps + Lean** aplicadas a **pipelines de dados** — automação, **testes de qualidade de dados**, versionamento, CI/CD de pipelines, **observabilidade** de dados (frescor, volume, esquema), colaboração entre engenharia e negócio.
- **MLOps**: DevOps para **machine learning** — **versionamento de dados, código e modelos** (DVC, Git), **rastreamento de experimentos** e **registro de modelos** (**MLflow**), **CI/CD/CT** (treinamento contínuo), *feature store*, **monitoramento em produção** (*data drift* — mudança na distribuição das entradas; *concept drift* — mudança na relação entrada→saída), retreinamento; Kubeflow, SageMaker.
- **BI**: processo de **coleta, organização, análise e compartilhamento** de informações para apoiar decisões.
  - **Pipeline de dados**: **ingestão** (batch/streaming, CDC — captura de mudanças) → **transformação** (**ETL**: transforma antes de carregar, em *staging*; **ELT**: carrega e transforma no destino — comum em nuvem) → **armazenamento** (DW/data marts — modelo **estrela**: fato + dimensões; **floco de neve**) → **consumo** (OLAP: drill-down, roll-up, slice, dice, pivot; dashboards e relatórios — Power BI, Tableau, Metabase, Superset).
  - **Orquestração**: agendamento e dependências entre tarefas (Apache **Airflow** — DAGs; Dagster, Prefect); **integração** de fontes heterogêneas (APIs, bancos, arquivos); qualidade e governança (catálogo, linhagem, metadados).

## ⚠️ Pegadinhas
1. Oracle: `ALTER SYSTEM SET DB_CACHE_SIZE=2G SCOPE=SPFILE;` (não `ALTER DATABASE`); MySQL: `SET GLOBAL innodb_buffer_pool_size = <bytes>`.
2. `CREATE INDEX nome ON tabela (coluna);` — não existe `ALTER TABLE ... ADD INDEX` no Oracle (existe no MySQL).
3. Isolamento padrão: PostgreSQL e Oracle = **Read Committed**; MySQL = **Repeatable Read**.
4. `NO_DATA_FOUND` (nenhuma linha) × `TOO_MANY_ROWS` (várias) em `SELECT INTO`.
5. PostgreSQL 15 = **MERGE**; 17 = **backup incremental** e **JSON_TABLE**; 18 = **E/S assíncrona** e **uuidv7**.
6. Regressão **logística** = classificação; k-means = não supervisionado.
7. Spark: transformações são **lazy**; ações disparam.

## Questões comentadas (inéditas, estilo FCC)

**Q1.** Um DBA deseja aumentar o *buffer cache* do Oracle 19c para 4 GB, com a alteração valendo **somente** após a próxima reinicialização da instância. O comando correto é:
(A) `ALTER DATABASE SET DB_CACHE_SIZE=4G;` (B) `ALTER SYSTEM SET DB_CACHE_SIZE=4G SCOPE=MEMORY;` (C) **`ALTER SYSTEM SET DB_CACHE_SIZE=4G SCOPE=SPFILE;`** (D) `SET GLOBAL DB_CACHE_SIZE=4G;` (E) `ALTER SESSION SET DB_CACHE_SIZE=4G SCOPE=BOTH;`
✅ **C.**

**Q2.** No PostgreSQL, após muitas operações de UPDATE e DELETE, para recuperar o espaço ocupado por tuplas mortas e atualizar as estatísticas usadas pelo otimizador, deve-se executar:
(A) `REINDEX DATABASE`. (B) `TRUNCATE`. (C) **`VACUUM ANALYZE`.** (D) `CLUSTER`. (E) `CHECKPOINT`.
✅ **C.**

**Q3.** Em PL/SQL, um `SELECT ... INTO` que não retorna nenhuma linha dispara a exceção:
(A) TOO_MANY_ROWS. (B) **NO_DATA_FOUND.** (C) INVALID_CURSOR. (D) ZERO_DIVIDE. (E) VALUE_ERROR.
✅ **B.**

**Q4.** Recurso introduzido no PostgreSQL 17 que permite realizar backups contendo apenas os blocos alterados desde um backup anterior:
(A) MERGE. (B) **backup incremental com pg_basebackup e pg_combinebackup.** (C) replicação lógica a partir de standby. (D) E/S assíncrona. (E) pg_stat_io.
✅ **B.**

**Q5.** Um modelo de detecção de fraudes apresentou VP = 80, FN = 20, FP = 40 e VN = 860. Sua precisão e seu recall são, respectivamente:
(A) 0,80 e 0,67. (B) **0,67 e 0,80.** (C) 0,94 e 0,80. (D) 0,67 e 0,96. (E) 0,80 e 0,94.
✅ **B.** Precisão = 80/(80+40) ≈ 0,67; recall = 80/(80+20) = 0,80.

**Q6.** Prática que aplica princípios de DevOps ao ciclo de vida de modelos de aprendizado de máquina, incluindo versionamento de modelos, treinamento contínuo e monitoramento de *drift* em produção, é denominada:
(A) DataOps. (B) FinOps. (C) **MLOps.** (D) GitOps. (E) ETL.
✅ **C.**
