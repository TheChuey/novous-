"""Registered agent squads and persistent aggregate health metrics."""

import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any

from core_engine import agent_factory
from orchestration.orchestration_interface import SUBAGENT_LIBRARY_ROOT
import yaml


DATA_PATH = Path(__file__).resolve().parent.parent / "agentMemory" / "data"
METRICS_PATH = DATA_PATH / "orchestration_squad_metrics.json"
SQUADS_PATH = DATA_PATH / "orchestration_squads.json"
_LOCK = threading.RLock()
_DEFAULT_DEFINITIONS = {
    "rag-squad": {
        "squad_id": "rag-squad",
        "name": "RAG Knowledge Squad",
        "description": "Retrieves evidence from knowledge branches and prepares grounded answers.",
        "primary_agent": "rag-presenter",
        "subagents": ["rag-retriever"],
        "default_pattern": "sequential",
    },
    "code-squad": {
        "squad_id": "code-squad",
        "name": "Code Development Squad",
        "description": "Plans code work, builds requested changes, and troubleshoots results.",
        "primary_agent": "code-planer",
        "subagents": [
            "code-builder",
            "tester",
            "code-troubleshooter",
        ],
        "default_pattern": "sequential",
    },
}


def _read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {label} '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path}")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _read_metrics() -> dict[str, dict[str, Any]]:
    return _read_json(METRICS_PATH, "Squad metrics")


def _read_definitions() -> dict[str, dict[str, Any]]:
    if not SQUADS_PATH.is_file():
        return {key: dict(value) for key, value in _DEFAULT_DEFINITIONS.items()}
    saved = _read_json(SQUADS_PATH, "Squad definitions")
    definitions = {}
    for squad_id, definition in saved.items():
        if not isinstance(definition, dict):
            raise RuntimeError(f"Invalid squad definition for '{squad_id}'.")
        definitions[squad_id] = dict(definition)
    code_squad = definitions.get("code-squad")
    if code_squad:
        subagents = code_squad.get("subagents")
        if isinstance(subagents, list) and {
            "code-builder",
            "code-troubleshooter",
        } <= set(subagents) and (
            "code-error-triager" in subagents or "tester" not in subagents
        ):
            legacy_ids = {
                "code-builder",
                "code-troubleshooter",
                "code-error-triager",
                "tester",
            }
            extras = [agent_id for agent_id in subagents if agent_id not in legacy_ids]
            code_squad["subagents"] = [
                "code-builder",
                "tester",
                "code-troubleshooter",
                *extras,
            ]
    return definitions


def list_agent_catalog() -> dict[str, list[dict[str, str]]]:
    agents = [
        {
            "id": str(agent["id"]),
            "name": str(agent.get("name") or agent["id"]),
            "description": str(agent.get("description") or ""),
        }
        for agent in agent_factory.list_agents()
    ]
    subagents = []
    if not SUBAGENT_LIBRARY_ROOT.is_dir():
        raise RuntimeError(
            f"Sub-agent library folder does not exist: {SUBAGENT_LIBRARY_ROOT}"
        )
    for path in sorted(SUBAGENT_LIBRARY_ROOT.glob("*.yaml")):
        try:
            definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise RuntimeError(f"Could not load sub-agent definition '{path}': {exc}") from exc
        if not isinstance(definition, dict):
            raise RuntimeError(f"Sub-agent definition must be a YAML object: {path}")
        agent_id = path.stem
        declared_id = str(definition.get("id") or agent_id)
        if declared_id != agent_id:
            raise RuntimeError(
                f"Sub-agent id '{declared_id}' does not match definition filename '{path.name}'."
            )
        subagents.append(
            {
                "id": agent_id,
                "name": str(definition.get("name") or agent_id),
                "description": str(definition.get("description") or ""),
            }
        )
    return {"agents": agents, "subagents": subagents}


def list_squads() -> list[dict[str, Any]]:
    with _LOCK:
        definitions = _read_definitions()
        metrics = _read_metrics()
    squads = []
    for squad_id, definition in definitions.items():
        values = metrics.get(squad_id, {})
        squads.append(
            {
                **definition,
                "metrics": {
                    "total_runs": int(values.get("total_runs", 0)),
                    "successful_runs": int(values.get("successful_runs", 0)),
                    "failed_runs": int(values.get("failed_runs", 0)),
                    "average_duration_ms": float(
                        values.get("average_duration_ms", 0)
                    ),
                    "last_duration_ms": int(values.get("last_duration_ms", 0)),
                    "last_status": str(values.get("last_status", "healthy")),
                },
            }
        )
    return squads


def get_squad(squad_id: str) -> dict[str, Any] | None:
    return next(
        (squad for squad in list_squads() if squad["squad_id"] == squad_id),
        None,
    )


def get_squad_id_for_primary_agent(agent_id: str) -> str | None:
    return next(
        (
            squad["squad_id"]
            for squad in list_squads()
            if squad["primary_agent"] == agent_id
        ),
        None,
    )


def _validate_definition(
    name: str, primary_agent: str, subagents: list[str]
) -> None:
    if not name.strip():
        raise ValueError("Squad name is required.")
    catalog = list_agent_catalog()
    if not any(agent["id"] == primary_agent for agent in catalog["agents"]):
        raise ValueError(f"Primary agent is not available: {primary_agent}")
    catalog_ids = {agent["id"] for agent in catalog["subagents"]}
    if len(set(subagents)) != len(subagents):
        raise ValueError("Sub-agent selections must not contain duplicates.")
    unknown = [agent_id for agent_id in subagents if agent_id not in catalog_ids]
    if unknown:
        raise ValueError(f"Sub-agent definitions are not available: {', '.join(unknown)}")


def create_squad(
    name: str, description: str, primary_agent: str, subagents: list[str]
) -> dict[str, Any]:
    clean_name = name.strip()
    _validate_definition(clean_name, primary_agent, subagents)
    base_id = re.sub(r"[^a-z0-9]+", "-", clean_name.lower()).strip("-")
    if not base_id:
        raise ValueError("Squad name must contain letters or numbers.")
    with _LOCK:
        definitions = _read_definitions()
        squad_id = base_id
        suffix = 2
        while squad_id in definitions:
            squad_id = f"{base_id}-{suffix}"
            suffix += 1
        definitions[squad_id] = {
            "squad_id": squad_id,
            "name": clean_name,
            "description": description.strip(),
            "primary_agent": primary_agent,
            "subagents": list(subagents),
            "default_pattern": "sequential",
        }
        _write_json(SQUADS_PATH, definitions)
    return get_squad(squad_id)


def delete_squad(squad_id: str) -> bool:
    with _LOCK:
        definitions = _read_definitions()
        if squad_id not in definitions:
            return False
        del definitions[squad_id]
        _write_json(SQUADS_PATH, definitions)
        metrics = _read_metrics()
        metrics.pop(squad_id, None)
        _write_json(METRICS_PATH, metrics)
    return True


def record_squad_run(squad_id: str, success: bool, duration_ms: int) -> None:
    if get_squad(squad_id) is None:
        raise ValueError(f"Unknown registered squad: {squad_id}")
    with _LOCK:
        metrics = _read_metrics()
        values = metrics.setdefault(
            squad_id,
            {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_duration_ms": 0,
                "last_duration_ms": 0,
                "last_status": "healthy",
            },
        )
        total = int(values.get("total_runs", 0)) + 1
        successful = int(values.get("successful_runs", 0)) + int(success)
        failed = int(values.get("failed_runs", 0)) + int(not success)
        duration = max(0, int(duration_ms))
        previous_average = float(values.get("average_duration_ms", 0))
        values.update(
            total_runs=total,
            successful_runs=successful,
            failed_runs=failed,
            average_duration_ms=round(
                ((previous_average * (total - 1)) + duration) / total, 2
            ),
            last_duration_ms=duration,
            last_status=(
                "failing" if failed / total > 0.3
                else "degraded" if failed / total > 0.1
                else "healthy"
            ),
        )
        _write_json(METRICS_PATH, metrics)
