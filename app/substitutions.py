"""Substitution hints: a small base of common ingredient swaps (butter↔margarine…).

Kept dependency-free and data-driven: each canonical ingredient maps to a list
of ready substitutes (with ratios where it matters). Matching is word-based,
so 'butter' never matches inside 'buttermilk'.
"""

from __future__ import annotations

import re
from typing import Dict, List

# canonical ingredient -> ready substitutes (ratio in parentheses when ≠ 1:1)
SUBSTITUTIONS: Dict[str, List[str]] = {
    "butter": ["margarine (1:1)", "coconut oil (1:1)", "olive oil (use ¾ of the amount)"],
    "margarine": ["butter (1:1)"],
    "shortening": ["butter (1:1)", "coconut oil (1:1)"],
    "milk": ["any plant milk (1:1)", "water + a knob of butter (per cup)"],
    "buttermilk": ["milk + 1 tbsp lemon juice or vinegar per cup (rest 5 min)"],
    "heavy cream": ["milk + 2 tbsp melted butter per cup", "coconut cream (1:1)"],
    "whipping cream": ["milk + 2 tbsp melted butter per cup"],
    "sour cream": ["plain yogurt (1:1)", "cottage cheese blended smooth"],
    "yogurt": ["sour cream (1:1)", "buttermilk (1:1)"],
    "cream cheese": ["cottage cheese blended smooth", "ricotta (1:1)"],
    "ricotta": ["cottage cheese (1:1)"],
    "cottage cheese": ["ricotta (1:1)"],
    "egg": ["1 tbsp ground flax + 3 tbsp water (baking)", "¼ cup applesauce (baking)"],
    "flour": ["spelt flour (1:1)", "gluten-free blend (check the bag)"],
    "all-purpose flour": ["bread flour (slightly chewier result)"],
    "bread flour": ["all-purpose flour (slightly softer result)"],
    "whole wheat flour": ["all-purpose flour (softer, less nutty)"],
    "cornstarch": ["potato starch (1:1)", "flour (use 2× the amount)"],
    "sugar": ["honey (use ¾ of the amount, reduce liquid)", "maple syrup (use ¾ of the amount)"],
    "brown sugar": ["white sugar + a splash of molasses", "coconut sugar (1:1)"],
    "powdered sugar": ["blended white sugar (1 cup sugar = 1¾ cup powder)"],
    "honey": ["maple syrup (1:1)", "agave syrup (1:1)"],
    "maple syrup": ["honey (1:1)"],
    "molasses": ["honey or dark corn syrup (1:1)"],
    "soy sauce": ["tamari (gluten-free, 1:1)", "salt + a splash of water"],
    "lemon juice": ["lime juice (1:1)", "white vinegar (½ the amount)"],
    "vinegar": ["lemon juice (1:1)"],
    "baking powder": ["¼ tsp baking soda + ½ tsp cream of tartar per 1 tsp"],
    "baking soda": ["baking powder (use 3× the amount, drop the salt)"],
    "yeast": ["sourdough starter (adjust flour and liquid)"],
    "vanilla extract": ["vanilla sugar (1:1)", "a splash of almond extract (stronger)"],
    "chocolate": ["cocoa powder + butter (3 tbsp cocoa + 1 tbsp butter per 30 g)"],
    "cocoa powder": ["carob powder (1:1)"],
    "tomato paste": ["ketchup (1:1, sweeter)", "tomato purée reduced by simmering"],
    "onion": ["shallot (1:1)", "onion powder (1 tbsp powder = 1 medium onion)"],
    "garlic": ["garlic powder (¼ tsp powder = 1 clove)"],
    "chicken broth": ["vegetable broth (1:1)", "bouillon cube + water"],
    "vegetable broth": ["chicken broth (1:1, not vegetarian)", "bouillon cube + water"],
    "white wine": ["chicken or vegetable broth + a squeeze of lemon"],
    "red wine": ["beef broth + a splash of balsamic vinegar"],
    "mayonnaise": ["plain yogurt (1:1)", "sour cream (1:1)"],
    "mustard": ["dijon ↔ yellow mustard (1:1, milder)"],
    "breadcrumbs": ["crushed crackers", "rolled oats (softer crust)"],
    "rolled oats": ["quinoa flakes (1:1)"],
    "rice": ["quinoa (1:1)", "bulgur (1:1)"],
    "quinoa": ["rice (1:1)"],
    "pasta": ["any short pasta shape of similar size"],
}

# match key in a line: word boundary, optional plural -s/-es, case-insensitive
_PATTERN = re.compile(
    "|".join(r"\b" + re.escape(k) + r"(?:es|s)?\b" for k in sorted(SUBSTITUTIONS, key=len, reverse=True)),
    re.IGNORECASE,
)


def find_substitutions(line: str) -> List[str]:
    """Substitutes for every known ingredient mentioned in the line ('1 cup butter' → …)."""
    seen: List[str] = []
    for match in _PATTERN.finditer(line or ""):
        key = re.sub(r"(?:es|s)$", "", match.group(0).lower())
        for sub in SUBSTITUTIONS.get(key, []):
            if sub not in seen:
                seen.append(sub)
    return seen
