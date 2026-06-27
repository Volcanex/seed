import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from core.db import PROJECT_ROOT, get_conn

router = APIRouter()

PHOTOS_DIR = PROJECT_ROOT / "data" / "photos"
PHOTOS_DIR.mkdir(exist_ok=True, parents=True)


class HuntCreate(BaseModel):
    name: str
    date: str
    location_id: Optional[int] = None
    sale_type: str = "kgsale"
    cost_gbp: float = 0
    kg_price_gbp: Optional[float] = None
    notes: Optional[str] = None


class ItemCreate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    brand_name: Optional[str] = None
    nina_price_guess_gbp: Optional[float] = None
    purchase_price_gbp: Optional[float] = None
    weight_g: Optional[float] = None
    condition: str = "good"
    notes: Optional[str] = None
    photo_filenames: list = []


class ItemPatch(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    brand_name: Optional[str] = None
    nina_price_guess_gbp: Optional[float] = None
    purchase_price_gbp: Optional[float] = None
    weight_g: Optional[float] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class HuntPatch(BaseModel):
    cost_gbp: Optional[float] = None
    kg_price_gbp: Optional[float] = None
    notes: Optional[str] = None


@router.get("/locations")
def get_locations():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, type, area FROM locations WHERE active=1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/")
def create_hunt(body: HuntCreate):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO hunts (name, date, location_id, sale_type, cost_gbp, kg_price_gbp, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (body.name, body.date, body.location_id, body.sale_type,
             body.cost_gbp, body.kg_price_gbp, body.notes),
        )
        return _hunt_full(conn, cur.lastrowid)


@router.get("/active")
def get_active_hunt():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM hunts WHERE status='active' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return _hunt_full(conn, row["id"])


@router.get("/")
def list_hunts():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT h.id, h.name, h.date, h.sale_type, h.cost_gbp, h.kg_price_gbp,
                   h.status, h.created_at, l.name AS location_name,
                   COUNT(i.id) AS item_count,
                   COALESCE(SUM(i.nina_price_guess_gbp), 0) AS est_value_gbp
            FROM hunts h
            LEFT JOIN locations l ON l.id = h.location_id
            LEFT JOIN items i ON i.hunt_id = h.id
            GROUP BY h.id
            ORDER BY h.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]


@router.get("/{hunt_id}")
def get_hunt(hunt_id: int):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM hunts WHERE id=?", (hunt_id,)).fetchone():
            raise HTTPException(404, "Hunt not found")
        return _hunt_full(conn, hunt_id)


@router.patch("/{hunt_id}")
def patch_hunt(hunt_id: int, body: HuntPatch):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM hunts WHERE id=?", (hunt_id,)).fetchone():
            raise HTTPException(404, "Hunt not found")
        fields = {k: v for k, v in body.model_dump().items() if v is not None}
        if fields:
            set_clause = ", ".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE hunts SET {set_clause} WHERE id=?", (*fields.values(), hunt_id))
        return _hunt_full(conn, hunt_id)


@router.post("/{hunt_id}/items")
def add_item(hunt_id: int, body: ItemCreate):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM hunts WHERE id=? AND status='active'", (hunt_id,)).fetchone():
            raise HTTPException(404, "Active hunt not found")
        cur = conn.execute(
            """INSERT INTO items
               (hunt_id, description, category, brand_name, nina_price_guess_gbp,
                purchase_price_gbp, weight_g, condition, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (hunt_id, body.description, body.category, body.brand_name,
             body.nina_price_guess_gbp, body.purchase_price_gbp,
             body.weight_g, body.condition, body.notes),
        )
        item_id = cur.lastrowid
        for i, fn in enumerate(body.photo_filenames):
            if fn and (PHOTOS_DIR / fn).exists():
                conn.execute(
                    "INSERT INTO item_photos (item_id, filename, sort_order) VALUES (?,?,?)",
                    (item_id, fn, i),
                )
        return _item_full(conn, item_id)


@router.patch("/{hunt_id}/items/{item_id}")
def patch_item(hunt_id: int, item_id: int, body: ItemPatch):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM items WHERE id=? AND hunt_id=?", (item_id, hunt_id)).fetchone():
            raise HTTPException(404, "Item not found")
        fields = {k: v for k, v in body.model_dump().items() if v is not None}
        if fields:
            set_clause = ", ".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE items SET {set_clause} WHERE id=?", (*fields.values(), item_id))
        return _item_full(conn, item_id)


@router.delete("/{hunt_id}/items/{item_id}")
def delete_item(hunt_id: int, item_id: int):
    with get_conn() as conn:
        for p in conn.execute("SELECT filename FROM item_photos WHERE item_id=?", (item_id,)).fetchall():
            (PHOTOS_DIR / p["filename"]).unlink(missing_ok=True)
        conn.execute("DELETE FROM item_photos WHERE item_id=?", (item_id,))
        conn.execute("DELETE FROM items WHERE id=? AND hunt_id=?", (item_id, hunt_id))
        return {"ok": True}


@router.post("/{hunt_id}/complete")
def complete_hunt(hunt_id: int):
    with get_conn() as conn:
        if not conn.execute("SELECT id FROM hunts WHERE id=?", (hunt_id,)).fetchone():
            raise HTTPException(404)
        conn.execute("UPDATE hunts SET status='complete' WHERE id=?", (hunt_id,))
        return _hunt_full(conn, hunt_id)


@router.post("/photos")
async def upload_photo(image: UploadFile = File(...)):
    ct = image.content_type or ""
    if not ct.startswith("image/"):
        raise HTTPException(400, "Must be an image file")
    data = await image.read()
    if len(data) > 30 * 1024 * 1024:
        raise HTTPException(400, "Image too large (max 30 MB)")
    ext = (ct.split("/")[-1] or "jpg").replace("jpeg", "jpg")
    if ext not in ("jpg", "png", "gif", "webp", "heic"):
        ext = "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    (PHOTOS_DIR / filename).write_bytes(data)
    return {"filename": filename, "url": f"/photos/{filename}"}


def _hunt_full(conn, hunt_id: int) -> dict:
    h = conn.execute(
        "SELECT h.*, l.name AS location_name FROM hunts h LEFT JOIN locations l ON l.id=h.location_id WHERE h.id=?",
        (hunt_id,),
    ).fetchone()
    items = []
    for row in conn.execute("SELECT * FROM items WHERE hunt_id=? ORDER BY created_at", (hunt_id,)).fetchall():
        items.append(_item_full(conn, row["id"]))
    d = dict(h)
    d["items"] = items
    return d


def _item_full(conn, item_id: int) -> dict:
    row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    item = dict(row)
    photos = conn.execute(
        "SELECT filename, is_worn FROM item_photos WHERE item_id=? ORDER BY sort_order, id",
        (item_id,),
    ).fetchall()
    item["photos"] = [{"url": f"/photos/{p['filename']}", "is_worn": bool(p["is_worn"])} for p in photos]
    return item
