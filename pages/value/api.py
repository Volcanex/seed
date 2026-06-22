import base64
import json
import os

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

from core.db import get_conn

router = APIRouter()

_MODEL  = "anthropic/claude-haiku-4-5"
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

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Vision API not configured (OPENROUTER_API_KEY missing)")

    b64 = base64.standard_b64encode(data).decode()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://apparel.gabrielpenman.com",
                },
                json={
                    "model": _MODEL,
                    "max_tokens": 256,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{ct};base64,{b64}"}},
                            {"type": "text", "text": _PROMPT},
                        ],
                    }],
                },
            )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"]
        vision = json.loads(text)
    except json.JSONDecodeError:
        vision = {"brand": None, "confidence": "low", "notes": "could not parse response"}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"OpenRouter error {exc.response.status_code}: {exc.response.text[:200]}")
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
