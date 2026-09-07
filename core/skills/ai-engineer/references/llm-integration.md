# LLM Integration

Use for provider boundaries; compose openai-docs for OpenAI. Inspect pinned SDKs and current official
provider docs before writing API syntax.

1. Define typed request, response, usage, finish-state, and error representations.
2. Validate structured output against the application schema; preserve refusals and truncation.
3. Bound timeout, cancellation, concurrency, and output size.
4. Retry only documented transient failures, with finite jittered attempts, when replay is safe.
5. Test matching sync/async clients, malformed schemas, unknown models, rate limits, cancellation,
   partial streams, and non-idempotent effects.

Never infer capability from a model name or silently swap incompatible models. Return the adapter
contract, source URL/date, SDK and model identity, unsupported cases, checks run, and unknowns.
