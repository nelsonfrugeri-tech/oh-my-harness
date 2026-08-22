---
version: 1.0.0
name: frontend-ui
description: |
  Base de conhecimento de design de UI/UX frontend (2026). Cobre a teoria de cores OKLCH (uniformidade
  perceptual, tokens semânticos, design de dark mode), tipografia fluida com clamp(), fontes variáveis,
  layout moderno em CSS (container queries, subgrid, :has()), grade de espaçamento de 8px, biblioteca de
  animação Motion (spring physics, prefers-reduced-motion), padrões de UX (skeleton screens, optimistic UI,
  command palette), acessibilidade (WCAG 2.2 AA, contraste APCA, focus-visible, HTML semântico), stack de
  design system (primitivos Radix UI + Tailwind CSS v4 + shadcn/ui), tendências visuais de 2026 (bento
  grids, glassmorphism, textura de grão) e otimização de ícones/imagens.
  Use quando: (1) Projetar interfaces, (2) Escolher paletas de cores e tipografia, (3) Implementar
  animações, (4) Garantir acessibilidade WCAG 2.2, (5) Construir componentes de design system.
  Gatilhos: /frontend-ui, /ui, /ux, design, color, typography, animation, accessibility, OKLCH.
type: knowledge
---

# Frontend UI — Base de Conhecimento

## Propósito

Esta skill é a base de conhecimento para design de UI/UX frontend (2026).
Ela cobre design visual, layout, motion, acessibilidade e a stack de design system.

**O que esta skill contém:**
- Teoria de cores OKLCH (uniformidade perceptual, tokens semânticos, dark mode)
- Tipografia fluida com `clamp()` e fontes variáveis
- Layout moderno em CSS (container queries, subgrid, `:has()`)
- Grade de espaçamento de 8px
- Animações Motion (biblioteca Motion, árvore de decisão, reduced motion)
- Padrões de UX (skeleton screens, optimistic UI, command palette)
- Acessibilidade (WCAG 2.2, APCA, focus-visible, HTML semântico)
- Stack de design system (Radix UI + Tailwind v4 + shadcn/ui)
- Tendências visuais de 2026 (bento grids, glassmorphism, grão)
- Ícones e otimização de imagens

---

## Princípios Fundamentais

1. **Tokens, não valores mágicos** — toda cor, espaçamento e font-size vem de um design token
2. **OKLCH é o padrão** — perceptualmente uniforme, gamut P3, integrado ao Tailwind v4
3. **Primitivos headless primeiro** — Radix UI para comportamento + acessibilidade, Tailwind para estilização
4. **Motion com propósito** — animações comunicam estado, não são decoração
5. **Acessibilidade é inegociável** — WCAG 2.2 AA no mínimo, teste com teclado e leitor de tela

---

## 1. Teoria de Cores OKLCH

### Por que OKLCH em vez de HSL

| Aspecto | HSL | OKLCH |
|--------|-----|-------|
| Uniformidade perceptual | Não — o mesmo L parece diferente entre matizes | Sim — L=0.5 sempre aparenta o mesmo brilho |
| Gamut de cores | Apenas sRGB | P3 (mais vívido em telas modernas) |
| Dark mode | Ajustar cada cor manualmente | Ajustar o eixo L de forma sistemática |
| Tailwind v4 | Legado | Suporte nativo |

### Sistema de Tokens (Dois Níveis)

```css
/* Tier 1: Primitives (the full palette) */
:root {
  --blue-50:  oklch(0.97 0.01 264);
  --blue-100: oklch(0.93 0.03 264);
  --blue-200: oklch(0.87 0.07 264);
  --blue-500: oklch(0.65 0.25 264);
  --blue-700: oklch(0.45 0.20 264);
  --blue-900: oklch(0.30 0.12 264);

  --neutral-50:  oklch(0.98 0 0);
  --neutral-100: oklch(0.95 0 0);
  --neutral-900: oklch(0.13 0 0);
}

/* Tier 2: Semantic tokens (what the primitives mean) */
:root {
  --color-bg:           var(--neutral-50);
  --color-bg-elevated:  oklch(1 0 0);
  --color-surface:      oklch(0.97 0 0);
  --color-muted:        var(--neutral-100);
  --color-text:         var(--neutral-900);
  --color-text-muted:   oklch(0.45 0 0);
  --color-primary:      var(--blue-500);
  --color-primary-hover: var(--blue-700);
  --color-border:       oklch(0.88 0 0);
}

/* Dark mode: flip L axis */
[data-theme="dark"] {
  --color-bg:           var(--neutral-900);
  --color-bg-elevated:  oklch(0.18 0 0);
  --color-surface:      oklch(0.15 0 0);
  --color-muted:        oklch(0.22 0 0);
  --color-text:         oklch(0.93 0 0);
  --color-text-muted:   oklch(0.65 0 0);
  --color-border:       oklch(0.28 0 0);
}
```

### Config CSS-First do Tailwind v4

```css
@import "tailwindcss";

@theme {
  --color-primary:        oklch(0.65 0.25 264);
  --color-primary-hover:  oklch(0.60 0.25 264);
  --color-surface:        oklch(0.98 0 0);
  --font-sans: "Inter Variable", system-ui, sans-serif;
  --font-mono: "JetBrains Mono Variable", monospace;
  --radius-lg:  0.75rem;
  --radius-xl:  1rem;
}
```

**Referência:** [references/color-oklch.md](references/color-oklch.md)

---

## 2. Tipografia

### Escala Tipográfica Fluida (clamp)

```css
:root {
  /* clamp(min, preferred, max) — no breakpoints needed */
  --text-xs:   clamp(0.75rem,  0.70rem + 0.25vw, 0.8125rem);
  --text-sm:   clamp(0.875rem, 0.82rem + 0.28vw, 0.9375rem);
  --text-base: clamp(1rem,     0.93rem + 0.38vw, 1.125rem);
  --text-lg:   clamp(1.125rem, 1.02rem + 0.53vw, 1.3125rem);
  --text-xl:   clamp(1.25rem,  1.10rem + 0.75vw, 1.5625rem);
  --text-2xl:  clamp(1.5rem,   1.28rem + 1.10vw, 2rem);
  --text-3xl:  clamp(1.875rem, 1.50rem + 1.88vw, 2.75rem);
  --text-4xl:  clamp(2.25rem,  1.75rem + 2.50vw, 3.5rem);
}

/* Apply */
h1 { font-size: var(--text-4xl); font-weight: 700; line-height: 1.1; }
h2 { font-size: var(--text-3xl); font-weight: 600; line-height: 1.2; }
h3 { font-size: var(--text-2xl); font-weight: 600; line-height: 1.3; }
p  { font-size: var(--text-base); line-height: 1.6; }
```

### Fontes Variáveis

```css
@font-face {
  font-family: "Inter Variable";
  src: url("/fonts/InterVariable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}

/* Animate weight on hover (no layout shift) */
.nav-link {
  font-variation-settings: "wght" 400;
  transition: font-variation-settings 200ms ease;
}
.nav-link:hover { font-variation-settings: "wght" 600; }
```

### Combinações de Fontes (2026)

| Título | Corpo | Caráter |
|---------|------|-----------|
| Inter Variable | Inter Variable | Limpo, neutro, SaaS |
| Instrument Serif | Inter Variable | Editorial, elegante |
| Space Grotesk | DM Sans | Tech, moderno |
| Geist Sans | Geist Mono | Ferramentas de desenvolvimento |
| Fraunces Variable | Source Sans 3 | Acolhedor, amigável |

**Referência:** [references/typography-fluid-typography.md](references/typography-fluid-typography.md)

---

## 3. Layout Moderno em CSS

### Container Queries

```css
/* Components respond to their container, not the viewport */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1.5rem;
  }
}

@container card (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
}
```

### Subgrid (alinhado entre irmãos)

```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.product-card {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 3; /* image | title | price — all aligned across cards */
}
```

### Seletor :has()

```css
/* Parent selector — layout depends on children */
.card:has(img)       { grid-template-rows: 200px 1fr; }
.card:not(:has(img)) { grid-template-rows: 1fr; }

/* Form state styling */
.form-group:has(input:invalid) {
  --border-color: oklch(0.65 0.25 25);
}
```

### Grade de Espaçamento de 8px

```
4px   micro (gap inside icon, inline padding)
8px   xs (between inline elements)
12px  sm (tight component padding)
16px  md (standard component padding)
24px  lg (section gaps, card padding)
32px  xl (major spacing)
48px  2xl (section padding)
64px  3xl (hero sections)
```

**Referência:** [references/layout-modern-css-layout.md](references/layout-modern-css-layout.md)

---

## 4. Motion

### Árvore de Decisão de Bibliotecas

```
Need animation?
  |
  +-- Simple state (show/hide, color, opacity) → CSS transition
  |
  +-- Keyframe sequence (loading spinner)      → CSS @keyframes
  |
  +-- Layout reorder / enter-exit / gesture    → Motion (Framer Motion)
  |
  +-- Complex timeline / scroll-driven         → GSAP
  |
  +-- Page transition                          → View Transitions API
```

### Biblioteca Motion (Spring Physics)

```tsx
import { motion, AnimatePresence } from "motion/react";

// Layout animation: smooth list reorder
function AnimatedList({ items }: { items: Item[] }): React.JSX.Element {
  return (
    <AnimatePresence initial={false}>
      {items.map((item) => (
        <motion.li
          key={item.id}
          layout
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
          className="overflow-hidden"
        >
          {item.content}
        </motion.li>
      ))}
    </AnimatePresence>
  );
}

// Entrance animation
function FadeIn({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 30, delay: 0.1 }}
    >
      {children}
    </motion.div>
  );
}
```

### Reduced Motion (Inegociável)

```css
/* CSS: disable all animations for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

```tsx
// React hook
function useReducedMotion(): boolean {
  const [prefersReduced, setPrefersReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = (e: MediaQueryListEvent): void => setPrefersReduced(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return prefersReduced;
}
```

**Referência:** [references/motion-animation-guide.md](references/motion-animation-guide.md)

---

## 5. Padrões de UX

### Skeleton Screens

```tsx
function CardSkeleton(): React.JSX.Element {
  return (
    <div className="animate-pulse rounded-xl border bg-surface p-4 space-y-3">
      <div className="h-48 rounded-lg bg-muted" />
      <div className="h-4 w-3/4 rounded bg-muted" />
      <div className="h-4 w-1/2 rounded bg-muted" />
    </div>
  );
}

// Shimmer variant
function Shimmer({ className }: { className?: string }): React.JSX.Element {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded bg-muted",
        "after:absolute after:inset-0 after:-translate-x-full",
        "after:animate-[shimmer_1.5s_infinite]",
        "after:bg-gradient-to-r after:from-transparent after:via-white/20 after:to-transparent",
        className,
      )}
    />
  );
}
```

### Optimistic UI

```tsx
function useLikePost(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (liked: boolean) => toggleLike(postId, liked),
    onMutate: async (liked) => {
      await queryClient.cancelQueries({ queryKey: ["post", postId] });
      const previous = queryClient.getQueryData(["post", postId]);
      queryClient.setQueryData(["post", postId], (old: Post) => ({
        ...old,
        liked,
        likeCount: old.likeCount + (liked ? 1 : -1),
      }));
      return { previous };
    },
    onError: (_err, _liked, context) => {
      queryClient.setQueryData(["post", postId], context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["post", postId] });
    },
  });
}
```

**Referência:** [references/ux-patterns-interaction-patterns.md](references/ux-patterns-interaction-patterns.md)

---

## 6. Acessibilidade (WCAG 2.2)

### Principais Critérios da WCAG 2.2

| Critério | Requisito | Implementação |
|-----------|-------------|----------------|
| 1.4.3 Contraste (Mín.) | Razão de contraste do texto | APCA Lc >= 60 para texto de corpo |
| 2.4.7 Foco Visível | Indicador de foco visível | `:focus-visible` com outline de 2px |
| 2.4.11 Foco Não Obscurecido | Foco não escondido | `scroll-margin`, gestão de z-index |
| 2.5.8 Tamanho do Alvo (Mín.) | Alvo de toque >= 24×24px | `min-w-6 min-h-6` |
| 4.1.2 Nome, Papel, Valor | Marcação semântica | HTML semântico + ARIA apenas quando necessário |

### Gestão de Foco

```css
/* Global focus style — keyboard navigation only */
:focus-visible {
  outline: 2px solid oklch(0.65 0.25 264);
  outline-offset: 2px;
  border-radius: var(--radius-sm, 0.25rem);
}

/* Remove default ring for mouse/touch */
:focus:not(:focus-visible) {
  outline: none;
}

/* Ensure sticky headers don't obscure focused elements */
:target,
:focus-visible {
  scroll-margin-top: 5rem;
}
```

### HTML Semântico Primeiro

```tsx
// GOOD: semantic HTML — built-in behavior and accessibility
<button type="submit" onClick={handleSubmit}>Submit</button>
<a href="/about">About</a>
<nav aria-label="Main navigation">...</nav>

// BAD: div soup — requires ARIA to compensate
<div role="button" tabIndex={0} onClick={handleSubmit}>Submit</div>

// Rule: First rule of ARIA — don't use ARIA if native HTML does the job

// When ARIA IS needed (custom widget)
<div
  role="slider"
  aria-valuemin={0}
  aria-valuemax={100}
  aria-valuenow={value}
  aria-label="Volume"
  tabIndex={0}
  onKeyDown={handleKeyDown}
/>
```

### Testes de Acessibilidade

```typescript
// Playwright with axe-core
import AxeBuilder from "@axe-core/playwright";

test("homepage has no accessibility violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

**Referência:** [references/accessibility-wcag-2-2.md](references/accessibility-wcag-2-2.md)

---

## 7. Stack de Design System

### Stack Recomendada

```
Radix UI (behavior + accessibility primitives)
  + Tailwind CSS v4 (utility-first styling, OKLCH, CSS-first config)
  + shadcn/ui (copy-paste components — you own the code)
  = Your Design System
```

### Configuração do shadcn/ui

```bash
npx shadcn@latest init
npx shadcn@latest add button card dialog dropdown-menu input label
```

### Utilitário cn() (Essencial)

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// Usage
<button className={cn(
  "rounded-lg px-4 py-2 font-medium transition-colors",
  "bg-primary text-white hover:bg-primary-hover",
  isLoading && "cursor-not-allowed opacity-50",
  className,
)}>
```

### Radix UI Dialog

```tsx
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

interface ModalProps {
  trigger: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

function Modal({ trigger, title, children }: ModalProps): React.JSX.Element {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg rounded-xl bg-surface p-6 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
          {children}
          <Dialog.Close asChild>
            <button className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100" aria-label="Close">
              <X className="size-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

**Referência:** [references/components-shadcn-ecosystem.md](references/components-shadcn-ecosystem.md)

---

## 8. Tendências Visuais de 2026

### Bento Grid

```css
.bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(3, 200px);
  gap: 1rem;
}
.bento-featured { grid-column: span 2; grid-row: span 2; }
.bento-item {
  border-radius: var(--radius-xl);
  background: oklch(0.97 0.005 264);
  padding: 1.5rem;
  overflow: hidden;
}
```

### Glassmorphism (usado com bom senso)

```css
.glass {
  background: oklch(1 0 0 / 0.65);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid oklch(1 0 0 / 0.2);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.08);
}

[data-theme="dark"] .glass {
  background: oklch(0.2 0 0 / 0.5);
  border-color: oklch(1 0 0 / 0.08);
}
```

### Ícones e Imagens

```tsx
// Icons: Lucide React (consistent, tree-shakeable)
import { Search, ChevronRight, X } from "lucide-react";
<Search className="size-4 shrink-0" strokeWidth={1.5} />

// Images: AVIF > WebP > JPEG
<picture>
  <source srcSet="/hero.avif" type="image/avif" />
  <source srcSet="/hero.webp" type="image/webp" />
  <img
    src="/hero.jpg"
    alt="Descriptive alt text — describe what the image shows"
    width={1200}
    height={630}
    loading="lazy"
    decoding="async"
    className="rounded-xl object-cover"
  />
</picture>
```

**Referência:** [references/visual-trends-2026.md](references/visual-trends-2026.md)

---

## Reference Files

- [references/accessibility-wcag-2-2.md](references/accessibility-wcag-2-2.md) — WCAG 2.2 — Guia de Implementação Frontend
- [references/color-dark-mode.md](references/color-dark-mode.md) — Dark Mode — Abordagem Design-First
- [references/color-oklch.md](references/color-oklch.md) — Espaço de Cores OKLCH — Em Profundidade
- [references/color-semantic-tokens.md](references/color-semantic-tokens.md) — Sistema de Tokens Semânticos — Arquitetura em Dois Níveis
- [references/components-icons-images.md](references/components-icons-images.md) — Ícones e Imagens — Lucide, Otimização e Boas Práticas
- [references/components-shadcn-ecosystem.md](references/components-shadcn-ecosystem.md) — Ecossistema shadcn/ui — A Arquitetura Headless + Copy-Paste
- [references/layout-modern-css-layout.md](references/layout-modern-css-layout.md) — Layout Moderno em CSS — Container Queries, Subgrid, :has() e Mais
- [references/layout-spacing-system.md](references/layout-spacing-system.md) — Sistema de Espaçamento — Grade de 8px e Arquitetura de Tokens
- [references/motion-animation-guide.md](references/motion-animation-guide.md) — Guia de Animação — Árvore de Decisão, Performance e Implementação
- [references/typography-fluid-typography.md](references/typography-fluid-typography.md) — Tipografia Fluida — clamp() em Profundidade
- [references/typography-font-pairing.md](references/typography-font-pairing.md) — Combinação de Fontes — Princípios e Combinações Comprovadas
- [references/typography-variable-fonts.md](references/typography-variable-fonts.md) — Fontes Variáveis — Eixos, Performance e Animação
- [references/ux-patterns-interaction-patterns.md](references/ux-patterns-interaction-patterns.md) — Padrões de Interação — Command Palettes, Toasts, Modais e Mais
- [references/ux-patterns-loading-states.md](references/ux-patterns-loading-states.md) — Estados de Carregamento — Skeletons, Optimistic UI e Streaming
- [references/visual-trends-2026.md](references/visual-trends-2026.md) — Tendências Visuais de 2026 — Bento, Glass, Grão e Além