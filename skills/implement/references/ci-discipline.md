# Disciplina de CI

## Regras Fundamentais
1. **Main sempre verde** — main quebrada bloqueia todo mundo
2. **Commits pequenos** — cada commit é uma unidade lógica, revisável de forma independente
3. **Feedback rápido** — CI roda em < 10 minutos (otimize: paralelize, use cache, divida)
4. **Corrija builds quebrados imediatamente** — prioridade máxima, nenhum trabalho novo até corrigir

## Higiene de Commits
```
feat: add user registration endpoint     ← new feature
fix: handle null email in validation      ← bug fix  
refactor: extract auth middleware         ← no behavior change
test: add integration tests for payments  ← tests only
docs: update API documentation            ← docs only
chore: upgrade dependencies               ← maintenance
```

## Trunk-Based Development
- Branches de vida curta (< 2 dias)
- PRs pequenos (< 400 linhas de diff)
- Feature flags para features incompletas
- Merge para main com frequência

## Estágios do Pipeline de CI
```
1. Lint + Format check (< 30s)
2. Unit tests (< 2min)
3. Integration tests (< 5min)
4. Build artifact (< 2min)
5. Deploy to staging (automated)
6. E2E smoke tests (< 5min)
```

## Anti-padrões
- Commits de "conserto depois" na main
- PRs grandes que ficam dias parados em review
- Pular a CI com [skip ci] para "economizar tempo"
- Rodar apenas testes unitários (sem integração)
