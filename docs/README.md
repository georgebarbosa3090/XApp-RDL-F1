# Portal de Documentação Oficial — Projeto xApp RDL (Resource and Decision Layer)

<div align="center">

**Arquitetura Unificada de Governança, Arbitragem de Conflitos Multi-xApp e Validação Causal em Open RAN**  
*Homologado para O-RAN ALLIANCE WG2/WG3, O-RAN SC Release J, ns-3.48 / 5G-LENA v5.1 e NORI E2 Agent*

</div>

---

## 📚 Estrutura Consolidada da Documentação

A documentação do projeto foi consolidada em **7 volumes canônicos**, eliminando redundâncias e estabelecendo uma fonte única e autoritativa de verdade técnica e científica:

```text
docs/
+-- 01_arquitetura_e_modelagem.md            # [Vol 01] Arquitetura Core, Agentes e Modelagem Matemática
+-- 02_guia_operacional_deploy_e_simulacao.md# [Vol 02] Deploy K8s/k3d, Helm, Observabilidade e Simulação ns-3
+-- 03_taxonomia_de_conflitos_e_cenarios.md  # [Vol 03] Taxonomia de Conflitos e Portfólio de Cenários (S0–S15)
+-- 04_relatorio_cientifico_mestre_rdl.md    # [Vol 04] Monografia Científica Mestre, Resultados e Estatística
+-- 05_auditoria_e_conformidade_oran.md      # [Vol 05] Auditoria Causal, Rastreabilidade SHA-256 e Normas O-RAN
+-- 06_roadmap_e_pesquisa_futura_6g.md       # [Vol 06] Roadmap 2026-2028, Fase 3 Federada 6G e Testbed UFPA
+-- 07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md # [Vol 07] Resultados da Simulação, Baselines e Cenários (S0–S15)
+-- assets/                                  # Diagramas de arquitetura e modelos visuais
+-- compliance/                              # Perfis de compatibilidade O-RAN congelados
+-- e2/                                      # Definições ASN.1 e matrizes normativas E2AP/E2SM
\-- figures/                                 # Figuras científicas em alta resolução (300 DPI)
```

---

## 🧭 Guia de Leitura por Perfil de Atuação

| Perfil de Interesse | Volumes Recomendados | Objetivo Principal |
| :--- | :--- | :--- |
| **Arquiteto de Software / Engenheiro O-RAN** | [Vol 01](01_arquitetura_e_modelagem.md) & [Vol 05](05_auditoria_e_conformidade_oran.md) | Compreender os agentes cognitivos, codecs ASN.1 APER e conformidade normativa E2AP/E2SM. |
| **Operador de Infraestrutura / DevOps** | [Vol 02](02_guia_operacional_deploy_e_simulacao.md) | Subir clusters k3d, instalar via Helm, monitorar métricas Prometheus e depurar pods. |
| **Pesquisador Científico / Avaliador** | [Vol 04](04_relatorio_cientifico_mestre_rdl.md), [Vol 03](03_taxonomia_de_conflitos_e_cenarios.md) & [Vol 07](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md) | Analisar as evidências causais, tabelas completas de simulação, testes pareados e cenários S0–S15. |
| **Pesquisador 6G / Estrategista de IA** | [Vol 06](06_roadmap_e_pesquisa_futura_6g.md) & [Vol 07](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md) | Explorar a evolução para Intent-Driven RIC (A1), federação multi-RIC e comparativos Safe-MAPPO. |

---

## 🚀 Resumo Executivo dos Volumes

### [Volume 01: Arquitetura, Módulos Core e Modelagem Matemática](01_arquitetura_e_modelagem.md)
Apresenta o design da xApp RDL sob Clean Architecture / DDD, os agentes especialistas (`PerceptionAgent`, `ReasoningAgent`, `RefinementAgent`), modelos analíticos físicos de rádio (Shannon com calibração 3GPP, filas $M/G/1$, consumo Earth Project) e formulação CMDP / Safe-MAPPO com *Safety Guards* invariantes.

### [Volume 02: Guia Operacional de Deploy, Simulação e Observabilidade](02_guia_operacional_deploy_e_simulacao.md)
Guia prático passo a passo para provisionamento de clusters Kubernetes leves com `k3d`, deploys via Helm e manifestos K8s, configuração do Rancher e Kiali, execução da suíte de co-simulação ns-3.48 / 5G-LENA / NORI e integração com o testbed físico GreenRAN da UFPA.

### [Volume 03: Taxonomia de Conflitos Multi-xApp e Portfólio de Cenários (S0 a S15)](03_taxonomia_de_conflitos_e_cenarios.md)
Classifica formalmente os 5 tipos de conflito em Open RAN (Direto, Indireto, Implícito/Semântico, Temporal Ping-Pong e Tempestade de Conflitos) e detalha a especificação técnica dos 16 cenários experimentais (de macrocélulas 5G a satélites NTN, pelotões V2X e segurança Zero-Trust).

### [Volume 04: Relatório Científico Mestre de Experimentos RDL (F1 × F2)](04_relatorio_cientifico_mestre_rdl.md)
Monografia científica exaustiva detalhando o protocolo experimental em 6 camadas, resultados de 167 fluxos reais FlowMonitor, comparações pareadas multi-seed (Wilcoxon $p < 0,001$, Cohen's $d_z > 4,0$), ablações cognitivas, sensibilidade da janela de decisão ($\Delta t_{win}$), tempos de recuperação ($t_{recover}$), registro de UE (45,8 ms) e a galeria completa de 30 figuras científicas (300 DPI) e 21 tabelas consolidadas CSV.

### [Volume 05: Relatório de Auditoria Técnico-Científica e Conformidade O-RAN](05_auditoria_e_conformidade_oran.md)
Documenta a superação da lacuna metodológica de prova causal, o fechamento do círculo de evidências de não-repúdio ($KPM(t_0) \to \dots \to KPM(t_1)$), verificação de integridade por checksums SHA-256 e conformidade com especificações O-RAN WG2 e WG3.

### [Volume 06: Roadmap de Pesquisa (2026–2028), Fase 3 e RDL Autônoma 6G](06_roadmap_e_pesquisa_futura_6g.md)
Delineia a evolução do projeto em direção ao 6G Zero-Touch, detalhando a governança por intenção via interface A1, aprendizado federado multi-RIC, coordenação SAGIN (Space-Air-Ground) e cronograma da campanha experimental física no laboratório GreenRAN/UFPA.

### [Volume 07: Relatório Exaustivo de Resultados de Simulação (S0 a S15)](07_relatorio_resultados_simulacao_baselines_hrdl_cardl.md)
Apresenta o comparativo multidimensional completo cruzando os 7 baselines (B0 a B6) e os 16 cenários experimentais (S0 a S15), detalhando throughput, latência P95, violação de SLA, tempos de estabilização ($t_{\text{settle}}$), eficiência energética (EEVS), decomposição em 11 estágios do loop fechado e matriz de recomendações técnicas de uso H-RDL vs CA-RDL.

---

### [Trilha Especial: Auditoria Profunda e Conformidade O-RAN](auditoria/README.md)
Relatórios formais de auditoria técnica, interoperabilidade E2 e conformidade com o ecossistema O-RAN SC Release J e OpenRAN@Brasil.

---

- **Autor:** George Alexandro Ferreira Barbosa  
- **Orientador:** Prof. Dr. André Riker  
- **Instituição:** Universidade Federal do Pará (UFPA) — Instituto de Tecnologia (ITEC) — PPGCOMP  
- **Release Oficial:** `2.0.0-certified`
