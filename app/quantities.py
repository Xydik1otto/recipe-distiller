"""Ingredient amount parsing: '1/2 cup', '½', '0.5' -> normalized quantities.

Normal forms used across the app:
- a quantity is always a float (1/2, ½ and 0.5 all become 0.5);
- display goes back through format_qty() as a clean fraction ('1/2', '1 1/2');
- parse_ingredient() splits a line into qty / unit / name so servings scaling
  and the shopping list can recompute amounts.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

_VULGAR: Dict[str, str] = {
    "¼": "1/4", "½": "1/2", "¾": "3/4", "⅓": "1/3", "⅔": "2/3",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5", "⅙": "1/6",
    "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8",
}

_AMOUNT_RE = re.compile(
    r"""^\s*
    (?:
      (?P<whole>\d+)\s+(?P<num>\d+)\s*/\s*(?P<den>\d+)   # 1 1/2
    | (?P<num2>\d+)\s*/\s*(?P<den2>\d+)                  # 1/2
    | (?P<dec>\d+(?:[.,]\d+)?)                           # 0.5 / 1,5 / 2
    | (?P<vulgar>[¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])                     # ½
    )
    \s*(?P<rest>.*)$""",
    re.VERBOSE,
)

_UNITS = {
    "cup", "cups", "tbsp", "tablespoon", "tablespoons", "tsp", "teaspoon",
    "teaspoons", "g", "gr", "gram", "grams", "kg", "ml", "l", "litre",
    "litres", "liter", "liters", "oz", "ounce", "ounces", "lb", "lbs",
    "pound", "pounds", "pcs", "piece", "pieces", "clove", "cloves",
    "pinch", "pinches", "pack", "packs", "can", "cans", "bunch", "bunches",
}


def parse_amount(text: str) -> Optional[Dict]:
    """Leading amount of a string -> {'qty': float, 'rest': str} or None."""
    m = _AMOUNT_RE.match(str(text or ""))
    if not m:
        return None
    if m.group("vulgar"):
        num, den = _VULGAR[m.group("vulgar")].split("/")
        qty = int(num) / int(den)
    elif m.group("whole") is not None:
        qty = int(m.group("whole")) + int(m.group("num")) / int(m.group("den"))
    elif m.group("num2") is not None:
        qty = int(m.group("num2")) / int(m.group("den2"))
    else:
        qty = float(m.group("dec").replace(",", "."))
    return {"qty": qty, "rest": (m.group("rest") or "").strip()}


def format_qty(qty: float) -> str:
    """Float -> friendly display: 2.0 -> '2', 1.5 -> '1 1/2', 0.75 -> '3/4'."""
    if qty >= 100:
        return str(int(round(qty)))
    for den in (1, 2, 3, 4, 6, 8):
        scaled = qty * den
        if abs(scaled - round(scaled)) < 1e-9:
            n = int(round(scaled))
            whole, rem = divmod(n, den)
            if rem == 0:
                return str(whole) if whole else "0"
            if whole:
                return f"{whole} {rem}/{den}"
            return f"{rem}/{den}"
    return f"{qty:.2f}".rstrip("0").rstrip(".")


def parse_ingredient(text: str) -> Dict:
    """'1/2 cup sugar' -> {'qty': 0.5, 'unit': 'cup', 'name': 'sugar'}.

    Unparsable lines ('salt to taste') get qty=None and the full text as name.
    """
    text = normalize_ingredient(text)
    amount = parse_amount(text)
    if not amount:
        return {"qty": None, "unit": "", "name": re.sub(r"\s+", " ", text).strip()}
    rest = amount["rest"]
    first, _, tail = rest.partition(" ")
    unit, name = (first.lower(), tail) if first.lower() in _UNITS else ("", rest)
    return {"qty": round(amount["qty"], 4), "unit": unit,
            "name": re.sub(r"\s+", " ", name).strip(" ,")}


def normalize_ingredient(text: str) -> str:
    """Unicode fractions and decimal commas -> plain 'n/d' / 'n.d' text."""
    out = str(text or "")
    for ch, frac in _VULGAR.items():
        out = out.replace(ch, frac)
    out = re.sub(r"(\d),(\d)", r"\1.\2", out)   # 1,5 -> 1.5
    return re.sub(r"\s+", " ", out).strip()


_PLURALIZABLE = {"cup", "tablespoon", "teaspoon", "gram", "pound", "ounce",
                 "clove", "can", "pack", "bunch", "piece", "pinch",
                 "litre", "liter"}


def scale_ingredient(text: str, factor: float) -> str:
    """'1 1/2 cups flour' scaled x2 -> '3 cups flour'. Unparsable lines pass through."""
    amount = parse_amount(text)
    if not amount or not factor:
        return normalize_ingredient(text)
    rest = amount["rest"]
    first, _, tail = rest.partition(" ")
    if first.lower() in _UNITS:
        unit = first.lower()
        if amount["qty"] * factor > 1 and unit in _PLURALIZABLE:
            unit += "s"
        rest = f"{unit} {tail}".strip()
    return f"{format_qty(amount['qty'] * factor)} {rest}".strip()


def parse_servings(text) -> Optional[float]:
    """'6 servings' / 'Serves 4-6' -> 6.0; None when there is no number."""
    if text is None:
        return None
    if isinstance(text, dict) or isinstance(text, list):
        text = str(text)
    m = re.search(r"\d+(?:[.,]\d+)?", str(text))
    return float(m.group(0).replace(",", ".")) if m else None


def scale_recipe(recipe: Dict, servings: Optional[float] = None,
                 factor: Optional[float] = None) -> Optional[Dict]:
    """Copy of the recipe with every ingredient amount scaled.

    Give either an explicit factor, or target servings together with a recipe
    whose 'servings' contains a base number ('6 servings' -> base 6).
    Returns None when the factor cannot be determined.
    """
    if factor is None:
        base = parse_servings(recipe.get("servings"))
        if base is None or not servings:
            return None
        factor = float(servings) / base
    if not factor or factor <= 0:
        return None
    out = dict(recipe)
    out["ingredients"] = [scale_ingredient(i, factor)
                          for i in recipe.get("ingredients") or []]
    parsed = recipe.get("ingredients_parsed")
    if parsed:
        out["ingredients_parsed"] = [
            dict(p, qty=(round(p["qty"] * factor, 4)
                         if p.get("qty") is not None else None))
            for p in parsed]
    if servings is not None:
        out["servings"] = f"{format_qty(float(servings))} servings"
    out["scaled_by"] = round(factor, 4)
    return out
