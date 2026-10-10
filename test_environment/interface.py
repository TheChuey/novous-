"""Test Environment Doorway: Python API & FastAPI Router
(/api/testing/*, /api/prompt-builder/*)."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import prompt_builder, test_runner, tool_workbench

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)


class ToolWorkbenchRequest(BaseModel):
    tool_code: str = Field(..., min_length=1, max_length=50000)
    function_input: dict[str, Any] = Field(default_factory=dict)


class ToolWorkbenchLLMRequest(ToolWorkbenchRequest):
    model: str = Field(..., min_length=1, max_length=120)
    user_prompt: str = Field(..., min_length=1, max_length=5000)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""
    markdown: str = Field(..., min_length=1)


class AddCategoryRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""
    required_header: str = ""


class AddPartRequest(BaseModel):
    category: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    id: str | None = None


# --- Prompt builder --------------------------------------------------------

@router.get("/api/prompt-builder/categories")
def api_categories():
    return prompt_builder.get_manifest()


@router.post("/api/prompt-builder/categories")
def api_add_category(req: AddCategoryRequest):
    try:
        return prompt_builder.add_category(
            cat_id=req.id,
            name=req.name,
            description=req.description,
            required_header=req.required_header,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/categories/{cat_id}")
def api_delete_category(cat_id: str):
    try:
        return prompt_builder.delete_category(cat_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/prompt-builder/parts")
def api_parts(category: str | None = None):
    return {"parts": prompt_builder.load_parts(category)}


@router.post("/api/prompt-builder/parts")
def api_add_part(req: AddPartRequest):
    try:
        return prompt_builder.add_part(
            category=req.category,
            title=req.title,
            content=req.content,
            part_id=req.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/prompt-builder/parts/{part_id:path}")
def api_delete_part(part_id: str):
    try:
        return prompt_builder.delete_part(part_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/prompt-builder/assemble")
def api_assemble(req: AssembleRequest):
    if not req.parts and not req.extra_instructions.strip():
        raise HTTPException(status_code=400, detail="Select at least one prompt part.")
    result = prompt_builder.assemble_prompt(req.parts, req.extra_instructions)
    if result["missing"]:
        raise HTTPException(status_code=400,
                            detail=f"Unknown part ids: {', '.join(result['missing'])}")
    return result


# --- Test runner -----------------------------------------------------------

@router.post("/api/testing/tool-workbench/execute")
def api_execute_tool_test(req: ToolWorkbenchRequest):
    return tool_workbench.run_python_tool(req.tool_code, req.function_input)


@router.post("/api/testing/tool-workbench/test-with-llm")
def api_test_tool_with_llm(req: ToolWorkbenchLLMRequest):
    try:
        function = tool_workbench.get_function_definition(req.tool_code)
        schema = tool_workbench.get_tool_schema(function)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        import ollama
        response = ollama.chat(
            model=req.model,
            messages=[{"role": "user", "content": req.user_prompt}],
            tools=[schema],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM tool-call request failed: {exc}") from exc

    message = response.get("message", {})
    tool_calls = message.get("tool_calls") or []
    llm_text_response = message.get("content", "")
    if not tool_calls:
        return {
            "status": "ERROR",
            "error_code": "ERR_NO_TOOL_CALL",
            "message": "The selected model did not return a tool call.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": [],
        }

    call = tool_calls[0].get("function", {})
    if call.get("name") != function.name:
        return {
            "status": "ERROR",
            "error_code": "ERR_UNEXPECTED_TOOL_CALL",
            "message": "The model called an unexpected tool function.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
        }
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return {
                "status": "ERROR",
                "error_code": "ERR_INVALID_TOOL_ARGUMENTS",
                "message": "The model returned invalid JSON tool arguments.",
                "llm_text_response": llm_text_response,
                "tool_calls_detected": tool_calls,
            }
    if not isinstance(arguments, dict):
        return {
            "status": "ERROR",
            "error_code": "ERR_INVALID_TOOL_ARGUMENTS",
            "message": "The model's tool arguments must be a JSON object.",
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
        }

    execution = tool_workbench.run_python_tool(req.tool_code, arguments)
    return {
        "status": execution["status"],
        "error_code": execution["error_code"],
        "llm_text_response": llm_text_response,
        "tool_calls_detected": tool_calls,
        "function_input": arguments,
        "tool_execution_result": execution,
    }


@router.post("/api/testing/tool-workbench/promote")
def api_promote_tool(req: ToolWorkbenchRequest):
    try:
        function = tool_workbench.get_function_definition(req.tool_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    execution = tool_workbench.run_python_tool(req.tool_code, req.function_input)
    if execution["status"] != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail={"message": "The tool must pass its test before promotion.",
                    "test_result": execution},
        )

    promoted = tool_workbench.promote_python_tool(req.tool_code, function.name)
    return {"promoted": promoted, "test_result": execution}


@router.get("/api/testing/tool-workbench/tools/{tool_name}")
def api_get_workbench_tool(tool_name: str):
    try:
        return tool_workbench.get_custom_tool_source(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/testing/tool-workbench/tools/{tool_name}")
def api_delete_workbench_tool(tool_name: str):
    try:
        return tool_workbench.delete_custom_tool(tool_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not delete tool: {exc}") from exc


@router.post("/api/testing/run_header_tests")
def api_run_header_tests(req: HeaderTestRequest):
    try:
        return test_runner.run_tests_for_agent(req.agent_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/testing/evaluate_markdown")
def api_evaluate_markdown(payload: dict):
    md_text = payload.get("markdown", "")
    if not md_text.strip():
        raise HTTPException(status_code=400, detail="markdown field is required.")
    return test_runner.run_header_tests(md_text, payload.get("agent_id", "draft"))


@router.post("/api/testing/publish")
def api_publish(req: PublishRequest):
    """Save a prompt to its agent profile and archive the updated definition."""
    from core_engine.agent_factory import find_agent_dir, parse_markdown_sections

    agent_dir = find_agent_dir(req.agent_id)
    if not agent_dir:
        raise HTTPException(status_code=404, detail=f"Agent not found: {req.agent_id}")

    json_path = agent_dir / "agent.json"
    try:
        metadata = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Could not read agent metadata: {exc}")
    if not isinstance(metadata, dict):
        raise HTTPException(status_code=500, detail="Agent metadata must be a JSON object.")

    markdown = req.markdown.strip()
    if not markdown:
        raise HTTPException(status_code=400, detail="Prompt content must not be empty.")

    purpose = parse_markdown_sections(markdown).get("purpose", "").strip()
    if purpose:
        metadata["description"] = purpose

    try:
        (agent_dir / "agent.md").write_text(markdown + "\n", encoding="utf-8")
        json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save agent files: {exc}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = re.sub(r"[^A-Za-z0-9_-]+", "-", (req.label or req.agent_id).strip()).strip("-_")
    label = label or req.agent_id
    dest = TEST_AGENTS_DIR / f"{req.agent_id}__{label}__{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for src in agent_dir.iterdir():
        if src.is_file():
            shutil.copy2(src, dest / src.name)

    manifest_path = TEST_AGENTS_DIR / "manifest.json"
    manifest = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    manifest.append({
        "agent_id": req.agent_id,
        "label": label,
        "snapshot": dest.name,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = test_runner.run_tests_for_agent(req.agent_id)
    return {"saved": True, "path": f"agents/{req.agent_id}/agent.md",
            "metadata_path": f"agents/{req.agent_id}/agent.json",
            "snapshot": dest.name, "snapshot_path": f"test_agents/{dest.name}",
            "header_report": report}


@router.get("/api/testing/fixtures")
def api_fixtures():
    fixtures = []
    if TEST_AGENTS_DIR.is_dir():
        for child in sorted(TEST_AGENTS_DIR.iterdir()):
            if child.is_dir():
                fixtures.append({
                    "snapshot": child.name,
                    "files": sorted(p.name for p in child.iterdir() if p.is_file()),
                })
    return {"fixtures": fixtures}
