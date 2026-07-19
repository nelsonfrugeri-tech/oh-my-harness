# Arquitetura de Gerenciamento de Estado

Decision tree para escolher a ferramenta certa para cada tipo de estado.

---

## Categorias de Estado

| Categoria | Descrição | Ferramenta | Exemplos |
|----------|-------------|------|----------|
| **Estado do servidor** | Dados de APIs/DB | TanStack Query | Usuários, posts, produtos |
| **Estado do cliente** | Estado de UI de toda a app | Zustand | Tema, sidebar, notificações |
| **Estado local** | Específico do componente | useState | Inputs de formulário, toggles, modais |
| **Estado de formulário** | Lógica de formulário complexa | React Hook Form | Formulários multi-step, validação |
| **Estado da URL** | Navegação/filtros | URL params | Busca, paginação, filtros |

---

## Árvore de Decisão

```
Os dados vêm de uma API/banco de dados?
├── SIM → TanStack Query
│   (cache, refetch em segundo plano, estados de carregamento/erro)
│
└── NÃO → É compartilhado entre muitos componentes?
    ├── SIM → Zustand
    │   (estado de UI global, preferências do usuário, carrinho de compras)
    │
    └── NÃO → É lógica de formulário complexa?
        ├── SIM → React Hook Form
        │   (validação, multi-step, campos dinâmicos)
        │
        └── NÃO → Está na URL?
            ├── SIM → URL search params
            │   (filtros, paginação, query de busca)
            │
            └── NÃO → useState / useReducer
                (toggle local, modal aberto, valor do input)
```

---

## Estado do Servidor (TanStack Query)

**Use para:** Qualquer dado que vem de uma fonte externa (API, banco de dados).

```typescript
// GOOD — server data managed by TanStack Query
function UsersList() {
	const { data: users, isLoading } = useQuery({
		queryKey: ["users"],
		queryFn: fetchUsers,
	});

	if (isLoading) return <Skeleton />;
	return <List items={users} />;
}
```

**Recursos que você ganha de graça:**
- Refetch automático em segundo plano
- Cache com stale time configurável
- Estados de carregamento e erro
- Atualizações otimistas
- Scroll infinito/paginação
- Prefetching
- Refetch ao focar a janela
- Suporte offline

---

## Estado do Cliente (Zustand)

**Use para:** Estado de UI global que não vem de um servidor.

```typescript
// GOOD — UI state in Zustand
const useUIStore = create<UIStore>((set) => ({
	sidebarOpen: true,
	theme: "light" as "light" | "dark",
	notifications: [] as Notification[],
	toggleSidebar: () =>
		set((s) => ({ sidebarOpen: !s.sidebarOpen })),
	setTheme: (theme) => set({ theme }),
	addNotification: (n) =>
		set((s) => ({ notifications: [...s.notifications, n] })),
}));
```

---

## Estado Local (useState)

**Use para:** Estado que pertence a um único componente e seus filhos.

```typescript
// GOOD — local state
function Modal() {
	const [isOpen, setIsOpen] = useState(false);

	return (
		<>
			<button onClick={() => setIsOpen(true)}>Open</button>
			{isOpen && <Dialog onClose={() => setIsOpen(false)} />}
		</>
	);
}

// GOOD — derived local state
function FilteredList({ items }: { items: Item[] }) {
	const [search, setSearch] = useState("");

	const filtered = items.filter((item) =>
		item.name.toLowerCase().includes(search.toLowerCase()),
	);

	return (
		<div>
			<input value={search} onChange={(e) => setSearch(e.target.value)} />
			<List items={filtered} />
		</div>
	);
}
```

---

## Estado de Formulário (React Hook Form)

**Use para:** Formulários complexos com validação, campos dinâmicos, multi-step.

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
	name: z.string().min(1, "Required"),
	email: z.string().email("Invalid email"),
	role: z.enum(["admin", "user"]),
});

type FormValues = z.infer<typeof schema>;

function CreateUserForm() {
	const {
		register,
		handleSubmit,
		formState: { errors, isSubmitting },
	} = useForm<FormValues>({
		resolver: zodResolver(schema),
		defaultValues: { role: "user" },
	});

	const onSubmit = async (data: FormValues) => {
		await createUser(data);
	};

	return (
		<form onSubmit={handleSubmit(onSubmit)}>
			<input {...register("name")} />
			{errors.name && <span>{errors.name.message}</span>}

			<input {...register("email")} type="email" />
			{errors.email && <span>{errors.email.message}</span>}

			<select {...register("role")}>
				<option value="user">User</option>
				<option value="admin">Admin</option>
			</select>

			<button type="submit" disabled={isSubmitting}>
				Create
			</button>
		</form>
	);
}
```

---

## Estado da URL

**Use para:** Filtros, queries de busca, paginação — qualquer coisa que deveria ser compartilhável via URL.

```typescript
// Next.js App Router
import { useSearchParams, useRouter, usePathname } from "next/navigation";

function ProductFilters() {
	const searchParams = useSearchParams();
	const router = useRouter();
	const pathname = usePathname();

	const category = searchParams.get("category") ?? "all";
	const sort = searchParams.get("sort") ?? "name";

	function updateParams(updates: Record<string, string>) {
		const params = new URLSearchParams(searchParams.toString());
		for (const [key, value] of Object.entries(updates)) {
			params.set(key, value);
		}
		router.push(`${pathname}?${params.toString()}`);
	}

	return (
		<div>
			<select
				value={category}
				onChange={(e) => updateParams({ category: e.target.value })}
			>
				<option value="all">All</option>
				<option value="electronics">Electronics</option>
			</select>
		</div>
	);
}
```

---

## Anti-Padrões

### 1. Estado do Servidor no Zustand

```typescript
// BAD — managing server data in Zustand
const useUserStore = create((set) => ({
	users: [],
	isLoading: false,
	fetchUsers: async () => {
		set({ isLoading: true });
		const users = await fetch("/api/users").then((r) => r.json());
		set({ users, isLoading: false });
	},
}));

// GOOD — use TanStack Query for server data
function useUsers() {
	return useQuery({
		queryKey: ["users"],
		queryFn: () => fetch("/api/users").then((r) => r.json()),
	});
}
```

### 2. Estado Global para Questões Locais

```typescript
// BAD — modal state in global store
const useUIStore = create((set) => ({
	isDeleteModalOpen: false,
	isEditModalOpen: false,
	isConfirmModalOpen: false,
	// 20 more modal states...
}));

// GOOD — local state for local concerns
function UserRow({ user }: { user: User }) {
	const [showDeleteModal, setShowDeleteModal] = useState(false);
	return (
		<>
			<button onClick={() => setShowDeleteModal(true)}>Delete</button>
			{showDeleteModal && <DeleteModal user={user} />}
		</>
	);
}
```

### 3. Prop Drilling vs Context vs Zustand

```typescript
// If prop drilling is 2-3 levels — just pass props
// If prop drilling is 4+ levels — consider Zustand or Context
// If data changes frequently — Zustand (Context re-renders all consumers)
// If data rarely changes — Context is fine (theme, locale, auth)
```

### 4. Estado Derivado Armazenado Separadamente

```typescript
// BAD — storing derived state
const useStore = create((set) => ({
	items: [],
	filteredItems: [], // This is derived!
	filterText: "",
	setFilter: (text) =>
		set((s) => ({
			filterText: text,
			filteredItems: s.items.filter((i) => i.name.includes(text)),
		})),
}));

// GOOD — compute derived state
const useStore = create((set) => ({
	items: [],
	filterText: "",
	setFilter: (text) => set({ filterText: text }),
}));

// In component
function FilteredList() {
	const items = useStore((s) => s.items);
	const filterText = useStore((s) => s.filterText);
	const filtered = useMemo(
		() => items.filter((i) => i.name.includes(filterText)),
		[items, filterText],
	);
}
```

---

## Tabela de Resumo

| Pergunta | Resposta |
|----------|--------|
| Dados de API? | TanStack Query |
| Estado de UI global? | Zustand |
| Toggle/input local? | useState |
| Formulário complexo? | React Hook Form + Zod |
| Compartilhável via URL? | URL search params |
| Contexto que muda raramente? | React Context |

---

## Links

- [TanStack Query vs Zustand](https://tkdodo.eu/blog/react-query-and-zustand)
- [Zustand Documentation](https://zustand.docs.pmnd.rs/)
- [React Hook Form](https://react-hook-form.com/)
