from __future__ import annotations

import argparse
import os
import pickle
import sys
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for local imports when executed as a script.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from agentic_rag import AgenticRagEngine
from utils import retry_with_exponential_backoff

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL = os.getenv("MODEL", "gpt-4o")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
DEFAULT_MODE = os.getenv("RAG_MODE", "agentic")
DEFAULT_TOP_K = int(os.getenv("TOP_K", "8"))
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.0"))
DEFAULT_MAX_ITERATIONS = int(os.getenv("AGENTIC_MAX_ITERATIONS", "2"))
DEFAULT_LANGUAGE = os.getenv("OUTPUT_LANGUAGE", "en")


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
            "7. LANGUAGE INSTRUCTION: Respond in English. "
            "Maintain the same professional tone and citation format, and always use English for all explanations and summaries, even if the user's question is in another language."
        )

    return base_prompt


# Deprecated: Use get_system_prompt(language) instead for language-specific responses.
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
        temperature=temperature,
    )
    return response.choices[0].message.content


def retrieve(
    client: OpenAI,
    question: str,
    k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
):
    """
    Retrieve relevant document chunks using vector similarity search.

    Args:
        client: OpenAI client instance
        question: User's query
        k: Number of top results to return
        similarity_threshold: Minimum cosine similarity score (0.0-1.0)

    Returns:
        List of document chunks with metadata, filtered by similarity threshold
    """

    index, docs = _load_artifacts()

    query_vec = _create_embedding(client, question)
    query_array = np.array([query_vec], dtype="float32")
    faiss.normalize_L2(query_array)

    distances, indices = index.search(query_array, k)

    results = []
    for score, item_index in zip(distances[0], indices[0]):
        if 0 <= item_index < len(docs) and score >= similarity_threshold:
            results.append(docs[item_index])

    return results


def render_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{index + 1}] {hit['path']}\n{hit['text']}" for index, hit in enumerate(hits))


def answer_from_hits(
    client: OpenAI,
    question: str,
    hits: list[dict],
    *,
    language: str = DEFAULT_LANGUAGE,
    history: str | None = None,
) -> str:
    if not hits:
        return "I don't have enough information to answer this question."

    messages = [
        {"role": "system", "content": get_system_prompt(language)},
        {"role": "user", "content": format_user_prompt(question, render_context(hits), history)},
    ]
    return _create_chat_completion(client, messages)


def run_standard_query(
    client: OpenAI,
    question: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    history: str | None = None,
    k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> dict[str, Any]:
    hits = retrieve(client, question, k=k, similarity_threshold=similarity_threshold)
    answer = answer_from_hits(client, question, hits, language=language, history=history)
    return {
        "mode": "standard",
        "answer": answer,
        "hits": hits,
        "sub_queries": [question],
        "executed_queries": [question] if hits else [],
        "iterations": 1 if hits else 0,
        "reflection_notes": [],
        "retrieval_history": [],
    }


def run_agentic_query(
    client: OpenAI,
    question: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    history: str | None = None,
    k: int = 4,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    engine = AgenticRagEngine(
        chat_fn=lambda messages, temperature=0.2: _create_chat_completion(client, messages, temperature),
        retrieve_fn=lambda query, round_k, threshold: retrieve(
            client,
            query,
            k=round_k,
            similarity_threshold=threshold,
        ),
        synthesize_fn=lambda prompt_question, hits, response_language, conversation_history: answer_from_hits(
            client,
            prompt_question,
            hits,
            language=response_language,
            history=conversation_history,
        ),
        language=language,
        max_iterations=max_iterations,
        top_k=k,
        similarity_threshold=similarity_threshold,
    )
    result = engine.run(question, history=history)
    return {
        "mode": "agentic",
        "answer": result.answer,
        "hits": result.hits,
        "sub_queries": result.sub_queries,
        "executed_queries": result.executed_queries,
        "iterations": result.iterations,
        "reflection_notes": result.reflection_notes,
        "retrieval_history": result.retrieval_history,
    }


def run_query(
    client: OpenAI,
    question: str,
    *,
    mode: str = DEFAULT_MODE,
    language: str = DEFAULT_LANGUAGE,
    history: str | None = None,
    k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    if mode == "standard":
        return run_standard_query(
            client,
            question,
            language=language,
            history=history,
            k=k,
            similarity_threshold=similarity_threshold,
        )
    return run_agentic_query(
        client,
        question,
        language=language,
        history=history,
        k=min(k, 4),
        similarity_threshold=similarity_threshold,
        max_iterations=max_iterations,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Query the AI Knowledge Base.")
    parser.add_argument("question", nargs="?", help="Question to ask the knowledge base")
    parser.add_argument(
        "--mode",
        choices=["standard", "agentic"],
        default=DEFAULT_MODE if DEFAULT_MODE in {"standard", "agentic"} else "agentic",
        help="Retrieval mode to use",
    )
    parser.add_argument(
        "--language",
        choices=["en", "zh"],
        default=DEFAULT_LANGUAGE if DEFAULT_LANGUAGE in {"en", "zh"} else "en",
        help="Output language for the final answer",
    )
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help="Top-k results for retrieval")
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help="Minimum cosine similarity score to keep a retrieved chunk",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help="Maximum retrieval rounds in agentic mode",
    )
    parser.add_argument(
        "--show-trace",
        action="store_true",
        help="Print planner, retrieval, and reflection trace after the answer",
    )
    return parser.parse_args()


def _print_trace(result: dict[str, Any]) -> None:
    if result.get("mode") != "agentic":
        return

    print("\n=== Agentic Trace ===")
    print(f"Sub-queries: {result.get('sub_queries', [])}")
    print(f"Executed queries: {result.get('executed_queries', [])}")
    print(f"Iterations: {result.get('iterations', 0)}")

    retrieval_history = result.get("retrieval_history", [])
    if retrieval_history:
        print("Retrieval history:")
        for entry in retrieval_history:
            print(
                f"- iteration {entry['iteration']}: {entry['query']} "
                f"(new_hits={entry['new_hits']}, paths={entry['paths']})"
            )

    reflection_notes = result.get("reflection_notes", [])
    if reflection_notes:
        print("Reflection notes:")
        for note in reflection_notes:
            print(f"- {note}")


def main():
    args = parse_args()
    if not args.question:
        print('Usage: python scripts/ask.py "your question"')
        sys.exit(1)

    client = OpenAI()

    try:
        result = run_query(
            client,
            args.question,
            mode=args.mode,
            language=args.language,
            k=args.k,
            similarity_threshold=args.similarity_threshold,
            max_iterations=args.max_iterations,
        )
        print(result["answer"])
        if args.show_trace:
            _print_trace(result)
    except FileNotFoundError as error:
        print(f"Error: {error}")
        print("Please run 'make index' or 'python scripts/build_index.py' first.")
        sys.exit(1)
    except Exception as error:  # noqa: BLE001 - surface the failure for CLI callers
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
