#!/usr/bin/env python3
"""
Page compiler — walks `pages/` and writes `output/{slug}.html`.

Each page is a directory under `pages/` with:
- `config.json` — at minimum `{"title": "..."}`. Optional: `description`,
  `slug`, `body_class`, `nav`, `order`, anything else your shell.html
  wants to interpolate.
- `content.html` — HTML fragment for the page body. May include a
  `<style>` block.

The fragment is inserted into `core/templates/shell.html` at the
`{{ content }}` placeholder. `{{ title }}` and any other `{{ key }}`
tokens found in the shell are filled from config.json, falling back to
sensible defaults.

Also copies `core/static/*` into `output/css|js|assets` so the server
can mount them as static.

## Slug-with-slashes

If `config.json` sets a slug like `"admin/audits"`, this compiler writes
`output/admin/audits.html` (parent directories are auto-created). Combined
with the tree-walk fallback in `server.py`, this means a single compiled
HTML can serve every `/<prefix>/<dynamic>` URL — no per-slug page needed.

## Token registry

`<!-- seed:NAME -->` markers in content.html are replaced by registered
renderers before the content is spliced into the shell. Register your
own with `register_token("NAME", lambda ctx: "...")` from a project
hook (most projects don't need this).

## Manifest auto-stub

If `data/manifest.json` exists with shape
`{"items": [{"slug": "...", "title": "..."}]}`, this compiler emits a
default page for every entry that has no hand-written
`pages/{prefix}-{slug}/` directory. Configure via env vars:

  SEED_MANIFEST_PATH       (default: data/manifest.json)
  SEED_MANIFEST_PREFIX     (default: item)        # so item-{slug}.html
  SEED_MANIFEST_TEMPLATE   (default: stub.html)   # under core/templates/

Usage: python3 compile.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parent
PAGES_DIR = PROJECT_ROOT / "pages"
OUTPUT_DIR = PROJECT_ROOT / "output"
SHELL_PATH = PROJECT_ROOT / "core" / "templates" / "shell.html"
STATIC_SRC = PROJECT_ROOT / "core" / "static"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "core" / "templates"

DEFAULTS = {
    "title": "Untitled",
    "description": "",
    "site_name": "Seed",
    "body_class": "",
}

TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

# Token registry: `<!-- seed:NAME -->` → renderer(context) -> str.
# Projects extend this by importing `register_token` from compile and
# calling it before main() runs (e.g. from a project-level hook).
SEED_TOKEN_RE = re.compile(r"<!--\s*seed:([a-zA-Z0-9_-]+)\s*-->")
_TOKEN_REGISTRY: dict[str, Callable[[dict], str]] = {}


def register_token(name: str, renderer: Callable[[dict], str]) -> None:
    """Register a `<!-- seed:NAME -->` content token. The renderer is
    called once per page and receives the page's render context dict.
    Last registration wins (idempotent override is fine)."""
    _TOKEN_REGISTRY[name] = renderer


def expand_seed_tokens(content: str, context: dict) -> str:
    if not _TOKEN_REGISTRY:
        return content

    def sub(match: re.Match) -> str:
        name = match.group(1)
        renderer = _TOKEN_REGISTRY.get(name)
        if renderer is None:
            return match.group(0)
        try:
            return renderer(context) or ""
        except Exception as exc:  # pragma: no cover — fail loud, keep building
            print(f"  ⚠ token `{name}` raised: {exc}")
            return match.group(0)

    return SEED_TOKEN_RE.sub(sub, content)


def load_shell() -> str:
    if not SHELL_PATH.is_file():
        sys.exit(f"ERROR: shell template not found at {SHELL_PATH}")
    return SHELL_PATH.read_text(encoding="utf-8")


def render(template: str, context: dict) -> str:
    def sub(match: re.Match) -> str:
        key = match.group(1)
        return str(context.get(key, match.group(0)))
    return TOKEN_RE.sub(sub, template)


def compile_page(page_dir: Path, shell: str) -> tuple[Path | None, dict | None]:
    config_file = page_dir / "config.json"
    content_file = page_dir / "content.html"
    if not (config_file.is_file() and content_file.is_file()):
        print(f"  · {page_dir.name}: skipped (missing config.json or content.html)")
        return None, None

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  ✗ {page_dir.name}: invalid config.json — {exc}")
        return None, None

    content = content_file.read_text(encoding="utf-8")
    slug = config.get("slug", page_dir.name)

    context = {**DEFAULTS, **{k: v for k, v in config.items() if isinstance(v, (str, int, float))}}
    context["slug"] = slug

    # Expand seed:* tokens before splicing into the shell so registered
    # renderers can produce HTML the shell template doesn't know about.
    content = expand_seed_tokens(content, context)
    context["content"] = content

    html = render(shell, context)
    out_path = OUTPUT_DIR / f"{slug}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)  # supports slug-with-slashes
    out_path.write_text(html, encoding="utf-8")
    try:
        rel = out_path.relative_to(PROJECT_ROOT)
    except ValueError:
        rel = out_path
    print(f"  ✓ {slug:<28}  →  {rel}")
    return out_path, config


def copy_static() -> int:
    if not STATIC_SRC.is_dir():
        return 0
    count = 0
    for src in STATIC_SRC.rglob("*"):
        if src.is_file():
            rel = src.relative_to(STATIC_SRC)
            dst = OUTPUT_DIR / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
    return count


# ---------- Manifest auto-stub --------------------------------------------

DEFAULT_STUB_BODY = (
    '<article class="seed-stub">'
    '<h1>{title}</h1>'
    '<p>{description}</p>'
    '<p><em>This page was auto-generated from <code>data/manifest.json</code>. '
    'Add a hand-written <code>pages/{prefix}-{slug}/</code> directory to override.</em></p>'
    '</article>'
)


def load_manifest() -> dict:
    path = Path(os.environ.get("SEED_MANIFEST_PATH") or str(DATA_DIR / "manifest.json"))
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def emit_manifest_stubs(shell: str, handled_slugs: set[str]) -> int:
    manifest = load_manifest()
    if not manifest:
        return 0
    items = manifest.get("items") or manifest.get("entries") or []
    if not items:
        return 0

    prefix = os.environ.get("SEED_MANIFEST_PREFIX", "item")
    template_name = os.environ.get("SEED_MANIFEST_TEMPLATE", "stub.html")
    template_path = TEMPLATES_DIR / template_name
    template = (
        template_path.read_text(encoding="utf-8")
        if template_path.is_file()
        else DEFAULT_STUB_BODY
    )

    built = 0
    for item in items:
        slug = item.get("slug")
        page_slug = f"{prefix}-{slug}"
        if not slug or page_slug in handled_slugs or slug in handled_slugs:
            continue
        body = template.format(
            slug=slug,
            prefix=prefix,
            title=item.get("title", slug),
            description=item.get("description", ""),
        )
        ctx = {
            **DEFAULTS,
            "title": item.get("title", slug),
            "description": item.get("description", ""),
            "slug": page_slug,
            "body_class": "is-stub",
            "content": body,
        }
        out_path = OUTPUT_DIR / f"{page_slug}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render(shell, ctx), encoding="utf-8")
        built += 1
    return built


def main() -> None:
    if not PAGES_DIR.is_dir():
        sys.exit(f"ERROR: {PAGES_DIR} not found")

    OUTPUT_DIR.mkdir(exist_ok=True)
    shell = load_shell()

    print("Compiling pages...")
    built = 0
    handled: set[str] = set()
    for page_dir in sorted(PAGES_DIR.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        out, config = compile_page(page_dir, shell)
        if out:
            built += 1
        if config:
            handled.add(config.get("slug", page_dir.name))

    stub_built = emit_manifest_stubs(shell, handled)
    if stub_built:
        print(f"  + {stub_built} stub page(s) auto-emitted from manifest")

    print()
    static_count = copy_static()
    if static_count:
        print(f"Copied {static_count} static file(s) from {STATIC_SRC.relative_to(PROJECT_ROOT)} → output/")
    print(f"Done. {built} page(s) compiled.")


if __name__ == "__main__":
    main()
