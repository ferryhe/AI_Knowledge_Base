# IAA Knowledge Base Agent

This project builds a Retrieval-Augmented Generation workflow on top of the Markdown files stored in `Knowledge_Base_MarkDown/`.

It now supports two query paths:

- `agentic`: planner -> multi-query retrieval -> reflection -> synthesis
- `standard`: single retrieval pass -> synthesis

The upgrade keeps the existing FAISS index format intact while improving complex, cross-document questions.

This branch also adds:

- local hybrid reranking on top of FAISS retrieval
- domain-aware planner and reflector prompts for actuarial, insurance, governance, risk, ethics, and AI-model questions

## Project Structure

```text
AI_Agent/
  scripts/
    build_index.py          # chunks and embeds Knowledge_Base_MarkDown
    ask.py                  # CLI question answering
    agentic_rag.py          # iterative agentic workflow engine
    responses_pipeline.py   # Open WebUI pipeline entry point
  tests/
    test_smoke.py
    test_rag_pipeline.py
  streamlit_app.py          # optional local UI
  AGENTIC_SEARCH.md         # agentic workflow notes
  requirements.txt
  Makefile
  .env.example
  knowledge_base.faiss
  knowledge_base.meta.pkl
```

## Quick Start

### 1. Prepare Environment

- Install Python 3.9+ and git.
- Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

```powershell
cd AI_Agent
copy .env.example .env
```

### 2. Install Dependencies

With `make`:

```bash
make setup
```

Without `make`:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Build the Vector Index

```powershell
cd AI_Agent
python .\scripts\build_index.py --source ..\Knowledge_Base_MarkDown
```

This writes:

- `knowledge_base.faiss`
- `knowledge_base.meta.pkl`

### 4. Ask Questions

Agentic mode is the default:

```powershell
cd AI_Agent
python .\scripts\ask.py "What themes connect the governance and risk documents?"
```

Force the original single-pass mode:

```powershell
python .\scripts\ask.py --mode standard "Summarize the governance framework"
```

Inspect the planner and reflection trace:

```powershell
python .\scripts\ask.py --mode agentic --show-trace "Compare governance and risk control guidance"
```

### 5. Optional Streamlit UI

```powershell
cd AI_Agent
pip install streamlit
streamlit run .\streamlit_app.py
```

The Streamlit app now uses the same query runtime as the CLI for normal questions.

## Running Tests

Use the same Python interpreter that has the dependencies installed:

```powershell
cd AI_Agent
python -m pytest tests/test_smoke.py tests/test_rag_pipeline.py
```

The tests monkeypatch OpenAI calls, so they do not require network access or an API key.

## Open WebUI Pipelines Integration

1. Copy `scripts/responses_pipeline.py` into your Open WebUI Pipelines folder.
2. Copy `scripts/agentic_rag.py` and `scripts/query_enhancements.py` beside it if you want the full agentic workflow there as well.
3. Mount the generated FAISS artifacts into the container.

Example:

```yaml
volumes:
  - ./AI_Agent/knowledge_base.faiss:/data/knowledge_base.faiss
  - ./AI_Agent/knowledge_base.meta.pkl:/data/knowledge_base.meta.pkl
  - ./AI_Agent/scripts/responses_pipeline.py:/app/pipelines/responses_pipeline.py
  - ./AI_Agent/scripts/agentic_rag.py:/app/pipelines/agentic_rag.py
  - ./AI_Agent/scripts/query_enhancements.py:/app/pipelines/query_enhancements.py
```

If `agentic_rag.py` is missing in the pipeline runtime, `responses_pipeline.py` falls back to single-pass retrieval. If `query_enhancements.py` is missing, the pipeline still runs but skips reranking and domain-aware planner guidance.

## Configuration

Environment variables:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | API key used for embeddings and chat | required |
| `MODEL` | Chat model for answers | `gpt-4o` |
| `EMBEDDING_MODEL` | Embedding model for FAISS vectors | `text-embedding-3-large` |
| `RAG_MODE` | `agentic` or `standard` | `agentic` |
| `AGENTIC_MAX_ITERATIONS` | Max retrieval rounds in agentic mode | `2` |
| `AGENTIC_SYNTHESIS_TOP_K` | Global cap on merged hits before final synthesis | computed from `TOP_K` |
| `TOP_K` | Default retrieval size | `8` |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity score | `0.0` |
| `OUTPUT_LANGUAGE` | Final answer language | `en` |
| `SOURCE_DIR` | Path to Markdown corpus | `../Knowledge_Base_MarkDown` |
| `INDEX_PATH` | FAISS file location | `knowledge_base.faiss` |
| `META_PATH` | Metadata pickle location | `knowledge_base.meta.pkl` |

## FAQ

**Which files are indexed?**

All `.md` files under `SOURCE_DIR`.

**How do I disable Agentic RAG?**

Set `RAG_MODE=standard` or pass `--mode standard` to `scripts/ask.py`.

**Can I switch to another model?**

Yes. Set `MODEL` in `AI_Agent/.env`.

**What about non-Markdown assets?**

Images in `*_assets/` folders are not embedded.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Missing vector store files` | index not built yet | run `python scripts/build_index.py` |
| `ModuleNotFoundError: faiss` | dependency missing in current interpreter | install `requirements.txt` in the same interpreter used to run the app |
| Streamlit button disabled | API key or index missing | set `OPENAI_API_KEY` and rebuild the index |
| Pipeline stays single-pass | `agentic_rag.py` not present in pipeline runtime | copy or mount `agentic_rag.py` next to `responses_pipeline.py` |

## Notes

- `AGENTIC_SEARCH.md` documents the runtime flow, rollback path, and current scope.
- This upgrade is local-corpus Agentic RAG. It does not yet add external web search or multi-agent research.
