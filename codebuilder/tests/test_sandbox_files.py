import pytest

from codebuilder import files
from test_environment import sandbox_env, sandbox_paths


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    config = tmp_path / "allowed_paths.json"
    config.write_text('{"sandbox_roots": [%s]}' % ('"' + str(docs).replace("\\", "\\\\") + '"'), encoding="utf-8")
    monkeypatch.setattr(sandbox_env, "CONFIG_PATH", config)
    monkeypatch.setattr(sandbox_env, "SCRIPTS_DIR", scripts)
    return scripts, docs


def test_save_and_read_in_scripts_and_extra_root(sandbox):
    scripts, docs = sandbox
    saved = files.save(str(scripts), "app", "print(1)\n")
    assert saved["saved"] and saved["name"] == "app.py"
    assert files.read(saved["path"])["content"] == "print(1)\n"
    assert files.save(str(docs), "doc.py", "x = 1\n")["saved"]
    assert {f["name"] for f in files.listing()["files"]} == {"app.py", "doc.py"}


def test_overwrite_needs_confirmation(sandbox):
    scripts, _ = sandbox
    files.save(str(scripts), "a.py", "1")
    again = files.save(str(scripts), "a.py", "2")
    assert again["exists"] and not again["saved"]
    assert (scripts / "a.py").read_text() == "1"
    assert files.save(str(scripts), "a.py", "2", overwrite=True)["saved"]


def test_escapes_and_bad_names_are_rejected(sandbox, tmp_path):
    scripts, _ = sandbox
    with pytest.raises(files.FileRejected):
        files.save(str(tmp_path), "outside.py", "x")
    with pytest.raises(files.FileRejected):
        files.save(str(scripts / ".." ), "escape.py", "x")
    for name in ("..\\x.py", "a/b.py", "bad:name.py"):
        with pytest.raises(files.FileRejected):
            files.save(str(scripts), name, "x")
    (tmp_path / "secret.py").write_text("x")
    with pytest.raises(files.FileRejected):
        files.read(str(tmp_path / "secret.py"))


def test_add_remove_clear_roots(sandbox, tmp_path):
    scripts, docs = sandbox
    extra = tmp_path / "extra"
    extra.mkdir()
    sandbox_paths.add_root(str(extra))
    assert sandbox_paths.is_allowed(extra)
    assert sandbox_paths.remove_root(str(extra)) is True
    assert not sandbox_paths.is_allowed(extra)
    sandbox_paths.clear_roots()
    assert [r for r in sandbox_paths.allowed_roots()] == [scripts.resolve()]
    with pytest.raises(ValueError):
        sandbox_paths.remove_root(str(scripts))


def test_run_command_picks_streamlit(sandbox):
    assert files.run_command("C:/a/app.py", "import streamlit as st").startswith("streamlit run")
    assert files.run_command("C:/a/app.py", "print(1)").startswith("python ")


def test_unconfigured_root_falls_back_inside_repo(tmp_path, monkeypatch):
    config = tmp_path / "allowed_paths.json"
    config.write_text('{"sandbox_root": "Z:\\\\definitely\\\\missing\\\\root"}', encoding="utf-8")
    monkeypatch.setattr(sandbox_env, "CONFIG_PATH", config)
    monkeypatch.setattr(sandbox_env, "FALLBACK_ROOT", tmp_path / "fallback")
    assert sandbox_env.sandbox_root() == tmp_path / "fallback"
