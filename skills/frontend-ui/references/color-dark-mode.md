# Dark Mode — Abordagem Design-First

## Filosofia: Dark-First

Projete para dark mode PRIMEIRO e só então adapte para o modo claro. Por quê?
- Dark mode é mais difícil de acertar (contraste, legibilidade, cansaço visual)
- Se fica ótimo no escuro, adaptar para o claro é simples
- A maioria das ferramentas de desenvolvimento, apps criativos e SaaS modernos tem dark mode como padrão
- OKLCH torna a adaptação trivial via inversão do eixo L

---

## Inversão de Lightness em OKLCH

A técnica central: no dark mode, inverta o eixo L (lightness) dos seus tokens.

```
Light mode: L = 0.95 (light bg)    -> Dark mode: L = 0.13 (dark bg)
Light mode: L = 0.15 (dark text)   -> Dark mode: L = 0.93 (light text)
Light mode: L = 0.65 (primary)     -> Dark mode: L = 0.70 (slightly brighter primary)
```

### Implementação

```css
:root {
  /* Light mode (default) */
  --color-bg: oklch(0.99 0 0);
  --color-bg-subtle: oklch(0.96 0 0);
  --color-surface: oklch(1 0 0);
  --color-text: oklch(0.15 0 0);
  --color-text-secondary: oklch(0.40 0 0);
  --color-border: oklch(0.87 0 0);

  /* Primary stays similar but may brighten slightly */
  --color-primary: oklch(0.55 0.25 264);
}

[data-theme="dark"] {
  /* Invert L axis */
  --color-bg: oklch(0.13 0 0);
  --color-bg-subtle: oklch(0.16 0 0);
  --color-surface: oklch(0.18 0 0);
  --color-text: oklch(0.93 0 0);
  --color-text-secondary: oklch(0.65 0 0);
  --color-border: oklch(0.25 0 0);

  /* Primary: bump L up for visibility on dark bg */
  --color-primary: oklch(0.70 0.22 264);
}
```

---

## Variante dark: do Tailwind

O Tailwind oferece a variante `dark:`. Combine-a com CSS custom properties:

```css
/* app.css */
@import "tailwindcss";

@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));
```

```tsx
// Component usage
<div className="bg-white dark:bg-gray-950">
  <h1 className="text-gray-900 dark:text-gray-50">Title</h1>
  <p className="text-gray-600 dark:text-gray-400">Description</p>
</div>

// Better approach: use semantic tokens so you don't need dark: at all
<div className="bg-background text-foreground">
  <h1 className="text-foreground">Title</h1>
  <p className="text-muted-foreground">Description</p>
</div>
```

### Implementação do Theme Toggle

```tsx
"use client";

import { useEffect, useState } from "react";
import { Moon, Sun, Monitor } from "lucide-react";

type Theme = "light" | "dark" | "system";

function useTheme() {
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    const stored = localStorage.getItem("theme") as Theme | null;
    if (stored) setTheme(stored);
  }, []);

  useEffect(() => {
    const root = document.documentElement;

    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      root.dataset.theme = mq.matches ? "dark" : "light";

      const handler = (e: MediaQueryListEvent) => {
        root.dataset.theme = e.matches ? "dark" : "light";
      };
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }

    root.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  return { theme, setTheme };
}

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const icons: Record<Theme, typeof Sun> = {
    light: Sun,
    dark: Moon,
    system: Monitor,
  };

  const next: Record<Theme, Theme> = {
    light: "dark",
    dark: "system",
    system: "light",
  };

  const Icon = icons[theme];

  return (
    <button
      onClick={() => setTheme(next[theme])}
      className="rounded-lg p-2 hover:bg-surface-hover"
      aria-label={`Current theme: ${theme}. Click to change.`}
    >
      <Icon className="size-5" />
    </button>
  );
}
```

---

## Erros Comuns em Dark Mode

### 1. Fundo Preto Puro

```css
/* BAD: pure black is harsh and unnatural */
[data-theme="dark"] {
  --color-bg: oklch(0 0 0); /* #000000 */
}

/* GOOD: very dark gray is easier on the eyes */
[data-theme="dark"] {
  --color-bg: oklch(0.13 0 0); /* approximately #1a1a1a */
}
```

### 2. Contraste Excessivo

```css
/* BAD: white text on black is fatiguing */
[data-theme="dark"] {
  --color-text: oklch(1 0 0);   /* pure white */
  --color-bg: oklch(0.07 0 0);  /* near black */
}

/* GOOD: slightly muted text reduces eye strain */
[data-theme="dark"] {
  --color-text: oklch(0.93 0 0); /* soft white */
  --color-bg: oklch(0.13 0 0);   /* dark gray */
}
```

### 3. Esquecer da Elevação

No modo claro, a elevação é indicada por sombras. No dark mode, sombras ficam invisíveis
contra fundos escuros. Use superfícies mais claras no lugar:

```css
/* Light mode: elevation via shadow */
.card {
  background: oklch(1 0 0);
  box-shadow: 0 4px 6px oklch(0 0 0 / 0.07);
}

/* Dark mode: elevation via lighter surface */
[data-theme="dark"] .card {
  background: oklch(0.20 0 0); /* lighter than bg */
  box-shadow: 0 4px 6px oklch(0 0 0 / 0.3); /* subtle depth */
}
```

### 4. Fundos Coloridos Saturados Demais

```css
/* BAD: saturated colors are blinding on dark backgrounds */
[data-theme="dark"] {
  --color-primary-bg: oklch(0.65 0.25 264);
}

/* GOOD: desaturate and darken for dark mode */
[data-theme="dark"] {
  --color-primary-bg: oklch(0.20 0.05 264); /* low L, low C */
}
```

### 5. Não Testar Imagens e Ilustrações

Imagens projetadas para o modo claro podem destoar no escuro. Soluções:
- Adicionar bordas sutis ao redor das imagens
- Reduzir o brilho das ilustrações com um filtro CSS
- Fornecer variantes em dark mode para ilustrações importantes

```css
[data-theme="dark"] img:not([data-theme-aware]) {
  filter: brightness(0.9) contrast(1.05);
}
```

---

## Contraste no Dark Mode

### APCA (Advanced Perceptual Contrast Algorithm)

O APCA está substituindo as razões de contraste do WCAG 2. Principais diferenças:
- Sensível à polaridade: claro-sobre-escuro tem limiares diferentes de escuro-sobre-claro
- Mais preciso para a percepção no mundo real
- Mínimos recomendados:
  - Texto de corpo: Lc 60 (claro-sobre-escuro) ou Lc -60 (escuro-sobre-claro)
  - Texto grande: Lc 45
  - UI não textual: Lc 30

```css
/* Test your dark mode tokens */
/* --color-text (L=0.93) on --color-bg (L=0.13) */
/* Contrast: roughly Lc 80 — excellent */

/* --color-text-secondary (L=0.65) on --color-bg (L=0.13) */
/* Contrast: roughly Lc 50 — good for secondary text */

/* --color-text-tertiary (L=0.45) on --color-bg (L=0.13) */
/* Contrast: roughly Lc 30 — minimum for non-essential text */
```

---

## Prevenção de Flash (SSR)

Evite o "flash de tema errado" no carregamento da página:

```html
<!-- In <head>, BEFORE any CSS loads -->
<script>
  (function() {
    const theme = localStorage.getItem("theme");
    if (theme === "dark" || (!theme && matchMedia("(prefers-color-scheme:dark)").matches)) {
      document.documentElement.dataset.theme = "dark";
    } else {
      document.documentElement.dataset.theme = "light";
    }
  })();
</script>
```

Para Next.js, use a biblioteca `next-themes`, que cuida disso automaticamente.

---

## Configuração Completa de Tokens Light/Dark

Consulte [semantic-tokens.md](semantic-tokens.md) para o sistema completo de tokens em dois níveis,
com definições tanto para o modo claro quanto para o dark mode.
