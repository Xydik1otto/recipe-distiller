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

app = FastAPI(title="Recipe Distiller", version="0.3.0")
# bookmarklet calls the API from any third-party site
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = Path(__file__).parent.parent / "static"


@app.get("/bookmarklet", response_class=HTMLResponse)
def bookmarklet_page():
    return FileResponse(STATIC_DIR / "bookmarklet.html")


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
def list_saved(q: str = "", tag: str = ""):
    conn = db.connect()
    return {"recipes": db.list_saved(conn, q=q or None, tag=tag or None)}


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
    ings = "".join(f"<li>{i}</li>" for i in r.get("ingredients", []))
    steps = "".join(f"<li>{s}</li>" for s in r.get("steps", []))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{item['title']}</title>
<style>body{{font-family:Georgia,serif;max-width:640px;margin:2rem auto;line-height:1.5}}
h1{{border-bottom:2px solid #333}} @media print {{ button {{ display:none }} }}</style>
</head><body onload="window.print()">
<button onclick="window.print()">Print</button>
<h1>{item['title']}</h1>
<p>{r.get('servings') or ''} {r.get('total_time') and '· ' + r.get('total_time') or ''}</p>
<h2>Ingredients</h2><ul>{ings}</ul>
<h2>Steps</h2><ol>{steps}</ol>
<p><a href="{item['url']}">Original: {item['url']}</a></p>
</body></html>"""
