"""Shared test fixtures."""

import pytest

from agentMemory import code_scratchpad


@pytest.fixture(autouse=True)
def isolated_code_scratchpad(tmp_path, monkeypatch):
    """Keep every test away from the real code scratchpad file."""
    path = tmp_path / "code_scratchpad.json"
    monkeypatch.setattr(code_scratchpad, "CODE_SCRATCHPAD_PATH", path)
    return path
