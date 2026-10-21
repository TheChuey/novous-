"""Test Environment Doorway: Python API & FastAPI Router
(/api/testing/*, /api/prompt-builder/*)."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import (
    behavior_probe, model_log, prompt_builder, prompt_judge, report_store, sandbox_env, test_runner, tool_workbench,
)

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"


class ToolWorkbenchRequest(BaseModel):
    tool_code: str = Field(..., min_length=1, max_length=50000)
    function_input: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = Field(5, ge=1, le=600)

class ToolWorkbenchLLMRequest(ToolWorkbenchRequest):
    model: str = Field(..., min_length=1, max_length=120)
    user_prompt: str = Field(..., min_length=1, max_length=5000)


class ToolWorkbenchGenerateRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=5000)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PromptEvaluationComponent(BaseModel):
    title: str = ""
    content: str = ""
    category: str = ""


class PromptEvaluationTool(BaseModel):
    name: str = ""
    description: str = ""
    signature: str = ""


class PromptEvaluationRequest(BaseModel):
    title: str = ""
    description: str = ""
    sections: list[PromptEvaluationComponent] = Field(default_factory=list)
    tools: list[PromptEvaluationTool] = Field(default_factory=list)


class PromptJudgeRequest(PromptEvaluationRequest):
    model: str = Field(..., min_length=1, max_length=120)


class ProbeRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=120)
    title: str = ""
    description: str = ""
    prompt: str = Field(..., min_length=1, max_length=60000)
    fact_question: str = Field("", max_length=300)
    fact_answer: str = Field("", max_length=100)


class SaveReportRequest(BaseModel):
    kind: Literal["prompt", "tool"] = "prompt"
    title: str = Field("", max_length=200)
    model: str = Field("", max_length=120)
    subject: str = Field("", max_length=60000)
    notes: str = Field("", max_length=5000)
    result: dict[str, Any]


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""
    markdown: str = Field(..., min_length=1)
    environment: Literal["workspace", "codebuilder", "prompt-creation"] = "workspace"
    tools: list[str] | None = None


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


@router.post("/api/prompt-builder/evaluate")
def api_evaluate_prompt(req: PromptEvaluationRequest):
    return test_runner.run_prompt_component_tests(
        req.title,
        req.description,
        [component.model_dump() for component in req.sections],
        [tool.model_dump() for tool in req.tools],
    )


@router.post("/api/prompt-builder/judge")
def api_judge_prompt(req: PromptJudgeRequest):
    try:
        return prompt_judge.judge_prompt(
            req.model, req.title, req.description,
            [component.model_dump() for component in req.sections],
            [tool.model_dump() for tool in req.tools],
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"AI review returned unusable output: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI review failed: {exc}") from exc


@router.post("/api/prompt-builder/probe")
def api_probe_prompt(req: ProbeRequest):
    try:
        result = behavior_probe.run_probes(
            req.model, req.prompt, req.title, req.description, req.fact_question, req.fact_answer)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model test failed: {exc}") from exc
    passed = all(component["passed"] for component in result["components"])
    log = model_log.record_run(
        req.model, req.title, passed, result["components"],
        result["strengths"], result["weaknesses"], result["improvements"])
    result["model_log"] = {"runs": log["runs"], "passes": log["passes"], "probe_failures": log["probe_failures"]}
    return result


@router.get("/api/testing/model-logs/{model:path}")
def api_model_log(model: str):
    return model_log.get_log(model)


@router.post("/api/testing/reports")
def api_save_report(req: SaveReportRequest):
    return report_store.save_report(req.kind, req.title, req.model, req.result, req.subject, req.notes)


@router.get("/api/testing/reports")
def api_list_reports():
    return {"reports": report_store.list_reports()}


@router.get("/api/testing/reports/{report_id}")
def api_get_report(report_id: str):
    try:
        return report_store.get_report(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- Test runner -----------------------------------------------------------

@router.post("/api/testing/tool-workbench/execute")
def api_execute_tool_test(req: ToolWorkbenchRequest):
    return tool_workbench.run_python_tool(req.tool_code, req.function_input, timeout=req.timeout_seconds)


@router.post("/api/testing/tool-workbench/test-harness")
def api_test_harness(req: ToolWorkbenchRequest):
    try:
        return {"harness": tool_workbench.build_test_harness(req.tool_code)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/testing/tool-workbench/test-with-llm")
def api_test_tool_with_llm(req: ToolWorkbenchLLMRequest):
    try:
        function = tool_workbench.get_function_definition(tool_workbench.strip_test_harness(req.tool_code))
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

    def failure(code: str, text: str, arguments=None):
        return {
            "status": "ERROR",
            "error_code": code,
            "message": text,
            "llm_text_response": llm_text_response,
            "tool_calls_detected": tool_calls,
            "function_input": arguments,
            "tool_execution_result": None,
        }

    if not tool_calls:
        return failure("ERR_NO_TOOL_CALL", "The selected model did not return a tool call.")

    call = tool_calls[0].get("function", {})
    if call.get("name") != function.name:
        return failure("ERR_UNEXPECTED_TOOL_CALL", "The model called an unexpected tool function.")
    arguments = call.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return failure("ERR_INVALID_TOOL_ARGUMENTS", "The model returned invalid JSON tool arguments.")
    if not isinstance(arguments, dict):
        return failure("ERR_INVALID_TOOL_ARGUMENTS", "The model's tool arguments must be a JSON object.")
    problem = tool_workbench.validate_arguments(function, arguments)
    if problem:
        return failure("ERR_INVALID_TOOL_ARGUMENTS", problem, arguments)

    execution = tool_workbench.run_python_tool(tool_workbench.strip_test_harness(req.tool_code), arguments, timeout=req.timeout_seconds)
    return {
        "status": execution["status"],
        "error_code": execution["error_code"],
        "llm_text_response": llm_text_response,
        "tool_calls_detected": tool_calls,
        "function_input": arguments,
        "tool_execution_result": execution,
    }


@router.post("/api/testing/tool-workbench/generate-function")
def api_generate_tool_function(req: ToolWorkbenchGenerateRequest):
    try:
        generated = tool_workbench.generate_python_function(req.description, req.model)
    except ValueError as exc:
        return {"status": "ERROR", "error_code": "ERR_INVALID_GENERATED_FUNCTION",
                "message": str(exc), "code": None, "function_name": None}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Function generation failed: {exc}") from exc
    return {"status": "SUCCESS", "error_code": None, **generated}


@router.post("/api/testing/tool-workbench/promote")
def api_promote_tool(req: ToolWorkbenchRequest):
    try:
        function = tool_workbench.get_function_definition(tool_workbench.strip_test_harness(req.tool_code))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    execution = tool_workbench.run_python_tool(tool_workbench.strip_test_harness(req.tool_code), req.function_input, timeout=req.timeout_seconds)
    if execution["status"] != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail={"message": "The tool must pass its test before promotion.",
                    "test_result": execution},
        )

    clean_code = tool_workbench.strip_test_harness(req.tool_code)
    promoted = tool_workbench.promote_python_tool(clean_code, function.name)
    requirements_added = sandbox_env.add_to_requirements(clean_code)
    return {"promoted": promoted, "test_result": execution, "requirements_added": requirements_added}


class SandboxInstallRequest(BaseModel):
    packages: list[str] = Field(..., min_length=1, max_length=20)


class SandboxCheckRequest(BaseModel):
    source: str = Field("", max_length=50000)
    modules: list[str] = Field(default_factory=list, max_length=20)


@router.get("/api/sandbox/packages")
def api_sandbox_packages():
    return {"exists": sandbox_env.exists(), "packages": sandbox_env.list_packages()}


@router.post("/api/sandbox/check")
def api_sandbox_check(req: SandboxCheckRequest):
    return {"missing": sandbox_env.missing_modules(req.source, req.modules)}


@router.post("/api/sandbox/install")
def api_sandbox_install(req: SandboxInstallRequest):
    try:
        return sandbox_env.install(req.packages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/sandbox/reset")
def api_sandbox_reset():
    return sandbox_env.reset()


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
        return test_runner.run_tests_for_agent(req.agent_id, req.environment)
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
    from core_engine import tool_catalog
    from core_engine.agent_factory import LIBRARY_ROOT, parse_markdown_sections, parse_yaml_frontmatter

    if req.tools is not None:
        missing_tools = tool_catalog.unknown_tool_names(req.tools)
        if missing_tools:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tools: {', '.join(missing_tools)}",
            )

    agent_path = LIBRARY_ROOT / f"{req.agent_id}.md"
    if not agent_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Agent not found in {req.environment}: {req.agent_id}",
        )

    markdown = req.markdown.strip()
    if not markdown:
        raise HTTPException(status_code=400, detail="Prompt content must not be empty.")

    metadata = {}
    if agent_path.exists() and agent_path.suffix == ".md":
        try:
            metadata = parse_yaml_frontmatter(agent_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"Could not read agent metadata: {exc}")
    if not isinstance(metadata, dict):
        metadata = {}

    purpose = parse_markdown_sections(markdown).get("purpose", "").strip()
    if purpose:
        metadata["description"] = purpose
    metadata["id"] = req.agent_id
    metadata["name"] = metadata.get("name") or req.agent_id.replace("-", " ").title()
    metadata["mode"] = metadata.get("mode") or req.environment
    metadata["model"] = metadata.get("model") or "qwen2.5-coder:latest"
    metadata["environment"] = req.environment
    if req.tools is not None:
        metadata["tools"] = list(dict.fromkeys(req.tools))

    try:
        lines = ["---"]
        for key in ["id", "name", "description", "mode", "model", "squad", "environment", "version"]:
            if key not in metadata or metadata[key] in (None, ""):
                continue
            lines.append(f"{key}: {metadata[key]}")
        if metadata.get("tools"):
            lines.append("tools:")
            for tool in metadata["tools"]:
                lines.append(f"  - {tool}")
        lines.append("---")
        frontmatter = "\n".join(lines) + "\n\n"
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        agent_path.write_text(frontmatter + markdown + "\n", encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save agent files: {exc}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = re.sub(r"[^A-Za-z0-9_-]+", "-", (req.label or req.agent_id).strip()).strip("-_")
    label = label or req.agent_id
    snapshot_prefix = f"{req.environment}__" if req.environment != "workspace" else ""
    dest = TEST_AGENTS_DIR / f"{snapshot_prefix}{req.agent_id}__{label}__{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    if agent_path.exists():
        shutil.copy2(agent_path, dest / agent_path.name)

    manifest_path = TEST_AGENTS_DIR / "manifest.json"
    manifest = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    manifest.append({
        "agent_id": req.agent_id,
        "environment": req.environment,
        "label": label,
        "snapshot": dest.name,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = test_runner.run_header_tests(markdown, req.agent_id)
    report["source"] = f"library/{req.agent_id}.md"
    return {"saved": True, "path": f"library/{req.agent_id}.md",
            "metadata_path": f"library/{req.agent_id}.md",
            "environment": req.environment,
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
