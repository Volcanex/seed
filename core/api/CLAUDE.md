# core/api — shared API routers

Files here are auto-discovered at startup and mounted at `/api/{stem}`.
Each must export `router = APIRouter()`. See
`.claude/rules/api-conventions.md` for the convention; see `server.py`
for the discovery code.

## What's shipped

| File | Mounted at | Purpose |
|---|---|---|
| `admin.py` | `/api/admin` | Cookie-based single-user auth: login / logout / verify, plus a browser-runnable test runner |

## admin.py

Single-user, password-gated. Cookie value is constant ("ok") — the
gate is the password. Configure via env vars:

| Env var | Default | What |
|---|---|---|
| `ADMIN_COOKIE` | `seed_admin` | Cookie name |
| `ADMIN_COOKIE_VALUE` | `ok` | Cookie value (don't change unless you know why) |
| `ADMIN_PASSWORD` | `change-me` | The password. Set this in `.env` for any real deployment. |

Endpoints:

- `POST /api/admin/login` — body `{password}` → sets the cookie on success
- `POST /api/admin/logout` — clears the cookie
- `GET /api/admin/verify` — `{admin: bool}` (used by `nav.js` to swap drawer sections)
- `POST /api/admin/tests/run` — runs `pytest tests/ -v` synchronously and returns the
  exit code + output. Admin-only. Useful as a "re-run the suite from the browser"
  button in your admin UI.

`is_admin(request)` and `require_admin(request)` are exported for other
API modules to gate endpoints. Import from `core.api.admin`.

## How the gate works

`server.py::_admin_gated()` redirects any unauthenticated request to a
path under `/admin` (except `/admin/login`) to `/admin/login`. The
endpoints here are how the frontend toggles that cookie.

When real multi-user auth is needed (multiple humans, external
surfaces, audit logs), upgrade the cookie to a signed token (HMAC) and
introduce a session table — but most internal-only projects never need
to.
