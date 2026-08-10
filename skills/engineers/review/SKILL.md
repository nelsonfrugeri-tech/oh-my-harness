---
version: 1.0.0
name: review
description: |
  Metodologia de code review independente de linguagem. Cobre taxonomia de severidade (BLOCKER/MAJOR/MINOR/NIT),
  templates de comentários, checklist de review (segurança, performance, testes, qualidade de código, arquitetura),
  critérios de decisão (aprovar, aprovar com ressalvas, bloquear) e o fluxo do processo de review.
  Use quando: (1) Revisar qualquer PR independentemente da linguagem, (2) Classificar a severidade de um problema,
  (3) Escrever comentários de review estruturados, (4) Tomar decisões de merge/bloqueio.
  Gatilhos: /review, code review, PR review, security review, quality gate.
type: capability
---

# Review — Metodologia de Code Review

## Propósito

Esta skill é a base de conhecimento para code review sistemático. Ela é **independente de linguagem** — a
metodologia, a taxonomia de severidade, os templates de comentários e os critérios de decisão se aplicam a qualquer linguagem.
Os checklists específicos de linguagem (Python, TypeScript) estão nas referências.

**O que esta skill contém:**
- Taxonomia de severidade (BLOCKER, MAJOR, MINOR, NIT)
- Checklist de review (categorias universais)
- Templates de comentários (formato estruturado de feedback)
- Critérios de decisão (aprovar, aprovar com ressalvas, bloquear)
- Fluxo do processo de review

---

## Filosofia

### Review é um Quality Gate, Não um Exercício de Guarda de Portão

O objetivo do review é software melhor. Todo comentário deve ser:
- **Acionável** — achado específico com referência file:line, não reclamações vagas
- **Construtivo** — proponha uma alternativa quando identificar um problema
- **Classificado** — todo achado carrega uma severidade para que a prioridade fique clara
- **Independente** — o revisor não pode ser o autor do código

### Princípios

1. **Leia antes de julgar** — leia o diff completo e todos os arquivos tocados antes de formar qualquer opinião
2. **Classifique todo achado** — BLOCKER, MAJOR, MINOR ou NIT — sem ambiguidade
3. **Resuma o veredito** — total de BLOCKERs/MAJORs/MINORs, recomendação final
4. **Nunca modifique o código** — revisores descrevem, autores corrigem
5. **Sem blockers = aprovado** — declare explicitamente "Nenhum blocker encontrado — aprovado" quando estiver limpo

---

## 1. Taxonomia de Severidade

### BLOCKER

**Quando usar:**
- Vulnerabilidades de segurança (injection, XSS, secrets hardcoded, bypass de autenticação)
- Potencial de perda de dados (erros não tratados em caminhos de escrita, transações ausentes)
- Bugs de correção (erros de lógica que produzem resultados errados em caminhos críticos)
- Mudanças de API que quebram compatibilidade sem versionamento

**Efeito:** O merge deve ser bloqueado até a resolução. Requer correção imediata.

**Template:**
```markdown
[BLOCKER] {Short description}

**File:** {path}:{line}
**Issue:** {clear description of the problem in 1-2 sentences}

**Current code:**
```{lang}
{problematic code}
```

**Suggested fix:**
```{lang}
{corrected code}
```

**Impact:** {what happens if this ships}
**Action:** Block merge. Must be corrected before any approval.
```

---

### MAJOR

**Quando usar:**
- Problemas de performance (N+1 queries em hot paths, O(n²) onde O(n) é possível)
- Testes ausentes em caminhos críticos de código
- Memory leaks ou resource leaks
- Tratamento de erros ausente em operações que podem falhar
- Violações de arquitetura que criam acoplamento significativo

**Efeito:** Deve ser corrigido antes do merge ou imediatamente após. Cria dívida técnica significativa.

**Template:**
```markdown
[MAJOR] {Short description}

**File:** {path}:{line}
**Issue:** {description}

**Current code:**
```{lang}
{problematic code}
```

**Suggested fix:**
```{lang}
{corrected code}
```

**Impact if unaddressed:** {production impact}
**Action:** Fix before merge (preferred) or create a ticket and fix immediately after.
```

---

### MINOR

**Quando usar:**
- Anotações de tipo / type hints ausentes
- Nomeação pouco descritiva
- Problemas de qualidade de código (alta complexidade ciclomática, duplicação de código, docstrings ausentes)
- Asserções de teste fracas demais
- Desvios de estilo de código

**Efeito:** Não bloqueia o merge. Deve ser corrigido em um follow-up. Afeta a manutenibilidade.

**Template:**
```markdown
[MINOR] {Short description}

**File:** {path}:{line}
**Issue:** {description}
**Suggestion:** {what to do instead}
**Why:** {brief explanation of the benefit}
```

---

### NIT

**Quando usar:**
- Preferência pessoal (quando ambas as abordagens estão corretas)
- Inconsistências triviais de formatação não capturadas por linters
- Melhorias opcionais

**Efeito:** Nenhuma ação necessária. Bom ter.

**Template:**
```markdown
[NIT] {Short description} — {one-line suggestion}
```

---

## 2. Checklist de Review

Aplique a todo arquivo alterado, independentemente da linguagem.

### Segurança
- [ ] Nenhum secret ou credencial hardcoded (API keys, senhas, tokens)
- [ ] Entrada externa é validada antes do uso
- [ ] Injection de SQL/comando/HTML é prevenida
- [ ] Autenticação e autorização aplicadas em cada fronteira
- [ ] Dados sensíveis não são logados (PII, senhas, tokens)
- [ ] Operações criptográficas usam algoritmos e bibliotecas aprovados
- [ ] Security headers configurados (para endpoints web)

**Severidade típica:** BLOCKER

### Performance
- [ ] Nenhum padrão de N+1 query (loops com chamadas a DB dentro)
- [ ] Algoritmos eficientes para a escala dos dados (O(n²) é suspeito)
- [ ] Recursos gerenciados (conexões, file handles fechados após o uso)
- [ ] Sem serialização/desserialização desnecessária em hot paths
- [ ] Caching considerado para operações caras e repetidas

**Severidade típica:** MAJOR (hot paths) / MINOR (cold paths)

### Testes
- [ ] Caminhos críticos de código têm testes
- [ ] Testes não são frágeis (testam comportamento, não implementação)
- [ ] Asserções são específicas (não apenas "não quebra")
- [ ] Caminhos de erro são testados (não apenas o happy path)
- [ ] Nomes dos testes descrevem o comportamento sendo testado

**Severidade típica:** BLOCKER (sem testes em código crítico) / MAJOR (<50% de cobertura em caminho crítico)

### Qualidade de Código
- [ ] Tipos são explícitos (type hints, tipos de TypeScript — sem `any` implícito)
- [ ] Tratamento de erros é explícito — sem engolir exceções silenciosamente
- [ ] Logging estruturado (não print/console.log)
- [ ] APIs públicas têm documentação/docstrings
- [ ] Nomeação é descritiva e autoexplicativa
- [ ] Responsabilidade Única — cada função/classe faz uma coisa
- [ ] DRY — código não é duplicado
- [ ] Complexidade ciclomática é razoável (< 10 por função)
- [ ] Imports organizados e imports não usados removidos

**Severidade típica:** MINOR / MAJOR (APIs públicas)

### Arquitetura
- [ ] Separação de responsabilidades (lógica de negócio não misturada com I/O)
- [ ] Injeção de dependência (dependências não criadas inline na lógica de negócio)
- [ ] Nenhuma dependência circular introduzida
- [ ] Dependências fixadas em versões exatas
- [ ] Async/await usado corretamente (sem chamadas bloqueantes em contexto async)
- [ ] Configuração externalizada (não hardcoded)

**Severidade típica:** MINOR / MAJOR (violação séria)

### Honestidade epistêmica (doutrina em `doctrine/epistemics.md`)
- [ ] Todo número, métrica ou estado afirmado — no código, no comentário, na descrição do PR ou
      no relatório da mudança — tem evidência observada (saída de comando, teste, medição)
- [ ] Hipóteses estão rotuladas como hipóteses; nenhum "deve funcionar" apresentado como conclusão
- [ ] Decisões de trade-off (fix rápido × correto, abordagem A × B) citam o dado que as embasou,
      ou declaram a hipótese e o que faria revisitá-la

**Severidade típica:** BLOCKER (dado inventado ou certeza sem evidência) / MAJOR (hipótese sem rótulo)

### Específico de Frontend (TypeScript/React)
- [ ] Nenhum secret ou API key em código client-side
- [ ] `dangerouslySetInnerHTML` é sanitizado
- [ ] ARIA labels em elementos interativos
- [ ] HTML semântico (`nav`, `main`, `article`, `section`)
- [ ] Navegação por teclado funcional
- [ ] Contraste de cor WCAG AA (4.5:1)
- [ ] Error Boundaries em rotas críticas
- [ ] Nenhuma diretiva `"use client"` desnecessária
- [ ] Imagens otimizadas (next/image, lazy loading, WebP)

**Referências:** [references/checklist-python.md](references/checklist-python.md) | [references/checklist-typescript.md](references/checklist-typescript.md)

---

## 3. Critérios de Decisão

### BLOQUEAR MERGE

**Condição:** 1 ou mais achados BLOCKER

**Template:**
```markdown
**Recommendation:** BLOCK MERGE

**Verdict:** Found {n} BLOCKER(s) that must be resolved before this PR can be merged.

**Blockers:**
- {blocker 1} — {file}:{line}
- {blocker 2} — {file}:{line}

**Summary:** {n} BLOCKER, {n} MAJOR, {n} MINOR, {n} NIT
```

---

### APROVAR COM RESSALVAS

**Condição:** 0 BLOCKERs, 1 ou mais MAJORs

**Template:**
```markdown
**Recommendation:** APPROVE WITH CAVEATS

**Verdict:** No blockers found. {n} MAJOR finding(s) must be resolved before production.

**Majors (fix before production):**
- {major 1} — {file}:{line}
- {major 2} — {file}:{line}

**Action:** Merge is acceptable, but create tickets for MAJOR findings and resolve before next release.

**Summary:** 0 BLOCKER, {n} MAJOR, {n} MINOR, {n} NIT
```

---

### APROVAR

**Condição:** 0 BLOCKERs, 0 MAJORs

**Template:**
```markdown
**Recommendation:** APPROVE

**Verdict:** No blocking issues found. MINOR findings and NITs can be addressed as continuous improvement.

**Minor findings (optional, follow-up):**
- {minor 1}

**Summary:** 0 BLOCKER, 0 MAJOR, {n} MINOR, {n} NIT
```

---

### APROVAR COM ELOGIO

**Condição:** Poucos ou nenhum achado (apenas NIT), código de alta qualidade

**Template:**
```markdown
**Recommendation:** APPROVE

**Verdict:** Excellent quality. Patterns applied consistently. Zero blocking issues.

**Highlights:**
- {highlight 1}
- {highlight 2}

**Summary:** 0 BLOCKER, 0 MAJOR, 0 MINOR, {n} NIT
```

---

## 4. Fluxo do Processo de Review

```
1. READ the issue/PR description — understand the intent before reading the code
2. READ the full diff — all changed files, not just the interesting ones
3. READ the context — files called by the changed code, tests, related files
4. APPLY the checklist — go through each category systematically
5. WRITE findings — use the comment templates, classify every finding
6. WRITE the summary — total counts, final recommendation, clear verdict
7. POST the review — all findings documented, no verbal-only feedback
```

### O Que Verificar Primeiro

Ordem de prioridade quando o tempo é limitado:

1. **Segurança** — BLOCKERs aparecem aqui com mais frequência
2. **Correção** — bugs de lógica, integridade de dados
3. **Testes** — cobertura ausente em caminhos críticos
4. **Arquitetura** — acoplamento, separação de responsabilidades
5. **Performance** — N+1 queries, eficiência de algoritmos
6. **Qualidade de código** — type hints, nomeação, documentação

### Nunca Faça

- Revisar seu próprio código — sempre use um revisor diferente
- Dar feedback verbal que não é documentado — achados devem ser escritos
- Dizer "está bom" sem verificar segurança e testes
- Pular o resumo — sempre declare os totais e o veredito final

---

## Reference Files

- [references/checklist-python.md](references/checklist-python.md) — Checklist de Code Review Python
- [references/checklist-typescript.md](references/checklist-typescript.md) — Checklist de Code Review TypeScript/React