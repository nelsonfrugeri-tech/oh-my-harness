/** Provider-neutral schema reference for the create-feature workflow. */

export type Track = 'developer' | 'ai-engineer'

export type WorkflowStatus =
  | 'success'
  | 'ready_for_remote'
  | 'blocked_at_development'
  | 'blocked_at_fix'
  | 'failed_max_iterations'

export interface FeatureInput {
  readonly featureName: string
  readonly featureSlug: string
  readonly refinementContent: string
  readonly track: Track
  readonly repo: string
}

export interface AcceptanceCriterion {
  readonly scenario: string
  readonly given: string
  readonly when: string
  readonly then: string
}

export interface UserStory {
  readonly title: string
  readonly asA: string
  readonly iWant: string
  readonly soThat: string
  readonly acceptanceCriteria: readonly AcceptanceCriterion[]
  readonly definitionOfDone: readonly string[]
  readonly issueUrl: string
  readonly markdown: string
}

export interface ImplementationResult {
  readonly summary: string
  readonly filesChanged: readonly string[]
  readonly commands: readonly string[]
  readonly branch: string
  readonly verdict: 'done' | 'blocked'
  readonly blockedReason: string
}

export interface Finding {
  readonly severity: 'blocker' | 'major' | 'minor' | 'nit'
  readonly description: string
  readonly reproSteps: string
}

export interface ValidationResult {
  readonly verdict: 'pass' | 'fail'
  readonly summary: string
  readonly evidenceReferences: readonly string[]
  readonly issues: readonly Finding[]
}

export interface ValidationIteration {
  readonly iteration: number
  readonly qa: ValidationResult
  readonly sre: ValidationResult
}

export interface RemoteResult {
  readonly url: string
  readonly title: string
  readonly body: string
}

export interface WorkflowResult {
  readonly status: WorkflowStatus
  readonly feature: FeatureInput
  readonly userStory: UserStory
  readonly implementation: ImplementationResult
  readonly validationHistory: readonly ValidationIteration[]
  readonly remote: RemoteResult
  readonly nextStep: string
}

export const workflowContract = Object.freeze({
  maxValidationIterations: 3,
  roles: Object.freeze(['tech-pm', 'developer', 'ai-engineer', 'qa', 'sre']),
  capabilities: Object.freeze(['code-host', 'memory']),
})
