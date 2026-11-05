"""Fraction / amount parsing tests: '1/2 cup', '½', '0.5' -> normalized qty."""

from app.quantities import (format_qty, normalize_ingredient, parse_amount,
                            parse_ingredient, parse_servings, scale_ingredient)


def test_parse_amount_fractions_decimals_vulgar():
    assert parse_amount("1/2 cup sugar") == {"qty": 0.5, "rest": "cup sugar"}
    assert parse_amount("½ tsp salt") == {"qty": 0.5, "rest": "tsp salt"}
    assert parse_amount("0.5 kg flour") == {"qty": 0.5, "rest": "kg flour"}
    assert parse_amount("1,5 l milk") == {"qty": 1.5, "rest": "l milk"}
    assert parse_amount("1 1/2 cups flour") == {"qty": 1.5, "rest": "cups flour"}
    assert parse_amount("3 beets, grated") == {"qty": 3.0, "rest": "beets, grated"}


def test_parse_amount_rejects_amountless_text():
    assert parse_amount("salt to taste") is None
    assert parse_amount("") is None
    assert parse_amount(None) is None


def test_format_qty_friendly_fractions():
    assert format_qty(2.0) == "2"
    assert format_qty(0.5) == "1/2"
    assert format_qty(0.75) == "3/4"
    assert format_qty(1.5) == "1 1/2"
    assert format_qty(1 / 3) == "1/3"
    assert format_qty(2 / 3) == "2/3"
    assert format_qty(0.335) == "0.34"  # no clean fraction -> decimals


def test_parse_ingredient_splits_qty_unit_name():
    assert parse_ingredient("1/2 cup sugar") == {"qty": 0.5, "unit": "cup", "name": "sugar"}
    assert parse_ingredient("200 ml sour cream") == {"qty": 200.0, "unit": "ml", "name": "sour cream"}
    assert parse_ingredient("3 beets, grated") == {"qty": 3.0, "unit": "", "name": "beets, grated"}
    assert parse_ingredient("salt to taste") == {"qty": None, "unit": "", "name": "salt to taste"}


def test_normalize_ingredient_unicode_and_comma():
    assert normalize_ingredient("½ cup butter") == "1/2 cup butter"
    assert normalize_ingredient("1,5 kg bananas") == "1.5 kg bananas"
    assert normalize_ingredient("  ¾  tsp ") == "3/4 tsp"


def test_scale_ingredient():
    assert scale_ingredient("2 cups flour", 1.5) == "3 cups flour"
    assert scale_ingredient("1/2 cup sugar", 2) == "1 cup sugar"
    assert scale_ingredient("1 1/2 cups flour", 2) == "3 cups flour"
    assert scale_ingredient("½ tsp salt", 3) == "1 1/2 tsp salt"
    assert scale_ingredient("salt to taste", 2) == "salt to taste"
    assert scale_ingredient("3 eggs", 0.5) == "1 1/2 eggs"


def test_parse_servings():
    assert parse_servings("6 servings") == 6.0
    assert parse_servings("Serves 4-6") == 4.0
    assert parse_servings(None) is None
    assert parse_servings("one loaf") is None


def test_extractor_adds_normalized_parsed_ingredients():
    from app.extractor import extract_from_html
    from conftest import load
    recipe = extract_from_html(load("fractions.html"), "https://example.com/banana")
    assert recipe["ingredients"][0] == "1/2 cup butter"       # ½ -> 1/2
    assert recipe["ingredients"][2] == "0.5 tsp baking soda"  # decimal kept
    parsed = recipe["ingredients_parsed"]
    assert parsed[0] == {"qty": 0.5, "unit": "cup", "name": "butter"}
    assert parsed[4] == {"qty": 1.5, "unit": "kg", "name": "bananas"}  # 1,5 -> 1.5
    assert parsed[5]["qty"] is None and parsed[5]["name"] == "salt to taste"


def test_api_extract_includes_parsed_ingredients(client):
    client, _ = client
    r = client.post("/api/extract", json={"url": "https://example.com/banana"})
    assert r.status_code == 200
    assert r.json()["recipe"]["ingredients_parsed"][0]["qty"] == 0.5
