# Roadmap de Migração para O-RAN Release 5 — Migration to Release 5

**Projeto:** xApp RDL (Resource and Decision Layer) — Fase 1 (H-RDL Determinística)  
**Documento:** `MIGRATION_RELEASE5.md`  
**Escopo:** Planejamento e roteiro de migração da infraestrutura normativa do H-RDL para o O-RAN Release 5 (E2SM-KPM v08.00 e E2SM-RC v10.00) após a conclusão da Fase 1.

---

## 1. Contexto e Estratégia de Isolamento

A O-RAN ALLIANCE finalizou a especificação do **Release 5**, introduzindo atualizações importantes como E2SM-KPM v08.00 e E2SM-RC v10.00, com foco em ampliação de recursos AI/ML, otimização de fatias de rádio e suporte a sensoriamento 6G ISAC.

Para proteger os experimentos e publicações da Fase 1, a evolução para o Release 5 seguirá os seguintes princípios:

1. **Congelamento da Fase 1:** A Fase 1 permanece 100% ancorada no perfil congelado `E2AP v02.03`, `E2SM-KPM v03.00` e `E2SM-RC v01.03`.
2. **Desenvolvimento em Branch Dedicada:** Qualquer trabalho de adaptação para o Release 5 será desenvolvido isoladamente na branch `feature/oran-release5-profile`.
3. **Migração Gradual (Post-Gate 6):** A migração efetiva será iniciada somente após a conclusão do Gate 6 (Artifact Readiness) da Fase 1.

---

## 2. Roteiro de Atualização das Especificações Normativas

| Especificação Normativa | Versão Fase 1 (Congelada) | Versão Planejada (Release 5) | Principais Recursos / Impacto no RDL |
| :--- | :---: | :---: | :--- |
| **E2AP** | `v02.03` | `v03.01` | Suporte a novas causas de erro e mensagens estendidas de serviço. |
| **E2SM-KPM** | `v03.00` | `v08.00` | Mapeamento expandido de métricas 3GPP 28.552, suporte a fatias dinâmicas e ISAC. |
| **E2SM-RC** | `v01.03` | `v10.00` | Estilos adicionais de controle, suporte estendido a parâmetros MIMO e beamforming. |
| **O-RAN SC** | Release J | Empirically Validated Release | Future profile will target the O-RAN SC release empirically validated against the selected O-RAN Alliance Release 5 E2 profile. |

---

## 3. Matriz de Tarefas para a Fase 2 (CA-RDL / Release 5)

- [ ] Instanciar repositório/branch `feature/oran-release5-profile`.
- [ ] Atualizar os esquemas ASN.1 APER para KPM v08.00 e RC v10.00.
- [ ] Conectar os novos parâmetros de controle ao modelo de aprendizado por reforço multiagente (MAPPO) da Fase 2.
- [ ] Manter compatibilidade reversa com os conectores da Fase 1 via camada de abstração `e2/adapters/`.
