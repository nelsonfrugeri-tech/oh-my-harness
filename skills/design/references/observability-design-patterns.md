# Observabilidade por Design

## Integração dos Três Pilares
```
Request → Trace (distributed, spans) 
       → Metrics (aggregated, counters/histograms)
       → Logs (contextual, structured)
       
Link: trace_id in all three → correlated debugging
```

## Padrão de Correlação
```python
# Inject trace_id into every log entry
import structlog
from opentelemetry import trace

structlog.configure(
    processors=[
        add_trace_context,  # adds trace_id, span_id
        structlog.processors.JSONRenderer(),
    ]
)
```

## Padrão de Dashboard RED/USE
- **RED** para serviços: Rate, Errors, Duration
- **USE** para recursos: Utilization, Saturation, Errors
- Todo serviço recebe os dois

## Checklist de Observabilidade para Novos Serviços
- [ ] Logging estruturado com correlação por trace_id
- [ ] Instrumentação com OpenTelemetry (automática + manual para caminhos críticos)
- [ ] Métricas RED exportadas para o Prometheus
- [ ] Endpoint de health (/health, /ready)
- [ ] SLO definido e com dashboard
- [ ] Alertas baseados na burn rate do SLO
- [ ] Runbook escrito e vinculado aos alertas
