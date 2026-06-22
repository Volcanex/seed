# apparel

London clothing sourcing tool for Gabriel's girlfriend — track KG sale shops, car boots, and fabric wholesale across London, plus identify clothing brands from photos.

**Owner:** Gabriel Penman  
**Domain:** apparel.gabrielpenman.com  
**Stack:** gseed-app (FastAPI + compile pipeline), SQLite, Leaflet.js, Anthropic claude-haiku vision  
**Port:** 8005

## Tools

- `/map` — London map with sourcing locations. Filter by type: KG Sale / Car Boot / Fabric.
- `/value` — Upload clothing photo → Claude vision identifies brand → tier + estimated resale value.

## Environment variables

| Var | Required | What |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for `/value`) | Claude Haiku vision calls |
| `SEED_DB_PATH` | No | SQLite path (default: `data/seed.db`) |

Add `ANTHROPIC_API_KEY` to the gcore passport and to `.env` here before deploying.

## DB tables

- `locations` — name, type (`kgsale`/`carboot`/`fabric`), lat/lng, price_info, opening_hours, notes, website, active, last_verified
- `brands` — name, tier (`S`/`A`/`B`/`C`/`F`), min/max_value_gbp, notes, keywords

Tier meaning: S = top shelf (£60-450), A = good find (£15-140), B = worth buying (£8-55), C = depends (£3-20), F = not worth reselling (<£5).

## Setup

```bash
pip install -r requirements.txt
python3 data/seed_db.py        # populate initial brands + locations (safe to re-run)
python3 compile.py
python3 server.py              # local dev on :8080
```

## Deploy

```bash
# 1. Add ANTHROPIC_API_KEY to .env
# 2. Seed the DB (runs on host, data/ volume-mounted into container)
python3 data/seed_db.py
# 3. Build and start
docker compose up -d
# 4. Nginx vhost
sudo cp nginx/apparel.conf /etc/nginx/sites-available/apparel
sudo ln -s /etc/nginx/sites-available/apparel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
# 5. Systemd service
sudo cp apparel.service /etc/systemd/system/apparel.service
sudo systemctl enable --now apparel
```

## Adding locations

POST to `/api/map` with JSON body: `{name, type, lat, lng, price_info, opening_hours, notes, address, area, website}`.  
Or run `data/seed_db.py` after adding entries to the `LOCATIONS` list.

The cron skill can call the POST endpoint to add newly discovered spots.

## Key commands

```bash
python3 compile.py                  # rebuild pages (run after any pages/ change)
python3 scripts/compile_docs.py     # rebuild docs index below
pytest                              # run smoke tests
docker compose logs -f              # tail container logs
```

<!-- DOCS:START -->
| Path | Summary |
|------|---------|
| `agents/CLAUDE.md` | Agents — kickoff prompts for parallel integrations |
| `core/api/CLAUDE.md` | core/api — shared API routers |
| `core/templates/CLAUDE.md` | Templates — the shared shell |
| `pages/CLAUDE.md` | Pages |
| `tests/CLAUDE.md` | Tests |

_Auto-compiled 2026-06-22 18:44 UTC — 5 doc(s) found._
<!-- DOCS:END -->
