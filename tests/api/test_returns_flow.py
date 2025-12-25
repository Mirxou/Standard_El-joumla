import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.models.return_invoice import ReturnManager
from unittest.mock import MagicMock

client = TestClient(app)

class TestReturnsFlow:
    @pytest.fixture
    def mock_return_manager(self):
        manager = MagicMock()
        manager.create_return.return_value = 123
        manager.list_returns.return_value = []
        return manager

    def test_create_return_endpoint(self, mock_return_manager):
        from src.api.routes import get_return_manager, get_current_user
        
        # Override Dependencies
        app.dependency_overrides[get_return_manager] = lambda: mock_return_manager
        app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}

        try:
            payload = {
                "return_type": "SALE_RETURN",
                "return_reason": "DEFECTIVE",
                "items": [
                    {"product_id": 1, "quantity": 1, "unit_price": 50.0}
                ]
            }

            # Since we are mocking the dependency, the actual DB call is bypassed.
            # This tests the route logic and Pydantic validation.
            response = client.post("/api/v1/returns", json=payload)
            
            # Expect 200 OK because we mocked success
            assert response.status_code == 200
            assert response.json()["id"] == 123
        finally:
            app.dependency_overrides = {}

    def test_get_returns_list(self, mock_return_manager):
        from src.api.routes import get_return_manager, get_current_user

        app.dependency_overrides[get_return_manager] = lambda: mock_return_manager
        app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}

        try:
            response = client.get("/api/v1/returns")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        finally:
            app.dependency_overrides = {}
