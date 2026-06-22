"""Smoke tests — verify the core framework wires up."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def compile_pages():
    result = subprocess.run(
        [sys.executable, "compile.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"compile.py failed:\n{result.stderr}"


@pytest.fixture(scope="session")
def client():
    sys.path.insert(0, str(PROJECT_ROOT))
    from server import app
    return TestClient(app)


def test_health(client):
    r = client.get("/api/_health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_routes_index_lists_app_routes(client):
    r = client.get("/api/_routes")
    assert r.status_code == 200
    paths = [route["path"] for route in r.json()["routes"]]
    assert "/api/map" in paths
    assert "/api/value/identify" in paths


def test_map_api(client):
    r = client.get("/api/map")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_home_page_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "<title>Home" in body
    assert "apparel" in body


def test_map_page_renders(client):
    r = client.get("/map")
    assert r.status_code == 200
    assert "map" in r.text.lower()


def test_value_page_renders(client):
    r = client.get("/value")
    assert r.status_code == 200
    assert "Identify" in r.text


def test_404_on_missing_page(client):
    r = client.get("/definitely-not-a-page")
    assert r.status_code == 404


def test_compile_docs_runs_cleanly():
    result = subprocess.run(
        [sys.executable, "scripts/compile_docs.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"compile_docs.py failed:\n{result.stderr}"

    root = (PROJECT_ROOT / "CLAUDE.md").read_text()
    assert "<!-- DOCS:START -->" in root
    assert "<!-- DOCS:END -->" in root


def test_home_config_is_valid_json():
    for cfg in (PROJECT_ROOT / "pages").glob("*/config.json"):
        data = json.loads(cfg.read_text())
        assert "title" in data, f"{cfg} missing title"
