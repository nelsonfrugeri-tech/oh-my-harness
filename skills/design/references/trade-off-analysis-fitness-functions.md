# Architecture Fitness Functions

## Conceito
Verificações automatizadas que garantem que as decisões de arquitetura sejam mantidas ao longo do tempo.

## Tipos
| Tipo | Ferramenta | Exemplo |
|------|------|---------|
| Regras de dependência | ArchUnit (Java), Dependency Cruiser (JS), import-linter (Python) | "a camada de domínio não deve importar da infraestrutura" |
| Métricas de acoplamento | Análise de código | "Nenhum módulo tem afferent coupling > 10" |
| Tempo de build | Métrica de CI | "O build completa em < 5 minutos" |
| Cobertura de testes | Ferramentas de cobertura | "O domínio core tem > 90% de cobertura" |
| Compatibilidade de API | OpenAPI diff | "Nenhum breaking change na API pública" |
| Performance | Suíte de benchmark | "Latência P99 < 200ms no teste de carga" |

## Exemplo em Python (import-linter)
```toml
# .importlinter
[importlinter]
root_packages = myapp

[importlinter:contract:layers]
name = Layer architecture
type = layers
layers =
    myapp.api
    myapp.domain
    myapp.infrastructure
```

## Integração com CI
- Execute as fitness functions em todo PR
- Bloqueie o merge se restrições arquiteturais forem violadas
- Dashboard mostrando as tendências das fitness functions ao longo do tempo
