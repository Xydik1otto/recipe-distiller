"""Bulk import from multiple URLs: per-URL results, partial failures isolated."""

FIXTURE_URLS = ["https://example.com/borscht", "https://example.com/pancakes",
                "https://example.com/soup"]


def test_bulk_import_saves_all(client):
    client, calls = client
    r = client.post("/api/recipes/import-urls", json={"urls": FIXTURE_URLS})
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 3 and body["failed"] == 0
    assert all(res["ok"] for res in body["results"])
    titles = {res["title"] for res in body["results"]}
    assert titles == {"Grandma's Borscht", "Quick Pancakes", "Simple Tomato Soup"}
    assert len(client.get("/api/recipes").json()["recipes"]) == 3


def test_bulk_import_partial_failure(client):
    client, _ = client
    urls = ["https://example.com/borscht", "https://unknown.example/x",
            "https://example.com/about"]  # ok, fetch error, not-a-recipe
    body = client.post("/api/recipes/import-urls", json={"urls": urls}).json()
    assert body["imported"] == 1 and body["failed"] == 2
    results = body["results"]
    assert results[0]["ok"] is True
    assert results[1]["ok"] is False and "failed to fetch" in results[1]["error"]
    assert results[2]["ok"] is False and "No recipe found" in results[2]["error"]
    # the good URL was still saved — partial failure loses nothing else
    listing = client.get("/api/recipes").json()["recipes"]
    assert [x["title"] for x in listing] == ["Grandma's Borscht"]


def test_bulk_import_validation(client):
    client, _ = client
    assert client.post("/api/recipes/import-urls", json={"urls": []}).status_code == 422
    assert client.post("/api/recipes/import-urls",
                       json={"urls": ["https://example.com/x"] * 26}).status_code == 422
    assert client.post("/api/recipes/import-urls",
                       json={"urls": ["not a url"]}).status_code == 422


def test_bulk_import_is_repeatable(client):
    client, _ = client
    for _ in range(2):
        client.post("/api/recipes/import-urls", json={"urls": ["https://example.com/cake"]})
    assert len(client.get("/api/recipes").json()["recipes"]) == 2
