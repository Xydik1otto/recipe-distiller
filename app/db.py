"""SQLite storage: extraction cache + saved recipe book."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Dict, List, Optional

CACHE_TTL = 24 * 3600  # seconds

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    url        TEXT PRIMARY KEY,
    data       TEXT NOT NULL,
    fetched_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS saved (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT NOT NULL,
    title      TEXT NOT NULL,
    data       TEXT NOT NULL,
    saved_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS meal_plan (
    slot      INTEGER PRIMARY KEY,
    recipe_id INTEGER
);
"""

PLAN_SLOTS = 7  # one week, slot 0 = Monday


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns that older DB files miss (idempotent)."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(saved)").fetchall()]
    if "tags" not in cols:
        conn.execute("ALTER TABLE saved ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'")
        conn.commit()
    if "favorite" not in cols:
        conn.execute("ALTER TABLE saved ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    if "rating" not in cols:
        conn.execute("ALTER TABLE saved ADD COLUMN rating INTEGER NOT NULL DEFAULT 0")
        conn.commit()


def db_path() -> str:
    return os.environ.get("RECIPE_DB", "recipes.db")


def connect(path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    _migrate(conn)
    return conn


def cache_get(conn: sqlite3.Connection, url: str) -> Optional[Dict]:
    row = conn.execute("SELECT data, fetched_at FROM cache WHERE url = ?", (url,)).fetchone()
    if not row or time.time() - row["fetched_at"] > CACHE_TTL:
        return None
    return json.loads(row["data"])


def cache_put(conn: sqlite3.Connection, url: str, data: Dict) -> None:
    conn.execute("INSERT OR REPLACE INTO cache (url, data, fetched_at) VALUES (?, ?, ?)",
                 (url, json.dumps(data, ensure_ascii=False), time.time()))
    conn.commit()


def save_recipe(conn: sqlite3.Connection, url: str, data: Dict) -> int:
    cur = conn.execute(
        "INSERT INTO saved (url, title, data, saved_at) VALUES (?, ?, ?, ?)",
        (url, data.get("title") or url, json.dumps(data, ensure_ascii=False), time.time()))
    conn.commit()
    return cur.lastrowid


def list_saved(conn: sqlite3.Connection, q: Optional[str] = None,
               tag: Optional[str] = None, favorite: Optional[bool] = None,
               sort: Optional[str] = None) -> List[Dict]:
    """Saved recipes; optional search by title/ingredients, tag, favorites-only, sorting.

    sort: None/'new' -> newest first, 'rating' -> best rated first, 'title' -> A-Z.
    """
    sql = "SELECT id, url, title, tags, favorite, rating, saved_at FROM saved"
    clauses, params = [], []
    if q:
        clauses.append("(title LIKE ? OR data LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if favorite:
        clauses.append("favorite = 1")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += {"rating": " ORDER BY rating DESC, saved_at DESC",
            "title": " ORDER BY title COLLATE NOCASE"}.get(sort or "", " ORDER BY saved_at DESC")
    rows = conn.execute(sql, params).fetchall()
    return [{"id": r["id"], "url": r["url"], "title": r["title"],
             "tags": json.loads(r["tags"]), "favorite": bool(r["favorite"]),
             "rating": r["rating"], "saved_at": r["saved_at"]}
            for r in rows]


def set_rating(conn: sqlite3.Connection, recipe_id: int,
               favorite: Optional[bool] = None,
               rating: Optional[int] = None) -> bool:
    """Set favorite flag and/or 0..5 star rating; returns False when id is unknown."""
    sets, params = [], []
    if favorite is not None:
        sets.append("favorite = ?")
        params.append(1 if favorite else 0)
    if rating is not None:
        sets.append("rating = ?")
        params.append(int(rating))
    if not sets:
        return conn.execute("SELECT 1 FROM saved WHERE id = ?",
                            (recipe_id,)).fetchone() is not None
    params.append(recipe_id)
    cur = conn.execute(f"UPDATE saved SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    return cur.rowcount > 0


def set_tags(conn: sqlite3.Connection, recipe_id: int, tags: List[str]) -> bool:
    tags = sorted({str(t).strip() for t in tags if str(t).strip()})
    cur = conn.execute("UPDATE saved SET tags = ? WHERE id = ?",
                       (json.dumps(tags, ensure_ascii=False), recipe_id))
    conn.commit()
    return cur.rowcount > 0


def export_all(conn: sqlite3.Connection) -> List[Dict]:
    """Every saved recipe in full, for JSON export."""
    rows = conn.execute(
        "SELECT url, title, data, tags, favorite, rating, saved_at "
        "FROM saved ORDER BY saved_at").fetchall()
    return [{"url": r["url"], "title": r["title"],
             "recipe": json.loads(r["data"]), "tags": json.loads(r["tags"]),
             "favorite": bool(r["favorite"]), "rating": r["rating"],
             "saved_at": r["saved_at"]} for r in rows]


def import_recipes(conn: sqlite3.Connection, items: List[Dict]) -> int:
    """Bulk insert from an export file; returns the number imported."""
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        recipe = item.get("recipe") or item.get("data")
        if not isinstance(recipe, dict) or not item.get("url"):
            continue
        title = item.get("title") or recipe.get("title") or str(item["url"])
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        fav = 1 if item.get("favorite") else 0
        rating = item.get("rating")
        rating = int(rating) if isinstance(rating, (int, float)) and 0 <= rating <= 5 else 0
        conn.execute(
            "INSERT INTO saved (url, title, data, saved_at, tags, favorite, rating) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(item["url"]), title, json.dumps(recipe, ensure_ascii=False),
             float(item.get("saved_at") or time.time()),
             json.dumps([str(t) for t in tags], ensure_ascii=False), fav, rating))
        count += 1
    conn.commit()
    return count


def get_saved(conn: sqlite3.Connection, recipe_id: int) -> Optional[Dict]:
    row = conn.execute("SELECT * FROM saved WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "url": row["url"], "title": row["title"],
            "tags": json.loads(row["tags"]),
            "favorite": bool(row["favorite"]), "rating": row["rating"],
            "saved_at": row["saved_at"], "recipe": json.loads(row["data"])}


def delete_saved(conn: sqlite3.Connection, recipe_id: int) -> bool:
    cur = conn.execute("DELETE FROM saved WHERE id = ?", (recipe_id,))
    conn.execute("DELETE FROM meal_plan WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    return cur.rowcount > 0


def get_plan(conn: sqlite3.Connection) -> List[Dict]:
    """7 slots (0..6), each with the slotted recipe id and title (or None)."""
    rows = conn.execute(
        "SELECT p.slot, p.recipe_id, s.title FROM meal_plan p "
        "LEFT JOIN saved s ON s.id = p.recipe_id").fetchall()
    by_slot = {r["slot"]: (r["recipe_id"], r["title"]) for r in rows}
    return [{"slot": s, "recipe_id": by_slot.get(s, (None, None))[0],
             "title": by_slot.get(s, (None, None))[1]} for s in range(PLAN_SLOTS)]


def set_plan_slot(conn: sqlite3.Connection, slot: int,
                  recipe_id: Optional[int]) -> bool:
    """Place a recipe into a slot (recipe_id=None clears it)."""
    if not 0 <= slot < PLAN_SLOTS:
        return False
    if recipe_id is not None and not conn.execute(
            "SELECT 1 FROM saved WHERE id = ?", (recipe_id,)).fetchone():
        return False
    conn.execute("INSERT OR REPLACE INTO meal_plan (slot, recipe_id) VALUES (?, ?)",
                 (slot, recipe_id))
    conn.commit()
    return True


def plan_recipes(conn: sqlite3.Connection) -> List[Dict]:
    """Full recipe payloads of slotted meals, in slot order (empties skipped)."""
    rows = conn.execute(
        "SELECT s.data FROM meal_plan p JOIN saved s ON s.id = p.recipe_id "
        "ORDER BY p.slot").fetchall()
    return [json.loads(r["data"]) for r in rows]
