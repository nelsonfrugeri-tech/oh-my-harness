# Técnicas de Questionamento

## Os 5 Porquês

Para cada requisito, pergunte "por quê" até chegar à necessidade raiz.

```
Requirement: "Add a cache to the API"
Why? → "The API is slow"
Why? → "Database queries take too long"
Why? → "We're doing full table scans"
Why? → "No indexes on the filter columns"
Why? → "Schema was created without performance analysis"

Real solution: Add indexes, not a cache.
```

## Categorias de Perguntas

### Perguntas de Escopo
- O que exatamente isso deve alterar?
- O que NÃO deve mudar?
- Há funcionalidades relacionadas afetadas?
- Qual é a implementação mínima viável?

### Perguntas de Comportamento
- Quais são as entradas e as saídas esperadas?
- O que acontece com entrada inválida?
- O que acontece com entrada vazia/nula?
- O que acontece sob acesso concorrente?
- Quais são as condições de contorno?

### Perguntas de Restrição
- Quais são os requisitos de performance? (latência, throughput)
- Quais são as implicações de segurança?
- Qual compatibilidade retroativa deve ser mantida?
- Em quais ambientes isso deve funcionar?

### Perguntas de Dependência
- Com qual código existente isso interage?
- De quais serviços externos isso depende?
- São necessárias migrações de banco de dados?
- São necessárias mudanças de configuração?

### Perguntas de Aceitação
- Como saberemos que isso está concluído?
- Quem aprova a implementação?
- Quais testes provam que funciona?
- O que "pronto para produção" significa para isso?

## Quando Perguntar ao Usuário

Pergunte quando:
- O requisito é ambíguo
- Existem múltiplas interpretações válidas
- O escopo não está claro
- Trade-offs exigem uma decisão de produto

NÃO pergunte quando:
- A resposta está no código/docs
- É uma decisão puramente técnica
- O requisito é claro e não ambíguo
