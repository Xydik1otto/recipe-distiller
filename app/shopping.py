"""Shopping list: merge ingredients of several recipes into one list.

Same item with the same unit gets its quantities summed ('1 cup flour' +
'2 cups flour' -> '3 cups flour'); lines without a parseable amount are
passed through verbatim (deduplicated).
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from .quantities import format_qty, parse_ingredient

_PLURAL_TO_SINGULAR = {
    "cups": "cup", "tablespoons": "tablespoon", "teaspoons": "teaspoon",
    "grams": "gram", "pounds": "pound", "ounces": "ounce", "cloves": "clove",
    "cans": "can", "packs": "pack", "bunches": "bunch", "pieces": "piece",
    "pinches": "pinch", "litres": "litre",
}
_SINGULAR_TO_PLURAL = {v: k for k, v in _PLURAL_TO_SINGULAR.items()}


def _unit_key(unit: str) -> str:
    return _PLURAL_TO_SINGULAR.get(unit, unit)


def _name_key(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[.,;:]+$", "", name.strip().lower()))


def _display_unit(unit: str, qty: float) -> str:
    if qty > 1 and unit in _SINGULAR_TO_PLURAL:
        return _SINGULAR_TO_PLURAL[unit]
    return unit


def build_shopping_list(recipes: Iterable[Dict]) -> Dict:
    """Combined list over any number of recipe dicts."""
    totals: Dict[Tuple[str, str, str], float] = {}   # (unit_key, display_unit, name) -> qty
    unparsed: List[str] = []
    seen_unparsed = set()
    for recipe in recipes:
        for line in recipe.get("ingredients") or []:
            parsed = parse_ingredient(str(line))
            if parsed["qty"] is None:
                text = parsed["name"]
                key = _name_key(text)
                if text and key not in seen_unparsed:
                    seen_unparsed.add(key)
                    unparsed.append(text)
                continue
            unit = parsed["unit"] or ""
            name = parsed["name"]
            if not name:
                continue
            key = (_unit_key(unit), _name_key(name))
            if key in totals:
                totals[key][0] += parsed["qty"]
            else:
                totals[key] = [parsed["qty"], unit, name]
    items = [" ".join(filter(None, (format_qty(round(v[0], 4)),
                                    _display_unit(v[1], v[0]), v[2])))
             for v in totals.values()]
    return {"items": sorted(items), "unparsed": sorted(unparsed)}
