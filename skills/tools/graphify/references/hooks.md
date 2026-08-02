# graphify reference: commit hook e integração nativa com CLAUDE.md

Carregue isto quando o usuário pediu para instalar o post-commit hook ou fazer o wire do graphify no CLAUDE.md de um projeto.

## Para git commit hook

Instale um post-commit hook que auto-rebuilds o grafo depois de todo commit. Nenhum processo em background necessário - dispara uma vez por commit, funciona com qualquer editor.

```bash
graphify hook install    # install
graphify hook uninstall  # remove
graphify hook status     # check
```

Depois de todo `git commit`, o hook detecta quais arquivos de código mudaram (via `git diff HEAD~1`), re-roda AST extraction nesses arquivos, e reconstrói `graph.json` e `GRAPH_REPORT.md`. Mudanças de doc/image são ignoradas pelo hook - rode `/graphify --update` manualmente para essas.

Se um post-commit hook já existe, o graphify apenda a ele em vez de substituí-lo.

---

## Para integração nativa com CLAUDE.md

Rode uma vez por projeto para deixar o graphify always-on em sessões do Claude Code:

```bash
graphify claude install
```

Isto escreve uma seção `## graphify` no CLAUDE.md local que instrui o Claude a verificar o grafo antes de responder perguntas sobre o codebase e reconstruí-lo depois de mudanças de código. Nenhum `/graphify` manual necessário em sessões futuras.

```bash
graphify claude uninstall  # remove the section
```
