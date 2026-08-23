# Sistema de Espaçamento — Grade de 8px e Arquitetura de Tokens

## A Grade de 8px

A grade de 8px é o sistema de espaçamento padrão do mercado. Todos os valores de
espaçamento são múltiplos de 8px (com 4px para microajustes).

### Por Que 8?

- Divide de forma limpa: 8 / 2 = 4, 8 / 4 = 2
- Escala de forma limpa: 8, 16, 24, 32, 40, 48, 56, 64
- Funciona com resoluções de tela comuns (divisível na maioria das grades de pixel)
- Adotada pelo Material Design, Apple HIG e pela maioria dos design systems

---

## Escala de Espaçamento

### Sistema de Tokens Completo

```css
:root {
  /* Base unit: 4px (for micro spacing) */
  --space-0:  0;
  --space-px: 1px;
  --space-0.5: 0.125rem;  /* 2px */
  --space-1:   0.25rem;   /* 4px  — micro */
  --space-1.5: 0.375rem;  /* 6px */
  --space-2:   0.5rem;    /* 8px  — base unit */
  --space-2.5: 0.625rem;  /* 10px */
  --space-3:   0.75rem;   /* 12px */
  --space-3.5: 0.875rem;  /* 14px */
  --space-4:   1rem;      /* 16px — component padding */
  --space-5:   1.25rem;   /* 20px */
  --space-6:   1.5rem;    /* 24px — section gaps */
  --space-7:   1.75rem;   /* 28px */
  --space-8:   2rem;      /* 32px — major spacing */
  --space-9:   2.25rem;   /* 36px */
  --space-10:  2.5rem;    /* 40px */
  --space-11:  2.75rem;   /* 44px */
  --space-12:  3rem;      /* 48px — section padding */
  --space-14:  3.5rem;    /* 56px */
  --space-16:  4rem;      /* 64px — hero spacing */
  --space-20:  5rem;      /* 80px */
  --space-24:  6rem;      /* 96px */
  --space-28:  7rem;      /* 112px */
  --space-32:  8rem;      /* 128px — page sections */
}
```

### Mapeamento do Tailwind

A escala de espaçamento do Tailwind mapeia diretamente para este sistema:

| Tailwind | Valor | Pixels | Caso de Uso |
|----------|-------|--------|----------|
| `p-0.5` | 0.125rem | 2px | Micro: padding de badge |
| `p-1` | 0.25rem | 4px | Micro: espaço entre ícones, espaçamento inline |
| `p-2` | 0.5rem | 8px | Pequeno: padding compacto |
| `p-3` | 0.75rem | 12px | Pequeno: componentes compactos |
| `p-4` | 1rem | 16px | Padrão: padding de componente |
| `p-5` | 1.25rem | 20px | Médio: padding confortável |
| `p-6` | 1.5rem | 24px | Médio: padding de card |
| `p-8` | 2rem | 32px | Grande: padding interno de seção |
| `p-10` | 2.5rem | 40px | Grande: padding generoso |
| `p-12` | 3rem | 48px | XL: padding de seção |
| `p-16` | 4rem | 64px | XXL: padding de hero |
| `p-20` | 5rem | 80px | Espaçamento em nível de página |
| `p-24` | 6rem | 96px | Grandes quebras de seção |

---

## Convenções de Nomenclatura

### Numérica (estilo Tailwind)

```css
--space-1, --space-2, --space-4, --space-8, --space-16
```

**Prós:** Mapeamento direto para valores em pixel, familiar para usuários do Tailwind.
**Contras:** Não é semântico, difícil saber quando usar cada um.

### Tamanhos de Camiseta (T-Shirt Sizing)

```css
--space-xs:  0.25rem;  /* 4px */
--space-sm:  0.5rem;   /* 8px */
--space-md:  1rem;     /* 16px */
--space-lg:  1.5rem;   /* 24px */
--space-xl:  2rem;     /* 32px */
--space-2xl: 3rem;     /* 48px */
--space-3xl: 4rem;     /* 64px */
```

**Prós:** Fácil de lembrar, intenção semântica.
**Contras:** Granularidade limitada, não consegue expressar 12px vs 16px.

### Semântica (Recomendada para design systems)

```css
/* Component-level tokens */
--space-component-padding: var(--space-4);       /* 16px */
--space-component-gap: var(--space-3);           /* 12px */
--space-component-padding-sm: var(--space-2);    /* 8px */

/* Section-level tokens */
--space-section-padding: var(--space-12);        /* 48px */
--space-section-gap: var(--space-8);             /* 32px */

/* Page-level tokens */
--space-page-padding: var(--space-16);           /* 64px */
--space-page-gutter: var(--space-6);             /* 24px */

/* Content spacing */
--space-stack-sm: var(--space-2);                /* 8px — tight content */
--space-stack-md: var(--space-4);                /* 16px — normal content */
--space-stack-lg: var(--space-8);                /* 32px — section breaks */

/* Inline spacing */
--space-inline-sm: var(--space-1);               /* 4px — icon + text */
--space-inline-md: var(--space-2);               /* 8px — button gap */
--space-inline-lg: var(--space-4);               /* 16px — nav items */
```

---

## Ritmo Vertical

Ritmo vertical significa espaçamento consistente entre elementos para criar harmonia visual.

```css
/* Base line height determines the rhythm unit */
:root {
  --rhythm: 1.5rem; /* 24px = base font-size (16px) * line-height (1.5) */
}

/* All vertical spacing should be multiples of the rhythm unit */
h1 { margin-bottom: calc(var(--rhythm) * 1); }   /* 24px */
h2 { margin-bottom: calc(var(--rhythm) * 0.75); } /* 18px */
p  { margin-bottom: var(--rhythm); }               /* 24px */
ul { margin-bottom: var(--rhythm); }               /* 24px */

/* Section breaks: larger multiples */
section + section { margin-top: calc(var(--rhythm) * 3); } /* 72px */
```

### Espaçamento de Prosa com Tailwind

```tsx
<article className="prose prose-lg">
  {/* Tailwind typography plugin handles vertical rhythm automatically */}
  <h1>Title</h1>
  <p>Paragraph with proper spacing...</p>
  <h2>Subtitle</h2>
  <p>Another paragraph...</p>
</article>
```

---

## Espaçamento Consistente de Componentes

### Exemplo de Componente Card

```tsx
function Card({ title, description, children }: CardProps) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      {/* Header: tight spacing between title and description */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      {/* Content: standard gap */}
      <div className="space-y-3">
        {children}
      </div>
    </div>
  );
}
```

### Padrões de Espaçamento

```
COMPONENT ANATOMY:
+--[p-6]------------------------------------------+
|                                                   |
|  [Title]                                         |
|  [mt-1] Description                              |
|                                                   |
|  [mb-4] ─── gap between header and content       |
|                                                   |
|  [Content item 1]                                |
|  [space-y-3] ─── gap between items               |
|  [Content item 2]                                |
|  [space-y-3]                                      |
|  [Content item 3]                                |
|                                                   |
+--------------------------------------------------+
```

---

## Regras

1. **Nunca use valores arbitrários** — sempre use a escala de espaçamento
2. **4px para micro** — padding de ícone, espaços inline, espaçamento de badge
3. **Incrementos de 8px para todo o resto** — 8, 16, 24, 32, 48, 64
4. **Padding > margin** — prefira padding dentro dos contêineres a margin por fora
5. **`gap` > `margin`** — use o gap do CSS para espaçamento consistente em flex/grid
6. **Consistente dentro dos componentes** — um card sempre usa o mesmo padding
7. **Escale para telas maiores** — use espaçamento responsivo com container queries

```css
/* Using gap instead of margin (cleaner, no collapsing issues) */
.stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-4); /* 16px between all children */
}

/* Responsive spacing with container queries */
.section {
  container-type: inline-size;
  padding: var(--space-6); /* 24px mobile */
}

@container (min-width: 768px) {
  .section { padding: var(--space-12); } /* 48px tablet+ */
}

@container (min-width: 1200px) {
  .section { padding: var(--space-16); } /* 64px desktop */
}
```
