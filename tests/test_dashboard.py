"""Playwright E2E tests for the dashboard view."""
import pytest

BASE_URL = "http://localhost:8000"


class TestDashboard:
    def test_dashboard_loads_after_login(self, logged_in_page):
        """Dashboard view renders after login."""
        logged_in_page.click('[data-view="dashboard"]')
        logged_in_page.wait_for_selector(".dashboard-grid, .stat-card, h2", timeout=5000)

    def test_dashboard_api_returns_data(self, logged_in_page, flask_server):
        """Dashboard API returns valid JSON with expected keys."""
        resp = logged_in_page.request.get(f"{flask_server}/api/dashboard")
        assert resp.status == 200
        data = resp.json()
        assert "total_cases" in data
        assert "needs_review" in data
        assert "screening_stats" in data

    def test_nav_links_present(self, logged_in_page):
        """All primary nav links are present in the header."""
        nav_labels = ["Dashboard", "New Screening", "Review Queue", "Cases",
                      "Regulatory Updates", "Agents", "Audit Trail"]
        for label in nav_labels:
            assert logged_in_page.is_visible(f'text={label}'), f"Nav link '{label}' not found"

    def test_sign_out_button_visible_in_header(self, logged_in_page):
        """Sign out button is visible in the main app header."""
        assert logged_in_page.is_visible("#btn-logout")

    def test_cases_api_returns_list(self, logged_in_page, flask_server):
        """Cases API returns a list (seeded data expected)."""
        resp = logged_in_page.request.get(f"{flask_server}/api/cases")
        assert resp.status == 200
        data = resp.json()
        assert "cases" in data
        assert isinstance(data["cases"], list)

    def test_regulatory_updates_api(self, logged_in_page, flask_server):
        """Regulatory updates API returns an updates list."""
        resp = logged_in_page.request.get(f"{flask_server}/api/regulatory-updates")
        assert resp.status == 200
        data = resp.json()
        assert "updates" in data

    def test_stats_api(self, logged_in_page, flask_server):
        """Stats API returns screening statistics."""
        resp = logged_in_page.request.get(f"{flask_server}/api/stats")
        assert resp.status == 200
        data = resp.json()
        assert "total" in data

    def test_audit_api(self, logged_in_page, flask_server):
        """Audit trail API returns events list."""
        resp = logged_in_page.request.get(f"{flask_server}/api/audit")
        assert resp.status == 200
        data = resp.json()
        assert "events" in data
        assert isinstance(data["events"], list)
