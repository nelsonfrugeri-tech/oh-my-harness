---
order: 6
id: portability
label: Na prática
title: Mude o ambiente. Leve os contratos.
lead: O que é compartilhado evolui uma vez. O que é específico permanece explícito.
diagram: boundaries
note: "Compare o mesmo papel nos dois harnesses. Mostre a diferença entre instalar o plugin e sincronizar o adapter completo. Não prometa igualdade das respostas."
source: README.md
---

## Três fronteiras para entender a instalação

**No projeto OMH:** agents, skills, policies, hooks, evals e contratos versionados. **No harness:** representações nativas e configuração instalada. **Na máquina:** providers, identidade e conhecimento externo aos repositórios de produto.

Isso permite trocar providers sem introduzir nomes de ferramentas em todos os agents. Também permite usar Claude Code e Codex sobre a mesma base conceitual de trabalho.

### Plugin não é instalação completa

No Codex, instalar somente o plugin não instala os custom agents do adapter completo. Siga o caminho de instalação correspondente ao resultado desejado e revise a configuração antes de sincronizar.

### O que não está sendo prometido

O suporte documentado é para Claude Code e Codex. Outros harnesses exigem adapters e validação próprios. As permissões e o isolamento do reviewer diferem entre os dois ambientes; o contrato deve ser preservado sem esconder essas diferenças.
