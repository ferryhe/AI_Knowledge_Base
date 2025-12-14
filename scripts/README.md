# Scripts Overview

Run these from the repo root (adjust the Python path to your venv, e.g., `AI_Agent/.venv/Scripts/python.exe`).

## update_catalog_metadata.py
- Generates publish dates and summaries for each markdown in `Knowledge_Base_MarkDown` using OpenAI, then rebuilds the `## Catalog` block in `README.md`.
- Requires `OPENAI_API_KEY` in `AI_Agent/.env`; depends on `openai` and `python-dotenv`.
- Usage: `python scripts/update_catalog_metadata.py`
- Notes: processes the first ~4000 chars of each file, pauses between API calls, and expects an existing `## Catalog` section in `README.md`.

## find_original_links.py
- Searches the web for likely original sources of each markdown file and ranks results (optionally with OpenAI).
- Outputs `original_sources.md`, archives each run under `working_runs/`, and writes high-confidence hits to `final_original_sources.md`.
- Supports backends `serpapi` (default, needs `SERPAPI_API_KEY`), `langsearch` (`LANGSEARCH_API_KEY`), or `duckduckgo`; use `--no-ai` to disable OpenAI ranking.
- Key flags: `--limit` (test a subset), `--skip-existing-final` (skip files already in `final_original_sources.md`).
- Usage: `python scripts/find_original_links.py --backend serpapi --max-searches 250`

## fix_asset_folder_case.py
- Aligns actual asset folder names with the most common casing used in markdown image links, fixing case-sensitivity issues.
- Renames folders within `Knowledge_Base_MarkDown` (via a temporary rename) but does not rewrite markdown paths.
- Usage: `python scripts/fix_asset_folder_case.py`
- Occasional cleanup tool; run only when casing drifts across environments.

## fix_contents_spacing.py
- Ensures lines under a `# Contents` (case-insensitive) heading end with two spaces so Markdown preserves line breaks.
- Scans all markdown files under `Knowledge_Base_MarkDown` and rewrites only files that need changes.
- Usage: `python scripts/fix_contents_spacing.py`
- Ad hoc formatter; run as needed (e.g., before publishing or after bulk imports).
