---
order: 5
id: engineering
label: Operating model
title: Troque o modelo. Preserve o time.
lead: Papéis, responsabilidades e handoffs permanecem estáveis; modelos e harnesses se tornam mecanismos substituíveis de execução.
diagram: engineering
note: "Explique harness-invariance sem chamar os agents de imutáveis: eles evoluem por versionamento, mas sua organização não precisa ser reconstruída quando o modelo ou harness muda. Depois mostre o humano governando esse time."
source: core/skills/feature/SKILL.md
---

## Uma organização de agentes, não um chat com personas

O operating model define papéis antes de escolher qual modelo vai executá-los. Um pedido como “implemente autenticação” deixa decisões demais implícitas; um contrato de trabalho explicita outcome, critérios de aceite, restrições, riscos e o que precisa ser observado para declarar conclusão.

O OMH distribui esse contrato entre agentes com responsabilidades distintas. Product thinking enquadra o problema. Arquitetura decide fronteiras e trade-offs. Implementação altera o produto. Testes tentam falsificar o comportamento. Review independente desafia tanto a qualidade observável quanto a aderência ao pedido.

### Harness-invariant, não literalmente imutável

Agents e skills evoluem de forma versionada. O que permanece estável é a topologia do trabalho: responsabilidades, fronteiras, critérios e handoffs. Claude Code e Codex podem representar esses papéis de formas diferentes sem obrigar o método a recomeçar.

Tool agents operam capacidades compartilhadas, como contexto do projeto, knowledge base e code graph. Domain agents assumem decisões de engenharia dentro de seus limites. Separar papéis reduz conflitos de interesse e torna os handoffs inspecionáveis.

### Review em dois eixos

- **Standards:** defeitos, riscos e violações de engenharia observáveis no artefato.
- **Spec:** divergências entre o resultado entregue e o contrato solicitado.

O autor faz self-check, mas não aprova o próprio trabalho. Um reviewer independente precisa apontar evidência concreta, prioridade e consequência de cada finding.

### Autonomia com fronteiras

Agents podem explorar, implementar e verificar sem interromper o loop por escolhas rotineiras. A decisão volta ao humano quando envolve autorização, mudança material de escopo, risco irreversível ou aceite do resultado.

Human-in-the-loop não significa microgerenciar cada tool call. Significa manter responsabilidade nos pontos que mudam a decisão.
