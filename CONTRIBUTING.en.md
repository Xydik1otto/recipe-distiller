# 🤝 Contributing to Recipe Distiller

Thanks for your interest! The project is small and local-first — all help is
welcome. This document explains how the code is organized, how to run and test
it, and walks step by step through the two most common kinds of contribution:
**adding a source site** and **adding a unit of measure**.

## What this project is

Recipe Distiller is a self-hosted web app (FastAPI + Vanilla JS) that
"distills" any recipe page into a clean card: title, time, servings,
ingredients with normalized amounts, and steps. Recipes can then be scaled to
a different serving count, converted between units, merged into a shopping
list, a weekly meal plan, and print view. Alongside it live a browser
extension (bookmarklet + WebExtension) and a mobile port (a separate branch,
see below).

## Architecture: how the logic works

### 3-tier extraction pipeline (`app/extractor.py`)

The single entry point is `extract_from_html(html, url)`. It tries three tiers
in order and stops at the first one that produced ingredients or steps:

1. **JSON-LD** (`<script type="application/ld+json">`, schema.org/Recipe) —
   the most reliable tier. The parser recursively finds a `Recipe` node even
   inside `@graph`/`mainEntity`/`itemListElement`, understands `HowToStep` and
   nested `HowToSection` ("For the dough" → the section's steps), and converts
   ISO-8601 durations (`PT1H30M` → `1 hr 30 min`). All `<script>` tags are
   removed from the tree before microdata/heuristics parsing — which is why
   JSON-LD is always tried first.
2. **Microdata** (`itemscope`/`itemprop`, schema.org/Recipe) — the fallback
   when JSON-LD is missing or empty. Reads `itemprop="recipeIngredient"`,
   `recipeInstructions`, `name`, `recipeYield`, `prepTime`… (values come from
   `content`/`datetime` when the element is `meta`/`time`).
3. **Heuristics** — the last resort for sites without any markup: headings
   (`h1..h4`, `strong`, `b`, `summary`) containing the words "ingredient" /
   "instruction|direction|method|preparation|steps", and the first `ul`/`ol`
   after such a heading. This tier yields no servings or time.

Before tiers 2–3 the page is stripped of noise (`script`, `style`, `noscript`,
`aside`, `nav`, `footer`, `form`) — ads and life stories never reach the clean
payload. The result goes through `_augment_ingredients`: every ingredient line
is normalized and parsed into the `ingredients_parsed` structure.

### Quantities and fractions (`app/quantities.py`)

- `parse_amount()` understands `1 1/2`, `1/2`, `0.5`, `1,5` and unicode
  fractions (`½` → `1/2`). A quantity is always stored as a float.
- `format_qty()` is the reverse, for display: `2.0` → `2`, `1.5` → `1 1/2`,
  `0.75` → `3/4`.
- `parse_ingredient()` splits a line into `qty` / `unit` / `name`; lines
  without an amount ("salt to taste") pass through as-is.
- `scale_ingredient()` / `scale_recipe()` — scaling to servings (from
  `servings` or an explicit factor), with correct singular/plural forms
  (`1 cup` → `3 cups`).

### Unit conversion (`app/convert.py`)

- Volume is exact: `1 cup = 240 ml`, `1 tbsp = 15 ml`, `1 tsp = 5 ml`.
- Weight needs density, so only a lookup table of common ingredients
  (`DENSITY`, grams per ml: flour, sugar, butter, milk…) is converted. The
  longest match wins: `brown sugar` beats `sugar`.
- `convert_ingredient()` only annotates what is missing: `200 g sugar` shows
  the ml equivalent, `1 cup milk` shows grams, `2 eggs` shows nothing. A wrong
  guess is worse than no conversion, so unknown ingredients are left untouched.

### Shopping list (`app/shopping.py`)

`build_shopping_list()` merges ingredients from any number of recipes: the
same item with the same unit (singular = plural, `cups` = `cup`) is summed
(`1 cup flour` + `2 cups flour` → `3 cups flour`); lines without an amount
pass through verbatim and are deduplicated.

### Weekly meal plan (`meal_plan`)

The `meal_plan` table in SQLite: 7 slots (slot 0 = Monday), each holding a
reference to a saved recipe. The `GET/PUT /api/plan` and
`GET /api/plan/shopping-list` endpoints build the week's shopping list from
the plan.

### SQLite book (`app/db.py`)

Two stores in one file (the path is set via `RECIPE_DB`, a local SQLite file
by default): `cache` (URL → extracted recipe, 24h TTL) and `saved` (your
personal recipe book with ratings, favorites and tags). Migrations are
idempotent (`ALTER TABLE ... ADD COLUMN` when a column is missing).

## Environment and tests

```bash
pip install -e ".[dev]"
pytest
```

**Tests are fully offline.** The network is never called: `fetch_html` is
mocked with fixtures. HTML fixtures live in `tests/fixtures/` — they are
*real, reduced HTML* of actual pages (`jsonld.html`, `microdata.html`,
`heuristic.html`, `fractions.html`, `not_a_recipe.html`), and the conftest
`tests/conftest.py` maps fake URLs (`https://example.com/borscht` etc.) onto
those files. Fixtures deliberately contain "dirt" — ads, navigation, life
stories — to verify the extractor never lets it through.

## HOW TO ADD A SOURCE SITE

If a specific site parses poorly (empty card, garbage in ingredients, lost
steps) — work step by step, from the bottom of the pipeline up:

1. **Save the real HTML.** Open the problem page in a browser, `Ctrl+U` (or
   Save Page), and save the *full* HTML. Turn it into a fixture — small but
   truthful: real tags and structure, extra paragraphs and ads stay (they are
   part of the test), personal data goes. Put the file in
   `tests/fixtures/<site-name>.html`.
2. **Check JSON-LD.** Search the HTML for
   `<script type="application/ld+json">` and the word `"Recipe"`. If the node
   is there but the parser loses something (nested sections, `HowToSection`,
   unusual fields) — fix the parser in `extract_jsonld()` /
   `_parse_instructions()`, not the data. Most large sites have JSON-LD —
   often all you need is to add a fixture and a test; the code doesn't change
   at all.
3. **No JSON-LD — check microdata.** Search for
   `itemtype="...schema.org/Recipe"` and `itemprop="recipeIngredient"`. If
   microdata exists but is imprecise — patch `extract_microdata()` /
   `_microdata_texts()` (e.g. a new element type or attribute).
4. **Nothing at all — heuristics.** The site then parses via the third tier.
   Check whether `_INGR_RE`/`_STEPS_RE` find the section headings on this site
   (maybe it says "Інгредієнти" / "Zutaten" — extend the regexes carefully and
   only when needed). Change the "list after heading" logic only as a last
   resort — it is shared by all markup-free sites.
5. **Add a test.** In `tests/test_extractor.py` (or a separate file) — a test
   that `extract_from_html(load("your-file.html"), "https://...")` yields the
   expected `title`, `ingredients`, `steps`. If the site should work through
   `/api/extract`, add the URL → fixture mapping to `tests/conftest.py` and a
   test via `client`.
6. **Make sure nothing leaks.** The payload must not contain ad/article text —
   see `test_jsonld_output_is_cleaned_no_bloat` as the example.

A minimal test example:

```python
def test_new_site():
    recipe = extract_from_html(load("new_site.html"), "https://new.example/recipe")
    assert recipe["title"] == "..."
    assert "2 cups flour" in recipe["ingredients"]
```

## HOW TO ADD A UNIT OF MEASURE

1. Add the new unit to `_UNITS` in `app/quantities.py` (so the parser
   recognizes it after the amount). If the unit has singular/plural forms,
   also add it to `_PLURALIZABLE` (same file) and to the `_PLURAL_TO_SINGULAR`
   / `_SINGULAR_TO_PLURAL` tables in `app/shopping.py` (so the shopping list
   merges `1 cup` and `2 cups` correctly).
2. If it is a **volume** unit — add the exact factor to `VOLUME_ML` in
   `app/convert.py`. If it is a **weight** unit — to `WEIGHT_G`.
3. If the unit needs a **density** to convert to grams/millilitres — add the
   ingredient (not the unit!) to the `DENSITY` table in `app/convert.py` as
   `grams / 240` for measuring cups or `g/ml` for liquids, e.g.:

   ```python
   "semolina": 160 / 240,   # 160 g per 240 ml cup
   ```

   The longest key wins, so specific names (`brown sugar`) are listed before
   short ones (`sugar`). If you don't know the density — **don't add** the
   entry: a wrong conversion is worse than none; the ingredient simply passes
   without annotation.
4. Add cases to `tests/test_convert.py` (and `tests/test_quantities.py` if you
   touched the parser): verify both the conversion and that an unknown
   ingredient with the same unit stays unannotated.

## Branches

- **`master`** — the stable branch: server + extension + tests. All new work
  targets it.
- **`mobile/android-ios`** — the mobile port (Capacitor Android/iOS shells
  around the same server, CI builds of the APK/.app). Mobile work happens in
  that branch; it periodically re-integrates changes from `master`.

## Pull requests and commits

- Fork → branch `feature/<something>` → PR. One PR — one logical change.
- **Every feature comes with a test.** A PR without a test won't be merged.
- Small commits, clear messages in the `feat:` / `fix:` / `docs:` style
  (see `git log` — messages are detailed and explain *what* and *why*).
- Before a PR: `pytest` fully green; don't touch other people's fixtures
  without need.

## i18n: Ukrainian and English

The UI has two languages — Ukrainian and English (strings in
`static/i18n.js`). New UI strings are added in both languages at once. **No
Russian localization** — a deliberate project decision; such PRs will be
declined. A proofread of the English strings in `static/i18n.js` is also a
welcome contribution.

## Mobile port and extension development

- **Mobile** (`mobile/android-ios`): Capacitor shells in `mobile/` +
  `capacitor.config.ts`; the native projects are generated (`npx cap add
  android` / `ios`). Make UI/server-logic changes in `master` — the shells
  merely wrap the same web app; the server address is entered in settings.
  Build/install details are in `MOBILE.md` on that branch.
- **Extension** (`extension/`): WebExtension + bookmarklet. No hardcoded URLs
  beyond the configurable localhost; permissions are minimal (see
  `SECURITY.md`: SSRF/XSS/injection/extension permissions are the security
  boundary).

## Bug reports and ideas

Open an Issue using the templates (`.github/ISSUE_TEMPLATE/`), in Ukrainian or
English. For parsing problems include: the site URL, what you expected, what
you got, and — if you can — a snippet of the HTML with JSON-LD/microdata (that
alone almost always shrinks the fix to one commit).

If you're looking for a task: parsing complex sites (TIER-3 heuristics), new
substitution pairs (`app/substitutions.py`), densities for `DENSITY`,
proofreading `static/i18n.js`.

## License

By contributing you agree your changes are released under the project's MIT
license (see `LICENSE`).
