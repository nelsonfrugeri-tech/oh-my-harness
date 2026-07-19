# Definindo SLOs

## Tipos de SLI

| Tipo de SLI | Fórmula | Exemplo |
|----------|---------|---------|
| Disponibilidade | `good_requests / total_requests` | 99,9% das requisições retornam não-5xx |
| Latência | `fast_requests / total_requests` | 95% das requisições < 200ms, 99% < 1s |
| Throughput | `processed / expected` | Processa 99,9% das mensagens da fila |
| Corretude | `correct_responses / total_responses` | 99,99% retornam dados corretos |
| Atualidade | `fresh_data / total_data` | 99% dos dados atualizados em até 1 minuto |

## Seleção da meta de SLO
- Comece pelo desempenho atual (por exemplo, se a disponibilidade é 99,95%, defina o SLO em 99,9%)
- Nunca defina 100% — é impossível e impede deploys
- SLOs mais rigorosos = maior custo de engenharia. Cada 9 adicional é cerca de 10x mais difícil
- SLOs diferentes por tier: serviços críticos 99,99%, ferramentas internas 99,5%

## Error Budget
```
Error budget = 1 - SLO target
Example: 99.9% SLO → 0.1% error budget → 43.8 min/month downtime allowed
```

| SLO | Orçamento mensal | Orçamento trimestral |
|-----|---------------|-----------------|
| 99% | 7.3h | 21.9h |
| 99.9% | 43.8min | 2.2h |
| 99.95% | 21.9min | 1.1h |
| 99.99% | 4.4min | 13.1min |

## Modelo de documento de SLO
```yaml
service: payment-api
slos:
  - name: availability
    sli: ratio of non-5xx responses
    target: 99.95%
    window: 30 days rolling
    measurement: Prometheus query
  - name: latency-p99
    sli: 99th percentile response time
    target: < 500ms
    window: 30 days rolling
```

## Alinhamento com stakeholders
- O time de produto concorda com as metas (eles aceitam o trade-off)
- SLOs são documentos vivos — revise trimestralmente
- Alerte com base em burn rate, não em violações de threshold
