"""Smoke tests for SQLite scaffolding (core/db.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "smoke.db"
    monkeypatch.setenv("SEED_DB_PATH", str(db_file))
    for mod_name in list(sys.modules):
        if mod_name == "core.db" or mod_name.endswith(".core.db"):
            del sys.modules[mod_name]
    import importlib.util
    spec = importlib.util.spec_from_file_location("core.db", PROJECT_ROOT / "core" / "db.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_init_creates_tables(tmp_db):
    assert tmp_db.DB_PATH.is_file()
    with tmp_db.get_conn() as conn:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    assert "locations" in tables
    assert "brands" in tables


def test_get_conn_round_trip(tmp_db):
    with tmp_db.get_conn() as conn:
        conn.execute("INSERT INTO locations(name, type) VALUES (?, ?)", ("Test Shop", "kgsale"))
    with tmp_db.get_conn() as conn:
        row = conn.execute("SELECT name FROM locations WHERE type=?", ("kgsale",)).fetchone()
    assert row is not None
    assert row["name"] == "Test Shop"


def test_get_conn_rolls_back_on_exception(tmp_db):
    with pytest.raises(RuntimeError):
        with tmp_db.get_conn() as conn:
            conn.execute("INSERT INTO locations(name, type) VALUES (?, ?)", ("bad", "kgsale"))
            raise RuntimeError("boom")
    with tmp_db.get_conn() as conn:
        row = conn.execute("SELECT name FROM locations WHERE name=?", ("bad",)).fetchone()
    assert row is None


def test_init_is_idempotent(tmp_db):
    tmp_db.init_db()
    tmp_db.init_db()
    with tmp_db.get_conn() as conn:
        conn.execute("INSERT INTO brands(name, tier) VALUES (?, ?)", ("Test Brand", "A"))
