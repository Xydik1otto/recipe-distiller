"""Substitution hints: swap base + per-ingredient matching, served to the UI."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.substitutions import SUBSTITUTIONS, find_substitutions


def test_base_has_common_swaps():
    assert SUBSTITUTIONS["butter"] and any("margarine" in s for s in SUBSTITUTIONS["butter"])
    assert SUBSTITUTIONS["milk"] and SUBSTITUTIONS["egg"] and SUBSTITUTIONS["sugar"]
    # every entry is a non-empty list of non-empty strings
    for key, subs in SUBSTITUTIONS.items():
        assert key == key.lower().strip()
        assert subs and all(isinstance(s, str) and s.strip() for s in subs)


def test_match_butter_in_line():
    assert any("margarine" in s for s in find_substitutions("1 cup butter, softened"))


def test_match_plural_and_case():
    hits = find_substitutions("2 large Eggs")
    assert any("flax" in s for s in hits)


def test_no_false_positive_on_buttermilk():
    # 'butter' must not match inside 'buttermilk'
    hits = find_substitutions("1 cup buttermilk")
    assert not any("margarine" in s for s in hits)
    assert any("lemon juice" in s for s in hits)


def test_unknown_ingredient_returns_empty():
    assert find_substitutions("3 dragon fruits") == []


def test_api_full_base(client):
    client, _ = client
    r = client.get("/api/substitutions")
    assert r.status_code == 200
    body = r.json()
    assert "butter" in body["substitutions"]
    assert body["substitutions"]["butter"]


def test_api_match_endpoint(client):
    client, _ = client
    r = client.post("/api/substitutions/match",
                    json={"ingredients": ["1 cup butter", "3 dragon fruits"]})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["substitutes"] and items[1]["substitutes"] == []


def test_ui_shows_hints_and_base(client):
    client, _ = client
    page = client.get("/").text
    assert "data-sub=" in page            # per-ingredient hint span
    assert "/api/substitutions/match" in page
    assert 'id="substbase"' in page       # browsable full base
