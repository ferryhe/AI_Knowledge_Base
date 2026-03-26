# Open WebUI Pipelines integration for the IAA AI Knowledge Base.
# Mount knowledge_base.faiss and knowledge_base.meta.pkl into /data inside the
# container, or override INDEX_PATH / META_PATH via environment variables.

from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from agentic_rag import AgenticRagEngine
except ImportError:
    AgenticRagEngine = None

try:
    from query_enhancements import rerank_hits
except ImportError:
    rerank_hits = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL = os.getenv("MODEL", "gpt-4o")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
RAG_MODE = os.getenv("RAG_MODE", "agentic")
AGENTIC_MAX_ITERATIONS = int(os.getenv("AGENTIC_MAX_ITERATIONS", "2"))
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


def _render_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{index + 1}] {hit['path']}\n{hit['text']}" for index, hit in enumerate(hits))


def _retrieve(client: OpenAI, question: str, k: int = 8, similarity_threshold: float = 0.0):
    index, docs = _load_artifacts()

    query_vec = client.embeddings.create(model=EMB_MODEL, input=[question]).data[0].embedding
    query_array = np.array([query_vec], dtype="float32")
    faiss.normalize_L2(query_array)

    search_k = min(len(docs), max(k, max(k * 4, 12)))
    distances, indices = index.search(query_array, search_k)
    results = []
    for score, item_index in zip(distances[0], indices[0]):
        if 0 <= item_index < len(docs) and score >= similarity_threshold:
            results.append({**docs[item_index], "retrieval_score": float(score)})
    if rerank_hits is not None:
        return rerank_hits(question, results, top_k=k)
    return results


def _chat(client: OpenAI, messages: list[dict], temperature: float = 0.2) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _answer_from_hits(client: OpenAI, question: str, hits: list[dict]) -> str:
    if not hits:
        return "I don't have enough information to answer this question."

    prompt = (
        "You will receive Markdown excerpts from the IAA AI Knowledge Base. Each excerpt already includes a numeric tag "
        "like [1], [2], etc., plus its file path. Use only these excerpts to answer the question. "
        "When citing information, reuse the same numeric tag and file path so the reader can trace the source. "
        "If there is no supporting excerpt, say 'Not sure' and mention which Markdown file should be reviewed.\n\n"
        f"Retrieved snippets:\n{_render_context(hits)}\n\nQuestion: {question}"
    )

    return _chat(
        client,
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )


def pipeline(messages: list[dict]):
    client = OpenAI()
    question = _latest_user_question(messages) or "Summarize the latest AI Task Force documents."

    if AgenticRagEngine is not None and RAG_MODE == "agentic":
        engine = AgenticRagEngine(
            chat_fn=lambda prompt_messages, temperature=0.2: _chat(client, prompt_messages, temperature),
            retrieve_fn=lambda query, k, threshold: _retrieve(client, query, k=k, similarity_threshold=threshold),
            synthesize_fn=lambda prompt_question, hits, language, history: _answer_from_hits(client, prompt_question, hits),
            language="en",
            max_iterations=AGENTIC_MAX_ITERATIONS,
            top_k=4,
        )
        return engine.run(question).answer

    hits = _retrieve(client, question)
    return _answer_from_hits(client, question, hits)
