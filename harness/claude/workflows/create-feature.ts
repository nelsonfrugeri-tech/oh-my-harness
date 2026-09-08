export const meta = {
  name: 'create-feature',
  description: 'Pipeline de criação de feature após refinamento técnico: user_history (tech-pm) → development (software-engineer ou ai-engineer) → validation_loop[evidence-reviewer] (max 3 iterações) → open_pr (ou escalação ao usuário). Refinamento técnico interativo é feito antes pelo skill /feature.',
  whenToUse: 'Após o refinamento técnico interativo estar consolidado. Recebe args: { featureName, featureSlug, refinementContent, evidence, hypotheses, unknowns, track }. Track = "software-engineer" ou "ai-engineer" decide quem implementa.',
  phases: [
    { title: 'user_history', detail: 'tech-pm escreve user story e abre item no sistema de gerenciamento (GitHub Issues por padrão); salva cópia em <feature>/user_history/user_history.md' },
    { title: 'development', detail: 'software-engineer ou ai-engineer (conforme track) implementa a feature seguindo refinamento + user_history' },
    { title: 'validation', detail: 'evidence-reviewer valida a implementação em modo somente-leitura: roda os testes e gates do projeto e reporta comando e saída de cada verificação; loop até pass ou max 3 iterações' },
    { title: 'fix_iteration', detail: 'software-engineer/ai-engineer corrige os problemas reportados pelo evidence-reviewer, então re-valida' },
    { title: 'open_pr', detail: 'Se validação passou: software-engineer/ai-engineer abre PR no GitHub com template padronizado. Se 3 loops falharem: retorna estado para o usuário resolver.' },
  ],
}

const featureName = args?.featureName
const featureSlug = args?.featureSlug
const refinementContent = args?.refinementContent
const refinementEvidence = Array.isArray(args?.evidence) ? args.evidence : []
const refinementHypotheses = Array.isArray(args?.hypotheses) ? args.hypotheses : []
const refinementUnknowns = Array.isArray(args?.unknowns) ? args.unknowns : []
const track = args?.track === 'ai-engineer' ? 'ai-engineer' : 'software-engineer'
const repo = args?.repo
const docsBase = featureSlug

if (!featureName || !featureSlug || !refinementContent) {
  throw new Error('create-feature precisa de args: { featureName: string, featureSlug: string, refinementContent: string, track?: "software-engineer"|"ai-engineer", repo?: "owner/name" }')
}

const MAX_ITERATIONS = 3

const USER_HISTORY_SCHEMA = {
  type: 'object',
  required: ['title', 'asA', 'iWant', 'soThat', 'acceptanceCriteria', 'definitionOfDone', 'evidence', 'hypotheses', 'unknowns', 'markdown'],
  properties: {
    title: { type: 'string' },
    asA: { type: 'string' },
    iWant: { type: 'string' },
    soThat: { type: 'string' },
    acceptanceCriteria: {
      type: 'array',
      items: {
        type: 'object',
        required: ['scenario', 'given', 'when', 'then'],
        properties: {
          scenario: { type: 'string' },
          given: { type: 'string' },
          when: { type: 'string' },
          then: { type: 'string' },
        },
      },
    },
    definitionOfDone: { type: 'array', items: { type: 'string' } },
    evidence: { type: 'array', items: { type: 'string' }, description: 'Verified facts, derived results, and inspectable sources' },
    hypotheses: { type: 'array', items: { type: 'string' }, description: 'Falsifiable assumptions that affect the feature decision' },
    unknowns: { type: 'array', items: { type: 'string' }, description: 'Missing information and its decision impact' },
    issueUrl: { type: 'string', description: 'URL do issue criado no sistema de gerenciamento, ou string vazia se não conseguiu criar' },
    markdown: { type: 'string', description: 'Markdown completo da user history (para gravar em user_history.md)' },
  },
}

const IMPLEMENTATION_SCHEMA = {
  type: 'object',
  required: ['summary', 'filesChanged', 'commands', 'evidence', 'hypotheses', 'unknowns', 'verdict'],
  properties: {
    summary: { type: 'string', description: 'O que foi implementado e por quê' },
    filesChanged: { type: 'array', items: { type: 'string' } },
    commands: { type: 'array', items: { type: 'string' }, description: 'Comandos para rodar/testar localmente' },
    evidence: { type: 'array', items: { type: 'string' }, description: 'Executed observations and their scope' },
    hypotheses: { type: 'array', items: { type: 'string' }, description: 'Hypotheses tested or still open' },
    unknowns: { type: 'array', items: { type: 'string' }, description: 'Remaining unverified risks' },
    branch: { type: 'string', description: 'Nome do branch git criado, se aplicável' },
    verdict: { type: 'string', enum: ['done', 'blocked'], description: 'done = pronto para validação; blocked = usuário precisa intervir' },
    blockedReason: { type: 'string' },
  },
}

const VALIDATION_RESULT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'checks', 'hypotheses', 'unknowns', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    summary: { type: 'string' },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        required: ['command', 'output', 'proves'],
        properties: {
          command: { type: 'string', description: 'Comando exato executado, com cwd quando não for a raiz do repositório' },
          output: { type: 'string', description: 'Saída literal e status de saída do comando' },
          proves: { type: 'string', description: 'O que essa execução estabelece, e em que escopo' },
        },
      },
    },
    hypotheses: { type: 'array', items: { type: 'string' }, description: 'Causal or behavioral explanations not established by the executed checks' },
    unknowns: { type: 'array', items: { type: 'string' }, description: 'Material cases, environments, or gates left unexecuted' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'description'],
        properties: {
          severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] },
          description: { type: 'string' },
          reproSteps: { type: 'string' },
        },
      },
    },
  },
}

const PR_SCHEMA = {
  type: 'object',
  required: ['prUrl', 'title', 'body'],
  properties: {
    prUrl: { type: 'string' },
    title: { type: 'string' },
    body: { type: 'string' },
  },
}

const implementerAgentType = track
const implementerLabel = track

phase('user_history')
log(`Feature: ${featureName} (${featureSlug}) — track: ${track}`)

const userHistory = await agent(
  `Você é o tech-pm. Use o refinamento técnico abaixo como base e produza a user history desta feature.

# Feature
${featureName}

# Refinamento técnico (refinement_tech.md)
${refinementContent}

# Registro de evidência do refinamento
Verificado ou derivado: ${JSON.stringify(refinementEvidence)}
Hipóteses: ${JSON.stringify(refinementHypotheses)}
Desconhecidos: ${JSON.stringify(refinementUnknowns)}

# Tarefas
1. Escreva uma user history no formato INVEST: título, "As a / I want / So that", critérios de aceitação Given/When/Then (3-6 cenários), Definition of Done.
2. Crie um issue/ticket no repositório ${repo || '<descobrir via git remote>'} via a capability \`code-host\` (carregue a tool concreta via ToolSearch — ver harness/claude/CLAUDE.md). Se \`code-host\` não estiver plugada ou falhar, deixe issueUrl como string vazia e prossiga.
3. Use a skill \`evidence\`. Preserve evidência verificada, hipóteses falsificáveis, desconhecidos e a proveniência quantitativa; nunca invente uma métrica.
4. Devolva tudo no schema, incluindo o markdown completo pronto para ser salvo em ${docsBase}/user_history/user_history.md.

Grave o markdown final em disco em \`${docsBase}/user_history/user_history.md\`. Peça ao agent \`knowledge-base\` para registrar um resumo; se a knowledge base não estiver disponível, siga sem ela.`,
  { agentType: 'tech-pm', label: 'tech-pm:user_history', phase: 'user_history', schema: USER_HISTORY_SCHEMA },
)

phase('development')

let implementation = await agent(
  `Você é o ${implementerAgentType}. Implemente a feature abaixo seguindo refinamento + user history.

# Feature
${featureName} (slug: ${featureSlug})

# Refinamento técnico
${refinementContent}

# User history
${userHistory.markdown}

# Definition of Done
${(userHistory.definitionOfDone || []).map((d, i) => `${i + 1}. ${d}`).join('\n')}

# Tarefas
1. Crie um branch git: feature/${featureSlug}
2. Implemente o código necessário, com testes mínimos.
3. Garanta que o build/lint/tests locais passam.
4. Use a skill \`evidence\`. Retorne observações executadas com escopo, hipóteses testadas e desconhecidos restantes; testes passando provam apenas os casos exercitados.
5. Retorne resumo, arquivos alterados, comandos de verificação, nome do branch.

Se houver bloqueio que exige decisão do usuário, retorne verdict="blocked" com blockedReason claro.`,
  { agentType: implementerAgentType, label: `${implementerLabel}:implement`, phase: 'development', schema: IMPLEMENTATION_SCHEMA },
)

if (implementation.verdict === 'blocked') {
  log(`${implementerLabel} bloqueado: ${implementation.blockedReason}`)
  return {
    status: 'blocked_at_development',
    featureName,
    featureSlug,
    track,
    userHistory,
    implementation,
    nextStep: 'Usuário precisa resolver o bloqueio antes de prosseguir.',
  }
}

let iteration = 0
let validationResult = null
let validationPassed = false
const validationHistory = []

while (iteration < MAX_ITERATIONS) {
  iteration++
  phase('validation')
  log(`Iteração ${iteration}/${MAX_ITERATIONS} — evidence-reviewer`)

  validationResult = await agent(
    `Você é o evidence-reviewer. Valide a implementação abaixo em modo **somente-leitura**.

# Feature
${featureName}

# User history
${userHistory.markdown}

# Refinamento técnico
${refinementContent}

# Implementação (iteração ${iteration})
${JSON.stringify(implementation, null, 2)}

# Tarefas
1. Descubra os comandos de qualidade do projeto (build, lint, typecheck, testes, gates) na configuração do repositório; não presuma um comando.
2. Execute-os com Bash e registre comando, saída literal e o que cada execução estabelece. Experimentos que exijam mutação rodam numa cópia descartável fora do repositório.
3. Confronte cada critério de aceitação da user history com uma verificação executada. Critério sem verificação vira \`unknowns\`, nunca pass.
4. Nunca edite arquivos, commite, faça push ou merge; você não é o dono da mudança.

# Veredito
Use a skill \`evidence\`. Preserve explicações sem sustentação como hipóteses e escope toda alegação ao ambiente e aos casos executados; teste passando prova os casos exercitados, não ausência de defeito.
pass apenas se TODOS os critérios de aceitação foram verificados por execução e sem blockers. Caso contrário fail + lista de issues com severidade e repro.`,
    { agentType: 'evidence-reviewer', label: `evidence-reviewer:iter${iteration}`, phase: 'validation', schema: VALIDATION_RESULT_SCHEMA },
  )

  validationHistory.push({ iteration, validation: validationResult })

  validationPassed = validationResult?.verdict === 'pass'

  log(`Iteração ${iteration}: evidence-reviewer=${validationResult?.verdict ?? 'erro'}`)

  if (validationPassed) break

  if (iteration >= MAX_ITERATIONS) break

  phase('fix_iteration')
  log(`Iteração ${iteration} falhou. ${implementerLabel} vai corrigir.`)

  const validationIssues = (validationResult?.issues || []).map(i => `[${i.severity}] ${i.description}${i.reproSteps ? ` (repro: ${i.reproSteps})` : ''}`).join('\n')

  implementation = await agent(
    `Você é o ${implementerAgentType}. A iteração ${iteration} de validação falhou. Corrija os problemas abaixo.

# Implementação atual
${JSON.stringify(implementation, null, 2)}

# Problemas reportados pelo evidence-reviewer
${validationIssues || '(nenhum)'}

# Tarefa
Corrija no mesmo branch. Re-rode build/lint/tests. Retorne summary atualizado com o que mudou nesta correção, lista de arquivos alterados (todos, não só os desta correção), comandos.

Se algum problema não puder ser resolvido sem decisão do usuário, retorne verdict="blocked" com blockedReason específico.`,
    { agentType: implementerAgentType, label: `${implementerLabel}:fix${iteration}`, phase: 'fix_iteration', schema: IMPLEMENTATION_SCHEMA },
  )

  if (implementation.verdict === 'blocked') {
    return {
      status: 'blocked_at_fix',
      featureName,
      featureSlug,
      track,
      userHistory,
      implementation,
      validationHistory,
      iterationsUsed: iteration,
      nextStep: 'Usuário precisa resolver o bloqueio.',
    }
  }
}

if (!validationPassed) {
  log(`Esgotou ${MAX_ITERATIONS} iterações sem pass. Escalando para o usuário.`)
  return {
    status: 'failed_max_iterations',
    featureName,
    featureSlug,
    track,
    userHistory,
    implementation,
    validationHistory,
    iterationsUsed: iteration,
    nextStep: `Após ${MAX_ITERATIONS} iterações o evidence-reviewer ainda reporta issues. Revisar manualmente.`,
  }
}

phase('open_pr')
log('Validação aprovada. Abrindo PR.')

const pr = await agent(
  `Você é o ${implementerAgentType}. Abra um Pull Request no GitHub para esta feature.

# Feature
${featureName} (slug: ${featureSlug})

# Repositório
${repo || '(descobrir via git remote)'}

# Branch
${implementation.branch || `feature/${featureSlug}`}

# User history (link)
${userHistory.issueUrl || '(sem issue link)'}

# Iterações de validação
evidence-reviewer: ${validationResult?.verdict}, iterações usadas: ${iteration}/${MAX_ITERATIONS}

# Padrão de descrição do PR (use este template exato)
## Resumo
<2-4 linhas sobre o que muda e por quê — derive da user history>

## Mudanças
- <bullet points dos arquivos/módulos principais>

## User History
- Issue: ${userHistory.issueUrl || '<n/a>'}
- Critérios de aceitação cobertos:
${(userHistory.acceptanceCriteria || []).map(ac => `  - ${ac.scenario}`).join('\n')}

## Evidências
${(validationResult?.checks || []).map(c => `- \`${c.command}\` — ${c.proves}`).join('\n')}

## Status da evidência
- Observações verificadas: <cite os paths de validação exatos e os comandos executados>
- Hipóteses e desconhecidos: <preserve o que a validação não estabeleceu>

## Como testar
${(implementation.commands || []).map(c => `\`\`\`\n${c}\n\`\`\``).join('\n')}

## Checklist
- [x] Gates do projeto executados pelo evidence-reviewer
- [x] Critérios de aceitação confrontados com verificação executada
- [x] Hipóteses e desconhecidos preservados no relatório de validação

# Tarefa
Abra o Pull/Merge Request via a capability \`code-host\` (carregue a tool concreta via ToolSearch — ver harness/claude/CLAUDE.md). Faça push do branch antes se necessário. Retorne prUrl, title e body usados.`,
  { agentType: implementerAgentType, label: `${implementerLabel}:open_pr`, phase: 'open_pr', schema: PR_SCHEMA },
)

return {
  status: 'success',
  featureName,
  featureSlug,
  track,
  userHistory,
  implementation,
  validationHistory,
  iterationsUsed: iteration,
  pr,
}
