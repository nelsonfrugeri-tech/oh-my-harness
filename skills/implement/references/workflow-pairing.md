# Pair Programming e Mob Programming

## Estilos de Pair Programming

### Driver-Navigator (Clássico)

```
Driver:    Writes code, handles the tactical
Navigator: Watches, thinks strategically, catches issues
           ↕ Switch every 15-25 minutes
```

**Ideal para:** Desenvolvimento geral, alternativa ao code review.

### Ping-Pong (nativo do TDD)

```
Developer A: Writes a failing test
Developer B: Makes it pass, then writes the next failing test
Developer A: Makes it pass, then writes the next failing test
             ↕ Natural switching on each RED-GREEN cycle
```

**Ideal para:** Praticar TDD, aprendizado, contribuição equilibrada.

### Strong-Style

```
Navigator: Dictates exactly what to type
Driver:    Types only what is dictated, asks questions
           "For an idea to go from your head into the computer,
            it MUST go through someone else's hands"
```

**Ideal para:** Ensino, onboarding, transferência de conhecimento.

## Quando Fazer Par

| Situação | Fazer Par? | Por quê |
|-----------|-------|-----|
| Onboarding | Sim | Transferência de conhecimento |
| Lógica complexa | Sim | Duas mentes, menos bugs |
| Travado > 30 min | Sim | Perspectiva nova |
| CRUD rotineiro | Não | Complexidade insuficiente |
| Spikes | Talvez | Depende da familiaridade |
| Debugging | Sim | Rubber duck + expertise |

## Mob Programming

### Preparação
- Uma tela, um teclado
- Time inteiro presente
- Rotacione o driver a cada 10-15 minutos
- Timer visível para todos

### Papéis
- **Driver:** Digita APENAS o que o mob diz
- **Navigator(s):** Direcionam o driver, discutem a abordagem
- **Facilitator:** Gerencia a rotação, mantém o foco, garante a participação

### Regras
1. Trate as ideias de todos com respeito
2. "Sim, e..." em vez de "Não, mas..."
3. Se travar, faça uma pausa de 5 minutos
4. Pausas a cada 50 minutos
5. Todos participam (sem espectadores)
6. Confie no processo — parece lento, mas produz qualidade

### Quando Fazer Mob
- Decisões de arquitetura que todo o time precisa entender
- Integrações complexas que envolvem múltiplos subsistemas
- Alinhamento do time sobre novos padrões ou convenções
- Spikes onde o conhecimento coletivo é valioso
- Code review de mudanças críticas (revisão ao vivo)
