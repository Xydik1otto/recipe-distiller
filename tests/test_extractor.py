"""Extraction pipeline tests against fixed HTML fixtures."""

from app.extractor import (_parse_duration, extract_from_html, extract_heuristics,
                           extract_jsonld, extract_microdata)
from bs4 import BeautifulSoup

from conftest import load


def test_jsonld_full_recipe():
    recipe = extract_from_html(load("jsonld.html"), "https://example.com/borscht")
    assert recipe["title"] == "Grandma's Borscht"
    assert recipe["servings"] == "6 servings"
    assert recipe["prep_time"] == "20 min"
    assert recipe["cook_time"] == "1 hr"
    assert recipe["total_time"] == "1 hr 20 min"
    assert recipe["ingredients"] == ["3 beets, grated", "1 kg cabbage, shredded",
                                     "200 ml sour cream"]
    assert recipe["steps"] == ["Grate the beets.", "Shred the cabbage.",
                               "Simmer everything for one hour."]
    assert recipe["canonical_url"] == "https://example.com/borscht"


def test_jsonld_found_inside_at_graph():
    soup = BeautifulSoup(load("jsonld.html"), "html.parser")
    node = extract_jsonld(soup)
    assert node is not None and node["title"] == "Grandma's Borscht"


def test_jsonld_output_is_cleaned_no_bloat():
    recipe = extract_from_html(load("jsonld.html"), "https://example.com/borscht")
    text = str(recipe)
    # no life-story / ad text leaks into the clean payload
    assert "childhood" not in text
    assert "BUY KNIVES" not in text
    assert "newsletter" not in text.lower()


def test_microdata_recipe():
    recipe = extract_from_html(load("microdata.html"), "https://example.com/pancakes")
    assert recipe["title"] == "Quick Pancakes"
    assert recipe["servings"] == "4 pancakes"
    assert recipe["prep_time"] == "10 min"
    assert recipe["cook_time"] == "15 min"
    assert recipe["ingredients"] == ["2 eggs", "250 ml milk", "150 g flour"]
    assert len(recipe["steps"]) == 3


def test_microdata_extractor_direct():
    soup = BeautifulSoup(load("microdata.html"), "html.parser")
    recipe = extract_microdata(soup)
    assert recipe is not None and recipe["title"] == "Quick Pancakes"


def test_heuristic_fallback():
    recipe = extract_from_html(load("heuristic.html"), "https://example.com/soup")
    assert recipe["title"] == "Simple Tomato Soup"
    assert recipe["ingredients"] == ["1 kg ripe tomatoes", "1 onion",
                                     "2 cloves garlic", "500 ml vegetable stock"]
    assert recipe["steps"] == ["Chop the onion and garlic.",
                               "Saute until soft, add tomatoes and stock.",
                               "Simmer 30 minutes, blend, season."]


def test_heuristic_no_structured_data_direct():
    soup = BeautifulSoup(load("heuristic.html"), "html.parser")
    recipe = extract_heuristics(soup)
    assert recipe is not None and len(recipe["ingredients"]) == 4


def test_not_a_recipe_returns_none():
    assert extract_from_html(load("not_a_recipe.html"), "https://example.com/about") is None


def test_duration_parsing():
    assert _parse_duration("PT1H30M") == "1 hr 30 min"
    assert _parse_duration("PT45M") == "45 min"
    assert _parse_duration("PT2H") == "2 hr"
    assert _parse_duration("about 40 minutes") == "about 40 minutes"
    assert _parse_duration(None) is None


def test_priority_jsonld_wins_over_heuristics():
    """Page has both JSON-LD and heuristic lists — JSON-LD payload must win."""
    recipe = extract_from_html(load("jsonld.html"), "https://example.com/borscht")
    assert "beets" in recipe["ingredients"][0]
