"""CodeBuilder pillar package.

Layers (dependencies point downward only):

    interface.py   HTTP adapter (FastAPI router)          \
    tools/         agent adapter (@tool functions)         > service.py  -> host bridge (lazy)
                                                          /
    execution.py   engine: isolated runs, stuck handling
    schemas.py     contracts (pydantic models)

Importing this package is cheap and has no dependency on the host app.
"""

from .execution import execute_python_code
from .schemas import (
    CodeExecutionRequest,
    CodeExecutionResult,
    DiagnosticItem,
    StructuredEditRequest,
)
from .service import agent_meta as load_codebuilder_agent_meta

__all__ = [
    "CodeExecutionRequest",
    "CodeExecutionResult",
    "DiagnosticItem",
    "StructuredEditRequest",
    "execute_python_code",
    "load_codebuilder_agent_meta",
]
