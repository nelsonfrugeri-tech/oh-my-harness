# Ícones e Imagens — Lucide, Otimização e Boas Práticas

## Bibliotecas de Ícones

### Lucide (Escolha Padrão)

O Lucide é o fork comunitário do Feather Icons, com mais de 1500 ícones, design
baseado em traço (stroke) consistente e excelentes integrações com React/Vue/Svelte.

```tsx
import { Search, Menu, X, ChevronRight, Star, Heart } from "lucide-react";

// Direct usage
<Search className="size-4" />
<Menu className="size-5 text-muted-foreground" />

// Reusable Icon wrapper for consistency
interface IconProps {
  icon: React.ElementType;
  size?: number;
  className?: string;
}

function Icon({ icon: IconComponent, size = 16, className }: IconProps) {
  return (
    <IconComponent
      size={size}
      strokeWidth={1.5}
      className={cn("shrink-0", className)}
    />
  );
}

// Usage
<Icon icon={Search} size={20} className="text-muted-foreground" />
```

### Diretrizes de Tamanho

| Contexto | Tamanho | Tailwind | strokeWidth |
|---------|------|----------|-------------|
| Alinhado com o texto | 16px | `size-4` | 1.5-2 |
| Ícone de botão | 16-18px | `size-4` | 1.5 |
| Navegação | 20px | `size-5` | 1.5 |
| Card de destaque | 24px | `size-6` | 1.5 |
| Hero/estado vazio | 32-48px | `size-8` a `size-12` | 1-1.5 |

### Alinhamento de Ícone + Texto

```tsx
// Always use flex + gap for icon-text alignment
<button className="inline-flex items-center gap-2">
  <Search className="size-4" />
  <span>Search</span>
</button>

// For icon-only buttons, always include sr-only label
<button className="inline-flex items-center justify-center size-10 rounded-lg hover:bg-accent"
  aria-label="Open menu">
  <Menu className="size-5" />
</button>
```

### Conjuntos de Ícones Alternativos

| Biblioteca | Ícones | Estilo | Quando Usar |
|---------|-------|-------|-------------|
| **Lucide** | 1500+ | Traço, consistente | Padrão para a maioria dos projetos |
| **Phosphor** | 9000+ | Múltiplos pesos (thin/light/regular/bold/fill/duotone) | Quando você precisa de máxima flexibilidade |
| **Heroicons** | 300+ | Outline + Solid | Ecossistema Tailwind, conjunto minimalista |
| **Tabler Icons** | 5000+ | Traço | Conjunto grande, open source |

### Exemplo com Phosphor (Quando o Lucide Não Basta)

```tsx
import { MagnifyingGlass, House, Gear } from "@phosphor-icons/react";

// Phosphor supports weight variants
<MagnifyingGlass weight="light" size={20} />
<House weight="duotone" size={24} />
<Gear weight="bold" size={16} />
```

---

## Padrão de SVG Inline

Para ícones personalizados que não existem em nenhuma biblioteca, use componentes SVG inline:

```tsx
interface SvgIconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

function CustomLogo({ size = 24, ...props }: SvgIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
    </svg>
  );
}
```

---

## Otimização de Imagens

### Prioridade de Formato: AVIF > WebP > JPEG

| Formato | Tamanho vs JPEG | Qualidade | Suporte dos Navegadores (2026) |
|--------|-------------|---------|----------------------|
| **AVIF** | 50-60% menor | Excelente | 95%+ |
| **WebP** | 25-35% menor | Excelente | 98%+ |
| **JPEG** | Referência (baseline) | Bom | 100% |
| **PNG** | Maior | Sem perdas (lossless) | 100% (use para transparência quando não houver WebP/AVIF) |

### Padrão do Elemento picture

```tsx
<picture>
  <source srcSet="/images/hero.avif" type="image/avif" />
  <source srcSet="/images/hero.webp" type="image/webp" />
  <img
    src="/images/hero.jpg"
    alt="Dashboard overview showing analytics charts and key metrics"
    width={1200}
    height={630}
    loading="lazy"
    decoding="async"
    className="rounded-xl object-cover"
  />
</picture>
```

### Imagens Responsivas com srcset

```tsx
<picture>
  {/* Art direction: different crop for mobile */}
  <source
    media="(max-width: 639px)"
    srcSet="/images/hero-mobile.avif 640w"
    type="image/avif"
  />
  <source
    media="(max-width: 639px)"
    srcSet="/images/hero-mobile.webp 640w"
    type="image/webp"
  />

  {/* Desktop: full resolution */}
  <source
    srcSet="/images/hero-sm.avif 640w, /images/hero-md.avif 1024w, /images/hero-lg.avif 1920w"
    sizes="100vw"
    type="image/avif"
  />
  <source
    srcSet="/images/hero-sm.webp 640w, /images/hero-md.webp 1024w, /images/hero-lg.webp 1920w"
    sizes="100vw"
    type="image/webp"
  />

  <img
    src="/images/hero-md.jpg"
    srcSet="/images/hero-sm.jpg 640w, /images/hero-md.jpg 1024w, /images/hero-lg.jpg 1920w"
    sizes="100vw"
    alt="Dashboard overview"
    width={1920}
    height={1080}
    loading="lazy"
    decoding="async"
  />
</picture>
```

### Otimização de Imagens no Next.js

```tsx
import Image from "next/image";

// Automatic optimization: resizing, format conversion, lazy loading
<Image
  src="/images/hero.jpg"
  alt="Dashboard overview"
  width={1200}
  height={630}
  priority       // Above the fold — skip lazy loading
  quality={85}   // Balance quality vs size
  className="rounded-xl object-cover"
/>

// Fill mode for responsive containers
<div className="relative aspect-video overflow-hidden rounded-xl">
  <Image
    src="/images/hero.jpg"
    alt="Dashboard overview"
    fill
    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
    className="object-cover"
  />
</div>
```

### Lazy Loading

```tsx
// Native lazy loading (preferred)
<img loading="lazy" decoding="async" ... />

// Intersection Observer for advanced control
function LazyImage({ src, alt, ...props }: ImageProps) {
  const ref = useRef<HTMLImageElement>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setLoaded(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" } // Start loading 200px before visible
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <img
      ref={ref}
      src={loaded ? src : undefined}
      data-src={src}
      alt={alt}
      {...props}
    />
  );
}
```

### Pipeline de Build de Imagens com sharp

```ts
// scripts/optimize-images.ts
import sharp from "sharp";
import { glob } from "glob";

const images = await glob("public/images/source/**/*.{jpg,png}");

for (const img of images) {
  const name = path.parse(img).name;
  const input = sharp(img);

  // Generate AVIF
  await input.clone().avif({ quality: 75 }).toFile(`public/images/${name}.avif`);

  // Generate WebP
  await input.clone().webp({ quality: 80 }).toFile(`public/images/${name}.webp`);

  // Generate optimized JPEG fallback
  await input.clone().jpeg({ quality: 85, mozjpeg: true }).toFile(`public/images/${name}.jpg`);

  // Generate responsive sizes
  for (const width of [640, 1024, 1920]) {
    await input.clone().resize(width).avif({ quality: 75 }).toFile(`public/images/${name}-${width}w.avif`);
    await input.clone().resize(width).webp({ quality: 80 }).toFile(`public/images/${name}-${width}w.webp`);
  }
}
```

---

## Diretrizes de Texto Alternativo (Alt)

| Tipo de Imagem | Texto Alternativo |
|-----------|----------|
| Informativa (gráfico, foto) | Descreva o que ela mostra: `"Revenue chart showing 40% growth in Q3"` |
| Decorativa (fundo, separador) | Vazio: `alt=""` |
| Funcional (botão com ícone) | Descreva a ação: `"Close dialog"` (via aria-label no botão) |
| Complexa (infográfico) | Alt breve + descrição detalhada em outro lugar |

```tsx
// Informative image
<img alt="Team photo: 5 engineers in the office celebrating a launch" ... />

// Decorative image (conveys no information)
<img alt="" role="presentation" ... />

// Icon inside a button (button gets the label, not the icon)
<button aria-label="Close dialog">
  <X className="size-4" aria-hidden="true" />
</button>
```

---

## Regras

1. **Lucide como padrão** — consistente, leve, bem mantido
2. **AVIF primeiro, WebP como fallback, JPEG como rede de segurança** — use o elemento picture
3. **Sempre defina width/height** — evita layout shift (CLS)
4. **loading="lazy" para conteúdo abaixo da dobra** — prioridade apenas para o que está acima da dobra
5. **Texto alt significativo** — descreva o que a imagem comunica, não como ela se parece
6. **aria-hidden="true" em ícones decorativos** — leitores de tela os ignoram
7. **strokeWidth={1.5}** como padrão no Lucide — mais limpo que o valor padrão 2
