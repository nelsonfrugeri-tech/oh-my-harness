# Monolito vs Monolito Modular vs Microservices

## O Espectro de Arquitetura (2026)

A indústria foi além do debate binário monolito-vs-microservices.
A arquitetura existe em um espectro. O monolito modular é o ponto de equilíbrio pragmático
para a maioria dos times em 2026.

## Matriz Comparativa

| Critério | Monolito | Monolito Modular | Microservices |
|----------|----------|-----------------|---------------|
| Deployment | Unidade única | Unidade única | Independente por serviço |
| Consistência de dados | Transações ACID | ACID dentro dos módulos | Consistência eventual |
| Comunicação | Chamadas de função | Chamadas de função (API do módulo) | Rede (HTTP/gRPC/eventos) |
| Autonomia do time | Baixa | Média | Alta |
| Complexidade operacional | Baixa | Baixa | Alta |
| Overhead de latência | Nenhum | Nenhum | Saltos de rede |
| Debug/trace | Stack traces simples | Stack traces simples | Distributed tracing |
| Diversidade de tecnologia | Stack único | Stack único | Poliglota possível |
| Granularidade de escala | App inteiro | App inteiro | Por serviço |
| Velocidade de dev (time pequeno) | Rápida | Rápida | Lenta (overhead) |
| Velocidade de dev (organização grande) | Lenta (conflitos) | Média | Rápida (independência) |

## Framework de Decisão

### Comece pelo Monolito

```
New project? Start with a monolith.
- You don't know your domain boundaries yet
- Network overhead is unnecessary complexity
- ACID transactions are free
- Debugging is trivial
```

### Evolua para o Monolito Modular

```
Growing team (10-50)? Refactor to modular monolith.
- Enforce module boundaries in code
- Each module owns its tables (separate schemas)
- Communication via public module APIs only
- No direct cross-module database access
```

**Estrutura do monolito modular:**
```
src/
  modules/
    orders/
      __init__.py       # Public API exports only
      api.py            # Public functions other modules can call
      domain/           # Internal: business logic
        models.py
        services.py
      infra/            # Internal: database, external calls
        repository.py
        client.py
      tests/
    payments/
      __init__.py
      api.py
      domain/
      infra/
      tests/
```

**Regras de imposição:**
1. `__init__.py` exporta apenas a API pública
2. Regra de linting: nenhum import de `modules.X.domain` ou `modules.X.infra` por outros módulos
3. Testes de arquitetura verificam que não há violações de fronteira entre módulos
4. Cada módulo tem seu próprio schema de banco de dados (ou prefixo de schema)

### Extraia para Microservices (Quando Justificado)

```
Only extract to microservices when:
- A module needs independent scaling (10x more traffic)
- A module needs different technology (ML in Python, API in Go)
- Team independence is blocked by monolith deployment
- Compliance requires isolation (PCI-DSS, HIPAA)
```

**Extraia um módulo por vez:**
1. O módulo já tem uma fronteira de API limpa (monolito modular)
2. Substitua as chamadas in-process por HTTP/gRPC
3. Extraia as tabelas do banco para um banco separado
4. Implante de forma independente
5. Adicione circuit breakers e timeouts

## Sinais do Mundo Real

**Sinais de que você precisa de microservices:**
- A fila de deploy tem 2+ semanas
- Os times bloqueiam uns aos outros nas releases
- Um componente precisa de 100x mais recursos
- Domínios regulatórios distintos (PCI vs não-PCI)

**Sinais de que você NÃO precisa de microservices:**
- "A Netflix faz isso" (você não é a Netflix)
- Time com menos de 10 desenvolvedores
- Domínio de negócio único
- Sem necessidade de escala independente
- O time não tem expertise em sistemas distribuídos

## O Caso da Amazon Prime Video (2023)

A Amazon Prime Video migrou de microservices DE VOLTA para um monolito no sistema de
monitoramento de qualidade de vídeo. A arquitetura distribuída tinha:
- Alto custo de infraestrutura (transferência de dados entre serviços)
- Gargalo de escala na camada de orquestração
- Complexidade desnecessária para um serviço de um único time

**Lição:** decisões de arquitetura dependem do contexto. Até a Amazon escolhe monolitos
quando o contexto justifica.

## Fontes

- https://blog.bytebytego.com/p/monolith-vs-microservices-vs-modular
- https://www.javacodegeeks.com/2025/12/microservices-vs-modular-monoliths-in-2025-when-each-approach-wins.html
- https://blog.justenougharchitecture.com/microservices-vs-monoliths-vs-modular-monoliths-a-2025-decision-framework/
- Sam Newman, "Building Microservices" (2nd ed, 2021)
