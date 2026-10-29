import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core_engine.interface import router as core_router
from editor.interface import router as editor_router
from workspace.interface import router as workspace_router
from test_environment.interface import router as test_router
from codebuilder.interface import router as codebuilder_router
from file_manager.interface import router as file_manager_router
from tools.interface import router as tools_router
from orchestration import router as orchestration_router

app = FastAPI(title="Novous AGENT FACTORY", version="4.0.0")


@app.on_event("startup")
def migrate_sandbox_environment():
    """Move packages from the old in-repo sandbox venv to the configured sandbox folder."""
    import threading
    from agentMemory.interface import start_document_scanner
    from test_environment import sandbox_env

    threading.Thread(target=sandbox_env.migrate_legacy, daemon=True).start()
    start_document_scanner()

# Mount Component Backend Routers
app.include_router(tools_router)
app.include_router(core_router)
app.include_router(editor_router)
app.include_router(workspace_router)
app.include_router(test_router)
app.include_router(codebuilder_router)
app.include_router(file_manager_router)
app.include_router(orchestration_router)

# Serve Static Assets (CSS, JS)
app.mount("/static", StaticFiles(directory=Path("frontend") / "static"), name="static")

# Mount Page Routes
@app.get("/")
def index_page():
    return FileResponse("frontend/pages/index.html")

@app.get("/editor")
def editor_page():
    return FileResponse("frontend/pages/editor.html")

@app.get("/codebuilder")
def codebuilder_page():
    return FileResponse("frontend/pages/codeBuilder.html")

@app.get("/chat")
def chat_page():
    return FileResponse("frontend/pages/chat.html")

@app.get("/terminal")
def terminal_page():
    return FileResponse("frontend/pages/terminal.html")

@app.api_route("/test", methods=["GET", "POST"])
def test_page():
    return FileResponse("frontend/pages/testing.html")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("PROJECT_MANAGER_HOST", "127.0.0.1")
    port = int(os.getenv("PROJECT_MANAGER_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)
