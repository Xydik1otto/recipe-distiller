"""Extraction pipeline: HTML -> clean recipe dict.

Priority order:
1. JSON-LD (schema.org/Recipe) — most reliable.
2. Microdata (itemscope/itemprop).
3. Heuristics — ul/ol lists near the words "Ingredients" / "Instructions".
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1")
DESKTOP_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

_H_DUR = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?$", re.I)


def _parse_duration(value) -> Optional[str]:
    """ISO-8601 duration ('PT1H30M') or plain text -> '1 hr 30 min'."""
    if not value:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
        if not value:
            return None
    if isinstance(value, dict):
        value = value.get("name") or ""
    text = str(value)
    m = _H_DUR.search(text)
    if m:
        h, mi = int(m.group(1) or 0), int(m.group(2) or 0)
        parts = []
        if h:
            parts.append(f"{h} hr")
        if mi:
            parts.append(f"{mi} min")
        return " ".join(parts) or None
    return text.strip() or None


def _clean_list(items) -> List[str]:
    out: List[str] = []
    for item in items or []:
        if isinstance(item, dict):
            item = item.get("name") or item.get("text") or ""
        if isinstance(item, list):  # HowToStep / HowToSection nesting
            item = " ".join(_clean_list(item))
        text = re.sub(r"\s+", " ", str(item)).strip()
        if text:
            out.append(text)
    return out


def _find_recipe_node(data):
    """Recursively find a schema.org/Recipe node in parsed JSON-LD."""
    if isinstance(data, list):
        for item in data:
            found = _find_recipe_node(item)
            if found is not None:
                return found
        return None
    if isinstance(data, dict):
        types = data.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if any(t.lower() == "recipe" for t in types or []):
            return data
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in data:
                found = _find_recipe_node(data[key])
                if found is not None:
                    return found
    return None


def extract_jsonld(soup: BeautifulSoup) -> Optional[Dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text() or "")
        except (json.JSONDecodeError, ValueError):
            continue
        node = _find_recipe_node(data)
        if node:
            title = node.get("name")
            if isinstance(title, list):
                title = title[0] if title else None
            return {
                "title": (title or "").strip() or None,
                "servings": (str(node.get("recipeYield") or node.get("yield") or "").strip() or None),
                "prep_time": _parse_duration(node.get("prepTime")),
                "cook_time": _parse_duration(node.get("cookTime")),
                "total_time": _parse_duration(node.get("totalTime")),
                "ingredients": _clean_list(
                    node.get("recipeIngredient") or node.get("ingredients")),
                "steps": _clean_list(
                    node.get("recipeInstructions") or node.get("instructions")),
            }
    return None


def _microdata_texts(soup: BeautifulSoup, prop: str) -> List[str]:
    out = []
    for el in soup.find_all(attrs={"itemprop": prop}):
        if el.name in ("meta",):
            val = el.get("content", "")
        elif el.name in ("time",):
            val = el.get("datetime") or el.get_text(" ", strip=True)
        else:
            val = el.get_text(" ", strip=True)
        if val:
            out.append(val)
    return out


def extract_microdata(soup: BeautifulSoup) -> Optional[Dict]:
    scope = soup.find(attrs={"itemtype": re.compile(r"schema\.org/Recipe", re.I)})
    if not scope:
        return None
    root = scope
    # itemprop values may live in nested scopes; search the whole doc but the
    # Recipe scope is the common case — search within it, falling back to doc.
    def _find(prop):
        vals = _microdata_texts(root, prop)
        return vals or _microdata_texts(soup, prop)

    ingredients = _find("recipeIngredient") or _find("ingredients")
    steps = _find("recipeInstructions") or _find("instructions") or _find("recipeDirections")
    title = _find("name")
    return {
        "title": title[0].strip() if title else None,
        "servings": (_find("recipeYield") or _find("yield") or [None])[0],
        "prep_time": _parse_duration((_find("prepTime") or [None])[0]),
        "cook_time": _parse_duration((_find("cookTime") or [None])[0]),
        "total_time": _parse_duration(_find("totalTime")[0] if _find("totalTime") else None),
        "ingredients": _clean_list(ingredients),
        "steps": _clean_list(steps),
    }


_HEADING_TAGS = ("h1", "h2", "h3", "h4", "strong", "b", "summary")
_INGR_RE = re.compile(r"ingredient", re.I)
_STEPS_RE = re.compile(r"(instruction|direction|method|preparation|steps)", re.I)


def _list_after_heading(heading) -> Optional[List[str]]:
    """First ul/ol following the heading in document order."""
    lst = heading.find_next(["ul", "ol"])
    if lst is None:
        return None
    items = [li.get_text(" ", strip=True) for li in lst.find_all("li")]
    items = [i for i in items if i]
    return items or None


def extract_heuristics(soup: BeautifulSoup) -> Optional[Dict]:
    ingredients: List[str] = []
    steps: List[str] = []
    for h in soup.find_all(_HEADING_TAGS):
        text = h.get_text(" ", strip=True)
        if not text:
            continue
        if not ingredients and _INGR_RE.search(text):
            found = _list_after_heading(h)
            if found and len(found) >= 2:
                ingredients = found
        elif not steps and _STEPS_RE.search(text):
            found = _list_after_heading(h)
            if found and len(found) >= 1:
                steps = found
    if not ingredients and not steps:
        return None
    title_el = soup.find("h1")
    return {
        "title": title_el.get_text(" ", strip=True) if title_el else None,
        "servings": None, "prep_time": None, "cook_time": None, "total_time": None,
        "ingredients": ingredients,
        "steps": steps,
    }


def extract_from_html(html: str, url: str) -> Optional[Dict]:
    """Full pipeline over raw HTML. Returns a clean recipe dict or None."""
    soup = BeautifulSoup(html, "html.parser")
    recipe = extract_jsonld(soup)  # JSON-LD first, while <script> tags still exist
    # strip noise (ads, nav, analytics) before microdata/heuristics parsing
    for tag in soup(["script", "style", "noscript", "aside", "nav", "footer", "form"]):
        tag.decompose()
    if not recipe or not (recipe["ingredients"] or recipe["steps"]):
        recipe = extract_microdata(soup) or None
    if not recipe or not (recipe["ingredients"] or recipe["steps"]):
        recipe = extract_heuristics(soup)
    if not recipe:
        return None
    recipe.setdefault("canonical_url", url)
    # drop empty fields for a clean payload
    return {k: v for k, v in recipe.items() if v}
