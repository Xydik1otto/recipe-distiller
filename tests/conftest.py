"""Shared fixtures: HTML fixtures loader + FastAPI TestClient with mocked fetch."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(PROJECT_ROOT))


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient with an isolated SQLite DB and fetch_html monkeypatched."""
    monkeypatch.setenv("RECIPE_DB", str(tmp_path / "test.db"))
    import app.main as main_mod
    calls = []

    def fake_fetch(url, max_attempts=3, timeout=20.0):
        calls.append(url)
        mapping = {
            "https://example.com/borscht": load("jsonld.html"),
            "https://example.com/cake": load("jsonld_sections.html"),
            "https://example.com/pancakes": load("microdata.html"),
            "https://example.com/soup": load("heuristic.html"),
            "https://example.com/about": load("not_a_recipe.html"),
        }
        if url not in mapping:
            raise RuntimeError(f"failed to fetch {url}: no fixture")
        return mapping[url]

    monkeypatch.setattr(main_mod, "fetch_html", fake_fetch)
    from fastapi.testclient import TestClient
    yield TestClient(main_mod.app), calls
