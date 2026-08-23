# Metodologia de Pesquisa

## Checklist de Pesquisa

1. **Busca no codebase primeiro** — Isso já foi resolvido antes neste projeto?
2. **Verificação da documentação** — Existe documentação sobre como abordar isso?
3. **Busca na web** — Quais são as melhores práticas atuais?
4. **Múltiplas fontes** — Cruze pelo menos 2-3 fontes
5. **Verificação de atualidade** — As fontes são recentes (últimos 6 meses)?
6. **Análise de trade-offs** — Quais são as alternativas?

## Gatilhos de Pesquisa

Sempre pesquise quando:
- Escolher uma biblioteca ou framework
- Escolher um padrão arquitetural
- Adicionar uma nova dependência
- Lidar com uma tecnologia que você não usa recentemente
- O problema parece comum (alguém provavelmente já resolveu bem)

Pule a pesquisa quando:
- A solução é óbvia e bem estabelecida
- Você já verificou essa abordagem recentemente
- É uma mudança trivial sem alternativas

## Como Documentar a Pesquisa

Para decisões significativas, documente:
```markdown
## Decision: {what was decided}

### Context
{why this decision was needed}

### Options Considered
1. **Option A**: {description}
   - Pros: {list}
   - Cons: {list}

2. **Option B**: {description}
   - Pros: {list}
   - Cons: {list}

### Decision
Chose Option {X} because {justification}.

### Sources
- {url 1}
- {url 2}
```
