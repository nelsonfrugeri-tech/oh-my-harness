# Combinação de fontes — princípios e combinações comprovadas

## Princípios de combinação

### 1. Contraste, não conflito

Boas combinações têm contraste claro em UMA dimensão enquanto compartilham as outras:

```
GOOD: Serif heading + Sans body  (contrast: category)
GOOD: Geometric heading + Humanist body  (contrast: construction)
BAD:  Two similar sans-serifs  (no contrast, looks like a mistake)
BAD:  Decorative heading + decorative body  (competing for attention)
```

### 2. A regra do dois

Use no máximo **duas** famílias de fontes. Se precisar de uma terceira, use a mesma família
em um peso ou estilo diferente.

```css
:root {
  --font-heading: "Instrument Serif", Georgia, serif;
  --font-body: "Inter Variable", system-ui, sans-serif;
  --font-mono: "JetBrains Mono Variable", monospace; /* OK: mono is functional */
}
```

### 3. Combine a x-height

Fontes que combinam bem tendem a ter x-heights parecidas (a altura das letras minúsculas).
Se as x-heights diferem muito, as fontes parecem desalinhadas no mesmo font-size.

### 4. Harmonia histórica

Fontes da mesma época ou tradição de design tendem a combinar naturalmente:
- **Serif humanista + Sans humanista** (ex.: Garamond + Gill Sans)
- **Sans geométrica + Slab geométrica** (ex.: Futura + Rockwell)
- **Serif moderna + Sans grotesk** (ex.: Didot + Helvetica)

---

## 5 combinações comprovadas para 2026

### 1. O padrão SaaS — Inter Variable

```css
:root {
  --font-heading: "Inter Variable", system-ui, sans-serif;
  --font-body: "Inter Variable", system-ui, sans-serif;
}

h1 { font-weight: 700; letter-spacing: -0.025em; }
h2 { font-weight: 600; letter-spacing: -0.02em; }
body { font-weight: 400; }
```

**Vibe:** Limpa, neutra, profissional. Funciona para tudo.
**Usada por:** Linear, Vercel, Raycast, incontáveis produtos SaaS.
**Quando usar:** Quando você quer que o design seja invisível, deixando o conteúdo brilhar.

### 2. A editorial — Instrument Serif + Inter

```css
:root {
  --font-heading: "Instrument Serif", Georgia, serif;
  --font-body: "Inter Variable", system-ui, sans-serif;
}

h1 {
  font-family: var(--font-heading);
  font-style: italic;
  font-size: var(--text-5xl);
  letter-spacing: -0.02em;
}

body {
  font-family: var(--font-body);
}
```

**Vibe:** Elegante, editorial, premium. Personalidade forte.
**Usada por:** Site de marketing do Notion, blogs editoriais, marcas de luxo.
**Quando usar:** Landing pages, blogs, portfólios, quando você quer aconchego.

### 3. A tech moderna — Space Grotesk + DM Sans

```css
:root {
  --font-heading: "Space Grotesk", system-ui, sans-serif;
  --font-body: "DM Sans", system-ui, sans-serif;
}

h1 {
  font-family: var(--font-heading);
  font-weight: 700;
  letter-spacing: -0.03em;
}

body {
  font-family: var(--font-body);
  font-weight: 400;
}
```

**Vibe:** Voltada a tecnologia, geométrica, moderna. Confiante.
**Usada por:** Ferramentas para desenvolvedores, crypto/web3, landing pages de startups.
**Quando usar:** Quando você quer sinalizar inovação e sofisticação técnica.

### 4. A calorosa e amigável — Fraunces + Source Sans 3

```css
:root {
  --font-heading: "Fraunces Variable", Georgia, serif;
  --font-body: "Source Sans 3 Variable", system-ui, sans-serif;
}

h1 {
  font-family: var(--font-heading);
  font-weight: 700;
  font-variation-settings: "SOFT" 100, "WONK" 1;
}

body {
  font-family: var(--font-body);
}
```

**Vibe:** Calorosa, amigável, acessível. Toque humano.
**Usada por:** Plataformas de comunidade, educação, organizações sem fins lucrativos.
**Quando usar:** Quando você quer transmitir acolhimento e confiança.

### 5. A stack de desenvolvedor — Geist Sans + Geist Mono

```css
:root {
  --font-heading: "Geist Sans", system-ui, sans-serif;
  --font-body: "Geist Sans", system-ui, sans-serif;
  --font-mono: "Geist Mono", ui-monospace, monospace;
}

h1 {
  font-weight: 700;
  letter-spacing: -0.025em;
}

code, pre {
  font-family: var(--font-mono);
  font-size: 0.9em;
}
```

**Vibe:** Técnica, precisa, nativa da Vercel. Estética limpa para desenvolvedores.
**Usada por:** Vercel, documentação do Next.js, ferramentas para desenvolvedores.
**Quando usar:** Produtos voltados a desenvolvedores, documentação, blogs técnicos.

---

## Stacks de fontes do sistema — quando fontes customizadas não são necessárias

### A stack do GitHub

```css
--font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
             Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
```

### A stack moderna

```css
--font-body: system-ui, -apple-system, sans-serif;
```

**Quando usar fontes do sistema:**
- Painéis administrativos e ferramentas internas (velocidade > branding)
- Aplicações críticas em performance (zero carregamento de fontes)
- Apps com muito conteúdo, onde a familiaridade importa
- Melhoria progressiva: fonte do sistema como base, customizada como aprimoramento

---

## Otimização de carregamento para combinações

### Estratégia: carregue a primária primeiro

```html
<head>
  <!-- Preload the font used above the fold (heading or body) -->
  <link rel="preload" href="/fonts/InterVariable.woff2" as="font" type="font/woff2" crossorigin />

  <!-- Secondary font loads normally (body text has fallback) -->
  <link rel="preload" href="/fonts/InstrumentSerif-Italic.woff2" as="font" type="font/woff2" crossorigin />
</head>
```

### Métricas de fallback compatíveis

Use `size-adjust` no `@font-face` para minimizar o layout shift na troca:

```css
/* System fallback with adjusted metrics to match Inter */
@font-face {
  font-family: "Inter Fallback";
  src: local("Arial");
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}

:root {
  --font-body: "Inter Variable", "Inter Fallback", system-ui, sans-serif;
}
```

Ferramentas para calcular métricas de fallback:
- https://screenspan.net/fallback
- `next/font` faz isso automaticamente no Next.js

---

## Regras

1. **No máximo duas famílias** — a mono é uma exceção funcional
2. **Título + corpo devem contrastar** — serif/sans, geométrica/humanista ou peso
3. **Faça self-host quando possível** — pacotes fontsource, zero dependência de terceiros
4. **Sempre defina font-display: swap** — o texto nunca deve ficar invisível
5. **Faça preload da fonte above-the-fold** — a fonte visível na primeira renderização
6. **Teste em dispositivos reais** — fontes renderizam de forma diferente em macOS vs Windows vs Android
