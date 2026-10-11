"""Data models and request schemas for the CodeBuilder pillar."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    timeout_seconds: float = Field(default=10.0, description="Execution timeout in seconds")
    mode: str = Field(
        default="safe",
        description="Execution mode: 'safe' runs in-process; 'risky' runs in an isolated subprocess",
    )


class DiagnosticItem(BaseModel):
    path: Optional[str] = Field(default=None, description="Target file path, if available")
    line: Optional[int] = Field(default=None, description="Line number of the issue")
    column: Optional[int] = Field(default=None, description="Column number of the issue")
    message: str = Field(..., description="Diagnostic error message")
    severity: str = Field(default="error", description="Severity level: error, warning, or info")
    run_id: Optional[str] = Field(default=None, description="Execution run identifier")


class CodeExecutionResult(BaseModel):
    run_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)


class StructuredEditRequest(BaseModel):
    target_path: str = Field(..., description="Target file path relative to the workspace root")
    content: str = Field(..., description="Proposed content or patch")
    explanation: Optional[str] = Field(default=None, description="Explanation of the requested change")
