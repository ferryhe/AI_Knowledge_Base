import os
from pathlib import Path

import streamlit as st
from openai import OpenAI

from scripts.ask import (
    INDEX_PATH,
    META_PATH,
    MODEL,
    SYSTEM_PROMPT,
    format_user_prompt,
    get_document_snippets,
    retrieve,
)

REPO_URL = "https://github.com/ferryhe/IAA_AI_Knowledge_Base"
DOCS_DIR = Path(__file__).resolve().parent.parent / "Knowledge_Base_MarkDown"
PREVIEW_CHAR_LIMIT = 4000


st.set_page_config(page_title="IAA Knowledge Base Q&A", layout="wide")
st.title("IAA Knowledge Base Q&A")

st.caption("Grounded Q&A over the Markdown corpus published in the public repository.")

has_api_key = bool(os.getenv("OPENAI_API_KEY"))
artifacts_ready = INDEX_PATH.exists() and META_PATH.exists()

if not has_api_key:
    st.warning("Set `OPENAI_API_KEY` in `AI_Agent/.env` before issuing queries.")
if not artifacts_ready:
    st.warning("Vector index not found. Run `make index` (or `python scripts/build_index.py`) first.")

if "history" not in st.session_state:
    st.session_state.history = []
if "show_help" not in st.session_state:
    st.session_state.show_help = False
if "pending_summary_prompt" not in st.session_state:
    st.session_state.pending_summary_prompt = None
chat_disabled = not (has_api_key and artifacts_ready)
user_query = st.chat_input(
    "Type a question about the Markdown documents...",
    disabled=chat_disabled,
    key="chat_prompt",
)

def load_markdown_catalog():
    if not DOCS_DIR.exists():
        return []
    return sorted(DOCS_DIR.rglob("*.md"))


def read_preview_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) <= PREVIEW_CHAR_LIMIT:
        return text
    return f"{text[:PREVIEW_CHAR_LIMIT]}\n...\n(Preview truncated to {PREVIEW_CHAR_LIMIT:,} characters.)"


md_files = load_markdown_catalog()
relative_paths = [str(path.relative_to(DOCS_DIR)) for path in md_files]
selected_file = None
selected_label = None

with st.sidebar:
    st.header("Knowledge Library")
    st.caption(f"Source: [{REPO_URL}]({REPO_URL})")
    st.metric("Markdown files", len(md_files))

    if st.button("How to use this agent"):
        st.session_state.show_help = not st.session_state.show_help
    if st.session_state.show_help:
        st.markdown(
            "- Browse the Markdown files to understand available context.\n"
            "- Ask focused questions using the main panel form.\n"
            "- Review answers with citations and inspect retrieved snippets."
        )

    filter_term = st.text_input("Filter files", placeholder="Type keywords", label_visibility="collapsed")

    filtered_options = relative_paths
    if filter_term:
        lowered = filter_term.lower()
        filtered_options = [path for path in relative_paths if lowered in path.lower()]

    if not filtered_options:
        st.info("No files match the current filter.")
        selected_file = None
    else:
        selected_label = st.selectbox(
            "Select a Markdown file", filtered_options, label_visibility="collapsed"
        )
        selected_file = md_files[relative_paths.index(selected_label)]
        github_blob = f"{REPO_URL}/blob/main/Knowledge_Base_MarkDown/{selected_label.replace(os.sep, '/')}"
        st.markdown(f"[Open in GitHub]({github_blob})")
        with st.expander("Preview", expanded=False):
            st.code(read_preview_text(selected_file), language="markdown")
        if st.button("Summarize this file", use_container_width=True, key="summarize_button"):
            if not has_api_key or not artifacts_ready:
                st.error("Set up the API key and index before requesting summaries.")
            else:
                summary_prompt = (
                    f"Summarize the key objectives, findings, and recommended actions from `{selected_label}`. "
                    "Use only content from that document."
                )
                doc_path = f"Knowledge_Base_MarkDown/{selected_label.replace(os.sep, '/')}"
                st.session_state.pending_summary_prompt = {
                    "question": summary_prompt,
                    "doc_path": doc_path,
                }

trigger_question = None
target_doc_path = None
pending_summary = st.session_state.pending_summary_prompt
if pending_summary:
    trigger_question = pending_summary.get("question")
    target_doc_path = pending_summary.get("doc_path")
    st.session_state.pending_summary_prompt = None
elif user_query is not None:
    if chat_disabled:
        st.error("Set up the API key and index before issuing queries.")
    else:
        cleaned = user_query.strip()
        if cleaned:
            trigger_question = cleaned
        else:
            st.warning("Please enter a question before submitting.")

def _format_history_for_prompt(max_turns: int = 3, max_answer_chars: int = 300) -> str | None:
    if not st.session_state.history:
        return None
    recent = st.session_state.history[-max_turns:]
    formatted = []
    for turn in recent:
        answer = turn["answer"]
        if len(answer) > max_answer_chars:
            answer = answer[:max_answer_chars].rstrip() + "..."
        formatted.append(f"Q: {turn['question']}\nA: {answer}")
    return "\n\n".join(formatted)


if trigger_question:
    try:
        with st.spinner("Retrieving and generating answer..."):
            client = OpenAI()
            if target_doc_path:
                hits = get_document_snippets(target_doc_path)
                if not hits:
                    raise FileNotFoundError(
                        f"Document `{target_doc_path}` is not present in the current index. "
                        "Rebuild the index to include it."
                    )
                convo_history = None
            else:
                hits = retrieve(client, trigger_question)
                convo_history = _format_history_for_prompt()
            context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": format_user_prompt(trigger_question, context, convo_history)},
            ]
            response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
            answer = response.choices[0].message.content
            st.session_state.history.append({"question": trigger_question, "answer": answer, "hits": hits})
    except FileNotFoundError as err:
        st.error(f"{err}")
    except Exception as err:  # noqa: BLE001 - surface user-friendly error
        st.error(f"Unable to generate an answer: {err}")

st.divider()
st.subheader("Conversation history")
st.caption(f"Responses cite Markdown sources from [{REPO_URL}]({REPO_URL}).")

if not st.session_state.history:
    st.info("No questions yet. Submit one to start building the conversation timeline.")
else:
    for entry in st.session_state.history:
        st.markdown(f"**You:** {entry['question']}")
        st.markdown(f"**AI:** {entry['answer']}")
        with st.expander("Retrieved snippets"):
            for i, hit in enumerate(entry["hits"], start=1):
                repo_link = f"{REPO_URL}/blob/main/{hit['path'].replace(os.sep, '/')}"
                st.markdown(f"**[{i}]** [{hit['path']} ↗]({repo_link})")
                st.code(hit["text"], language="markdown")
