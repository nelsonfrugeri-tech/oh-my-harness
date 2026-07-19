---
version: 1.0.0
name: research
description: |
  Metodologia estruturada de pesquisa técnica para decisões de engenharia. Cobre estratégias de
  busca específicas por plataforma (Google, GitHub, HuggingFace, PyPI, npm, arXiv, Papers with Code),
  operadores de busca avançados, taxonomia de fontes por domínio, protocolo de validação multi-fonte,
  templates de síntese (tabelas de comparação, formato de recomendação, log de pesquisa), frameworks
  de debate (análise de trade-off, matrizes de decisão), anti-padrões e quando parar de pesquisar.
  Use quando: (1) Escolher tecnologias/bibliotecas/frameworks, (2) Comparar alternativas,
  (3) Avaliar o estado da arte, (4) Embasar decisões arquiteturais com evidências,
  (5) Investigar vulnerabilidades ou breaking changes.
  Triggers: /research, comparar opções, estado da arte, avaliar alternativas, seleção de tecnologia.
type: capability
---

# Research — Metodologia de Pesquisa Técnica

## Propósito

Esta skill é a base de conhecimento para pesquisa técnica estruturada. Ela fornece metodologia,
não opiniões. Toda recomendação que um agente fizer deve estar fundamentada em pesquisa atual,
verificada e multi-fonte.

**O que esta skill contém:**
- Estratégias de busca por plataforma
- Operadores de busca avançados
- Taxonomia de fontes por domínio
- Protocolo de validação (multi-fonte, verificação de data, detecção de viés)
- Templates de síntese (tabelas de comparação, formato de recomendação, log de pesquisa)
- Frameworks de debate (análise de trade-off, matrizes de decisão)
- Anti-padrões comuns
- Quando parar de pesquisar

**O que esta skill NÃO contém:**
- Conhecimento específico de domínio (isso vive em python, typescript, ai-ml, etc.)
- Workflow de execução (isso é responsabilidade dos agentes)

---

## 1. Estratégias de Busca por Plataforma

Cada plataforma tem pontos fortes diferentes. Use a plataforma certa para a pergunta certa.

### Árvore de Decisão

```
What am I researching?
  |
  +-- Library/framework selection? --> PyPI/npm + GitHub + Google
  |
  +-- AI/ML model or technique? --> HuggingFace + arXiv + Papers with Code
  |
  +-- Infrastructure/DevOps tool? --> GitHub + Google + vendor docs
  |
  +-- Security vulnerability? --> NVD + GitHub Advisories + Google
  |
  +-- Benchmark/performance data? --> Papers with Code + GitHub + blog posts
  |
  +-- Best practice/pattern? --> Google + GitHub (real codebases) + docs
  |
  +-- Breaking changes/migration? --> GitHub releases + changelog + Google
```

### Pontos Fortes das Plataformas

| Plataforma | Melhor Para | Limitações |
|----------|----------|-------------|
| **Google** | Busca geral, blog posts, tutoriais, docs | Ruidoso, spam de SEO, resultados desatualizados |
| **GitHub** | Código-fonte, releases, stars, issues, uso real | Popularidade != qualidade |
| **PyPI** | Pacotes Python, versões, dependências | Nenhum sinal de qualidade além de downloads |
| **npm** | Pacotes JS/TS, versões, dependências | Igual ao PyPI |
| **HuggingFace** | Modelos, datasets, spaces, benchmarks | Específico para AI/ML |
| **arXiv** | Papers de pesquisa, técnicas de ponta | Acadêmico, pode não ser prático |
| **Papers with Code** | Benchmarks SOTA, leaderboards | Foco acadêmico |
| **Stack Overflow** | Problemas comuns, workarounds | Respostas podem estar desatualizadas |
| **Docs oficiais** | Referência oficial de API, guias | Pode ficar atrás dos releases |

**Referências:** [references/platforms/](references/platforms/)

---

## 2. Operadores de Busca Avançados

### Google

```
# Exact match
"pydantic v2 migration guide"

# Site-specific
site:docs.anthropic.com tool use
site:github.com qdrant client python

# Date filter
"fastapi middleware" after:2025-01-01

# Exclude results
qdrant python -javascript -typescript

# File type
filetype:pdf "system design" "microservices"

# OR operator
(fastapi OR django) "rate limiting" 2025

# In title
intitle:"migration guide" pydantic v2

# In URL
inurl:changelog qdrant
```

### GitHub

```
# Search code
language:python "from anthropic import" stars:>100

# Search repos
topic:rag language:python stars:>500 pushed:>2025-01-01

# Search issues/PRs
repo:pydantic/pydantic is:issue is:open label:bug "v2"

# Filename search
filename:pyproject.toml "pydantic>=2"

# Exclude forks
fork:false stars:>100 "semantic cache"

# Recently updated
pushed:>2025-06-01 topic:vector-database language:python
```

### HuggingFace

```
# Model search with filters
https://huggingface.co/models?search=<query>&sort=trending

# Filter by task
https://huggingface.co/models?pipeline_tag=text-generation&sort=trending

# Filter by library
https://huggingface.co/models?library=transformers&sort=downloads
```

### arXiv

```
# Search by title
ti:"retrieval augmented generation"

# Search by abstract
abs:"chain of thought" AND abs:"reasoning"

# Category filter
cat:cs.CL  (Computation and Language)
cat:cs.AI  (Artificial Intelligence)
cat:cs.LG  (Machine Learning)

# Date filter
submittedDate:[2025-01-01 TO 2025-12-31]

# Combined
ti:"RAG" AND cat:cs.CL AND submittedDate:[2025-01-01 TO *]
```

---

## 3. Taxonomia de Fontes por Domínio

### Bibliotecas e Frameworks

| Prioridade | Fonte | O Que Verificar |
|----------|--------|---------------|
| 1 | **Docs oficiais** | Referência de API, guias de migração, changelog |
| 2 | **GitHub releases** | Notas de release, breaking changes, histórico de versões |
| 3 | **PyPI/npm** | Tendências de download, data do último release, dependências |
| 4 | **GitHub issues** | Bugs conhecidos, issues comuns, responsividade dos mantenedores |
| 5 | **Blog posts** | Tutoriais, comparações, uso no mundo real |
| 6 | **Stack Overflow** | Erros comuns, workarounds |

**Sinais de alerta:**
- Último release há > 12 meses
- Tendências de download em queda
- Muitas issues abertas sem respostas dos mantenedores
- Sem type stubs (Python) ou sem @types (TypeScript)

### Modelos e Técnicas de AI/ML

| Prioridade | Fonte | O Que Verificar |
|----------|--------|---------------|
| 1 | **Papers with Code** | Benchmarks SOTA, leaderboards |
| 2 | **HuggingFace** | Model cards, benchmarks, uso pela comunidade |
| 3 | **arXiv** | Paper original, metodologia, limitações |
| 4 | **Blogs oficiais** | Anúncios de Anthropic, OpenAI, Google |
| 5 | **GitHub** | Implementações de referência, reproduções da comunidade |

**Sinais de alerta:**
- Sem reprodução independente
- Benchmarks apenas em datasets escolhidos a dedo
- Sem open weights ou acesso via API
- Paper sem código

### Infraestrutura e DevOps

| Prioridade | Fonte | O Que Verificar |
|----------|--------|---------------|
| 1 | **Docs oficiais** | Instalação, configuração, operação |
| 2 | **GitHub** | Stars, issues, cadência de releases |
| 3 | **CNCF landscape** | Nível de maturidade, adoção |
| 4 | **Comparações de vendors** | Ler com consciência de viés |
| 5 | **Postmortems de produção** | Modos reais de falha |

**Sinais de alerta:**
- Sem clientes de referência em produção
- Projeto de mantenedor único para infraestrutura crítica
- Sem documentação de disaster recovery
- Vendor lock-in sem estratégia de saída

### Segurança

| Prioridade | Fonte | O Que Verificar |
|----------|--------|---------------|
| 1 | **NVD (nvd.nist.gov)** | Base de dados de CVE, scores de severidade |
| 2 | **GitHub Security Advisories** | Advisories por repositório |
| 3 | **OWASP** | Top 10, cheat sheets, guia de testes |
| 4 | **Snyk/Sonatype** | Bases de dados de vulnerabilidades de dependências |
| 5 | **Boletins de segurança de vendors** | Advisories específicos do provedor |

---

## 4. Protocolo de Validação

Toda informação pesquisada deve passar por validação antes de ser apresentada como fato.

### O Protocolo de 4 Verificações

```
For every claim or recommendation:

1. SOURCE COUNT
   - Minimum 2 independent sources for factual claims
   - Minimum 3 sources for technology recommendations
   - "Independent" = different authors/organizations

2. DATE CHECK
   - Source published within last 12 months? -> strong signal
   - Source published 12-24 months ago? -> verify still current
   - Source published > 24 months ago? -> treat as potentially outdated
   - ALWAYS check: has a newer version been released since the source?

3. BIAS DETECTION
   - Is the source a vendor recommending their own product? -> flag bias
   - Is the author affiliated with a competing product? -> flag bias
   - Is the benchmark run by the tool's own team? -> flag bias
   - Are negative aspects discussed? -> more credible if yes

4. CROSS-REFERENCE
   - Do multiple independent sources agree? -> strong signal
   - Do sources contradict each other? -> investigate why
   - Is there a clear consensus? -> note the consensus
   - Is there active debate? -> present both sides
```

### Níveis de Confiança

Após a validação, atribua um nível de confiança a cada afirmação:

| Nível | Critério | Rótulo |
|-------|----------|-------|
| **Alto** | 3+ fontes recentes independentes concordam, sem contradições | Apresentar como fato |
| **Médio** | 2 fontes concordam, ou fontes recentes mas limitadas | "Com base nas evidências disponíveis..." |
| **Baixo** | Fonte única, ou fontes desatualizadas, ou contradições | Marcar como [Não verificado] |
| **Nenhum** | Nenhuma fonte encontrada, ou todas as fontes desatualizadas | "Não é possível verificar. Baseado em dados de treinamento que podem estar desatualizados." |

### Quando as Fontes Conflitam

```
1. Note the conflict explicitly
2. Check which source is more recent
3. Check which source has more credibility (official docs > blog post)
4. Check if the conflict is due to version differences
5. Present both sides with dates and sources
6. Recommend the user verify with their specific version/setup
```

---

## 5. Templates de Síntese

### Template de Tabela de Comparação

```markdown
## Comparison: {Topic}

**Context:** {What problem are we solving? What constraints exist?}
**Date researched:** {YYYY-MM-DD}
**Sources consulted:** {N sources}

| Criterion | {Option A} | {Option B} | {Option C} |
|-----------|------------|------------|------------|
| **Maturity** | {description} | {description} | {description} |
| **Performance** | {metrics} | {metrics} | {metrics} |
| **Ecosystem** | {integrations} | {integrations} | {integrations} |
| **Learning curve** | {assessment} | {assessment} | {assessment} |
| **Maintenance** | {release cadence, community} | ... | ... |
| **Cost** | {pricing model} | {pricing model} | {pricing model} |
| **Lock-in risk** | {low/medium/high + why} | ... | ... |
| **Our constraints** | {fit assessment} | {fit assessment} | {fit assessment} |

### Recommendation

**Choice:** {Option X}
**Confidence:** {High/Medium/Low}
**Reasoning:** {2-3 sentences explaining the decision}
**Trade-offs accepted:** {what we give up by choosing this}
**Revisit when:** {conditions that should trigger re-evaluation}

### Sources
1. {source with URL and date}
2. {source with URL and date}
```

### Formato de Recomendação Única

```markdown
## Recommendation: {Topic}

**Problem:** {What we need to solve}
**Recommendation:** {Tool/approach}
**Version:** {Exact version}
**Confidence:** {High/Medium/Low}

**Why this:**
- {Reason 1 with source}
- {Reason 2 with source}

**Why not {alternative 1}:**
- {Reason with source}

**Risks:**
- {Risk 1 + mitigation}

**Sources:**
1. {source}
2. {source}
```

### Formato de Log de Pesquisa

```markdown
## Research Log: {Topic}

**Question:** {What are we trying to answer?}
**Started:** {timestamp}
**Completed:** {timestamp}

### Search queries used
1. `{query}` on {platform} -> {N results reviewed}

### Sources reviewed
| # | Source | Date | Relevance | Key finding |
|---|--------|------|-----------|-------------|
| 1 | {URL} | {date} | {high/med/low} | {one-liner} |

### Key findings
1. {Finding 1}

### Contradictions found
- {Source A} says X, but {Source B} says Y. Resolution: {explanation}

### Conclusion
{Final answer with confidence level}
```

---

## 6. Frameworks de Debate

### Análise de Trade-off

```markdown
## Trade-off Analysis: {Decision}

### Option A: {Name}
**Pros:**
- {Pro 1} -- weight: {high/medium/low}
**Cons:**
- {Con 1} -- weight: {high/medium/low}
**Best when:** {conditions where this is the right choice}
**Worst when:** {conditions where this fails}

### Decision Matrix
| Criterion | Weight | Option A | Option B |
|-----------|--------|----------|----------|
| {criterion 1} | {1-5} | {1-5} | {1-5} |
| **Weighted total** | -- | {sum} | {sum} |

### Verdict
{Which option and why, acknowledging what we give up}
```

### Protocolo do Advogado do Diabo

```
1. State the preferred option clearly
2. Steel-man the OPPOSING option (make the strongest case against your preference)
3. Identify the #1 reason the preferred option could FAIL
4. Identify the #1 reason the opposing option could SUCCEED
5. Check: did we dismiss the alternative too quickly?
6. Final decision with honest acknowledgment of risks
```

### Verificação de Reversibilidade

```
1. Easily reversible (days)   -> Decide quickly
2. Moderately reversible (weeks) -> Research adequately, document
3. Hard to reverse (months)    -> Research thoroughly, prototype
4. Irreversible (public API, data format, lock-in) -> Maximum research
```

---

## 7. Protocolo de Segurança de Dependências

Execute ANTES de instalar qualquer dependência.

### Passos

1. **Encontre a versão estável mais recente** — busque no PyPI/npm/Cargo, nunca use a versão dos dados de treinamento
2. **Verifique a segurança** — NVD, GitHub Advisories, Snyk
3. **Verifique se é mantido** — último release <12 meses, issues ativas, commits recentes
4. **Audite após instalar**

```bash
pip-audit          # Python
npm audit          # Node.js
cargo audit        # Rust
```

### Sinais de Alerta (não instalar)
- Sem release há >12 meses
- CVEs conhecidos sem patch disponível
- Mantenedor único que parou de contribuir
- Contagem de downloads <1K/semana (PyPI) ou <100/semana (npm)
- Licença incompatível

---

## 8. Anti-Padrões

| Anti-Padrão | Errado | Certo |
|-------------|-------|-------|
| Dependência de dados de treinamento | "Com base no meu conhecimento, X é o melhor" | Busque primeiro, depois recomende |
| Fonte única | "Este blog diz que X é melhor" | Cruze 3+ fontes |
| Ignorar datas | "Tutorial diz para usar X v2.0" | Verifique a versão atual primeiro |
| Viés de popularidade | "50k stars = melhor escolha" | Stars medem popularidade, não adequação |
| Vendor como neutro | "AWS diz que Bedrock é o melhor" | Vendor recomenda o próprio produto — sinalize o viés |
| Fechamento prematuro | Achou uma opção → recomenda | Ache alternativas → compare → recomende |
| Esconder pontos negativos | "X é ótimo porque [só prós]" | Reconheça os trade-offs explicitamente |

---

## 9. Quando Parar de Pesquisar

### Orçamentos de Tempo

| Impacto | Tempo máximo | Fontes necessárias |
|--------|----------|----------------|
| Trivial | 5 min | 1 |
| Baixo | 15 min | 2 |
| Médio | 30 min | 3 |
| Alto | 1 hora | 4+ |
| Crítico | 2+ horas | 5+ |

### Pare Quando
- 3+ fontes independentes concordam
- Uma opção domina em todos os critérios importantes
- As últimas 3 fontes não adicionaram informação nova
- Orçamento de tempo excedido
- A decisão é facilmente reversível

---

## Reference Files

- [references/methodology/debate-frameworks.md](references/methodology/debate-frameworks.md) — Frameworks de Debate e Trade-off
- [references/methodology/synthesis-templates.md](references/methodology/synthesis-templates.md) — Templates de Síntese
- [references/methodology/validation-protocol.md](references/methodology/validation-protocol.md) — Protocolo de Validação
- [references/platforms/arxiv.md](references/platforms/arxiv.md) — arXiv e Busca Acadêmica
- [references/platforms/github-search.md](references/platforms/github-search.md) — Busca no GitHub
- [references/platforms/google.md](references/platforms/google.md) — Operadores Avançados de Busca do Google
- [references/platforms/huggingface.md](references/platforms/huggingface.md) — Busca no HuggingFace
- [references/platforms/infrastructure.md](references/platforms/infrastructure.md) — Busca de Infraestrutura
- [references/platforms/pypi-npm.md](references/platforms/pypi-npm.md) — Busca no PyPI e npm
- [references/security/vulnerability-sources.md](references/security/vulnerability-sources.md) — Fontes de Vulnerabilidades e Segurança
