# Checklist de Code Review Python

Checklist detalhado para code review de Python. 25 verificações em 7 categorias.

---

## Como Usar

Para cada arquivo Python modificado:
1. Percorra as categorias abaixo sequencialmente
2. Marque [x] quando o item for verificado
3. Se encontrar uma violação, escreva um comentário com: verificação violada, severidade típica, correção de código

A severidade é indicativa. Use o bom senso conforme o contexto.

---

## Segurança

### [ ] 1. Secrets e Configuração
**Verificar:**
- Nenhuma API key, token ou senha hardcoded
- Configuração vem de variáveis de ambiente
- Use pydantic-settings ou similar

**Severidade típica:** BLOCKER

---

### [ ] 2. Validação de Entrada Externa
**Verificar:**
- Dados de APIs, requests, arquivos são validados
- Use Pydantic para schemas
- Campos obrigatórios, tipos, validações customizadas

**Severidade típica:** MAJOR

---

### [ ] 3. Prevenção de SQL Injection
**Verificar:**
- Queries parametrizadas (não concatenação de strings)
- Use ORM ou prepared statements
- Sem f-strings em SQL

**Severidade típica:** BLOCKER

---

### [ ] 4. Autenticação e Autorização
**Verificar:**
- Endpoints protegidos quando necessário
- Ownership/permissões verificados
- Validação de token adequada

**Severidade típica:** BLOCKER (endpoints públicos) / MAJOR (interno)

---

### [ ] 5. Dados Sensíveis em Logs
**Verificar:**
- Nenhuma senha, token, PII em logs
- Logging estruturado sem dados sensíveis
- Bodies de request/response sanitizados

**Severidade típica:** BLOCKER

---

## Performance

### [ ] 6. N+1 Queries
**Verificar:**
- Nenhum loop com queries a DB dentro
- Eager loading de relacionamentos
- JOINs em vez de múltiplas queries

**Severidade típica:** MAJOR

---

### [ ] 7. Algoritmos Eficientes
**Verificar:**
- Complexidade algorítmica (evitar O(n²) ou pior em hot paths)
- Estruturas de dados apropriadas
- Operações caras fora de loops

**Severidade típica:** MINOR / MAJOR (se em hot path)

---

### [ ] 8. Gerenciamento de Recursos
**Verificar:**
- Context managers para arquivos, conexões, locks
- Sem memory leaks (caches limitados, referências limpas)
- Recursos liberados corretamente

**Severidade típica:** BLOCKER (leaks confirmados) / MAJOR (suspeitos)

---

## Testes

### [ ] 9. Cobertura de Testes
**Verificar:**
- Código crítico tem testes (auth, pagamento, dados)
- Novos endpoints/features têm testes
- Cobertura >60% (geral), >80% (core), 100% (crítico)

**Severidade típica:** BLOCKER (código crítico sem testes) / MAJOR (cobertura <50%)

---

### [ ] 10. Qualidade dos Testes
**Verificar:**
- Testes não são frágeis (sem sleep, sem IDs/timestamps hardcoded)
- Edge cases testados
- Asserções específicas e claras

**Severidade típica:** MINOR

---

## Qualidade de Código

### [ ] 11. Type Hints
**Verificar:**
- Parâmetros de função tipados
- Retornos de função tipados
- Variáveis complexas tipadas
- Tipos modernos usados (`list[str]` e não `List[str]`)

**Severidade típica:** MINOR (funções privadas) / MAJOR (APIs públicas)

---

### [ ] 12. Tratamento de Erros
**Verificar:**
- Try/except em operações que podem falhar
- Exceções específicas (não `Exception` genérica)
- Erros logados adequadamente
- Cleanup em `finally` ou context managers

**Severidade típica:** BLOCKER (operações críticas) / MAJOR (APIs) / MINOR (geral)

---

### [ ] 13. Logging Estruturado
**Verificar:**
- Logs em operações críticas
- Contexto incluído (user_id, request_id, order_id)
- Níveis apropriados (info/warning/error)
- Logging estruturado (JSON) preferido

**Severidade típica:** MAJOR (APIs e serviços) / MINOR (código interno)

---

### [ ] 14. Docstrings
**Verificar:**
- APIs públicas documentadas
- Funções complexas explicadas
- Parâmetros e retornos descritos
- Exemplos quando necessário

**Severidade típica:** MAJOR (APIs públicas) / MINOR (complexas) / NIT (simples)

---

### [ ] 15. Nomeação
**Verificar:**
- Nomes revelam a intenção
- Convenções seguidas (snake_case para funções, PascalCase para classes)
- Sem abreviações obscuras
- Consistência dentro do módulo

**Severidade típica:** MINOR (variáveis) / MAJOR (APIs públicas)

---

### [ ] 16. Princípio da Responsabilidade Única
**Verificar:**
- Função faz uma coisa
- <20-30 linhas idealmente
- Pode ser testada isoladamente
- Nome não contém "and" (process_AND_send_AND_update)

**Severidade típica:** MINOR / MAJOR (se muito complexa)

---

### [ ] 17. DRY (Don't Repeat Yourself)
**Verificar:**
- Sem código duplicado
- Lógica repetida extraída para funções
- Padrões identificados e abstraídos

**Severidade típica:** MINOR

---

### [ ] 18. Complexidade Ciclomática
**Verificar:**
- Pontos de decisão razoáveis (<10 ideal, <15 aceitável)
- If/loops aninhados minimizados
- Função pode ser dividida se muito complexa

**Severidade típica:** MINOR (>10) / MAJOR (>15)
**Ferramenta:** `radon cc --min C`

---

### [ ] 19. Imports Organizados
**Verificar:**
- Ordem: stdlib → third-party → local
- Sem imports não usados
- Sem star imports (`import *`)
- Um import por linha

**Severidade típica:** NIT
**Ferramenta:** `ruff check --select I`

---

## Arquitetura

### [ ] 20. Separação de Responsabilidades
**Verificar:**
- Models não têm lógica de negócio
- Controllers/endpoints são finos
- Services contêm a lógica
- Repositories isolam o acesso a dados

**Severidade típica:** MINOR / MAJOR (violação séria)

---

### [ ] 21. Injeção de Dependência
**Verificar:**
- Dependências injetadas, não importadas diretamente
- Fácil de testar com mocks
- Configuração vem de fora

**Severidade típica:** MINOR

---

## Configuração e Dependências

### [ ] 22. Dependências Fixadas
**Verificar:**
- Versões fixadas (requirements.txt ou poetry.lock)
- Sem ranges de versão amplos demais
- Dependências de dev separadas

**Severidade típica:** MAJOR (produção) / MINOR (dev)

---

### [ ] 23. Async/Await Correto
**Verificar:**
- Operações I/O-bound usam async
- Não bloqueia o event loop
- Await em operações assíncronas

**Severidade típica:** MAJOR (se bloquear o event loop) / MINOR (performance)

---

## Documentação

### [ ] 24. README Atualizado
**Verificar:**
- Instruções de setup refletem as mudanças
- Novas dependências documentadas
- Novos endpoints/features descritos

**Severidade típica:** MINOR

---

### [ ] 25. CHANGELOG Atualizado
**Verificar:**
- Breaking changes documentadas
- Novas features listadas
- Formato consistente

**Severidade típica:** NIT

---

## Ferramentas de Automação

```bash
# Type checking
mypy src/

# Linting
ruff check .

# Security
bandit -r src/

# Complexity
radon cc src/ --min C

# Coverage
pytest --cov=src --cov-report=term-missing

# Imports
ruff check --select I
```
