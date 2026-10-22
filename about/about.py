"""Sync app identity from about.md to the index page and app documentation."""

import argparse
import html
import re
import sys
import time
from pathlib import Path


ABOUT_DIR = Path(__file__).resolve().parent
ROOT = ABOUT_DIR.parent
SOURCE = ABOUT_DIR / "about.md"
INDEX = ROOT / "frontend" / "pages" / "index.html"
DOCUMENTATION = ROOT / "app_documentation" / "ABOUT.md"
LOGO_PATTERN = re.compile(
    r'<(?:span|h1)\s+class="logo-text"[^>]*>.*?</(?:span|h1)>',
    re.DOTALL,
)
TITLE_PATTERN = re.compile(r"<title>.*?</title>", re.DOTALL | re.IGNORECASE)
SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$")


def parse_about(markdown: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_section = None
    for line in markdown.splitlines():
        match = SECTION_PATTERN.match(line)
        if match:
            current_section = match.group(1).strip().casefold()
            if current_section in sections:
                raise ValueError(f"Duplicate section in about.md: {match.group(1)}")
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(line)

    def value_for(section: str) -> str:
        lines = [line.strip() for line in sections.get(section, []) if line.strip()]
        value = " ".join(lines).strip()
        if section == "name":
            value = re.sub(r"^Name of the Application:\s*", "", value, flags=re.IGNORECASE)
        return value

    heading_section = "h1" if "h1" in sections else "header"
    values = {
        "name": value_for("name"),
        "browser_title": value_for("browser tab"),
        "h1": value_for(heading_section),
        "description": value_for("description"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise ValueError(
            "about.md must include non-empty ## Name, ## Browser Tab, "
            "## h1 (or ## header), "
            "and ## Description sections; "
            f"missing: {', '.join(missing)}"
        )
    return values


def replace_file(path: Path, content: str) -> None:
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def sync(markdown: str) -> None:
    values = parse_about(markdown)
    index_html = INDEX.read_text(encoding="utf-8")
    if len(LOGO_PATTERN.findall(index_html)) != 1:
        raise RuntimeError(f"Expected exactly one app logo heading in {INDEX}.")
    if len(TITLE_PATTERN.findall(index_html)) != 1:
        raise RuntimeError(f"Expected exactly one browser tab title in {INDEX}.")
    heading = (
        '<h1 class="logo-text" data-about-managed="true" '
        'style="font-size: inherit; font-weight: inherit; line-height: inherit; margin: 0;">'
        f'{html.escape(values["h1"])}</h1>'
    )
    updated_index = LOGO_PATTERN.sub(heading, index_html, count=1)
    title = f"<title>{html.escape(values['browser_title'])}</title>"
    updated_index = TITLE_PATTERN.sub(title, updated_index, count=1)

    documentation = markdown.rstrip() + "\n"
    replace_file(INDEX, updated_index)
    replace_file(DOCUMENTATION, documentation)
    print(f"Synced app heading, browser tab title, and documentation for {values['name']}.")


def watch() -> None:
    sync(SOURCE.read_text(encoding="utf-8-sig"))
    last_content = SOURCE.read_bytes()
    candidate = None
    changed_at = 0.0
    print(f"Watching {SOURCE} for changes. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(0.5)
            try:
                content = SOURCE.read_bytes()
            except OSError as exc:
                print(f"Could not read {SOURCE}: {exc}", file=sys.stderr)
                continue
            if content == last_content:
                candidate = None
                continue
            if content != candidate:
                candidate = content
                changed_at = time.monotonic()
                continue
            if time.monotonic() - changed_at < 0.75:
                continue
            try:
                sync(content.decode("utf-8-sig"))
            except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
                print(f"Could not sync about.md: {exc}", file=sys.stderr)
            else:
                last_content = content
            candidate = None
    except KeyboardInterrupt:
        print("\nStopped watching about.md.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync about/about.md to the app heading and app documentation."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="keep running and sync whenever about.md changes",
    )
    args = parser.parse_args()
    if args.watch:
        watch()
    else:
        sync(SOURCE.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    main()
