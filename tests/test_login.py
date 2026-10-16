"""Playwright E2E tests for login / logout flows."""
import pytest

BASE_URL = "http://localhost:8000"


class TestLoginPage:
    def test_login_page_renders(self, page, flask_server):
        """Login page loads and shows required fields."""
        page.goto(f"{flask_server}/login")
        assert page.title() == "TradePe — Sign In"
        assert page.is_visible("#username")
        assert page.is_visible("#password")
        assert page.is_visible("#btn-signin")

    def test_login_page_shows_brand(self, page, flask_server):
        """TradePe brand text appears on login page."""
        page.goto(f"{flask_server}/login")
        assert "TradePe" in page.inner_text(".logotype")

    def test_login_page_shows_demo_hint(self, page, flask_server):
        """Demo credential hints are shown on the login page."""
        page.goto(f"{flask_server}/login")
        hint = page.inner_text(".demo-hint")
        assert "admin" in hint
        assert "Admin123!" in hint

    def test_unauthenticated_root_redirects_to_login(self, page, flask_server):
        """Visiting / without a session redirects to /login."""
        page.goto(f"{flask_server}/")
        assert "/login" in page.url

    def test_unauthenticated_api_returns_401(self, page, flask_server):
        """API endpoint returns 401 without a session."""
        resp = page.request.get(f"{flask_server}/api/dashboard")
        assert resp.status == 401

    def test_wrong_password_shows_error(self, page, flask_server):
        """Submitting wrong credentials shows an error message."""
        page.goto(f"{flask_server}/login")
        page.fill("#username", "admin")
        page.fill("#password", "wrongpassword")
        page.click("#btn-signin")
        page.wait_for_selector("#login-error")
        error_text = page.inner_text("#login-error")
        assert "Invalid" in error_text

    def test_wrong_username_shows_error(self, page, flask_server):
        """Submitting a non-existent username shows an error message."""
        page.goto(f"{flask_server}/login")
        page.fill("#username", "nonexistent_user")
        page.fill("#password", "Admin123!")
        page.click("#btn-signin")
        page.wait_for_selector("#login-error")
        assert "Invalid" in page.inner_text("#login-error")

    def test_successful_admin_login(self, page, flask_server):
        """Admin credentials log in and redirect to the dashboard."""
        page.goto(f"{flask_server}/login")
        page.fill("#username", "admin")
        page.fill("#password", "Admin123!")
        page.click("#btn-signin")
        page.wait_for_url(f"{flask_server}/")
        assert page.url == f"{flask_server}/"

    def test_successful_analyst_login(self, page, flask_server):
        """Analyst credentials log in and redirect to the dashboard."""
        page.goto(f"{flask_server}/login")
        page.fill("#username", "analyst")
        page.fill("#password", "Analyst123!")
        page.click("#btn-signin")
        page.wait_for_url(f"{flask_server}/")
        assert page.url == f"{flask_server}/"

    def test_already_logged_in_redirects_away_from_login(self, logged_in_page, flask_server):
        """Visiting /login while already authenticated redirects to /."""
        logged_in_page.goto(f"{flask_server}/login")
        assert logged_in_page.url == f"{flask_server}/"

    def test_logout_clears_session(self, logged_in_page, flask_server):
        """Clicking Sign out clears the session and redirects to /login."""
        logged_in_page.click("#btn-logout")
        logged_in_page.wait_for_url(f"{flask_server}/login")
        assert "/login" in logged_in_page.url

    def test_after_logout_cannot_access_dashboard(self, logged_in_page, flask_server):
        """After logout, navigating to / redirects back to /login."""
        logged_in_page.click("#btn-logout")
        logged_in_page.wait_for_url(f"{flask_server}/login")
        logged_in_page.goto(f"{flask_server}/")
        assert "/login" in logged_in_page.url

    def test_header_shows_username_after_login(self, logged_in_page):
        """The header shows the logged-in username after authentication."""
        user_text = logged_in_page.inner_text(".header-user")
        assert "admin" in user_text

    def test_header_shows_admin_badge(self, logged_in_page):
        """Admin role badge is visible in the header for admin users."""
        assert logged_in_page.is_visible(".header-user .env-badge")
