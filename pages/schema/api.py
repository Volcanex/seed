from fastapi import APIRouter

from core.db import get_conn

router = APIRouter()


@router.get("/locations")
def get_locations():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM locations ORDER BY best_find DESC, score DESC, date_added DESC, name"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/brands")
def get_brands():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM brands ORDER BY tier, name"
        ).fetchall()
    return [dict(r) for r in rows]
