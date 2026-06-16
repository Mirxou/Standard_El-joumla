import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock necessary modules
sys.modules["psycopg2"] = MagicMock()

import sys
from unittest.mock import MagicMock, patch  # noqa: F811

import pytest  # noqa: F811
from fastapi.testclient import TestClient  # noqa: F811

from src.api.app import app
from src.api.auth import JWTAuthManager
from src.core.database_manager import DatabaseManager

# Mock necessary modules
sys.modules["psycopg2"] = MagicMock()

from src.api.app import app  # noqa: F811
from src.api.auth import JWTAuthManager  # noqa: F811
from src.api.routes import get_auth_manager, get_db_manager
from src.core.database_manager import DatabaseManager  # noqa: F811


class TestMobileAuth:

    @pytest.fixture
    def mock_db_manager(self):
        mock = MagicMock(spec=DatabaseManager)
        mock.initialize.return_value = True

        # Mock fetch_one for user lookup
        mock.fetch_one.side_effect = self.db_fetch_one_side_effect

        return mock

    def db_fetch_one_side_effect(self, query, params):
        # Flatten query for easier matching
        query_flat = " ".join(query.split())

        # Mock password lookup - CHECK THIS FIRST
        if "SELECT password_hash, salt FROM users" in query:
            return ("hashed_password", "salt")

        # Mock settings lookup (secret key)
        if "SELECT value FROM settings" in query:
            return ("super-secret-key",)

        # Mock user lookup by username
        if "FROM users" in query and ("username = ?" in query or "username = ?" in query_flat):
            # User found: id=1, username=testuser, name=Test User, role=1, active=1, company=1
            # Based on auth.py: id, username, full_name, role_id, is_active, company_id
            return (1, "testuser", "Test User", 1, 1, 1)

        # Mock user lookup by ID (generic)
        if "from users" in query.lower() and "id = ?" in query.lower():
            return (1, "testuser", "Test User", 1, 1, 1)

        return None

    @pytest.fixture
    def auth_manager(self, mock_db_manager):
        # Create a real AuthManager with the mock DB
        # We need to mock the internal security service verify password to avoid hashing issues
        with patch(
            "src.core.security_service.AdvancedSecurityService.verify_password",
            return_value=True,
        ), patch("src.models.user.UserManager._verify_password", return_value=True):

            manager = JWTAuthManager(mock_db_manager)
            return manager

    @pytest.fixture
    def client(self, mock_db_manager, auth_manager):
        # Override dependencies
        app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
        app.dependency_overrides[get_auth_manager] = lambda: auth_manager

        # Patch the CLASSES so that lifespan instantiates mocks
        with patch("src.api.app.ConfigManager") as MockConfigManager, patch(
            "src.api.app.DatabaseManager"
        ) as MockDatabaseManager, patch(
            "src.core.security_service.AdvancedSecurityService.verify_password",
            return_value=True,
        ), patch(
            "src.models.user.UserManager._verify_password", return_value=True
        ):

            # Setup ConfigManager mock
            mock_config = MockConfigManager.return_value
            mock_config.get_database_path.return_value = ":memory:"
            mock_config.get_database_backend.return_value = "sqlite"
            mock_config.validate_config.return_value = (True, [])

            # Setup DatabaseManager mock (for lifespan)
            mock_db_instance = MockDatabaseManager.return_value
            mock_db_instance.initialize.return_value = True

            # We also need to ensure that the mocked DB manager used in lifespan
            # behaves correctly if it's referenced elsewhere, although we are overriding dependencies for routes.

            with TestClient(app) as c:
                yield c

        # Clean up
        app.dependency_overrides = {}

    def test_login_flow(self, client):
        """Test successful login and token receipt"""
        login_data = {"username": "testuser", "password": "correctpassword"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "testuser"
        assert data["user_id"] == 1

    def test_protected_route_access(self, client):
        """Test accessing a protected route with a valid token"""
        # 1. Login to get token
        login_data = {"username": "testuser", "password": "any"}

        login_res = client.post("/api/v1/auth/login", json=login_data)
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        # 2. Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200, f"Access failed: {response.text}"
        data = response.json()
        assert data["username"] == "testuser"
        assert data["user_id"] == 1

    def test_login_failure(self, client):
        """Test login with wrong credentials (simulated by failing password check)"""
        # Force verify_password to return False for this test using another patch or mock config
        # Since we instantiated auth_manager in the fixture with patches active, we need to modify behavior.
        # It's cleaner to mock the auth_manager.authenticate_user method directly for this specific test case
        # or recreate the override.

        # Strategy: Mock auth_manager.authenticate_user to return None
        with patch.object(
            app.dependency_overrides[get_auth_manager](),
            "authenticate_user",
            return_value=None,
        ):
            login_data = {"username": "testuser", "password": "wrongpassword"}

            response = client.post("/api/v1/auth/login", json=login_data)

            assert response.status_code == 401
            assert "detail" in response.json()

    def test_refresh_token_flow(self, client):
        """Test refreshing an access token"""
        # 1. Login
        login_res = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "pwd"})
        refresh_token = login_res.json()["refresh_token"]

        # 2. Refresh
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
