# 🍲 Recipe Distiller — «Just the recipe»

![tests](https://github.com/bigpi/recipe-distiller/actions/workflows/tests.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.12+-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![version](https://img.shields.io/badge/version-1.0.0-orange)

URL → clean recipe. No ads, no 1,200 words about someone's childhood, no popups.

> Українська версія: **[README.md](README.md)**

## Why this exists

> "I just wanted a recipe. Instead I got 2,000 words about how this recipe
> reminds me of my grandmother's summers in Tuscany…"
> — a typical post from r/mildlyinfuriating, tens of thousands of upvotes

This isn't one complaint — it's a systemic pain: "I just wanted a recipe 😫"
posts regularly blow up on r/mildlyinfuriating and r/webdev, the existing
service justtherecipe.food proved the demand (people will use even a bare-bones
tool just to get "only the recipe"), and an analysis of 9,363 posts confirms a
stable anti-bloat trend — users increasingly demand clean content. Recipe
Distiller is the local answer to this pain: your own server, your own recipes,
zero ads.

## The problem

Recipe sites have become SEO junkyards: to learn 6 ingredients you must scroll
through "grandma's story", 14 ad blocks and a newsletter popup. This is mass
frustration (see above).

## How it works — 3-tier pipeline

```
                    ┌─────────────────────────────┐
   URL ──httpx──▶   │  fetch: retries + mobile UA │
                    └──────────────┬──────────────┘
                                   ▼
        ┌──────────────────────────────────────────────────┐
        │  TIER 1  JSON-LD  <script type="application/ld+  │  ← most reliable
        │          json"> schema.org/Recipe (@graph too)   │
        ├──────────────────────────────────────────────────┤
        │  TIER 2  Microdata  itemscope / itemprop         │  ← fallback
        ├──────────────────────────────────────────────────┤
        │  TIER 3  Heuristics: ul/ol near "Ingredients" /  │  ← last resort
        │          "Instructions" headings                 │
        └──────────────────────────────────────────────────┘
```

## Quick start

```bash
git clone https://github.com/bigpi/recipe-distiller.git
cd recipe-distiller
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://127.0.0.1:8000

pytest                               # tests run offline on fixed HTML fixtures
bash scripts/smoke.sh                # smoke: boots a server, checks key endpoints
```

Step-by-step install for non-programmers (Windows `start.bat`, Linux systemd
unit, updates): **[INSTALL.md](INSTALL.md)**.

## Browser extension (MV3)

`extension/` is an unpacked Manifest V3 extension: click the toolbar button on
any recipe page and the distiller opens with that URL, extracting immediately.
Install: `chrome://extensions` → Developer mode → **Load unpacked** → pick
`extension/`. Details: [extension/README.md](extension/README.md).

## Features

- **Extraction pipeline**: JSON-LD (with `@graph`, nested HowToSection/HowToStep)
  → microdata → heuristics; quantity normalisation (`½`, `1/2`, `0.5` → parsed qty).
- **Recipe book**: search by title/ingredients, tags, favourites ♥ + 5-star
  ratings, sort by newness/rating/title, one-click **JSON + CSV export**,
  JSON import (deletion asks for confirmation).
- **Substitution hints**: a base of common swaps (butter↔margarine,
  egg→flax egg, buttermilk→milk+lemon…) shown per ingredient and browsable in the UI.
- **Unit conversion**: cups→ml→g annotations for typical ingredients.
- **Serving scaling**, **merged shopping list** (across recipes and the weekly
  plan), **printable shopping list** and a print-friendly recipe view.
- **Weekly meal plan** (7 slots) with drag & drop.
- **First-run experience**: an opt-in banner loads 3 demo recipes so you can try
  everything without scraping a real site.
- **UI in Ukrainian and English** (browser-language auto-detect, persisted
  choice; no other locales by design).
- **PWA offline**: the service worker caches the app shell and your saved book.
- **a11y**: aria-labels on interactive elements, visible focus outline, keyboard
  friendly.
- Bookmarklet, 24h extraction cache, 143 tests — all offline, no network.

## API

| Method | Path | What it does |
|---|---|---|
| POST | `/api/extract` `{url}` | fetch + extract a recipe (24h SQLite cache) |
| POST | `/api/recipes` `{url}` | extract and save to the book |
| GET | `/api/recipes?q=&tag=` | list; search by title/ingredients, tag filter |
| GET | `/api/recipes?favorite=1&sort=rating\|title\|new` | favourites-only filter, sort by rating/title/newness |
| PUT | `/api/recipes/{id}/rating` `{favorite?, rating?}` | favourite ♥ + 5-star rating |
| POST | `/api/convert` `{ingredients: []}` | cups→ml→g hints for typical ingredients |
| GET | `/api/substitutions` | the substitution base (butter↔margarine etc.) |
| POST | `/api/substitutions/match` `{ingredients: []}` | per-line substitution hints |
| PUT | `/api/recipes/{id}/tags` `{tags: []}` | set tags |
| GET | `/api/recipes/export` | export everything as JSON |
| GET | `/api/recipes/export.csv` | export everything as CSV |
| POST | `/api/recipes/import` | import from the export format |
| POST | `/api/demo` | first-run: add 3 demo recipes (opt-in, idempotent) |
| POST | `/api/scale` `{recipe, servings\|factor}` | rescale quantities |
| POST | `/api/recipes/{id}/scale` `{servings}` | scale a saved recipe |
| POST | `/api/shopping-list` `{recipe_ids: []}` | merge ingredients across recipes |
| GET | `/api/plan` | weekly plan (7 slots, Mon–Sun) |
| PUT | `/api/plan` `{slot, recipe_id\|null}` | assign/clear a slot |
| GET | `/api/plan/shopping-list` | shopping list generated from the plan |
| GET | `/bookmarklet` | bookmarklet button page (drag) |
| GET | `/api/recipes/{id}` | one saved recipe |
| DELETE | `/api/recipes/{id}` | delete |
| GET | `/print/{id}` | printable view |
| GET | `/` | web UI: URL field → recipe card → Save |
| GET | `/i18n.js` | UA/EN dictionaries (UI language switch) |

## Contributing

Bugs, ideas, PRs are welcome: **[CONTRIBUTING.md](CONTRIBUTING.md)**.
Security issues — **[SECURITY.md](SECURITY.md)** (please don't open a public
issue for vulnerabilities).

## License

[MIT](LICENSE) © bigpi
