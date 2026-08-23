# ATAM — Architecture Tradeoff Analysis Method

## Processo
1. **Apresentar a arquitetura** — os stakeholders entendem o sistema
2. **Identificar os quality attributes** — performance, segurança, modificabilidade, disponibilidade
3. **Construir a utility tree** — priorizar cenários por importância e dificuldade
4. **Analisar os cenários** — encontrar sensitivity points e tradeoff points
5. **Documentar os riscos** — riscos não mitigados viram ADRs ou action items

## Utility Tree
```
Quality Attribute → Sub-attribute → Scenario → Priority (H/M/L)
Performance → Latency → API responds < 200ms for 95% of requests → (H, H)
Security → Auth → Support MFA for all user accounts → (H, M)
Modifiability → Extensibility → Add new payment provider in < 1 sprint → (M, H)
```

## Conceitos-Chave
- **Sensitivity point**: decisão arquitetural que afeta UM quality attribute
- **Tradeoff point**: decisão que afeta MÚLTIPLOS quality attributes (ex.: caching melhora a performance mas complica a consistência)
- **Risco**: sensitivity ou tradeoff point não mitigado

## ATAM Leve
Para times menores, execute em 2-4 horas:
1. Liste os 5 principais quality attributes
2. Identifique 3 decisões arquiteturais por atributo
3. Encontre os tradeoff points (decisões que afetam múltiplos atributos)
4. Documente como ADRs
