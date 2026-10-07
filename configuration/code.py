"""configuration/code.py

Stateful engine classes, core objects and active execution loops.

Component: Models & Environment Management. Everything that talks to
the local Ollama instance for *discovery* lives here: installed-model
scans, capability lookups and the models.json refresh. All lookups are
cached with the same TTL/failure semantics as before - a failed scan
keeps the previous snapshot so "no models visible" and "Ollama
unreachable" stay distinguishable.
"""

from __future__ import annotations

import time

import ollama

from .data import load_models, save_models
from .helperfunctions import model_ids

# How long a successful Ollama model scan is trusted before we re-list.
_MODEL_SCAN_TTL = 60.0
_model_scan_cache: dict = {"at": -1.0, "ids": []}  # ordered list of installed model ids


def config_model_ids() -> list:
    """The model ids in models.json (re-scanned by refresh_models() at
    every server startup, so it reflects THIS machine's Ollama)."""

    return model_ids(load_models())


def installed_model_ids() -> list:
    """Ordered ids of installed Ollama models, cached briefly.

    A failed scan keeps theprevious snapshot (or [] when there was none),
    so "no models visible" and "Ollama unreachable" stay distinguishable.
    """

    global _model_scan_cache

    now = time.monotonic()
    if _model_scan_cache["ids"] and now - _model_scan_cache["at"] < _MODEL_SCAN_TTL:
        return _model_scan_cache["ids"]

    try:
        ids = []
        for m in ollama.list().get("models", []):
            mid = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
            if mid and mid not in ids:
                ids.append(mid)
        _model_scan_cache = {"at": now, "ids": ids}
    except Exception:
        pass  # keep whatever we had before

    return _model_scan_cache["ids"]


# Per-model capabilities (ollama.show), cached per process. None = unknown
# (older Ollama that does not report capabilities yet).
_cap_cache: dict = {}


def capabilities(model: str) -> list | None:
    """The reported capabilities for `model` (['completion', 'tools', ...])."""

    if model in _cap_cache:
        return _cap_cache[model]

    try:
        info = ollama.show(model=model).model_dump()
        caps = info.get("capabilities") or []
        _cap_cache[model] = caps
        return caps
    except Exception:
        _cap_cache[model] = None
        return None


def supports_tools(model: str) -> bool | None:
    """True/False when Ollama reports capabilities, None when unknown."""

    caps = capabilities(model)
    if caps is None:
        return None
    return "tools" in caps


def scan_models() -> list:
    """Return the deduped list of locally installed Ollama models."""

    models = []
    try:
        for m in ollama.list().get("models", []):
            model_id = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
            size = m.get("size", 0) if isinstance(m, dict) else getattr(m, "size", 0)
            if model_id:
                models.append({"id": model_id, "name": model_id, "source": "ollama", "size": size})
    except Exception as exc:
        print(f"[llm] ollama scan failed: {exc}")

    seen, unique = set(), []
    for m in models:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)
    return unique


def refresh_models() -> list:
    """Scan Ollama and write models.json (returns the model list)."""

    models = scan_models()

    if models:
        save_models(models)
        print(f"[llm] wrote {len(models)} models to models.json")
    else:
        print("[llm] scan found no models - keeping models.json")

    return models
