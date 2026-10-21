#!/usr/bin/env python3
"""Migrate legacy split agents into library/{agent_id}.md."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_ROOT = ROOT / "library"
LEGACY_DIRS = [ROOT / "workspace" / "agents", ROOT / "codebuilder" / "agents"]


def _render_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key in ["id", "name", "description", "mode", "model", "squad", "environment", "version"]:
        if key not in meta or meta[key] in (None, ""):
            continue
        lines.append(f"{key}: {meta[key]}")
    tools = meta.get("tools") or []
    if tools:
        lines.append("tools:")
        for tool in tools:
            lines.append(f"  - {tool}")
    skills = meta.get("skills") or []
    if skills:
        lines.append("skills:")
        for skill in skills:
            if isinstance(skill, dict):
                for skill_name, config in skill.items():
                    lines.append(f"  - {skill_name}:")
                    if isinstance(config, dict):
                        for nested_key, nested_value in config.items():
                            lines.append(f"      {nested_key}: {nested_value}")
            else:
                lines.append(f"  - {skill}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _safe_body(raw: str) -> str:
    if not raw:
        return ""
    if raw.startswith("---"):
        lines = raw.splitlines()
        end = None
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end = idx
                break
        if end is not None:
            return "\n".join(lines[end + 1:]).strip("\n")
    return raw.strip("\n")


for legacy_dir in LEGACY_DIRS:
    if not legacy_dir.is_dir():
        continue
    LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    for agent_dir in sorted(legacy_dir.iterdir(), key=lambda p: p.name.lower()):
        if not agent_dir.is_dir():
            continue
        json_path = agent_dir / "agent.json"
        md_path = agent_dir / "agent.md"
        if not json_path.is_file():
            continue
        try:
            meta = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        agent_id = str(meta.get("id") or agent_dir.name)
        out_path = LIBRARY_ROOT / f"{agent_id}.md"
        body = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
        final = _render_frontmatter(meta) + "\n" + _safe_body(body) + "\n"
        out_path.write_text(final, encoding="utf-8")
        json_path.rename(json_path.with_suffix(".json.bak"))
        if md_path.exists():
            md_path.rename(md_path.with_suffix(".md.bak"))

print(f"Migrated legacy agent definitions into {LIBRARY_ROOT}.")
