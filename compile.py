#!/usr/bin/env python3
"""
Page compiler — walks `pages/` and writes `output/{slug}.html`.

Each page is a directory under `pages/` with:
- `config.json` — at minimum `{"title": "..."}`. Optional: `description`,
  `nav`, `order`, anything else your shell.html wants to interpolate.
- `content.html` — HTML fragment for the page body. May include a
  `<style>` block.

The fragment is inserted into `core/templates/shell.html` at the
`{{ content }}` placeholder. `{{ title }}` and any other `{{ key }}`
tokens found in the shell are filled from config.json, falling back to
sensible defaults.

Also copies `core/static/*` into `output/css|js|assets` so the server
can mount them as static.

Usage: python3 compile.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PAGES_DIR = PROJECT_ROOT / "pages"
OUTPUT_DIR = PROJECT_ROOT / "output"
SHELL_PATH = PROJECT_ROOT / "core" / "templates" / "shell.html"
STATIC_SRC = PROJECT_ROOT / "core" / "static"

DEFAULTS = {
    "title": "Untitled",
    "description": "",
    "site_name": "Seed",
}

TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def load_shell() -> str:
    if not SHELL_PATH.is_file():
        sys.exit(f"ERROR: shell template not found at {SHELL_PATH}")
    return SHELL_PATH.read_text(encoding="utf-8")


def render(shell: str, context: dict[str, str]) -> str:
    def sub(match: re.Match) -> str:
        key = match.group(1)
        return str(context.get(key, match.group(0)))
    return TOKEN_RE.sub(sub, shell)


def compile_page(page_dir: Path, shell: str) -> Path | None:
    config_file = page_dir / "config.json"
    content_file = page_dir / "content.html"
    if not (config_file.is_file() and content_file.is_file()):
        print(f"  · {page_dir.name}: skipped (missing config.json or content.html)")
        return None

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  ✗ {page_dir.name}: invalid config.json — {exc}")
        return None

    content = content_file.read_text(encoding="utf-8")
    slug = config.get("slug", page_dir.name)

    context = {**DEFAULTS, **{k: v for k, v in config.items() if isinstance(v, (str, int, float))}}
    context["content"] = content
    context["slug"] = slug

    html = render(shell, context)
    out_path = OUTPUT_DIR / f"{slug}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✓ {slug:<20}  →  {out_path.relative_to(PROJECT_ROOT)}")
    return out_path


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


def main() -> None:
    if not PAGES_DIR.is_dir():
        sys.exit(f"ERROR: {PAGES_DIR} not found")

    OUTPUT_DIR.mkdir(exist_ok=True)
    shell = load_shell()

    print("Compiling pages...")
    built = 0
    for page_dir in sorted(PAGES_DIR.iterdir()):
        if not page_dir.is_dir() or page_dir.name.startswith("_"):
            continue
        if compile_page(page_dir, shell):
            built += 1

    print()
    static_count = copy_static()
    if static_count:
        print(f"Copied {static_count} static file(s) from {STATIC_SRC.relative_to(PROJECT_ROOT)} → output/")
    print(f"Done. {built} page(s) compiled.")


if __name__ == "__main__":
    main()
