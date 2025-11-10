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

SYSTEM_PROMPT = (
    "You are the documentation expert for the IAA AI Knowledge Base. "
    "Answer strictly based on the retrieved snippets, cite the file path for every key statement, "
    "and reply 'Not sure' if the evidence is missing."
)


def _latest_user_question(messages):
    for item in reversed(messages):
        if item.get("role") == "user":
            return item.get("content", "")
    return ""


def _retrieve(client: OpenAI, question: str, k: int = 8):
    if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
        raise FileNotFoundError(
            "Missing index or metadata files. "
            f"Expected:\n  {INDEX_PATH}\n  {META_PATH}\n"
            "Run scripts/build_index.py and mount the results into the container."
        )

    index = faiss.read_index(INDEX_PATH)
    docs = pickle.load(open(META_PATH, "rb"))

    query_vec = client.embeddings.create(model=EMB_MODEL, input=[question]).data[0].embedding
    distances, indices = index.search(np.array([query_vec], dtype="float32"), k)
    return [docs[i] for i in indices[0]]


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
