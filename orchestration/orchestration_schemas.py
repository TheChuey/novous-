"""Pydantic schemas for generic orchestration tasks."""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    step_number: int
    agent_id: str
    phase: str
    status: str
    details: str
    error_reason: Optional[str] = None
    timestamp: str


class OrchestrationRequest(BaseModel):
    trace_id: Optional[str] = Field(
        default=None,
        max_length=80,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Optional trace ID assigned by the orchestration service",
    )
    squad_id: Optional[str] = Field(
        default=None, description="Registered squad to associate with this run"
    )
    pattern: str = Field(
        default="sequential",
        description="Execution strategy: 'sequential' (default for local LLM hardware safety), 'fanout', or 'router'",
    )
    primary_agent: str = Field(
        default="rag-presenter", description="Main user-facing agent ID from library/"
    )
    subagents: List[str] = Field(
        default_factory=list, description="Ordered sub-agent IDs from subAgentLibrary/"
    )
    workflow_action: Literal["all", "plan", "build", "troubleshoot"] = Field(
        default="all",
        description="Optional registered Code Development Squad action.",
    )
    user_query: str = Field(..., description="User query or task prompt")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Custom parameters")


class SquadCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)
    primary_agent: str = Field(..., min_length=1, max_length=80)
    subagents: List[str] = Field(default_factory=list, max_length=20)


class OrchestrationResponse(BaseModel):
    trace_id: str
    pattern: str
    query: str
    status: str
    final_answer: str
    result_payload: Optional[Any] = None
    execution_trace: List[TraceStep] = Field(default_factory=list)
