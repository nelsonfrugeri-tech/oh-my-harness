# Checklist de Code Review TypeScript/React

Checklist detalhado para code review de TypeScript/React/Next.js. 28 verificações em 7 categorias.

---

## Como Usar

Para cada arquivo TypeScript/TSX modificado:
1. Percorra as categorias abaixo sequencialmente
2. Marque [x] quando o item for verificado
3. Se encontrar uma violação, escreva um comentário com: verificação violada, severidade típica, correção de código

A severidade é indicativa. Use o bom senso conforme o contexto.

---

## Segurança

### [ ] 1. Secrets e Variáveis de Ambiente
**Verificar:**
- Nenhuma API key, token ou senha em código client-side
- Env vars com `NEXT_PUBLIC_` apenas para dados genuinamente públicos
- Secrets usados apenas em Server Components ou API routes
- `.env.local` no `.gitignore`

**Severidade típica:** BLOCKER

---

### [ ] 2. Prevenção de XSS
**Verificar:**
- `dangerouslySetInnerHTML` nunca usado com input do usuário sem sanitização
- DOMPurify ou equivalente usado quando HTML dinâmico é necessário
- `href` com protocolo `javascript:` bloqueado
- Conteúdo gerado pelo usuário escapado por padrão

**Severidade típica:** BLOCKER

---

### [ ] 3. CSRF e Formulários
**Verificar:**
- Formulários com CSRF tokens quando necessário
- Server Actions com validação de origem
- Fetch requests com credentials corretamente configurados

**Severidade típica:** MAJOR

---

### [ ] 4. Autenticação e Autorização
**Verificar:**
- Rotas protegidas com middleware ou layout guards
- Tokens não armazenados em localStorage (prefira httpOnly cookies)
- Verificação de permissões antes de exibir dados sensíveis
- Server Components usados para dados que requerem autenticação

**Severidade típica:** BLOCKER (rotas públicas) / MAJOR (interno)

---

### [ ] 5. Validação de Entrada
**Verificar:**
- Dados de formulário validados com Zod ou equivalente
- Server Actions validam a entrada antes de processar
- Schemas compartilhados entre client e server quando possível
- File uploads com validação de tipo e tamanho

**Severidade típica:** MAJOR

---

## Acessibilidade

### [ ] 6. HTML Semântico
**Verificar:**
- `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<header>`, `<footer>` usados corretamente
- `<button>` para ações, `<a>` para navegação (nunca `<div onClick>`)
- Headings em ordem hierárquica (h1 > h2 > h3)
- Listas (`<ul>`, `<ol>`) para conteúdo em lista

**Severidade típica:** MAJOR

---

### [ ] 7. ARIA Labels e Roles
**Verificar:**
- Elementos interativos customizados têm `role` e `aria-label`
- Botões apenas com ícone têm `aria-label`
- `aria-live` para conteúdo dinâmico que muda
- `aria-hidden="true"` em elementos decorativos
- `aria-expanded`, `aria-selected` em menus e tabs

**Severidade típica:** MAJOR (elementos interativos) / MINOR (decorativos)

---

### [ ] 8. Navegação por Teclado
**Verificar:**
- Todos os elementos interativos acessíveis via Tab
- Ordem de tab lógica (sem `tabIndex` > 0)
- Escape fecha modais/dropdowns
- Enter/Space ativa botões
- Setas para navegação em menu/tab
- Focus trap em modais

**Severidade típica:** MAJOR

---

### [ ] 9. Gerenciamento de Foco
**Verificar:**
- Foco movido para o modal quando ele abre
- Foco retorna ao trigger quando o modal fecha
- Foco visível (outline não removido globalmente)
- Skip links para o conteúdo principal
- `autoFocus` usado com cuidado

**Severidade típica:** MAJOR (modais) / MINOR (geral)

---

### [ ] 10. Cor e Contraste
**Verificar:**
- Razão de contraste >= 4.5:1 para texto normal (WCAG AA)
- Razão de contraste >= 3:1 para texto grande (>18px bold, >24px)
- Informação não transmitida apenas por cor (ícones, padrões, texto)
- Dark mode com contraste adequado

**Severidade típica:** MINOR

---

### [ ] 11. Imagens e Mídia
**Verificar:**
- Todas as imagens informativas têm `alt` descritivo
- Imagens decorativas têm `alt=""`
- Vídeos têm legendas/subtítulos quando possível
- SVGs acessíveis com `role="img"` e `aria-label`

**Severidade típica:** MAJOR (imagens informativas) / NIT (decorativas)

---

## Performance

### [ ] 12. Bundle Size
**Verificar:**
- Sem imports de bibliotecas inteiras quando apenas uma função é necessária
- Dynamic imports (`next/dynamic`, `React.lazy`) para componentes pesados
- Tree-shaking funcionando (named imports, não default de barrel files)
- Sem dependências duplicadas

**Severidade típica:** MAJOR (>50KB adicionados) / MINOR (<50KB)

---

### [ ] 13. Otimização de Render
**Verificar:**
- `React.memo` em componentes puros renderizados com frequência
- `useMemo` para computações caras
- `useCallback` para callbacks passados como props
- Keys estáveis em listas (nunca índice de array se a lista muda)
- Estado no nível correto (sem lifting desnecessário)
- Sem atualizações de estado em cascata causando múltiplos re-renders

**Severidade típica:** MINOR / MAJOR (listas grandes, tabelas)

---

### [ ] 14. Imagens e Assets
**Verificar:**
- `next/image` usado em vez de `<img>` (otimização automática)
- Formatos modernos (WebP, AVIF) quando possível
- `loading="lazy"` para imagens below the fold
- `priority` em imagens LCP (hero, above fold)
- Prop `sizes` correta para imagens responsivas

**Severidade típica:** MINOR / MAJOR (imagens LCP)

---

### [ ] 15. Data Fetching
**Verificar:**
- Data fetching no servidor quando possível (Server Components)
- `fetch` com `cache` e `revalidate` corretamente configurados
- Sem waterfalls (data fetching paralelo com `Promise.all`)
- Loading states com Suspense boundaries
- Streaming com React Server Components quando aplicável

**Severidade típica:** MAJOR (waterfalls em páginas críticas) / MINOR

---

### [ ] 16. Core Web Vitals
**Verificar:**
- LCP: elemento principal renderiza rápido (sem bloqueio)
- CLS: layouts estáveis (tamanhos definidos para imagens/ads/embeds)
- INP: interações respondem rápido (<200ms)
- Sem layout shifts causados por fontes, imagens ou conteúdo dinâmico

**Severidade típica:** MAJOR

---

## Testes

### [ ] 17. Testes de Componente
**Verificar:**
- Componentes críticos têm testes com Testing Library
- Testes interagem como usuário (click, type, não detalhes de implementação)
- Queries acessíveis usadas (`getByRole`, `getByLabelText`, não `getByTestId`)
- Estados testados (loading, error, empty, success)

**Severidade típica:** BLOCKER (componentes críticos sem testes) / MAJOR (cobertura <50%)

---

### [ ] 18. Testes de Hook
**Verificar:**
- Custom hooks testados com `renderHook`
- Side effects testados (chamadas de API, subscriptions)
- Cleanup verificado (event listeners, timers)

**Severidade típica:** MAJOR

---

### [ ] 19. Testes E2E
**Verificar:**
- Fluxos críticos cobertos (login, checkout, CRUD principal)
- Playwright ou Cypress configurado
- Testes não frágeis (sem hard waits, locators estáveis)
- Pipeline de CI roda E2E

**Severidade típica:** MAJOR (fluxos críticos) / MINOR

---

### [ ] 20. Testes de Acessibilidade
**Verificar:**
- axe-core integrado nos testes
- `toHaveNoViolations()` em testes de componente
- Testes de navegação por teclado em componentes interativos

**Severidade típica:** MINOR

---

## Qualidade de Código

### [ ] 21. TypeScript Strict
**Verificar:**
- Sem `any` (use `unknown` se o tipo for realmente desconhecido)
- Sem `@ts-ignore` ou `@ts-expect-error` sem justificativa
- Generics usados corretamente
- Utility types usados onde apropriado (Partial, Pick, Omit, Record)
- Discriminated unions para state machines
- Operador `satisfies` para validação de tipo

**Severidade típica:** MINOR (`any` em lugares isolados) / MAJOR (`any` em interfaces públicas)

---

### [ ] 22. Design de Componente
**Verificar:**
- Props tipadas com interface ou type (não inline)
- Componentes < 200 linhas (se mais, decomponha)
- Responsabilidade Única (um componente, uma responsabilidade)
- Composição em vez de herança
- Default exports para páginas, named exports para componentes

**Severidade típica:** MINOR / MAJOR (componentes >300 linhas)

---

### [ ] 23. Tratamento de Erros
**Verificar:**
- Error Boundaries em rotas/layouts
- Arquivos `error.tsx` no App Router
- Erros de fetch tratados com try/catch
- Mensagens de erro claras para o usuário
- Sentry ou equivalente para error tracking

**Severidade típica:** MAJOR (rotas sem error boundary) / MINOR

---

### [ ] 24. Nomeação e Convenções
**Verificar:**
- Componentes: PascalCase (`UserProfile`, não `userProfile`)
- Hooks: prefixo `use` (`useAuth`, não `getAuth`)
- Arquivos: kebab-case ou correspondendo ao nome do componente
- Constantes: UPPER_SNAKE_CASE
- Props booleanas: prefixo `is`, `has`, `should`

**Severidade típica:** MINOR

---

## Arquitetura

### [ ] 25. Server vs Client Components
**Verificar:**
- `"use client"` apenas onde necessário (interatividade, hooks, browser APIs)
- Dados sensíveis apenas em Server Components
- Props serializáveis entre Server e Client Components
- Não passar funções como props de Server para Client Components

**Severidade típica:** MAJOR (`"use client"` desnecessariamente em árvore grande) / MINOR

---

### [ ] 26. Gerenciamento de Estado
**Verificar:**
- Estado local quando possível (useState, useReducer)
- Context para estado compartilhado em árvore pequena
- Store externo (Zustand, Jotai) para estado global complexo
- Estado na URL para filtros/paginação (nuqs, useSearchParams)
- Sem prop drilling excessivo (>3 níveis)

**Severidade típica:** MINOR / MAJOR (gerenciamento de estado errado em escala)

---

### [ ] 27. Padrões de Data Fetching
**Verificar:**
- Server Components para data fetching estático/SSR
- React Server Actions para mutations
- SWR/TanStack Query para data fetching client-side com cache
- Sem fetch em useEffect quando Server Component é possível
- Loading states (Suspense, loading.tsx)

**Severidade típica:** MAJOR (fetch desnecessário em useEffect) / MINOR

---

## Estilização

### [ ] 28. Tailwind e Design System
**Verificar:**
- Classes Tailwind consistentes (sem misturar com CSS modules sem motivo)
- Design tokens usados (cores do tema, não hex hardcoded)
- Design responsivo com breakpoints corretos (sm, md, lg, xl)
- Dark mode usando a variante `dark:` quando aplicável
- Espaçamento consistente (use a escala: 1, 2, 3, 4, não valores arbitrários)

**Severidade típica:** NIT (inconsistências menores) / MINOR (violação do design system)

---

## Ferramentas de Automação

```bash
# Type checking
npx tsc --noEmit

# Linting + formatting
npx biome check .

# Accessibility audit
npx axe-core-cli http://localhost:3000

# Bundle analysis
npx @next/bundle-analyzer

# Testing
npx vitest run

# E2E
npx playwright test

# Lighthouse CI
npx lhci autorun
```
