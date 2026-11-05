"""Unit conversion cups→ml→g for typical ingredients."""

import pytest

from app.convert import annotate_ingredient, convert_ingredient, density_of


def test_cup_to_ml_and_grams():
    assert convert_ingredient("2 cups flour") == "≈ 480 ml · ≈ 240 g"
    assert convert_ingredient("1/2 cup sugar") == "≈ 120 ml · ≈ 100 g"


def test_specific_ingredient_wins_over_generic():
    # 'brown sugar' (1.1 cup-weight) must not match plain 'sugar' density
    assert convert_ingredient("1 cup brown sugar") == "≈ 240 ml · ≈ 220 g"


def test_grams_to_ml():
    assert convert_ingredient("200 g butter") == "≈ 211 ml"


def test_ml_and_litres_do_not_double_convert():
    assert convert_ingredient("250 ml milk") == "≈ 258 g"
    assert convert_ingredient("1 l water") == "≈ 1000 g"


def test_unknown_ingredient_returns_none():
    assert convert_ingredient("2 eggs") is None
    assert convert_ingredient("salt to taste") is None


def test_annotate_appends_parenthesis():
    assert annotate_ingredient("1 cup butter") == "1 cup butter (≈ 240 ml · ≈ 227 g)"
    assert annotate_ingredient("3 beets, grated") == "3 beets, grated"


def test_fractions_and_vulgars_convert():
    out = convert_ingredient("½ cup honey")
    assert out == "≈ 120 ml · ≈ 170 g"


def test_density_lookup_most_specific():
    assert density_of("whole wheat flour") == pytest.approx(130 / 240)
    assert density_of("anything") is None


def test_api_convert_endpoint(client):
    client, _ = client
    r = client.post("/api/convert",
                    json={"ingredients": ["2 cups flour", "1 tsp salt", "2 eggs"]})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["converted"] == "≈ 480 ml · ≈ 240 g"
    assert "≈ 6 g" in items[1]["converted"]          # 1 tsp fine salt ≈ 5.7 g
    assert items[2]["converted"] is None


def test_print_view_shows_conversions(client):
    client, _ = client
    rid = client.post("/api/recipes", json={"url": "https://example.com/pancakes"}).json()["id"]
    page = client.get(f"/print/{rid}")
    assert page.status_code == 200
    assert "≈" in page.text          # some ingredient got a conversion annotation
