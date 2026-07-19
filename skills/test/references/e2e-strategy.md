# Estratégia de Testes -- Pyramid vs Trophy

## A Pirâmide de Testes

Originalmente proposta por Mike Cohn, popularizada por Martin Fowler.

```
        /  E2E  \          5-10% of tests
       /----------\
      / Integration \      20-30% of tests
     /----------------\
    /    Unit Tests     \  60-70% of tests
   /____________________\
```

### Justificativa
- Testes unitários são rápidos, baratos e isolados
- Testes de integração têm custo moderado
- Testes E2E são lentos, caros e frágeis
- Mais testes na base = feedback mais rápido

### Melhor Para
- Bibliotecas com funções puras
- Serviços de backend com lógica de negócio complexa
- Pipelines de processamento de dados
- Algoritmos e computações matemáticas

## O Troféu de Testes

Proposto por Kent C. Dodds como uma alternativa moderna.

```
        ___E2E___          10% of tests
       /         \
      | Integration |      40-50% of tests (MOST)
      |_____________|
       \  Unit   /         20-30% of tests
        \_______/
       |  Static  |        Continuous (type checker, linter)
       |__________|
```

### Justificativa
- Testes de integração dão a maior confiança por teste
- O ferramental moderno torna os testes de integração rápidos o suficiente
- Testes unitários em código trivial adicionam manutenção sem confiança
- A análise estática captura categorias inteiras de bugs de graça

### Melhor Para
- Aplicações frontend (React, Vue, Angular)
- APIs REST/GraphQL
- Microsserviços com muitos pontos de integração
- Aplicações full-stack

## O Diamante de Testes (Híbrido)

Para times que precisam de ambos:

```
        /  E2E  \          Critical paths only
       /----------\
      | Integration |      Most tests here
      |_____________|
      | Integration |      (yes, double-wide)
      |_____________|
       \  Unit   /         Pure logic only
        \_______/
```

## O que Testar Onde

### Análise Estática
```
mypy / TypeScript strict     -> type errors
ruff / Biome                 -> code smells, unused imports
bandit / semgrep             -> security vulnerabilities
```

### Testes Unitários
- Funções puras (sem I/O, sem efeitos colaterais)
- Lógica de validação
- Transformações de dados
- Cálculos de regras de negócio
- Formatação de mensagens de erro
- Funções utilitárias

### Testes de Integração
- Ciclo de request/response de endpoint HTTP
- Operações CRUD de banco de dados
- Comportamento de leitura/escrita de cache
- Produção/consumo de mensagens de fila
- Fluxo de autenticação
- Verificações de autorização
- Upload/download de arquivos

### Testes E2E
- Signup do usuário -> login -> usar funcionalidade -> logout
- Fluxo de compra (adicionar ao carrinho -> checkout -> pagamento -> confirmação)
- Operações de admin (criar usuário -> atribuir papel -> verificar acesso)
- Recuperação de erro (falha de rede -> retry -> sucesso)

## Anti-Padrões

### Cone de Sorvete de Testes (pirâmide invertida)
```
   /________________________\
  /       E2E Tests          \    <- too many, slow, flaky
 /--------------------------\
|     Integration Tests      |
 \--------------------------/
  \    Unit Tests    /            <- too few
   \________________/
```

**Problema:** CI lento, testes flaky, baixa confiança dos desenvolvedores.

### Ampulheta de Testes
```
        /  E2E  \              <- many
       /----------\
      |            |
      |            |           <- few integration tests
      |            |
       \__________/
    /    Unit Tests     \      <- many
   /____________________\
```

**Problema:** Unit + E2E sem integração = lacunas no meio onde a maioria dos bugs vive.
