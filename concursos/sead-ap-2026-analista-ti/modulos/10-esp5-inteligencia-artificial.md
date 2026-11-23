# Módulo 10 — Específicos 5: Inteligência Artificial, IA Generativa e Agentes

> Tema **novo** em editais de TI, com **6 subitens**. Bancas cobram **conceitos e siglas** (RAG, LLM, embeddings, prompt injection, alucinação, few-shot) e **governança/LGPD**. Estimativa: 2–3 questões e forte candidato à **discursiva**.

## Mapa do edital (item 5)
5.1 Fundamentos de IA, ML e PLN · 5.2 LLM e engenharia de prompts · 5.3 RAG · 5.4 Automação de fluxos e agentes · 5.5 Riscos e segurança de IA · 5.6 Governança, ética, privacidade e uso responsável no setor público (LGPD).

## 5.1 Fundamentos
- **IA**: sistemas que executam tarefas que exigiriam inteligência humana (percepção, raciocínio, linguagem, decisão).
- **IA fraca/estreita** (tarefa específica — todas as atuais) × **IA forte/geral (AGI)** (hipotética). **Simbólica** (regras, sistemas especialistas) × **conexionista** (redes neurais).
- Hierarquia: **IA ⊃ Machine Learning ⊃ Deep Learning ⊃ IA generativa/LLMs**.

### Machine Learning — tipos de aprendizado
| Tipo | Dados | Tarefas | Algoritmos |
|---|---|---|---|
| **Supervisionado** | **Rotulados** (entrada + resposta) | **Classificação** (categoria: spam/não spam) e **regressão** (valor contínuo: preço) | Regressão linear/logística, árvores de decisão, **random forest**, SVM, k-NN, Naive Bayes, redes neurais |
| **Não supervisionado** | **Sem rótulos** | **Agrupamento (clustering)**, redução de dimensionalidade, associação, anomalias | **k-means**, DBSCAN, hierárquico, **PCA**, Apriori |
| **Por reforço** | **Agente** interage com **ambiente**, recebe **recompensas/punições** | Jogos, robótica, controle | Q-learning, policy gradient |
| Semissupervisionado / autossupervisionado | Poucos rótulos / rótulos gerados dos próprios dados | Pré-treino de LLMs | — |

> ⚠️ **Regressão logística** é algoritmo de **classificação**, apesar do nome. **k-means** (agrupamento, não supervisionado) ≠ **k-NN** (classificação, supervisionado).

- **Divisão dos dados**: treino / validação / teste; **validação cruzada (k-fold)**.
- **Overfitting** (sobreajuste: decora o treino, vai mal em dados novos — alta variância) × **underfitting** (modelo simples demais — alto viés). Remédios para overfitting: mais dados, regularização (L1/L2, dropout), modelo mais simples, *early stopping*.
- **Matriz de confusão**: VP, VN, FP (falso alarme, erro tipo I), FN (erro tipo II).

| Métrica | Fórmula | Use quando |
|---|---|---|
| **Acurácia** | (VP+VN)/total | Classes balanceadas |
| **Precisão** | VP/(VP+**FP**) | Falso positivo é caro (ex.: bloquear e-mail legítimo) |
| **Recall / sensibilidade** | VP/(VP+**FN**) | Falso negativo é caro (ex.: não detectar fraude/doença) |
| **F1-score** | média harmônica de precisão e recall | Classes desbalanceadas |
| AUC-ROC | área sob a curva ROC | Comparar classificadores |
| MAE, RMSE, R² | — | Regressão |

- **Deep Learning**: redes neurais com muitas camadas. **CNN** (imagens), **RNN/LSTM** (sequências — legado em texto), **Transformers** (atenção — base dos LLMs), GANs e **modelos de difusão** (geração de imagens).

### Processamento de Linguagem Natural (PLN/NLP)
- Pré-processamento: **tokenização**, normalização, remoção de **stopwords**, **stemming** (corta ao radical: "estudando" → "estud") × **lematização** (forma canônica do dicionário: "estudando" → "estudar").
- Representações: bag-of-words, **TF-IDF**, **word embeddings** (Word2Vec, GloVe), embeddings contextuais (BERT).
- Tarefas: classificação de texto, **análise de sentimento**, **NER** (reconhecimento de entidades nomeadas: pessoas, órgãos, datas), tradução, sumarização, perguntas e respostas, chatbots.
- **Transformer** (artigo "Attention Is All You Need", Google, 2017): mecanismo de **autoatenção** (*self-attention*) processa a sequência **em paralelo**. **BERT** (encoder — compreensão) × **GPT** (decoder — geração, autorregressivo) × T5 (encoder-decoder).

## 5.2 LLMs e engenharia de prompts
- **LLM (Large Language Model)**: modelo Transformer com bilhões de **parâmetros**, pré-treinado em enormes volumes de texto para **prever o próximo token**.
- **Ciclo de treino**: **pré-treino** (autossupervisionado) → **ajuste fino (fine-tuning)** por instruções → alinhamento com **RLHF** (aprendizado por reforço com feedback humano) ou similares.
- **Token**: unidade de texto (pedaço de palavra) — define custo e limite. **Janela de contexto**: quantidade máxima de tokens (entrada + saída) que o modelo considera de uma vez.
- **Parâmetros de geração**: **temperatura** (baixa ≈ respostas mais determinísticas e factuais; alta ≈ mais criativas e variadas), **top-p** (amostragem por núcleo), **top-k**, máximo de tokens.
- **Alucinação**: resposta **fluente, porém falsa ou inventada** (inclusive citações). Mitigações: RAG com fontes, temperatura baixa, pedir citações, verificação humana.
- Modelos **fundacionais** (*foundation models*), **multimodais** (texto + imagem + áudio), **abertos** (pesos disponíveis: Llama, Mistral) × **proprietários** (via API). **SLM**: modelos pequenos, rodam localmente (bom para dados sensíveis).

### Técnicas de engenharia de prompts
| Técnica | Descrição |
|---|---|
| **Zero-shot** | Só a instrução, sem exemplos |
| **Few-shot** (one-shot) | Instrução + **alguns exemplos** de entrada/saída |
| **Chain-of-Thought (CoT)** | Pede raciocínio **passo a passo** antes da resposta |
| **Role / persona prompting** | "Você é um analista de licitações…" |
| **System prompt** | Instruções de comportamento definidas pelo desenvolvedor, com prioridade sobre o usuário |
| Delimitadores e formato | Separar contexto com marcadores; pedir saída em **JSON**/tabela |
| **ReAct** | Alterna **Raciocínio (Reason)** e **Ação (Act — usar ferramentas)** |
| Self-consistency / prompt chaining | Várias respostas e votação / dividir tarefa em etapas |

Boas práticas: ser **específico e claro**, dar **contexto**, definir **formato de saída**, dar **exemplos**, definir **restrições** ("responda só com base no texto fornecido; se não souber, diga que não sabe").

## 5.3 RAG — Retrieval-Augmented Generation (Geração Aumentada por Recuperação)
**Ideia**: antes de responder, o sistema **recupera** trechos relevantes de uma base de conhecimento e os **insere no prompt** como contexto. O LLM gera a resposta **fundamentada** nesses trechos.

**Pipeline**
1. **Ingestão/indexação** (offline): coletar documentos (leis, normas, manuais) → **dividir em *chunks*** (pedaços com sobreposição) → gerar **embeddings** → armazenar em **banco vetorial** com metadados.
2. **Recuperação** (online): a pergunta vira embedding → **busca por similaridade** (cosseno; k vizinhos) — opcionalmente **busca híbrida** (vetorial + palavra-chave/BM25) e **re-ranking**.
3. **Aumento**: montar o prompt = instruções + **trechos recuperados** + pergunta.
4. **Geração**: o LLM responde, idealmente **citando as fontes**.

| | **RAG** | **Fine-tuning** |
|---|---|---|
| O que muda | O **contexto** fornecido (modelo intacto) | Os **pesos** do modelo |
| Atualização | Basta atualizar a base (**dados recentes**) | Exige novo treino |
| Melhor para | **Conhecimento** factual, específico, que muda; **citação de fontes** | **Estilo, formato, comportamento**, tarefas especializadas |
| Custo | Menor | Maior |
| Controle de acesso | Pode filtrar documentos por perfil do usuário | Difícil (conhecimento "embutido") |

- **Benefícios**: reduz **alucinação**, usa **dados internos e atualizados** sem retreinar, permite **rastreabilidade** (fontes), respeita permissões.
- **Riscos**: recuperar trecho errado/desatualizado, **prompt injection indireta** (instruções maliciosas escondidas nos documentos), vazamento de documentos sigilosos se não houver controle de acesso, *chunking* ruim.
- Avaliação: **relevância do contexto**, **fidelidade (groundedness)** da resposta às fontes, relevância da resposta.
- Variações: GraphRAG (grafos de conhecimento), RAG agêntico.

## 5.4 Automação de fluxos e agentes de IA
- **Automação tradicional / RPA**: regras fixas, roteiros determinísticos ("se X, faça Y"); robôs que imitam cliques (UiPath, Power Automate). Ferramentas de fluxo: **n8n**, Zapier, Make, Power Automate, Airflow.
- **Agente de IA**: sistema em que um LLM **decide autonomamente os passos** para atingir um objetivo, usando:
  - **Ferramentas (tools / function calling)**: APIs, busca, banco de dados, execução de código;
  - **Memória** (curto prazo: contexto; longo prazo: banco vetorial);
  - **Planejamento** e **ciclo percepção → raciocínio → ação → observação** (ReAct);
  - **Orquestração** de **múltiplos agentes** (multiagente: cada agente com um papel).
- **MCP (Model Context Protocol)**: padrão aberto (lançado pela Anthropic, 2024) para conectar modelos/agentes a **ferramentas e fontes de dados** de forma padronizada (cliente–servidor). **A2A**: protocolo para comunicação entre agentes.
- **Workflow com LLM** (passos definidos pelo desenvolvedor) × **agente** (o modelo decide os passos). Quanto mais autonomia, mais **controles** são necessários.
- **Human-in-the-loop**: aprovação humana em ações sensíveis (pagamentos, envio de ofícios, exclusões, decisões sobre direitos).
- Usos no setor público: triagem de demandas da ouvidoria, atendimento ao cidadão (chatbot com RAG), análise preliminar de processos e editais, resumo de documentos, classificação de protocolos, apoio à elaboração de ETP/TR (sempre com revisão humana).

## 5.5 Riscos e segurança de sistemas de IA
### OWASP Top 10 para Aplicações com LLM (2025)
| # | Risco | Descrição |
|---|---|---|
| LLM01 | **Prompt Injection** | Entradas manipulam o comportamento do modelo. **Direta** (usuário: "ignore as instruções anteriores…") ou **indireta** (instruções escondidas em páginas, e-mails, documentos do RAG) |
| LLM02 | **Sensitive Information Disclosure** | Vazamento de dados pessoais, segredos, dados de treino |
| LLM03 | **Supply Chain** | Modelos, datasets, bibliotecas e plugins de terceiros comprometidos |
| LLM04 | **Data and Model Poisoning** | Envenenamento de dados de treino/ajuste/embeddings |
| LLM05 | **Improper Output Handling** | Usar a saída do LLM sem validação (gera XSS, SQLi, execução de código) |
| LLM06 | **Excessive Agency** | Agente com permissões/ferramentas/autonomia demais |
| LLM07 | **System Prompt Leakage** | Vazamento das instruções de sistema (não guarde segredos nelas) |
| LLM08 | **Vector and Embedding Weaknesses** | Falhas em RAG/bancos vetoriais (acesso indevido, injeção, inversão de embeddings) |
| LLM09 | **Misinformation** | Desinformação/alucinação com aparência confiável |
| LLM10 | **Unbounded Consumption** | Consumo ilimitado (custos, negação de serviço, extração do modelo) |

- Outros ataques: **jailbreak** (burlar salvaguardas), **exemplos adversariais**, **inversão de modelo** e **inferência de pertencimento** (descobrir dados de treino), roubo de modelo.
- **Mitigações**: **guardrails** (filtros de entrada e saída), **menor privilégio** para ferramentas do agente, **aprovação humana**, separar instruções de dados não confiáveis, **validar/sanitizar a saída**, limitar taxa e custo, **red teaming**, logs e monitoramento, avaliação contínua, não colocar segredos no prompt.
- **Frameworks**: **NIST AI RMF 1.0** (funções **Govern, Map, Measure, Manage**), **ISO/IEC 42001:2023** (sistema de **gestão de IA** — certificável), ISO/IEC 23894 (riscos de IA), MITRE ATLAS.

## 5.6 Governança, ética, privacidade e uso responsável no setor público
### Princípios de IA responsável (convergentes em OCDE, UNESCO, EBIA, PL 2.338)
**Centralidade da pessoa humana**, **transparência**, **explicabilidade**, **não discriminação** (combate a **vieses**), **supervisão humana**, **segurança e robustez**, **privacidade e proteção de dados**, **responsabilização (accountability)**, sustentabilidade.

### Marco brasileiro
| Instrumento | Conteúdo |
|---|---|
| **EBIA** — Estratégia Brasileira de IA (Portaria MCTI 4.617/2021) | Eixos de governança, regulação, uso ético, P&D, força de trabalho, poder público |
| **PBIA** — Plano Brasileiro de IA 2024–2028 ("IA para o Bem de Todos") | Investimentos em infraestrutura, capacitação, IA no serviço público |
| **PL 2.338/2023** (marco legal da IA) | Aprovado no **Senado (dez/2024)**, em tramitação na Câmara (confirmar situação). Abordagem **baseada em risco**: **risco excessivo** (vedado — ex.: pontuação social pelo poder público, manipulação subliminar) e **alto risco** (avaliação de impacto, supervisão humana); direitos das pessoas afetadas |
| **LGPD** | Base legal para tratar dados no treino/uso; **art. 20 — revisão de decisões automatizadas**; princípios de finalidade, necessidade, transparência, não discriminação; **RIPD** |
| **AI Act** (União Europeia, 2024) | Referência internacional: riscos **inaceitável, alto, limitado (transparência), mínimo** |

### Boas práticas para IA no setor público
1. **Base legal** (LGPD art. 7º/11 — em geral, execução de políticas públicas/competência legal) e **finalidade** definida.
2. **Minimização**, anonimização/pseudonimização e **proibição de inserir dados pessoais ou sigilosos em ferramentas públicas** sem contrato e avaliação.
3. **RIPD** e **avaliação de impacto algorítmico** para usos de alto risco.
4. **Transparência ativa**: informar ao cidadão que está interagindo com IA; publicar inventário de sistemas de IA.
5. **Supervisão humana** e **direito de revisão** (art. 20) em decisões que afetem direitos.
6. Testes de **viés** e acurácia por grupo; monitoramento contínuo.
7. **Segurança** (OWASP LLM, controle de acesso no RAG, logs) e **soberania de dados** (localização, contratos — IN SGD 94/2022).
8. **Comitê de governança de IA**, política de uso, capacitação dos servidores.
9. Contratação: especificar requisitos de privacidade, segurança, auditabilidade, propriedade dos dados e **vedação ao uso dos dados do órgão para treinar modelos do fornecedor**.

## ⚠️ Pegadinhas do bloco
1. RAG **não altera os pesos** do modelo; fine-tuning altera.
2. **Temperatura alta** = mais criatividade/aleatoriedade (e mais risco de alucinação).
3. **Few-shot** = com exemplos; **zero-shot** = sem exemplos.
4. **Prompt injection indireta** vem de **conteúdo externo** (documentos, sites), não do usuário.
5. **Precisão** penaliza falso positivo; **recall** penaliza falso negativo.
6. Clustering é **não supervisionado**; classificação e regressão são **supervisionadas**.
7. Dados pessoais usados em IA **continuam sob a LGPD**.

## 🧠 Memorize
- **RAG** = "**R**ecupera, **A**umenta, **G**era".
- **NIST AI RMF** = "**G**overnar, **M**apear, **M**edir, **M**anejar" (GMMM).
- Agente = **LLM + Ferramentas + Memória + Planejamento**.

## Questões comentadas (estilo IDCAP)

**Q1.** Uma técnica de IA generativa consulta uma base de conhecimento externa, recupera trechos relevantes e os insere no contexto do modelo antes da geração da resposta, sem alterar os parâmetros do modelo. Essa técnica é conhecida como:
(A) Fine-tuning. (B) **RAG (Retrieval-Augmented Generation).** (C) RLHF. (D) Transfer learning.
✅ **B.**

**Q2.** Em engenharia de prompts, uma técnica fornece ao modelo alguns exemplos de entrada e saída desejadas; outra solicita que o modelo explicite o raciocínio em etapas antes de responder. São, respectivamente:
(A) Zero-shot e ReAct. (B) **Few-shot e Chain-of-Thought.** (C) Chain-of-Thought e few-shot. (D) Role prompting e zero-shot.
✅ **B.**

**Q3.** Um chatbot de atendimento ao cidadão que usa RAG passou a responder com instruções maliciosas inseridas em um documento PDF indexado na base. Esse ataque é classificado como:
(A) Data poisoning do pré-treino. (B) **Prompt injection indireta.** (C) Jailbreak direto. (D) Negação de serviço.
✅ **B.** A instrução maliciosa veio de conteúdo externo processado pelo modelo.

**Q4.** Um modelo de detecção de fraudes em benefícios deve minimizar os casos de fraude não detectados. A métrica a ser priorizada é:
(A) Precisão. (B) **Recall (sensibilidade).** (C) Acurácia. (D) Especificidade.
✅ **B.** Fraude não detectada = falso negativo.

**Q5.** Algoritmo de aprendizado não supervisionado usado para agrupar registros semelhantes em k grupos:
(A) k-NN. (B) Regressão logística. (C) **k-means.** (D) Random forest.
✅ **C.**

**Q6.** Segundo a LGPD, o titular tem direito a solicitar a revisão de decisões tomadas unicamente com base em tratamento automatizado de dados pessoais que afetem seus interesses. Esse direito está no:
(A) art. 7º. (B) art. 11. (C) art. 18. (D) **art. 20.**
✅ **D.**
