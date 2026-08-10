---
version: 1.0.0
upstream_source: https://github.com/langchain-ai/langchain-skills
upstream_version: 92e4f3b494c02d8927f85ab3b8d97417b445b6ee
adaptation_status: local-adaptation
name: ecosystem-primer
description: |
  Ponto de partida obrigatório para qualquer projeto de agent com LangChain, LangGraph ou
  Deep Agents — invoque ANTES de consultar outras skills langchain-* ou escrever código. Cobre
  seleção de framework (LangChain vs LangGraph vs Deep Agents vs composição híbrida), padrões de
  agent, install, environment setup e qual skill carregar em seguida. Adaptação local do projeto
  upstream; não declara paridade byte a byte.
  Use quando: (1) Iniciar um projeto LangChain/LangGraph/Deep Agents, (2) Decidir qual framework
  usar, (3) Descobrir qual skill langchain-* carregar para a tarefa.
  Triggers: /langchain, langchain, langgraph, deep agents, framework selection, qual framework usar.
type: capability
---

<overview>
LangChain Inc. maintains three layered open-source tools for building agents, plus LangSmith for observability. The stack, top-down:

- **Deep Agents** (top layer, *harness*) — batteries-included toolkit built on LangChain + LangGraph. Ships with planning, file management, subagent spawning, and memory out of the box.
- **LangGraph** (middle layer, *runtime*) — low-level orchestration for durable execution, custom control flow, and stateful workflows. LangChain agents run on top of LangGraph.
- **LangChain** (bottom layer, *framework*) — abstractions for models, tools, and the agent loop. Provider-agnostic, easiest to start with.
- **LangSmith** (cross-cutting) — observability and evaluation platform. Framework-agnostic; always recommended alongside any of the above.

Higher layers depend on lower ones, but you don't need to use lower layers directly. Deep Agents gives you LangGraph's durable execution without writing graph code. LangChain gives you models and tools without managing graph edges.
</overview>

---

## Step 1 — Choose Your Tool

<decision-table>

Evaluate these conditions in order and stop at the first match:

1. If the task needs planning, file management across a long session, persistent memory, subagent delegation, or on-demand skills → **Deep Agents**
2. Else, if the task needs custom control flow (deterministic loops, branching logic) → **LangGraph**
3. Else, if it's a single-purpose agent with a fixed set of tools → **LangChain** (`create_agent` function)
4. Else, if it's a pure model call, retrieval pipeline, or simple prompt chain with no agent loop → **LangChain** (direct model / chain)

This is your **layer**. BUT you are not done: later in Step 4, you MUST load the layer-specific skill before writing any agent code.

</decision-table>

---

## Tool Profiles

<langchain-profile>

### LangChain — agent framework

**Best for:**
- Single-purpose agents with a fixed tool set
- RAG pipelines and document Q&A
- Model calls, prompt templates, structured output

**Not ideal when:**
- The agent needs to plan across many steps or manage large context
- Control flow is conditional, iterative, or parallel
- State must persist across sessions

All LangChain agents use `create_agent(model, tools=[...])`.

</langchain-profile>

<langgraph-profile>

### LangGraph — agent runtime

**Best for:**
- Custom control flow — deterministic loops, reflection cycles, parallel fan-out
- Complex workflows combining deterministic and agentic steps
- Human-in-the-loop with precise interrupt and resume points
- State that must survive failures or span long sessions

**Not ideal when:**
- You want planning, file management, and subagent delegation out of the box (use Deep Agents instead)
- The workflow is simple enough for a straight tool loop

All LangGraph graphs use `StateGraph(State)` with explicit nodes, edges, and conditional edges.

</langgraph-profile>

<deep-agents-profile>

### Deep Agents — agent harness

**Best for:**
- Long-running tasks that require planning and decomposition
- Agents that read, write, and manage files across a session
- Delegating subtasks to specialized subagents
- Persistent memory across sessions
- Loading domain-specific skills on demand

**Not ideal when:**
- The task is simple enough for a single-purpose agent
- You need precise hand-crafted control over every graph edge (use LangGraph directly)

All Deep Agents use `create_deep_agent(model, tools=[...])`.

</deep-agents-profile>

---

## Mixing Layers

<mixing-layers>

The tools are layered, so they can be combined in the same project. Common patterns:

- **Deep Agents orchestrator → LangGraph subagent** — when the main agent needs planning and memory but one subtask requires a deterministic graph.
- **LangGraph graph wrapped as a tool or subagent** — when a specialized pipeline (e.g. RAG, reflection loop) is called by a broader agent.

A compiled LangGraph graph can be registered as a named subagent inside Deep Agents — the orchestrator delegates to it via the `task` tool without knowing its internal structure. LangChain tools and retrievers work freely inside both LangGraph nodes and Deep Agents tools.

</mixing-layers>

---

## Step 2 — Set Environment Variables

Always set these for observability. These are the current LangSmith env var names. Copy them as-is. OLDER NAMES NO LONGER WORK.

<environment-variables>
LANGSMITH_API_KEY=<your-key>
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=<project-name>
</environment-variables>

Model-provider and tool-specific keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`, etc.) depend on your stack — set them as needed.

---

## Step 3 — How the Docs Work

<docs>

All documentation lives at **docs.langchain.com**, organized into two top-level sections:

- **OSS** — LangChain, LangGraph, Deep Agents. Python (`/oss/python/`) and TypeScript (`/oss/javascript/`) trees in parallel.
- **LangSmith** — observability, evaluation, deployment, prompt engineering.

Each product has its own page tree: overview → quickstart → how-to guides → reference.

### Canonical landing pages

Start here rather than tree-searching from root (swap `python` → `javascript` for TypeScript):

- **LangChain** — `/oss/python/langchain/overview`
- **LangGraph** — `/oss/python/langgraph/overview`
- **Deep Agents** — `/oss/python/deepagents/overview`
- **LangSmith** — `/langsmith/home` (no language split)

### Accessing docs in an agent context

Resolve live documentation through the abstract `web` capability configured by the harness.
If the provider exposes structured documentation navigation, use it to explore the canonical
paths above and retrieve only the pages relevant to the question.

When structured navigation is unavailable, use the `llms.txt` index:
1. Fetch `https://docs.langchain.com/llms.txt` — structured list of all pages with descriptions
2. Identify the 2–4 most relevant pages for the question
3. Fetch those pages directly for accurate, up-to-date content

> Always prefer fetching live docs over relying on training-data knowledge — these libraries evolve fast and APIs change often.

</docs>

---

## Step 4 — Load the Right Skill Next

Load the shipped skill that matches the layer selected in Step 1. This is required even for
a minimal local agent: the layer-specific skill carries the implementation contract, while
this primer only supports framework selection. For current APIs and provider setup, resolve
the relevant official documentation through the `web` capability.

<next-skills>

### LangChain

- **`langchain-fundamentals`** — building agents, structured output, and middleware
- **`langchain-rag`** — adding RAG / vector store retrieval
- **`langchain-dependencies`** — package versions, installs, or dependency management questions

### LangGraph

- **`langgraph-fundamentals`** — any LangGraph graph
- **`langgraph-human-in-the-loop`** — human-in-the-loop or approval workflows
- **`langgraph-persistence`** — state that must survive restarts, or cross-thread memory

### Deep Agents

**Always load `deep-agents-core` first.** Then, as needed:

- **`deep-agents-orchestration`** — subagent delegation or orchestration
- **`deep-agents-memory`** — cross-session persistent memory

</next-skills>
