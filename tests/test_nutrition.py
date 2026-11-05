"""Nutrition estimate tests: per-100g keyword table + gram conversion (offline)."""

from app.nutrition import estimate, _grams, _food


def test_food_lookup_longest_key_wins():
    assert _food("1 cup sour cream")[0] == "sour cream"
    assert _food("2 tbsp butter")[0] == "butter"
    assert _food("a pinch of unicorn dust") is None


def test_grams_direct_mass_units():
    assert _grams(250, "g", "flour") == 250
    assert _grams(0.5, "kg", "potatoes") == 500
    assert _grams(2, "oz", "cheese") == 56


def test_grams_volume_units_with_cup_density():
    assert _grams(1, "cup", "flour") == 120      # density override
    assert _grams(1, "cup", "milk") == 240
    assert _grams(2, "cups", "quinoa") == 300    # generic 150 g fallback
    assert _grams(3, "tbsp", "oil") == 45


def test_grams_piece_items():
    assert _grams(2, "", "eggs") == 100          # ~50 g per egg
    assert _grams(1, "clove", "garlic") == 3
    assert _grams(1, "", "salt") is None

def test_estimate_totals_and_per_serving():
    recipe = {"servings": "2 servings",
              "ingredients": ["300 g chicken", "200 ml cream"]}
    out = estimate(recipe)
    # chicken 300g: 3*165=495 kcal, 93 p; cream 200ml: 2*340=680 kcal, 4.2 p, 72 f
    assert out["kcal"] == 1175
    assert out["per_serving"] == 588
    assert out["protein_g"] == round(93 + 2 * 2.1)
    assert out["coverage"] == 1.0
    assert out["unknown"] == []


def test_estimate_reports_unknown_lines():
    out = estimate({"ingredients": ["2 eggs", "salt to taste", "dragon scales"]})
    assert out["kcal"] == 155                     # 2 × ~50 g eggs → 100 g × 155/100
    assert "dragon scales" in out["unknown"]
    assert "salt to taste" in out["unknown"]      # no food keyword either
    assert out["coverage"] == round(1 - 2 / 3, 2)


def test_estimate_without_servings_has_none_per_serving():
    out = estimate({"ingredients": ["100 g butter"]})
    assert out["per_serving"] is None
    assert out["kcal"] == 717


def test_estimate_empty_recipe():
    out = estimate({})
    assert out["kcal"] == 0 and out["coverage"] == 0.0


def test_api_nutrition_endpoint(client):
    client, _ = client
    r = client.post("/api/nutrition",
                    json={"recipe": {"servings": "4 servings",
                                     "ingredients": ["2 cups milk", "150 g flour"]}})
    assert r.status_code == 200
    body = r.json()
    assert body["kcal"] == round(2 * 240 * 61 / 100 + 1.5 * 364)
    assert body["per_serving"] == round(body["kcal"] / 4)


def test_api_nutrition_for_saved_recipe_and_404(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    body = client.get(f"/api/recipes/{rid}/nutrition").json()
    assert body["kcal"] > 0
    assert client.get("/api/recipes/9999/nutrition").status_code == 404
