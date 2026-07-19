# Guia do Modelo C4

## Visão Geral

O modelo C4 (Context, Containers, Components, Code) de Simon Brown fornece um conjunto
hierárquico de diagramas de arquitetura de software. Pense nele como o Google Maps para
software — dá para aproximar e afastar em diferentes níveis de detalhe.

## Nível 1: Diagrama de Contexto do Sistema

**Objetivo:** mostrar como o sistema se encaixa no mundo ao seu redor.

**Elementos:**
- Seu sistema de software (centro)
- Usuários/personas (quem o utiliza)
- Sistemas externos (com o que ele se integra)

**Regras:**
- No máximo 10-15 elementos
- Sem detalhes técnicos (nada de bancos de dados, filas)
- Rotule os relacionamentos com o que fazem, não como fazem

**Structurizr DSL:**
```
workspace {
    model {
        customer = person "Customer" "Places orders online"
        admin = person "Admin" "Manages products and orders"

        ecommerce = softwareSystem "E-Commerce Platform" "Allows customers to browse and purchase products" {
            !tags "internal"
        }

        payment = softwareSystem "Payment Gateway" "Processes credit card payments" {
            !tags "external"
        }
        email = softwareSystem "Email Service" "Sends transactional emails" {
            !tags "external"
        }

        customer -> ecommerce "Browses products, places orders"
        admin -> ecommerce "Manages catalog and orders"
        ecommerce -> payment "Processes payments" "HTTPS"
        ecommerce -> email "Sends order confirmations" "SMTP"
    }
    views {
        systemContext ecommerce "SystemContext" {
            include *
            autoLayout
        }
    }
}
```

## Nível 2: Diagrama de Containers

**Objetivo:** mostrar as escolhas de tecnologia em alto nível e como os containers se comunicam.

**Elementos:**
- Containers: aplicações web, APIs, bancos de dados, filas de mensagens, sistemas de arquivos
- Sistemas externos (do Nível 1)
- Usuários (do Nível 1)

**Regras:**
- Um container = uma unidade que pode ser implantada/executada separadamente
- Inclua as escolhas de tecnologia (ex.: "React SPA", "Python/FastAPI", "PostgreSQL")
- Mostre os protocolos de comunicação nas setas (HTTPS, gRPC, SQL, AMQP)

**Structurizr DSL:**
```
workspace {
    model {
        customer = person "Customer"

        ecommerce = softwareSystem "E-Commerce Platform" {
            spa = container "Web App" "Product browsing and checkout" "React/TypeScript"
            api = container "API Server" "REST API for all operations" "Python/FastAPI"
            worker = container "Background Worker" "Processes async tasks" "Python/Celery"
            db = container "Database" "Stores products, orders, users" "PostgreSQL"
            cache = container "Cache" "Session and product cache" "Redis"
            queue = container "Message Queue" "Async task distribution" "RabbitMQ"
        }

        payment = softwareSystem "Payment Gateway" "" "external"

        customer -> spa "Uses" "HTTPS"
        spa -> api "Calls" "HTTPS/JSON"
        api -> db "Reads/Writes" "SQL"
        api -> cache "Reads/Writes" "Redis Protocol"
        api -> queue "Publishes tasks" "AMQP"
        worker -> queue "Consumes tasks" "AMQP"
        worker -> db "Reads/Writes" "SQL"
        api -> payment "Processes payments" "HTTPS"
    }
    views {
        container ecommerce "Containers" {
            include *
            autoLayout
        }
    }
}
```

## Nível 3: Diagrama de Componentes

**Objetivo:** mostrar a estrutura interna de um único container.

**Elementos:**
- Componentes: agrupamentos lógicos (controllers, services, repositories)
- Outros containers com os quais interagem

**Regras:**
- Crie apenas para containers complexos
- Componentes = lógicos, não físicos (um componente pode abranger vários arquivos)
- Mostre qual componente conversa com qual dependência externa

**Quando criar:** apenas quando um container é complexo o suficiente para que sua estrutura
interna precise de documentação. Pule para containers simples (ex.: um cache Redis).

## Nível 4: Diagrama de Código

**Objetivo:** detalhe em nível de classe/função.

**Regras:** quase nunca vale a pena manter manualmente. Use a navegação da IDE no lugar.
Útil apenas para algoritmos ou estruturas de dados complexas que precisem de explicação visual.

## Diagramas Complementares

Além dos níveis centrais do C4, estes diagramas acrescentam contexto:

| Diagrama | Objetivo | Quando |
|---------|---------|------|
| **Deployment** | Onde cada container roda (cloud, k8s, VMs) | Para operações e infraestrutura |
| **Dynamic** | Sequência de interações para um caso de uso específico | Fluxos complexos |
| **System Landscape** | Todos os sistemas da organização | Contexto corporativo |

## Dicas de Structurizr DSL

```
# Tags for styling
element "external" {
    background #999999
    color #ffffff
}

# Groups for visual organization
group "Payment Domain" {
    paymentService = container "Payment Service" ...
    paymentDb = container "Payment DB" ...
}

# Deployment view
deploymentEnvironment "Production" {
    deploymentNode "AWS" {
        deploymentNode "ECS" {
            containerInstance api
            containerInstance worker
        }
        deploymentNode "RDS" {
            containerInstance db
        }
    }
}
```

## Anti-padrões

1. **Níveis demais** — a maioria dos projetos precisa apenas do Nível 1 + Nível 2
2. **Detalhe demais** — se um diagrama tem 30+ elementos, divida-o
3. **Protocolos ausentes** — sempre rotule as setas com protocolo/formato
4. **Mistura de níveis** — não mostre bancos de dados em um diagrama de Contexto do Sistema
5. **Diagramas desatualizados** — trate diagramas como código, atualize junto com a base de código

## Fontes

- https://c4model.com/
- https://structurizr.com/
- https://github.com/structurizr/dsl
