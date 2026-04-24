#!/usr/bin/env python3
"""
Seed framework — FastAPI with page+router auto-discovery.

Two conventions drive the server:

1. Pages live at `pages/{slug}/content.html` + `pages/{slug}/config.json`.
   `compile.py` walks these and emits `output/{slug}.html` wrapped in
   `core/templates/shell.html`. The server serves `output/` as static.

2. API routers live at `pages/{slug}/api.py` (or `core/api/*.py`, or any
   `*/api/*.py`). Each file must export `router = APIRouter()`. Discovery
   scans the tree at startup and mounts each router at a path derived from
   its file location. No manual registration.
"""

import importlib.util
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"

_discovered: list[dict] = []


def _mount_router(app: FastAPI, py_file: Path, prefix: str, group: str) -> None:
    module_name = f"{group}.{py_file.stem}".replace("/", ".")
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        print(f"  ✗ {py_file.relative_to(PROJECT_ROOT)}: could not load")
        return

    module = importlib.util.module_from_spec(spec)
    parent = str(py_file.parent.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f"  ✗ {py_file.relative_to(PROJECT_ROOT)}: {exc}")
        return

    router = getattr(module, "router", None)
    if router is None:
        print(f"  ⚠ {py_file.relative_to(PROJECT_ROOT)}: no `router` exported")
        return

    app.include_router(router, prefix=prefix)
    _discovered.append({"file": str(py_file.relative_to(PROJECT_ROOT)), "prefix": prefix})
    print(f"  ✓ {prefix}  ←  {py_file.relative_to(PROJECT_ROOT)}")


def discover_apis(app: FastAPI) -> None:
    """
    Mount all API routers found in the repo.

    Conventions (in order):
    - `core/api/{name}.py`       → `/api/{name}`
    - `pages/{slug}/api.py`      → `/api/{slug}`
    - `{anything}/api/{name}.py` → `/api/{anything}/{name}`

    `{anything}` in the third form is the directory name — this is the
    "core/product split" escape hatch. One top-level product by default
    (`pages/`); add more top-level dirs only when you truly need isolation.
    """
    # core/api/*.py → /api/*
    core_api = PROJECT_ROOT / "core" / "api"
    if core_api.is_dir():
        for py in sorted(core_api.glob("*.py")):
            if py.name.startswith("_"):
                continue
            _mount_router(app, py, f"/api/{py.stem}", "core.api")

    # pages/{slug}/api.py → /api/{slug}
    pages_dir = PROJECT_ROOT / "pages"
    if pages_dir.is_dir():
        for api_py in sorted(pages_dir.glob("*/api.py")):
            slug = api_py.parent.name
            _mount_router(app, api_py, f"/api/{slug}", f"pages.{slug}")

    # Any other top-level */api/*.py → /api/{top}/{name}
    for top in sorted(PROJECT_ROOT.iterdir()):
        if not top.is_dir() or top.name in {"core", "pages", "output", "tests", "scripts", ".git", ".claude", "static"}:
            continue
        api_dir = top / "api"
        if not api_dir.is_dir():
            continue
        for py in sorted(api_dir.glob("*.py")):
            if py.name.startswith("_"):
                continue
            _mount_router(app, py, f"/api/{top.name}/{py.stem}", f"{top.name}.api")


app = FastAPI(
    title="Seed",
    description="Static-first site framework with FastAPI routers.",
    version="0.1.0",
)


print("Discovering APIs...")
discover_apis(app)
print()


@app.get("/api/_health", tags=["system"])
async def health():
    return {"status": "ok"}


@app.get("/api/_routes", tags=["system"])
async def routes():
    """List discovered routers and all mounted routes. Handy for sanity checks."""
    all_routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path") and route.path.startswith("/api/"):
            all_routes.append({
                "path": route.path,
                "methods": sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"}),
            })
    return {"discovered": _discovered, "routes": sorted(all_routes, key=lambda r: r["path"])}


# Static assets compiled by compile.py (CSS, JS, images)
if OUTPUT_DIR.exists():
    for sub in ("css", "js", "assets"):
        p = OUTPUT_DIR / sub
        if p.is_dir():
            app.mount(f"/{sub}", StaticFiles(directory=p), name=sub)


@app.get("/{path:path}", include_in_schema=False)
async def serve_pages(path: str):
    """Serve compiled HTML pages with clean URLs."""
    if path.startswith("api/"):
        return JSONResponse({"error": "not found"}, status_code=404)

    if path in ("", "/"):
        index = OUTPUT_DIR / "home.html"
        if index.is_file():
            return FileResponse(index)
        return HTMLResponse(_placeholder_home(), status_code=200)

    # Direct file match
    file_path = OUTPUT_DIR / path
    if file_path.is_file():
        return FileResponse(file_path)

    # Slug → output/{slug}.html
    slug_html = OUTPUT_DIR / f"{path}.html"
    if slug_html.is_file():
        return FileResponse(slug_html)

    # Directory index
    index_html = OUTPUT_DIR / path / "index.html"
    if index_html.is_file():
        return FileResponse(index_html)

    return HTMLResponse(_placeholder_404(path), status_code=404)


def _placeholder_home() -> str:
    return (
        "<!doctype html><title>Seed</title>"
        "<h1>Seed is running, but nothing is compiled yet.</h1>"
        "<p>Run <code>python3 compile.py</code> to build pages.</p>"
    )


def _placeholder_404(path: str) -> str:
    from html import escape
    return (
        "<!doctype html><title>Not found</title>"
        f"<h1>404</h1><p><code>/{escape(path)}</code> does not exist.</p>"
        "<p><a href=\"/\">Home</a></p>"
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    reload_flag = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=reload_flag)
