# Self-Check Pré-Submissão

## Antes de Abrir um PR

### Qualidade de Código
- [ ] Todos os testes passam localmente
- [ ] Nenhum statement de debug/print deixado para trás
- [ ] Nenhum código comentado
- [ ] Nenhum TODO sem uma issue vinculada
- [ ] Nenhum valor hardcoded que deveria ser config
- [ ] O tratamento de erros cobre os edge cases

### Segurança
- [ ] Nenhum segredo/credencial no código
- [ ] Validação de input nas fronteiras
- [ ] Nenhum vetor de SQL injection
- [ ] Nenhum vetor de XSS (se for frontend)

### Testes
- [ ] O código novo tem testes
- [ ] Edge cases cobertos (vazio, nulo, limite)
- [ ] Caminhos de erro testados
- [ ] Os testes são determinísticos (sem flaky)

### Documentação
- [ ] CHANGELOG atualizado
- [ ] README atualizado (se o comportamento mudou)
- [ ] Lógica complexa tem comentários inline
- [ ] API pública documentada

### Higiene de Git
- [ ] Os commits são unidades lógicas (não "fix" ou "wip")
- [ ] A branch está rebaseada na main mais recente
- [ ] Nenhum merge commit na feature branch
- [ ] A descrição do PR explica o PORQUÊ, não só o O QUÊ

### Performance
- [ ] Nenhuma query N+1 introduzida
- [ ] Nenhuma coleção sem limite em memória
- [ ] Paginação para endpoints de listagem
