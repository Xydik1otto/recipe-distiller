"""Pantry tests: fridge list storage + cook-what-you-have matching (all offline)."""

from app import db, pantry


def test_set_and_get_pantry_normalises(client):
    client, _ = client
    r = client.put("/api/pantry", json={"items": ["  Beet ", "potato", "beet", ""]})
    assert r.status_code == 200
    assert r.json()["items"] == ["beet", "potato"]   # deduped, lower-case, sorted
    assert client.get("/api/pantry").json()["items"] == ["beet", "potato"]


def test_pantry_persists_across_connections(tmp_path):
    import os
    os.environ["RECIPE_DB"] = str(tmp_path / "p.db")
    conn = db.connect()
    db.set_pantry(conn, ["milk", "eggs"])
    conn.close()
    assert db.get_pantry(db.connect()) == ["eggs", "milk"]


def test_match_full_coverage_means_can_cook():
    recipe = {"ingredients": ["2 beets", "3 potatoes", "salt to taste"]}
    report = pantry.match_recipe(recipe, ["beet", "potato"])
    assert report["can_cook"] is True
    assert report["coverage"] == 1.0
    assert report["missing"] == []


def test_match_reports_missing_ingredients():
    recipe = {"ingredients": ["2 beets", "300 g beef", "sour cream"]}
    report = pantry.match_recipe(recipe, ["beets"])
    assert report["can_cook"] is False
    assert any("beef" in m for m in report["missing"])
    assert any("sour cream" in m for m in report["missing"])
    assert 0 < report["coverage"] < 1


def test_staples_never_missing():
    recipe = {"ingredients": ["1 tsp salt", "2 cups water", "1 onion"]}
    report = pantry.match_recipe(recipe, ["onion"])
    assert report["can_cook"] is True   # salt+water are staples, onion is in pantry


def test_word_boundary_matching():
    # 'beet' must not satisfy 'beetroot sugar' — no substring matches
    report = pantry.match_recipe({"ingredients": ["beetroot sugar"]}, ["beet"])
    assert report["can_cook"] is False
    assert pantry.match_recipe({"ingredients": ["1 cup beets"]}, ["beet"])["can_cook"]


def test_empty_recipe_and_empty_pantry():
    assert pantry.match_recipe({"ingredients": []}, [])["coverage"] == 0.0
    report = pantry.match_recipe({"ingredients": ["1 onion"]}, [])
    assert report["can_cook"] is False


def test_api_match_sorted_by_coverage(client):
    client, _ = client
    borscht = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()
    pancakes = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()
    client.put("/api/pantry", json={"items": ["beet", "potato", "cabbage", "butter", "eggs", "milk", "flour"]})
    body = client.get("/api/pantry/match").json()
    assert body["pantry"][0] == "beet"
    by_id = {m["id"]: m for m in body["matches"]}
    # pancakes: eggs + milk + flour are all in the pantry → cookable now
    assert by_id[pancakes["id"]]["can_cook"] is True
    assert by_id[pancakes["id"]]["missing"] == []
    # borscht needs beef/broth/etc. that the pantry lacks
    assert by_id[borscht["id"]]["can_cook"] is False
    assert by_id[borscht["id"]]["missing"]
    coverages = [m["coverage"] for m in body["matches"]]
    assert coverages == sorted(coverages, reverse=True)


def test_api_match_after_delete_and_empty_pantry(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    client.delete(f"/api/recipes/{rid}")
    body = client.get("/api/pantry/match").json()
    assert body["matches"] == []
    assert body["pantry"] == []
