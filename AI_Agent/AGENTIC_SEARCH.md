# Agentic RAG Workflow

## What Changed

`AI_Agent/` now supports an Agentic RAG workflow on top of the existing FAISS index.

Instead of a single retrieval pass, the runtime can now:

1. plan retrieval-oriented sub-queries from the user question
2. retrieve evidence for each sub-query
3. reflect on coverage and optionally run one more retrieval round
4. synthesize a grounded final answer with citations

This keeps the original vector store format intact while improving multi-step, cross-document questions.

## Scope of This Upgrade

This implementation is intentionally bounded:

- uses the existing local FAISS index only
- does not change index or metadata formats
- adds agentic orchestration at query time
- preserves a `standard` fallback mode

It is an Agentic RAG upgrade, not yet a full web-connected deep research system.

## Runtime Flow

### Standard mode

`question -> retrieve top-k once -> synthesize answer`

### Agentic mode

`question -> planner -> retrieve -> reflect -> optional second retrieve -> synthesize`

## Entry Points

- CLI: `AI_Agent/scripts/ask.py`
- Streamlit: `AI_Agent/streamlit_app.py`
- Open WebUI pipeline: `AI_Agent/scripts/responses_pipeline.py`

All three entry points can now use the same agentic query path.

## Configuration

Environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `RAG_MODE` | `agentic` or `standard` | `agentic` |
| `AGENTIC_MAX_ITERATIONS` | max retrieval rounds in agentic mode | `2` |
| `TOP_K` | top-k retrieval size | `8` |
| `SIMILARITY_THRESHOLD` | minimum similarity score | `0.0` |
| `OUTPUT_LANGUAGE` | final answer language | `en` |

CLI examples:

```powershell
cd AI_Agent
python .\scripts\ask.py "What themes connect the governance and risk documents?"
python .\scripts\ask.py --mode standard "Summarize the governance framework"
python .\scripts\ask.py --mode agentic --show-trace "Compare governance and risk control guidance"
```

## Open WebUI Note

`responses_pipeline.py` will use agentic mode when `agentic_rag.py` is available alongside it.

If only `responses_pipeline.py` is copied into another runtime and `agentic_rag.py` is missing, the pipeline falls back to the original single-pass retrieval behavior.

## Rollback

No data migration is involved.

To disable agentic behavior:

- set `RAG_MODE=standard`
- or run CLI with `--mode standard`

## Current Limitations

- retrieval still depends on the local FAISS corpus only
- reflection uses the model's judgment, so trace inspection is useful for debugging complex failures
- the agent currently runs a maximum of two retrieval rounds by default to control latency and cost

## Next Logical Step

If this workflow proves stable, the next upgrade should target:

1. reranking retrieved chunks before synthesis
2. richer planner prompts for actuarial / governance domain questions
3. optional external tools beyond the local FAISS store
