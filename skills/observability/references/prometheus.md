# Prometheus

## Padrões Essenciais de PromQL

### Rate e increase
- `rate(metric[5m])` — taxa por segundo ao longo de 5 minutos (para counters)
- `increase(metric[1h])` — aumento total ao longo de 1 hora
- Sempre use `rate()` antes de `sum()`: `sum(rate(metric[5m]))` e não `rate(sum(metric))`

### Percentis
```promql
histogram_quantile(0.99, sum(rate(http_duration_seconds_bucket[5m])) by (le))
```

### Recording Rules
Pré-compute queries custosas:
```yaml
groups:
  - name: slo
    interval: 30s
    rules:
      - record: job:http_errors:rate5m
        expr: sum(rate(http_requests_total{code=~"5.."}[5m])) by (job)
```

### Federation
- Use para agregar dados entre clusters
- Remote write para armazenamento de longo prazo (Thanos, Cortex, Mimir)
- Versão: Prometheus 2.53+ (estável em 2026)
