# AI Production

Use for production fitness after relevant integration, retrieval, agent, and eval contracts exist.

1. Define quality, safety, latency, availability, throughput, token, spend, and data budgets.
2. Trace model attempts, retrieval, tools, effects, fallbacks, and final responses with correlation;
   record provider/model/tier, tokens, latency, status, retry, cache, and dated price evidence.
3. Bound concurrency, queues, deadlines, retries, circuit behavior, and spend.
4. Permit fallback only across verified schema, safety, residency, context, tool, latency, and price
   semantics; expose every fallback.
5. Use lawful replay or shadow checks, canary, staged exposure, stop signals, and recoverable rollback.
6. Re-evaluate on model, SDK, prompt, corpus, tool, policy, or price changes.

Cache only with tenant, authorization, versions, safety, freshness, and deletion in the key and
invalidation contract. Return metrics with unit/population/window/source/method, resilience and
privacy checks, rollout criteria, price provenance, and unexecuted production validation.
