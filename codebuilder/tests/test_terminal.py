import time

from codebuilder.terminal import TerminalBusy, TerminalSession


def _wait(session, seconds=10):
    deadline = time.time() + seconds
    while session.running and time.time() < deadline:
        time.sleep(0.05)
    time.sleep(0.2)


def test_runs_command_and_buffers_output():
    session = TerminalSession()
    session.run("echo novous-terminal")
    _wait(session)
    text, end = session.read(0)
    assert "novous-terminal" in text and "[process exited with code 0]" in text
    assert session.read(end)[0] == ""


def test_cd_is_limited_to_allowed_folders(tmp_path):
    session = TerminalSession()
    start = session.cwd
    session.run(f'cd "{tmp_path}"')
    assert session.cwd == start
    assert "outside the allowed sandbox paths" in session.read(0)[0]
    (start / "sub").mkdir(exist_ok=True)
    session.run("cd sub")
    assert session.cwd == (start / "sub").resolve()
    session.run("cd does-not-exist")
    assert session.cwd == (start / "sub").resolve()
    (start / "sub").rmdir() if not any((start / "sub").iterdir()) else None


def test_busy_then_stop():
    session = TerminalSession()
    session.run('python -c "import time; time.sleep(30)"')
    try:
        session.run("echo second")
        raised = False
    except TerminalBusy:
        raised = True
    assert raised
    assert session.stop() is True
    _wait(session)
    assert not session.running
