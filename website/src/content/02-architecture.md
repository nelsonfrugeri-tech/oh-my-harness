---
order: 2
id: architecture
label: O sistema
title: Três ativos que não pertencem ao modelo.
lead: Disciplina para conhecer, memória para acumular e uma organização de agentes que atravessa harnesses.
diagram: architecture
note: "Apresente a hierarquia: modelo e harness executam; governança epistemológica, conhecimento e operating model permanecem. Mostre os três como partes integradas do mesmo agentic loop."
source: README.md
---

## Não é uma coleção de prompts

O OMH transforma práticas de engenharia em artefatos versionados: agents com responsabilidades explícitas, skills com critérios de conclusão, policies compartilhadas, hooks em pontos específicos do ciclo e evals que protegem contratos estruturais.

### 01 — Governança epistemológica

O modelo não recebe licença para preencher lacunas com plausibilidade. O sistema administra o status do conhecimento: fato, resultado derivado, inferência, hipótese, estimativa, desconhecido e decisão têm significados e exigências diferentes.

### 02 — Conhecimento durável

Transcript não vira verdade automaticamente. O sistema separa memória episódica de conhecimento curado, preserva provenance e mantém Markdown como fonte de verdade. Índices podem ser reconstruídos; o conhecimento não fica preso a um banco nem a uma sessão.

### 03 — Operating model portátil de agentes

Papéis, responsabilidades, skills e handoffs formam uma organização estável, versionada e independente do modelo. O adapter muda; o contrato do arquiteto, do implementador, do QA e do reviewer permanece reconhecível.

### Portabilidade é uma propriedade do sistema

O core define intenção, papéis e método. Cada adapter traduz esse contrato para o formato, as permissões e os mecanismos nativos do harness. Capabilities abstratas permitem trocar providers sem reescrever o comportamento de todos os agents.
