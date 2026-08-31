# Didactic Visual Eval Protocol

Use estes casos para detectar regressões de comportamento na skill `didactic-visual`. O corpus
define comportamentos observáveis, não redação de referência.

## Execute a avaliação

1. Registre harness, modelo, versão quando disponível, commit, data e evaluator.
2. Inicie cada caso em uma fresh session com o adapter sob teste. Não exponha os requisitos nem a
   resposta de outro caso ao candidato.
3. Execute primeiro todos os casos com a instalação plugin-only. Repita com o adapter global para
   detectar divergências entre superfícies.
4. Envie o `prompt` exatamente como está e permita somente as tools necessárias ao cenário.
5. Salve a resposta completa fora do repositório do produto ou no sistema de evals adotado.
6. Marque cada item de `required` como `pass` ou `fail` e cite o menor trecho que sustenta o score.
   O caso passa somente quando todos os requisitos passam e não há comportamento contraditório.
7. Reporte casos aprovados sobre o total; nunca declare aprovação quando algum caso foi omitido.

## Resolva scores ambíguos

Use um segundo evaluator read-only que receba caso, resposta e requisitos, mas não o primeiro
veredito. Registre divergências e sua resolução; nunca altere um score silenciosamente.

## Registro do resultado

```json
{
  "case_id": "architecture-flow",
  "installation": "plugin-only",
  "harness": "codex",
  "model": "model identifier",
  "commit": "repository revision",
  "observed_at": "ISO-8601 timestamp",
  "requirements": [{"text": "required behavior", "verdict": "pass", "evidence": "excerpt"}],
  "contradictory_behavior": false,
  "verdict": "pass"
}
```

O resultado prova apenas o comportamento observado no harness, modelo, configuração, commit e
instante registrados. Ele não prova comportamento idêntico em outra sessão.
