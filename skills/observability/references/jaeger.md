# Jaeger

## Rastreamento Distribuído

### Estratégias de Amostragem de Traces
| Estratégia | Quando |
|----------|------|
| Head-based (probabilística) | Padrão, baixo overhead, taxa de amostragem de 1-10% |
| Tail-based | Captura todos os erros/requisições lentas, maior custo de recursos |
| Rate-limiting | Número fixo de traces/segundo por serviço |

### Atributos de Span (convenções OpenTelemetry)
```
http.method, http.status_code, http.url
db.system, db.statement (sanitized)
rpc.service, rpc.method
error (boolean), error.message
```

### Correlação entre traces e logs
- Injete o `trace_id` nos logs estruturados
- Grafana: datasource do Jaeger vinculado ao Loki via `trace_id`

### Versão: Jaeger 2.x com OTLP nativo (estável em 2026)
