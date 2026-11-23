# Apresentação e Raio-X da Prova

**Concurso**: Tribunal Regional do Trabalho da 8ª Região (Pará e Amapá) — Edital nº 1, de 1º/10/2026 (DOU de 02/10/2026)
**Cargo**: 04 — Analista Judiciário — Área Apoio Especializado — **Especialidade Tecnologia da Informação** — cadastro de reserva — inicial **R$ 16.040,88**
**Banca**: **Fundação Carlos Chagas (FCC)**
**Prova**: **domingo, 17/01/2027, manhã** — objetiva + redação no mesmo dia — **4h30** — Belém, Marabá, Santarém e Macapá
**Requisito**: superior em TI, ou superior em qualquer área + pós-graduação em Informática.

> Fonte: Edital nº 1/2026 (texto do DOU). Confira retificações e o **Edital de Convocação (previsto para 08/12/2026)** no site da FCC.

## Raio-X da prova

| Prova | Questões | Escala | Peso | Caráter |
|---|---:|---|---:|---|
| **Conhecimentos Gerais** | 20 | 0 a 10 | **1** | Habilitatório e classificatório |
| **Conhecimentos Específicos** | 40 | 0 a 10 | **2** | Habilitatório e classificatório |
| **Discursiva — Redação** | 1 | 0 a 10 | — | Eliminatório e classificatório |

- **Nota da objetiva** = (Gerais × 1 + Específicos × 2) ÷ 3. **Mínimo para habilitação: 6,00** (cotistas: 4,80).
- **Cada questão específica vale o dobro** de uma geral na média: acertar 1 específica ≈ 0,167 ponto na nota; 1 geral ≈ 0,167 × ½.
- **Redação**: só são corrigidas as **320 primeiras** colocações da ampla concorrência em TI (mais todos os cotistas habilitados). **Mínimo 6,00.** **20 a 30 linhas.** Tema de **interesse geral**, não necessariamente de TI.
- Alternativas: **A a E** (5). Marcação com caneta de tinta preta ou azul, corpo transparente.
- Não há prova de títulos. A classificação final soma objetiva + redação (confira a fórmula no edital/retificações).

### Distribuição estimada dentro de cada prova (o edital não fixa — estimativa pelo padrão FCC/TRT)

| Conhecimentos Gerais (20) | Estimativa | Conhecimentos Específicos (40) | Estimativa |
|---|---:|---|---:|
| Língua Portuguesa | 7–9 | Noções de Direito Constitucional | 3–5 |
| Matemática, RL e Estatística | 4–5 | Noções de Direito Administrativo (inclui 14.133) | 4–6 |
| Noções de Legislação (TRT8, CNJ, CSJT, Estatuto de Roma, Carta da ONU) | 3–4 | **Tecnologia da Informação** | **28–32** |
| Noções de Direitos Humanos | 2–3 | Inglês técnico (dentro de TI) | 0–2 |
| Direitos das Pessoas com Deficiência | 2–3 | | |

> ⚠️ Atenção: o edital do Analista de TI **não tem Noções de Informática** nos Gerais. Direito Constitucional e Administrativo valem **peso 2**.

## Perfil real da FCC para Analista de TI de TRT (análise da prova TRT-15/2023)
Analisei a prova FCC de dezembro de 2023 para Analista Judiciário – TI do TRT-15 (mesmo formato: 60 questões, 4h30). Conclusões:
1. **Questões práticas e de detalhe**: "Um Analista deseja… deve usar o comando…". Cai **sintaxe exata**: `CREATE INDEX idx ON processo (ano);` no Oracle; `ALTER SYSTEM SET DB_CACHE_SIZE=2G SCOPE=SPFILE;`; `SET GLOBAL innodb_buffer_pool_size = 5368709120;` no MySQL; `git clone` com token.
2. **Stack da PDPJ-Br**: porta padrão do **Spring Eureka (8761)** no `application.properties`; anotação **`@Mapper`** do MapStruct; **WildFly `bin/add-user.sh`**. O edital do TRT-8 lista exatamente essa stack — **é o coração da prova**.
3. **Código**: completar recursão em Java, `enum` em TypeScript, reconhecer um Service Worker (PWA).
4. **Redes avançadas**: sub-redes IPv4 + IPv6, **HSRP**, **EIGRP**, **DiffServ (EF)**, **NBR 14565** (MUTO), WPA2.
5. **Normas por subseção**: ISO 27002:2022 (controle de acesso → política específica por tema), ISO 27701 (registro de operações → inventário), NIST SSDF, CIS Controls v8, NIST SP 800-145.
6. **Engenharia**: requisitos (RF × RNF), APF (contar pontos de função), BPMN, UML 2.5, POO, padrões de projeto (Factory Method), Gitflow, testes, JUnit, CMMI/MPS.BR.

**Estratégia FCC**: estude **sintaxe, valores padrão, nomes de arquivos, portas, anotações e versões** — não só o conceito. Itens com **versão no edital** (PostgreSQL 15–18, Oracle 19c, MySQL 8, OWASP Top 10:2025, PMBOK 8, ITIL Version 5, ISO 27701:2026, TLS 1.2/1.3, RFC 6749/9700) têm alta chance de cair.

## Meta de pontuação (para ficar entre os 320 e brigar por nomeação)

| Prova | Meta | Nota (0–10) |
|---|---|---|
| Gerais | 15/20 | 7,5 |
| Específicos | 30/40 | 7,5 |
| **Objetiva** | (7,5 + 2 × 7,5) / 3 | **7,5** |
| Redação | — | ≥ 7,0 |

Concorrência em TI de TRT costuma exigir **objetiva ≥ 7,5–8,0** para nomeação. Foque em **Específicos** (2/3 da nota).

## Como usar esta apostila
| Fase | Período | Material |
|---|---|---|
| **Base** | 23/11 a 03/01 (6 semanas) | Módulos 1–16 + questões dos módulos, conforme o **Plano de 8 semanas** (volume Revisão) |
| **Consolidação** | 04/01 a 10/01 | Simulado completo (Módulo 18) + revisão dos erros |
| **Intensivo** | 11/01 a 16/01 | **Super Revisão** + flashcards + redação |
| **Prova** | 17/01 | Checklist |

Legenda: ⚠️ pegadinha · 🧠 memorize · 🔢 número que cai · ✅ gabarito · (confirmar) = dado a conferir na fonte oficial.
