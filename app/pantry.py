"""Pantry: what's already in the fridge → which saved recipes you can cook now.

Matching is deliberately simple and offline: a pantry item matches an
ingredient line when the item's words appear in the line (case-insensitive,
word boundaries — 'beet' does not match 'beetroot sugar'). Basic staples
(salt, pepper, water, oil) are assumed to be always at home and never
counted as missing.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List

from .quantities import parse_ingredient

# Staples assumed present in every kitchen — never listed as "missing".
STAPLES = {"salt", "pepper", "water", "oil", "sugar", "flour"}
# Filler words that turn a staple into a phrase ("salt to taste").
_FILLERS = {"to", "taste", "fresh", "ground", "chopped", "grated"}


def _stem(word: str) -> str:
    """Crude plural stem applied to both sides: beets/beet, berries/berry."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]          # potatoes → potato, tomatoes → tomato
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _words(text: str) -> List[str]:
    return [_stem(w) for w in re.findall(r"[a-zа-яіїєґ']+", str(text).lower())]


def _line_key(line: str) -> str:
    """'2 cups shredded cabbage' -> 'cups shredded cabbage' (amount dropped)."""
    parsed = parse_ingredient(str(line))
    return parsed["name"] or str(line)


def _matches(line: str, item: str) -> bool:
    """Whole-word containment of the pantry item inside the ingredient line."""
    item_words = _words(item)
    if not item_words:
        return False
    line_words = _words(line)
    n = len(item_words)
    return any(line_words[i:i + n] == item_words
               for i in range(len(line_words) - n + 1))


def _is_staple(line: str) -> bool:
    tokens = _words(_line_key(line))
    return bool(tokens) and all(t in STAPLES or t in _FILLERS for t in tokens)


def match_recipe(recipe: Dict, pantry: Iterable[str]) -> Dict:
    """Coverage report for one recipe against the pantry list."""
    items = [str(p).strip().lower() for p in pantry if str(p).strip()]
    matched, missing = [], []
    for line in recipe.get("ingredients") or []:
        line = str(line)
        if _is_staple(line):
            matched.append(line)  # staple: always available
            continue
        if any(_matches(line, it) for it in items):
            matched.append(line)
        else:
            missing.append(line)
    total = len(matched) + len(missing)
    coverage = round(len(matched) / total, 2) if total else 0.0
    return {"matched": matched, "missing": missing,
            "coverage": coverage, "can_cook": not missing and total > 0}


def match_recipes(recipes: Iterable[Dict], pantry: Iterable[str]) -> List[Dict]:
    """One report per recipe, best coverage first (ties: title A-Z)."""
    pantry = [str(p).strip().lower() for p in pantry if str(p).strip()]
    reports = []
    for recipe in recipes:
        m = match_recipe(recipe["recipe"], pantry)
        reports.append({"id": recipe["id"], "title": recipe["title"],
                        **m})
    reports.sort(key=lambda r: (-r["coverage"], r["title"].lower()))
    return reports
