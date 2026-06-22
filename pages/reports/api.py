from fastapi import APIRouter
from core.db import get_conn

router = APIRouter()


@router.get("")
def list_reports():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY date_added DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{report_id}")
def get_report(report_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)
