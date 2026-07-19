---
version: 1.0.0
name: typescript
description: |
  Base de conhecimento TypeScript/Frontend (2026). Cobre o type system avançado (discriminated unions,
  branded types, template literals, satisfies, conditional and mapped types), strict tsconfig,
  padrões estruturais de TypeScript, React 19+ (compound components, polymorphic, Server Components,
  Server Actions, streaming), custom hooks, árvore de decisão de state management (TanStack Query vs Zustand
  vs useState vs React Hook Form), Tailwind CSS v4, Vitest, Playwright E2E, otimização de performance
  (Core Web Vitals, code splitting) e ferramentas (Biome, pnpm, Vite).
  Use quando: (1) Escrever ou revisar código TypeScript/React, (2) Escolher estratégia de state management,
  (3) Projetar arquitetura de componentes React, (4) Configurar ferramentas de frontend.
  Triggers: /typescript, typescript, react, nextjs, frontend, vitest, tailwind, zustand, tanstack.
type: knowledge
---

# TypeScript — Base de Conhecimento

## Propósito

Esta skill é a base de conhecimento para engenharia moderna de TypeScript e frontend (2026).
Ela cobre o type system, arquitetura React, state management, testes e ferramentas.

**O que esta skill contém:**
- Type system de TypeScript (discriminated unions, branded types, utility types)
- Configuração de strict tsconfig
- Padrões de React 19+ (compound components, polymorphic, Server Components)
- Custom hooks e composição de hooks
- Arquitetura de state management (árvore de decisão)
- Tailwind CSS v4 (utility-first, OKLCH, CSS-first config)
- Vitest + Testing Library (testes de unidade e de componentes)
- Playwright (E2E, regressão visual)
- Performance (Core Web Vitals, code splitting, memoização)
- Ferramentas (Biome, pnpm, Vite)

---

## Princípios Fundamentais

1. **Sempre `strict: true`** — sem Any implícito, null safety, checagens contravariantes de funções
2. **Tipos são contratos** — discriminated unions em vez de campos nullable, branded types nas fronteiras
3. **Composição sobre herança** — compound components, hooks, não hierarquias de classes
4. **Server-first no Next.js** — priorize Server Components, adicione "use client" apenas quando necessário
5. **Formatação: Biome** — tabs, aspas duplas, ponto e vírgula, trailing commas (substitui ESLint + Prettier)

---

## 1. Type System

### Discriminated Unions

```typescript
// Model states explicitly — never "maybe" fields
type LoadingState<T> =
	| { status: "idle" }
	| { status: "loading" }
	| { status: "success"; data: T }
	| { status: "error"; error: string };

function render<T>(state: LoadingState<T>): React.ReactNode {
	switch (state.status) {
		case "idle":
			return null;
		case "loading":
			return <Spinner />;
		case "success":
			return <Data value={state.data} />;
		case "error":
			return <ErrorMessage message={state.error} />;
	}
}
```

### Branded Types

```typescript
// Prevent passing wrong ID types at compile time
type UserId = string & { readonly __brand: unique symbol };
type OrderId = string & { readonly __brand: unique symbol };

function createUserId(raw: string): UserId {
	if (!raw.startsWith("usr_")) throw new Error(`Invalid user ID: ${raw}`);
	return raw as UserId;
}

function getUser(id: UserId): Promise<User> { ... }
function getOrder(id: OrderId): Promise<Order> { ... }

const userId = createUserId("usr_123");
getUser(userId);          // OK
getOrder(userId);         // TypeScript error: UserId ≠ OrderId
```

### Template Literal Types

```typescript
type HTTPMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
type APIRoute = `/api/${string}`;
type EventName<T extends string> = `on${Capitalize<T>}`;

// Mapped types
type ReadOnly<T> = { readonly [K in keyof T]: T[K] };
type Optional<T> = { [K in keyof T]?: T[K] };
type Nullable<T> = { [K in keyof T]: T[K] | null };

// Conditional types
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
type FlattenArray<T> = T extends Array<infer U> ? U : T;
```

### `satisfies` Operator

```typescript
// satisfies: validate shape WITHOUT widening the type
const palette = {
	red: [255, 0, 0],
	green: "#00ff00",
	blue: [0, 0, 255],
} satisfies Record<string, string | number[]>;

// TypeScript knows red is number[] (not string | number[])
palette.red.map((x) => x * 2); // OK
palette.green.toUpperCase();    // OK
```

**Referência:** [references/type-system.md](references/type-system.md)

---

## 2. Strict tsconfig

```jsonc
// tsconfig.json
{
	"compilerOptions": {
		// Strict mode (required)
		"strict": true,
		"noUncheckedIndexedAccess": true,
		"exactOptionalPropertyTypes": true,
		"noImplicitOverride": true,

		// Module resolution
		"moduleResolution": "bundler",
		"module": "ESNext",
		"target": "ES2022",
		"lib": ["ES2022", "DOM", "DOM.Iterable"],

		// Output
		"outDir": "./dist",
		"rootDir": "./src",
		"declaration": true,

		// Developer experience
		"verbatimModuleSyntax": true,
		"forceConsistentCasingInFileNames": true,
		"skipLibCheck": true,

		// Path aliases
		"paths": {
			"@/*": ["./src/*"]
		}
	},
	"include": ["src"],
	"exclude": ["node_modules", "dist"]
}
```

**Referência:** [references/strict-config.md](references/strict-config.md)

---

## 3. React Component Patterns

### Compound Components

```typescript
interface SelectContextValue {
	value: string;
	onChange: (value: string) => void;
}

const SelectContext = createContext<SelectContextValue | null>(null);

function useSelect(): SelectContextValue {
	const ctx = useContext(SelectContext);
	if (!ctx) throw new Error("useSelect must be used within <Select>");
	return ctx;
}

interface SelectProps {
	value: string;
	onChange: (value: string) => void;
	children: React.ReactNode;
}

function Select({ value, onChange, children }: SelectProps): React.JSX.Element {
	return (
		<SelectContext value={{ value, onChange }}>
			<div role="listbox">{children}</div>
		</SelectContext>
	);
}

interface OptionProps {
	value: string;
	children: React.ReactNode;
}

Select.Option = function Option({ value, children }: OptionProps): React.JSX.Element {
	const { value: selected, onChange } = useSelect();
	return (
		<div
			role="option"
			aria-selected={selected === value}
			onClick={() => onChange(value)}
			className="cursor-pointer px-3 py-2 hover:bg-muted"
		>
			{children}
		</div>
	);
};
```

### Polymorphic Components

```typescript
type PolymorphicProps<T extends React.ElementType> = {
	as?: T;
	children?: React.ReactNode;
} & Omit<React.ComponentPropsWithRef<T>, "as" | "children">;

function Text<T extends React.ElementType = "span">({
	as,
	...props
}: PolymorphicProps<T>): React.JSX.Element {
	const Component = as ?? "span";
	return <Component {...props} />;
}

// Usage: infers the right props
<Text as="h1" className="text-4xl">Heading</Text>     // h1 props
<Text as="label" htmlFor="input">Label</Text>         // label props
<Text as="button" onClick={() => {}}>Button</Text>    // button props
```

**Referência:** [references/component-patterns.md](references/component-patterns.md)

---

## 4. React Server Components

```typescript
// Server Component (default in Next.js App Router — no "use client")
// Can: async/await, direct DB access, access server secrets
// Cannot: useState, useEffect, browser APIs, event handlers

async function UserProfile({ userId }: { userId: string }): Promise<React.JSX.Element> {
	// Direct DB call — no API needed
	const user = await db.user.findUniqueOrThrow({ where: { id: userId } });
	const posts = await db.post.count({ where: { authorId: userId } });

	return (
		<div>
			<h1>{user.name}</h1>
			<p>{posts} posts</p>
			<Suspense fallback={<ActivitySkeleton />}>
				<UserActivity userId={userId} />
			</Suspense>
		</div>
	);
}

// Client Component — only when you need interactivity
"use client";

interface LikeButtonProps {
	postId: string;
	initialCount: number;
}

function LikeButton({ postId, initialCount }: LikeButtonProps): React.JSX.Element {
	const [count, setCount] = useState(initialCount);
	const [liked, setLiked] = useState(false);

	return (
		<button
			onClick={() => {
				setCount((c) => c + (liked ? -1 : 1));
				setLiked((l) => !l);
			}}
			aria-pressed={liked}
		>
			{liked ? "♥" : "♡"} {count}
		</button>
	);
}
```

### Server Actions

```typescript
// app/actions.ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";

const createPostSchema = z.object({
	title: z.string().min(1).max(200),
	content: z.string().min(1),
});

export async function createPost(formData: FormData): Promise<{ error?: string }> {
	const parsed = createPostSchema.safeParse({
		title: formData.get("title"),
		content: formData.get("content"),
	});

	if (!parsed.success) {
		return { error: parsed.error.message };
	}

	await db.post.create({ data: parsed.data });
	revalidatePath("/posts");
	return {};
}
```

**Referência:** [references/server-components.md](references/server-components.md)

---

## 5. Custom Hooks

```typescript
// Generic debounce hook
function useDebounce<T>(value: T, delay: number): T {
	const [debounced, setDebounced] = useState<T>(value);

	useEffect(() => {
		const timer = setTimeout(() => setDebounced(value), delay);
		return () => clearTimeout(timer);
	}, [value, delay]);

	return debounced;
}

// Async operation hook with loading/error state
interface AsyncState<T> {
	data: T | null;
	loading: boolean;
	error: string | null;
}

function useAsync<T>(fn: () => Promise<T>, deps: React.DependencyList): AsyncState<T> {
	const [state, setState] = useState<AsyncState<T>>({
		data: null,
		loading: true,
		error: null,
	});

	useEffect(() => {
		let cancelled = false;
		setState({ data: null, loading: true, error: null });

		fn()
			.then((data) => {
				if (!cancelled) setState({ data, loading: false, error: null });
			})
			.catch((err: unknown) => {
				if (!cancelled) {
					setState({ data: null, loading: false, error: String(err) });
				}
			});

		return () => {
			cancelled = true;
		};
	}, deps); // eslint-disable-line react-hooks/exhaustive-deps

	return state;
}
```

**Referência:** [references/hooks.md](references/hooks.md)

---

## 6. State Management

### Árvore de Decisão

```
Que tipo de estado?
  |
  +-- Dados server/async (chamadas de API, DB) --> TanStack Query
  |
  +-- Estado de URL / navegação                --> Next.js router, nuqs
  |
  +-- Estado de formulário                     --> React Hook Form
  |
  +-- Estado complexo de client                --> Zustand
  |
  +-- Estado local simples                     --> useState / useReducer
```

### TanStack Query (Estado de Servidor)

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

function useUser(userId: string) {
	return useQuery({
		queryKey: ["users", userId],
		queryFn: () => fetchUser(userId),
		staleTime: 5 * 60 * 1000, // 5 minutes
		enabled: Boolean(userId),
	});
}

function useUpdateUser() {
	const queryClient = useQueryClient();
	return useMutation({
		mutationFn: updateUser,
		onSuccess: (updatedUser) => {
			queryClient.setQueryData(["users", updatedUser.id], updatedUser);
			queryClient.invalidateQueries({ queryKey: ["users"] });
		},
	});
}
```

### Zustand (Estado de Client)

```typescript
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface CartItem {
	id: string;
	name: string;
	price: number;
	quantity: number;
}

interface CartStore {
	items: CartItem[];
	addItem: (item: Omit<CartItem, "quantity">) => void;
	removeItem: (id: string) => void;
	updateQuantity: (id: string, quantity: number) => void;
	clear: () => void;
	total: () => number;
	itemCount: () => number;
}

const useCartStore = create<CartStore>()(
	devtools(
		persist(
			(set, get) => ({
				items: [],
				addItem: (item) =>
					set((s) => {
						const existing = s.items.find((i) => i.id === item.id);
						if (existing) {
							return {
								items: s.items.map((i) =>
									i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i,
								),
							};
						}
						return { items: [...s.items, { ...item, quantity: 1 }] };
					}),
				removeItem: (id) => set((s) => ({ items: s.items.filter((i) => i.id !== id) })),
				updateQuantity: (id, quantity) =>
					set((s) => ({
						items: s.items
							.map((i) => (i.id === id ? { ...i, quantity } : i))
							.filter((i) => i.quantity > 0),
					})),
				clear: () => set({ items: [] }),
				total: () => get().items.reduce((sum, i) => sum + i.price * i.quantity, 0),
				itemCount: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
			}),
			{ name: "cart" },
		),
	),
);
```

**Referência:** [references/tanstack-query.md](references/tanstack-query.md)

---

## 7. Tailwind CSS v4

```css
/* app.css — v4: CSS-first config, no tailwind.config.js */
@import "tailwindcss";

@theme {
	/* Colors in OKLCH */
	--color-surface: oklch(0.98 0 0);
	--color-surface-elevated: oklch(1 0 0);
	--color-primary: oklch(0.65 0.25 264);
	--color-primary-hover: oklch(0.60 0.25 264);
	--color-muted: oklch(0.90 0 0);
	--color-text: oklch(0.15 0 0);
	--color-text-muted: oklch(0.45 0 0);

	/* Typography */
	--font-sans: "Inter Variable", system-ui, sans-serif;
	--font-mono: "JetBrains Mono Variable", monospace;

	/* Spacing */
	--radius-sm: 0.375rem;
	--radius-md: 0.5rem;
	--radius-lg: 0.75rem;
	--radius-xl: 1rem;
}

/* Dark mode */
[data-theme="dark"] {
	--color-surface: oklch(0.13 0 0);
	--color-surface-elevated: oklch(0.18 0 0);
	--color-muted: oklch(0.25 0 0);
	--color-text: oklch(0.93 0 0);
	--color-text-muted: oklch(0.65 0 0);
}
```

**Referência:** [references/tailwind.md](references/tailwind.md)

---

## 8. Testes com Vitest

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UserCard } from "./UserCard";

describe("UserCard", () => {
	const user = userEvent.setup();

	it("renders user name and email", () => {
		render(<UserCard name="Alice" email="alice@test.com" />);
		expect(screen.getByRole("heading", { name: "Alice" })).toBeInTheDocument();
		expect(screen.getByText("alice@test.com")).toBeInTheDocument();
	});

	it("calls onEdit when edit button is clicked", async () => {
		const onEdit = vi.fn();
		render(<UserCard name="Alice" email="alice@test.com" onEdit={onEdit} />);
		await user.click(screen.getByRole("button", { name: /edit/i }));
		expect(onEdit).toHaveBeenCalledOnce();
	});

	it("shows loading state", () => {
		render(<UserCard name="Alice" email="alice@test.com" loading />);
		expect(screen.getByRole("progressbar")).toBeInTheDocument();
		expect(screen.queryByRole("heading")).not.toBeInTheDocument();
	});
});

// vitest.config.ts
export default defineConfig({
	test: {
		environment: "jsdom",
		globals: true,
		setupFiles: "./src/test/setup.ts",
		coverage: {
			provider: "v8",
			reporter: ["text", "lcov"],
			thresholds: { branches: 80, functions: 80, lines: 80 },
		},
	},
});
```

**Referência:** [references/vitest.md](references/vitest.md)

---

## 9. Performance

### Metas de Core Web Vitals

| Métrica | Bom | Precisa Melhorar | Ruim |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | < 2.5s | 2.5–4s | > 4s |
| INP (Interaction to Next Paint) | < 200ms | 200–500ms | > 500ms |
| CLS (Cumulative Layout Shift) | < 0.1 | 0.1–0.25 | > 0.25 |

### Code Splitting

```typescript
// Lazy-load heavy components
const AdminDashboard = lazy(() => import("./AdminDashboard"));
const ReportViewer = lazy(() => import("./ReportViewer"));

function App(): React.JSX.Element {
	return (
		<Suspense fallback={<PageSkeleton />}>
			<Routes>
				<Route path="/admin" element={<AdminDashboard />} />
				<Route path="/reports" element={<ReportViewer />} />
			</Routes>
		</Suspense>
	);
}
```

### Memoização (use com medição)

```typescript
// memo: prevent re-render when props unchanged
const ExpensiveList = memo(function ExpensiveList({ items }: { items: Item[] }) {
	return <ul>{items.map((item) => <ListItem key={item.id} item={item} />)}</ul>;
}, (prev, next) => prev.items === next.items);

// useMemo: cache expensive computation
const sortedItems = useMemo(
	() => [...items].sort((a, b) => a.name.localeCompare(b.name)),
	[items],
);

// useCallback: stable reference for callbacks passed to children
const handleDelete = useCallback(
	(id: string) => dispatch({ type: "DELETE", payload: id }),
	[dispatch],
);
```

**Referência:** [references/performance.md](references/performance.md)

---

## 10. Ferramentas Essenciais

| Categoria | Ferramenta | Propósito | Comando |
|----------|------|---------|---------|
| Lint + Format | **Biome** | Linter e formatter unificado | `biome check --write .` |
| Teste | **Vitest** | Testes de unidade/componente | `vitest run` |
| E2E | **Playwright** | Testes end-to-end | `playwright test` |
| Pacote | **pnpm** | Gerenciamento de dependências | `pnpm install` |
| Build | **Vite** | Ferramenta de build e dev server | `vite dev` |
| Tipos | **TypeScript** | Checagem estática de tipos | `tsc --noEmit` |

### biome.json

```json
{
	"$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
	"organizeImports": { "enabled": true },
	"linter": {
		"enabled": true,
		"rules": {
			"recommended": true,
			"complexity": { "noExcessiveCognitiveComplexity": "warn" },
			"suspicious": { "noExplicitAny": "error" }
		}
	},
	"formatter": {
		"enabled": true,
		"indentStyle": "tab",
		"indentWidth": 1,
		"lineWidth": 100
	},
	"javascript": {
		"formatter": {
			"quoteStyle": "double",
			"semicolons": "always",
			"trailingCommas": "all"
		}
	}
}
```

**Referência:** [references/biome.md](references/biome.md)

---

## Reference Files

- [references/architecture.md](references/architecture.md) — Arquitetura de State Management
- [references/biome.md](references/biome.md) — Biome 2+ - Linter & Formatter
- [references/component-patterns.md](references/component-patterns.md) — Padrões de Componentes React - React 19+
- [references/hooks.md](references/hooks.md) — React Hooks - Custom Hooks & Padrões
- [references/patterns.md](references/patterns.md) — Padrões de TypeScript
- [references/performance.md](references/performance.md) — Performance React - Core Web Vitals & Otimização
- [references/playwright.md](references/playwright.md) — Playwright 1.50+ - Testes E2E
- [references/pnpm.md](references/pnpm.md) — pnpm 10+ - Gerenciador de Pacotes
- [references/server-components.md](references/server-components.md) — React Server Components - Next.js 15+
- [references/strict-config.md](references/strict-config.md) — TypeScript Strict Config - Boas Práticas de tsconfig.json
- [references/tailwind.md](references/tailwind.md) — Tailwind CSS 4+ - Estilização Utility-First
- [references/tanstack-query.md](references/tanstack-query.md) — TanStack Query v5 - Gerenciamento de Server State
- [references/testing-library.md](references/testing-library.md) — Testing Library - Testes React
- [references/type-system.md](references/type-system.md) — Type System Avançado - TypeScript 5.7+
- [references/vite.md](references/vite.md) — Vite 6+ - Build Tool & Dev Server
- [references/vitest.md](references/vitest.md) — Vitest 3+ - Framework de Testes
- [references/zustand.md](references/zustand.md) — Zustand 5+ - State Management