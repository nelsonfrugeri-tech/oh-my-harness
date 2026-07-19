# Langfuse

## Observabilidade de LLM

### O que rastrear
- Template de prompt + variáveis
- Modelo, temperature, max_tokens
- Contagem de tokens de entrada/saída
- Latência (TTFT, total)
- Custo por requisição
- Notas de feedback do usuário

### Integração
```python
from langfuse import Langfuse
langfuse = Langfuse()

trace = langfuse.trace(name="chat", user_id=user_id)
generation = trace.generation(
    name="llm-call",
    model="claude-sonnet-4-6",
    input=messages,
    output=response.content,
    usage={"input": input_tokens, "output": output_tokens}
)
```

### Avaliação
- Avaliação feita por modelo (LLM-as-judge)
- Fluxos de anotação humana
- Teste A/B de variantes de prompt

### Versão: Langfuse 3.x (estável em 2026, self-hosted ou cloud)
