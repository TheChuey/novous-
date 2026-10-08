"""Test Environment Doorway: Python API & FastAPI Router
(/api/testing/*, /api/prompt-builder/*)."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from test_environment import prompt_builder, test_runner

router = APIRouter()

TEST_AGENTS_DIR = Path(__file__).resolve().parent / "test_agents"


class HeaderTestRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)


class AssembleRequest(BaseModel):
    parts: list[str] = []
    extra_instructions: str = ""


class PublishRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    label: str = ""


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
    """Snapshot an agent definition into the isolated test_agents/ fixture store."""
    from core_engine.agent_factory import find_agent_dir
    agent_dir = find_agent_dir(req.agent_id)
    if not agent_dir:
        raise HTTPException(status_code=404, detail=f"Agent not found: {req.agent_id}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = (req.label or req.agent_id).strip()
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
    return {"published": True, "snapshot": dest.name, "path": f"test_agents/{dest.name}",
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
