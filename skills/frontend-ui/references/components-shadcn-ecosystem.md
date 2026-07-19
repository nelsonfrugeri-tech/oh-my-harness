# Ecossistema shadcn/ui — A Arquitetura Headless + Copy-Paste

## Filosofia

O shadcn/ui NÃO é uma biblioteca de componentes que você instala como dependência.
É uma **coleção de componentes reutilizáveis** que você copia para o seu projeto.

```
Architecture:

  Radix UI Primitives       (behavior + accessibility)
       +
  Tailwind CSS              (styling utilities)
       +
  class-variance-authority  (variant management)
       +
  clsx + tailwind-merge     (class composition)
       =
  shadcn/ui components      (copied into YOUR code)
```

### Por Que Essa Arquitetura Vence

| Biblioteca Tradicional | Abordagem shadcn/ui |
|--------------------|-------------------|
| `npm install component-lib` | `npx shadcn@latest add button` |
| Caixa-preta — não dá para modificar o interior | Código-fonte completo no seu projeto |
| Conflitos de versão, upgrades que quebram | Você é dono do código, atualiza quando quiser |
| Estilos globais, conflitos de CSS | Utilitários do Tailwind, zero CSS global |
| Design opinativo | SEUS design tokens |

---

## Guia de Configuração

### 1. Inicializar em um Projeto Existente

```bash
npx shadcn@latest init
```

Isso cria:
- `components/ui/` — onde os componentes ficam
- `lib/utils.ts` — o utilitário `cn()`
- Atualiza `tailwind.config` (ou `app.css` no Tailwind v4)

### 2. O Utilitário cn()

```ts
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

**Por que clsx E twMerge juntos?**
- `clsx` cuida das classes condicionais: `clsx("base", isActive && "active")`
- `twMerge` resolve conflitos do Tailwind: `twMerge("px-2 px-4")` → `"px-4"`
- Juntos: composição de classes segura e livre de conflitos

### 3. Adicionar Componentes

```bash
# Add individual components
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add input
npx shadcn@latest add label
npx shadcn@latest add select
npx shadcn@latest add sheet
npx shadcn@latest add tabs
npx shadcn@latest add toast
npx shadcn@latest add tooltip
```

Cada comando copia o código-fonte do componente para `components/ui/`.

---

## Padrões de Customização

### Modificando Variantes

O shadcn/ui usa `class-variance-authority` (cva) para variantes:

```tsx
// components/ui/button.tsx (YOUR code, fully customizable)
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  // Base styles
  "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-border bg-transparent hover:bg-accent",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // ADD YOUR OWN variants
        brand: "bg-gradient-to-r from-primary to-secondary text-white hover:opacity-90",
        glass: "bg-white/10 backdrop-blur-lg border border-white/20 text-white hover:bg-white/20",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-lg px-8",
        xl: "h-14 rounded-xl px-10 text-base",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### Estendendo com Composição

```tsx
// Compose shadcn primitives into domain-specific components
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface LoadingButtonProps extends React.ComponentProps<typeof Button> {
  loading?: boolean;
}

export function LoadingButton({ loading, children, disabled, ...props }: LoadingButtonProps) {
  return (
    <Button disabled={loading || disabled} {...props}>
      {loading && <Loader2 className="mr-2 size-4 animate-spin" />}
      {children}
    </Button>
  );
}
```

---

## Sistema de Temas de Cores

O shadcn/ui usa CSS custom properties para temas:

```css
/* Tailwind v4: @theme directive */
@import "tailwindcss";

@theme {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.15 0 0);
  --color-card: oklch(1 0 0);
  --color-card-foreground: oklch(0.15 0 0);
  --color-primary: oklch(0.55 0.25 264);
  --color-primary-foreground: oklch(0.98 0.01 264);
  --color-secondary: oklch(0.94 0.005 264);
  --color-secondary-foreground: oklch(0.15 0 0);
  --color-muted: oklch(0.94 0.005 264);
  --color-muted-foreground: oklch(0.45 0.02 264);
  --color-accent: oklch(0.94 0.005 264);
  --color-accent-foreground: oklch(0.15 0 0);
  --color-destructive: oklch(0.55 0.22 25);
  --color-destructive-foreground: oklch(0.98 0.01 25);
  --color-border: oklch(0.87 0 0);
  --color-input: oklch(0.87 0 0);
  --color-ring: oklch(0.55 0.25 264);
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
}
```

---

## Camadas de Animação

Construa sobre o shadcn/ui com bibliotecas de componentes animados:

### Aceternity UI

Seções hero, efeitos de landing page, animações complexas:

```tsx
// Aceternity-style spotlight card
function SpotlightCard({ children }: { children: React.ReactNode }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  return (
    <div
      className="group relative rounded-xl border bg-surface p-8 overflow-hidden"
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      }}
    >
      {/* Spotlight effect */}
      <div
        className="pointer-events-none absolute -inset-px opacity-0
          transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(400px circle at ${position.x}px ${position.y}px,
            oklch(0.65 0.25 264 / 0.1), transparent 40%)`,
        }}
      />
      {children}
    </div>
  );
}
```

### Magic UI

Microinterações, botões, cards com animação sutil:

```tsx
// Shimmer button
function ShimmerButton({ children }: { children: React.ReactNode }) {
  return (
    <button className="group relative rounded-lg bg-primary px-6 py-3
      text-primary-foreground overflow-hidden">
      <span className="relative z-10">{children}</span>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite]
        bg-gradient-to-r from-transparent via-white/20 to-transparent
        group-hover:animate-[shimmer_1.5s_infinite]" />
    </button>
  );
}
```

---

## Quando Usar o Mantine

O shadcn/ui é ideal para design systems personalizados. Mas o **Mantine** é melhor quando:

| Cenário | Usar shadcn/ui | Usar Mantine |
|----------|-------------|-------------|
| Design de marca personalizado | Sim | Talvez |
| Velocidade de desenvolvimento | Moderada | Rápida |
| Componentes de dados ricos (tabelas, gráficos) | Limitado | Extenso |
| Design system completo | Construa o seu | Nativo |
| Controle sobre cada detalhe | Controle total | A biblioteca controla |
| Dashboards administrativos | Funciona | Mais adequado |

O Mantine oferece: DatePicker, RichTextEditor, Notifications, Spotlight,
Charts e muitos componentes que o shadcn/ui não tem.

---

## Plugins Essenciais

| Pacote | Finalidade |
|---------|---------|
| `@radix-ui/react-*` | Primitivos acessíveis de base |
| `class-variance-authority` | Gerenciamento de variantes para componentes |
| `clsx` | Junção condicional de classes |
| `tailwind-merge` | Resolução de conflitos de classes do Tailwind |
| `cmdk` | Paleta de comandos |
| `sonner` | Notificações toast |
| `@tanstack/react-table` | Tabelas de dados |
| `@tanstack/react-virtual` | Virtualização de listas |
| `recharts` | Gráficos |
| `date-fns` | Utilitários de data |
| `react-day-picker` | Seletor de data |
| `vaul` | Componente drawer |

---

## Regras

1. **Copie, não instale** — os componentes do shadcn/ui vivem no SEU projeto
2. **cn() em todo lugar** — use para toda composição de classes
3. **Customize via tokens** — altere as CSS custom properties, não o código do componente
4. **Adicione variantes, não faça fork** — estenda as variantes do cva em vez de duplicar
5. **Radix para comportamento** — deixe o Radix cuidar de a11y, teclado, foco
6. **Tailwind para estilização** — classes utilitárias, sem arquivos CSS personalizados
