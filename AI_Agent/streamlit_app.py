import os
import locale
from pathlib import Path

import streamlit as st
from openai import OpenAI

from scripts.ask import (
    INDEX_PATH,
    META_PATH,
    MODEL,
    get_system_prompt,
    format_user_prompt,
    get_document_snippets,
    retrieve,
)

REPO_URL = "https://github.com/ferryhe/AI_Knowledge_Base"
DOCS_DIR = Path(__file__).resolve().parent.parent / "Knowledge_Base_MarkDown"
PREVIEW_CHAR_LIMIT = 4000

# Translation dictionaries
TRANSLATIONS = {
    "en": {
        "page_title": "AI Knowledge Base Q&A",
        "title": "AI Knowledge Base Q&A",
        "caption": "Grounded Q&A over the Markdown corpus published in the public repository.",
        "api_key_warning": "Set `OPENAI_API_KEY` in `AI_Agent/.env` before issuing queries.",
        "index_warning": "Vector index not found. Run `make index` (or `python scripts/build_index.py`) first.",
        "chat_placeholder": "Type a question about the Markdown documents...",
        "knowledge_library": "Knowledge Library",
        "source": "Source",
        "markdown_files": "Markdown files",
        "how_to_use": "How to use this agent",
        "help_text": "- Browse the Markdown files to understand available context.\n- Ask focused questions using the main panel form.\n- Review answers with citations and inspect retrieved snippets.",
        "filter_files": "Filter files",
        "filter_placeholder": "Type keywords",
        "select_file": "Select a Markdown file",
        "open_github": "Open in GitHub",
        "preview": "Preview",
        "summarize_file": "Summarize this file",
        "setup_error": "Set up the API key and index before requesting summaries.",
        "setup_query_error": "Set up the API key and index before issuing queries.",
        "empty_question_warning": "Please enter a question before submitting.",
        "retrieving": "Retrieving and generating answer...",
        "doc_not_found": "Document `{doc_path}` is not present in the current index. Rebuild the index to include it.",
        "generation_error": "Unable to generate an answer: {err}",
        "conversation_history": "Conversation history",
        "response_caption": "Responses cite Markdown sources from [{repo}]({repo}).",
        "no_questions": "No questions yet. Submit one to start building the conversation timeline.",
        "you": "You",
        "ai": "AI",
        "retrieved_snippets": "Retrieved snippets",
        "no_filter_match": "No files match the current filter.",
        "preview_truncated": "(Preview truncated to {limit:,} characters.)",
        "language": "Language / 语言",
    },
    "zh": {
        "page_title": "AI 知识库问答",
        "title": "AI 知识库问答",
        "caption": "基于公共仓库中发布的 Markdown 语料库进行有根据的问答。",
        "api_key_warning": "在发起查询之前，请在 `AI_Agent/.env` 中设置 `OPENAI_API_KEY`。",
        "index_warning": "未找到向量索引。请先运行 `make index`（或 `python scripts/build_index.py`）。",
        "chat_placeholder": "输入关于 Markdown 文档的问题...",
        "knowledge_library": "知识库",
        "source": "来源",
        "markdown_files": "Markdown 文件",
        "how_to_use": "如何使用此智能体",
        "help_text": "- 浏览 Markdown 文件以了解可用内容。\n- 使用主面板表单提出重点问题。\n- 查看带引用的答案并检查检索到的片段。",
        "filter_files": "筛选文件",
        "filter_placeholder": "输入关键词",
        "select_file": "选择 Markdown 文件",
        "open_github": "在 GitHub 中打开",
        "preview": "预览",
        "summarize_file": "总结此文件",
        "setup_error": "请在请求摘要之前设置 API 密钥和索引。",
        "setup_query_error": "请在发起查询之前设置 API 密钥和索引。",
        "empty_question_warning": "请在提交前输入问题。",
        "retrieving": "正在检索并生成答案...",
        "doc_not_found": "文档 `{doc_path}` 不在当前索引中。重建索引以包含它。",
        "generation_error": "无法生成答案：{err}",
        "conversation_history": "对话历史",
        "response_caption": "响应引用来自 [{repo}]({repo}) 的 Markdown 源。",
        "no_questions": "尚无问题。提交一个问题以开始构建对话时间线。",
        "you": "你",
        "ai": "AI",
        "retrieved_snippets": "检索到的片段",
        "no_filter_match": "没有文件匹配当前筛选条件。",
        "preview_truncated": "（预览截断为 {limit:,} 个字符。）",
        "language": "Language / 语言",
    }
}

def detect_system_language():
    """Detect system language and return 'en' or 'zh'"""
    try:
        lang = locale.getdefaultlocale()[0]
        if lang and lang.startswith('zh'):
            return 'zh'
    except Exception:
        pass
    return 'en'

def get_text(key, **kwargs):
    """Get translated text for the current language"""
    lang = st.session_state.get('language', 'en')
    # Validate language exists in TRANSLATIONS
    lang = lang if lang in TRANSLATIONS else 'en'
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS['en'][key])
    if kwargs:
        return text.format(**kwargs)
    return text


# Initialize language in session state before page config
if "language" not in st.session_state:
    st.session_state.language = detect_system_language()

st.set_page_config(page_title=get_text("page_title"), layout="wide")

# Header layout: title on the left, language toggle on the right
col1, col2 = st.columns([6, 1])
with col1:
    st.title(get_text("title"))
with col2:
    current_lang = st.session_state.language
    new_lang = st.selectbox(
        get_text("language"),
        options=["en", "zh"],
        index=0 if current_lang == "en" else 1,
        format_func=lambda x: "English" if x == "en" else "中文",
        key="language_selector"
    )
    if new_lang != st.session_state.language:
        st.session_state.language = new_lang
        st.rerun()

st.caption(get_text("caption"))

has_api_key = bool(os.getenv("OPENAI_API_KEY"))
artifacts_ready = INDEX_PATH.exists() and META_PATH.exists()

if not has_api_key:
    st.warning(get_text("api_key_warning"))
if not artifacts_ready:
    st.warning(get_text("index_warning"))

if "history" not in st.session_state:
    st.session_state.history = []
if "show_help" not in st.session_state:
    st.session_state.show_help = False
if "pending_summary_prompt" not in st.session_state:
    st.session_state.pending_summary_prompt = None
chat_disabled = not (has_api_key and artifacts_ready)
user_query = st.chat_input(
    get_text("chat_placeholder"),
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
    return f"{text[:PREVIEW_CHAR_LIMIT]}\n...\n{get_text('preview_truncated', limit=PREVIEW_CHAR_LIMIT)}"


md_files = load_markdown_catalog()
relative_paths = [str(path.relative_to(DOCS_DIR)) for path in md_files]
selected_file = None
selected_label = None

with st.sidebar:
    st.header(get_text("knowledge_library"))
    st.caption(f"{get_text('source')}: [{REPO_URL}]({REPO_URL})")
    st.metric(get_text("markdown_files"), len(md_files))

    if st.button(get_text("how_to_use")):
        st.session_state.show_help = not st.session_state.show_help
    if st.session_state.show_help:
        st.markdown(get_text("help_text"))

    filter_term = st.text_input(get_text("filter_files"), placeholder=get_text("filter_placeholder"), label_visibility="collapsed")

    filtered_options = relative_paths
    if filter_term:
        lowered = filter_term.lower()
        filtered_options = [path for path in relative_paths if lowered in path.lower()]

    if not filtered_options:
        st.info(get_text("no_filter_match"))
        selected_file = None
    else:
        selected_label = st.selectbox(
            get_text("select_file"), filtered_options, label_visibility="collapsed"
        )
        selected_file = md_files[relative_paths.index(selected_label)]
        github_blob = f"{REPO_URL}/blob/main/Knowledge_Base_MarkDown/{selected_label.replace(os.sep, '/')}"
        st.markdown(f"[{get_text('open_github')}]({github_blob})")
        with st.expander(get_text("preview"), expanded=False):
            st.code(read_preview_text(selected_file), language="markdown")
        if st.button(get_text("summarize_file"), use_container_width=True, key="summarize_button"):
            if not has_api_key or not artifacts_ready:
                st.error(get_text("setup_error"))
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
        st.error(get_text("setup_query_error"))
    else:
        cleaned = user_query.strip()
        if cleaned:
            trigger_question = cleaned
        else:
            st.warning(get_text("empty_question_warning"))

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
        with st.spinner(get_text("retrieving")):
            client = OpenAI()
            if target_doc_path:
                hits = get_document_snippets(target_doc_path)
                if not hits:
                    raise FileNotFoundError(
                        get_text("doc_not_found", doc_path=target_doc_path)
                    )
                convo_history = None
            else:
                hits = retrieve(client, trigger_question)
                convo_history = _format_history_for_prompt()
            context = "\n\n".join(f"[{i+1}] {hit['path']}\n{hit['text']}" for i, hit in enumerate(hits))
            
            # Get system prompt with language preference
            system_prompt = get_system_prompt(st.session_state.language)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": format_user_prompt(trigger_question, context, convo_history)},
            ]
            response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.2)
            answer = response.choices[0].message.content
            st.session_state.history.append({"question": trigger_question, "answer": answer, "hits": hits})
    except FileNotFoundError as err:
        st.error(f"{err}")
    except Exception as err:  # noqa: BLE001 - surface user-friendly error
        st.error(get_text("generation_error", err=err))

st.divider()
st.subheader(get_text("conversation_history"))
st.caption(get_text("response_caption", repo=REPO_URL))

if not st.session_state.history:
    st.info(get_text("no_questions"))
else:
    for entry in st.session_state.history:
        st.markdown(f"**{get_text('you')}:** {entry['question']}")
        st.markdown(f"**{get_text('ai')}:** {entry['answer']}")
        with st.expander(get_text("retrieved_snippets")):
            for i, hit in enumerate(entry["hits"], start=1):
                repo_link = f"{REPO_URL}/blob/main/{hit['path'].replace(os.sep, '/')}"
                st.markdown(f"**[{i}]** [{hit['path']} ↗]({repo_link})")
                st.code(hit["text"], language="markdown")
