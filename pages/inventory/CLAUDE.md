# pages/inventory

Gabriel's inventory management interface.

**API:** `/api/inventory` (pages/inventory/api.py)

## Endpoints

- `GET /api/inventory/items?hunt_id=&status=` — all items with computed cost_gbp and thumb_url
- `PATCH /api/inventory/items/{id}` — update item (list price, sold price, status, post date, vinted URL)
- `GET /api/inventory/hunts` — hunt summaries with item counts and revenue
- `GET /api/inventory/stats` — aggregate stats (total, listed, sold, profit)
- `GET /api/inventory/insights` — breakdown by category and brand
- `GET /api/inventory/export.csv` — full CSV export

## Cost calculation

Item cost is computed server-side per request (not stored):
- KG sale: `weight_g / 1000 × kg_price_gbp` from the parent hunt
- Fixed price: `purchase_price_gbp` on the item itself
