"""FastAPI app: POST /api/extract, recipe book endpoints, single-page UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl

from . import db
from .extractor import extract_from_html
from .fetcher import fetch_html

app = FastAPI(title="Recipe Distiller", version="1.0.0")
# bookmarklet calls the API from any third-party site
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.get("/bookmarklet", response_class=HTMLResponse)
def bookmarklet_page():
    return FileResponse(STATIC_DIR / "bookmarklet.html")


@app.get("/sw.js", response_class=FileResponse,
         responses={200: {"content": {"application/javascript": {}}}})
def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/i18n.js", response_class=FileResponse,
         responses={200: {"content": {"application/javascript": {}}}})
def i18n_js():
    return FileResponse(STATIC_DIR / "i18n.js", media_type="application/javascript")


@app.get("/manifest.webmanifest")
def webmanifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/favicon.svg")
def favicon():
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


class ExtractRequest(BaseModel):
    url: HttpUrl


class SaveRequest(BaseModel):
    url: HttpUrl


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/extract")
def extract(req: ExtractRequest):
    url = str(req.url)
    conn = db.connect()
    try:
        cached = db.cache_get(conn, url)
        if cached:
            return {"source": "cache", "recipe": cached}
        html = fetch_html(url)
        recipe = extract_from_html(html, url)
        if not recipe:
            raise HTTPException(status_code=422,
                                detail="No recipe found on this page (JSON-LD, microdata and heuristics all failed).")
        db.cache_put(conn, url, recipe)
        return {"source": "live", "recipe": recipe}
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/recipes")
def save(req: SaveRequest):
    url = str(req.url)
    conn = db.connect()
    html = fetch_html(url)
    recipe = extract_from_html(html, url)
    if not recipe:
        raise HTTPException(status_code=422, detail="No recipe found on this page.")
    recipe_id = db.save_recipe(conn, url, recipe)
    db.cache_put(conn, url, recipe)
    return {"id": recipe_id, "recipe": recipe}


@app.get("/api/recipes")
def list_saved(q: str = "", tag: str = "", favorite: int = 0, sort: str = ""):
    conn = db.connect()
    return {"recipes": db.list_saved(conn, q=q or None, tag=tag or None,
                                     favorite=bool(favorite), sort=sort or None)}


class RatingRequest(BaseModel):
    favorite: Optional[bool] = None
    rating: Optional[int] = None  # 0..5 stars, 0 = no rating


@app.put("/api/recipes/{recipe_id}/rating")
def set_rating(recipe_id: int, req: RatingRequest):
    if req.rating is not None and not 0 <= req.rating <= 5:
        raise HTTPException(status_code=422, detail="rating must be 0..5")
    if not db.set_rating(db.connect(), recipe_id,
                         favorite=req.favorite, rating=req.rating):
        raise HTTPException(status_code=404, detail="Recipe not found.")
    item = db.get_saved(db.connect(), recipe_id)
    return {"id": recipe_id, "favorite": item["favorite"], "rating": item["rating"]}


class ScaleRequest(BaseModel):
    recipe: Dict
    servings: Optional[float] = None
    factor: Optional[float] = None


class ScaleServingsRequest(BaseModel):
    servings: float


@app.post("/api/scale")
def scale_recipe(req: ScaleRequest):
    from .quantities import scale_recipe as _scale
    scaled = _scale(req.recipe, servings=req.servings, factor=req.factor)
    if not scaled:
        raise HTTPException(
            status_code=422,
            detail="Cannot scale: pass 'factor', or 'servings' together with a recipe "
                   "whose 'servings' contains a base number.")
    return {"recipe": scaled}


@app.post("/api/recipes/{recipe_id}/scale")
def scale_saved(recipe_id: int, req: ScaleServingsRequest):
    item = db.get_saved(db.connect(), recipe_id)
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    from .quantities import scale_recipe as _scale
    scaled = _scale(item["recipe"], servings=req.servings)
    if not scaled:
        raise HTTPException(status_code=422,
                            detail="Recipe has no numeric servings to scale from.")
    return {"recipe": scaled}


class ConvertRequest(BaseModel):
    ingredients: List[str]


@app.post("/api/convert")
def convert_units(req: ConvertRequest):
    """cups→ml→g annotations for typical ingredients ('1/2 cup flour' → '≈ 60 g')."""
    from .convert import convert_ingredient
    items = [{"original": i, "converted": convert_ingredient(i)}
             for i in req.ingredients]
    return {"items": items}


@app.get("/api/substitutions")
def substitutions_base():
    """The full swap base, for display ('butter → margarine 1:1, coconut oil …')."""
    from .substitutions import SUBSTITUTIONS
    return {"substitutions": SUBSTITUTIONS}


@app.post("/api/substitutions/match")
def substitutions_match(req: ConvertRequest):
    """Per-line hints: which known ingredient appears and what can replace it."""
    from .substitutions import find_substitutions
    items = [{"original": i, "substitutes": find_substitutions(i)}
             for i in req.ingredients]
    return {"items": items}


class ShoppingListRequest(BaseModel):
    recipe_ids: List[int]


@app.post("/api/shopping-list")
def shopping_list(req: ShoppingListRequest):
    conn = db.connect()
    recipes, missing = [], []
    for rid in req.recipe_ids:
        item = db.get_saved(conn, rid)
        (recipes.append(item["recipe"]) if item else missing.append(rid))
    from .shopping import build_shopping_list
    result = build_shopping_list(recipes)
    result["missing_ids"] = missing
    return result


class PlanSlotRequest(BaseModel):
    slot: int  # 0..6, 0 = Monday
    recipe_id: Optional[int] = None


@app.get("/api/plan")
def get_plan():
    return {"slots": db.get_plan(db.connect())}


@app.put("/api/plan")
def put_plan_slot(req: PlanSlotRequest):
    if not 0 <= req.slot < db.PLAN_SLOTS:
        raise HTTPException(status_code=422,
                            detail=f"slot must be 0..{db.PLAN_SLOTS - 1}")
    if not db.set_plan_slot(db.connect(), req.slot, req.recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"slot": req.slot, "recipe_id": req.recipe_id}


@app.get("/api/plan/shopping-list")
def plan_shopping_list():
    from .shopping import build_shopping_list
    conn = db.connect()
    recipes = db.plan_recipes(conn)
    result = build_shopping_list(recipes)
    result["slots_used"] = len(recipes)
    return result


@app.get("/api/recipes/export")
def export_recipes():
    conn = db.connect()
    return {"version": 1, "recipes": db.export_all(conn)}


@app.get("/api/recipes/export.csv")
def export_recipes_csv():
    """One-click data safety: the whole book as CSV (title,url,tags,favorite,rating,saved_at)."""
    import csv
    import io

    conn = db.connect()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["title", "url", "tags", "favorite", "rating", "saved_at"])
    for r in db.export_all(conn):
        writer.writerow([r["title"], r["url"], ";".join(r["tags"]),
                         int(r["favorite"]), r["rating"], r["saved_at"]])
    from fastapi.responses import Response
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="recipes.csv"'})


@app.post("/api/demo")
def load_demo_recipes():
    """First-run experience: load 3 demo recipes (skips ones already present)."""
    from .demo import load_demo
    return {"added": load_demo(db.connect())}


@app.post("/api/recipes/import")
def import_recipes(payload: Any = Body(...)):
    """Accepts {'recipes': [...]} or a bare [...] in the export format."""
    items = payload.get("recipes") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise HTTPException(status_code=422, detail="Expected {'recipes': [...]} or a list.")
    imported = db.import_recipes(db.connect(), items)
    return {"imported": imported}


class TagsRequest(BaseModel):
    tags: List[str]


@app.put("/api/recipes/{recipe_id}/tags")
def set_tags(recipe_id: int, req: TagsRequest):
    if not db.set_tags(db.connect(), recipe_id, req.tags):
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"id": recipe_id, "tags": sorted(set(req.tags))}


@app.get("/api/recipes/{recipe_id}")
def get_saved(recipe_id: int):
    item = db.get_saved(db.connect(), recipe_id)
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return item


@app.delete("/api/recipes/{recipe_id}")
def delete_saved(recipe_id: int):
    if not db.delete_saved(db.connect(), recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"deleted": recipe_id}


@app.get("/print/{recipe_id}", response_class=HTMLResponse)
def print_view(recipe_id: int):
    item = db.get_saved(db.connect(), recipe_id)
    if not item:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    r = item["recipe"]
    from html import escape

    from .convert import annotate_ingredient
    title = escape(item["title"])
    url = escape(item["url"], quote=True)
    ings = "".join(f"<li>{annotate_ingredient(escape(str(i)))}</li>"
                   for i in r.get("ingredients", []))
    steps = "".join(f"<li>{escape(str(s))}</li>" for s in r.get("steps", []))
    meta = " · ".join(x for x in (r.get("servings"),
                                  r.get("total_time") and f"total: {r.get('total_time')}")
                      if x)
    return f"""<!doctype html><html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 640px; margin: 2rem auto;
         line-height: 1.55; color: #111; padding: 0 1rem; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: .3rem; margin-bottom: .3rem; }}
  .meta {{ color: #555; margin-top: 0; }}
  li {{ margin: .3rem 0; }}
  .toolbar {{ margin-bottom: 1rem; }}
  footer {{ margin-top: 2rem; border-top: 1px solid #999; font-size: .85rem; color: #555;
            word-break: break-all; }}
  /* --- print: clean card, no chrome, no awkward page breaks --- */
  @media print {{
    body {{ margin: 0 auto; max-width: none; font-size: 12pt; padding: 0; }}
    .toolbar {{ display: none; }}
    a {{ color: #111; text-decoration: none; }}
    li {{ break-inside: avoid; page-break-inside: avoid; }}
    h1, h2 {{ break-after: avoid; page-break-after: avoid; }}
    footer {{ border-top: 1px solid #333; }}
  }}
</style>
</head><body>
<div class="toolbar"><button onclick="window.print()">🖨 Друк</button></div>
<h1>{title}</h1>
<p class="meta">{escape(meta)}</p>
<h2>Ingredients</h2><ul>{ings}</ul>
<h2>Steps</h2><ol>{steps}</ol>
<footer>Original: <a href="{url}">{url}</a> — Recipe Distiller</footer>
</body></html>"""
