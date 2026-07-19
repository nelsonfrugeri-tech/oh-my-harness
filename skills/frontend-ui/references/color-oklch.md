# Espaço de Cores OKLCH — Em Profundidade

## O que é OKLCH?

OKLCH (Oklab Lightness Chroma Hue) é um espaço de cores perceptualmente uniforme projetado por
Bjorn Ottosson em 2020. Ele corrige os problemas fundamentais do HSL/HSV e foi adotado
como o modelo de cores padrão no Tailwind CSS v4.

### Sintaxe

```css
/* oklch(Lightness Chroma Hue / Alpha) */
color: oklch(0.65 0.25 264);
color: oklch(0.65 0.25 264 / 0.5); /* 50% opacity */
```

### Parâmetros

| Parâmetro | Intervalo | Descrição |
|-----------|-------|-------------|
| **L** (Lightness) | 0 - 1 | 0 = preto, 1 = branco. Perceptualmente linear. |
| **C** (Chroma) | 0 - ~0.4 | 0 = cinza, maior = mais vívido. O máximo depende do gamut. |
| **H** (Hue) | 0 - 360 | Ângulo da roda de cores. 0=rosa, 90=amarelo, 180=ciano, 264=azul |

---

## Por que OKLCH é Melhor que HSL

### O Problema da Uniformidade Perceptual

O HSL afirma que `lightness: 50%` significa "brilho médio" para qualquer matiz. Isso é mentira.

```css
/* HSL: these are both "50% lightness" but look completely different */
.yellow { color: hsl(60, 100%, 50%); }  /* Extremely bright */
.blue   { color: hsl(240, 100%, 50%); } /* Very dark */

/* OKLCH: L=0.65 actually looks the same brightness regardless of hue */
.yellow { color: oklch(0.65 0.25 90); }  /* Medium brightness */
.blue   { color: oklch(0.65 0.25 264); } /* Same medium brightness */
```

Isso importa enormemente para:
- **Gerar paletas**: as escalas de tonalidade são visualmente consistentes
- **Dark mode**: a inversão de lightness realmente funciona
- **Acessibilidade**: os cálculos de contraste fazem sentido

### Suporte ao Gamut P3

OKLCH consegue representar cores fora do sRGB, no gamut P3 mais amplo que as telas
Apple modernas, os celulares Android mais recentes e muitos monitores suportam.

```css
/* sRGB max blue — this is the most vivid blue HSL can do */
.srgb-blue { color: hsl(240, 100%, 50%); }

/* P3 blue — 25% more vivid, visible on modern displays */
.p3-blue { color: oklch(0.45 0.31 264); }

/* Graceful fallback for older displays */
.vivid-blue {
  color: oklch(0.65 0.25 264); /* sRGB-safe */
}

@media (color-gamut: p3) {
  .vivid-blue {
    color: oklch(0.65 0.31 264); /* P3 vivid */
  }
}
```

### Tabela Comparativa

| Recurso | RGB/Hex | HSL | OKLCH |
|---------|---------|-----|-------|
| Legível por humanos | Não | Mais ou menos | Sim |
| Perceptualmente uniforme | Não | Não | Sim |
| Gamut P3 | Não | Não | Sim |
| Amigável a dark mode | Não | Não | Sim |
| Geração de paletas | Difícil | Inconsistente | Consistente |
| Suporte de navegadores (2026) | Total | Total | Total (96%+) |
| Nativo no Tailwind v4 | Não | Legado | Padrão |

---

## Gerando Paletas com OKLCH

### O Método Simples: Fixe C e H, Varie L

Para criar uma escala de tonalidade (50-950), mantenha Chroma e Hue constantes e varie a Lightness:

```css
:root {
  /* Blue palette — H=264, C=0.15 (moderate) */
  --blue-50:  oklch(0.97 0.01 264);
  --blue-100: oklch(0.93 0.03 264);
  --blue-200: oklch(0.87 0.07 264);
  --blue-300: oklch(0.78 0.12 264);
  --blue-400: oklch(0.70 0.18 264);
  --blue-500: oklch(0.65 0.22 264);  /* primary */
  --blue-600: oklch(0.55 0.22 264);
  --blue-700: oklch(0.47 0.19 264);
  --blue-800: oklch(0.38 0.15 264);
  --blue-900: oklch(0.30 0.12 264);
  --blue-950: oklch(0.22 0.08 264);
}
```

### Avançado: Curva de Chroma

Na prática, o chroma mais vívido acontece na lightness intermediária. Para uma
paleta de aparência natural, aumente o chroma no meio e diminua nos extremos:

```css
:root {
  /* Green palette with chroma curve */
  --green-50:  oklch(0.97 0.02 150);  /* low C: almost white */
  --green-100: oklch(0.93 0.05 150);
  --green-200: oklch(0.87 0.10 150);
  --green-300: oklch(0.78 0.16 150);
  --green-400: oklch(0.70 0.20 150);
  --green-500: oklch(0.65 0.22 150);  /* peak chroma */
  --green-600: oklch(0.55 0.20 150);
  --green-700: oklch(0.47 0.17 150);
  --green-800: oklch(0.38 0.13 150);
  --green-900: oklch(0.30 0.10 150);
  --green-950: oklch(0.22 0.06 150);  /* low C: almost black */
}
```

### Template Completo de Paleta de Marca

```css
:root {
  /* Brand primary: pick your hue */
  --hue-primary: 264;   /* blue */
  --hue-success: 150;   /* green */
  --hue-warning: 75;    /* amber */
  --hue-danger: 25;     /* red */

  /* Neutral: zero chroma */
  --gray-50:  oklch(0.98 0 0);
  --gray-100: oklch(0.94 0 0);
  --gray-200: oklch(0.87 0 0);
  --gray-300: oklch(0.78 0 0);
  --gray-400: oklch(0.65 0 0);
  --gray-500: oklch(0.55 0 0);
  --gray-600: oklch(0.45 0 0);
  --gray-700: oklch(0.37 0 0);
  --gray-800: oklch(0.27 0 0);
  --gray-900: oklch(0.20 0 0);
  --gray-950: oklch(0.13 0 0);
}
```

---

## Integração OKLCH no Tailwind v4

O Tailwind v4 usa OKLCH internamente para sua paleta padrão. Sua diretiva `@theme`
deve usar OKLCH para manter a consistência:

```css
@import "tailwindcss";

@theme {
  /* These are OKLCH values that Tailwind v4 understands natively */
  --color-primary: oklch(0.65 0.25 264);
  --color-primary-foreground: oklch(0.98 0.01 264);

  --color-secondary: oklch(0.55 0.15 150);
  --color-secondary-foreground: oklch(0.98 0.01 150);

  --color-destructive: oklch(0.55 0.22 25);
  --color-destructive-foreground: oklch(0.98 0.01 25);

  --color-muted: oklch(0.94 0.005 264);
  --color-muted-foreground: oklch(0.55 0.02 264);
}
```

Nos componentes:
```tsx
<button className="bg-primary text-primary-foreground hover:bg-primary/90">
  Click me
</button>
```

---

## Ferramentas e Recursos

| Ferramenta | URL | Propósito |
|------|-----|---------|
| **OKLCH Color Picker** | https://oklch.com | Seletor OKLCH interativo com visualização de gamut |
| **Realtime Colors** | https://www.realtimecolors.com | Gerador completo de paletas com preview de dark mode |
| **Radix Colors** | https://www.radix-ui.com/colors | Paletas prontas compatíveis com OKLCH |
| **Huetone** | https://huetone.ardov.me | Crie escalas de paleta com uniformidade perceptual |
| **Color.js** | https://colorjs.io | Biblioteca JavaScript para manipulação de OKLCH |
| **Open Props** | https://open-props.style | Propriedades CSS customizadas, incluindo cores OKLCH |

---

## Suporte de Navegadores

Em 2026, OKLCH tem **96%+ de suporte global**:
- Chrome 111+ (March 2023)
- Firefox 113+ (May 2023)
- Safari 15.4+ (March 2022)
- Edge 111+ (March 2023)

Para o caso raro em que você precisa de um fallback:
```css
.element {
  /* Fallback for ancient browsers */
  color: #3b82f6;
  /* Modern browsers use this */
  color: oklch(0.65 0.25 264);
}
```

---

## Referência de Valores Comuns de Hue

| Hue | Cor | Uso Comum |
|-----|-------|-----------|
| 0 | Rosa/Vermelho | Perigo, amor |
| 25 | Vermelho/Laranja | Erro, destrutivo |
| 50 | Laranja | Aviso |
| 75 | Âmbar/Amarelo | Cautela, destaque |
| 90 | Amarelo | Atenção |
| 120 | Lima | Crescimento |
| 150 | Verde | Sucesso, positivo |
| 180 | Verde-azulado/Ciano | Informação, fresco |
| 210 | Azul-céu | Calma, links |
| 240 | Azul | Primário, confiança |
| 264 | Índigo/Azul | Primário, marca |
| 290 | Roxo | Criativo, premium |
| 320 | Magenta | Destaque |
| 340 | Rosa | Divertido, feminino |
