# TypeScript Strict Config - tsconfig.json Best Practices

Configuração recomendada para projetos TypeScript modernos (5.7+).

---

## tsconfig.json Recomendado

```jsonc
{
	"compilerOptions": {
		// Type Checking — maximum strictness
		"strict": true,
		"noUncheckedIndexedAccess": true,
		"exactOptionalPropertyTypes": true,
		"noFallthroughCasesInSwitch": true,
		"noImplicitOverride": true,
		"noImplicitReturns": true,
		"noPropertyAccessFromIndexSignature": true,
		"noUnusedLocals": true,
		"noUnusedParameters": true,
		"forceConsistentCasingInFileNames": true,
		"verbatimModuleSyntax": true,

		// Module System
		"module": "ESNext",
		"moduleResolution": "bundler",
		"resolveJsonModule": true,
		"allowImportingTsExtensions": true,
		"noEmit": true,

		// Language & Environment
		"target": "ES2022",
		"lib": ["ES2023", "DOM", "DOM.Iterable"],
		"jsx": "react-jsx",

		// Path Aliases
		"baseUrl": ".",
		"paths": {
			"@/*": ["./src/*"]
		},

		// Interop
		"esModuleInterop": true,
		"isolatedModules": true,
		"skipLibCheck": true
	},
	"include": ["src/**/*.ts", "src/**/*.tsx"],
	"exclude": ["node_modules", "dist", "build"]
}
```

---

## Opções do Strict Mode Explicadas

### `strict: true`

Habilita todas as strict flags de uma vez:

| Flag | O que faz |
|------|--------------|
| `strictNullChecks` | `null` e `undefined` são tipos distintos; devem ser tratados explicitamente |
| `strictFunctionTypes` | Checagem contravariante de parâmetros de função |
| `strictBindCallApply` | Type-check de `bind`, `call`, `apply` |
| `strictPropertyInitialization` | Propriedades de classe devem ser inicializadas ou declaradas como opcionais |
| `noImplicitAny` | Erros em `any` type implícito |
| `noImplicitThis` | Erros em `this` com `any` type implícito |
| `alwaysStrict` | Emite `"use strict"` em todos os arquivos |
| `useUnknownInCatchVariables` | `catch(e)` retorna `unknown` em vez de `any` |

### `noUncheckedIndexedAccess`

Acesso por índice retorna `T | undefined` em vez de `T`:

```typescript
const arr = [1, 2, 3];
const item = arr[0]; // number | undefined (not number)

// Forces explicit checks
if (item !== undefined) {
	console.log(item.toFixed()); // OK
}

const map: Record<string, number> = { a: 1 };
const val = map["b"]; // number | undefined (not number)
```

**Sempre habilite.** Pega bugs reais com acesso por índice a array/objeto.

### `exactOptionalPropertyTypes`

Distingue entre "propriedade ausente" e "propriedade é undefined":

```typescript
interface Config {
	name: string;
	timeout?: number; // can be MISSING, but not explicitly undefined
}

const a: Config = { name: "app" }; // OK — timeout missing
// const b: Config = { name: "app", timeout: undefined }; // Error!
```

### `verbatimModuleSyntax`

Força a keyword `type` explícita para imports type-only:

```typescript
// Must use 'type' for type-only imports
import type { User } from "./types";
import { createUser } from "./users";

// Or inline type imports
import { createUser, type User } from "./users";
```

Isso garante que bundlers possam remover type imports com segurança sem análise do TypeScript.

---

## ESM vs CJS

### Recomendação moderna: ESM-first

```jsonc
// package.json
{
	"type": "module"
}
```

```jsonc
// tsconfig.json
{
	"compilerOptions": {
		"module": "ESNext",
		"moduleResolution": "bundler"
	}
}
```

### Opções de moduleResolution

| Value | Quando usar |
|-------|-------------|
| `"bundler"` | Projetos frontend usando Vite, webpack, esbuild. **Escolha padrão.** |
| `"nodenext"` | Bibliotecas Node.js que precisam emitir ESM/CJS. Resolução strict. |
| `"node16"` | Igual ao nodenext mas fixado no comportamento do Node 16. |
| `"node"` | Resolução CJS legada. **Evite em projetos novos.** |

### `"bundler"` vs `"nodenext"`

- `bundler`: Relaxado — permite imports sem extensão, funciona com Vite/webpack
- `nodenext`: Strict — exige extensões `.js`, respeita `exports` do package.json

Use `bundler` para apps, `nodenext` para bibliotecas publicadas.

---

## Target e Lib

### `target`

Qual versão do JS emitir. Com `noEmit: true` (o bundler cuida do emit), defina para o mínimo do seu runtime:

| Runtime | Target recomendado |
|---------|-------------------|
| Browsers modernos | `ES2022` |
| Node 20+ | `ES2022` |
| Node 18 | `ES2021` |

### `lib`

Quais definições de tipo incluir:

```jsonc
{
	"lib": [
		"ES2023",      // Latest stable ES features
		"DOM",          // Browser APIs (window, document, fetch)
		"DOM.Iterable"  // Iterable DOM collections (NodeList, etc.)
	]
}
```

- **Frontend:** `["ES2023", "DOM", "DOM.Iterable"]`
- **Node.js:** `["ES2023"]` (use `@types/node` em vez de DOM)
- **Biblioteca compartilhada:** `["ES2023"]` (sem tipos específicos de runtime)

---

## Project References (Monorepo)

Para monorepos, use project references para manter os builds rápidos:

```jsonc
// tsconfig.json (root)
{
	"references": [
		{ "path": "./packages/shared" },
		{ "path": "./packages/web" },
		{ "path": "./packages/api" }
	],
	"files": []
}
```

```jsonc
// packages/shared/tsconfig.json
{
	"compilerOptions": {
		"composite": true,
		"outDir": "./dist",
		"rootDir": "./src"
	},
	"include": ["src/**/*.ts"]
}
```

```jsonc
// packages/web/tsconfig.json
{
	"compilerOptions": {
		"composite": true,
		"noEmit": true
	},
	"references": [
		{ "path": "../shared" }
	],
	"include": ["src/**/*.ts", "src/**/*.tsx"]
}
```

---

## Configs Específicas por Framework

### Next.js 15

```jsonc
{
	"compilerOptions": {
		"strict": true,
		"noUncheckedIndexedAccess": true,
		"exactOptionalPropertyTypes": true,
		"target": "ES2022",
		"lib": ["ES2023", "DOM", "DOM.Iterable"],
		"module": "ESNext",
		"moduleResolution": "bundler",
		"jsx": "preserve",
		"noEmit": true,
		"incremental": true,
		"esModuleInterop": true,
		"isolatedModules": true,
		"skipLibCheck": true,
		"resolveJsonModule": true,
		"verbatimModuleSyntax": true,
		"plugins": [{ "name": "next" }],
		"paths": {
			"@/*": ["./src/*"]
		}
	},
	"include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
	"exclude": ["node_modules"]
}
```

### Vite + React

```jsonc
{
	"compilerOptions": {
		"strict": true,
		"noUncheckedIndexedAccess": true,
		"target": "ES2022",
		"lib": ["ES2023", "DOM", "DOM.Iterable"],
		"module": "ESNext",
		"moduleResolution": "bundler",
		"jsx": "react-jsx",
		"noEmit": true,
		"isolatedModules": true,
		"esModuleInterop": true,
		"skipLibCheck": true,
		"verbatimModuleSyntax": true,
		"allowImportingTsExtensions": true,
		"paths": {
			"@/*": ["./src/*"]
		}
	},
	"include": ["src"],
	"exclude": ["node_modules"]
}
```

---

## Links

- [TypeScript — tsconfig reference](https://www.typescriptlang.org/tsconfig)
- [TypeScript — Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)
- [Total TypeScript — tsconfig cheat sheet](https://www.totaltypescript.com/tsconfig-cheat-sheet)
