from pathlib import Path

ROOT = Path("Knowledge_Base_MarkDown")
CONTENTS_HEADING = "contents"


def matches_contents_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return False
    return CONTENTS_HEADING in stripped.lower()


def fix_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin1")
    lines = text.splitlines()
    updated_lines = []
    in_contents = False
    changed = False
    for line in lines:
        stripped = line.strip()
        if matches_contents_heading(line):
            in_contents = True
            updated_lines.append(line)
            continue
        if in_contents:
            if not stripped or stripped.startswith("#"):
                in_contents = False
                updated_lines.append(line)
                continue
            if not line.endswith("  "):
                line = f"{line.rstrip()}  "
                changed = True
        updated_lines.append(line)
    if changed:
        path.write_text("\n".join(updated_lines) + ("\n" if text.endswith("\n") else ""))
    return changed


def main():
    changed_any = False
    for md in sorted(ROOT.rglob("*.md")):
        if fix_file(md):
            print(f"Updated contents spacing in {md}")
            changed_any = True
    if not changed_any:
        print("No contents blocks needed adjustment.")


if __name__ == "__main__":
    main()
