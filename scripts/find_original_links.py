"""
Search Knowledge_Base_MarkDown documents on the web and guess their original links.

Usage examples (run from the repo root):
    # Quick dry run without LLM (cheapest)
    AI_Agent/.venv/Scripts/python.exe scripts/find_original_links.py --no-ai --limit 5

    # Full run using GPT (requires OPENAI_API_KEY in AI_Agent/.env)
    AI_Agent/.venv/Scripts/python.exe scripts/find_original_links.py

    # Use SerpAPI (needs SERPAPI_API_KEY) for more reliable search results
    AI_Agent/.venv/Scripts/python.exe scripts/find_original_links.py --backend serpapi --max-searches 250

The script writes a Markdown report (original_sources.md) at the repo root with one
row per Markdown file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Sequence

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None  # type: ignore

# Silence noisy rename warnings from duckduckgo_search.
warnings.filterwarnings(
    "ignore",
    message="This package (`duckduckgo_search`) has been renamed to `ddgs`",
    category=RuntimeWarning,
)


ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "Knowledge_Base_MarkDown"
DEFAULT_OUTPUT = ROOT / "original_sources.md"
FINAL_OUTPUT = ROOT / "final_original_sources.md"
DEFAULT_ENV = ROOT / "AI_Agent" / ".env"
ARCHIVE_DIR = ROOT / "working_runs"


@dataclass
class Document:
    path: Path
    title: str
    snippet: str


def fail_if_missing_ddg() -> None:
    if DDGS is None:
        raise SystemExit(
            "duckduckgo_search is required. Install it with:\n"
            "AI_Agent/.venv/Scripts/python.exe -m pip install duckduckgo-search"
        )


def load_openai_client(env_path: Path, disabled: bool) -> Optional[OpenAI]:
    if disabled:
        return None
    if OpenAI is None:
        print("openai package not installed; falling back to heuristics.")
        return None
    if load_dotenv:
        load_dotenv(env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not found; falling back to heuristics.")
        return None
    return OpenAI(api_key=api_key)


def extract_title_and_snippet(path: Path, max_chars: int = 600) -> Document:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = raw.splitlines()
    title = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped.lstrip("#").strip()
            break
    if not title:
        cleaned = re.sub(r"[_\-]+", " ", path.stem)
        title = cleaned.strip()

    snippet_parts: list[str] = []
    total = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("!["):
            continue
        if stripped.startswith("_Note"):
            continue
        total += len(stripped)
        snippet_parts.append(stripped)
        if total >= max_chars:
            break
    snippet = " ".join(snippet_parts)[:max_chars]
    return Document(path=path, title=title, snippet=snippet)


def build_query(doc: Document) -> str:
    stem_terms = re.sub(r"[_\-]+", " ", doc.path.stem)
    year_match = re.search(r"(19|20)\d{2}", doc.path.stem)
    title_phrase = f"\"{doc.title}\""
    parts = [title_phrase]
    if year_match:
        parts.append(year_match.group(0))
    if stem_terms.lower() not in doc.title.lower():
        parts.append(stem_terms)
    parts.append("pdf")
    return " ".join(parts)


def search_duckduckgo(query: str, max_results: int) -> list[dict[str, str]]:
    fail_if_missing_ddg()
    results: list[dict[str, str]] = []
    with DDGS() as ddgs:  # type: ignore
        for res in ddgs.text(
            query,
            max_results=max_results,
            safesearch="moderate",
            timelimit=None,
            backend="api",
            region="us-en",
        ):
            results.append(
                {
                    "title": res.get("title", "") if isinstance(res, dict) else "",
                    "href": res.get("href", "") if isinstance(res, dict) else "",
                    "body": res.get("body", "") if isinstance(res, dict) else "",
                }
            )
    return results


def search_serpapi(query: str, max_results: int) -> list[dict[str, str]]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        print("SERPAPI_API_KEY missing; falling back to DuckDuckGo.")
        return []
    params = {
        "engine": "google",
        "q": query,
        "num": max_results,
        "api_key": api_key,
    }
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=25)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"SerpAPI request failed: {exc}")
        return []
    data = resp.json()
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    organic = data.get("organic_results", [])
    results: list[dict[str, str]] = []
    for item in organic[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "href": item.get("link", ""),
                "body": item.get("snippet", ""),
            }
        )
    return results


def search_langsearch(query: str, max_results: int) -> list[dict[str, str]]:
    api_key = os.getenv("LANGSEARCH_API_KEY")
    if not api_key:
        print("LANGSEARCH_API_KEY missing; falling back to DuckDuckGo.")
        return []
    endpoint = os.getenv("LANGSEARCH_ENDPOINT", "https://api.langsearch.com/v1/web-search")
    payload = {"query": query, "count": max_results, "freshness": "noLimit", "summary": False}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=25)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"LangSearch request failed: {exc}")
        return []
    data = resp.json()
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data["data"]
    raw = (
        data.get("webPages", {}).get("value")
        if isinstance(data.get("webPages"), dict)
        else None
    )
    if raw is None:
        raw = data.get("web") or data.get("results") or data.get("data") or []
    candidates: list[dict[str, str]] = []
    # Handle nested dict structures, e.g., {"results": {"web": [...]}}
    if isinstance(raw, dict):
        for key in ("web", "results", "items", "data"):
            value = raw.get(key)
            if isinstance(value, list):
                raw = value
                break
        else:
            raw = list(raw.values())
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or ""
            href = item.get("url", "") or item.get("link", "")
            body = item.get("snippet", "") or item.get("summary", "") or item.get("description", "")
            candidates.append({"title": title, "href": href, "body": body})
    results: list[dict[str, str]] = candidates[:max_results]
    return results


def check_link(url: str, timeout: float = 10.0) -> bool:
    if not url:
        return False
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if 200 <= resp.status_code < 400:
            return True
        resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        return 200 <= resp.status_code < 400
    except Exception:
        return False


def strip_json_block(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
    return stripped.strip()


def ai_rank(
    client: OpenAI, model: str, doc: Document, results: Sequence[dict[str, str]]
) -> Optional[tuple[int, str, str]]:
    if not results:
        return None
    summary_lines = []
    for idx, res in enumerate(results, start=1):
        summary_lines.append(
            f"{idx}. Title: {res.get('title','')}\n"
            f"URL: {res.get('href','')}\n"
            f"Snippet: {res.get('body','')}"
        )
    prompt = (
        "Pick the search result that is most likely the original/public source link for this document. "
        "Prefer authoritative publishers and PDF/HTML originals over re-posts. "
        "Reply with JSON: {\"choice\": <index or null>, \"confidence\": \"low|medium|high\", \"reason\": \"...\"}."
    )
    messages = [
        {"role": "system", "content": "You rank links to find original documents."},
        {
            "role": "user",
            "content": (
                f"File name: {doc.path.name}\n"
                f"Title: {doc.title}\n"
                f"Snippet: {doc.snippet}\n\n"
                "Search results:\n" + "\n".join(summary_lines) + "\n\n" + prompt
            ),
        },
    ]
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=0.0, max_tokens=200
        )
    except Exception as exc:  # pragma: no cover - defensive
        print(f"OpenAI ranking failed: {exc}")
        return None
    content = response.choices[0].message.content or ""
    content = strip_json_block(content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    choice = data.get("choice")
    if isinstance(choice, int):
        idx = choice - 1
        if 0 <= idx < len(results):
            return idx, str(data.get("confidence", "ai")), str(data.get("reason", "ai-ranked"))
    return None


def heuristic_score(result: dict[str, str], doc: Document) -> float:
    title_match = SequenceMatcher(
        None, doc.title.lower(), result.get("title", "").lower()
    ).ratio()
    token_overlap = len(
        set(doc.title.lower().split()) & set(result.get("title", "").lower().split())
    )
    url = result.get("href", "").lower()
    url_bonus = 0.08 if doc.path.stem.split("_")[0].lower() in url else 0.0
    pdf_bonus = 0.08 if url.endswith(".pdf") else 0.0
    body_overlap = len(
        set(doc.title.lower().split()) & set(result.get("body", "").lower().split())
    )
    return title_match + 0.02 * token_overlap + 0.01 * body_overlap + url_bonus + pdf_bonus


def pick_result(
    doc: Document,
    results: list[dict[str, str]],
    ai_client: Optional[OpenAI],
    model: str,
) -> tuple[Optional[str], str, str]:
    if ai_client:
        ai_choice = ai_rank(ai_client, model, doc, results)
        if ai_choice:
            idx, confidence, reason = ai_choice
            return results[idx].get("href", ""), confidence, reason

    best_href = None
    best_score = -1.0
    best_reason = "heuristic"
    for res in results:
        score = heuristic_score(res, doc)
        if score > best_score:
            best_score = score
            best_href = res.get("href", "")
            best_reason = f"heuristic score {score:.2f}"
    confidence = "high" if best_score >= 1.2 else "medium" if best_score >= 0.9 else "low"
    return best_href, confidence, best_reason


def write_report(rows: Sequence[dict[str, str]], output: Path) -> None:
    lines = [
        "# Original Document Links",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "| File | Title | Proposed original link | Confidence | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        link = row["link"]
        link_cell = f"[link]({link})" if link else "not found"
        lines.append(
            f"| `{row['file']}` | {row['title']} | {link_cell} | {row['confidence']} | {row['notes']} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {output}")


def write_final_report(rows: Sequence[dict[str, str]], output: Path) -> None:
    filtered = []
    for r in rows:
        if r.get("confidence") != "high" or not r.get("link"):
            continue
        if not check_link(r["link"]):
            continue
        filtered.append(r)
    lines = [
        "# Final Original Sources (high confidence)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "| # | File | Link |",
        "| --- | --- | --- |",
    ]
    for idx, row in enumerate(filtered, start=1):
        link_cell = f"[link]({row['link']})"
        lines.append(f"| {idx} | `{row['file']}` | {link_cell} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(filtered)} high-confidence rows to {output}")


def load_final_filenames(path: Path) -> set[str]:
    if not path.exists():
        return set()
    names = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        name = parts[1].strip("`").strip()
        if name:
            names.add(name)
    return names


def archive_report(output_path: Path, archive_dir: Path) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = archive_dir / f"{output_path.stem}_{stamp}.md"
    target.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Archived report to {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find original links for markdown files.")
    parser.add_argument(
        "--kb-dir",
        default=str(KB_DIR),
        help="Path to the Knowledge_Base_MarkDown folder (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output Markdown report path (default: %(default)s).",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=8,
        help="Number of search results to fetch per query (default: %(default)s).",
    )
    parser.add_argument(
        "--max-searches",
        type=int,
        default=250,
        help="Maximum number of paid searches to issue (default: %(default)s; useful for SerpAPI/LangSearch caps).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of files to process (useful for testing).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Delay between searches in seconds (default: %(default)s).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model for ranking (default: %(default)s).",
    )
    parser.add_argument(
        "--backend",
        choices=["duckduckgo", "serpapi", "langsearch"],
        default="serpapi",
        help="Search backend to use (default: %(default)s). SerpAPI requires SERPAPI_API_KEY; LangSearch uses LANGSEARCH_API_KEY.",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable OpenAI ranking and use heuristics only.",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV),
        help="Path to .env file containing OPENAI_API_KEY (default: %(default)s).",
    )
    parser.add_argument(
        "--final-output",
        default=str(FINAL_OUTPUT),
        help="Path to write the high-confidence subset (default: %(default)s).",
    )
    parser.add_argument(
        "--archive-dir",
        default=str(ARCHIVE_DIR),
        help="Directory to archive each original_sources.md run with a timestamp (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-existing-final",
        action="store_true",
        help="Skip files already present in final_original_sources.md when searching.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    kb_dir = Path(args.kb_dir)
    output_path = Path(args.output)
    env_path = Path(args.env_file)

    if not kb_dir.exists():
        raise SystemExit(f"Knowledge base directory not found: {kb_dir}")

    if load_dotenv:
        load_dotenv(env_path)

    ai_client = load_openai_client(env_path, args.no_ai)
    docs = sorted(kb_dir.glob("*.md"))
    if args.skip_existing_final:
        existing = load_final_filenames(Path(args.final_output))
        docs = [d for d in docs if d.name not in existing]
        print(f"Skipping {len(existing)} files already in final report; {len(docs)} remaining.")

    if args.limit:
        docs = docs[: args.limit]

    rows: list[dict[str, str]] = []
    total = len(docs)
    searches_used = 0
    for idx, path in enumerate(docs, start=1):
        doc = extract_title_and_snippet(path)
        query = build_query(doc)
        print(f"[{idx}/{total}] Searching for {path.name} ...")
        if args.backend == "serpapi":
            if searches_used >= args.max_searches:
                rows.append(
                    {
                        "file": path.name,
                        "title": doc.title,
                        "link": "",
                        "confidence": "none",
                        "notes": "skipped: SerpAPI search budget exceeded",
                    }
                )
                continue
            results = search_serpapi(query, max_results=args.max_results)
            searches_used += 1
            if not results:
                results = search_duckduckgo(query, max_results=args.max_results)
        elif args.backend == "langsearch":
            if searches_used >= args.max_searches:
                rows.append(
                    {
                        "file": path.name,
                        "title": doc.title,
                        "link": "",
                        "confidence": "none",
                        "notes": "skipped: LangSearch search budget exceeded",
                    }
                )
                continue
            results = search_langsearch(query, max_results=args.max_results)
            searches_used += 1
            if not results:
                results = search_duckduckgo(query, max_results=args.max_results)
        else:
            results = search_duckduckgo(query, max_results=args.max_results)
        if not results:
            rows.append(
                {
                    "file": path.name,
                    "title": doc.title,
                    "link": "",
                    "confidence": "none",
                    "notes": "no search results",
                }
            )
            continue
        link, confidence, notes = pick_result(doc, results, ai_client, args.model)
        rows.append(
            {
                "file": path.name,
                "title": doc.title,
                "link": link or "",
                "confidence": confidence,
                "notes": notes,
            }
        )
        time.sleep(args.delay)

    write_report(rows, output_path)
    archive_report(output_path, Path(args.archive_dir))
    write_final_report(rows, Path(args.final_output))


if __name__ == "__main__":
    main()
