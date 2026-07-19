# Quadrante de Dívida Técnica (Martin Fowler)

## O Quadrante
|  | Deliberada | Inadvertida |
|--|-----------|-------------|
| **Prudente** | "Sabemos que isto é um atalho, vamos corrigir no próximo sprint" | "Agora sabemos como deveríamos ter feito" |
| **Imprudente** | "Não temos tempo para design" | "O que é layering?" |

## Estratégia de Gestão
### Rastrear
- Marque a dívida no código: `# DEBT: <description> — <issue-link>`
- Mantenha um backlog de dívida (separado do backlog de features)
- Quantifique: estime o custo de corrigir + o custo de NÃO corrigir (juros)

### Priorizar
1. **Juros altos**: dívida que atrasa toda feature (ex: sem suíte de testes)
2. **Bloqueante**: dívida que impede features importantes
3. **Juros baixos**: código feio mas estável que ninguém toca
4. **Aceitar**: dívida deliberada e prudente com prazo documentado

### Orçamento
- Aloque 15-20% da capacidade do sprint para redução de dívida
- Nunca faça "sprint de dívida" — distribua ao longo de todos os sprints
- Vincule o trabalho de dívida ao trabalho de feature quando possível (boy scout rule)

### Métricas
- Tendência do lead time (crescente = acúmulo de dívida)
- Taxa de defeitos em áreas de alta dívida
- Pesquisas de satisfação de desenvolvedores
- Tempo para integrar um novo membro no time
