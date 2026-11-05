"""First-run demo: 3 ready-made recipes loaded on opt-in, so a new user can try
the distiller, shopping list and meal plan without scraping any real site."""

from __future__ import annotations

from typing import Dict, List

DEMO_RECIPES: List[Dict] = [
    {
        "url": "https://demo.local/borscht",
        "title": "Demo: Ukrainian borscht",
        "recipe": {
            "title": "Ukrainian borscht",
            "servings": "6 servings",
            "total_time": "1 hour 30 minutes",
            "ingredients": [
                "2 beets, grated",
                "3 potatoes, diced",
                "1 onion, chopped",
                "2 carrots, grated",
                "4 cups vegetable broth",
                "2 tbsp tomato paste",
                "1 cup shredded cabbage",
                "3 cloves garlic",
                "2 tbsp butter",
                "1 tbsp lemon juice",
                "sour cream and dill, to serve",
            ],
            "steps": [
                "Simmer the beets in broth for 20 minutes.",
                "Add potatoes, onion and carrots; cook 15 more minutes.",
                "Stir in cabbage, tomato paste and garlic; simmer 10 minutes.",
                "Finish with lemon juice; serve with sour cream and dill.",
            ],
        },
    },
    {
        "url": "https://demo.local/banana-bread",
        "title": "Demo: banana bread",
        "recipe": {
            "title": "Banana bread",
            "servings": "8 slices",
            "total_time": "1 hour 10 minutes",
            "ingredients": [
                "3 ripe bananas, mashed",
                "1/3 cup butter, melted",
                "3/4 cup sugar",
                "1 egg, beaten",
                "1 tsp vanilla extract",
                "1 tsp baking soda",
                "1 1/2 cups all-purpose flour",
                "1/2 cup chocolate chips",
            ],
            "steps": [
                "Mash the bananas and mix in butter, sugar and egg.",
                "Stir in flour, baking soda and vanilla; fold in the chips.",
                "Pour into a loaf pan and bake at 175°C for 60 minutes.",
            ],
        },
    },
    {
        "url": "https://demo.local/shakshuka",
        "title": "Demo: shakshuka",
        "recipe": {
            "title": "Shakshuka",
            "servings": "2 servings",
            "total_time": "30 minutes",
            "ingredients": [
                "2 tbsp olive oil",
                "1 onion, sliced",
                "3 cloves garlic, minced",
                "1 red bell pepper, sliced",
                "1 can (400 g) crushed tomatoes",
                "1 tsp paprika",
                "4 eggs",
                "100 g feta, crumbled",
                "bread, to serve",
            ],
            "steps": [
                "Soften the onion, garlic and pepper in olive oil.",
                "Add tomatoes and paprika; simmer 10 minutes.",
                "Crack in the eggs, cover and cook until the whites set.",
                "Top with feta and serve with bread.",
            ],
        },
    },
]


def load_demo(conn) -> int:
    """Insert demo recipes whose URLs are not in the book yet; returns added count."""
    from . import db
    added = 0
    existing = {row["url"] for row in
                conn.execute("SELECT url FROM saved").fetchall()}
    for demo in DEMO_RECIPES:
        if demo["url"] in existing:
            continue
        db.save_recipe(conn, demo["url"], demo["recipe"])
        added += 1
    return added
