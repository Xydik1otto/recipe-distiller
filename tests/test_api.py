"""API + storage tests: extract endpoint, cache, recipe book, print view."""

from app import db


def test_extract_jsonld_page(client):
    client, calls = client
    r = client.post("/api/extract", json={"url": "https://example.com/borscht"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "live"
    assert body["recipe"]["title"] == "Grandma's Borscht"
    assert len(body["recipe"]["ingredients"]) == 3


def test_extract_uses_cache_on_second_call(client):
    client, calls = client
    r1 = client.post("/api/extract", json={"url": "https://example.com/borscht"})
    assert r1.json()["source"] == "live"
    r2 = client.post("/api/extract", json={"url": "https://example.com/borscht"})
    assert r2.json()["source"] == "cache"
    assert len(calls) == 1, "fetcher must be called exactly once (cache hit on retry)"


def test_extract_heuristic_page(client):
    client, _ = client
    r = client.post("/api/extract", json={"url": "https://example.com/soup"})
    assert r.status_code == 200
    assert r.json()["recipe"]["title"] == "Simple Tomato Soup"


def test_extract_not_a_recipe_422(client):
    client, _ = client
    r = client.post("/api/extract", json={"url": "https://example.com/about"})
    assert r.status_code == 422
    assert "No recipe found" in r.json()["detail"]


def test_extract_unknown_url_502(client):
    client, _ = client
    r = client.post("/api/extract", json={"url": "https://unknown.example/x"})
    assert r.status_code == 502


def test_save_list_get_delete_cycle(client):
    client, _ = client
    r = client.post("/api/recipes", json={"url": "https://example.com/pancakes"})
    assert r.status_code == 200
    rid = r.json()["id"]
    assert r.json()["recipe"]["title"] == "Quick Pancakes"

    listing = client.get("/api/recipes").json()["recipes"]
    assert [x["id"] for x in listing] == [rid]
    assert listing[0]["title"] == "Quick Pancakes"

    item = client.get(f"/api/recipes/{rid}").json()
    assert item["recipe"]["ingredients"] == ["2 eggs", "250 ml milk", "150 g flour"]

    page = client.get(f"/print/{rid}")
    assert page.status_code == 200
    assert "Quick Pancakes" in page.text
    assert "2 eggs" in page.text

    assert client.delete(f"/api/recipes/{rid}").status_code == 200
    assert client.get(f"/api/recipes/{rid}").status_code == 404
    assert client.get("/api/recipes").json()["recipes"] == []


def test_index_page_served(client):
    client, _ = client
    r = client.get("/")
    assert r.status_code == 200
    assert "Recipe Distiller" in r.text


def test_db_persists_across_connections(tmp_path):
    import os
    os.environ["RECIPE_DB"] = str(tmp_path / "p.db")
    conn = db.connect()
    rid = db.save_recipe(conn, "https://x/1", {"title": "T", "ingredients": ["a"]})
    conn.close()
    conn2 = db.connect()
    assert db.get_saved(conn2, rid)["recipe"]["title"] == "T"
