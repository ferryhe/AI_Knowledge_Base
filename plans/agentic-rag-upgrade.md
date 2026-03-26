# Agentic RAG Upgrade Plan

## Metadata

- Objective: Upgrade `AI_Agent/` from single-pass FAISS RAG to an Agentic RAG workflow aligned with `agentic_search.md`
- Branch: `feat/agentic-rag-upgrade`
- Scope: `AI_Agent/` implementation, tests, and documentation
- Non-goal: split into a standalone repository

## Current Baseline

The current system uses a linear pipeline:

1. embed user question
2. retrieve top-k FAISS chunks once
3. send snippets to the model
4. print a cited answer

This is reliable for simple lookup questions, but it has no:

- query decomposition
- iterative retrieval
- gap analysis / reflection
- explicit working state across steps
- controllable fallback between standard and agentic modes

## Target Architecture

The upgraded workflow will follow:

1. `planner`
   - decompose a complex question into 2-4 retrieval-oriented sub-queries
2. `retrieve`
   - execute FAISS retrieval for each sub-query
   - merge and deduplicate results into a shared evidence set
3. `reflect`
   - assess whether the current evidence is sufficient
   - either request one more retrieval round or continue
4. `synthesize`
   - generate the final grounded answer with citations

The orchestrator is implemented as an explicit state machine so the workflow remains lightweight, testable, and easy to integrate with the existing CLI, Streamlit app, and Open WebUI pipeline.

## Delivery Phases

### Phase 1: Stabilize the Core Abstractions

Goal: introduce reusable agentic workflow code without breaking existing retrieval helpers.

Changes:

- add a new module for the workflow implementation
- keep `scripts/ask.py::retrieve()` available for compatibility
- centralize prompt formatting and citation-safe synthesis paths
- add environment-based knobs for iteration count and retrieval limits

Exit criteria:

- existing retrieval tests still pass
- new workflow can run from Python with mocked model responses

### Phase 2: Implement Agentic RAG Engine

Goal: make the system truly iterative.

Changes:

- add graph state for question, sub-queries, evidence, iteration count, and final answer
- implement planner node
- implement retrieval node
- implement reflector node with stop / continue decision
- implement synthesizer node
- add robust JSON parsing and fallback behavior when the model output is malformed

Exit criteria:

- a complex question can produce multiple sub-queries
- at least one loop path is covered by tests
- synthesis still enforces grounded citations

### Phase 3: Integrate Entry Points

Goal: make the new workflow usable without forcing an all-or-nothing cutover.

Changes:

- update CLI `scripts/ask.py`
- support `--mode standard|agentic`
- default to `agentic` for normal queries
- wire Open WebUI pipeline to the same agentic engine
- preserve existing index / metadata file layout

Exit criteria:

- CLI still works with a single command
- Open WebUI pipeline uses the same orchestration path

### Phase 4: Tests, Docs, and Rollout Guardrails

Goal: make the upgrade maintainable.

Changes:

- add unit tests for planner / reflector / orchestration behavior
- document architecture, config, and rollback path
- update `AI_Agent/README.md`
- add an implementation note file for future extraction into shared tooling

Exit criteria:

- `pytest AI_Agent/tests/test_smoke.py AI_Agent/tests/test_rag_pipeline.py` passes
- documentation explains how to switch back to `standard` mode

## File Plan

Expected additions:

- `AI_Agent/scripts/agentic_rag.py`
- `AI_Agent/AGENTIC_SEARCH.md`
- `plans/agentic-rag-upgrade.md`

Expected edits:

- `AI_Agent/scripts/ask.py`
- `AI_Agent/scripts/responses_pipeline.py`
- `AI_Agent/requirements.txt`
- `AI_Agent/README.md`
- `AI_Agent/tests/test_rag_pipeline.py`

## Rollback Strategy

If the agentic path is unstable:

- run CLI with `--mode standard`
- keep standard retrieval helpers intact
- do not change index format or metadata schema in this upgrade

This keeps rollback limited to runtime selection rather than data migration.

## Verification Commands

```powershell
cd AI_Agent
pytest tests/test_smoke.py tests/test_rag_pipeline.py
python .\scripts\ask.py --mode standard "Summarize the governance framework"
python .\scripts\ask.py --mode agentic "What are the main themes across the governance and risk documents?"
```

## Next Step

Implement the agentic engine first, then wire the CLI and pipeline to it.
