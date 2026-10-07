"""pipelines/data.py

Constants and paths for the multi-agent cascade component.

Component: Multi-Agent Cascades.
"""

from __future__ import annotations

from pathlib import Path

#: The default step chain (one file, bundled with the component).
CONFIG_FILE = Path(__file__).resolve().parent / "pipeline.json"

#: One JSONL line per pipeline run, in the shared data directory.
RECORDS_FILE = Path(__file__).resolve().parents[1] / "data" / "pipeline_runs.jsonl"

_STEP_FEED_TEMPLATE = (
    "Below is what the previous pipeline step ({name}) produced.\n"
    "Use it as your required input. Do NOT ask for it again - just act on it.\n"
    "--- {name} OUTPUT ---\n"
    "{output}\n"
    "--- END {name} OUTPUT ---\n"
)
