"""Prompt Part Assembler & Category Manifest for the prompt builder."""

import json
import re
import shutil
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "PromptBuilderFiles"
CATEGORIES_FILE = PROMPT_DIR / "categories.json"
PARTS_DIR = PROMPT_DIR / "parts"


def _ensure_dirs() -> None:
    PARTS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "item"


def load_categories() -> list[dict]:
    if not CATEGORIES_FILE.is_file():
        return []
    data = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return data.get("categories", [])


def save_categories(categories: list[dict]) -> None:
    _ensure_dirs()
    CATEGORIES_FILE.write_text(
        json.dumps({"categories": categories}, indent=2) + "\n", encoding="utf-8"
    )


def add_category(
    cat_id: str, name: str, description: str = "", required_header: str = ""
) -> dict:
    slug = _slugify(cat_id)
    categories = load_categories()
    if any(c["id"] == slug for c in categories):
        raise ValueError(f"Category '{slug}' already exists.")

    new_cat = {
        "id": slug,
        "name": name.strip(),
        "description": description.strip(),
    }
    if required_header.strip():
        new_cat["required_header"] = required_header.strip()

    categories.append(new_cat)
    save_categories(categories)

    (PARTS_DIR / slug).mkdir(parents=True, exist_ok=True)
    return new_cat


def delete_category(cat_id: str) -> dict:
    categories = load_categories()
    cat_to_remove = next((c for c in categories if c["id"] == cat_id), None)
    if not cat_to_remove:
        raise ValueError(f"Category '{cat_id}' not found.")

    updated = [c for c in categories if c["id"] != cat_id]
    save_categories(updated)

    cat_dir = PARTS_DIR / cat_id
    if cat_dir.is_dir():
        shutil.rmtree(cat_dir)

    return {"deleted": cat_id}


def load_parts(category: str | None = None) -> list[dict]:
    """Each part is a markdown file: parts/<category>/<slug>.md with optional frontmatter."""
    _ensure_dirs()
    parts = []
    if not PARTS_DIR.is_dir():
        return parts
    for part_file in sorted(PARTS_DIR.rglob("*.md")):
        raw = part_file.read_text(encoding="utf-8")
        rel = part_file.relative_to(PARTS_DIR).as_posix()
        cat = rel.split("/")[0] if "/" in rel else "misc"
        title = part_file.stem.replace("-", " ").replace("_", " ").title()
        body = raw
        if raw.startswith("---"):
            chunks = raw.split("---", 2)
            if len(chunks) >= 3:
                for line in chunks[1].strip().splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        if key.strip() == "title":
                            title = value.strip()
                body = chunks[2].strip()
        if category and cat != category:
            continue
        parts.append({
            "id": f"{cat}/{part_file.stem}",
            "category": cat,
            "title": title,
            "content": body,
            "path": f"PromptBuilderFiles/parts/{rel}",
        })
    return parts


def add_part(
    category: str, title: str, content: str, part_id: str | None = None
) -> dict:
    _ensure_dirs()
    cat_slug = _slugify(category)
    part_slug = _slugify(part_id or title)

    cat_dir = PARTS_DIR / cat_slug
    cat_dir.mkdir(parents=True, exist_ok=True)

    file_path = cat_dir / f"{part_slug}.md"
    file_content = f"---\ntitle: {title.strip()}\n---\n\n{content.strip()}\n"
    file_path.write_text(file_content, encoding="utf-8")

    return {
        "id": f"{cat_slug}/{part_slug}",
        "category": cat_slug,
        "title": title.strip(),
        "content": content.strip(),
        "path": f"PromptBuilderFiles/parts/{cat_slug}/{part_slug}.md",
    }


def delete_part(part_id: str) -> dict:
    _ensure_dirs()
    if "/" not in part_id:
        raise ValueError("Invalid part ID format. Expected 'category/part_slug'.")

    cat, slug = part_id.split("/", 1)
    file_path = (PARTS_DIR / cat / f"{slug}.md").resolve()

    try:
        file_path.relative_to(PARTS_DIR.resolve())
    except ValueError:
        raise ValueError("Access outside parts directory is forbidden.")

    if not file_path.is_file():
        raise FileNotFoundError(f"Part '{part_id}' not found.")

    file_path.unlink()
    return {"deleted": part_id}


def get_manifest() -> dict:
    """Full categories manifest with each category's available parts."""
    categories = load_categories()
    parts = load_parts()
    for cat in categories:
        cat["parts"] = [p for p in parts if p["category"] == cat["id"]]
    return {
        "categories": categories,
        "uncategorized_parts": [
            p for p in parts if p["category"] not in {c["id"] for c in categories}
        ],
        "total_parts": len(parts),
    }


def assemble_prompt(selected_ids: list[str], extra_instructions: str = "") -> dict:
    """Compose a single prompt from the selected part ids in category order."""
    categories = load_categories()
    order = {c["id"]: i for i, c in enumerate(categories)}
    parts = {p["id"]: p for p in load_parts()}

    chosen = [parts[pid] for pid in selected_ids if pid in parts]
    chosen.sort(key=lambda p: (order.get(p["category"], 999), p["title"]))

    sections = []
    for part in chosen:
        sections.append(f"## {part['title']}\n\n{part['content'].strip()}")

    if extra_instructions.strip():
        sections.append(f"## Additional Instructions\n\n{extra_instructions.strip()}")

    prompt = "\n\n".join(sections)
    return {
        "prompt": prompt,
        "selected": [p["id"] for p in chosen],
        "missing": [pid for pid in selected_ids if pid not in parts],
        "char_count": len(prompt),
        "part_count": len(chosen),
    }
