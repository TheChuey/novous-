"""configuration/logic.py

Workflows, step sequencing, conditional routing and error orchestration.

Component: Models & Environment Management. Model *selection* routing:
explicit arg > config/models.json > first installed Ollama model, with
tool-support ordering when the caller needs tool calling.
"""

from __future__ import annotations

from .code import config_model_ids, installed_model_ids, supports_tools


def resolve_model(model: str | None, require_tools: bool = False) -> str:
    """Pick which model to use: explicit arg (when suitable) > config > Ollama list.

    An explicitly requested model that is NOT installed on this machine is
    dropped so the app falls back to a detected one instead of erroring with
    a 404 - this keeps settings written on one OS (e.g. Windows) from
    breaking the app on another (e.g. Linux). When no models are visible at
    all, the explicit request is honoured as-is (previous behaviour).

    `require_tools`: when the caller needs tool calling, models that Ollama
    reports as NOT supporting tools are skipped so an agent with tools never
    gets a model that Ollama will reject with 400.
    """

    explicit = None
    if model:
        detected = set(config_model_ids()) | set(installed_model_ids())
        if model in detected:
            explicit = model
        elif detected:
            print(
                f"[ask_llm] requested model '{model}' is not installed locally - "
                "falling back to a detected model"
            )
        else:
            print(f"[ask_llm] no installed models visible - using requested '{model}' as-is")
            return model

    # Ordered candidates: explicit > models.json > live Ollama scan.
    candidates = []
    if explicit:
        candidates.append(explicit)
    for m in config_model_ids():
        if m not in candidates:
            candidates.append(m)
    for m in installed_model_ids():
        if m not in candidates:
            candidates.append(m)

    if require_tools:
        # Prefer models that definitely support tools; keep "unknown" ones as a
        # last resort (older Ollama), push confirmed-no-tools models to the end.
        tooled = [c for c in candidates if supports_tools(c) is True]
        unknown = [c for c in candidates if supports_tools(c) is None]
        others = [c for c in candidates if c not in tooled and c not in unknown]
        ordered = tooled + unknown + others
        if explicit and others and explicit in others:
            print(
                f"[ask_llm] requested model '{explicit}' does not support tools - "
                "falling back to one that does"
            )
    else:
        ordered = candidates

    if not ordered:
        raise RuntimeError(
            "No model available. Specify one in the frontend, "
            "add models to models.json, or install one in Ollama."
        )

    chosen = ordered[0]
    if chosen is explicit:
        print(f"[ask_llm] explicit model used: {model}")
    elif chosen in config_model_ids():
        print(f"[ask_llm] model from models.json: {chosen}")
    else:
        print(f"[ask_llm] first installed Ollama model: {chosen}")

    return chosen
