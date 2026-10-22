"""Generate a single markdown master copy of the entire Novous source tree."""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_scope import ROOT, fence_for, iter_source_files

TODAY = datetime.now().strftime("%Y%m%d")
OUT = ROOT / "app_documentation" / f"MASTER_COPY_{TODAY}.md"

MAX_FILE_BYTES = 200_000

try:
    COMMIT = os.popen("git rev-parse --short HEAD").read().strip()
except Exception:
    COMMIT = "unknown"


def get_lang(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    return {
        "py": "python",
        "js": "javascript",
        "json": "json",
        "html": "html",
        "css": "css",
        "md": "markdown",
        "txt": "text",
        "bat": "batch",
        "sh": "bash",
        "yaml": "yaml",
        "yml": "yaml",
        "cfg": "ini",
        "ini": "ini",
    }.get(ext, ext)


def read_source(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"<unreadable: {exc}>"
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        text = text[:MAX_FILE_BYTES] + "\n... <truncated> ..."
    return text


def main() -> None:
    files = list(iter_source_files(ROOT))
    chunks = ["# Novous — Master Copy", "",
              f"Complete source copy of the Novous repository — {len(files)} files.",
              f"Date: {datetime.now().strftime('%Y-%m-%d')}",
              f"Commit: {COMMIT}", ""]
    for rel, path in files:
        text = read_source(path)
        fence = fence_for(text)
        chunks.append(f"## `{rel}`")
        chunks.append(f"{fence}{get_lang(path.suffix)}")
        chunks.append(text)
        chunks.append(fence)
        chunks.append("")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {len(files)} files)")


if __name__ == "__main__":
    main()
