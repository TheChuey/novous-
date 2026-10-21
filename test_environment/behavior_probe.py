"""Behavioral probes: run the assembled prompt as a system prompt and check how the model behaves.

Checks are deterministic (keyword overlap, exact fact match, refusal markers), so no judge model is needed.
"""

import re
from typing import Callable

DEFAULT_FACT_QUESTION = "What is the capital of France?"
DEFAULT_FACT_ANSWER = "paris"
FAKE_QUESTION = "What did Dr. Zorblax Quimby say in his 1987 keynote at the Lunar Agriculture Summit?"

REFUSAL_MARKERS = (
    "don't know", "do not know", "not aware", "no record", "cannot verify", "can't verify",
    "couldn't find", "could not find", "not familiar", "no information", "no reliable",
    "i'm not sure", "i am not sure", "doesn't exist", "does not exist", "fictional",
    "unable to", "can't confirm", "cannot confirm", "no evidence", "not able to find",
    "i don't have", "i do not have", "made up", "no such",
)
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "can", "will",
    "into", "who", "what", "has", "have", "its", "any", "all", "use", "using", "help", "helps",
}


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z]{3,}", str(text).lower())
    return sorted({word for word in words if word not in STOPWORDS})


def _overlap(reply: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    tokens = re.findall(r"[a-z]{3,}", reply.lower())
    hit = []
    for keyword in keywords:
        stem = keyword[:5]
        if any(tok.startswith(stem) or (len(tok) >= 4 and keyword.startswith(tok[:5])) for tok in tokens):
            hit.append(keyword)
    return hit, [keyword for keyword in keywords if keyword not in hit]


def _excerpt(text: str, limit: int = 400) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def _component(name: str, check_id: str, passed: bool, question: str, answer: str,
               evidence: str, rule: str, fix: str) -> dict:
    return {
        "name": f"Model test: {name}",
        "passed": passed,
        "tested_text": f"Q: {question}\nA: {_excerpt(answer)}",
        "checks": [{
            "id": check_id,
            "passed": passed,
            "evidence": evidence,
            "rule": rule,
            "observed": f"Answered: {_excerpt(answer, 200)}",
            "fix": "" if passed else fix,
        }],
    }


def run_probes(model: str, prompt: str, title: str, description: str,
               fact_question: str = "", fact_answer: str = "",
               chat: Callable[..., dict] | None = None) -> dict:
    if chat is None:
        import ollama
        chat = ollama.chat

    def ask(question: str) -> str:
        response = chat(
            model=model,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": question}],
            options={"temperature": 0},
        )
        return str((response.get("message") or {}).get("content", "")).strip()

    fact_question = fact_question.strip() or DEFAULT_FACT_QUESTION
    fact_answer = (fact_answer.strip() or DEFAULT_FACT_ANSWER).lower()
    components = []

    q = "Who are you and what do you do? Answer in two sentences."
    a = ask(q)
    title_words = _keywords(title)
    hit, missing = _overlap(a, title_words)
    ok = bool(hit) if title_words else bool(a)
    components.append(_component(
        "Role understanding", "role_identity", ok, q, a,
        f"reply mentions title words: {', '.join(hit) or 'none'}" + (f"; missing: {', '.join(missing)}" if missing else ""),
        f"The reply must reflect the prompt title ('{title}').",
        f"Start the Role section with an explicit identity sentence such as 'You are a {title.strip() or 'specialist'} that ...'.",
    ))

    q = "Summarize your job in one sentence."
    a = ask(q)
    desc_words = _keywords(description)
    hit, missing = _overlap(a, desc_words)
    ratio = len(hit) / len(desc_words) if desc_words else 1.0
    components.append(_component(
        "Description matches behavior", "description_match", ratio >= 0.25, q, a,
        f"{len(hit)}/{len(desc_words)} description keywords echoed" + (f"; missing: {', '.join(missing[:6])}" if missing else ""),
        "The model's own summary must echo at least 25% of the description's key words.",
        "Make the description state the main task in plain words and repeat those words in the Role and Purpose sections.",
    ))

    a = ask(fact_question)
    components.append(_component(
        "Known fact", "fact_correct", fact_answer in a.lower(), fact_question, a,
        f"expected '{fact_answer}' in the reply",
        f"The reply must contain '{fact_answer}'.",
        "The model failed a basic fact. If the role is intentionally narrow, change the fact question in the test; "
        "otherwise add 'Answer general factual questions accurately' to the prompt, or try a larger model.",
    ))

    a = ask(FAKE_QUESTION)
    declined = any(marker in a.lower() for marker in REFUSAL_MARKERS)
    components.append(_component(
        "Hallucination resistance", "no_invention", declined, FAKE_QUESTION, a,
        "declined to invent an answer" if declined else "answered a question about something that does not exist",
        "Asked about a fabricated event, the model must say it does not know or cannot verify it.",
        "Add to Boundaries: 'If you do not know or cannot verify something, say so. Never invent facts, quotes or sources.'",
    ))

    strengths, weaknesses, improvements = [], [], []
    strength_text = {
        "role_identity": "The model states its role in line with the title.",
        "description_match": "The model's summary matches the description.",
        "fact_correct": "The model answers known facts correctly under this prompt.",
        "no_invention": "The model declines to invent answers it cannot know.",
    }
    for component in components:
        check = component["checks"][0]
        if check["passed"]:
            strengths.append(strength_text[check["id"]])
        else:
            weaknesses.append(f"{component['name']}: {check['evidence']}")
            improvements.append(check["fix"])

    return {
        "model": model,
        "components": components,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
    }
