# IAA Knowledge Base Agent (Runnable)

This project builds a Retrieval-Augmented Generation (RAG) workflow on top of the Markdown files stored in `Knowledge_Base_MarkDown/`.  
It provides both **command-line querying** and an **Open WebUI Pipelines** integration so the latest IAA AI documentation can be queried with citations.

---

## Project Structure
```
AI_Agent/
  ├─ scripts/
  │  ├─ build_index.py          # chunks & embeds Knowledge_Base_MarkDown
  │  ├─ ask.py                  # CLI question answering
  │  └─ responses_pipeline.py   # drop-in pipeline for Open WebUI
  ├─ requirements.txt
  ├─ Makefile
  ├─ .env.example
  ├─ knowledge_base.faiss       # generated FAISS index
  └─ knowledge_base.meta.pkl    # generated metadata
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
```bash
make index
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

## License
This agent indexes internal Markdown content from `Knowledge_Base_MarkDown/`.  
Ensure you have permission before exposing the generated artifacts externally.
