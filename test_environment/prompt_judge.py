"""LLM-as-judge review of a prompt, one rubric per section type.

The judge returns the same component/check shape as test_runner so the UI and
the "send failures to chat agent" flow can treat both kinds of result alike.
"""

import json
import re
from typing import Callable

RUBRICS = {
    "role": "States who the agent is and its domain of expertise in concrete terms.",
    "purpose": "States a specific goal or outcome the agent must achieve, not a vague aim.",
    "boundaries": "Lists concrete prohibitions or limits the agent must respect.",
    "output format": "Describes a checkable response format (structure, length, style).",
    "default": "Is clear, specific, actionable and does not contradict other sections.",
}
TOOL_RUBRIC = "Says what the tool does and when the agent should call it."
WHOLE_RUBRIC = "The sections are consistent with each other, with no contradictions or obvious gaps."


def _rubric_for(title: str) -> str:
    lower = title.strip().lower()
    for key, rubric in RUBRICS.items():
        if key != "default" and key in lower:
            return rubric
    return RUBRICS["default"]


def _build_request(title, description, sections, tools, target_model) -> str:
    items = [{"id": "prompt", "name": "Whole prompt", "rubric": WHOLE_RUBRIC}]
    for index, section in enumerate(sections):
        items.append({
            "id": f"section-{index}",
            "name": section.get("title", ""),
            "rubric": _rubric_for(section.get("title", "")),
            "text": str(section.get("content", ""))[:1500],
        })
    for index, tool in enumerate(tools):
        items.append({
            "id": f"tool-{index}",
            "name": tool.get("name", ""),
            "rubric": TOOL_RUBRIC,
            "text": str(tool.get("description", ""))[:600],
        })
    return (
        "You are a strict reviewer of agent system prompts. "
        f"The prompt will be run by the model '{target_model}'; judge whether it is "
        "clear and specific enough for a model of that kind.\n"
        f"Prompt title: {title}\nPrompt description: {description}\n\n"
        "Review each item against its rubric. Reply with ONLY a JSON array, one object per item: "
        '{"id": "...", "passed": true|false, "reason": "one sentence", "fix": "a concrete rewrite or empty"}.\n\n'
        f"Items:\n{json.dumps(items, ensure_ascii=False, indent=1)}"
    ), items


def _parse_verdicts(text: str) -> dict[str, dict]:
    match = re.search(r"\[.*\]", text or "", re.S)
    if not match:
        raise ValueError("The model did not return a JSON array.")
    data = json.loads(match.group(0))
    return {str(item.get("id")): item for item in data if isinstance(item, dict)}


def judge_prompt(model: str, title: str, description: str, sections: list[dict],
                 tools: list[dict], chat: Callable[..., dict] | None = None) -> dict:
    if chat is None:
        import ollama
        chat = ollama.chat
    request, items = _build_request(title, description, sections, tools, model)
    response = chat(model=model, messages=[{"role": "user", "content": request}])
    content = (response.get("message") or {}).get("content", "")
    verdicts = _parse_verdicts(content)

    components = []
    for item in items:
        verdict = verdicts.get(item["id"])
        if verdict is None:
            continue
        passed = bool(verdict.get("passed"))
        reason = str(verdict.get("reason") or "").strip()
        components.append({
            "name": f"AI review: {item['name']}",
            "passed": passed,
            "tested_text": item.get("text", ""),
            "checks": [{
                "id": "ai_review",
                "passed": passed,
                "evidence": reason or ("judged acceptable" if passed else "judged unacceptable"),
                "rule": item["rubric"],
                "observed": reason,
                "fix": "" if passed else str(verdict.get("fix") or "").strip(),
            }],
        })
    return {"model": model, "components": components, "raw": content[:4000]}
