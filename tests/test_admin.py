"""Smoke tests for the admin auth extraction.

Covers: cookie set on correct password, gate redirect, verify endpoint,
helper exports. Doesn't cover the test runner endpoint (which would
shell out to pytest itself).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def compile_pages():
    result = subprocess.run(
        [sys.executable, "compile.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"compile.py failed:\n{result.stderr}"


@pytest.fixture(scope="module")
def client():
    os.environ["ADMIN_PASSWORD"] = "test-pw"
    sys.path.insert(0, str(PROJECT_ROOT))
    from server import app  # noqa: E402
    return TestClient(app)


def test_admin_endpoints_mounted(client):
    """The admin module must auto-discover and expose its endpoints."""
    r = client.get("/api/_routes")
    assert r.status_code == 200
    paths = {route["path"] for route in r.json()["routes"]}
    assert "/api/admin/login" in paths
    assert "/api/admin/logout" in paths
    assert "/api/admin/verify" in paths


def test_verify_default_is_logged_out(client):
    r = client.get("/api/admin/verify")
    assert r.status_code == 200
    assert r.json() == {"admin": False}


def test_login_wrong_password_rejected(client):
    r = client.post("/api/admin/login", json={"password": "wrong"})
    assert r.status_code == 401


def test_login_sets_cookie_and_verify_flips(client):
    r = client.post("/api/admin/login", json={"password": "test-pw"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    r2 = client.get("/api/admin/verify")
    assert r2.json() == {"admin": True}

    # Logout clears it
    r3 = client.post("/api/admin/logout")
    assert r3.status_code == 200
    r4 = client.get("/api/admin/verify")
    assert r4.json() == {"admin": False}


def test_admin_path_redirects_when_logged_out(client):
    """Hitting any /admin/* path without the cookie should 302 to login.
    The login page itself is exempt."""
    r = client.get("/admin", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/admin/login"

    r2 = client.get("/admin/dashboard", follow_redirects=False)
    assert r2.status_code == 302


def test_admin_login_path_is_public(client):
    """The /admin/login page must NOT redirect (otherwise infinite loop)."""
    # Compiled output has no /admin/login page in the bare seed, so we
    # expect a 404 — but crucially NOT a 302 redirect to itself.
    r = client.get("/admin/login", follow_redirects=False)
    assert r.status_code != 302
