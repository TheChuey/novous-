"""CodeBuilder agent tools: the thin adapter between the chat agent and the pillar.

Importing this module registers each decorated function into the core tool
catalogue via the shared ``@tool`` decorator (the host does this at the bottom of
``core_engine/tool_catalog.py``). Tools hold no logic of their own: they validate
the call and delegate to ``service``.
"""

from core_engine.tool_catalog import tool

from .. import service


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


# Registered only when the host provides the questionnaire registry (core_engine.hitl).
# Agents that list the tool on a host without it simply do not receive it.
if service.host_supports_questionnaire():

    @tool(provider="codebuilder")
    def ask_user_questions(json_file_path: str, timeout_seconds: float = 300.0) -> str:
        """Pause the agent and ask the user a list of questions from a JSON file in the workspace.

        The browser pops up a step-by-step dialog; once the user submits answers this
        tool resumes and returns the questions and answers as a JSON string.

        Expected JSON file contents (a list, or an object with a "questions" list):
        [{"id": "q1", "question": "What is the target deployment environment?"}]
        Provide a workspace-root-relative path; do not prefix it with 'workspace/'.
        """
        return service.ask_user(json_file_path, timeout_seconds)
