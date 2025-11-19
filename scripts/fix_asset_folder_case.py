from collections import Counter, defaultdict
from pathlib import Path
import re

ROOT = Path("Knowledge_Base_MarkDown")
LINK_RE = re.compile(r"!\[[^\]]*]\(([^)]+)\)")


def build_folder_map() -> dict[str, Counter[str]]:
    folder_map: dict[str, Counter[str]] = defaultdict(Counter)
    for md in sorted(ROOT.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = md.read_text(encoding="latin1")
        for match in LINK_RE.finditer(text):
            ref = match.group(1)
            if ref.startswith("http://") or ref.startswith("https://"):
                continue
            rel = Path(ref)
            if not rel.parts:
                continue
            folder = rel.parts[0]
            folder_map[folder.lower()][folder] += 1
    return folder_map


def main() -> None:
    folder_map = build_folder_map()
    changes = []
    errors = []

    for folder in sorted(f for f in ROOT.iterdir() if f.is_dir()):
        if folder.name.lower() not in folder_map:
            continue
        counter = folder_map[folder.name.lower()]
        if folder.name in counter:
            continue
        candidate = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]
        target = ROOT / candidate
        if target.exists() and target.resolve() != folder.resolve():
            errors.append(f"target already exists {target}")
            continue
        temp = folder.with_name(folder.name + ".casefix")
        folder.rename(temp)
        temp.rename(target)
        changes.append((folder.name, candidate))

    for old, new in changes:
        print(f"Renamed {old} -> {new}")
    if errors:
        print("Skipped due to conflicts:")
        for err in errors:
            print(" ", err)


if __name__ == "__main__":
    main()
