from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.db import get_conn

router = APIRouter()


@router.get("")
def list_locations(
    type: str = Query(default=""),
    best_find: str = Query(default=""),
    min_score: str = Query(default=""),
    days: str = Query(default=""),
):
    conditions = ["active=1"]
    params = []

    if type:
        conditions.append("type=?")
        params.append(type)

    if best_find == "1":
        conditions.append("best_find=1")

    if min_score.isdigit():
        conditions.append("score>=?")
        params.append(int(min_score))

    if days.isdigit():
        cutoff = (date.today() - timedelta(days=int(days))).isoformat()
        conditions.append("date_added>=?")
        params.append(cutoff)

    where = " AND ".join(conditions)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM locations WHERE {where} ORDER BY best_find DESC, score DESC, area, name",
            params,
        ).fetchall()

    return [dict(r) for r in rows]


@router.post("")
def add_location(body: dict):
    if not {"name", "type"}.issubset(body):
        raise HTTPException(status_code=400, detail="name and type are required")

    today = date.today().isoformat()

    with get_conn() as conn:
        conn.execute(
            """INSERT INTO locations
               (name, type, address, area, lat, lng,
                price_info, opening_hours, notes, website,
                score, best_find, date_added, source, last_verified)
               VALUES
               (:name,:type,:address,:area,:lat,:lng,
                :price_info,:opening_hours,:notes,:website,
                :score,:best_find,:date_added,:source,:last_verified)""",
            {
                "name":          body.get("name"),
                "type":          body.get("type"),
                "address":       body.get("address"),
                "area":          body.get("area"),
                "lat":           body.get("lat"),
                "lng":           body.get("lng"),
                "price_info":    body.get("price_info"),
                "opening_hours": body.get("opening_hours"),
                "notes":         body.get("notes"),
                "website":       body.get("website"),
                "score":         body.get("score"),
                "best_find":     1 if body.get("best_find") else 0,
                "date_added":    body.get("date_added", today),
                "source":        body.get("source", "manual"),
                "last_verified": body.get("last_verified"),
            },
        )
    return {"ok": True}
