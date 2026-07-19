# Error Budgets

## Conceito
Error budget = indisponibilidade permitida. Se o SLO é 99,9%, você pode tolerar 0,1% de falhas.

## Burn Rate
```
burn_rate = actual_error_rate / allowed_error_rate
```
- burn_rate = 1 → consumindo o orçamento exatamente no ritmo permitido
- burn_rate > 1 → consumindo mais rápido do que o sustentável
- burn_rate = 10 → orçamento esgotado em 1/10 da janela

## Alertas de burn rate com múltiplas janelas
| Severidade | Janela longa | Janela curta | Burn rate | Orçamento consumido |
|----------|------------|--------------|-----------|----------------|
| Page (P1) | 1h | 5min | 14.4x | 2% em 1h |
| Page (P2) | 6h | 30min | 6x | 5% em 6h |
| Ticket | 3d | 6h | 1x | 10% em 3d |

## Política de esgotamento do orçamento
Quando o error budget se esgota:
1. **Congele** os lançamentos de features — apenas trabalho voltado a estabilidade
2. **Exija** postmortems para todos os incidentes que consumiram orçamento
3. **Invista** em trabalho de confiabilidade (redução de toil, automação, testes)
4. **Retome** o trabalho em features quando o orçamento se recuperar acima do threshold (por exemplo, 50%)

## Acompanhamento do orçamento
- Dashboard mostrando o % de orçamento restante ao longo da janela móvel
- Relatório semanal por e-mail/Slack para produto + engenharia
- Gatilho automático de congelamento quando o orçamento < 10%

## Trade-offs
- Generoso demais → o time ignora a confiabilidade
- Rígido demais → não dá para entregar nada, frustração
- Ponto ideal: o orçamento se alinha ao limiar de dor do usuário
