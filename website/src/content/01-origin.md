---
order: 1
id: origin
label: O ponto de partida
title: Modelos mudam. Harnesses também.
accent: A engenharia permanece.
lead: Governança epistemológica, conhecimento durável e um operating model portátil de agentes fecham o loop.
diagram: portability
note: "Abra pela tese central: modelo e harness são camadas substituíveis; o ativo durável é o sistema de engenharia. Em seguida, conecte esse sistema ao loop entre intenção, execução, verificação e aprendizado."
source: README.md
---

## O modelo não é o sistema

Modelos ficam mais capazes. Harnesses surgem, mudam de interface e são substituídos. Se papéis, conhecimento e critérios de qualidade estiverem presos a essas camadas, cada troca obriga a reconstruir a maneira de trabalhar.

O **oh-my-harness (OMH)** parte da premissa oposta: modelo e harness são mecanismos de execução. O sistema de engenharia precisa sobreviver a ambos.

Esse sistema preserva três ativos:

- **governança epistemológica:** o que sabemos, como sabemos e onde ainda existe incerteza;
- **conhecimento durável:** o que precisa sobreviver à sessão, ao modelo e ao harness;
- **operating model de agentes:** quem investiga, decide, implementa, testa, revisa e entrega.

### Desenvolvimento com agentes acontece em loops

Um coding agent lê o pedido, procura contexto, altera arquivos, executa comandos, observa o resultado e tenta novamente. Mas repetir até o teste passar não basta. O loop precisa questionar premissas, usar conhecimento acumulado, separar autoria de review e saber quando devolver uma decisão ao humano.

### O harness executa o loop

O harness envolve o modelo com instruções, contexto, tools, hooks, agents e condições de parada. O OMH não concorre com essa camada: instala nela um método portável e verificável.

Claude Code e Codex são os dois harnesses suportados nesta versão. O core compartilhado preserva a intenção; adapters nativos respeitam as diferenças. O humano continua responsável por restrições, trade-offs, autorizações e aceite.
