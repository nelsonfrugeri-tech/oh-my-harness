# React Performance - Core Web Vitals & Otimização

Guia completo de performance para React 19+ e Next.js 15+.

---

## Core Web Vitals

| Métrica | Alvo | O que mede |
|--------|--------|------------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Quando o maior elemento de conteúdo se torna visível |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Estabilidade visual — o quanto o conteúdo se desloca durante o carregamento |
| **INP** (Interaction to Next Paint) | < 200ms | Responsividade — atraso entre a interação e a atualização visual |

---

## React.memo

Previne re-renders quando as props não mudaram:

```typescript
import { memo } from "react";

// GOOD use case: list item rendered many times
const ProductCard = memo(function ProductCard({
	product,
}: {
	product: Product;
}) {
	return (
		<div className="rounded border p-4">
			<img src={product.image} alt={product.name} />
			<h3>{product.name}</h3>
			<p>${product.price}</p>
		</div>
	);
});

// With custom comparison
const DataGrid = memo(
	function DataGrid({ rows, columns }: DataGridProps) {
		// expensive render
		return <table>{/* ... */}</table>;
	},
	(prev, next) =>
		prev.rows.length === next.rows.length &&
		prev.columns === next.columns,
);
```

---

## useMemo e useCallback

### Quando realmente usar useMemo

```typescript
// GOOD — expensive computation
function Analytics({ data }: { data: DataPoint[] }) {
	const processed = useMemo(() => {
		return data
			.filter((d) => d.value > 0)
			.map((d) => ({ ...d, normalized: d.value / maxValue }))
			.sort((a, b) => b.normalized - a.normalized);
	}, [data]);

	return <Chart data={processed} />;
}

// BAD — trivial computation (overhead > savings)
function Greeting({ name }: { name: string }) {
	const message = useMemo(() => `Hello, ${name}!`, [name]);
	return <p>{message}</p>;
}
```

### Quando realmente usar useCallback

```typescript
// GOOD — callback passed to memoized child
function Parent() {
	const [items, setItems] = useState<Item[]>([]);

	const handleDelete = useCallback((id: string) => {
		setItems((prev) => prev.filter((item) => item.id !== id));
	}, []);

	return <MemoizedList items={items} onDelete={handleDelete} />;
}

// BAD — callback not passed to memoized child
function Form() {
	const handleSubmit = useCallback(() => {
		// doesn't matter — child isn't memoized
	}, []);

	return <button onClick={handleSubmit}>Submit</button>;
}
```

### Regra prática
- **useMemo**: Apenas para computações custosas ou igualdade referencial necessária pelas deps
- **useCallback**: Apenas ao passar para filhos envolvidos em `memo` ou como dependência

---

## Code Splitting

### React.lazy

```typescript
import { lazy, Suspense } from "react";

// Split by route
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Settings = lazy(() => import("./pages/Settings"));
const AdminPanel = lazy(() => import("./pages/AdminPanel"));

function App() {
	return (
		<Suspense fallback={<PageSkeleton />}>
			<Routes>
				<Route path="/dashboard" element={<Dashboard />} />
				<Route path="/settings" element={<Settings />} />
				<Route path="/admin" element={<AdminPanel />} />
			</Routes>
		</Suspense>
	);
}

// Split by feature
const HeavyEditor = lazy(() => import("./components/HeavyEditor"));

function DocumentPage() {
	const [editing, setEditing] = useState(false);

	return (
		<div>
			<button onClick={() => setEditing(true)}>Edit</button>
			{editing && (
				<Suspense fallback={<EditorSkeleton />}>
					<HeavyEditor />
				</Suspense>
			)}
		</div>
	);
}
```

### Named exports com lazy

```typescript
// utils/lazyNamed.ts
export function lazyNamed<T extends Record<string, React.ComponentType>>(
	factory: () => Promise<T>,
	name: keyof T,
) {
	return lazy(() =>
		factory().then((module) => ({ default: module[name] as React.ComponentType })),
	);
}

// Usage
const UserAvatar = lazyNamed(
	() => import("./components/User"),
	"UserAvatar",
);
```

---

## Otimização de Imagens

### Next.js Image

```typescript
import Image from "next/image";

function Hero() {
	return (
		<Image
			src="/hero.jpg"
			alt="Hero banner"
			width={1200}
			height={630}
			priority // LCP image — preload
			sizes="100vw"
			quality={85}
		/>
	);
}

function ProductImage({ src, name }: { src: string; name: string }) {
	return (
		<Image
			src={src}
			alt={name}
			width={400}
			height={400}
			sizes="(max-width: 768px) 100vw, 400px"
			loading="lazy" // Below the fold
			placeholder="blur"
			blurDataURL="data:image/jpeg;base64,..."
		/>
	);
}
```

### Regras
- **Imagens LCP**: Sempre adicione `priority`
- **Abaixo da dobra**: Use `loading="lazy"` (padrão)
- **Sempre defina sizes**: Previne layout shift
- **Use sizes responsivos**: `(max-width: 768px) 100vw, 50vw`

---

## Otimização de Fontes

```typescript
// app/layout.tsx
import { Inter } from "next/font/google";

const inter = Inter({
	subsets: ["latin"],
	display: "swap", // Prevent FOIT
	variable: "--font-inter",
});

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en" className={inter.variable}>
			<body>{children}</body>
		</html>
	);
}
```

---

## Análise de Bundle

### Vite

```typescript
// vite.config.ts
import { visualizer } from "rollup-plugin-visualizer";

export default defineConfig({
	plugins: [
		visualizer({
			open: true,
			gzipSize: true,
		}),
	],
	build: {
		rollupOptions: {
			output: {
				manualChunks: {
					vendor: ["react", "react-dom"],
					router: ["react-router-dom"],
					query: ["@tanstack/react-query"],
				},
			},
		},
	},
});
```

### Next.js

```bash
ANALYZE=true pnpm build
```

```typescript
// next.config.ts
import bundleAnalyzer from "@next/bundle-analyzer";

const withBundleAnalyzer = bundleAnalyzer({
	enabled: process.env.ANALYZE === "true",
});

export default withBundleAnalyzer({
	// config
});
```

---

## Virtualização

Para listas longas, renderize apenas os itens visíveis:

```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }: { items: Item[] }) {
	const parentRef = useRef<HTMLDivElement>(null);

	const virtualizer = useVirtualizer({
		count: items.length,
		getScrollElement: () => parentRef.current,
		estimateSize: () => 50, // estimated row height
		overscan: 5,
	});

	return (
		<div ref={parentRef} style={{ height: "400px", overflow: "auto" }}>
			<div
				style={{
					height: `${virtualizer.getTotalSize()}px`,
					position: "relative",
				}}
			>
				{virtualizer.getVirtualItems().map((virtualRow) => (
					<div
						key={virtualRow.key}
						style={{
							position: "absolute",
							top: 0,
							left: 0,
							width: "100%",
							height: `${virtualRow.size}px`,
							transform: `translateY(${virtualRow.start}px)`,
						}}
					>
						{items[virtualRow.index]!.name}
					</div>
				))}
			</div>
		</div>
	);
}
```

---

## React DevTools Profiler

### Como fazer profiling

1. Abra a aba React DevTools > Profiler
2. Clique em Record, interaja com a app, clique em Stop
3. Analise:
   - **Flamegraph**: Mostra a árvore de render dos componentes com timing
   - **Ranked**: Componentes ordenados por tempo de render
   - **Why did this render?**: Habilite nas configurações

### Achados comuns
- Componente re-renderiza com as mesmas props → adicione `memo`
- Re-render do pai em cascata para os filhos → mova o estado para baixo
- Mudança de Context re-renderiza tudo → divida os contexts
- Render custoso a cada frame → adicione `useMemo`

---

## Checklist de Performance

- [ ] Imagem LCP tem o atributo `priority`
- [ ] Imagens têm `width`/`height` ou `sizes` explícitos
- [ ] Fontes usam `display: "swap"`
- [ ] Componentes pesados são code-split com `lazy`
- [ ] Listas longas usam virtualização
- [ ] `React.memo` em componentes custosos e re-renderizados com frequência
- [ ] Bundle analisado — sem dependências grandes desnecessárias
- [ ] Server Components usados onde possível (zero JS no cliente)
- [ ] Data fetching paralelo com `Promise.all`
- [ ] Sem layout shift (CLS) por conteúdo dinâmico

---

## Links

- [web.dev — Core Web Vitals](https://web.dev/articles/vitals)
- [React — Optimizing Performance](https://react.dev/learn/render-and-commit)
- [Next.js — Image Optimization](https://nextjs.org/docs/app/building-your-application/optimizing/images)
- [TanStack Virtual](https://tanstack.com/virtual/latest)
