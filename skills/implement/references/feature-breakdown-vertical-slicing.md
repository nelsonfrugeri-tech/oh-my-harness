# Vertical Slicing & Walking Skeleton

## Vertical Slice
Uma slice que toca TODAS as camadas (UI → API → domínio → DB) mas entrega UMA fatia estreita de funcionalidade.

### Exemplo
Em vez de: "Construir gestão de usuários" (horizontal — todo o CRUD de uma vez)
Faça: "Usuário consegue se registrar com email" → "Usuário consegue fazer login" → "Usuário consegue redefinir a senha"

Cada slice é deployável e testável de forma independente.

## Critérios INVEST para Slices
- **I**ndependent — sem dependências de outras slices
- **N**egotiable — o escopo pode ser ajustado
- **V**aluable — entrega valor ao usuário
- **E**stimable — pequeno o suficiente para estimar
- **S**mall — concluível em 1-3 dias
- **T**estable — critérios de aceite claros

## Walking Skeleton
Implementação mínima ponta a ponta que prova que a arquitetura funciona.

```
Day 1: Empty endpoint → returns hardcoded response
Day 2: Endpoint → service → repository → real DB
Day 3: Basic error handling + health check
Day 4: CI/CD deploys skeleton to staging
```

Agora você tem: arquitetura comprovada, pipeline deployável, uma base sobre a qual construir.

## Estratégia de Decomposição
1. Mapeie a jornada do usuário (story map)
2. Identifique a primeira slice mais fina possível
3. Construa o walking skeleton para essa slice
4. Itere: cada slice adiciona funcionalidade ao skeleton
