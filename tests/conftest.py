"""Shared fixtures for Playwright E2E tests."""
import subprocess
import sys
import time
import os
import pytest

BASE_URL = "http://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin123!"
ANALYST_USER = "analyst"
ANALYST_PASS = "Analyst123!"


@pytest.fixture(scope="session", autouse=True)
def flask_server():
    """Start the Flask dev server for the test session."""
    env = os.environ.copy()
    env["FLASK_ENV"] = "testing"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    # Wait for server to become ready
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(f"{BASE_URL}/login", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    yield BASE_URL
    proc.terminate()
    proc.wait()


@pytest.fixture
def logged_in_page(page, flask_server):
    """Return a Playwright page already logged in as admin."""
    page.goto(f"{flask_server}/login")
    page.fill("#username", ADMIN_USER)
    page.fill("#password", ADMIN_PASS)
    page.click("#btn-signin")
    page.wait_for_url(f"{flask_server}/")
    return page
