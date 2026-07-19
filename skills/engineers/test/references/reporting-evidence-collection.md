# Relatórios de Teste e Coleta de Evidências

## Relatórios de Teste em CI
```yaml
# GitHub Actions
- name: Run tests
  run: pytest --junitxml=report.xml --cov=app --cov-report=html

- name: Upload test results
  uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: report.xml

- name: Upload coverage
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
```

## Artefatos de Evidência
| Tipo | Formato | Ferramenta |
|------|--------|------|
| Resultados de teste | JUnit XML | pytest, jest |
| Cobertura | HTML, Cobertura XML | coverage.py, istanbul |
| Screenshots | PNG | Playwright |
| Performance | JSON, HTML | k6, Locust |
| Acessibilidade | JSON | axe-core |
| Contratos de API | JSON | Pact |

## Limiares de Cobertura
```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 80

[tool.coverage.run]
branch = true
```

## Padrão de Comentário em PR
Comentar automaticamente em PRs com:
- Resumo de aprovação/falha dos testes
- Delta de cobertura (aumentou/diminuiu)
- Sinalizações de regressão de performance
- Links de diff de screenshots (se houver testes visuais)

## Anti-padrões
- Cobertura como única métrica de qualidade
- Armazenar artefatos de teste para sempre (retenha por 30 dias)
- Ignorar relatórios de testes flaky
