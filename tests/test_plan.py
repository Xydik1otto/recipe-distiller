"""Meal plan tests: 7 slots, drag-backend (PUT slot), plan shopping list."""

from app import db


def test_get_plan_returns_seven_empty_slots(client):
    client, _ = client
    slots = client.get("/api/plan").json()["slots"]
    assert len(slots) == 7
    assert all(s["recipe_id"] is None and s["title"] is None for s in slots)
    assert [s["slot"] for s in slots] == list(range(7))


def test_put_slot_then_plan_contains_title(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    r = client.put("/api/plan", json={"slot": 3, "recipe_id": rid})
    assert r.status_code == 200
    slots = client.get("/api/plan").json()["slots"]
    assert slots[3]["recipe_id"] == rid
    assert slots[3]["title"] == "Grandma's Borscht"
    assert slots[0]["recipe_id"] is None


def test_clear_slot_and_replace(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    rid2 = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    client.put("/api/plan", json={"slot": 0, "recipe_id": rid})
    client.put("/api/plan", json={"slot": 0, "recipe_id": rid2})  # replace
    slots = client.get("/api/plan").json()["slots"]
    assert slots[0]["recipe_id"] == rid2
    client.put("/api/plan", json={"slot": 0, "recipe_id": None})  # clear
    assert client.get("/api/plan").json()["slots"][0]["recipe_id"] is None


def test_put_slot_validation(client):
    client, _ = client
    assert client.put("/api/plan", json={"slot": 7, "recipe_id": None}).status_code == 422
    assert client.put("/api/plan", json={"slot": -1, "recipe_id": None}).status_code == 422
    assert client.put("/api/plan", json={"slot": 2, "recipe_id": 9999}).status_code == 404


def test_plan_shopping_list_merges_slotted_recipes(client):
    client, _ = client
    a = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    b = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    client.put("/api/plan", json={"slot": 0, "recipe_id": a})
    client.put("/api/plan", json={"slot": 4, "recipe_id": b})
    r = client.get("/api/plan/shopping-list")
    body = r.json()
    assert body["slots_used"] == 2
    assert any("sour cream" in i for i in body["items"])
    assert any("milk" in i for i in body["items"])


def test_plan_shopping_list_empty_plan(client):
    client, _ = client
    body = client.get("/api/plan/shopping-list").json()
    assert body == {"items": [], "unparsed": [], "slots_used": 0}


def test_plan_drops_entry_when_recipe_deleted(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    client.put("/api/plan", json={"slot": 1, "recipe_id": rid})
    client.delete(f"/api/recipes/{rid}")
    assert client.get("/api/plan").json()["slots"][1]["recipe_id"] is None


def test_plan_survives_reconnect(tmp_path):
    import os
    os.environ["RECIPE_DB"] = str(tmp_path / "plan.db")
    conn = db.connect()
    rid = db.save_recipe(conn, "https://x/1", {"title": "T"})
    db.set_plan_slot(conn, 5, rid)
    conn.close()
    conn2 = db.connect()
    assert db.get_plan(conn2)[5]["recipe_id"] == rid
