# Como consultar este backup

Este diretório preserva o modelo anterior da knowledge base. Leia este arquivo antes de
qualquer outro arquivo do backup. Consulte o legado somente quando o usuário pedir.

## Registro da preservação

- Data: {at}
- Motivo: {reason}
- Plano de origem: {plan}
- Arquivos preservados: {files}
- Manifesto: `.manifest.json`
- SHA-256 do manifesto: `{manifest_sha256}`
- Pontos marcados como legado: {legacy_points}

O manifesto registra o caminho original, tamanho em bytes e SHA-256 de cada arquivo.
O backup conserva os bytes; `.obsidian/` e `.trash/` permanecem fora desta operação.
Este arquivo é reservado: não é nota, não recebe validação de nota nem embedding.

## Organização anterior

O bundle usava `work/projects/<projeto>/`, com tópicos em subpastas, índices e logs.
Notas eram arquivos Markdown individuais, frequentemente com datas nos nomes.
O frontmatter tinha `type` livre, `knowledge_type` para o contrato do corpo,
`domain`, `topic`, `id`, `created_at`, `summary`, `tags` e `status`.
Os estados eram `stable`, `draft` e `deprecated`. `generated` identificava produtor e
horário; `provenance` registrava harness, sessão, execução e identidade da máquina.
Campos opcionais incluíam `verified`, `stale_after` e `distillation_key`.

`entities` e `aliases` eram listas; `entity_refs` declarava nomes e alternativas;
`references` guardava URLs e caminhos com seu status; `temporal_refs` guardava datas
com significado e fuso. `occurred_at` podia conter data, instante ou ausência de valor.
Notas eram imutáveis: uma correção criava outra nota com `supersedes` apontando o UUID
anterior. Esse modelo difere das versões congeladas em `.history/` do formato novo.

A identidade de um projeto tinha `knowledge_type: project`, `name`, `aliases`,
`repository_path`, `remote_url` e `default_branch`. O antigo `context.md` podia conter
um retrato legado do projeto e tinha um fluxo próprio de migração.
Os session records eram JSON mutáveis em diretórios de sessões, com provenance e
referências ao transcript. Permanecem aqui como legado; novos registros desse tipo
não são criados. Transcripts originais continuam sob responsabilidade do harness.

## Ler sem alterar

Busque explicitamente com `--legacy`. Resolva links antigos acrescentando `backup/`
aos caminhos relativos ao bundle. O status legado no Qdrant não altera o conteúdo
original e não exige gerar embeddings novamente. Um registro antigo não comprova
que a informação continua válida; confira o estado atual antes de reutilizá-la.

## Promover para o modelo atual

Crie uma nota nova com UUID novo e versão 1. Use o template atual do tipo escolhido,
conteúdo em pt-BR, entidades declaradas e comprovadas, e uma seção `Sources` apontando
para o arquivo de origem no backup. Proponha caminho e conteúdo ao usuário em uma única
revisão; somente após aprovação explícita execute `kb approve`. Preserve o arquivo
original do backup. Nunca promova todas as notas automaticamente.
