import os
import pickle
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

MODEL = os.getenv("MODEL", "gpt-4o")
EMB_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
INDEX_PATH = Path(os.getenv("INDEX_PATH", PROJECT_ROOT / "knowledge_base.faiss")).resolve()
META_PATH = Path(os.getenv("META_PATH", PROJECT_ROOT / "knowledge_base.meta.pkl")).resolve()
_INDEX_CACHE = None
_DOCS_CACHE = None

SYSTEM_PROMPT = (
    "You are the documentation expert for the IAA AI Knowledge Base. "
    "Every response must stay within the retrieved snippets and cite evidence using the snippet number plus file path "
    "in the format `[n] path/to/file.md`. Structure answers with a short summary followed by bullet points of "
    "supporting evidence. If the snippets do not contain the answer, reply 'Not sure' and recommend the most relevant "
    "Markdown file to inspect."
)


def format_user_prompt(question: str, context: str) -> str:
    return (
        "You will receive Markdown excerpts from the IAA AI Knowledge Base. Each excerpt already includes a numeric tag "
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


def retrieve(client: OpenAI, question: str, k: int = 8):
    index, docs = _load_artifacts()

    query_vec = client.embeddings.create(model=EMB_MODEL, input=[question]).data[0].embedding
    query_array = np.array([query_vec], dtype="float32")
    faiss.normalize_L2(query_array)

    distances, indices = index.search(query_array, k)
    return [docs[i] for i in indices[0] if 0 <= i < len(docs)]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ask.py \"your question\"")
        sys.exit(1)

    question = sys.argv[1]
    client = OpenAI()
    hits = retrieve(client, question)

    context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_user_prompt(question, context)},
    ]
    response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
