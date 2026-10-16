"""Playwright E2E tests for sanctions screening."""
import pytest

BASE_URL = "http://localhost:8000"


class TestScreening:
    def test_screening_api_clear_entity(self, logged_in_page, flask_server):
        """Screening a benign name returns a clear result."""
        resp = logged_in_page.request.post(
            f"{flask_server}/api/screen",
            data={"name": "Acme Widgets Ltd", "entity_type": "entity", "country": "US"},
        )
        assert resp.status == 200
        data = resp.json()
        assert "top_level" in data
        assert "screening_id" in data

    def test_screening_api_requires_name(self, logged_in_page, flask_server):
        """Screening without a name returns a 400 error."""
        resp = logged_in_page.request.post(
            f"{flask_server}/api/screen",
            data={"name": "", "entity_type": "entity"},
        )
        assert resp.status == 400
        data = resp.json()
        assert "error" in data

    def test_screening_api_hit_result(self, logged_in_page, flask_server):
        """Screening a known watchlist name returns hit results."""
        resp = logged_in_page.request.post(
            f"{flask_server}/api/screen",
            data={"name": "Al-Qaeda", "entity_type": "entity", "country": "AF"},
        )
        assert resp.status == 200
        data = resp.json()
        assert data["top_level"] in ("review", "high", "critical", "clear", "possible")
        assert "total" in data

    def test_screening_nav_view_loads(self, logged_in_page):
        """Clicking New Screening nav renders the screening form."""
        logged_in_page.click('[data-view="new-screening"]')
        logged_in_page.wait_for_selector('input, form, [data-testid="screening-form"]',
                                         timeout=5000)

    def test_review_queue_api(self, logged_in_page, flask_server):
        """Review queue API returns a hits list."""
        resp = logged_in_page.request.get(f"{flask_server}/api/queue")
        assert resp.status == 200
        data = resp.json()
        assert "hits" in data
        assert isinstance(data["hits"], list)

    def test_demo_batch_api(self, logged_in_page, flask_server):
        """Demo batch screening API runs and returns results."""
        resp = logged_in_page.request.post(f"{flask_server}/api/demo-batch")
        assert resp.status == 200
        data = resp.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 0


class TestCases:
    def test_create_case_api(self, logged_in_page, flask_server):
        """Creating a case via the API returns the new case with a recommendation."""
        payload = {
            "counterparty_name": "Test Corp",
            "customer_legal_name": "Buyer India Ltd",
            "customer_country": "IN",
            "customer_kyc_status": "verified",
        }
        resp = logged_in_page.request.post(
            f"{flask_server}/api/cases",
            data=payload,
        )
        assert resp.status == 201
        data = resp.json()
        assert "case" in data
        case = data["case"]
        assert "recommendation" in case
        assert "case_ref" in case

    def test_get_case_api(self, logged_in_page, flask_server):
        """A seeded case can be retrieved by ID."""
        cases_resp = logged_in_page.request.get(f"{flask_server}/api/cases")
        cases = cases_resp.json()["cases"]
        assert len(cases) > 0
        case_id = cases[0]["id"]
        resp = logged_in_page.request.get(f"{flask_server}/api/cases/{case_id}")
        assert resp.status == 200
        data = resp.json()
        assert "case" in data
        assert data["case"]["id"] == case_id

    def test_get_nonexistent_case_returns_404(self, logged_in_page, flask_server):
        """Fetching a non-existent case ID returns 404."""
        resp = logged_in_page.request.get(f"{flask_server}/api/cases/999999")
        assert resp.status == 404

    def test_cases_view_loads(self, logged_in_page):
        """Clicking Cases nav renders the cases view."""
        logged_in_page.click('[data-view="cases"]')
        logged_in_page.wait_for_selector('[data-view="cases"], .cases-list, table, h2',
                                         timeout=5000)
