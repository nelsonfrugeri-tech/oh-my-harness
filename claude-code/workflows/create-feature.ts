export const meta = {
  name: 'create-feature',
  description: 'Pipeline de criação de feature após refinamento técnico: user_history (tech-pm) → development (developer ou ai-engineer) → validation_loop[qa+sre] (max 3 iterações) → open_pr (ou escalação ao usuário). Refinamento técnico interativo é feito antes pelo skill /feature.',
  whenToUse: 'Após o refinamento técnico interativo estar consolidado. Recebe args: { featureName, featureSlug, refinementContent, evidence, hypotheses, unknowns, track }. Track = "developer" ou "ai-engineer" decide quem implementa.',
  phases: [
    { title: 'user_history', detail: 'tech-pm escreve user story e abre item no sistema de gerenciamento (GitHub Issues por padrão); salva cópia em <feature>/user_history/user_history.md' },
    { title: 'development', detail: 'developer ou ai-engineer (conforme track) implementa a feature seguindo refinamento + user_history' },
    { title: 'validation', detail: 'qa (funcional + e2e) e sre (infra + load + stress) em paralelo, gravam evidências em <feature>/validation/*.md; loop até pass ou max 3 iterações' },
    { title: 'fix_iteration', detail: 'developer/ai-engineer corrige problemas reportados por qa/sre, então re-valida' },
    { title: 'open_pr', detail: 'Se validação passou: developer/ai-engineer abre PR no GitHub com template padronizado. Se 3 loops falharem: retorna estado para o usuário resolver.' },
  ],
}

const featureName = args?.featureName
const featureSlug = args?.featureSlug
const refinementContent = args?.refinementContent
const refinementEvidence = Array.isArray(args?.evidence) ? args.evidence : []
const refinementHypotheses = Array.isArray(args?.hypotheses) ? args.hypotheses : []
const refinementUnknowns = Array.isArray(args?.unknowns) ? args.unknowns : []
const track = args?.track === 'ai-engineer' ? 'ai-engineer' : 'developer'
const repo = args?.repo
const docsBase = featureSlug

if (!featureName || !featureSlug || !refinementContent) {
  throw new Error('create-feature precisa de args: { featureName: string, featureSlug: string, refinementContent: string, track?: "developer"|"ai-engineer", repo?: "owner/name" }')
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

const QA_RESULT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'evidenceFiles', 'hypotheses', 'unknowns', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    summary: { type: 'string' },
    evidenceFiles: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'path', 'content'],
        properties: {
          name: { type: 'string', description: 'Nome do teste (ex: e2e_checkout_happy_path)' },
          path: { type: 'string', description: 'Path relativo dentro de <feature>/validation/' },
          content: { type: 'string', description: 'Conteúdo markdown completo da evidência' },
        },
      },
    },
    hypotheses: { type: 'array', items: { type: 'string' }, description: 'Causal or behavioral explanations not established by the executed tests' },
    unknowns: { type: 'array', items: { type: 'string' }, description: 'Material cases or environments not validated' },
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

const SRE_RESULT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'evidenceFiles', 'hypotheses', 'unknowns', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    summary: { type: 'string' },
    evidenceFiles: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'path', 'content'],
        properties: {
          name: { type: 'string' },
          path: { type: 'string' },
          content: { type: 'string' },
        },
      },
    },
    hypotheses: { type: 'array', items: { type: 'string' }, description: 'Operational or causal explanations not established by telemetry' },
    unknowns: { type: 'array', items: { type: 'string' }, description: 'Material production conditions not observed' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'description'],
        properties: {
          severity: { type: 'string', enum: ['blocker', 'major', 'minor', 'nit'] },
          description: { type: 'string' },
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
2. Crie um issue/ticket no repositório ${repo || '<descobrir via git remote>'} via a capability `code-host` (carregue a tool concreta via ToolSearch — ver claude-code/CLAUDE.md). Se `code-host` não estiver plugada ou falhar, deixe issueUrl como string vazia e prossiga.
3. Use a skill `evidence`. Preserve evidência verificada, hipóteses falsificáveis, desconhecidos e a proveniência quantitativa; nunca invente uma métrica.
4. Devolva tudo no schema, incluindo o markdown completo pronto para ser salvo em ${docsBase}/user_history/user_history.md.

Grave o markdown final em disco em `${docsBase}/user_history/user_history.md`. Peça ao agent `knowledge-base` para registrar um resumo; se a knowledge base não estiver disponível, siga sem ela.`,
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
4. Use a skill `evidence`. Retorne observações executadas com escopo, hipóteses testadas e desconhecidos restantes; testes passando provam apenas os casos exercitados.
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
let qaResult = null
let sreResult = null
let validationPassed = false
const validationHistory = []

while (iteration < MAX_ITERATIONS) {
  iteration++
  phase('validation')
  log(`Iteração ${iteration}/${MAX_ITERATIONS} — qa + sre em paralelo`)

  ;[qaResult, sreResult] = await parallel([
    () =>
      agent(
        `Você é o qa. Valide a implementação abaixo: testes funcionais e e2e cobrindo os critérios de aceitação. Execute os testes (use Bash). Para cada teste produza um arquivo .md de evidência (steps, expected, actual, screenshots se aplicável, verdict).

# Feature
${featureName}

# User history
${userHistory.markdown}

# Implementação (iteração ${iteration})
${JSON.stringify(implementation, null, 2)}

# Salvar evidências
Cada evidência deve ter path do tipo `${docsBase}/validation/qa_<nome_teste>.md`. Grave cada arquivo em disco; peça ao agent `knowledge-base` para registrar um resumo, se disponível.

# Veredito
Use a skill `evidence`. Preserve explicações sem sustentação como hipóteses e escope toda alegação ao ambiente e aos casos executados.
pass apenas se TODOS os critérios de aceitação foram validados sem blockers. Caso contrário fail + lista de issues com severidade e repro.`,
        { agentType: 'qa', label: `qa:iter${iteration}`, phase: 'validation', schema: QA_RESULT_SCHEMA },
      ),
    () =>
      agent(
        `Você é o sre. Valide infraestrutura, performance, carga e stress da implementação abaixo. Verifique se o ambiente está saudável e dimensionado, rode load test e stress test (k6/Locust ou equivalente), valide observabilidade (logs, métricas, traces, alertas relevantes).

# Feature
${featureName}

# Refinamento técnico
${refinementContent}

# Implementação (iteração ${iteration})
${JSON.stringify(implementation, null, 2)}

# Salvar evidências
Cada evidência deve ter path do tipo `${docsBase}/validation/sre_<nome_teste>.md`. Grave cada arquivo em disco; peça ao agent `knowledge-base` para registrar um resumo, se disponível.

# Veredito
Use a skill `evidence`. Toda métrica precisa de unidade, população, janela temporal, fonte e método. Trate explicações causais como hipóteses falsificáveis.
pass se infra/performance/observabilidade estão dentro de SLO e sem blockers. Caso contrário fail + lista de issues com severidade.`,
        { agentType: 'sre', label: `sre:iter${iteration}`, phase: 'validation', schema: SRE_RESULT_SCHEMA },
      ),
  ])

  validationHistory.push({ iteration, qa: qaResult, sre: sreResult })

  const qaPass = qaResult?.verdict === 'pass'
  const srePass = sreResult?.verdict === 'pass'
  validationPassed = qaPass && srePass

  log(`Iteração ${iteration}: qa=${qaResult?.verdict ?? 'erro'} sre=${sreResult?.verdict ?? 'erro'}`)

  if (validationPassed) break

  if (iteration >= MAX_ITERATIONS) break

  phase('fix_iteration')
  log(`Iteração ${iteration} falhou. ${implementerLabel} vai corrigir.`)

  const qaIssues = (qaResult?.issues || []).map(i => `[${i.severity}] ${i.description}${i.reproSteps ? ` (repro: ${i.reproSteps})` : ''}`).join('\n')
  const sreIssues = (sreResult?.issues || []).map(i => `[${i.severity}] ${i.description}`).join('\n')

  implementation = await agent(
    `Você é o ${implementerAgentType}. A iteração ${iteration} de validação falhou. Corrija os problemas abaixo.

# Implementação atual
${JSON.stringify(implementation, null, 2)}

# Problemas reportados pelo qa
${qaIssues || '(nenhum)'}

# Problemas reportados pelo sre
${sreIssues || '(nenhum)'}

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
    nextStep: `Após ${MAX_ITERATIONS} iterações qa+sre ainda reportam issues. Revisar manualmente.`,
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
qa: ${qaResult?.verdict}, sre: ${sreResult?.verdict}, iterações usadas: ${iteration}/${MAX_ITERATIONS}

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
- QA: ${docsBase}/validation/qa_*.md
- SRE: ${docsBase}/validation/sre_*.md

## Status da evidência
- Observações verificadas: <cite os paths de validação exatos e os comandos executados>
- Hipóteses e desconhecidos: <preserve o que a validação não estabeleceu>

## Como testar
${(implementation.commands || []).map(c => `\`\`\`\n${c}\n\`\`\``).join('\n')}

## Checklist
- [x] Testes funcionais (qa)
- [x] Testes e2e (qa)
- [x] Load test (sre)
- [x] Stress test (sre)
- [x] Observabilidade validada (sre)

# Tarefa
Abra o Pull/Merge Request via a capability `code-host` (carregue a tool concreta via ToolSearch — ver claude-code/CLAUDE.md). Faça push do branch antes se necessário. Retorne prUrl, title e body usados.`,
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
