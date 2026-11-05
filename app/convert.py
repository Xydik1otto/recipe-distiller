"""Unit conversion: cups→ml→g for typical ingredients.

Volume units are exact (1 cup = 240 ml, 1 tbsp = 15 ml, 1 tsp = 5 ml).
Weight needs density, so only a lookup table of common baking ingredients
(flour, sugar, butter, milk…) is converted: '1/2 cup flour' -> '≈ 60 g'.
Everything else passes through untouched — a wrong guess is worse than
no conversion.
"""

from __future__ import annotations

from typing import Dict, Optional

from .quantities import format_qty, parse_ingredient

VOLUME_ML: Dict[str, float] = {
    "cup": 240.0, "cups": 240.0, "tbsp": 15.0, "tablespoon": 15.0,
    "tablespoons": 15.0, "tsp": 5.0, "teaspoon": 5.0, "teaspoons": 5.0,
    "ml": 1.0, "l": 1000.0, "litre": 1000.0, "litres": 1000.0,
    "liter": 1000.0, "liters": 1000.0,
}

WEIGHT_G: Dict[str, float] = {
    "g": 1.0, "gr": 1.0, "gram": 1.0, "grams": 1.0, "kg": 1000.0,
    "oz": 28.35, "ounce": 28.35, "ounces": 28.35,
    "lb": 453.6, "lbs": 453.6, "pound": 453.6, "pounds": 453.6,
}

# grams per millilitre; longest key wins so 'brown sugar' beats 'sugar'
DENSITY: Dict[str, float] = {
    "flour": 120 / 240,          # all-purpose, spoon-and-level
    "bread flour": 130 / 240,
    "whole wheat flour": 130 / 240,
    "sugar": 200 / 240,          # granulated
    "brown sugar": 220 / 240,    # packed
    "powdered sugar": 120 / 240,
    "butter": 227 / 240,
    "margarine": 225 / 240,
    "milk": 1.03,
    "cream": 1.0,
    "water": 1.0,
    "oil": 218 / 240,            # vegetable / olive
    "honey": 1.42,
    "syrup": 1.33,
    "cocoa": 100 / 240,          # unsweetened powder
    "salt": 273 / 240,           # fine table salt
    "rice": 200 / 240,
    "oats": 90 / 240,            # rolled
    "baking powder": 0.9,
    "baking soda": 0.9,
    "yeast": 0.65,               # dry active
}


def density_of(name: str) -> Optional[float]:
    """Ingredient name -> g/ml, most specific match wins."""
    text = f" {str(name or '').lower()} "
    for key in sorted(DENSITY, key=len, reverse=True):
        if key in text:
            return DENSITY[key]
    return None


def convert_ingredient(text: str) -> Optional[str]:
    """'2 cups flour' -> '≈ 480 ml · ≈ 240 g'; None when nothing to convert.

    Only annotates what is missing: '200 g sugar' shows the ml equivalent,
    '1 cup milk' shows grams, '2 eggs' shows nothing.
    """
    parsed = parse_ingredient(text)
    qty, unit, name = parsed["qty"], parsed["unit"], parsed["name"]
    if qty is None:
        return None
    grams = mls = None
    if unit in VOLUME_ML:
        raw = qty * VOLUME_ML[unit]
        dens = density_of(name)
        if dens:
            grams = raw * dens
        if unit not in ("ml", "l", "litre", "liter", "litres", "liters"):
            mls = raw  # already in ml — nothing to add on that axis
    elif unit in WEIGHT_G:
        raw = qty * WEIGHT_G[unit]
        dens = density_of(name)
        if dens:
            mls = raw / dens
        if unit not in ("g", "gr", "gram", "grams"):
            grams = raw
    parts = []
    if mls is not None:
        parts.append(f"≈ {format_qty(round(mls))} ml")
    if grams is not None:
        parts.append(f"≈ {format_qty(round(grams))} g")
    return " · ".join(parts) if parts else None


def annotate_ingredient(text: str) -> str:
    """Original line with the conversion appended: '1/2 cup flour (≈ 60 g · ≈ 120 ml)'."""
    extra = convert_ingredient(text)
    return f"{text} ({extra})" if extra else text
