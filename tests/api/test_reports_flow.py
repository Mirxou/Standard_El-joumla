import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from unittest.mock import MagicMock

client = TestClient(app)

class TestReportsFlow:
    @pytest.fixture
    def mock_report_manager(self):
        manager = MagicMock()
        manager.get_financial_summary.return_value = {
            "total_sales": 1000,
            "net_profit": 500
        }
        manager.get_sales_trends.return_value = []
        manager.get_top_products.return_value = []
        manager.get_inventory_analytics.return_value = {}
        return manager

    def test_financial_summary_endpoint(self, mock_report_manager):
        from src.api.routes import get_report_manager, get_current_user
        
        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}

        try:
            response = client.get("/api/v1/reports/financial")
            assert response.status_code == 200
            data = response.json()
            assert data["total_sales"] == 1000
        finally:
            app.dependency_overrides = {}

    def test_sales_trends_endpoint(self, mock_report_manager):
        from src.api.routes import get_report_manager, get_current_user

        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}

        try:
            response = client.get("/api/v1/reports/charts/sales?days=30")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides = {}

    def test_inventory_analytics_endpoint(self, mock_report_manager):
        from src.api.routes import get_report_manager, get_current_user

        app.dependency_overrides[get_report_manager] = lambda: mock_report_manager
        app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}

        try:
            response = client.get("/api/v1/reports/analytics/inventory")
            assert response.status_code == 200
            assert isinstance(response.json(), dict)
        finally:
            app.dependency_overrides = {}
