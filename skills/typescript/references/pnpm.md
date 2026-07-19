# pnpm 10+ - Package Manager

pnpm e o gerenciador de pacotes recomendado para projetos TypeScript.

---

## Por que pnpm

- **Eficiente em disco**: Hard links — pacotes armazenados uma vez globalmente, linkados nos projetos
- **Strict por padrão**: Sem dependências fantasma (não dá para importar o que você não declarou)
- **Rápido**: Instalação paralela, store content-addressable
- **Nativo para monorepo**: Suporte a workspace embutido

---

## Boas Práticas de .npmrc

```ini
# .npmrc
# Strict mode — fail if peer deps are not met
strict-peer-dependencies=true

# Hoist only these packages (explicit whitelist)
public-hoist-pattern[]=*types*
public-hoist-pattern[]=*eslint*
public-hoist-pattern[]=*prettier*

# Exact versions by default
save-exact=true

# Always use lockfile
frozen-lockfile=true

# Node.js version enforcement
use-node-version=22.12.0
```

---

## Workspaces (Monorepo)

```yaml
# pnpm-workspace.yaml
packages:
  - "packages/*"
  - "apps/*"
  - "tools/*"
```

```
my-monorepo/
├── pnpm-workspace.yaml
├── package.json
├── apps/
│   ├── web/
│   │   └── package.json
│   └── api/
│       └── package.json
├── packages/
│   ├── shared/
│   │   └── package.json
│   └── ui/
│       └── package.json
└── tools/
    └── scripts/
        └── package.json
```

### Comandos de Workspace

```bash
# Install all workspace dependencies
pnpm install

# Run command in specific workspace
pnpm --filter web dev
pnpm --filter @myorg/shared build

# Run command in all workspaces
pnpm -r build
pnpm -r test

# Run only in workspaces that changed since main
pnpm -r --filter "...[origin/main]" build

# Add dependency to specific workspace
pnpm --filter web add react
pnpm --filter web add -D vitest

# Add workspace dependency (internal package)
pnpm --filter web add @myorg/shared --workspace
```

### Workspace Protocol

Referencie pacotes internos:

```json
// apps/web/package.json
{
	"dependencies": {
		"@myorg/shared": "workspace:*",
		"@myorg/ui": "workspace:^1.0.0"
	}
}
```

| Protocolo | Significado |
|----------|---------|
| `workspace:*` | Qualquer versão — sempre resolve para local |
| `workspace:^1.0.0` | Constraint de semver para publicação |
| `workspace:~1.0.0` | Constraint de tilde para publicação |

---

## Strict Mode

pnpm é strict por padrão — você não pode importar pacotes que não declarou:

```json
// If package A depends on package B, and B depends on lodash:
// In A, you CANNOT do: import _ from "lodash"
// You must explicitly add lodash to A's dependencies
```

Isso previne dependências fantasma — a causa #1 de problemas do tipo "funciona na minha máquina".

---

## Peer Dependencies

```bash
# Install and auto-install peer deps
pnpm install

# See unmet peer dependencies
pnpm install --reporter=default
```

```json
// package.json
{
	"peerDependencies": {
		"react": "^18.0.0 || ^19.0.0",
		"react-dom": "^18.0.0 || ^19.0.0"
	},
	"peerDependenciesMeta": {
		"react-dom": {
			"optional": true
		}
	}
}
```

---

## Overrides

Força uma versão específica em todos os pacotes:

```json
// package.json (root)
{
	"pnpm": {
		"overrides": {
			"typescript": "5.7.3",
			"minimist@<1.2.6": ">=1.2.6"
		}
	}
}
```

---

## Catalogs

Centralize o gerenciamento de versões em monorepos:

```yaml
# pnpm-workspace.yaml
packages:
  - "packages/*"
  - "apps/*"

catalog:
  react: "19.0.0"
  react-dom: "19.0.0"
  typescript: "5.7.3"
  vitest: "3.0.4"

catalogs:
  testing:
    "@testing-library/react": "16.1.0"
    "@testing-library/user-event": "14.5.2"
    "@playwright/test": "1.50.1"
```

Uso no package.json:
```json
{
	"dependencies": {
		"react": "catalog:",
		"react-dom": "catalog:"
	},
	"devDependencies": {
		"@testing-library/react": "catalog:testing",
		"vitest": "catalog:"
	}
}
```

---

## Comandos Comuns

```bash
# Install
pnpm install              # Install all deps
pnpm install --frozen-lockfile  # CI mode — fails if lockfile is outdated

# Add/remove
pnpm add react            # Add production dep
pnpm add -D vitest        # Add dev dep
pnpm remove lodash        # Remove dep

# Update
pnpm update               # Update within ranges
pnpm update --latest      # Update to latest (may break)
pnpm update react         # Update specific package

# Scripts
pnpm dev                  # Run dev script
pnpm build                # Run build script
pnpm test                 # Run test script

# Inspect
pnpm list                 # List installed packages
pnpm list --depth=0       # Top-level only
pnpm why react            # Why is this installed?
pnpm outdated             # Show outdated packages

# Store
pnpm store prune          # Clean up orphaned packages
```

---

## Configuração de CI

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 10
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - run: pnpm test
```

---

## Links

- [pnpm Documentation](https://pnpm.io/)
- [pnpm — Workspaces](https://pnpm.io/workspaces)
- [pnpm — Catalogs](https://pnpm.io/catalogs)
- [pnpm — .npmrc](https://pnpm.io/npmrc)
