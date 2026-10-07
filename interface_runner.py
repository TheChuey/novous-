"""
interface_runner.py - compatibility shim.

AgentInterface now lives in engine_logic.EngineRuntime. This alias keeps
existing imports (routers, run.py, test_environment/agent_test.py) working.
New code should import engine_interface instead.
"""

from engine_logic import DEFAULT_HISTORY_LIMIT, EngineRuntime as AgentInterface  # noqa: F401

__all__ = ["AgentInterface", "DEFAULT_HISTORY_LIMIT"]
