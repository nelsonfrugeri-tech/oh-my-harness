# Padrões de Arquitetura Orientada a Eventos

## CQRS (Command Query Responsibility Segregation)
- Separe os modelos de leitura e escrita
- Modelo de escrita: normalizado, otimizado para consistência
- Modelo de leitura: desnormalizado, otimizado para queries
- Use quando: os padrões de leitura/escrita diferem significativamente, necessidade de escala independente

## Event Sourcing
- Armazene eventos (fatos), não o estado atual
- Reconstrua o estado reproduzindo os eventos
- Benefícios: trilha de auditoria completa, debugging com time-travel, integração orientada a eventos
- Trade-offs: complexidade, consistência eventual, desafios de versionamento de eventos
- Use quando: requisitos de auditoria, lógica de domínio complexa, necessidade de replay de eventos

## Padrões de Saga
### Choreography
- Os serviços reagem a eventos de outros serviços
- Sem coordenador central — acoplamento fraco
- Fluxo completo mais difícil de entender, transações compensatórias distribuídas
- Use quando: fluxos simples, poucos serviços

### Orchestration  
- Um orquestrador central coordena os passos da saga
- Mais fácil de entender, tratamento de erros centralizado
- Risco de ponto único de falha, acoplamento mais forte ao orquestrador
- Use quando: fluxos complexos, muitos serviços, necessidade de visibilidade

## Design de Eventos
```json
{
  "event_id": "uuid",
  "event_type": "OrderPlaced",
  "aggregate_id": "order-123",
  "timestamp": "2026-01-01T00:00:00Z",
  "version": 1,
  "data": { "items": [...], "total": 99.99 },
  "metadata": { "user_id": "u-456", "correlation_id": "corr-789" }
}
```

## Versionamento de Eventos
- Schema registry (Confluent, AWS Glue)
- Upcasters: transformam eventos antigos para o novo schema na leitura
- Nunca apague tipos de evento — deprecie e pare de produzir
