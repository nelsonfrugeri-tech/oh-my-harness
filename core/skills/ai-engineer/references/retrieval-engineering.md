# Retrieval Engineering

Use to improve retrieval and grounded generation as separately observable stages.

1. Define corpus authority, document identity, tenant, freshness, update/delete, and not-found rules.
2. Build representative queries with independently labeled relevant source units and stable IDs.
3. Measure first-pass coverage and ranking separately; inspect misses, distractors, filters, and stale
   or conflicting versions before tuning generation.
4. Compare chunking, metadata, query transformation, hybrid search, reranking, and top-k on the same
   held-out set.
5. Require claim-level citations to exact source versions; abstain on absent or conflicting support.
6. Test corpus poisoning and instruction-like text as untrusted data.

Compose langchain-skills:ecosystem-primer then langchain-skills:langchain-rag for LangChain, and
evals:evaluate-rag for evaluation. In degraded mode, use official docs plus this stable contract and
report no invented metrics. Include absent answers, stale conflicts, tenant isolation, deletion
propagation, and retrieval-versus-generation diagnostic cases.
