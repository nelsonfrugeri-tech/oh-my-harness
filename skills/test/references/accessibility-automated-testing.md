# Testes Automatizados de Acessibilidade

## Integração com axe-core
```javascript
// Playwright + axe-core
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('page has no a11y violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

// Exclude known issues
const results = await new AxeBuilder({ page })
  .exclude('.third-party-widget')
  .withTags(['wcag2a', 'wcag2aa', 'wcag22aa'])
  .analyze();
```

## Lighthouse CI
```yaml
# lighthouserc.js
module.exports = {
  ci: {
    collect: { url: ['http://localhost:3000/'] },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.9 }],
      },
    },
  },
};
```

## Verificações-Chave do WCAG 2.2 (Automatizadas)
- Imagens têm texto alternativo (alt)
- Inputs de formulário têm labels
- Razões de contraste de cor (4.5:1 texto normal, 3:1 texto grande)
- A ordem de foco é lógica
- Atributos ARIA são válidos
- A hierarquia de cabeçalhos está correta (h1 → h2 → h3)

## O que a Automação Não Detecta (Requer Manual)
- Fluxo de navegação por teclado
- Experiência com leitor de tela
- Texto alternativo (alt) significativo (não apenas presente)
- Gerenciamento de foco em SPAs
- Anúncios de conteúdo dinâmico
