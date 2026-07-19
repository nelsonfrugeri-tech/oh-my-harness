# Template de Postmortem Blameless

## Cabeçalho

```markdown
# Postmortem: {Incident Title}

**Date:** YYYY-MM-DD
**Severity:** SEV{1-4}
**Duration:** {start} to {end} ({total duration})
**Authors:** {names}
**Status:** Draft | In Review | Complete
```

## 1. Resumo

Um parágrafo: o que aconteceu, impacto, duração, resolução.

```markdown
On {date}, {service} experienced {description of failure} for {duration},
affecting {N users / N% of traffic / specific functionality}. The root cause
was {one sentence}. The incident was resolved by {mitigation action}.
```

## 2. Impacto

```markdown
- **Duration:** HH:MM to HH:MM UTC ({N} minutes)
- **Users affected:** {number or percentage}
- **Revenue impact:** {estimated or N/A}
- **SLO impact:** {error budget consumed}
- **Data loss:** {yes/no, details}
```

## 3. Linha do Tempo

```markdown
| Time (UTC) | Event |
|------------|-------|
| HH:MM | {trigger event} |
| HH:MM | Alert fired: {alert name} |
| HH:MM | IC assigned: {name} |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied: {action} |
| HH:MM | Service restored |
| HH:MM | All-clear declared |
```

## 4. Causa Raiz

Explicação técnica detalhada. Use os 5 Porquês ou análise de árvore de falhas.
Consulte `root-cause-analysis.md` para técnicas.

```markdown
The root cause was {detailed explanation}.

### Contributing Factors
- {factor 1}
- {factor 2}
```

## 5. O Que Deu Certo

```markdown
- {positive aspect of the response}
- {thing that prevented worse outcome}
```

## 6. O Que Deu Errado

```markdown
- {thing that made the incident worse or slower to resolve}
- {gap in monitoring, process, or tooling}
```

## 7. Onde Tivemos Sorte

```markdown
- {thing that could have made it worse but didn't}
```

## 8. Itens de Ação

```markdown
| # | Action | Type | Owner | Deadline | Status |
|---|--------|------|-------|----------|--------|
| 1 | {action} | Prevent | {name} | {date} | TODO |
| 2 | {action} | Detect | {name} | {date} | TODO |
| 3 | {action} | Mitigate | {name} | {date} | TODO |
```

**Tipos de ação:**
- **Prevent:** Impedir que isso aconteça novamente
- **Detect:** Detectar mais rápido na próxima vez
- **Mitigate:** Reduzir o impacto quando acontecer

## 9. Lições Aprendidas

```markdown
- {key takeaway for the team}
```

## Regras da Cultura Blameless

1. Foque em sistemas e processos, não em indivíduos
2. "Quem" nunca é a causa raiz -- "que sistema permitiu isso"
3. Assuma que todos agiram com as melhores intenções e as informações disponíveis
4. O objetivo é aprender, não punir
5. Compartilhe amplamente -- outras equipes se beneficiam dos seus aprendizados
