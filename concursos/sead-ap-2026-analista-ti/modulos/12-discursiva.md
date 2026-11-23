# Módulo 12 — Prova Discursiva (Estudo de Caso)

> **30 pontos**, **20 a 40 linhas**, mesmo dia da objetiva. Confira no edital os critérios exatos de correção e o tempo total. Reserve **60–75 min**: 10 min de planejamento, 35 min de rascunho, 20 min para passar a limpo.

## Temas mais prováveis para Analista de TI (pelo edital)
1. **Contratação de solução de TIC** (Lei 14.133 + IN SGD 94/2022: DFD, ETP, Mapa de Riscos, TR, fiscalização).
2. **IA generativa no atendimento ao cidadão** (RAG, riscos, LGPD, governança, supervisão humana).
3. **Incidente de segurança / ransomware** (resposta a incidentes, LGPD art. 48, backup, continuidade).
4. **Migração para nuvem / modernização** (IaaS/PaaS/SaaS, DevOps, segurança, custos, PDTIC).
5. **Governo digital** (Lei 14.129, interoperabilidade, dados abertos, inclusão digital na Amazônia).

## Estrutura vencedora (adapte ao comando)
| Parte | Linhas | Conteúdo |
|---|---|---|
| 1. Introdução | 3–4 | Contextualize e anuncie os pontos que vai abordar (na ordem do enunciado) |
| 2. Desenvolvimento — item (a) | 8–10 | Responda o 1º comando com fundamento técnico/legal |
| 3. Desenvolvimento — item (b) | 8–10 | 2º comando |
| 4. Desenvolvimento — item (c) | 6–8 | 3º comando |
| 5. Conclusão | 2–3 | Retome o interesse público (eficiência, segurança, cidadão) |

**Checklist antes de passar a limpo**: respondi a **todos** os comandos? Citei **base legal** (lei, artigo, norma)? Usei **termos técnicos exatos**? Texto em **prosa**, impessoal, sem 1ª pessoa, sem gírias? Respeitei o **mínimo e o máximo de linhas**? Não me identifiquei?

**Conectores úteis**: Inicialmente · Em primeiro lugar · Além disso · Nesse sentido · Por sua vez · Paralelamente · Dessa forma · Por fim · Portanto · Em síntese.

---

## Caso 1 (modelo completo) — IA generativa no atendimento ao cidadão

**Enunciado (inédito, estilo estudo de caso):**
A Secretaria de Estado da Administração do Amapá pretende disponibilizar, no portal de serviços do Estado, um assistente virtual baseado em IA generativa para orientar cidadãos sobre serviços, documentos necessários e andamento de processos. A solução deverá consultar normas estaduais e, quando autorizado, dados pessoais dos requerentes. Na condição de Analista de Tecnologia da Informação, redija um texto dissertativo abordando:
a) as etapas de planejamento da contratação da solução, à luz da Lei nº 14.133/2021 e da IN SGD/ME nº 94/2022;
b) uma arquitetura técnica adequada e os principais riscos de segurança da solução, com as respectivas medidas de mitigação;
c) as medidas necessárias para garantir a conformidade com a LGPD e o uso responsável da IA.

**Resposta-modelo (≈ 34 linhas manuscritas):**

> A adoção de um assistente virtual com inteligência artificial generativa pode ampliar o acesso do cidadão amapaense aos serviços públicos, mas exige planejamento rigoroso, segurança e respeito à proteção de dados pessoais.
>
> Inicialmente, a contratação deve estar alinhada ao Plano Diretor de Tecnologia da Informação e Comunicação (PDTIC) e prevista no Plano de Contratações Anual. Conforme a IN SGD/ME nº 94/2022, a área demandante elabora o Documento de Formalização da Demanda e institui-se a Equipe de Planejamento da Contratação, composta pelos integrantes requisitante, técnico e administrativo. Em seguida, elabora-se o Estudo Técnico Preliminar, previsto no art. 18 da Lei nº 14.133/2021, com o levantamento das soluções de mercado, a análise do custo total de propriedade e a justificativa da solução escolhida. Paralelamente, constrói-se o Mapa de Gerenciamento de Riscos e, por fim, o Termo de Referência, com requisitos técnicos, níveis mínimos de serviço, pagamento vinculado a resultados e cláusulas de sigilo e de propriedade dos dados.
>
> Quanto à arquitetura, recomenda-se o padrão RAG (geração aumentada por recuperação): as normas estaduais são divididas em trechos, convertidas em embeddings e armazenadas em banco vetorial, de modo que o modelo responda com base em fontes oficiais citadas, o que reduz alucinações. A integração com os sistemas de processos deve ocorrer por APIs autenticadas com OAuth 2.0 e login gov.br, sob o princípio do menor privilégio. Entre os riscos, destacam-se a injeção de prompt, o vazamento de dados pessoais e respostas incorretas, mitigados por filtros de entrada e saída, controle de acesso aos documentos recuperados, registro de logs, testes de segurança (SAST, DAST e red teaming) e encaminhamento a atendente humano quando necessário.
>
> No tocante à LGPD, o tratamento deve fundamentar-se na execução de políticas públicas e no cumprimento de competências legais (arts. 7º, III, e 23), observando os princípios da finalidade, da necessidade e da transparência. Cabe elaborar o Relatório de Impacto à Proteção de Dados, indicar o encarregado, aplicar minimização e pseudonimização, vedar contratualmente o uso dos dados para treinar modelos do fornecedor e informar ao cidadão que ele interage com uma IA, assegurando a revisão humana prevista no art. 20.
>
> Dessa forma, a solução poderá tornar o atendimento mais ágil e eficiente, sem prejuízo da segurança da informação e dos direitos fundamentais dos cidadãos.

**Por que essa resposta pontua bem**: segue a ordem (a)(b)(c); cita leis e artigos; usa termos técnicos precisos (DFD, ETP, Mapa de Riscos, TR, RAG, embeddings, OAuth, menor privilégio, RIPD, encarregado); propõe riscos **com** mitigação; conclusão retoma o interesse público.

---

## Caso 2 (roteiro) — Ataque de ransomware em sistema estadual
**Enunciado:** Um ransomware criptografou servidores do sistema de folha de pagamento do Estado, e há indícios de exfiltração de dados pessoais dos servidores. Aborde: (a) as fases de resposta ao incidente; (b) as obrigações decorrentes da LGPD; (c) medidas para evitar novos incidentes e garantir a continuidade.

**Roteiro de resposta:**
- (a) **NIST SP 800-61**: preparação → **detecção e análise** (escopo, vetor de entrada, preservação de evidências) → **contenção** (isolar segmentos, desativar contas comprometidas), **erradicação** (remover malware, corrigir vulnerabilidade) e **recuperação** (restaurar a partir de **backup íntegro/imutável**, validar) → **pós-incidente** (lições aprendidas, relatório). Acionar a **ETIR**, o comitê de segurança e o CTIR Gov/CERT. **Não pagar resgate** (sem garantia, financia o crime).
- (b) **LGPD art. 48**: o **controlador** comunica à **ANPD e aos titulares** em **3 dias úteis** (Res. CD/ANPD 15/2024) — natureza dos dados, titulares afetados, medidas técnicas, riscos, medidas para reverter/mitigar. Registro do incidente; atuação do **encarregado**. Art. 46: medidas de segurança.
- (c) Backup **3-2-1-1-0** (cópia offline/imutável), testes de restauração, **RPO/RTO** definidos na **BIA**, **PCN**/plano de recuperação (ISO 22301), **MFA**, gestão de vulnerabilidades e patches, **EDR/SIEM**, segmentação de rede, menor privilégio, conscientização contra **phishing**, POSIN alinhada à ISO 27001/27002 e à PNSI.

## Caso 3 (roteiro) — Migração de sistemas para a nuvem
**Enunciado:** O Estado deseja migrar sistemas legados do datacenter próprio para a nuvem. Aborde: (a) modelos de serviço e de implantação adequados; (b) práticas de DevOps e de observabilidade; (c) cuidados de segurança, contratação e governança.

**Roteiro:**
- (a) **IaaS** (lift-and-shift de VMs), **PaaS** (modernizar apps e bancos gerenciados), **SaaS** (e-mail, colaboração); **nuvem híbrida** para dados sensíveis/legados críticos; estratégia por aplicação (rehost, replatform, refactor, retire).
- (b) **CI/CD** (GitLab CI/Jenkins), **IaC** (Terraform/Ansible), **contêineres e Kubernetes**, **observabilidade** (Prometheus, Grafana, Zabbix, logs e traces), SLO/SLA, métricas DORA.
- (c) **Responsabilidade compartilhada**, IAM com MFA, criptografia em repouso e em trânsito, **localização dos dados** e LGPD, backup e continuidade, prevenção de lock-in (portabilidade, padrões abertos), **ETP com análise de TCO**, alinhamento ao **PDTIC**, TR com níveis de serviço, fiscalização pela IN 94/2022, FinOps (controle de custos).

## Erros que derrubam a nota
- Responder em **tópicos/lista** (exija **prosa**).
- Ignorar um dos comandos (a, b ou c).
- Citar lei **errada** (ex.: "Lei 8.666" — revogada) ou inventar artigo.
- Texto genérico sem termos técnicos ("tomar medidas de segurança").
- Ultrapassar o limite de linhas ou ficar abaixo do mínimo.
