"""Approximate nutrition estimate from ingredient lines.

Deliberately rough (±20-30%): keyword → per-100g table, amounts converted
to grams with generic unit weights plus a few per-food cup densities.
Good enough for 'is this a light lunch or a holiday dinner', not for
medical use.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .quantities import parse_amount, parse_ingredient

# (kcal, protein g, fat g, carbs g) per 100 g of the edible food.
PER_100G: Dict[str, Tuple[float, float, float, float]] = {
    "chicken": (165, 31, 3.6, 0),
    "beef": (250, 26, 15, 0),
    "pork": (242, 27, 14, 0),
    "bacon": (541, 37, 42, 1.4),
    "sausage": (301, 12, 27, 2),
    "fish": (128, 20, 5, 0),
    "salmon": (208, 20, 13, 0),
    "shrimp": (99, 24, 0.3, 0.2),
    "egg": (155, 13, 11, 1.1),
    "milk": (61, 3.2, 3.3, 4.8),
    "cream": (340, 2.1, 36, 2.8),
    "sour cream": (198, 2.4, 19, 4.5),
    "yogurt": (61, 3.5, 3.3, 4.7),
    "cheese": (356, 23, 28, 2.4),
    "butter": (717, 0.9, 81, 0.1),
    "oil": (884, 0, 100, 0),
    "mayonnaise": (680, 1, 75, 0.6),
    "flour": (364, 10, 1, 76),
    "bread": (265, 9, 3.2, 49),
    "rice": (358, 7.2, 0.8, 79),
    "pasta": (371, 13, 1.5, 75),
    "noodle": (358, 10, 1.4, 74),
    "potato": (77, 2, 0.1, 17),
    "beet": (43, 1.6, 0.2, 10),
    "cabbage": (25, 1.3, 0.1, 5.8),
    "carrot": (41, 0.9, 0.2, 10),
    "onion": (40, 1.1, 0.1, 9.3),
    "garlic": (149, 6.4, 0.5, 33),
    "tomato": (18, 0.9, 0.2, 3.9),
    "cucumber": (15, 0.7, 0.1, 3.6),
    "pepper": (31, 1, 0.3, 7.3),          # bell pepper; black pepper is ~0 g used
    "mushroom": (22, 3.1, 0.3, 3.3),
    "apple": (52, 0.3, 0.2, 14),
    "banana": (89, 1.1, 0.3, 23),
    "lemon": (29, 1.1, 0.3, 9.3),
    "berries": (57, 0.7, 0.3, 14),
    "sugar": (387, 0, 0, 100),
    "honey": (304, 0.3, 0, 82),
    "chocolate": (546, 4.9, 31, 61),
    "nuts": (607, 20, 54, 14),
    "beans": (132, 8.7, 0.5, 23),
    "lentils": (116, 9, 0.4, 20),
    "broth": (10, 1, 0.4, 0.7),
    "stock": (10, 1, 0.4, 0.7),
    "tofu": (76, 8, 4.8, 1.9),
}

# Cup grams differ wildly by food; override the generic 150 g when it matters.
CUP_GRAMS = {
    "flour": 120, "sugar": 200, "butter": 227, "milk": 240, "cream": 240,
    "rice": 185, "nuts": 130, "berries": 145, "cheese": 113,
}

# Generic unit → grams (fallback when the food has no cup override).
UNIT_GRAMS = {
    "g": 1, "gr": 1, "gram": 1, "grams": 1, "kg": 1000,
    "ml": 1, "l": 1000, "litre": 1000, "litres": 1000,
    "liter": 1000, "liters": 1000,
    "oz": 28, "ounce": 28, "ounces": 28, "lb": 454, "lbs": 454,
    "pound": 454, "pounds": 454,
    "tbsp": 15, "tablespoon": 15, "tablespoons": 15,
    "tsp": 5, "teaspoon": 5, "teaspoons": 5,
    "clove": 3, "cloves": 3, "cans": 400, "can": 400,
    "piece": 100, "pieces": 100, "pcs": 100,
    "pinch": 0.3, "pinches": 0.3, "pack": 200, "packs": 200,
    "bunch": 100, "bunches": 100,
}
ITEM_GRAMS = {"egg": 50, "banana": 120, "beet": 110,
              "potato": 160, "onion": 110, "carrot": 80, "tomato": 120}


def _grams(qty: float, unit: str, name: str) -> Optional[float]:
    """Best-effort amount → grams; None when there is no clue at all."""
    if not unit:
        n = _stem(name.split()[-1].lower()) if name.split() else ""
        grams = ITEM_GRAMS.get(n)
        return qty * grams if grams is not None else None
    if unit in ("cup", "cups"):
        for food, grams in CUP_GRAMS.items():
            if re.search(rf"\b{re.escape(food)}", name.lower()):
                return qty * grams
        return qty * 150
    g = UNIT_GRAMS.get(unit)
    return qty * g if g is not None else None


def _stem(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _food(name: str) -> Optional[Tuple[str, Tuple[float, float, float, float]]]:
    words = [_stem(w) for w in re.findall(r"[a-z]+", name.lower())]
    # longest keyword first so 'sour cream' beats 'cream'; stem both sides so
    # '2 eggs' still matches the 'egg' row
    for key in sorted(PER_100G, key=len, reverse=True):
        kwords = [_stem(w) for w in key.split()]
        n = len(kwords)
        for i in range(len(words) - n + 1):
            if words[i:i + n] == kwords:
                return key, PER_100G[key]
    return None


def estimate(recipe: Dict) -> Dict:
    """Approximate nutrition for a recipe dict (kcal + macros + per serving)."""
    kcal = fat = protein = carbs = 0.0
    unknown: List[str] = []
    lines = recipe.get("ingredients") or []
    for line in lines:
        parsed = parse_ingredient(str(line))
        found = _food(parsed["name"] or str(line))
        if not found:
            unknown.append(str(line))
            continue
        grams = _grams(parsed["qty"], parsed["unit"] or "", parsed["name"] or "")
        if grams is None:
            # no amount: assume one generic item of the food (100 g)
            grams = 100.0
        f = found[1]
        kcal += f[0] * grams / 100
        protein += f[1] * grams / 100
        fat += f[2] * grams / 100
        carbs += f[3] * grams / 100
    servings = None
    m = parse_amount(str(recipe.get("servings") or ""))
    if m and m["qty"] > 0:
        servings = m["qty"]
    per_serving = round(kcal / servings) if servings else None
    return {"kcal": round(kcal), "protein_g": round(protein),
            "fat_g": round(fat), "carbs_g": round(carbs),
            "per_serving": per_serving, "coverage": round(1 - len(unknown) / len(lines), 2) if lines else 0.0,
            "unknown": unknown}
