"""First-run demo: opt-in load of 3 demo recipes into the book."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.demo import DEMO_RECIPES


def test_demo_data_is_well_formed():
    assert len(DEMO_RECIPES) == 3
    for demo in DEMO_RECIPES:
        assert demo["url"].startswith("https://demo.local/")
        r = demo["recipe"]
        assert r["title"] and r["ingredients"] and r["steps"] and r["servings"]


def test_api_loads_three_demo_recipes(client):
    client, _ = client
    r = client.post("/api/demo")
    assert r.status_code == 200
    assert r.json() == {"added": 3}
    titles = [item["title"] for item in client.get("/api/recipes").json()["recipes"]]
    assert len(titles) == 3
    assert any("borscht" in t.lower() for t in titles)


def test_api_demo_is_idempotent(client):
    client, _ = client
    assert client.post("/api/demo").json()["added"] == 3
    assert client.post("/api/demo").json()["added"] == 0
    assert len(client.get("/api/recipes").json()["recipes"]) == 3


def test_demo_recipes_work_with_shopping_list(client):
    """Demo recipes have parseable quantities — the whole pipeline is tryable."""
    client, _ = client
    client.post("/api/demo")
    ids = [r["id"] for r in client.get("/api/recipes").json()["recipes"]]
    r = client.post("/api/shopping-list", json={"recipe_ids": ids})
    body = r.json()
    assert r.status_code == 200
    assert len(body["items"]) >= len(body["unparsed"])  # mostly parsed quantities


def test_ui_has_optin_demo_banner(client):
    client, _ = client
    page = client.get("/").text
    assert 'id="demobanner"' in page
    assert 'id="demobtn"' in page                      # opt-in button
    assert "/api/demo" in page
    assert "rd-demo-dismissed" in page                 # dismiss / once-only flag
