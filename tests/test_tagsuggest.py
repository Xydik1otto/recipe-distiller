"""Tag autocomplete: vocabulary + usage counts + prefix suggestions."""

from app import db


def _tag(client, rid, tags):
    assert client.put(f"/api/recipes/{rid}/tags", json={"tags": tags}).status_code == 200


def test_all_tags_counts_and_dedupes(tmp_path):
    import os
    os.environ["RECIPE_DB"] = str(tmp_path / "t.db")
    conn = db.connect()
    a = db.save_recipe(conn, "https://x/1", {"title": "A"})
    b = db.save_recipe(conn, "https://x/2", {"title": "B"})
    db.set_tags(conn, a, ["dinner", "soup"])
    db.set_tags(conn, b, ["Dinner", "fast"])
    tags = db.all_tags(conn)
    conn.close()
    assert tags == [{"tag": "dinner", "count": 2},
                    {"tag": "fast", "count": 1},
                    {"tag": "soup", "count": 1}]


def test_suggest_prefix_filter_case_insensitive(tmp_path):
    import os
    os.environ["RECIPE_DB"] = str(tmp_path / "t.db")
    conn = db.connect()
    rid = db.save_recipe(conn, "https://x/1", {"title": "A"})
    db.set_tags(conn, rid, ["dinner", "Soup", "dessert"])
    filtered = db.all_tags(conn, q="dE")
    all_d = db.all_tags(conn, q="D")
    empty = db.all_tags(conn, q="xyz")
    conn.close()
    assert [t["tag"] for t in filtered] == ["dessert"]       # prefix, not substring
    assert [t["tag"] for t in all_d] == ["dessert", "dinner"]
    assert empty == []


def test_api_suggest_endpoint(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    _tag(client, rid, ["soup", "dinner"])
    rid2 = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    _tag(client, rid2, ["soup", "breakfast"])
    body = client.get("/api/tags/suggest").json()["suggestions"]
    assert body[0] == {"tag": "soup", "count": 2}          # most used first
    assert [t["tag"] for t in client.get("/api/tags/suggest?q=sou").json()["suggestions"]] == ["soup"]
    # empty book → empty vocabulary
    client.delete(f"/api/recipes/{rid}")
    client.delete(f"/api/recipes/{rid2}")
    assert client.get("/api/tags/suggest").json()["suggestions"] == []
