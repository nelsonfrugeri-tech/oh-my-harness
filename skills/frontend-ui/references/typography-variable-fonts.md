# Variable fonts — eixos, performance e animação

## O que são variable fonts?

Uma variable font é um único arquivo de fonte que contém toda a gama de variações
(peso, largura, inclinação etc.) em vez de arquivos separados para cada estilo.

```
Traditional:                    Variable:
Inter-Regular.woff2    (30KB)   InterVariable.woff2  (310KB)
Inter-Medium.woff2     (30KB)   = ALL weights + widths in ONE file
Inter-SemiBold.woff2   (30KB)
Inter-Bold.woff2       (30KB)
Inter-ExtraBold.woff2  (30KB)
...10 files = 300KB+           Actually SMALLER for 3+ styles
```

### Benefícios de performance

- **Menos requisições HTTP** — 1 arquivo vs 10+
- **Tamanho total menor** — ao usar 3+ pesos (muito comum)
- **Animações suaves** — interpola entre qualquer valor de peso
- **Sem FOUT entre pesos** — sem flash ao trocar de estilo

---

## Eixos de variação

### Eixos padrão (registrados)

| Eixo | Tag | Intervalo | Descrição |
|------|-----|-------|-------------|
| Weight | `wght` | 100-900 | de Thin a Black |
| Width | `wdth` | 75-125 | de Condensed a Expanded |
| Slant | `slnt` | -90-90 | Ângulo oblíquo |
| Italic | `ital` | 0-1 | de Roman a Italic |
| Optical Size | `opsz` | 8-144 | Otimizado para tamanho de exibição |

### Usando eixos

```css
@font-face {
  font-family: "Inter Variable";
  src: url("/fonts/InterVariable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap;
}

/* High-level properties (preferred when available) */
.heading {
  font-family: "Inter Variable", system-ui, sans-serif;
  font-weight: 700;
}

/* Low-level axis control */
.custom {
  font-variation-settings:
    "wght" 650,    /* between SemiBold and Bold */
    "wdth" 90;     /* slightly condensed */
}

/* Optical size: browser sets automatically based on font-size */
.auto-optical {
  font-size: 48px;
  font-optical-sizing: auto; /* browser selects optimal opsz */
}
```

---

## Animação com variable fonts

Variable fonts permitem transições suaves de peso/largura:

```css
/* Smooth weight transition on hover */
.nav-link {
  font-family: "Inter Variable", system-ui, sans-serif;
  font-variation-settings: "wght" 400;
  transition: font-variation-settings 200ms ease-out;
}

.nav-link:hover {
  font-variation-settings: "wght" 600;
}

.nav-link[aria-current="page"] {
  font-variation-settings: "wght" 700;
}
```

```css
/* Breathing animation for loading state */
@keyframes breathe {
  0%, 100% { font-variation-settings: "wght" 300; }
  50% { font-variation-settings: "wght" 700; }
}

.loading-text {
  animation: breathe 2s ease-in-out infinite;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .loading-text {
    animation: none;
    font-variation-settings: "wght" 400;
  }
}
```

---

## Variable fonts recomendadas (2026)

### Sans-serif

| Fonte | Eixos | Vibe | Origem |
|------|------|------|--------|
| **Inter Variable** | wght 100-900 | Limpa, neutra, SaaS | Google Fonts / fontsource |
| **Geist Sans** | wght 100-900 | Moderna, para devs | Vercel / fontsource |
| **DM Sans** | wght 100-1000, ital, opsz | Geométrica, amigável | Google Fonts |
| **Space Grotesk** | wght 300-700 | Tech, moderna | Google Fonts |
| **Plus Jakarta Sans** | wght 200-800 | Geométrica, calorosa | Google Fonts |
| **Outfit** | wght 100-900 | Geométrica, limpa | Google Fonts |

### Serif

| Fonte | Eixos | Vibe | Origem |
|------|------|------|--------|
| **Instrument Serif** | (apenas estática) | Editorial, elegante | Google Fonts |
| **Fraunces** | wght, opsz, SOFT, WONK | Calorosa, old-style | Google Fonts |
| **Lora** | wght 400-700, ital | Clássica, legível | Google Fonts |
| **Source Serif 4** | wght 200-900, opsz, ital | Versátil, profissional | Google Fonts |

### Monospace

| Fonte | Eixos | Vibe | Origem |
|------|------|------|--------|
| **JetBrains Mono** | wght 100-800 | Focada em devs | fontsource |
| **Geist Mono** | wght 100-900 | Moderna, Vercel | fontsource |
| **Fira Code** | wght 300-700 | Ligaturas, popular | Google Fonts |

---

## Self-hosting com fontsource

O fontsource fornece pacotes npm para self-host de fontes com carregamento otimizado:

```bash
npm install @fontsource-variable/inter
npm install @fontsource-variable/jetbrains-mono
```

```tsx
// app/layout.tsx or main entry
import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
```

```css
@theme {
  --font-sans: "Inter Variable", system-ui, sans-serif;
  --font-mono: "JetBrains Mono Variable", monospace;
}
```

Benefícios em relação ao CDN do Google Fonts:
- Sem requisições de terceiros (privacidade, GDPR)
- Sem latência de lookup de DNS
- Controle total sobre font-display
- Funciona offline

---

## Estratégias de font-display

| Estratégia | Comportamento | Quando usar |
|----------|----------|-------------|
| `swap` | Mostra o fallback imediatamente, troca ao carregar | Texto de corpo (escolha padrão) |
| `optional` | Mostra o fallback, troca só se carregar muito rápido | Páginas críticas em performance |
| `block` | Esconde o texto brevemente, depois mostra com a fonte | Apenas ícones e texto decorativo |
| `fallback` | Bloqueio breve, depois fallback, troca se for rápido | Meio-termo entre swap/optional |

```css
@font-face {
  font-family: "Inter Variable";
  src: url("/fonts/InterVariable.woff2") format("woff2");
  font-weight: 100 900;
  font-display: swap; /* Recommended default */
}
```

---

## Otimização de carregamento

```html
<!-- Preload the primary font (in <head>) -->
<link
  rel="preload"
  href="/fonts/InterVariable.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>

<!-- Preconnect if using Google Fonts (not recommended, prefer self-hosting) -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```

### Subsetting

Para fontes com grandes conjuntos de caracteres, faça subset para reduzir o tamanho do arquivo:

```bash
# Using pyftsubset (fonttools)
pyftsubset InterVariable.woff2 \
  --output-file=InterVariable-latin.woff2 \
  --flavor=woff2 \
  --layout-features="kern,liga,calt" \
  --unicodes="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
```

Os pacotes fontsource já vêm com subset por padrão.

---

## Stacks de fontes do sistema

Quando fontes customizadas não são necessárias, as stacks do sistema são instantâneas:

```css
/* System sans-serif stack */
--font-system-sans:
  system-ui,
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  Roboto,
  "Helvetica Neue",
  Arial,
  sans-serif;

/* System monospace stack */
--font-system-mono:
  ui-monospace,
  SFMono-Regular,
  "SF Mono",
  Menlo,
  Consolas,
  "Liberation Mono",
  monospace;
```

Use fontes do sistema para: painéis administrativos, ferramentas internas, apps críticos em performance.
Use fontes customizadas para: identidade de marca, marketing, editorial, sensação premium.
