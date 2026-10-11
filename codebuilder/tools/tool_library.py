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


@tool(provider="codebuilder")
def ask_user_questions(json_file_path: str, timeout_seconds: float = 300.0) -> str:
    """Pause the agent and ask the user a list of questions from a JSON file in the workspace.

    The browser pops up a step-by-step dialog; once the user submits answers this
    tool resumes and returns the questions and answers as a JSON string.

    Expected JSON file contents (a list, or an object with a "questions" list):
    [{"id": "q1", "question": "What is the target deployment environment?"}]
    Provide a workspace-root-relative path; do not prefix it with 'workspace/'.
    """
    import json

    from core_engine import hitl, langgraph_tools

    relative_path = str(json_file_path).strip().lstrip("/")
    if relative_path.startswith("workspace/"):
        relative_path = relative_path[len("workspace/"):]

    raw = langgraph_tools.read_file_tool.invoke({"relative_path": relative_path})
    if not isinstance(raw, str) or raw.startswith("Error reading file"):
        return f"Error: Questions file '{json_file_path}' was not found in the workspace."

    try:
        data = json.loads(raw)
    except Exception as exc:
        return f"Error parsing questions JSON file: {exc}"

    if isinstance(data, dict):
        raw_questions = data.get("questions", [])
    elif isinstance(data, list):
        raw_questions = data
    else:
        raw_questions = []

    questions = []
    for index, item in enumerate(raw_questions):
        if isinstance(item, dict):
            questions.append({
                "id": str(item.get("id", index)),
                "question": str(item.get("question", item)),
            })
        else:
            questions.append({"id": str(index), "question": str(item)})

    if not questions:
        return "Error: No questions found in the provided JSON file."

    try:
        timeout_value = float(timeout_seconds)
    except (TypeError, ValueError):
        timeout_value = 300.0

    record = hitl.create_request(questions)
    request_id = record["request_id"]

    completed_in_time = record["event"].wait(timeout=timeout_value)
    request_data = hitl.resolve_request(request_id)

    if not completed_in_time or request_data is None:
        return "Error: User questionnaire timed out waiting for input."

    answers = request_data.get("answers", {})
    output = {
        "status": "COMPLETED",
        "qa_pairs": [
            {
                "id": question["id"],
                "question": question["question"],
                "answer": answers.get(question["id"], answers.get(str(index), "No answer provided")),
            }
            for index, question in enumerate(questions)
        ],
    }
    return json.dumps(output, indent=2)