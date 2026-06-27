# pages/hunt

Nina's mobile-first field interface for recording buying trips.

**API:** `/api/hunt` (pages/hunt/api.py)  
**State:** active hunt stored in localStorage as `apparel_hunt_id`

## Flow

1. Start hunt — sale type (KG sale vs fixed price), location, date, total spend, kg price if applicable
2. Add items one by one — photos (camera capture), category, description, brand, Nina's price guess, weight (KG) or purchase price (fixed)
3. Complete — dopamine screen with summary

## Sale types

- `kgsale` — KG sale: per-item cost = weight_g / 1000 × kg_price_gbp. Item form shows weight field.
- `fixed` — fixed price per item: per-item cost = purchase_price_gbp. Item form shows price-paid field.

## Photos

Uploaded immediately to `/api/hunt/photos` → stored in `data/photos/`. Filenames sent with item create payload. Photos served at `/photos/{filename}` (static mount in server.py).
