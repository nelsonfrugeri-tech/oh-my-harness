# Code craft — padrões invioláveis

Fonte única das regras de qualidade de código. A skill `implement` referencia isto no corpo; a skill `review` transforma cada regra em item de checklist. Ative **antes de escrever, modificar ou revisar qualquer código**.

Os exemplos são em Python por concisão; o princípio é agnóstico de linguagem. Para o "como" concreto de tipagem, veja `python/references/type-system.md` e `typescript/references/type-system.md`.

---

## 1. Tipagem total, sempre

Nenhum parâmetro, retorno ou atributo sem tipo. `Any` só com justificativa explícita no código.

```python
# BAD
def parse(data):
    return data.get("id")

# GOOD
def parse(data: Mapping[str, object]) -> UserId:
    return UserId(str(data["id"]))
```

O tipo é um contrato verificável, não documentação. O typecheck (`mypy`, `tsc --noEmit`) roda no quality gate.

---

## 2. Imutabilidade por padrão

`frozen=True`, estruturas imutáveis, sem mutação in-place, sem estado compartilhado mutável. Mutabilidade é permitida só quando é o núcleo do que se está modelando, e fica isolada.

```python
# BAD — mutação in-place, estado partilhado
class Cart:
    def __init__(self) -> None:
        self.items: list[Item] = []
    def add(self, item: Item) -> None:
        self.items.append(item)

# GOOD — transformação retorna novo valor
@dataclass(frozen=True, slots=True)
class Cart:
    items: tuple[Item, ...] = ()
    def with_item(self, item: Item) -> "Cart":
        return replace(self, items=(*self.items, item))
```

---

## 3. Superfície pública mínima

Um conceito público por módulo — geralmente uma classe **ou** função pública, mais seu tipo de resultado. Mais que isso exige justificativa específica. O resto é privado (`_prefixo`). O objetivo é superfície mínima + alta coesão.

---

## 4. Funções e arquivos pequenos

- **Função:** alvo ≤ 15 linhas, teto ~25. Se cresceu, **quebre** — extraia por responsabilidade.
- **Arquivo/módulo:** alvo ≤ 120 linhas. Arquivo grande costuma ter mais de uma responsabilidade; separe.

O driver da quebra é **coesão**, não a contagem de linha. O tamanho pequeno é *sintoma* de bom design, não o objetivo — não fragmente em indireção inútil (um arquivo por função trivial). Coisas que mudam juntas ficam juntas.

Estes limites viram config de linter: `ruff` `C901` (complexity), `PLR0915` (statements), `PLR0912` (branches).

---

## 5. Guard clauses no lugar de aninhamento

Aninhamento ≤ 3 níveis. Trate casos de borda no topo com **early returns** e mantenha o caminho feliz raso e linear. Não force um único return à custa de aninhamento — clareza de fluxo vence contagem de returns.

```python
# BAD — caminho feliz enterrado, single-exit forçado
def charge(order: Order) -> Result:
    result = FAILURE
    if order.is_valid:
        if order.has_funds:
            result = do_charge(order)
    return result

# GOOD — guard clauses, caminho feliz raso
def charge(order: Order) -> Result:
    if not order.is_valid:
        return invalid(order)
    if not order.has_funds:
        return declined(order)
    return do_charge(order)
```

---

## 6. Design pattern no lugar de cadeias de condicional

Mais de 3 `if/elif` no mesmo nível decidindo por tipo/estado → troque por polymorphism, strategy, dispatch dict ou `match`. Uma cadeia longa de condicional é cheiro de um tipo faltando.

```python
# BAD
if kind == "email": send_email(msg)
elif kind == "sms": send_sms(msg)
elif kind == "push": send_push(msg)
elif kind == "webhook": send_webhook(msg)

# GOOD — dispatch por tabela
CHANNELS: Mapping[Kind, Channel] = {
    "email": EmailChannel(), "sms": SmsChannel(),
    "push": PushChannel(), "webhook": WebhookChannel(),
}
CHANNELS[kind].send(msg)
```

---

## 7. Evite retornar `None`

Exceção para erro, coleção vazia para "nada", `Optional[T]` só quando a ausência é semântica real. Nunca `None` como código de erro silencioso.

```python
# BAD — None ambíguo (não achou? falhou? vazio?)
def find_user(uid: UserId) -> User | None: ...

# GOOD — ausência explícita OU exceção
def find_user(uid: UserId) -> User:
    """Raises UserNotFound if absent."""
def find_users(q: Query) -> tuple[User, ...]:  # empty tuple, never None
```

---

## 8. Poucos parâmetros

≤ 4 parâmetros. Mais que isso, agrupe num dataclass (Introduce Parameter Object). Linter: `ruff` `PLR0913`.

```python
# BAD
def create_report(title, author, start, end, fmt, locale, tz): ...

# GOOD
@dataclass(frozen=True)
class ReportSpec:
    title: str; author: str; window: DateRange
    fmt: Format; locale: Locale; tz: ZoneInfo
def create_report(spec: ReportSpec) -> Report: ...
```

---

## 9. Comentário explica o *porquê*, nunca o *o quê*

Se o código já diz o que faz, não comente — nomeie melhor. Comentário justifica decisões não-óbvias, trade-offs, referências. Docstrings em inglês.

```python
# BAD — narra o óbvio
i += 1  # increment i

# GOOD — explica o não-óbvio
# Retry with jitter: the upstream rate-limiter buckets by 100ms window.
sleep(base_delay + random_jitter())
```

---

## 10. SOLID e patterns na medida certa

Aplique o padrão **certo**, nunca generalização especulativa (YAGNI). Abstração sem segundo caso concreto é dívida, não design. Prefira o simples que resolve hoje ao genérico que talvez sirva amanhã.

---

## Quality gate — obrigatório ao terminar

Nunca declare uma tarefa concluída sem rodar o pipeline de qualidade do projeto e corrigir o que falhar:

1. **Format** — `black` / `ruff format` / `biome format` / `prettier`
2. **Lint** — `ruff check` / `biome lint` / `eslint`
3. **Typecheck** — `mypy` / `tsc --noEmit`
4. **Test** — `pytest` / `vitest`

**Descoberta do comando** (nesta ordem, nunca hardcode): target de Makefile (`make lint`, `make format`, `make check`) → config do projeto (`pyproject.toml`, `biome.json`, scripts do `package.json`, `.pre-commit-config.yaml`) → default da linguagem. Se o projeto define `make lint`, é isso que roda.
