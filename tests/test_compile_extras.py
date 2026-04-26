"""Smoke tests for the compile.py extensions:

- token registry (`<!-- seed:NAME -->` → renderer)
- slug-with-slashes (`output/admin/foo.html`)
- body_class interpolation
- manifest auto-stub generator

These tests work against the live compile.py without subprocessing —
they import it and call functions directly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _fresh_compile_module():
    """Reload compile so the token registry is empty between tests."""
    for mod_name in list(sys.modules):
        if mod_name == "compile":
            del sys.modules[mod_name]
    import importlib.util
    spec = importlib.util.spec_from_file_location("compile", PROJECT_ROOT / "compile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_token_registry_expands_seed_tokens():
    mod = _fresh_compile_module()
    mod.register_token("greeting", lambda ctx: f"Hello, {ctx['title']}!")

    out = mod.expand_seed_tokens(
        "<p>before</p><!-- seed:greeting --><p>after</p>",
        {"title": "World"},
    )
    assert out == "<p>before</p>Hello, World!<p>after</p>"


def test_token_registry_leaves_unknown_tokens_alone():
    mod = _fresh_compile_module()
    out = mod.expand_seed_tokens("<!-- seed:unknown -->", {})
    assert out == "<!-- seed:unknown -->"


def test_slug_with_slashes_writes_nested_html(tmp_path, monkeypatch):
    """A slug like 'admin/foo' should write to output/admin/foo.html."""
    mod = _fresh_compile_module()
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")

    page_dir = tmp_path / "p"
    page_dir.mkdir()
    (page_dir / "config.json").write_text(json.dumps({
        "title": "Foo",
        "slug": "admin/foo",
    }))
    (page_dir / "content.html").write_text("<h1>Foo</h1>")

    shell = "<html><body>{{ content }}</body></html>"
    out, _ = mod.compile_page(page_dir, shell)
    assert out is not None
    assert out == tmp_path / "output" / "admin" / "foo.html"
    assert out.is_file()
    assert "<h1>Foo</h1>" in out.read_text()


def test_body_class_token_interpolates_into_shell(tmp_path, monkeypatch):
    mod = _fresh_compile_module()
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")

    page_dir = tmp_path / "p"
    page_dir.mkdir()
    (page_dir / "config.json").write_text(json.dumps({
        "title": "Cls",
        "body_class": "is-special",
    }))
    (page_dir / "content.html").write_text("body")

    shell = '<html><body class="{{ body_class }}">{{ content }}</body></html>'
    out, _ = mod.compile_page(page_dir, shell)
    html = out.read_text()
    assert 'class="is-special"' in html


def test_manifest_auto_stub_emits_pages_for_unhandled_items(tmp_path, monkeypatch):
    mod = _fresh_compile_module()

    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "items": [
            {"slug": "alpha", "title": "Alpha", "description": "First."},
            {"slug": "beta",  "title": "Beta",  "description": "Second."},
        ]
    }))
    monkeypatch.setenv("SEED_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("SEED_MANIFEST_PREFIX", "thing")

    shell = "<html><body class=\"{{ body_class }}\">{{ content }}</body></html>"
    handled: set[str] = set()  # nothing hand-written
    n = mod.emit_manifest_stubs(shell, handled)

    assert n == 2
    assert (tmp_path / "output" / "thing-alpha.html").is_file()
    assert (tmp_path / "output" / "thing-beta.html").is_file()
    text = (tmp_path / "output" / "thing-alpha.html").read_text()
    assert "Alpha" in text
    assert "is-stub" in text


def test_manifest_auto_stub_skips_handled_slugs(tmp_path, monkeypatch):
    mod = _fresh_compile_module()
    monkeypatch.setattr(mod, "OUTPUT_DIR", tmp_path / "output")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"items": [{"slug": "x", "title": "X"}]}))
    monkeypatch.setenv("SEED_MANIFEST_PATH", str(manifest_path))
    monkeypatch.setenv("SEED_MANIFEST_PREFIX", "p")

    # If the page slug was already handled by a hand-written page, skip it.
    n = mod.emit_manifest_stubs("<html>{{ content }}</html>", {"p-x"})
    assert n == 0
