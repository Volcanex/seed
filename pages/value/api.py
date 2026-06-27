import base64
import json
import logging
import os

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)

from core.db import get_conn

router = APIRouter()

_VISION_MODEL = "anthropic/claude-haiku-4.5"
_PRICE_MODEL  = "anthropic/claude-haiku-4.5"

_VISION_PROMPT = """Look at this clothing item carefully. Identify the brand and type of garment from any visible logos, text on labels or tags, patterns, or distinctive branding.

Reply with ONLY a JSON object — no other text:
{"brand": "exact brand name", "item_type": "e.g. blazer, jeans, dress, t-shirt, coat", "confidence": "high|medium|low", "notes": "brief observation"}

If no brand is visible, return: {"brand": null, "item_type": null, "confidence": "low", "notes": "no visible brand"}"""

_TIER_LABELS = {
    "S": "Top shelf — buy it",
    "A": "Good find",
    "B": "Worth buying at the right price",
    "C": "Depends on condition and price",
    "F": "Not worth reselling",
}

_CLOTHING_TERMS = {
    "blazer", "jacket", "dress", "jeans", "trousers", "coat", "shirt",
    "blouse", "skirt", "shorts", "top", "sweater", "hoodie", "cardigan",
    "suit", "jumpsuit", "playsuit", "leggings", "vest", "t-shirt",
}


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that models sometimes wrap JSON in."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _require_openrouter() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="API not configured (OPENROUTER_API_KEY missing)")
    return key


async def _identify_with_google_vision(data: bytes) -> dict:
    api_key = os.environ.get("GOOGLE_VISION_API_KEY")
    b64 = base64.standard_b64encode(data).decode()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
                json={
                    "requests": [{
                        "image": {"content": b64},
                        "features": [
                            {"type": "WEB_DETECTION", "maxResults": 10},
                            {"type": "LOGO_DETECTION", "maxResults": 5},
                        ],
                    }]
                },
            )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Google Vision error {exc.response.status_code}: {exc.response.text[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vision error: {exc}")

    response = resp.json()["responses"][0]
    web = response.get("webDetection", {})
    logos = response.get("logoAnnotations", [])

    brand = None
    if logos:
        brand = logos[0]["description"]
    else:
        for entity in web.get("webEntities", []):
            if entity.get("score", 0) > 0.5 and entity.get("description"):
                brand = entity["description"]
                break

    item_type = None
    best_guesses = web.get("bestGuessLabels", [])
    if best_guesses:
        label = best_guesses[0].get("label", "")
        clean = label.lower().replace(brand.lower(), "").strip() if brand else label.lower()
        for term in _CLOTHING_TERMS:
            if term in clean:
                item_type = term
                break
        if not item_type and clean:
            item_type = clean

    if not item_type:
        for entity in web.get("webEntities", []):
            desc = entity.get("description", "").lower()
            if desc in _CLOTHING_TERMS:
                item_type = desc
                break

    notes = best_guesses[0].get("label", "") if best_guesses else ""
    confidence = "high" if logos else ("medium" if brand else "low")
    return {"brand": brand, "item_type": item_type, "confidence": confidence, "notes": notes}


async def _identify_with_claude(data: bytes, content_type: str, api_key: str) -> dict:
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
                    "model": _VISION_MODEL,
                    "max_tokens": 256,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{b64}"}},
                            {"type": "text", "text": _VISION_PROMPT},
                        ],
                    }],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError:
        return {"brand": None, "item_type": None, "confidence": "low", "notes": "could not parse response"}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"OpenRouter error {exc.response.status_code}: {exc.response.text[:200]}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vision error: {exc}")


async def _estimate_with_claude(brand: str | None, item_type: str | None, api_key: str) -> dict | None:
    if not brand and not item_type:
        return None
    if brand:
        item_desc = f"{brand} {item_type}".strip() if item_type else brand
        context = f"Consider the brand's Vinted/Depop demographic and typical pricing."
    else:
        item_desc = item_type
        context = "This is an unbranded or generic item. Estimate conservatively."
    prompt = (
        f"What is the typical resale price range on Vinted UK for a secondhand '{item_desc}' in good condition? "
        "Also estimate the typical weight in grams for this type of garment.\n\n"
        f"{context}\n\n"
        "Reply with ONLY a JSON object — no other text:\n"
        '{"min_gbp": <integer>, "max_gbp": <integer>, "weight_g": <integer>}'
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://apparel.gabrielpenman.com",
                },
                json={
                    "model": _PRICE_MODEL,
                    "max_tokens": 64,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_fences(raw))
        return {
            "min": int(parsed["min_gbp"]),
            "max": int(parsed["max_gbp"]),
            "weight_g": int(parsed.get("weight_g", 0)) or None,
        }
    except Exception as exc:
        logger.warning("_estimate_with_claude failed for %r: %s", brand, exc)
        return None


async def _fetch_ebay_sold_prices(brand: str, item_type: str | None) -> list[float] | None:
    app_id = os.environ.get("EBAY_APP_ID")
    if not app_id:
        return None

    query = f"{brand} {item_type}".strip() if item_type else brand
    params = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.0.0",
        "APP-ID": app_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "siteid": "3",
        "itemFilter(0).name": "SoldItemsOnly",
        "itemFilter(0).value": "true",
        "itemFilter(1).name": "Currency",
        "itemFilter(1).value": "GBP",
        "itemFilter(2).name": "ListingType",
        "itemFilter(2).value": "FixedPrice",
        "paginationInput.entriesPerPage": "24",
        "categoryId": "3002",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://svcs.ebay.com/services/search/FindingService/v1",
                params=params,
            )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    try:
        items = (
            data["findCompletedItemsResponse"][0]
            ["searchResult"][0]
            .get("item", [])
        )
    except (KeyError, IndexError):
        return None

    prices = []
    for item in items:
        try:
            price_obj = item["sellingStatus"][0]["currentPrice"][0]
            if price_obj.get("@currencyId") == "GBP":
                prices.append(float(price_obj["__value__"]))
        except (KeyError, IndexError, ValueError, TypeError):
            pass

    return prices if len(prices) >= 3 else None


async def _estimate_depop_from_ebay(
    brand: str,
    item_type: str | None,
    ebay_prices: list[float],
    api_key: str,
) -> dict:
    ebay_prices.sort()
    n = len(ebay_prices)
    p25 = round(ebay_prices[n // 4])
    p75 = round(ebay_prices[(3 * n) // 4])
    median = round(ebay_prices[n // 2])

    item_desc = f"{brand} {item_type}".strip() if item_type else brand
    prompt = (
        f"eBay UK sold listings for '{item_desc}' (used clothing): "
        f"{n} sales, P25=£{p25}, median=£{median}, P75=£{p75}.\n\n"
        "Depop skews younger (18-30), fast-fashion and vintage brands. "
        "Prices typically 10-30% lower than eBay for mainstream brands, "
        "but higher for streetwear/vintage.\n\n"
        "Reply with ONLY a JSON object — no other text:\n"
        '{"min_gbp": <integer>, "max_gbp": <integer>}'
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://apparel.gabrielpenman.com",
                },
                json={
                    "model": _PRICE_MODEL,
                    "max_tokens": 64,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        resp.raise_for_status()
        parsed = json.loads(_strip_fences(resp.json()["choices"][0]["message"]["content"]))
        return {"min": int(parsed["min_gbp"]), "max": int(parsed["max_gbp"]), "weight_g": None}
    except Exception:
        return {"min": p25, "max": p75, "weight_g": None}


@router.post("/identify")
async def identify(image: UploadFile = File(...)):
    ct = image.content_type or ""
    if not ct.startswith("image/"):
        raise HTTPException(status_code=400, detail="Must be an image file")

    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")

    openrouter_key = _require_openrouter()

    if os.environ.get("GOOGLE_VISION_API_KEY"):
        vision = await _identify_with_google_vision(data)
    else:
        vision = await _identify_with_claude(data, ct, openrouter_key)

    brand_name = vision.get("brand")
    item_type = vision.get("item_type")
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

    live_prices = None
    price_source = None

    if brand_name:
        ebay_prices = await _fetch_ebay_sold_prices(brand_name, item_type)
        if ebay_prices:
            live_prices = await _estimate_depop_from_ebay(brand_name, item_type, ebay_prices, openrouter_key)
            price_source = "ebay+ai"
        elif not brand_row:
            # Only call Claude when brand is not already in the DB — saves ~1-2s for known brands
            live_prices = await _estimate_with_claude(brand_name, item_type, openrouter_key)
            price_source = "ai"
    elif item_type:
        # No brand identified — still estimate generic value from item type
        live_prices = await _estimate_with_claude(None, item_type, openrouter_key)
        price_source = "ai"

    result = {
        "brand": brand_name,
        "item_type": item_type,
        "confidence": vision.get("confidence", "low"),
        "notes": vision.get("notes", ""),
        "tier": None,
        "tier_label": "Unknown — not in database",
        "min_value_gbp": None,
        "max_value_gbp": None,
        "estimated_weight_g": None,
        "brand_notes": None,
        "price_source": price_source,
    }

    if brand_row:
        result.update({
            "tier": brand_row["tier"],
            "tier_label": _TIER_LABELS.get(brand_row["tier"], ""),
            "brand_notes": brand_row["notes"],
        })

    if live_prices:
        result.update({
            "min_value_gbp": live_prices["min"],
            "max_value_gbp": live_prices["max"],
            "estimated_weight_g": live_prices.get("weight_g"),
        })
    elif brand_row:
        result.update({
            "min_value_gbp": brand_row["min_value_gbp"],
            "max_value_gbp": brand_row["max_value_gbp"],
            "price_source": "database",
        })

    return result
