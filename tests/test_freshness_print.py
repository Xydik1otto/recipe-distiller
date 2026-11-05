"""Freshness: date added shown, sort-by-newness explicit, printable shopping list."""

import time
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "static" / "index.html"


def test_list_returns_saved_at(client):
    client, _ = client
    client.post("/api/recipes", json={"url": "https://example.com/borscht"})
    recipes = client.get("/api/recipes").json()["recipes"]
    assert recipes and recipes[0]["saved_at"] > 0


def test_sort_new_explicit_matches_default(client):
    client, _ = client
    client.post("/api/recipes", json={"url": "https://example.com/cake"})
    time.sleep(0.02)  # ensure saved_at differs
    client.post("/api/recipes", json={"url": "https://example.com/borscht"})
    default = client.get("/api/recipes").json()["recipes"]
    by_new = client.get("/api/recipes?sort=new").json()["recipes"]
    assert [r["id"] for r in default] == [r["id"] for r in by_new]
    # newest first: borscht was saved last
    assert by_new[0]["title"].lower().find("borscht") >= 0 or by_new[0]["id"] > by_new[-1]["id"]
    assert [r["id"] for r in by_new] == sorted((r["id"] for r in by_new), reverse=True)


def test_sort_title_overrides_newness(client):
    client, _ = client
    client.post("/api/recipes", json={"url": "https://example.com/borscht"})
    client.post("/api/recipes", json={"url": "https://example.com/cake"})
    titles = [r["title"] for r in client.get("/api/recipes?sort=title").json()["recipes"]]
    assert titles == sorted(titles, key=str.casefold)


def test_ui_shows_date_added_and_new_sort():
    src = SRC.read_text(encoding="utf-8")
    assert 'value="new"' in src                        # explicit newness option
    assert "toLocaleDateString" in src                 # date added next to each recipe


def test_ui_shopping_list_is_printable():
    src = SRC.read_text(encoding="utf-8")
    assert "window.print()" in src                     # print button on the list
    assert "body > :not(#shoplist)" in src             # print CSS: list only
    assert "#shoplist.hidden" in src                   # but nothing when hidden
