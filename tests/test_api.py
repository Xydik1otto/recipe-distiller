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


def _save_two(client):
    a = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    b = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    return a, b


def test_search_by_title_and_ingredient(client):
    client, _ = client
    _save_two(client)
    by_title = client.get("/api/recipes", params={"q": "borscht"}).json()["recipes"]
    assert [r["title"] for r in by_title] == ["Grandma's Borscht"]
    by_ingredient = client.get("/api/recipes", params={"q": "eggs"}).json()["recipes"]
    assert [r["title"] for r in by_ingredient] == ["Quick Pancakes"]
    assert client.get("/api/recipes", params={"q": "zzz-none"}).json()["recipes"] == []


def test_tags_set_filter_and_exported(client):
    client, _ = client
    a, b = _save_two(client)
    r = client.put(f"/api/recipes/{a}/tags", json={"tags": ["soup", "winter", "soup"]})
    assert r.status_code == 200 and r.json()["tags"] == ["soup", "winter"]
    assert client.put("/api/recipes/9999/tags", json={"tags": ["x"]}).status_code == 404
    tagged = client.get("/api/recipes", params={"tag": "soup"}).json()["recipes"]
    assert [x["id"] for x in tagged] == [a]
    assert b not in [x["id"] for x in tagged]
    export = client.get("/api/recipes/export").json()
    soup_item = next(x for x in export["recipes"] if x["recipe"].get("title"))
    assert any(x["tags"] == ["soup", "winter"] for x in export["recipes"])


def test_export_import_roundtrip(client):
    client, _ = client
    a, b = _save_two(client)
    client.put(f"/api/recipes/{a}/tags", json={"tags": ["soup"]})
    export = client.get("/api/recipes/export").json()
    assert len(export["recipes"]) == 2
    # wipe and restore
    for i in (a, b):
        client.delete(f"/api/recipes/{i}")
    assert client.get("/api/recipes").json()["recipes"] == []
    r = client.post("/api/recipes/import", json=export)
    assert r.status_code == 200 and r.json()["imported"] == 2
    back = client.get("/api/recipes").json()["recipes"]
    titles = {x["title"] for x in back}
    assert titles == {"Grandma's Borscht", "Quick Pancakes"}
    tagged = client.get("/api/recipes", params={"tag": "soup"}).json()["recipes"]
    assert len(tagged) == 1
    full = client.get(f"/api/recipes/{tagged[0]['id']}").json()
    assert "beets" in full["recipe"]["ingredients"][0]


def test_import_accepts_bare_list_and_skips_junk(client):
    client, _ = client
    items = [
        {"url": "https://example.com/borscht", "recipe": {"title": "Borscht", "ingredients": ["3 beets"]}},
        {"garbage": True},
        "not-a-dict",
    ]
    r = client.post("/api/recipes/import", json=items)
    assert r.status_code == 200 and r.json()["imported"] == 1
    assert len(client.get("/api/recipes").json()["recipes"]) == 1


def test_import_rejects_bad_shape(client):
    client, _ = client
    r = client.post("/api/recipes/import", json={"nope": 1})
    assert r.status_code == 422
