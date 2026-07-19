# React Server Components - Next.js 15+

Mental model, patterns e best practices para Server Components e Server Actions.

---

## Modelo Mental

### Fronteira Server vs Client

```
Server (roda no Node.js)          Client (roda no browser)
┌─────────────────────┐           ┌─────────────────────┐
│  Server Components   │           │  Client Components   │
│  - async/await       │    ──►   │  - useState          │
│  - direct DB access  │  "use    │  - useEffect         │
│  - file system       │  client" │  - event handlers    │
│  - env secrets       │           │  - browser APIs      │
│  - zero bundle size  │           │  - added to bundle   │
└─────────────────────┘           └─────────────────────┘
```

**Padrão no App Router: Server Components.** Adicione `"use client"` apenas quando precisar de interatividade.

### Árvore de Decisão

```
Precisa de useState/useEffect/event handlers?   → "use client"
Precisa de browser APIs (window, localStorage)? → "use client"
Precisa de lib third-party usando hooks?        → "use client"
Apenas renderizando dados?                      → Server Component
Buscando dados de DB/API?                       → Server Component
Usando secrets/env vars?                        → Server Component
Dependências pesadas (markdown, syntax hl)?     → Server Component
```

---

## Server Components

### Busca de Dados

Server Components podem ser async e buscar dados diretamente:

```typescript
// app/users/page.tsx — Server Component (default)
import { db } from "@/lib/db";

async function UsersPage() {
	const users = await db.user.findMany({
		orderBy: { createdAt: "desc" },
		take: 50,
	});

	return (
		<div>
			<h1>Users</h1>
			<ul>
				{users.map((user) => (
					<li key={user.id}>{user.name}</li>
				))}
			</ul>
		</div>
	);
}

export default UsersPage;
```

### Streaming com Suspense

Use Suspense para transmitir partes da página conforme ficam prontas:

```typescript
// app/dashboard/page.tsx
import { Suspense } from "react";

async function DashboardPage() {
	return (
		<div>
			<h1>Dashboard</h1>

			{/* This loads first */}
			<Suspense fallback={<StatsSkeleton />}>
				<Stats />
			</Suspense>

			{/* This can load independently */}
			<Suspense fallback={<ChartSkeleton />}>
				<RevenueChart />
			</Suspense>

			{/* This too */}
			<Suspense fallback={<TableSkeleton />}>
				<RecentOrders />
			</Suspense>
		</div>
	);
}

// Each component fetches its own data
async function Stats() {
	const stats = await fetchStats(); // Can be slow
	return <StatsGrid data={stats} />;
}

async function RevenueChart() {
	const revenue = await fetchRevenue(); // Independent fetch
	return <Chart data={revenue} />;
}
```

---

## Diretiva "use client"

Marca a fronteira onde o código começa a rodar no client:

```typescript
"use client";

import { useState } from "react";

interface CounterProps {
	initialCount: number; // Passed from server as serializable data
}

export function Counter({ initialCount }: CounterProps) {
	const [count, setCount] = useState(initialCount);

	return (
		<div>
			<p>Count: {count}</p>
			<button onClick={() => setCount((c) => c + 1)}>
				Increment
			</button>
		</div>
	);
}
```

### Composição: Server envolvendo Client

```typescript
// app/dashboard/page.tsx — Server Component
import { Counter } from "@/components/Counter"; // Client Component
import { db } from "@/lib/db";

async function DashboardPage() {
	const initialCount = await db.counter.get();

	// Server fetches data, Client handles interactivity
	return (
		<div>
			<h1>Dashboard</h1>
			<Counter initialCount={initialCount} />
		</div>
	);
}
```

### Empurre "use client" para baixo

Minimize client components empurrando a fronteira o mais para baixo possível:

```typescript
// BAD — entire page is client
"use client";
export function ProductPage() { ... }

// GOOD — only the interactive part is client
// app/products/[id]/page.tsx (Server)
async function ProductPage({ params }: { params: { id: string } }) {
	const product = await getProduct(params.id);
	return (
		<div>
			<h1>{product.name}</h1>
			<p>{product.description}</p>
			{/* Only this small part needs client */}
			<AddToCartButton productId={product.id} price={product.price} />
		</div>
	);
}
```

---

## Server Actions

Funções que rodam no servidor, chamáveis a partir de client components:

```typescript
// app/actions/user.ts
"use server";

import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { z } from "zod";

const UpdateUserSchema = z.object({
	name: z.string().min(1).max(100),
	email: z.string().email(),
});

export async function updateUser(
	userId: string,
	formData: FormData,
): Promise<{ success: boolean; error?: string }> {
	const raw = {
		name: formData.get("name"),
		email: formData.get("email"),
	};

	const parsed = UpdateUserSchema.safeParse(raw);
	if (!parsed.success) {
		return { success: false, error: parsed.error.message };
	}

	await db.user.update({
		where: { id: userId },
		data: parsed.data,
	});

	revalidatePath(`/users/${userId}`);
	return { success: true };
}
```

### Usando Server Actions em Formulários

```typescript
"use client";

import { useActionState } from "react";
import { updateUser } from "@/app/actions/user";

function EditUserForm({ userId }: { userId: string }) {
	const [state, formAction, isPending] = useActionState(
		(_prev: unknown, formData: FormData) => updateUser(userId, formData),
		null,
	);

	return (
		<form action={formAction}>
			<input name="name" required />
			<input name="email" type="email" required />
			<button type="submit" disabled={isPending}>
				{isPending ? "Saving..." : "Save"}
			</button>
			{state?.error && <p role="alert">{state.error}</p>}
		</form>
	);
}
```

---

## Cache e Revalidação

### fetch com caching do Next.js

```typescript
// Cached by default (SSG-like)
const data = await fetch("https://api.example.com/data");

// Revalidate every 60 seconds (ISR-like)
const data = await fetch("https://api.example.com/data", {
	next: { revalidate: 60 },
});

// No cache (SSR-like)
const data = await fetch("https://api.example.com/data", {
	cache: "no-store",
});
```

### unstable_cache (para dados non-fetch)

```typescript
import { unstable_cache } from "next/cache";
import { db } from "@/lib/db";

const getCachedUser = unstable_cache(
	async (userId: string) => {
		return db.user.findUnique({ where: { id: userId } });
	},
	["user"], // cache key prefix
	{
		revalidate: 300, // 5 minutes
		tags: ["users"],
	},
);

// Invalidate
import { revalidateTag } from "next/cache";
revalidateTag("users");
```

---

## Padrões

### Pré-carregando Dados

```typescript
// lib/queries.ts
import { cache } from "react";
import { db } from "@/lib/db";

// React cache deduplicates calls within a single render
export const getUser = cache(async (id: string) => {
	return db.user.findUnique({ where: { id } });
});

// Both components call getUser(id) but DB is hit only once
async function UserHeader({ userId }: { userId: string }) {
	const user = await getUser(userId);
	return <h1>{user?.name}</h1>;
}

async function UserSidebar({ userId }: { userId: string }) {
	const user = await getUser(userId);
	return <nav>{user?.role}</nav>;
}
```

### Busca de Dados em Paralelo

```typescript
async function Dashboard() {
	// Parallel — much faster than sequential
	const [stats, orders, revenue] = await Promise.all([
		getStats(),
		getRecentOrders(),
		getRevenue(),
	]);

	return (
		<div>
			<StatsGrid data={stats} />
			<OrdersTable data={orders} />
			<RevenueChart data={revenue} />
		</div>
	);
}
```

---

## Anti-Padrões

### 1. "use client" em tudo
```typescript
// BAD — defeats the purpose of RSC
"use client";
export default function Page() { ... }
```

### 2. Passando props não serializáveis através da fronteira
```typescript
// BAD — functions are not serializable
<ClientComponent onClick={() => doStuff()} />

// GOOD — use Server Actions
<ClientComponent action={serverAction} />
```

### 3. Buscando no client quando o server pode fazer
```typescript
// BAD — unnecessary client fetch
"use client";
function Users() {
	const { data } = useQuery({ queryFn: fetchUsers });
	return <List data={data} />;
}

// GOOD — fetch on server, pass data
async function Users() {
	const users = await db.user.findMany();
	return <List data={users} />;
}
```

---

## Links

- [Next.js — Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)
- [Next.js — Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)
- [React — Server Components RFC](https://react.dev/blog/2023/03/22/react-labs-what-we-have-been-working-on-march-2023)
