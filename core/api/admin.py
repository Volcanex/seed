"""Admin auth — single-user, password-gated.

Pair with `_admin_gated()` in `server.py` (which redirects unauthenticated
requests under `/admin/*` to `/admin/login`). This module provides the
matching endpoints:

  POST /api/admin/login    — set the admin cookie if the password matches
  POST /api/admin/logout   — clear the cookie
  GET  /api/admin/verify   — `{admin: bool}` for client-side conditionals
  POST /api/admin/tests/run — run pytest from the browser, admin-gated

Security model: this is a single-user, internal-only gate. Cookie value
is constant ("ok") — the gate is the password. Upgrade to real auth
(HMAC-signed tokens, sessions, multi-user) when a project needs it.

Configure via env vars (also read by `server.py`):

  ADMIN_COOKIE        — cookie name              (default: "seed_admin")
  ADMIN_COOKIE_VALUE  — cookie value             (default: "ok")
  ADMIN_PASSWORD      — required to log in       (default: "change-me")
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

# Reach project root when this module is auto-mounted by importlib —
# it's loaded by file path, not as a package, so relative imports won't
# work. Adding the project root to sys.path lets us import sibling
# packages (e.g. `core.db`) the same way as a normal `python -m` run.
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

router = APIRouter(tags=["admin"])

ADMIN_COOKIE = os.environ.get("ADMIN_COOKIE", "seed_admin")
ADMIN_VALUE = os.environ.get("ADMIN_COOKIE_VALUE", "ok")


def _admin_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", "change-me")


def is_admin(request: Request) -> bool:
    """Public helper — other API modules can import this to gate endpoints."""
    return request.cookies.get(ADMIN_COOKIE) == ADMIN_VALUE


def require_admin(request: Request) -> None:
    """Raise 401 if the request isn't authenticated. For use in endpoints
    that should be admin-only (declare `request: Request` and call this)."""
    if not is_admin(request):
        raise HTTPException(401, "admin only")


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(req: LoginRequest, response: Response):
    if req.password != _admin_password():
        # Constant-ish timing — not a real defence, just polite
        raise HTTPException(401, "wrong password")
    response.set_cookie(
        ADMIN_COOKIE,
        ADMIN_VALUE,
        max_age=60 * 60 * 24 * 30,  # 30 days
        httponly=True,
        samesite="lax",
        secure=False,  # nginx/Caddy terminates TLS; fine for internal use
        path="/",
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(ADMIN_COOKIE, path="/")
    return {"ok": True}


@router.get("/verify")
def verify(request: Request):
    return {"admin": is_admin(request)}


# ---------- Test runner ---------------------------------------------------
#
# Useful in production: lets you re-run the suite from the admin UI after
# pushing a hotfix. Synchronous (pytest takes a few seconds). Returns
# exit code, full output, and duration. Tests should isolate their state
# (e.g. tmp DBs in conftest.py) so this is safe to run against a live
# container.


@router.post("/tests/run")
def run_tests(request: Request):
    require_admin(request)

    project_root = Path(__file__).resolve().parent.parent.parent
    started = time.time()
    try:
        proc = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-v", "--tb=short", "--color=no"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": -1,
            "duration_seconds": time.time() - started,
            "output": (exc.stdout or "") + "\n--- TIMEOUT ---\n" + (exc.stderr or ""),
        }

    duration = time.time() - started
    output = proc.stdout + ("\n--- stderr ---\n" + proc.stderr if proc.stderr else "")
    return {
        "exit_code": proc.returncode,
        "duration_seconds": round(duration, 2),
        "output": output,
    }
