"""Regenerate the repository listing files for the tools and file_manager packages."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_scope import ROOT

LISTINGS = {
    "tools_listing.txt": "tools",
    "file_manager_listing.txt": "file_manager",
}


def collect(package: str) -> list[str]:
    entries = []
    for path in (ROOT / package).rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix.lower() == ".pyc":
            continue
        entries.append(path.relative_to(ROOT).as_posix())
    return sorted(entries)


def main() -> None:
    for filename, package in LISTINGS.items():
        entries = collect(package)
        target = ROOT / filename
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(entries))
            handle.write("\n")
        print(f"Wrote {target} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
