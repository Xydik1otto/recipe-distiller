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
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns that older DB files miss (idempotent)."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(saved)").fetchall()]
    if "tags" not in cols:
        conn.execute("ALTER TABLE saved ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'")
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
               tag: Optional[str] = None) -> List[Dict]:
    """Saved recipes, newest first; optional search by title/ingredients and tag."""
    sql = ("SELECT id, url, title, tags, saved_at, data FROM saved")
    clauses, params = [], []
    if q:
        clauses.append("(title LIKE ? OR data LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY saved_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return [{"id": r["id"], "url": r["url"], "title": r["title"],
             "tags": json.loads(r["tags"]), "saved_at": r["saved_at"]}
            for r in rows]


def set_tags(conn: sqlite3.Connection, recipe_id: int, tags: List[str]) -> bool:
    tags = sorted({str(t).strip() for t in tags if str(t).strip()})
    cur = conn.execute("UPDATE saved SET tags = ? WHERE id = ?",
                       (json.dumps(tags, ensure_ascii=False), recipe_id))
    conn.commit()
    return cur.rowcount > 0


def export_all(conn: sqlite3.Connection) -> List[Dict]:
    """Every saved recipe in full, for JSON export."""
    rows = conn.execute(
        "SELECT url, title, data, tags, saved_at FROM saved ORDER BY saved_at").fetchall()
    return [{"url": r["url"], "title": r["title"],
             "recipe": json.loads(r["data"]), "tags": json.loads(r["tags"]),
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
        conn.execute(
            "INSERT INTO saved (url, title, data, saved_at, tags) VALUES (?, ?, ?, ?, ?)",
            (str(item["url"]), title, json.dumps(recipe, ensure_ascii=False),
             float(item.get("saved_at") or time.time()),
             json.dumps([str(t) for t in tags], ensure_ascii=False)))
        count += 1
    conn.commit()
    return count


def get_saved(conn: sqlite3.Connection, recipe_id: int) -> Optional[Dict]:
    row = conn.execute("SELECT * FROM saved WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "url": row["url"], "title": row["title"],
            "tags": json.loads(row["tags"]),
            "saved_at": row["saved_at"], "recipe": json.loads(row["data"])}


def delete_saved(conn: sqlite3.Connection, recipe_id: int) -> bool:
    cur = conn.execute("DELETE FROM saved WHERE id = ?", (recipe_id,))
    conn.commit()
    return cur.rowcount > 0
