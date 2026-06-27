import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.db import get_conn

router = APIRouter()


class ItemUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    brand_name: Optional[str] = None
    condition: Optional[str] = None
    list_price_gbp: Optional[float] = None
    sold_price_gbp: Optional[float] = None
    status: Optional[str] = None
    vinted_url: Optional[str] = None
    post_date: Optional[str] = None
    notes: Optional[str] = None


@router.get("/items")
def list_items(
    hunt_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    with get_conn() as conn:
        where_clauses = []
        params = []
        if hunt_id is not None:
            where_clauses.append("i.hunt_id=?")
            params.append(hunt_id)
        if status:
            where_clauses.append("i.status=?")
            params.append(status)
        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        rows = conn.execute(f"""
            SELECT i.*,
                   h.name AS hunt_name, h.date AS hunt_date,
                   h.cost_gbp AS hunt_cost_gbp, h.sale_type, h.kg_price_gbp
            FROM items i
            JOIN hunts h ON h.id = i.hunt_id
            {where}
            ORDER BY i.created_at DESC
        """, params).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            photo = conn.execute(
                "SELECT filename FROM item_photos WHERE item_id=? ORDER BY sort_order, id LIMIT 1",
                (item["id"],),
            ).fetchone()
            item["thumb_url"] = f"/photos/{photo['filename']}" if photo else None
            # Compute cost for this item
            if item["sale_type"] == "kgsale" and item["kg_price_gbp"] and item["weight_g"]:
                item["cost_gbp"] = round((item["weight_g"] / 1000) * item["kg_price_gbp"], 2)
            elif item["purchase_price_gbp"]:
                item["cost_gbp"] = item["purchase_price_gbp"]
            else:
                item["cost_gbp"] = None
            items.append(item)
        return items


@router.patch("/items/{item_id}")
def update_item(item_id: int, body: ItemUpdate):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM items WHERE id=?", (item_id,)).fetchone():
            raise HTTPException(404, "Item not found")

        update = {k: v for k, v in body.model_dump().items() if v is not None}

        if update.get("status") == "listed" and "listed_at" not in update:
            update["listed_at"] = datetime.now().isoformat()
        if update.get("status") == "sold" and "sold_at" not in update:
            update["sold_at"] = datetime.now().isoformat()

        if update:
            set_clause = ", ".join(f"{k}=?" for k in update)
            conn.execute(f"UPDATE items SET {set_clause} WHERE id=?", (*update.values(), item_id))

        return dict(conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone())


@router.get("/hunts")
def list_hunts():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                h.id, h.name, h.date, h.cost_gbp, h.sale_type, h.status,
                l.name AS location_name,
                COUNT(i.id) AS item_count,
                SUM(CASE WHEN i.status='sold' THEN 1 ELSE 0 END) AS sold_count,
                COALESCE(SUM(CASE WHEN i.status='sold' THEN i.sold_price_gbp ELSE 0 END), 0) AS revenue_gbp,
                COALESCE(SUM(i.nina_price_guess_gbp), 0) AS est_value_gbp
            FROM hunts h
            LEFT JOIN locations l ON l.id = h.location_id
            LEFT JOIN items i ON i.hunt_id = h.id
            GROUP BY h.id
            ORDER BY h.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


@router.get("/stats")
def get_stats():
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total_items,
                SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) AS sold_count,
                SUM(CASE WHEN status='listed' THEN 1 ELSE 0 END) AS listed_count,
                SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) AS new_count,
                COALESCE(SUM(CASE WHEN status='sold' THEN sold_price_gbp ELSE 0 END), 0) AS total_revenue
            FROM items
        """).fetchone()
        total_cost = conn.execute(
            "SELECT COALESCE(SUM(cost_gbp), 0) FROM hunts"
        ).fetchone()[0]
        d = dict(row)
        d["total_cost"] = total_cost
        d["profit"] = round(d["total_revenue"] - total_cost, 2)
        return d


@router.get("/insights")
def get_insights():
    with get_conn() as conn:
        by_cat = conn.execute("""
            SELECT category,
                   COUNT(*) AS item_count,
                   SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) AS sold_count,
                   ROUND(AVG(CASE WHEN status='sold' THEN sold_price_gbp END), 2) AS avg_sold_price,
                   ROUND(AVG(nina_price_guess_gbp), 2) AS avg_nina_guess
            FROM items WHERE category IS NOT NULL
            GROUP BY category ORDER BY sold_count DESC, item_count DESC
        """).fetchall()

        by_brand = conn.execute("""
            SELECT brand_name,
                   COUNT(*) AS item_count,
                   SUM(CASE WHEN status='sold' THEN 1 ELSE 0 END) AS sold_count,
                   ROUND(AVG(CASE WHEN status='sold' THEN sold_price_gbp END), 2) AS avg_sold_price
            FROM items WHERE brand_name IS NOT NULL
            GROUP BY brand_name ORDER BY sold_count DESC, item_count DESC LIMIT 20
        """).fetchall()

        return {
            "by_category": [dict(r) for r in by_cat],
            "by_brand": [dict(r) for r in by_brand],
        }


@router.get("/export.csv")
def export_csv():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT i.id, h.name AS hunt, h.date AS hunt_date, h.cost_gbp AS hunt_cost,
                   i.description, i.category, i.brand_name, i.condition,
                   i.nina_price_guess_gbp, i.purchase_price_gbp, i.weight_g,
                   i.list_price_gbp, i.sold_price_gbp, i.status,
                   i.listed_at, i.sold_at, i.post_date, i.vinted_url, i.notes, i.created_at
            FROM items i JOIN hunts h ON h.id = i.hunt_id
            ORDER BY i.created_at DESC
        """).fetchall()

    buf = io.StringIO()
    fields = [
        "id", "hunt", "hunt_date", "hunt_cost", "description", "category",
        "brand_name", "condition", "nina_price_guess_gbp", "purchase_price_gbp",
        "weight_g", "list_price_gbp", "sold_price_gbp", "status",
        "listed_at", "sold_at", "post_date", "vinted_url", "notes", "created_at",
    ]
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for row in rows:
        w.writerow(dict(row))
    buf.seek(0)
    return StreamingResponse(
        iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=apparel_inventory.csv"},
    )
