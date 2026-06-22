"""SQLite scaffolding — connection helper, idempotent init, and a place
to put your schema.

This file is intentionally tiny. It gives you:

- A `DB_PATH` that env-var-overrides for tests / alternate deployments.
- A `SCHEMA` string containing the project's tables (CREATE TABLE IF
  NOT EXISTS so it's safe to run on every import).
- `init_db()` — idempotent.
- `get_conn()` — context-managed connection with `Row` factory and
  auto-commit/rollback semantics.

The example schema below is a single `kv` table — replace it with your
own. For larger projects, switch `SCHEMA` to a list of migration files
loaded from a `core/migrations/` directory.

When you outgrow SQLite (concurrent writers, real users, > ~10k rows of
hot data), swap to Postgres: change the connection function, keep the
context-manager surface. The SQL is usually portable enough that schema
+ queries don't change.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Override via env var for tests and alternate deployments.
DB_PATH = Path(
    os.environ.get("SEED_DB_PATH") or str(PROJECT_ROOT / "data" / "seed.db")
)

# Replace this with your project's schema. The example `kv` table exists
# only so the smoke test has something to read/write — there's no
# expectation downstream projects keep it.
SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS locations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    type          TEXT NOT NULL,
    address       TEXT,
    area          TEXT,
    lat           REAL,
    lng           REAL,
    price_info    TEXT,
    opening_hours TEXT,
    notes         TEXT,
    website       TEXT,
    active        INTEGER DEFAULT 1,
    last_verified TEXT
);

CREATE TABLE IF NOT EXISTS reports (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    source     TEXT,
    date_added TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS brands (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    tier          TEXT NOT NULL,
    min_value_gbp REAL,
    max_value_gbp REAL,
    notes         TEXT,
    keywords      TEXT
);
"""


def init_db() -> None:
    """Idempotent. Safe to call on every import."""
    DB_PATH.parent.mkdir(exist_ok=True, parents=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate(conn) -> None:
    existing = {r[1] for r in conn.execute("PRAGMA table_info(locations)").fetchall()}
    new_cols = [
        ("score",      "INTEGER"),
        ("best_find",  "INTEGER DEFAULT 0"),
        ("date_added", "TEXT"),
        ("source",     "TEXT"),
    ]
    for col, typedef in new_cols:
        if col not in existing:
            conn.execute(f"ALTER TABLE locations ADD COLUMN {col} {typedef}")


@contextmanager
def get_conn():
    """Context-managed connection.

    - Auto-commits on clean exit; rolls back on exception.
    - `row_factory = sqlite3.Row` so rows behave like dicts.
    - Foreign keys are enforced per connection.

    Usage:

        from core.db import get_conn

        with get_conn() as conn:
            row = conn.execute("SELECT * FROM kv WHERE key = ?", (k,)).fetchone()
            conn.execute("INSERT INTO kv(key, value) VALUES(?, ?)", (k, v))
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Initialise schema on import.
init_db()
