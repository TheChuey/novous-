"""Isolated virtualenv used to run untrusted test code (Tool Workbench and Code Builder)."""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "tools" / "allowed_paths.json"
FALLBACK_ROOT = PROJECT_ROOT / "workspace" / "sandbox"
LEGACY_VENV = PROJECT_ROOT / "workspace" / ".sandbox-venv"


def read_config() -> dict:
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _usable_root(candidate: Path) -> bool:
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def sandbox_root() -> Path:
    """Folder holding the sandbox venv and scripts: ``sandbox_root`` in allowed_paths.json, else inside the repo."""
    configured = str(read_config().get("sandbox_root") or "").strip()
    if configured:
        candidate = Path(os.path.expandvars(configured)).expanduser()
        if candidate.is_absolute() and _usable_root(candidate):
            return candidate.resolve()
    FALLBACK_ROOT.mkdir(parents=True, exist_ok=True)
    return FALLBACK_ROOT


SANDBOX_ROOT = sandbox_root()
SANDBOX_DIR = SANDBOX_ROOT / "venv"
SCRIPTS_DIR = SANDBOX_ROOT / "scripts"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
VENV_TIMEOUT_SECONDS = 120
INSTALL_TIMEOUT_SECONDS = 300
MAX_OUTPUT_CHARS = 20000

_PACKAGE_SPEC = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}((==|>=)[A-Za-z0-9._!+-]{1,40})?$")
_MODULE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_lock = threading.Lock()

# Import names that differ from their PyPI package name.
IMPORT_TO_PACKAGE = {
    "cv2": "opencv-python", "PIL": "pillow", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "yaml": "pyyaml", "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv", "dateutil": "python-dateutil", "serial": "pyserial",
    "docx": "python-docx", "fitz": "pymupdf", "jwt": "pyjwt", "attr": "attrs",
    "OpenSSL": "pyopenssl", "Crypto": "pycryptodome", "magic": "python-magic",
}


def exists() -> bool:
    return python_path().exists()


def python_path() -> Path:
    scripts = "Scripts" if os.name == "nt" else "bin"
    return SANDBOX_DIR / scripts / ("python.exe" if os.name == "nt" else "python")


def interpreter() -> str:
    """The sandbox Python when it exists, otherwise the server's own interpreter."""
    return str(python_path()) if exists() else sys.executable


def _run(command: list[str], timeout: int) -> dict:
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        completed = subprocess.run(
            command, capture_output=True, timeout=timeout, text=True,
            encoding="utf-8", errors="replace", **kwargs,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"Timed out after {timeout} seconds."}
    except OSError as exc:
        return {"ok": False, "output": f"Could not start process: {exc}"}
    output = (completed.stdout + completed.stderr).strip()
    return {"ok": completed.returncode == 0, "output": output[-MAX_OUTPUT_CHARS:]}


def migrate_legacy() -> dict:
    """Move packages from the old in-repo venv into the new sandbox venv, then delete the old one."""
    legacy_python = LEGACY_VENV / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if not legacy_python.exists() or LEGACY_VENV.resolve() == SANDBOX_DIR.resolve():
        return {"ok": True, "migrated": False}
    frozen = _run([str(legacy_python), "-m", "pip", "freeze", "--disable-pip-version-check"], 60)
    packages = [line.strip() for line in frozen["output"].splitlines() if line.strip() and not line.startswith(("-e", "#", "@"))] if frozen["ok"] else []
    created = ensure_venv()
    if not created["ok"]:
        return {"ok": False, "migrated": False, "output": created["output"]}
    if packages:
        installed = _run(
            [str(python_path()), "-m", "pip", "install", "--disable-pip-version-check", *packages],
            INSTALL_TIMEOUT_SECONDS,
        )
        if not installed["ok"]:
            return {"ok": False, "migrated": False, "output": installed["output"]}
    shutil.rmtree(LEGACY_VENV, ignore_errors=True)
    return {"ok": True, "migrated": True, "packages": len(packages)}


def ensure_venv() -> dict:
    with _lock:
        if exists():
            return {"ok": True, "output": "Sandbox environment is ready."}
        SANDBOX_DIR.parent.mkdir(parents=True, exist_ok=True)
        SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        return _run([sys.executable, "-m", "venv", str(SANDBOX_DIR)], VENV_TIMEOUT_SECONDS)


def validate_packages(packages: list[str]) -> list[str]:
    cleaned = []
    for package in packages:
        spec = (package or "").strip()
        if not _PACKAGE_SPEC.fullmatch(spec):
            raise ValueError(f"Invalid package name: {spec!r}")
        cleaned.append(spec)
    if not cleaned:
        raise ValueError("Enter at least one package.")
    if len(cleaned) > 20:
        raise ValueError("Install at most 20 packages at a time.")
    return cleaned


def install(packages: list[str]) -> dict:
    cleaned = validate_packages(packages)
    created = ensure_venv()
    if not created["ok"]:
        return {"ok": False, "packages": cleaned, "output": created["output"]}
    result = _run(
        [str(python_path()), "-m", "pip", "install", "--disable-pip-version-check", *cleaned],
        INSTALL_TIMEOUT_SECONDS,
    )
    return {"ok": result["ok"], "packages": cleaned, "output": result["output"]}


def reset() -> dict:
    with _lock:
        if SANDBOX_DIR.exists():
            shutil.rmtree(SANDBOX_DIR, ignore_errors=True)
            if SANDBOX_DIR.exists():
                return {"ok": False, "output": "Could not remove the sandbox; close programs using it and retry."}
    created = ensure_venv()
    return {"ok": created["ok"], "output": "Sandbox reset to an empty environment." if created["ok"] else created["output"]}


def list_packages() -> list[dict]:
    if not exists():
        return []
    result = _run([str(python_path()), "-m", "pip", "list", "--format=json", "--disable-pip-version-check"], 60)
    if not result["ok"]:
        return []
    try:
        return json.loads(result["output"])
    except json.JSONDecodeError:
        return []


def imported_modules(source: str) -> list[str]:
    """Top-level module names imported by source, in order of first appearance."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module.split(".")[0])
    return list(dict.fromkeys(name for name in names if _MODULE_NAME.fullmatch(name)))


def _is_local_module(name: str) -> bool:
    return (PROJECT_ROOT / name).is_dir() or (PROJECT_ROOT / f"{name}.py").is_file()


def third_party_modules(source: str) -> list[str]:
    return [
        name for name in imported_modules(source)
        if name not in sys.stdlib_module_names and not _is_local_module(name)
    ]


def package_for_module(module: str) -> str:
    return IMPORT_TO_PACKAGE.get(module, module)


def missing_modules(source: str, extra: list[str] | None = None) -> list[dict]:
    """Third-party modules the sandbox interpreter cannot import."""
    modules = list(dict.fromkeys(third_party_modules(source) + [m for m in (extra or []) if _MODULE_NAME.fullmatch(m)]))
    if not modules:
        return []
    probe = (
        "import importlib.util, json, sys\n"
        "print(json.dumps([m for m in json.loads(sys.argv[1]) if importlib.util.find_spec(m) is None]))"
    )
    result = _run([interpreter(), "-I", "-c", probe, json.dumps(modules)], 30)
    try:
        missing = json.loads(result["output"].splitlines()[-1]) if result["ok"] else modules
    except (json.JSONDecodeError, IndexError):
        missing = modules
    return [{"module": name, "package": package_for_module(name)} for name in missing]


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names() -> set[str]:
    if not REQUIREMENTS_PATH.exists():
        return set()
    names = set()
    for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if match and not line.lstrip().startswith("#"):
            names.add(_normalize(match.group(1)))
    return names


def add_to_requirements(source: str) -> list[str]:
    """Append third-party packages imported by source that requirements.txt lacks."""
    known = _requirement_names()
    installed = {_normalize(p["name"]): p["version"] for p in list_packages()}
    added = []
    for module in third_party_modules(source):
        package = package_for_module(module)
        key = _normalize(package)
        if key in known:
            continue
        version = installed.get(key)
        added.append(f"{package}>={version}" if version else package)
        known.add(key)
    if added:
        existing = REQUIREMENTS_PATH.read_text(encoding="utf-8") if REQUIREMENTS_PATH.exists() else ""
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        with REQUIREMENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(prefix + "\n".join(added) + "\n")
    return added
