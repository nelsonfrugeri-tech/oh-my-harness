# Teste de Regressão Visual

## Screenshots com Playwright
```javascript
test('homepage visual', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.01,
    fullPage: true,
  });
});

// Component-level
test('button states', async ({ page }) => {
  const button = page.locator('.primary-button');
  await expect(button).toHaveScreenshot('button-default.png');
  await button.hover();
  await expect(button).toHaveScreenshot('button-hover.png');
});
```

## Atualizar Baselines
```bash
npx playwright test --update-snapshots
```

## Comparação de Ferramentas
| Ferramenta | Tipo | Melhor para |
|------|------|----------|
| Playwright screenshots | Built-in | Simples, sem infra adicional |
| Percy (BrowserStack) | Cloud SaaS | Cross-browser, UI de revisão em equipe |
| Chromatic (Storybook) | Cloud SaaS | Bibliotecas de componentes |
| reg-suit | Self-hosted | Open-source, integração com CI |

## Boas Práticas
- Teste no nível de componente (menos flaky que páginas inteiras)
- Tamanho de viewport e fontes consistentes
- Oculte conteúdo dinâmico (timestamps, anúncios)
- Revise os diffs no CI antes de fazer merge
- Não tire screenshot de tudo — foque na UI crítica
