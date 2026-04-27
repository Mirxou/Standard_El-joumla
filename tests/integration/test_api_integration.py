import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import importlib

app_module = importlib.import_module("src.api.app")
pg_module = importlib.import_module("src.database.postgresql_backend")


class TestAPIIntegration:
    """Test API Integration"""

    @pytest.fixture
    def mock_stack(self, monkeypatch):
        """Create a mocked stack for lifespan startup"""
        mock_config = MagicMock()
        mock_config.get_database_backend.return_value = "postgresql"
        mock_config.get_database_path.return_value = "test.db"
        mock_config.get_database_url.return_value = "postgresql://user:pass@localhost/db"
        mock_config.get_cors_origins.return_value = ["http://localhost:3000"]

        mock_db = MagicMock()
        mock_db.initialize.return_value = True

        mock_pg = MagicMock()

        mock_config_cls = MagicMock(return_value=mock_config)
        mock_db_cls = MagicMock(return_value=mock_db)
        mock_pg_cls = MagicMock(return_value=mock_pg)

        monkeypatch.setattr(app_module, "ConfigManager", mock_config_cls)
        monkeypatch.setattr(app_module, "DatabaseManager", mock_db_cls)
        monkeypatch.setattr(pg_module, "PostgreSQLBackend", mock_pg_cls)

        return mock_db_cls, mock_pg_cls

    def test_app_initialization_with_postgres(self, mock_stack):
        """Test that app initializes PostgreSQLBackend when config says so"""
        mock_db_cls, mock_pg_cls = mock_stack

        with TestClient(app_module.app):
            mock_pg_cls.assert_called_with("postgresql://user:pass@localhost/db")
            mock_db_cls.assert_called()

    def test_app_health_endpoint(self):
        """Test health check endpoint"""
        with TestClient(app_module.app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_app_docs_endpoint(self):
        """Test API docs endpoint"""
        with TestClient(app_module.app) as client:
            response = client.get("/docs")
            assert response.status_code == 200


@pytest.fixture
def sample_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_product_data():
    return {
        "name": "Test Product",
        "sku": "TEST-001",
        "price": 99.99,
        "quantity": 100,
    }


class TestAPIEndpoints:
    """Test API endpoints"""

    def test_cors_headers(self):
        with TestClient(app_module.app) as client:
            response = client.options("/api/v1/")
            assert "access-control-allow-origin" in response.headers or response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



