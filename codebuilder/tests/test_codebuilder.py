"""CodeBuilder pillar tests. Standalone: no Ollama, no running host.

Run from the repo root:  python -m pytest codebuilder/tests -q
"""

import contextlib
import importlib
import importlib.machinery
import importlib.util
import os
import sys
import threading
import time
import types

import pytest

from codebuilder import service
from codebuilder.execution import cancel_run, execute_python_code, run_stream
from codebuilder.schemas import CodeExecutionRequest as Req
from codebuilder.schemas import StructuredEditRequest


def run(code, **kw):
    return execute_python_code(Req(code=code, **kw))


# --- engine: normal paths ---------------------------------------------------
def test_success_keeps_streams_apart():
    res = run("import sys\nprint('out')\nprint('err', file=sys.stderr)")
    assert res.status == "SUCCESS" and res.stdout == "out\n" and res.stderr == "err\n"
    assert res.stuck is None and not res.timed_out


def test_risky_mode_merges_in_order():
    res = run("import sys\nprint('o')\nprint('e', file=sys.stderr)", mode="risky")
    assert res.stdout == "o\ne\n" and res.stderr == ""


def test_runtime_error_reports_user_line():
    res = run("x = 1\nprint(x)\nprint(undefined_name)")
    assert res.status == "ERROR"
    assert res.diagnostics[0].line == 3 and "NameError" in res.diagnostics[0].message


def test_syntax_error_is_structured_and_fast():
    res = run("def f(:\n  pass")
    assert res.status == "ERROR" and res.diagnostics[0].line == 1
    assert "SyntaxError" in res.stderr


def test_input_fails_fast_instead_of_hanging():
    t = time.time()
    res = run("input('name? ')")
    assert time.time() - t < 5 and "EOFError" in res.stderr


# --- engine: stuck handling -------------------------------------------------
def test_infinite_loop_is_stopped_and_located():
    t = time.time()
    res = run("n = 0\nwhile True:\n    n += 1\n", timeout_seconds=1.0)
    assert time.time() - t < 4
    assert res.timed_out and res.status == "ERROR"
    assert res.stuck.reason == "timeout" and res.stuck.line in (2, 3)
    assert "while" in res.stuck.hint.lower()


def test_blocking_call_is_located():
    res = run("import time\nprint('x', end='', flush=True)\ntime.sleep(60)", timeout_seconds=1.0)
    assert res.timed_out and res.stuck.line == 3 and res.stdout == "x"


def test_unbounded_output_is_stopped_early():
    t = time.time()
    res = run("while True:\n    print('x' * 100)", timeout_seconds=10)
    assert time.time() - t < 5
    assert res.stuck.reason == "output_limit" and not res.timed_out


def test_timeout_is_clamped():
    res = run("print(1)", timeout_seconds=-5)  # nonsense input must not disable the limit
    assert res.status == "SUCCESS"


def test_cancel_stops_a_live_run():
    events, ids = [], []

    def consume():
        for ev in run_stream(Req(code="import time\ntime.sleep(60)", timeout_seconds=60, mode="risky")):
            events.append(ev)
            if ev["type"] == "start":
                ids.append(ev["run_id"])

    th = threading.Thread(target=consume)
    th.start()
    deadline = time.time() + 5
    while not ids and time.time() < deadline:
        time.sleep(0.02)
    assert cancel_run(ids[0]) is True
    th.join(10)
    assert not th.is_alive() and events[-1]["stuck"]["reason"] == "cancelled"
    assert cancel_run(ids[0]) is False


@pytest.mark.skipif(os.name == "nt", reason="uses /proc to look for leaked processes")
def test_child_processes_do_not_outlive_a_timeout():
    marker = f"GRANDCHILD_{os.getpid()}"
    code = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)  # {marker}'])\n"
        "time.sleep(300)\n"
    )
    assert run(code, timeout_seconds=1.0).timed_out
    time.sleep(0.4)
    leaked = []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace")
        except OSError:
            continue
        if marker in cmd and int(pid) != os.getpid() and "pytest" not in cmd:
            leaked.append(pid)
    assert leaked == []


def test_closing_the_stream_kills_the_process():
    gen = run_stream(Req(code="import time\nprint('x', flush=True)\ntime.sleep(60)", timeout_seconds=30, mode="risky"))
    for ev in gen:
        if ev["type"] == "stdout":
            break
    t = time.time()
    gen.close()
    assert time.time() - t < 3


# --- service ----------------------------------------------------------------
def test_edit_is_confined_to_the_project_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEBUILDER_EDIT_ROOT", str(tmp_path))
    ok = service.apply_edit(StructuredEditRequest(target_path="a/b.py", content="x = 1\n"))
    assert ok["status"] == "applied" and (tmp_path / "a" / "b.py").read_text() == "x = 1\n"
    for bad in ("../escape.py", str(tmp_path.parent / "escape.py"), "a"):
        with pytest.raises(service.EditRejected):
            service.apply_edit(StructuredEditRequest(target_path=bad, content="x"))


def test_agent_meta_has_the_documented_shape():
    meta = service.agent_meta()
    assert {"id", "name", "description", "mode", "tools"} <= set(meta)


# --- HTTP adapter -----------------------------------------------------------
@pytest.fixture()
def client():
    pytest.importorskip("httpx")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from codebuilder.interface import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_http_contract(client):
    assert client.get("/api/codebuilder/health").json() == {"status": "ok", "pillar": "codebuilder"}
    body = client.post("/api/codebuilder/execute", json={"code": "print('hi')"}).json()
    assert {"run_id", "status", "stdout", "stderr", "diagnostics"} <= set(body)
    assert client.post("/api/codebuilder/execute/stream", json={"code": "1", "mode": "safe"}).status_code == 400
    assert client.post("/api/codebuilder/execute/run_missing/cancel").status_code == 404


def test_http_stream_event_schema(client):
    import json

    with client.stream("POST", "/api/codebuilder/execute/stream",
                       json={"code": "print('a')", "mode": "risky"}) as resp:
        events = [json.loads(l[6:]) for l in resp.iter_lines() if l.startswith("data: ")]
    assert events[0]["type"] == "start" and events[-1]["type"] == "done"
    assert any(e["type"] == "stdout" and "a" in e["text"] for e in events)


# --- host contract: tool registration --------------------------------------
@contextlib.contextmanager
def fake_host(with_hitl):
    registry = {}
    pkg = types.ModuleType("core_engine")
    pkg.__path__ = []
    catalog = types.ModuleType("core_engine.tool_catalog")

    def tool(name=None, provider="core_engine"):
        def deco(fn):
            registry[name or fn.__name__] = provider
            return fn
        return deco

    catalog.tool = tool
    mods = {"core_engine": pkg, "core_engine.tool_catalog": catalog}
    if with_hitl:
        mods["core_engine.hitl"] = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("core_engine.hitl", None))
    saved = {k: sys.modules.get(k) for k in [*mods, "codebuilder.tools.tool_library"]}
    sys.modules.update(mods)
    sys.modules.pop("codebuilder.tools.tool_library", None)
    try:
        importlib.import_module("codebuilder.tools.tool_library")
        yield registry
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def test_tools_register_without_questionnaire_support():
    with fake_host(with_hitl=False) as registry:
        assert registry == {"send_code_to_editor": "codebuilder", "run_code_in_editor": "codebuilder"}


def test_questionnaire_tool_registers_when_host_has_hitl():
    with fake_host(with_hitl=True) as registry:
        assert registry.get("ask_user_questions") == "codebuilder"


# --- service: questionnaire bridge -----------------------------------------
@contextlib.contextmanager
def fake_questionnaire_host(file_text, answers=None):
    pkg = types.ModuleType("core_engine")
    pkg.__path__ = []
    tools = types.ModuleType("core_engine.langgraph_tools")

    class _ReadFile:
        @staticmethod
        def invoke(args):
            return file_text

    tools.read_file_tool = _ReadFile
    hitl = types.ModuleType("core_engine.hitl")
    state = {}

    def create_request(questions, session_id=None):
        event = threading.Event()
        state["record"] = {"request_id": "req_1", "event": event}
        if answers is not None:
            state["answers"] = answers
            event.set()
        return state["record"]

    def resolve_request(request_id):
        return {"answers": state.get("answers", {})} if state.get("answers") is not None else None

    hitl.create_request, hitl.resolve_request = create_request, resolve_request
    pkg.hitl, pkg.langgraph_tools = hitl, tools
    mods = {"core_engine": pkg, "core_engine.hitl": hitl, "core_engine.langgraph_tools": tools}
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def test_questionnaire_returns_answers_matched_by_id():
    import json

    text = json.dumps([{"id": "a", "question": "Q1"}, {"id": "b", "question": "Q2"}])
    with fake_questionnaire_host(text, answers={"a": "one", "b": "two"}):
        out = json.loads(service.ask_user("qs.json", timeout_seconds=5))
    assert out["status"] == "COMPLETED"
    assert [p["answer"] for p in out["qa_pairs"]] == ["one", "two"]


def test_questionnaire_times_out_instead_of_blocking_forever():
    with fake_questionnaire_host('["only question"]', answers=None):
        t = time.time()
        out = service.ask_user("qs.json", timeout_seconds=1)
    assert "timed out" in out and time.time() - t < 5


def test_questionnaire_reports_bad_files_as_text_errors():
    with fake_questionnaire_host("not json"):
        assert service.ask_user("qs.json").startswith("Error")
    with fake_questionnaire_host("Error reading file: nope"):
        assert "not found" in service.ask_user("qs.json")
