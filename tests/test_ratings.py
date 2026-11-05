"""Favorites + 5-star ratings: migration, rating endpoint, filters and sorting."""

import pytest

from app import db


def _save_two(client):
    a = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    b = client.post("/api/recipes", json={"url": "https://example.com/cake"}).json()["id"]
    return a, b


def test_new_columns_have_defaults(client):
    client, _ = client
    a, b = _save_two(client)
    listing = client.get("/api/recipes").json()["recipes"]
    for item in listing:
        assert item["favorite"] is False
        assert item["rating"] == 0


def test_set_favorite_and_rating(client):
    client, _ = client
    a, _ = _save_two(client)
    r = client.put(f"/api/recipes/{a}/rating", json={"favorite": True, "rating": 4})
    assert r.status_code == 200
    assert r.json() == {"id": a, "favorite": True, "rating": 4}
    item = client.get(f"/api/recipes/{a}").json()
    assert item["favorite"] is True and item["rating"] == 4


def test_rating_validation_and_404(client):
    client, _ = client
    _save_two(client)
    assert client.put("/api/recipes/1/rating", json={"rating": 6}).status_code == 422
    assert client.put("/api/recipes/1/rating", json={"rating": -1}).status_code == 422
    assert client.put("/api/recipes/999/rating", json={"rating": 3}).status_code == 404
    # empty payload on an existing recipe is a no-op that still answers 200
    assert client.put("/api/recipes/1/rating", json={}).status_code == 200


def test_clear_rating_with_zero(client):
    client, _ = client
    a, _ = _save_two(client)
    client.put(f"/api/recipes/{a}/rating", json={"rating": 5})
    client.put(f"/api/recipes/{a}/rating", json={"rating": 0})
    assert client.get(f"/api/recipes/{a}").json()["rating"] == 0


def test_sort_by_rating(client):
    client, _ = client
    a, b = _save_two(client)
    client.put(f"/api/recipes/{a}/rating", json={"rating": 3})
    client.put(f"/api/recipes/{b}/rating", json={"rating": 5})
    ids = [x["id"] for x in client.get("/api/recipes?sort=rating").json()["recipes"]]
    assert ids == [b, a]
    titles = [x["title"] for x in client.get("/api/recipes?sort=title").json()["recipes"]]
    assert titles == sorted(titles, key=str.lower)


def test_favorites_filter(client):
    client, _ = client
    a, b = _save_two(client)
    client.put(f"/api/recipes/{a}/rating", json={"favorite": True})
    ids = [x["id"] for x in client.get("/api/recipes?favorite=1").json()["recipes"]]
    assert ids == [a]


def test_rating_survives_export_import(client, tmp_path, monkeypatch):
    client, _ = client
    a, _ = _save_two(client)
    client.put(f"/api/recipes/{a}/rating", json={"favorite": True, "rating": 5})
    data = client.get("/api/recipes/export").json()
    # wipe and re-import into the same DB
    conn = db.connect()
    conn.execute("DELETE FROM saved")
    conn.commit()
    n = db.import_recipes(conn, data["recipes"])
    assert n == 2
    new_id = conn.execute("SELECT id FROM saved WHERE url = ?",
                          ("https://example.com/borscht",)).fetchone()[0]
    item = db.get_saved(conn, new_id)
    assert item["favorite"] is True and item["rating"] == 5


def test_older_db_file_is_migrated(tmp_path):
    """A pre-v0.4.0 DB without favorite/rating columns keeps working."""
    import sqlite3
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE saved (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT,
            title TEXT, data TEXT, saved_at REAL, tags TEXT DEFAULT '[]');
    """)
    conn.execute("INSERT INTO saved (url, title, data, saved_at) VALUES (?, ?, ?, ?)",
                 ("https://x", "Old", "{}", 1.0))
    conn.commit()
    conn.close()
    conn = db.connect(str(path))
    assert db.set_rating(conn, 1, favorite=True, rating=5)
    assert db.get_saved(conn, 1)["rating"] == 5
