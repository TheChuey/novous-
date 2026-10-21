"""4-Question Section Header Tests & Lexical Evaluator.

For each of the four required agent.md headers (role, purpose, boundaries,
output format) the runner asks four fixed questions and scores answers with
pure lexical analysis of the section text - no model calls required.
"""

import re
from pathlib import Path

from core_engine.agent_factory import parse_markdown_sections

REQUIRED_HEADERS = ["role", "purpose", "boundaries", "output format"]

HEADER_KEYWORDS = {
    "role": ["you are", "your", "agent", "assistant", "specialist", "expert",
             "engineer", "analyst", "writer", "helper", "responsible", "precise",
             "helpful", "investigate", "general"],
    "purpose": ["goal", "objective", "purpose", "help", "provide", "generate",
                "answer", "solve", "deliver", "produce", "task", "ensure",
                "summarize", "draft", "report", "inspect", "serve", "gather",
                "strategic"],
    "boundaries": ["never", "do not", "don't", "must not", "avoid", "refuse",
                   "forbidden", "limit", "only", "not allowed", "shall not", "no ",
                   "cannot", "outside", "stay", "scope", "within", "not "],
    "output format": ["format", "markdown", "list", "table", "heading", "bullet",
                      "json", "concise", "structure", "section", "paragraph",
                      "respond", "reply", "output", "use ", "lead", "direct",
                      "answer", "detail"],
}

PASS_THRESHOLD = 0.6
MIN_SECTION_CHARS = 40

DIRECTIVE_VERBS = ("must", "should", "always", "never", "keep", "use", "avoid",
                   "start", "end", "list", "provide", "include", "do", "don't",
                   "return", "respond", "state", "answer", "summarize", "draft",
                   "write", "inspect", "gather", "report", "verify", "stay",
                   "lead", "follow", "cite", "act", "deliver", "work")

SECTION_MIN_CHARS = 20


def _plain_section_text(content: str, title: str = "") -> str:
    """Strip markdown emphasis and a leading '**Title:**' label that repeats the heading."""
    text = str(content or "").strip()
    label = re.escape(title.strip()) if title.strip() else r"[A-Za-z][\w &/-]{0,30}"
    text = re.sub(rf"^\s*[*_`]*{label}[*_`]*\s*[:.\-–—][*_`]*\s*", "", text, count=1, flags=re.I)
    return re.sub(r"[*_`]+", "", text).strip()


PROMPT_ACTION_WORDS = (
    "analyze", "answer", "build", "create", "decide", "design", "develop",
    "explain", "generate", "help", "identify", "inspect", "plan", "provide",
    "review", "solve", "write",
)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", text.lower()))


def _matches(lower: str, token_set: set[str], keyword: str) -> bool:
    """Substring match with naive stemming: keyword matches section text."""
    if keyword in lower:
        return True
    if len(keyword) >= 4:
        return any(tok.startswith(keyword) for tok in token_set)
    return False


def _lexical_score(section: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    lower = section.lower()
    tokens = _tokens(section)
    found = [kw for kw in keywords if _matches(lower, tokens, kw)]
    missing = [kw for kw in keywords if not _matches(lower, tokens, kw)]
    score = len(found) / len(keywords) if keywords else 0.0
    return score, found, missing


def _ask(header: str, section: str | None) -> dict:
    """Run the fixed 4-question battery against one section."""
    questions = []

    # Q1: Does the required header exist with content?
    exists = bool(section and section.strip())
    questions.append({
        "id": "presence",
        "question": f"Does the document contain a '## {header}' section with content?",
        "score": 1.0 if exists else 0.0,
        "passed": exists,
        "evidence": "section found" if exists else "section missing or empty",
        "rule": f"The document must contain a '## {header}' heading followed by content.",
        "observed": "section found" if exists else "no such heading, or it has no content",
        "fix": "" if exists else f"Add a '## {header.title()}' section with real content.",
    })

    if not exists:
        for qid, text in (("depth", f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?"),
                          ("vocabulary", f"Does the '{header}' section use header-appropriate vocabulary?"),
                          ("actionability", f"Does the '{header}' section give actionable, testable guidance?")):
            questions.append({"id": qid, "question": text, "score": 0.0, "passed": False,
                              "evidence": "no section to evaluate",
                              "rule": "Requires the section to exist first.",
                              "observed": "no section",
                              "fix": f"Add the '## {header.title()}' section first."})
        return {"header": header, "questions": questions, "score": 0.0, "passed": False}

    # Q2: Depth - is the section long enough to be meaningful?
    depth = min(1.0, len(section.strip()) / (MIN_SECTION_CHARS * 1.5))
    questions.append({
        "id": "depth",
        "question": f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?",
        "score": round(depth, 2),
        "passed": depth >= PASS_THRESHOLD,
        "evidence": f"{len(section.strip())} characters",
        "rule": f"Score is length / {int(MIN_SECTION_CHARS * 1.5)} characters and must reach {PASS_THRESHOLD}.",
        "observed": f"{len(section.strip())} characters, score {round(depth, 2)}",
        "fix": "" if depth >= PASS_THRESHOLD else
               f"Expand to roughly {int(MIN_SECTION_CHARS * 1.5 * PASS_THRESHOLD)}+ characters of specific detail.",
    })

    # Q3: Lexical - does it use vocabulary expected of this header?
    score, found, missing = _lexical_score(section, HEADER_KEYWORDS[header])
    questions.append({
        "id": "vocabulary",
        "question": f"Does the '{header}' section use header-appropriate vocabulary?",
        "score": round(score, 2),
        "passed": score >= PASS_THRESHOLD,
        "evidence": f"matched {len(found)}/{len(HEADER_KEYWORDS[header])} markers"
                    + (f"; missing: {', '.join(missing[:4])}" if missing else ""),
        "rule": f"At least {int(PASS_THRESHOLD * 100)}% of these marker words/phrases must appear: {', '.join(HEADER_KEYWORDS[header])}.",
        "observed": f"matched {len(found)}/{len(HEADER_KEYWORDS[header])}: {', '.join(found) or 'none'}",
        "missing": missing,
        "fix": "" if score >= PASS_THRESHOLD else
               f"Naturally work in more of the missing markers, for example: {', '.join(missing[:8])}.",
    })

    # Q4: Actionability - imperative / directive phrasing present?
    directives = re.findall(
        r"\b(?:" + "|".join(re.escape(v) for v in DIRECTIVE_VERBS) + r")\b",
        section, flags=re.I)
    actionable = len(set(d.lower() for d in directives)) >= 2
    questions.append({
        "id": "actionability",
        "question": f"Does the '{header}' section give actionable, testable guidance?",
        "score": 1.0 if actionable else (0.5 if directives else 0.0),
        "passed": actionable,
        "evidence": f"directive terms: {', '.join(sorted(set(d.lower() for d in directives))[:5]) or 'none'}",
        "rule": "At least 2 different directive words must appear (must, should, always, never, use, avoid, return, ...).",
        "observed": f"{len(set(d.lower() for d in directives))} distinct: {', '.join(sorted(set(d.lower() for d in directives))) or 'none'}",
        "fix": "" if actionable else "Rewrite as direct instructions using at least two directive words such as 'must', 'always', 'never', 'use', 'return'.",
    })

    total = sum(q["score"] for q in questions) / len(questions)
    return {
        "header": header,
        "questions": questions,
        "score": round(total, 2),
        "passed": total >= PASS_THRESHOLD,
        "tested_text": section.strip()[:600],
    }


def run_header_tests(md_text: str, agent_id: str = "") -> dict:
    """Evaluate an agent.md body against the 4-question battery per header."""
    sections = parse_markdown_sections(md_text)
    results = [_ask(header, sections.get(header)) for header in REQUIRED_HEADERS]

    extras = sorted(h for h in sections if h not in REQUIRED_HEADERS)
    overall = sum(r["score"] for r in results) / len(results) if results else 0.0
    passed = sum(1 for r in results if r["passed"])

    return {
        "agent_id": agent_id,
        "results": results,
        "overall_score": round(overall, 2),
        "headers_passed": passed,
        "headers_total": len(results),
        "passed": passed == len(results),
        "extra_headers": extras,
        "verdict": "PASS" if passed == len(results) else "FAIL",
    }


def _text_component(name: str, text: str, min_chars: int, action_required: bool = False) -> dict:
    value = (text or "").strip()
    checks = [
        {
            "id": "present",
            "passed": bool(value),
            "evidence": "content provided" if value else "content is missing",
            "rule": "The field must not be empty.",
            "observed": f"{len(value)} characters" if value else "empty",
            "fix": "" if value else "Write content for this field.",
        },
        {
            "id": "detail",
            "passed": len(value) >= min_chars,
            "evidence": f"{len(value)} characters; requires at least {min_chars}",
            "rule": f"The text must be at least {min_chars} characters.",
            "observed": f"{len(value)} characters",
            "fix": "" if len(value) >= min_chars else
                   f"Expand the text by at least {min_chars - len(value)} characters with specific, concrete detail.",
        },
    ]
    if action_required:
        actions = [word for word in PROMPT_ACTION_WORDS if re.search(rf"\b{word}\b", value, re.I)]
        checks.append({
            "id": "intent",
            "passed": bool(actions),
            "evidence": (
                f"intent/action language found: {', '.join(actions[:4])}"
                if actions else "state the outcome or action this prompt should guide"
            ),
            "rule": f"The text must contain at least one action word such as: {', '.join(PROMPT_ACTION_WORDS)}.",
            "observed": f"found: {', '.join(actions[:4])}" if actions else "no action words found",
            "fix": "" if actions else
                   "Rewrite so it states the outcome the agent should achieve using an action verb (for example 'help', 'analyze', 'write').",
        })
    return {
        "name": name,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "tested_text": value[:600],
    }


def _tool_language_component(tool: dict) -> dict:
    name = str(tool.get("name") or "Unnamed tool")
    description = str(tool.get("description") or "").strip()
    component = _text_component(f"Tool: {name}", description, 30)
    lower = description.lower()
    when_present = bool(re.search(r"\b(when|if|whenever|once|after|before)\b", lower))
    action_present = bool(re.search(
        r"\b(read|write|create|delete|search|list|calculate|run|execute|return|retrieve|"
        r"send|update|compare|inspect|extract|convert|validate|use)\w*\b",
        lower,
    ))
    component["checks"].extend([
        {
            "id": "behavior",
            "passed": action_present,
            "evidence": "describes an operation" if action_present else "explain what the tool does",
            "rule": "The description must name an operation (read, write, search, calculate, return, run, ...).",
            "observed": "operation word found" if action_present else "no operation word found",
            "fix": "" if action_present else "Add a sentence saying what the tool does, starting with an action verb.",
        },
        {
            "id": "when_to_use",
            "passed": when_present,
            "evidence": "states a usage condition" if when_present else "explain when the agent should call this tool",
            "rule": "The description must state when to call the tool (use words such as when, if, whenever, after, before).",
            "observed": "usage condition found" if when_present else "no usage condition found",
            "fix": "" if when_present else "Add a sentence such as 'Call this tool when the user asks for ...'.",
        },
    ])
    component["passed"] = all(check["passed"] for check in component["checks"])
    component["signature"] = str(tool.get("signature") or "")
    return component


def run_prompt_component_tests(
    title: str,
    description: str,
    sections: list[dict],
    tools: list[dict],
) -> dict:
    """Evaluate the title, summary, each prompt section, and each tool description."""
    components = [
        _text_component("Prompt title", title, 4),
        _text_component("Prompt description", description, 40, action_required=True),
    ]
    components.append({
        "name": "Prompt sections",
        "passed": bool(sections),
        "checks": [{
            "id": "present",
            "passed": bool(sections),
            "evidence": (
                f"{len(sections)} section(s) included"
                if sections else "select at least one prompt section"
            ),
        }],
    })

    for section in sections:
        title_text = str(section.get("title") or "Untitled section").strip()
        content = str(section.get("content") or "").strip()
        plain = _plain_section_text(content, title_text)
        category = str(section.get("category") or "").strip().lower()
        section_type = "Skill" if category in {"skill", "skills"} else "Section"
        components.append(_text_component(f"{section_type} title: {title_text}", title_text, 4))
        component = _text_component(f"{section_type}: {title_text}", plain, SECTION_MIN_CHARS)
        if plain:
            directives = re.findall(
                r"\b(?:" + "|".join(re.escape(v) for v in DIRECTIVE_VERBS) + r")\b|\b(?:you are|act as|your)\b",
                plain,
                flags=re.I,
            )
            component["checks"].append({
                "id": "actionability",
                "passed": bool(directives),
                "evidence": (
                    f"instruction language found: {', '.join(sorted(set(d.lower() for d in directives))[:4])}"
                    if directives else "include an explicit instruction describing what the agent should do"
                ),
                "rule": f"The section must contain directive wording such as: {', '.join(DIRECTIVE_VERBS[:12])}, ...",
                "observed": (
                    f"found: {', '.join(sorted(set(d.lower() for d in directives))[:4])}"
                    if directives else "no directive wording found"
                ),
                "fix": "" if directives else
                       "Rewrite the section as explicit instructions using words like 'must', 'always', 'never', 'use', or 'return'.",
            })
            component["passed"] = all(check["passed"] for check in component["checks"])
        component["category"] = category
        components.append(component)

    for tool in tools:
        tool_name = str(tool.get("name") or "Unnamed tool")
        components.append(_text_component(f"Tool name: {tool_name}", tool_name, 3))
        components.append(_tool_language_component(tool))
    passed = sum(1 for component in components if component["passed"])
    return {
        "components": components,
        "components_passed": passed,
        "components_total": len(components),
        "passed": bool(components) and passed == len(components),
        "verdict": "PASS" if components and passed == len(components) else "FAIL",
    }


def run_tests_for_agent(agent_id: str, environment: str = "workspace") -> dict:
    """Locate an agent profile in its environment and run the header battery."""
    from core_engine.agent_factory import find_agent_file
    md_path = find_agent_file(agent_id, environment)
    if not md_path:
        raise FileNotFoundError(f"Agent not found in {environment}: {agent_id}")
    md_text = md_path.read_text(encoding="utf-8")
    report = run_header_tests(md_text, agent_id)
    report["source"] = str(md_path.relative_to(Path(__file__).resolve().parent.parent)).replace("\\", "/")
    return report
