# Padrões de Dashboard

## Os Quatro Golden Signals (Google SRE)
| Sinal | O Que | Métrica |
|--------|------|--------|
| Latency | Tempo para servir uma requisição | `histogram_quantile(0.99, rate(http_duration_seconds_bucket[5m]))` |
| Traffic | Volume de requisições | `sum(rate(http_requests_total[5m]))` |
| Errors | Taxa de requisições que falharam | `sum(rate(http_requests_total{code=~"5.."}[5m]))` |
| Saturation | Utilização de recursos | `container_memory_usage_bytes / container_spec_memory_limit_bytes` |

## Método RED (para serviços orientados a requisições)
- **Rate**: requisições por segundo
- **Errors**: erros por segundo
- **Duration**: distribuição de latência (p50, p95, p99)

## Método USE (para recursos: CPU, memória, disco, rede)
- **Utilization**: % de tempo em que o recurso está ocupado
- **Saturation**: profundidade da fila / trabalho aguardando
- **Errors**: contagem de erros

## Boas Práticas de Layout de Dashboard
```
Row 1: SLO status (availability, latency budget remaining)
Row 2: Golden signals (rate, errors, latency, saturation)
Row 3: Dependency health (database, cache, external APIs)
Row 4: Infrastructure (CPU, memory, disk, network)
```

## Padrões do Grafana
- Use variáveis para seleção de service/namespace/environment
- Crie templates de dashboards por tipo de serviço (API, worker, database)
- Anotações para deploys, incidentes, mudanças de configuração
- Vincule alertas aos painéis de dashboard relevantes
