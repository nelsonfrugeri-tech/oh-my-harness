# Checklist de Validação

## Validação Automatizada

### Projetos Python
```bash
# 1. Lint
ruff check . --fix

# 2. Format
black --check .

# 3. Type check
mypy src/

# 4. Unit tests
pytest tests/unit/ -v

# 5. Integration tests
pytest tests/integration/ -v

# 6. Full suite with coverage
pytest --cov=src --cov-report=term-missing
```

### Projetos TypeScript
```bash
# 1. Lint + Format
biome check --write .

# 2. Type check
tsc --noEmit

# 3. Unit tests
vitest run

# 4. E2E tests
playwright test

# 5. Coverage
vitest run --coverage
```

## Validação Manual

Quando os testes automatizados não são suficientes:

### Endpoints de API
```bash
# Test the endpoint manually
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "email": "test@example.com"}'

# Verify response code, body, headers
# Test error cases: invalid input, duplicate, unauthorized
```

### Mudanças de UI
- Verifique em pelo menos 2 navegadores
- Teste os breakpoints responsivos (mobile, tablet, desktop)
- Teste a navegação por teclado
- Teste com leitor de tela (se relevante para acessibilidade)
- Verifique o dark mode (se aplicável)

## Verificação de Regressão

Após a validação, sempre pergunte:
- Quebrei alguma funcionalidade existente?
- Alterei algum código compartilhado que outras funcionalidades usam?
- Há pontos de integração que precisam de teste?
