---
order: 7
id: demo
label: O loop
title: Uma demanda entra. Evidências saem.
lead: "O valor do OMH aparece no percurso completo: do contrato inicial ao código verificado, revisado e recuperável."
diagram: demo
note: "Use este capítulo como mapa da demonstração. Mostre os critérios antes da implementação, o diff e os testes antes da conclusão, o review antes do aceite e a recuperação da decisão em outra sessão."
source: core/skills/feature/SKILL.md
---

## Uma feature atravessa um sistema

### 01 — Descobrir

O fluxo começa pelo estado real do repositório: instruções aplicáveis, revisão atual, alterações existentes, comandos de build e teste, integrações disponíveis e limites de autorização. O agent não inventa o ambiente em que está trabalhando.

### 02 — Contratar

O pedido é convertido em outcome, escopo, critérios de aceite e riscos observáveis. Ambiguidades que mudariam materialmente o resultado voltam ao humano; escolhas rotineiras seguem com premissas explícitas e reversíveis.

### 03 — Construir e tentar falsificar

O especialista implementa a menor mudança suficiente e procura um check capaz de falhar pelo motivo correto. Primeiro vêm as verificações focadas; depois, os gates definidos pelo próprio projeto — format, lint, typecheck, testes e build quando aplicáveis.

### 04 — Desafiar

Um reviewer independente inspeciona o diff contra **Standards** e **Spec**. Findings carregam localização, evidência, impacto e prioridade. Correções materiais voltam ao loop até que não exista blocker conhecido.

### 05 — Decidir e preservar

O humano aceita, rejeita ou redireciona o resultado. Decisões duráveis são destiladas com provenance para a knowledge base; estados temporários permanecem na sessão. Em outra sessão — ou em outro harness suportado — o trabalho pode recomeçar a partir do conhecimento relevante.

### O que observar em uma demonstração

Não conte apenas quantas linhas o agent escreveu. Inspecione o contrato, o diff, os testes, os findings, as correções, o handoff e a memória recuperada. O produto do loop não é somente código: é uma cadeia de decisões que pode ser auditada.
