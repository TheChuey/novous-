"""CodeBuilder contracts: the data shapes shared by every layer.

This module is dependency-free (pydantic only). The HTTP adapter, the service,
the engine and the agent tools all speak these models and nothing else.

Compatibility: every field that existed before keeps its name, type and default.
New fields are additive and optional, so the existing frontend keeps working.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# Why a run was stopped by the supervisor (values of StuckInfo.reason).
STUCK_TIMEOUT = "timeout"          # still running at the deadline (loop, sleep, blocking call)
STUCK_OUTPUT_LIMIT = "output_limit"  # unbounded output (e.g. `while True: print(...)`)
STUCK_CANCELLED = "cancelled"      # stopped on request (cancel endpoint / client disconnect)


class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    timeout_seconds: float = Field(default=10.0, description="Hard wall-clock limit in seconds")
    mode: str = Field(
        default="safe",
        description="'safe': buffered result, stdout/stderr kept apart. "
        "'risky': merged output, streamable over SSE. Both run isolated.",
    )


class DiagnosticItem(BaseModel):
    path: Optional[str] = Field(default=None, description="Target file path, if available")
    line: Optional[int] = Field(default=None, description="Line number of the issue")
    column: Optional[int] = Field(default=None, description="Column number of the issue")
    message: str = Field(..., description="Diagnostic error message")
    severity: str = Field(default="error", description="Severity level: error, warning, or info")
    run_id: Optional[str] = Field(default=None, description="Execution run identifier")


class StuckInfo(BaseModel):
    """Explains why a run had to be stopped, and what to try next."""

    reason: str = Field(..., description="timeout | output_limit | cancelled")
    message: str
    line: Optional[int] = Field(default=None, description="Line of user code that was executing")
    source: Optional[str] = Field(default=None, description="Text of that line")
    hint: str = ""


class CodeExecutionResult(BaseModel):
    run_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)
    # Additive fields (ignored by older clients):
    return_code: Optional[int] = None
    timed_out: bool = False
    duration_seconds: Optional[float] = None
    stuck: Optional[StuckInfo] = None


class StructuredEditRequest(BaseModel):
    target_path: str = Field(..., description="Target file path relative to the workspace root")
    content: str = Field(..., description="Proposed content or patch")
    explanation: Optional[str] = Field(default=None, description="Explanation of the requested change")
