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


def db_path() -> str:
    return os.environ.get("RECIPE_DB", "recipes.db")


def connect(path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
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


def list_saved(conn: sqlite3.Connection) -> List[Dict]:
    rows = conn.execute(
        "SELECT id, url, title, saved_at FROM saved ORDER BY saved_at DESC").fetchall()
    return [{"id": r["id"], "url": r["url"], "title": r["title"],
             "saved_at": r["saved_at"]} for r in rows]


def get_saved(conn: sqlite3.Connection, recipe_id: int) -> Optional[Dict]:
    row = conn.execute("SELECT * FROM saved WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    return {"id": row["id"], "url": row["url"], "title": row["title"],
            "saved_at": row["saved_at"], "recipe": json.loads(row["data"])}


def delete_saved(conn: sqlite3.Connection, recipe_id: int) -> bool:
    cur = conn.execute("DELETE FROM saved WHERE id = ?", (recipe_id,))
    conn.commit()
    return cur.rowcount > 0
