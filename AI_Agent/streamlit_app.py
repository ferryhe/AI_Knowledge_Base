import os

import streamlit as st
from openai import OpenAI

from scripts.ask import INDEX_PATH, META_PATH, MODEL, SYSTEM_PROMPT, retrieve


st.set_page_config(page_title="IAA Knowledge Base Q&A", layout="wide")
st.title("IAA Knowledge Base Q&A")

st.write(
    "Ask questions about the Markdown documents stored in `Knowledge_Base_MarkDown/`. "
    "Answers are generated with citations pointing to the source files."
)

has_api_key = bool(os.getenv("OPENAI_API_KEY"))
artifacts_ready = INDEX_PATH.exists() and META_PATH.exists()

if not has_api_key:
    st.warning("Set `OPENAI_API_KEY` in `AI_Agent/.env` before issuing queries.")
if not artifacts_ready:
    st.warning("Vector index not found. Run `make index` (or `python scripts/build_index.py`) first.")

question = st.text_area(
    "Question", placeholder="e.g., Summarize the July 2025 AI governance consultation draft"
)
ask_button = st.button(
    "Ask", use_container_width=True, disabled=not (has_api_key and artifacts_ready)
)

if "history" not in st.session_state:
    st.session_state.history = []

if ask_button and question.strip():
    try:
        with st.spinner("Retrieving and generating answer..."):
            client = OpenAI()
            hits = retrieve(client, question)
            context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Retrieved snippets:\n{context}\n\nQuestion: {question}"},
            ]
            response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
            answer = response.choices[0].message.content
            st.session_state.history.insert(0, {"question": question, "answer": answer, "hits": hits})
        question = ""
    except FileNotFoundError as err:
        st.error(f"{err}")
    except Exception as err:  # noqa: BLE001 - surface user-friendly error
        st.error(f"Unable to generate an answer: {err}")

for entry in st.session_state.history:
    st.markdown(f"### Q: {entry['question']}")
    st.markdown(entry["answer"])
    with st.expander("Retrieved snippets"):
        for i, hit in enumerate(entry["hits"], start=1):
            st.markdown(f"**[{i}] {hit['path']}**")
            st.code(hit["text"], language="markdown")
