# IAA Knowledge Base Agent (Runnable)

This project builds a Retrieval-Augmented Generation (RAG) workflow on top of the Markdown files stored in `Knowledge_Base_MarkDown/`.  
It provides both **command-line querying** and an **Open WebUI Pipelines** integration so the latest IAA AI documentation can be queried with citations.

---

## Project Structure
```
AI_Agent/
  scripts/
    build_index.py          # chunks & embeds Knowledge_Base_MarkDown
    ask.py                  # CLI question answering
    responses_pipeline.py   # drop-in pipeline for Open WebUI
  tests/
    test_smoke.py           # offline regression test for index + retrieval
  streamlit_app.py          # optional local UI
  requirements.txt
  Makefile
  .env.example
  knowledge_base.faiss      # generated FAISS index
  knowledge_base.meta.pkl   # generated metadata
```

---

## Quick Start

### 1. Prepare Environment
- Install **Python 3.9+** and **git**.
- Copy `.env.example` to `.env` and set your `OPENAI_API_KEY`:
  ```bash
  cd AI_Agent
  cp .env.example .env   # use copy .env.example .env on Windows
  ```

### 2. Install Dependencies
Using GNU Make (Linux/macOS/WSL):
```bash
make setup
```

Windows (without `make`):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Build the Vector Index
GNU Make / POSIX:
```bash
make index
```

PowerShell (without `make`):
```powershell
cd AI_Agent
.\.venv\Scripts\activate
python .\scripts\build_index.py --source ..\Knowledge_Base_MarkDown
```

This script reads every Markdown file from `../Knowledge_Base_MarkDown/`, chunks them, and writes:
- `knowledge_base.faiss`
- `knowledge_base.meta.pkl`

You can override the source folder or output paths with the env vars in `.env`.

### 4. Ask Questions (Command Line)
```bash
make ask q="summarize the governance framework consultation draft"
```
Or directly:
```powershell
python scripts/ask.py "summarize the governance framework consultation draft"
```

### 5. Optional: Local Streamlit UI
```bash
pip install streamlit         # only needed once
streamlit run streamlit_app.py
```

PowerShell example (after activating `.venv`):
```powershell
pip install streamlit
streamlit run .\streamlit_app.py
```

The UI now disables the "Ask" button until `OPENAI_API_KEY` is set and the FAISS artifacts exist; rebuild the index whenever Markdown files change.

## Running Tests
- Smoke tests live under `tests/` and verify that chunking, FAISS serialization, and CLI retrieval stay aligned.
- Run them locally (no API key or network access required—the suite monkeypatches OpenAI calls):
  ```powershell
  cd AI_Agent
  pytest tests/test_smoke.py
  ```
- Incorporate the test run into your workflow whenever you touch `scripts/` or dependency versions to catch regressions early.

---

## Open WebUI Pipelines Integration
1. Copy `scripts/responses_pipeline.py` into your Open WebUI Pipelines folder.
2. Mount the generated files into the container:
   ```yaml
   volumes:
     - ./AI_Agent/knowledge_base.faiss:/data/knowledge_base.faiss
     - ./AI_Agent/knowledge_base.meta.pkl:/data/knowledge_base.meta.pkl
     - ./AI_Agent/scripts/responses_pipeline.py:/app/pipelines/responses_pipeline.py
   ```
3. The pipeline retrieves the top chunks from the index and answers with path citations.

### Rebuilding Workflow
1. Update Markdown files under `../Knowledge_Base_MarkDown/`.
2. Run `python scripts/build_index.py` (or `make index`) to regenerate `knowledge_base.*`.
3. Call `scripts.ask.refresh_cache()` or restart Streamlit/Open WebUI so cached indexes pick up the changes.

--- 

## Configuration
Environment variables (stored in `.env`):

| Variable      | Description                               | Default                                     |
|---------------|-------------------------------------------|---------------------------------------------|
| `OPENAI_API_KEY` | API key used for embeddings + chat        | _(required)_                                |
| `MODEL`       | Chat model for responses                  | `gpt-4o`                                    |
| `EMBEDDING_MODEL` | Embedding model for FAISS vectors        | `text-embedding-3-large`                    |
| `SOURCE_DIR`  | Path to Markdown corpus                   | `../Knowledge_Base_MarkDown`                |
| `INDEX_PATH`  | FAISS file location                       | `knowledge_base.faiss`                      |
| `META_PATH`   | Metadata pickle location                  | `knowledge_base.meta.pkl`                   |
| `STREAMLIT_PORT` | Override default Streamlit port (optional) | `8501` (handled via `streamlit` CLI)      |

---

## FAQ

**Q: Which files are indexed?**  
All `.md` files under `SOURCE_DIR`. If you add more documentation, re-run `make index`.

**Q: Can I switch to another LLM?**  
Yes. Set `MODEL` in `.env` (any Chat Completions compatible model).

**Q: What about non-Markdown assets?**  
Images live in `*_assets` folders and are not embedded. Add OCR or PDF handling as needed.

**Q: Where is my API key stored?**  
In `AI_Agent/.env`, which is ignored by git via the root `.gitignore`.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Missing vector store files` | `knowledge_base.*` not built yet | Run `make index` (or the PowerShell command above) and keep the files next to this README. |
| `ModuleNotFoundError: faiss` | Virtual environment not activated or install failed | Re-run `make setup` (POSIX) or `python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements.txt`. |
| Streamlit button disabled | API key or index missing | Set `OPENAI_API_KEY` in `.env` and rebuild the index. |
| Requests hitting wrong OpenAI model | `MODEL` only changed in `.env` | Streamlit/CLI now respect `MODEL`; restart the process after editing `.env`. |

For container deployments, inject secrets via environment variables (e.g., `OPENAI_API_KEY`, `MODEL`) instead of copying `.env`, and mount the generated FAISS files read-only to keep the runtime stateless.

---

## License
This agent indexes internal Markdown content from `Knowledge_Base_MarkDown/`.  
Ensure you have permission before exposing the generated artifacts externally.
