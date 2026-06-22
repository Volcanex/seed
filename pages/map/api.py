from fastapi import APIRouter, Query
from core.db import get_conn

router = APIRouter()


@router.get("")
def list_locations(type: str = Query(default="")):
    with get_conn() as conn:
        if type:
            rows = conn.execute(
                "SELECT * FROM locations WHERE active=1 AND type=? ORDER BY area, name",
                (type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM locations WHERE active=1 ORDER BY area, name"
            ).fetchall()
    return [dict(r) for r in rows]


@router.post("")
def add_location(body: dict):
    required = {"name", "type"}
    if not required.issubset(body):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="name and type are required")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO locations
               (name, type, address, area, lat, lng, price_info, opening_hours, notes, website, last_verified)
               VALUES (:name,:type,:address,:area,:lat,:lng,:price_info,:opening_hours,:notes,:website,:last_verified)""",
            {
                "name": body.get("name"),
                "type": body.get("type"),
                "address": body.get("address"),
                "area": body.get("area"),
                "lat": body.get("lat"),
                "lng": body.get("lng"),
                "price_info": body.get("price_info"),
                "opening_hours": body.get("opening_hours"),
                "notes": body.get("notes"),
                "website": body.get("website"),
                "last_verified": body.get("last_verified"),
            }
        )
    return {"ok": True}
