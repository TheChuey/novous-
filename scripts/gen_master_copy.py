"""Generate a single markdown master copy of the entire Novous source tree."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "MASTER_COPY.md"

INCLUDE = {".py", ".js", ".css", ".html", ".json", ".md", ".bat", ".sh"}
EXCLUDE_DIRS = {"venv", "__pycache__", ".git", "node_modules", "test_agents"}
MAX_FILE_BYTES = 200_000


def collect() -> list[Path]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "MASTER_COPY.md" or path.name == "novous-ai-builder-prompt-v2.md":
            continue
        if path.suffix not in INCLUDE:
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def main() -> None:
    files = collect()
    chunks = ["# Novous Agent Factory — Master Copy", "",
              f"Generated from `{ROOT}` — {len(files)} files.", ""]
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        chunks.append(f"## `{rel}`")
        chunks.append("```" + path.suffix.lstrip("."))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            text = f"<unreadable: {exc}>"
        if len(text.encode("utf-8")) > MAX_FILE_BYTES:
            text = text[:MAX_FILE_BYTES] + "\n... <truncated> ..."
        chunks.append(text)
        chunks.append("```")
        chunks.append("")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()
