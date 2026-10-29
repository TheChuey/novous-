"""Pydantic schemas for generic orchestration tasks."""

from typing import Any, List, Optional

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
    user_query: str = Field(..., description="User query or task prompt")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Custom parameters")


class OrchestrationResponse(BaseModel):
    trace_id: str
    pattern: str
    query: str
    status: str
    final_answer: str
    result_payload: Optional[Any] = None
    execution_trace: List[TraceStep] = Field(default_factory=list)
