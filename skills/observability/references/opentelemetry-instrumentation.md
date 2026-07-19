# Instrumentação do SDK OpenTelemetry

## Estratégia de Instrumentação

Comece com auto-instrumentação para ter visibilidade imediata e, então, adicione
spans manuais à medida que seu entendimento aprofunda. A jornada é incremental.

### Auto-Instrumentação

```python
# Python: zero-code auto-instrumentation
# pip install opentelemetry-distro opentelemetry-exporter-otlp
# opentelemetry-instrument python app.py

# Programmatic auto-instrumentation (more control)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

FlaskInstrumentor().instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
```

### Instrumentação Manual

```python
from opentelemetry import trace
from opentelemetry.trace import StatusCode

tracer = trace.get_tracer("my.service", "1.0.0")

@tracer.start_as_current_span("process_order")
def process_order(order_id: str) -> dict:
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)
    try:
        result = validate_order(order_id)
        span.set_attribute("order.items_count", len(result["items"]))
        return result
    except Exception as e:
        span.set_status(StatusCode.ERROR, str(e))
        span.record_exception(e)
        raise
```

## Propagação de Contexto

### W3C Trace Context (padrão, recomendado)

```python
from opentelemetry import propagate

# Inject context into outgoing HTTP headers
headers = {}
propagate.inject(headers)
# headers: traceparent, tracestate

# Extract context from incoming headers
ctx = propagate.extract(carrier=request.headers)
with tracer.start_as_current_span("handle_request", context=ctx):
    pass
```

### Baggage (contexto entre serviços)

```python
from opentelemetry import baggage, context

ctx = baggage.set_baggage("user.tier", "premium")
token = context.attach(ctx)
# Downstream reads: baggage.get_baggage("user.tier")
```

## Inicialização do SDK (deve ser a PRIMEIRA)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

resource = Resource.create({SERVICE_NAME: "my-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
# MUST happen before any instrumented library is imported
```

## Deploy do Collector

Sempre envie para o OTel Collector, não diretamente para os backends:
- Desacopla problemas de exportação da aplicação
- Simplifica o gerenciamento de segredos
- Habilita enriquecimento, amostragem e roteamento

```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
processors:
  batch: { timeout: 5s, send_batch_size: 8192 }
  memory_limiter: { limit_mib: 512 }
exporters:
  otlp: { endpoint: "tempo:4317" }
  prometheus: { endpoint: "0.0.0.0:8889" }
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp]
```

## Boas Práticas de Métricas

- Evite alocação no heap em caminhos críticos (hot paths)
- Use pré-agregação para consumo de memória previsível
- Meça a cobertura de instrumentação como você mede a cobertura de código

```python
from opentelemetry import metrics
meter = metrics.get_meter("my.service")
request_counter = meter.create_counter("http.requests", unit="1")
latency_histogram = meter.create_histogram("http.latency", unit="ms")
```

## Estratégias de Amostragem

| Estratégia | Caso de Uso |
|----------|----------|
| AlwaysOn | Dev/staging |
| TraceIdRatio(0.1) | 10% em produção com alto tráfego |
| ParentBased | Respeita a decisão do upstream |
| Custom | Todos os erros + N% de sucesso |

## Convenções Semânticas

Siga as convenções do OTel: `http.request.method`, `db.system`,
`rpc.service`. Personalizadas: reverse-DNS (`com.mycompany.order.id`).
