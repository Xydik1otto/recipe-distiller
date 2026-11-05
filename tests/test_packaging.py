"""Packaging: pyproject metadata, console-script entry point, requirements parity."""

import configparser  # noqa: F401  (stdlib sanity import)
import tomllib
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _project():
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]


def test_metadata_complete():
    p = _project()
    assert p["name"] == "recipe-distiller"
    assert p["readme"] == "README.md"
    assert p["license"] == {"text": "MIT"}
    assert p["requires-python"] == ">=3.10"
    deps = {d.split(">")[0].split("[")[0] for d in p["dependencies"]}
    assert {"fastapi", "uvicorn", "httpx", "beautifulsoup4"} <= deps


def test_console_script_declared_and_importable():
    p = _project()
    assert p["scripts"]["recipe-distiller"] == "app.cli:main"
    cli = import_module("app.cli")
    assert callable(cli.main)


def test_requirements_match_pyproject_dependencies():
    declared = {d.split(">=")[0].split("[")[0]: d for d in _project()["dependencies"]}
    req = {}
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            req[line.split(">=")[0].split("[")[0]] = line
    for name, spec in declared.items():
        assert name in req, f"{name} missing from requirements.txt"
        assert req[name] == spec
    assert "pytest" in req  # the repo runs its tests straight from requirements


def test_entry_point_installed_and_runs():
    """`pip install -e .` really works: the script is on PATH and answers --help."""
    import shutil
    import subprocess
    exe = shutil.which("recipe-distiller")
    assert exe, "console script not installed (run: pip install -e .)"
    out = subprocess.run([exe, "--help"], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0
    assert "--port" in out.stdout
