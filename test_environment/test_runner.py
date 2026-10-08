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
    })

    if not exists:
        for qid, text in (("depth", f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?"),
                          ("vocabulary", f"Does the '{header}' section use header-appropriate vocabulary?"),
                          ("actionability", f"Does the '{header}' section give actionable, testable guidance?")):
            questions.append({"id": qid, "question": text, "score": 0.0, "passed": False,
                              "evidence": "no section to evaluate"})
        return {"header": header, "questions": questions, "score": 0.0, "passed": False}

    # Q2: Depth - is the section long enough to be meaningful?
    depth = min(1.0, len(section.strip()) / (MIN_SECTION_CHARS * 1.5))
    questions.append({
        "id": "depth",
        "question": f"Is the '{header}' section detailed enough (>= {MIN_SECTION_CHARS} characters)?",
        "score": round(depth, 2),
        "passed": depth >= PASS_THRESHOLD,
        "evidence": f"{len(section.strip())} characters",
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
    })

    total = sum(q["score"] for q in questions) / len(questions)
    return {
        "header": header,
        "questions": questions,
        "score": round(total, 2),
        "passed": total >= PASS_THRESHOLD,
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


def run_tests_for_agent(agent_id: str) -> dict:
    """Locate workspace/agents/<id>/agent.md and run the battery against it."""
    from core_engine.agent_factory import find_agent_dir
    agent_dir = find_agent_dir(agent_id)
    if not agent_dir:
        raise FileNotFoundError(f"Agent not found: {agent_id}")
    md_path = agent_dir / "agent.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    report = run_header_tests(md_text, agent_id)
    report["source"] = str(md_path.relative_to(Path(__file__).resolve().parent.parent)).replace("\\", "/")
    return report
