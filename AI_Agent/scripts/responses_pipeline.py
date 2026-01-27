# Open WebUI Pipelines integration for the IAA AI Knowledge Base
# Mount knowledge_base.faiss and knowledge_base.meta.pkl into /data inside the
# container, or override INDEX_PATH / META_PATH via environment variables.

import os
import pickle
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL = os.getenv("MODEL", "gpt-4o")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
INDEX_PATH = os.getenv("INDEX_PATH", "/data/knowledge_base.faiss")
META_PATH = os.getenv("META_PATH", "/data/knowledge_base.meta.pkl")
_INDEX_CACHE = None
_DOCS_CACHE = None

SYSTEM_PROMPT = (
    "You are the documentation expert for the IAA AI Knowledge Base. "
    "CRITICAL INSTRUCTIONS:\n"
    "1. Answer ONLY using information from the retrieved snippets provided below.\n"
    "2. Every claim must cite evidence using the snippet number and file path in the format `[n] path/to/file.md`.\n"
    "3. Structure answers with a short summary followed by bullet points of supporting evidence.\n"
    "4. If the snippets do not contain sufficient information to answer the question, you MUST reply 'I don't have enough information to answer this question.' "
    "and recommend the most relevant Markdown file to inspect.\n"
    "5. NEVER make up information or draw conclusions not directly supported by the snippets.\n"
    "6. If you're uncertain about any detail, explicitly state your uncertainty."
)


def _latest_user_question(messages):
    for item in reversed(messages):
        if item.get("role") == "user":
            return item.get("content", "")
    return ""


def _load_artifacts(refresh: bool = False):
    global _INDEX_CACHE, _DOCS_CACHE

    if refresh or _INDEX_CACHE is None or _DOCS_CACHE is None:
        if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
            raise FileNotFoundError(
                "Missing index or metadata files. "
                f"Expected:\n  {INDEX_PATH}\n  {META_PATH}\n"
                "Run scripts/build_index.py and mount the results into the container."
            )

        _INDEX_CACHE = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as fh:
            _DOCS_CACHE = pickle.load(fh)

    return _INDEX_CACHE, _DOCS_CACHE


def refresh_cache():
    """Allow external callers to refresh the FAISS/metadata cache."""
    _load_artifacts(refresh=True)


def _retrieve(client: OpenAI, question: str, k: int = 8):
    index, docs = _load_artifacts()

    query_vec = client.embeddings.create(model=EMB_MODEL, input=[question]).data[0].embedding
    query_array = np.array([query_vec], dtype="float32")
    faiss.normalize_L2(query_array)

    distances, indices = index.search(query_array, k)
    return [docs[i] for i in indices[0] if 0 <= i < len(docs)]


def pipeline(messages: list[dict]):
    client = OpenAI()
    question = _latest_user_question(messages) or "Summarize the latest AI Task Force documents."
    hits = _retrieve(client, question)

    context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
    prompt = f"Retrieved snippets:\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content
