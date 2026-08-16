# Processo Sistemático de Correção de Bugs

## REPRODUZIR > ISOLAR > ESCREVER TESTE > CORRIGIR > VALIDAR > PREVENIR

## Disciplina de evidência (skill `evidence`)

Antes de mudar código, crie um registro de evidência com observações verificadas, hipóteses
concorrentes, desconhecidos e o próximo teste falsificador. Reprodução é evidência de que o sintoma
existe no ambiente observado; não é evidência de causa raiz. Uma correlação, uma mudança de código
próxima ou um teste de regressão passando não estabelecem, por si sós, causalidade nem a ausência
de defeitos relacionados.

Para uma mitigação urgente, compare blast radius, reversibilidade, custo de atraso e telemetria
disponível. Rotule o hotfix imediato separadamente da correção durável, diga qual hipótese ele
endereça, e defina rollback e observações pós-deploy antes de subir.

### Passo 1: REPRODUZIR

**Objetivo:** Disparar o bug de forma confiável.

Documente:
```markdown
## Bug Reproduction

### Environment
- OS: {os}
- Version: {app version}
- Database: {state}

### Steps
1. {step 1}
2. {step 2}
3. {step 3}

### Expected
{what should happen}

### Actual
{what actually happens}

### Frequency
{always / intermittent / specific conditions}
```

**Se você não conseguir reproduzir:**
- Verifique os logs em busca do erro
- Verifique se é específico do ambiente
- Verifique se depende dos dados
- Peça mais detalhes a quem reportou
- NÃO corrija por adivinhação sem reprodução
- Preserve explicações não verificadas como hipóteses em vez de reportá-las como fatos

### Passo 2: ISOLAR

**Técnicas:**

**Busca binária no código:**
```python
# Comment out half the code path
# Does the bug still happen?
# If yes: bug is in the remaining half
# If no: bug is in the commented-out half
# Repeat until found
```

**git bisect:**
```bash
git bisect start
git bisect bad HEAD          # current: has bug
git bisect good v1.2.0       # known good version
# Git checks out a middle commit
# Test it, then:
git bisect good  # or git bisect bad
# Repeat until found
git bisect reset
```

**Logging:**
```python
# Add strategic logging to narrow down
logger.debug("checkpoint_1", data=data)
# ... code ...
logger.debug("checkpoint_2", result=result)
```

### Passo 3: ESCREVER TESTE

```python
def test_order_total_does_not_overflow_with_large_quantities():
    """Regression test for BUG-1234: overflow on large orders."""
    order = Order(items=[Item(price=99999, quantity=99999)])
    # This MUST fail on the current code (before fix)
    assert order.total == Decimal("9999800001")
```

### Passo 4: CORRIGIR

- Corrija a CAUSA RAIZ, não o sintoma
- Alegue causa raiz apenas quando a evidência descarta as hipóteses concorrentes materiais
- Faça a mudança mínima necessária
- NÃO misture com refatoração ou novas funcionalidades
- Se a correção for complexa, adicione um comentário no código explicando o porquê

### Passo 5: VALIDAR

```bash
# 1. Run the regression test
pytest tests/test_order.py::test_order_total_does_not_overflow -v

# 2. Run the full suite
pytest

# 3. Test the original reproduction case manually
```

### Passo 6: PREVENIR

- Esse é um tipo de bug que pode ser detectado por uma regra de linter?
- Devemos adicionar uma restrição de tipo para evitar isso?
- Existem padrões semelhantes em outros lugares que precisam da mesma correção?
- Devemos adicionar monitoramento/alertas para essa condição?
