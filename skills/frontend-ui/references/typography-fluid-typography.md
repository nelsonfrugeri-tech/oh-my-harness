# Tipografia Fluida — clamp() em detalhes

## Visão geral

A tipografia fluida usa o `clamp()` do CSS para escalar suavemente o tamanho da fonte entre um mínimo
e um máximo, com base na largura da viewport. Sem necessidade de breakpoints.

```css
/* clamp(minimum, preferred, maximum) */
font-size: clamp(1rem, 0.925rem + 0.375vw, 1.125rem);
```

Esta única linha substitui:
```css
/* Old approach: multiple breakpoints */
font-size: 1rem;
@media (min-width: 768px) { font-size: 1.05rem; }
@media (min-width: 1024px) { font-size: 1.125rem; }
```

---

## A matemática

### Fórmula

```
preferred = min + (max - min) * (100vw - minViewport) / (maxViewport - minViewport)
```

Simplified for `rem` + `vw`:
```
Given: min = 1rem, max = 1.5rem, viewport range 320px-1440px
Rate = (1.5 - 1) / (1440 - 320) * 100 = 0.0446vw
Offset = 1 - 0.0446 * (320 / 16) = 0.1071rem

Result: clamp(1rem, 0.107rem + 0.0446vw, 1.5rem)
```

Na prática, **use uma calculadora** (veja Ferramentas abaixo).

---

## Escala tipográfica completa

Uma escala tipográfica fluida pronta para produção usando rem:

```css
:root {
  /* Body sizes */
  --text-xs:   clamp(0.694rem, 0.662rem + 0.16vw, 0.8rem);
  --text-sm:   clamp(0.833rem, 0.787rem + 0.23vw, 0.96rem);
  --text-base: clamp(1rem, 0.935rem + 0.33vw, 1.2rem);
  --text-lg:   clamp(1.2rem, 1.111rem + 0.44vw, 1.44rem);

  /* Heading sizes */
  --text-xl:   clamp(1.44rem,  1.318rem + 0.61vw, 1.728rem);
  --text-2xl:  clamp(1.728rem, 1.562rem + 0.83vw, 2.074rem);
  --text-3xl:  clamp(2.074rem, 1.852rem + 1.11vw, 2.488rem);
  --text-4xl:  clamp(2.488rem, 2.196rem + 1.46vw, 2.986rem);
  --text-5xl:  clamp(2.986rem, 2.605rem + 1.91vw, 3.583rem);

  /* Line heights (tighter for headings) */
  --leading-tight:  1.15;
  --leading-snug:   1.3;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
}

/* Usage */
h1 {
  font-size: var(--text-5xl);
  line-height: var(--leading-tight);
  letter-spacing: -0.025em;
}

h2 {
  font-size: var(--text-4xl);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
}

h3 {
  font-size: var(--text-3xl);
  line-height: var(--leading-snug);
}

h4 {
  font-size: var(--text-2xl);
  line-height: var(--leading-snug);
}

h5 {
  font-size: var(--text-xl);
  line-height: var(--leading-snug);
}

h6 {
  font-size: var(--text-lg);
  line-height: var(--leading-normal);
}

body {
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

small, .text-sm {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

.text-xs {
  font-size: var(--text-xs);
  line-height: var(--leading-normal);
}
```

---

## Proporções de escala

Escolha uma proporção de escala que combine com a personalidade do seu design:

| Proporção | Nome | Personalidade | Melhor para |
|-------|------|-------------|----------|
| 1.125 | Major Second | Sutil, densa | Dashboards de dados, admin |
| 1.200 | Minor Third | Equilibrada | SaaS, apps |
| 1.250 | Major Third | Hierarquia clara | Marketing, blogs |
| 1.333 | Perfect Fourth | Hierarquia forte | Landing pages |
| 1.414 | Augmented Fourth | Dramática | Editorial, revistas |
| 1.500 | Perfect Fifth | Muito dramática | Seções hero |

A escala acima usa **Minor Third (1.200)** — boa para a maioria dos apps.

---

## Por que rem, não px

```css
/* BAD: ignores user's font-size preference */
font-size: clamp(16px, 2vw, 20px);

/* GOOD: respects user's font-size preference */
font-size: clamp(1rem, 0.925rem + 0.375vw, 1.25rem);
```

Usuários que configuram o navegador com fonte base de 20px terão texto proporcionalmente maior
com rem. Com px, a preferência deles é ignorada — uma falha de acessibilidade.

---

## Integração com Tailwind v4

```css
@import "tailwindcss";

@theme {
  --font-size-xs:   clamp(0.694rem, 0.662rem + 0.16vw, 0.8rem);
  --font-size-sm:   clamp(0.833rem, 0.787rem + 0.23vw, 0.96rem);
  --font-size-base: clamp(1rem, 0.935rem + 0.33vw, 1.2rem);
  --font-size-lg:   clamp(1.2rem, 1.111rem + 0.44vw, 1.44rem);
  --font-size-xl:   clamp(1.44rem, 1.318rem + 0.61vw, 1.728rem);
  --font-size-2xl:  clamp(1.728rem, 1.562rem + 0.83vw, 2.074rem);
  --font-size-3xl:  clamp(2.074rem, 1.852rem + 1.11vw, 2.488rem);
  --font-size-4xl:  clamp(2.488rem, 2.196rem + 1.46vw, 2.986rem);
  --font-size-5xl:  clamp(2.986rem, 2.605rem + 1.91vw, 3.583rem);
}
```

Uso: `<h1 className="text-5xl">` usa automaticamente o valor fluido.

---

## Comprimento de linha responsivo (measure)

A tipografia fluida deve ser combinada com uma medida de leitura confortável:

```css
.prose {
  max-width: clamp(45ch, 50vw, 75ch);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}
```

Comprimento de linha ideal: **45-75 caracteres** para texto de corpo.

---

## Ferramentas e recursos

| Ferramenta | URL | Descrição |
|------|-----|-------------|
| **Fluid Type Scale** | https://www.fluid-type-scale.com | Gera escalas fluidas completas |
| **Utopia** | https://utopia.fyi/type/calculator | Calculadora avançada de tipografia fluida + espaçamento |
| **Type Scale** | https://typescale.com | Escala tipográfica visual com proporções |
| **Modern Fluid Typography** | https://modern-fluid-typography.vercel.app | Gerador interativo de clamp() |
| **Every Layout** | https://every-layout.dev | Padrões de layout + tipografia |

---

## Erros comuns

1. **Usar px em clamp()** — quebra as preferências de tamanho de fonte do usuário
2. **Intervalo muito amplo** — `clamp(0.5rem, ..., 4rem)` cria saltos de tamanho bruscos
3. **Esquecer o line-height** — títulos precisam de line-height mais apertado que o corpo
4. **Sem letter-spacing** — títulos grandes precisam de letter-spacing negativo (-0.02em a -0.04em)
5. **Ignorar o ritmo vertical** — o espaçamento entre elementos deve seguir a escala tipográfica
