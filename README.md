# AI Knowledge Base

AI materials live under `Knowledge_Base_MarkDown/`, each with a Markdown source and companion image folder. Entries below follow the requested section labels so readers can quickly scan the title, upload date, publish date, and summary. Links jump to the Markdown files inside `Knowledge_Base_MarkDown/`.

## Repository Layout
- `Knowledge_Base_MarkDown/` - curated Markdown documents plus `*_assets/` folders for inline images.
- `AI_Agent/` - Retrieval-Augmented Generation utilities (CLI, Streamlit UI, Open WebUI pipeline) that index the Markdown corpus.
- `AI_Agent/knowledge_base.*` - generated FAISS index + metadata created by `scripts/build_index.py`.
- `.gitignore` keeps API keys, indexes, and the virtual environment out of version control.

## Updating the Catalog
1. Drop the new `document.md` into `Knowledge_Base_MarkDown/` and keep supporting images in a sibling `document_assets/` directory so relative links continue to work.
2. Add the entry to the catalog table in `catelog.md` (title, upload date, publish date, and short summary).
3. Rebuild the search index so the AI assistant sees the changes:
   ```powershell
   cd AI_Agent
   python .\scripts\build_index.py --source ..\Knowledge_Base_MarkDown
   ```
4. Share the refreshed FAISS + metadata files (`AI_Agent/knowledge_base.faiss`, `AI_Agent/knowledge_base.meta.pkl`) with anyone else running the agent.

## Finding Original Source Links
- Requirements: `AI_Agent/.venv` Python, plus `SERPAPI_API_KEY` (or `LANGSEARCH_API_KEY`/`LANGSEARCH_ENDPOINT`) in `AI_Agent/.env`.
- Run from repo root to search for sources and write `original_sources.md` (full results), archive each run under `working_runs/`, and refresh `final_original_sources.md` with only working, high-confidence links:
  ```powershell
  find_original_links.py --backend langsearch --max-results 8 --max-searches 250 --skip-existing-final
  ```
- To force a full refresh, drop `--skip-existing-final`. Use `--backend serpapi` to switch providers.

## Querying with the Agent
- Quick-start instructions, environment variables, and troubleshooting live in `AI_Agent/README.md`.
- **NEW**: See `AI_Agent/IMPROVEMENTS.md` for detailed documentation of RAG improvements.
- For a fast CLI query on Windows PowerShell:
  ```powershell
  cd AI_Agent
  .\.venv\Scripts\python.exe .\scripts\ask.py "Summarize the AI governance framework"
  ```
- Launch the optional UI with `streamlit run streamlit_app.py` after setting `OPENAI_API_KEY` and rebuilding the index.
- A hosted build of the same AI agent is available at https://www.aixintelligence.ca/ for anyone who wants to explore the knowledge base without installing dependencies.

## Validating the Agent
- Run the smoke test whenever you change `AI_Agent/scripts/` or the indexing workflow:
  ```powershell
  cd AI_Agent
  pytest tests/test_smoke.py
  ```
- The test suite uses deterministic dummy embeddings, so it finishes quickly and does not require `OPENAI_API_KEY` or internet access. This guards against regressions in chunking, metadata serialization, and retrieval.

## Catalog
The full catalog now lives in [catelog.md](catelog.md).

---

When adding new material, keep the `document.md` + `document_assets/` pairing inside `Knowledge_Base_MarkDown/` so images continue to render in Markdown viewers without additional configuration.
