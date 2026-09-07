# AI Evaluation

Compose evals:evals-start for general routing, evals:evaluate-rag for RAG evaluation, and
langchain-skills:eval-engineering for Harbor. If unavailable, disclose degraded mode.

1. Define failure modes, population, unit, split, environment, model, harness, tools, and success
   state before observing candidates.
2. Prefer deterministic end-state evidence; use one calibrated, abstaining, blinded judge only for
   one irreducibly subjective failure mode.
3. Separate routing, retrieval, generation, factuality/freshness, safety, tools, latency, tokens,
   and cost. Averages cannot dispose of a critical failure.
4. Pin instruction bytes, model/harness, repository/corpus, tools, evaluator, and provenance.
5. Keep discovery, judge-development, locked, and rotating freshness/adversarial splits distinct.
6. Record missing and invalid runs honestly; never fabricate executions, traces, labels, metrics,
   signatures, prices, or release authority.

Return preregistered gates, requirement-to-check mapping, pins, evidence locations, per-slice outcomes,
calibration, and release eligibility.
