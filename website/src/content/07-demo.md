---
order: 7
id: demo
label: Demonstração
title: Mostre o caminho. Depois, o resultado.
lead: Um roteiro reproduzível para apresentar o OMH sem confundir ilustração com execução.
diagram: demo
note: "Este é um roteiro, não um replay de testes realizados. Prepare uma fixture pública e registre a revisão. Se um serviço não estiver disponível, mostre o fallback como ele realmente ocorreu."
source: README.md
---

## Prepare uma demonstração segura

Use um repositório descartável e dados sintéticos. Registre a revisão do OMH, o harness e os providers efetivamente disponíveis. Não mostre arquivos de autenticação, remotes privados nem transcripts pessoais.

1. **Mapeie o método:** abra o catálogo de agents e localize o mesmo papel nos dois adapters.
2. **Delimite uma tarefa:** apresente critérios de aceite pequenos e verificáveis.
3. **Examine a evidência:** mostre o diff e a saída real dos testes, com o escopo correto.
4. **Peça revisão independente:** diferencie Standards de Spec e trate os findings.
5. **Preserve uma decisão:** solicite explicitamente uma nota sintética com proveniência válida.
6. **Retome o contexto:** em outra sessão configurada, solicite a recuperação dessa decisão e inspecione a fonte.

### O que registrar para chamar de resultado

Anote comandos, revisão, ambiente e saídas observadas. O walkthrough deste site é documental: não afirma que esses passos foram executados por você. Se não houver runtime pronto, apresente os contratos e declare o limite.
