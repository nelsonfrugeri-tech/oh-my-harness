# Rubrica de Review Independente de Evidência

Revise as alegações e o registro de decisão sem modificar a implementação. Escale o review ao
impacto da decisão; escolhas triviais e facilmente reversíveis não precisam de cerimônia.

## Checagens

1. **Rastreabilidade** — Toda alegação factual e quantitativa material pode ser rastreada a uma
   fonte inspecionável, um comando exato ou uma derivação reprodutível?
2. **Escopo** — Cada alegação permanece dentro da revisão, do ambiente, da população e da janela
   temporal observados?
3. **Classificação** — Inferência, hipótese, estimativa, desconhecido e decisão estão distinguidos
   de fato verificado?
4. **Falsificabilidade** — Cada hipótese causal ou preditiva nomeia uma observação que poderia
   refutá-la?
5. **Alternativas** — Alternativas viáveis e o status quo foram comparados sob os mesmos critérios?
6. **Qualidade da decisão** — Reversibilidade, blast radius, custo de atraso e custo do erro estão
   explícitos?
7. **Colaboração crítica** — A crítica identifica evidência e risco, faz o steelman da proposta,
   oferece uma alternativa e diz o que mudaria a conclusão?
8. **Validação** — Sucesso, guardrail, rollback e observações de follow-up estão definidos antes de
   o resultado ser conhecido?

## Formato do finding

O template fica em inglês porque o finding vira artefato de repositório (comentário de PR via
`code-host`), como o template da skill `review`:

```markdown
[SEVERITY] Claim or decision at risk

Status: {unsupported | overstated | stale | non-falsifiable | decision gap}
Evidence inspected: {source or exact observation}
Why it matters: {decision impact}
Smallest correction: {relabel, measure, test, narrow scope, or add alternative}
What would resolve it: {specific evidence}
```

Aprove quando nenhuma alegação material está superdimensionada e a incerteza restante é explícita e
proporcional à decisão. Não exija pesquisa extra que não tem como mudar a escolha.
