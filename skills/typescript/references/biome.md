# Biome 2+ - Linter & Formatter

Biome substitui ESLint + Prettier com uma unica ferramenta ultrarapida.

---

## Config

```jsonc
// biome.json
{
	"$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
	"organizeImports": {
		"enabled": true
	},
	"formatter": {
		"enabled": true,
		"indentStyle": "tab",
		"indentWidth": 2,
		"lineWidth": 100
	},
	"linter": {
		"enabled": true,
		"rules": {
			"recommended": true,
			"complexity": {
				"noBannedTypes": "error",
				"noExcessiveCognitiveComplexity": {
					"level": "warn",
					"options": { "maxAllowedComplexity": 15 }
				}
			},
			"correctness": {
				"noUnusedImports": "error",
				"noUnusedVariables": "warn",
				"useExhaustiveDependencies": "warn"
			},
			"style": {
				"noNonNullAssertion": "warn",
				"useConst": "error",
				"useImportType": "error"
			},
			"suspicious": {
				"noExplicitAny": "warn",
				"noConsole": {
					"level": "warn",
					"options": {
						"allow": ["warn", "error"]
					}
				}
			},
			"a11y": {
				"recommended": true
			}
		}
	},
	"javascript": {
		"formatter": {
			"quoteStyle": "double",
			"trailingCommas": "all",
			"semicolons": "always"
		}
	},
	"files": {
		"ignore": [
			"node_modules",
			"dist",
			"build",
			".next",
			"coverage",
			"*.min.js"
		]
	}
}
```

---

## Comandos

```bash
# Check everything (lint + format + imports)
biome check .

# Check and auto-fix
biome check --write .

# Format only
biome format --write .

# Lint only
biome lint .

# CI mode (exits with error code)
biome ci .
```

---

## Migração do ESLint + Prettier

```bash
# Auto-migrate ESLint config
biome migrate eslint --write

# Auto-migrate Prettier config
biome migrate prettier --write
```

Após a migração:
1. Remova `.eslintrc`, `.prettierrc`, `.eslintignore`, `.prettierignore`
2. Remova `eslint`, `prettier`, e todos os plugins do `package.json`
3. Atualize os scripts:
   ```json
   {
     "scripts": {
       "lint": "biome ci .",
       "format": "biome check --write ."
     }
   }
   ```

---

## Integração com o Editor

### VS Code

Instale a extensão `biomejs.biome`.

```jsonc
// .vscode/settings.json
{
	"editor.defaultFormatter": "biomejs.biome",
	"editor.formatOnSave": true,
	"editor.codeActionsOnSave": {
		"quickfix.biome": "explicit",
		"source.organizeImports.biome": "explicit"
	},
	// Disable conflicting formatters
	"prettier.enable": false,
	"eslint.enable": false
}
```

---

## Configuração de CI

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  biome:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: biomejs/setup-biome@v2
        with:
          version: latest
      - run: biome ci .
```

---

## Padrões de Ignore

```jsonc
// biome.json
{
	"files": {
		"ignore": [
			"node_modules",
			"dist",
			"*.generated.ts",
			"**/*.d.ts"
		]
	}
}
```

Supressão inline:
```typescript
// biome-ignore lint/suspicious/noExplicitAny: legacy API requires any
const data: any = legacyApi.getData();

// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: parser logic
function parseComplex() { ... }
```

---

## Principais Regras de Lint

| Regra | Categoria | O que detecta |
|------|----------|-----------------|
| `noExplicitAny` | suspicious | Uso do tipo `any` |
| `noUnusedImports` | correctness | Imports mortos |
| `noUnusedVariables` | correctness | Variáveis mortas |
| `useExhaustiveDependencies` | correctness | Deps de hook faltando |
| `noNonNullAssertion` | style | Operador `!` inseguro |
| `useConst` | style | `let` que deveria ser `const` |
| `useImportType` | style | `type` faltando em imports type-only |
| `noConsole` | suspicious | Statements de console em código de produção |
| `noBannedTypes` | complexity | Tipos `{}`, `Object`, `Function` |
| `a11y/*` | a11y | Problemas de acessibilidade em JSX |

---

## Links

- [Biome Documentation](https://biomejs.dev/)
- [Biome — Rules](https://biomejs.dev/linter/rules/)
- [Biome — Formatter](https://biomejs.dev/formatter/)
- [Biome — Migration Guide](https://biomejs.dev/guides/migrate-eslint-prettier/)
