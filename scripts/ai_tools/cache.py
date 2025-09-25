"""Simple file-backed prompt-response cache."""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

DB_PATH = os.getenv("AI_CACHE_DB", ".ai_cache.sqlite")


class PromptCache:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._ensure_db()

    def _ensure_db(self) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value "
                "TEXT, ts INTEGER)"
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.path)
        try:
            cur = conn.execute("SELECT value FROM cache WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def set(self, key: str, value: str) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "REPLACE INTO cache (key, value, ts) "
                "VALUES (?, ?, strftime('%s','now'))",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()
