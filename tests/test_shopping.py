"""Shopping list tests: merging ingredients of multiple recipes."""

from app.shopping import build_shopping_list


def test_merges_same_item_same_unit():
    a = {"ingredients": ["2 cups flour", "1 cup sugar"]}
    b = {"ingredients": ["1 1/2 cups flour", "3 eggs"]}
    result = build_shopping_list([a, b])
    assert result["items"] == ["1 cup sugar", "3 1/2 cups flour", "3 eggs"]
    assert result["unparsed"] == []


def test_same_item_different_units_stay_separate():
    a = {"ingredients": ["500 ml milk"]}
    b = {"ingredients": ["2 cups milk"]}
    result = build_shopping_list([a, b])
    assert result["items"] == ["2 cups milk", "500 ml milk"]


def test_unit_plural_normalization_merges_cup_and_cups():
    result = build_shopping_list([{"ingredients": ["1 cup rice"]},
                                  {"ingredients": ["2 cups rice"]}])
    assert result["items"] == ["3 cups rice"]


def test_unparsed_lines_pass_through_deduplicated():
    a = {"ingredients": ["salt to taste", "pepper to taste"]}
    b = {"ingredients": ["salt to taste", "2 carrots"]}
    result = build_shopping_list([a, b])
    assert result["unparsed"] == ["pepper to taste", "salt to taste"]
    assert result["items"] == ["2 carrots"]


def test_fraction_and_decimal_amounts_merge_correctly():
    result = build_shopping_list([
        {"ingredients": ["1/2 cup butter", "0.5 kg onions"]},
        {"ingredients": ["½ cup butter", "1,5 kg onions"]}])
    assert result["items"] == ["1 cup butter", "2 kg onions"]  # 0.5 + 1.5


def test_api_shopping_list_over_saved_recipes(client):
    client, _ = client
    a = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    b = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    r = client.post("/api/shopping-list", json={"recipe_ids": [a, b]})
    assert r.status_code == 200
    body = r.json()
    assert body["missing_ids"] == []
    # borscht has '200 ml sour cream', pancakes '250 ml milk' — different items, no merge
    assert any("sour cream" in i for i in body["items"])
    assert any("milk" in i for i in body["items"])


def test_api_shopping_list_missing_ids_reported(client):
    client, _ = client
    a = client.post("/api/recipes", json={"url": "https://example.com/borscht"}).json()["id"]
    r = client.post("/api/shopping-list", json={"recipe_ids": [a, 777]})
    assert r.json()["missing_ids"] == [777]
    assert len(r.json()["items"]) == 3


def test_api_shopping_list_empty(client):
    client, _ = client
    r = client.post("/api/shopping-list", json={"recipe_ids": []})
    assert r.status_code == 200
    assert r.json() == {"items": [], "unparsed": [], "missing_ids": []}
