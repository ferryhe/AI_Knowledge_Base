from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for utils import
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from utils import retry_with_exponential_backoff

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL = os.getenv("MODEL", "gpt-4o")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")


def _resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default.resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve()
    return (PROJECT_ROOT / candidate).resolve()


INDEX_PATH = _resolve_path(os.getenv("INDEX_PATH"), PROJECT_ROOT / "knowledge_base.faiss")
META_PATH = _resolve_path(os.getenv("META_PATH"), PROJECT_ROOT / "knowledge_base.meta.pkl")
_INDEX_CACHE = None
_DOCS_CACHE = None

def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()

def get_system_prompt(language: str = "en") -> str:
    """
    Get the system prompt with language-specific instructions.
    
    Args:
        language: Language code ('en' or 'zh') - determines the response language
    
    Returns:
        System prompt with language instructions
    """
    base_prompt = (
        "You are the documentation expert for the IAA AI Knowledge Base. "
        "CRITICAL INSTRUCTIONS:\n"
        "1. Answer ONLY using information from the retrieved snippets provided below.\n"
        "2. Every claim must cite evidence using the snippet number and file path in the format `[n] path/to/file.md`.\n"
        "3. Structure answers with a short summary followed by bullet points of supporting evidence.\n"
        "4. If the snippets do not contain sufficient information to answer the question, you MUST reply 'I don't have enough information to answer this question.' "
        "and recommend the most relevant Markdown file to inspect.\n"
        "5. NEVER make up information or draw conclusions not directly supported by the snippets.\n"
        "6. If you're uncertain about any detail, explicitly state your uncertainty.\n"
    )
    
    if language == "zh":
        base_prompt += (
            "7. LANGUAGE INSTRUCTION: Respond in Chinese (中文). "
            "Maintain the same professional tone and citation format, but use Chinese language for all explanations and summaries."
        )
    else:
        base_prompt += (
            "7. LANGUAGE INSTRUCTION: Respond in the same language as the user's question. "
            "If the question is in Chinese, respond in Chinese. If in English, respond in English. "
            "Maintain the same professional tone and citation format regardless of language."
        )
    
    return base_prompt

# Keep the old constant for backward compatibility (defaults to English)
SYSTEM_PROMPT = get_system_prompt("en")


def format_user_prompt(question: str, context: str, history: str | None = None) -> str:
    history_block = ""
    if history:
        history_block = f"Prior conversation:\n{history}\n\n"
    return (
        history_block
        + "You will receive Markdown excerpts from the IAA AI Knowledge Base. Each excerpt already includes a numeric tag "
        "like [1], [2], etc., plus its file path. Use only these excerpts to answer the question. "
        "When citing information, reuse the same numeric tag and file path so the reader can trace the source. "
        "If there is no supporting excerpt, say 'Not sure' and mention which Markdown file should be reviewed.\n\n"
        f"Retrieved snippets:\n{context}\n\nQuestion: {question}"
    )


def _load_index(path: Path):
    try:
        return faiss.read_index(str(path))
    except TypeError:
        with open(path, "rb") as fh:
            buf = fh.read()
        arr = np.frombuffer(buf, dtype="uint8")
        return faiss.deserialize_index(arr)


def _load_artifacts(refresh: bool = False):
    global _INDEX_CACHE, _DOCS_CACHE

    if refresh or _INDEX_CACHE is None or _DOCS_CACHE is None:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            raise FileNotFoundError(
                "Missing vector store files. Run scripts/build_index.py first.\n"
                f"Expected:\n  {INDEX_PATH}\n  {META_PATH}"
            )

        _INDEX_CACHE = _load_index(INDEX_PATH)
        with META_PATH.open("rb") as fh:
            _DOCS_CACHE = pickle.load(fh)

    return _INDEX_CACHE, _DOCS_CACHE


def refresh_cache():
    """Reload FAISS and metadata, useful after re-building the index."""
    _load_artifacts(refresh=True)


def get_document_snippets(doc_path: str, limit: int | None = None):
    """Return FAISS metadata chunks for a specific Markdown path."""
    _, docs = _load_artifacts()
    target = _normalize_path(doc_path)
    matches = [doc for doc in docs if _normalize_path(doc["path"]).endswith(target)]
    if limit is not None:
        return matches[:limit]
    return matches


@retry_with_exponential_backoff(max_retries=3, initial_delay=1.0)
def _create_embedding(client: OpenAI, text: str) -> list[float]:
    """Create embedding with retry logic."""
    return client.embeddings.create(model=EMB_MODEL, input=[text]).data[0].embedding


@retry_with_exponential_backoff(max_retries=3, initial_delay=2.0)
def _create_chat_completion(client: OpenAI, messages: list[dict], temperature: float = 0.2) -> str:
    """Create chat completion with retry logic."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def retrieve(client: OpenAI, question: str, k: int = 8, similarity_threshold: float = 0.0):
    """
    Retrieve relevant document chunks using vector similarity search.
    
    Args:
        client: OpenAI client instance
        question: User's query
        k: Number of top results to return (default 8)
        similarity_threshold: Minimum cosine similarity score (0.0-1.0).
                            Default 0.0 returns all k results.
                            Recommended: 0.3-0.5 for stricter filtering.
    
    Returns:
        List of document chunks with metadata, filtered by similarity threshold
    """
    index, docs = _load_artifacts()

    query_vec = _create_embedding(client, question)
    query_array = np.array([query_vec], dtype="float32")
    faiss.normalize_L2(query_array)

    # FAISS IndexFlatIP returns cosine similarity scores (higher is better)
    distances, indices = index.search(query_array, k)
    
    # Filter by similarity threshold
    results = []
    for score, i in zip(distances[0], indices[0]):
        if 0 <= i < len(docs) and score >= similarity_threshold:
            results.append(docs[i])
    
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ask.py \"your question\"")
        sys.exit(1)

    question = sys.argv[1]
    client = OpenAI()
    
    try:
        hits = retrieve(client, question)
        
        # Check if we got any results
        if not hits:
            print("I don't have enough information to answer this question.")
            print("The knowledge base doesn't contain relevant documents for this query.")
            sys.exit(0)

        context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": format_user_prompt(question, context)},
        ]
        
        answer = _create_chat_completion(client, messages)
        print(answer)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run 'make index' or 'python scripts/build_index.py' first.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
