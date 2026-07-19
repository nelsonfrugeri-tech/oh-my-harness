# Alertas Baseados em Sintomas

## Princípio
Alerte sobre **o que os usuários experienciam** (sintomas), não sobre **o porquê** (causas).

## Sintomas vs Causas
| Sintoma (BOM) | Causa (RUIM) |
|----------------|-------------|
| Taxa de erro > 1% | Pod reiniciando |
| Latência p99 > 2s | CPU > 80% |
| Disponibilidade < 99.9% | Disco > 90% |
| Fila crescendo | Connection pool esgotado |

## Por Que Baseado em Sintomas
- Alertas baseados em causa disparam para não-problemas (CPU alta mas usuários estão bem)
- Alertas baseados em causa perdem falhas inéditas (nova causa, sem alerta)
- Alertas baseados em sintoma se conectam naturalmente aos SLOs

## Padrão de Implementação
```promql
# GOOD: symptom-based
alert: HighErrorRate
expr: sum(rate(http_requests_total{code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01

# BAD: cause-based
alert: HighCPU
expr: node_cpu_seconds_total > 0.8
```

## Quando Baseado em Causa é Aceitável
- Esgotamento de recursos que VAI causar sintomas (disco cheio → crash)
- Eventos de segurança (tentativas de acesso não autorizado)
- Planejamento de capacidade (não paging, apenas tickets)

## Higiene de Alertas
- Todo alerta deve ser **acionável** — se você não pode fazer nada, não faça paging
- Todo alerta deve ter um link para **runbook**
- Revise mensalmente: exclua alertas em que ninguém agiu
- Meta: <5 pages por turno de on-call
