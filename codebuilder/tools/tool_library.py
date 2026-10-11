"""CodeBuilder tools kept out of the core catalogue so the registry stays slim.

Importing this module registers each decorated function into the core
tool catalogue via the shared @tool decorator.
"""

from core_engine.tool_catalog import tool


@tool(provider="codebuilder")
def send_code_to_editor(code: str) -> str:
    """Queue generated Python code for insertion into the active CodeBuilder Monaco editor."""
    if not code.strip():
        raise ValueError("Code to send to the editor must not be empty.")
    return "CodeBuilder will insert this code into the active Monaco editor after the chat turn."


@tool(provider="codebuilder")
def run_code_in_editor() -> str:
    """Queue execution of the current contents of the active CodeBuilder editor."""
    return "CodeBuilder will run the active editor buffer after the chat turn."