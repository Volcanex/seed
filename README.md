# seed

A static-first web framework. HTML fragments get compiled into a shared
shell. APIs are auto-discovered FastAPI routers. Claude maintains its
own documentation via an auto-indexed `CLAUDE.md` tree.

Good for: marketing sites, dashboards, small SaaS, internal tools,
client work where you want a proven shape without a heavyweight
framework.

## Quickstart

```bash
git clone https://github.com/Volcanex/seed.git my-site
cd my-site
pip install -r requirements.txt

python3 compile.py          # Build pages into output/
python3 server.py           # Serve on http://localhost:8080
```

Open `http://localhost:8080/` — the home page is served from
`pages/home/`. Visit `/api/_routes` to see every mounted endpoint.

### With Docker

Two modes, one compose file. Pick the one that matches your host.

**Behind an existing reverse proxy** (host nginx, Cloudflare tunnel, etc.):

```bash
cp .env.example .env
# set HOST_PORT to a free loopback port, e.g. 5002
docker compose up -d
```

The app binds to `127.0.0.1:${HOST_PORT}`. Point your reverse proxy at
that. Nothing is exposed to the public internet directly.

**Standalone** (this container owns 80/443, automatic Let's Encrypt
TLS via Caddy):

```bash
cp .env.example .env
# set DOMAIN=yourdomain.com and EMAIL=you@example.com
docker compose --profile standalone up -d
```

**Dev mode** (live source mounting + uvicorn `--reload`):

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
docker compose up -d
```

Compose auto-merges the override; edits to `pages/`, `core/`, and
`server.py` take effect without a rebuild.

## Layout

```
CLAUDE.md              — Root project docs (auto-indexed)
server.py              — FastAPI; auto-discovers api.py files
compile.py             — Builds pages/* into output/*.html
core/
  templates/shell.html — Shared HTML shell (wraps every page)
  static/base.css      — Baseline CSS; copied to output/css/
pages/
  home/config.json     — Page metadata
  home/content.html    — Page body fragment
  hello/api.py         — Example auto-mounted router
scripts/
  compile_docs.py      — Rebuilds CLAUDE.md auto-index
.claude/
  rules/               — Path-scoped rules (auto-activate in Claude Code)
  commands/            — Slash commands (/new-page, /new-api, /compile)
tests/test_smoke.py    — pytest smoke suite
Dockerfile, docker-compose.yml, Caddyfile
```

## Conventions

**Pages.** Each page is `pages/{slug}/` with `config.json` + `content.html`.
Optionally `api.py` (auto-mounted at `/api/{slug}`). Optionally
`CLAUDE.md` (indexed automatically).

**APIs.** Any `*.py` that exports `router = APIRouter()` is found and
mounted at startup. See `.claude/rules/api-conventions.md`.

**Docs.** Every non-obvious directory gets a `CLAUDE.md`. No other `.md`
files. Root `CLAUDE.md` holds an auto-generated index between
`<!-- DOCS:START -->` and `<!-- DOCS:END -->`. Run
`python3 scripts/compile_docs.py` after edits.

## Extending

When a project grows to host multiple independent products on one infra,
introduce top-level product directories alongside `pages/` (see root
`CLAUDE.md` for the core/product split). Most projects never need this —
start without it.

## Why this exists

Three separate web projects I was running all converged on the same shape:
`pages/{slug}/{config.json, content.html}` + an auto-router FastAPI/Flask
server + a compile step for HTML. This repo is that shape, distilled, so
future projects start from something already proven.

The Claude docs system (auto-indexed `CLAUDE.md` files + path-scoped rules)
is the other half — it means Claude stays oriented as the project grows,
without anyone hand-writing an onboarding doc that rots.

## License

MIT — see `LICENSE`.
