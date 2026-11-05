"""Serving scaling tests: servings xN -> recalculated ingredient quantities."""

from app.quantities import scale_recipe


def test_scale_recipe_by_factor():
    recipe = {"servings": "6 servings",
              "ingredients": ["2 cups flour", "1/2 cup sugar", "3 eggs", "salt to taste"],
              "ingredients_parsed": [
                  {"qty": 2.0, "unit": "cups", "name": "flour"},
                  {"qty": 0.5, "unit": "cup", "name": "sugar"},
                  {"qty": 3.0, "unit": "", "name": "eggs"},
                  {"qty": None, "unit": "", "name": "salt to taste"}]}
    scaled = scale_recipe(recipe, factor=1.5)
    assert scaled["ingredients"] == ["3 cups flour", "3/4 cup sugar",
                                     "4 1/2 eggs", "salt to taste"]
    assert scaled["ingredients_parsed"][1]["qty"] == 0.75
    assert scaled["ingredients_parsed"][3]["qty"] is None
    assert scaled["scaled_by"] == 1.5
    assert scaled["servings"] == "6 servings"  # untouched when only a factor is given


def test_scale_recipe_by_target_servings():
    recipe = {"servings": "4 servings", "ingredients": ["250 ml milk"]}
    scaled = scale_recipe(recipe, servings=10)
    assert scaled["servings"] == "10 servings"
    assert scaled["ingredients"] == ["625 ml milk"]  # 250 * 2.5
    assert scaled["scaled_by"] == 2.5


def test_scale_recipe_down_and_original_untouched():
    recipe = {"servings": "8 servings", "ingredients": ["1 1/2 cups rice"]}
    scaled = scale_recipe(recipe, servings=2)
    assert scaled["ingredients"] == ["3/8 cups rice"]
    assert recipe["ingredients"] == ["1 1/2 cups rice"], "input must not be mutated"


def test_scale_recipe_impossible_cases_return_none():
    assert scale_recipe({"ingredients": ["1 cup"]}, servings=4) is None  # no base servings
    assert scale_recipe({"servings": "one loaf", "ingredients": []}, servings=4) is None
    assert scale_recipe({"servings": "4", "ingredients": []}, servings=0) is None
    assert scale_recipe({"servings": "4", "ingredients": []}, factor=0) is None


def test_api_scale_by_servings(client):
    client, _ = client
    r = client.post("/api/scale", json={
        "recipe": {"servings": "2 servings", "ingredients": ["1 cup rice", "1/2 tsp salt"]},
        "servings": 6})
    assert r.status_code == 200
    recipe = r.json()["recipe"]
    assert recipe["ingredients"] == ["3 cups rice", "1 1/2 tsp salt"]
    assert recipe["servings"] == "6 servings"


def test_api_scale_saved_recipe(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    r = client.post(f"/api/recipes/{rid}/scale", json={"servings": 12})  # base 6
    assert r.status_code == 200
    assert r.json()["recipe"]["ingredients"][0] == "6 beets, grated"
    assert client.post("/api/recipes/9999/scale", json={"servings": 4}).status_code == 404


def test_api_scale_422_when_no_base(client):
    client, _ = client
    r = client.post("/api/scale", json={"recipe": {"ingredients": ["1 cup"]}, "servings": 4})
    assert r.status_code == 422
    assert "Cannot scale" in r.json()["detail"]
