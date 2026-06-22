import base64
import json
import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from core.db import get_conn

router = APIRouter()

_PROMPT = """Look at this clothing item carefully. Identify the brand from any visible logos, text on labels or tags, patterns, or distinctive branding.

Reply with ONLY a JSON object — no other text:
{"brand": "exact brand name", "confidence": "high|medium|low", "notes": "brief observation"}

If no brand is visible, return: {"brand": null, "confidence": "low", "notes": "no visible brand"}"""

_TIER_LABELS = {
    "S": "Top shelf — buy it",
    "A": "Good find",
    "B": "Worth buying at the right price",
    "C": "Depends on condition and price",
    "F": "Not worth reselling",
}


@router.post("/identify")
async def identify(image: UploadFile = File(...)):
    ct = image.content_type or ""
    if not ct.startswith("image/"):
        raise HTTPException(status_code=400, detail="Must be an image file")

    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Vision API not configured (ANTHROPIC_API_KEY missing)")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": ct,
                            "data": base64.standard_b64encode(data).decode(),
                        },
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }],
        )
        vision = json.loads(msg.content[0].text)
    except json.JSONDecodeError:
        vision = {"brand": None, "confidence": "low", "notes": "could not parse response"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vision error: {exc}")

    brand_name = vision.get("brand")
    brand_row = None

    if brand_name:
        with get_conn() as conn:
            brand_row = conn.execute(
                """SELECT * FROM brands
                   WHERE lower(name) = lower(?)
                      OR (keywords IS NOT NULL AND instr(lower(keywords), lower(?)) > 0)
                   LIMIT 1""",
                (brand_name, brand_name),
            ).fetchone()

    result = {
        "brand": brand_name,
        "confidence": vision.get("confidence", "low"),
        "notes": vision.get("notes", ""),
        "tier": None,
        "tier_label": "Unknown — not in database",
        "min_value_gbp": None,
        "max_value_gbp": None,
        "brand_notes": None,
    }

    if brand_row:
        result.update({
            "tier": brand_row["tier"],
            "tier_label": _TIER_LABELS.get(brand_row["tier"], ""),
            "min_value_gbp": brand_row["min_value_gbp"],
            "max_value_gbp": brand_row["max_value_gbp"],
            "brand_notes": brand_row["notes"],
        })

    return result
