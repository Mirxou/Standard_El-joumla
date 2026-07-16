from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.app import app, auth_manager  # noqa: F811

client = TestClient(app)


# Mock verify_token for all tests in this file
@pytest.fixture(autouse=True)
def mock_auth():
    auth_manager.verify_token = MagicMock(
        return_value={"sub": "1", "username": "admin", "company_id": 1, "role": "admin"}
    )
    yield
    # No need to reset if it's a mock, but good practice


class TestReportsFlow:
    @pytest.fixture
    def mock_report_manager(self):
        manager = MagicMock()
        manager.get_financial_summary.return_value = {
            "total_sales": 1000,
            "net_profit": 500,
        }
        manager.get_sales_trends.return_value = []
        manager.get_top_products.return_value = []
        manager.get_inventory_analytics.return_value = {}
        return manager

    def test_financial_summary_endpoint(self, mock_report_manager):
        from src.api.routes import get_current_user, get_report_manager

        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {
            "id": 1,
            "username": "admin",
            "role": "admin",
        }

        try:
            auth_manager.verify_token.return_value = {
                "sub": "1",
                "username": "admin",
                "company_id": 1,
                "role": "admin",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            }
            response = client.get("/api/v1/reports/financial", headers={"Authorization": "Bearer test"})
            assert response.status_code == 200
            data = response.json()
            assert data["total_sales"] == 1000
        finally:
            app.dependency_overrides = {}

    def test_sales_trends_endpoint(self, mock_report_manager):
        from src.api.routes import get_current_user, get_report_manager

        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {
            "id": 1,
            "username": "admin",
            "role": "admin",
        }

        try:
            response = client.get(
                "/api/v1/reports/charts/sales?days=30",
                headers={"Authorization": "Bearer test"},
            )
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides = {}

    def test_inventory_analytics_endpoint(self, mock_report_manager):
        from src.api.routes import get_current_user, get_report_manager

        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {
            "id": 1,
            "username": "admin",
            "role": "admin",
        }

        try:
            response = client.get(
                "/api/v1/reports/analytics/inventory",
                headers={"Authorization": "Bearer test"},
            )
            assert response.status_code == 200
            assert isinstance(response.json(), dict)
        finally:
            app.dependency_overrides = {}
