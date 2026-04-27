import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys

# Mock dependencies
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()

from src.api.app import app, auth_manager
from src.api.routes import get_current_user
from src.core.database_manager import DatabaseManager

# Mock Auth to bypass FastAPI dependency injection
async def mock_get_current_user():
    return {"id": 1, "username": "testuser", "role_id": 1}

app.dependency_overrides[get_current_user] = mock_get_current_user

# Mock user data returned from auth_manager DB lookup
_MOCK_USER = {
    "user_id": 1,
    "username": "admin",
    "full_name": "Admin User",
    "role_id": 1,
    "company_id": 1,
    "is_active": True
}

_MOCK_PAYLOAD = {
    "sub": "1",
    "username": "admin",
    "company_id": 1,
    "role": "admin"
}


@pytest.fixture(autouse=True)
def mock_auth():
    """تعطيل التحقق من JWT وDB lookup للمصادقة"""
    with patch.object(auth_manager, 'verify_token', return_value=_MOCK_PAYLOAD), \
         patch.object(auth_manager, 'get_current_user', return_value=_MOCK_USER):
        yield


@pytest.fixture(autouse=True)
def mock_db_init():
    with patch('src.core.database_manager.DatabaseManager.initialize', return_value=True):
        yield


class TestSyncAPI:

    def test_handshake(self):
        with TestClient(app) as client:
            response = client.get(
                "/api/v1/sync/handshake",
                headers={"Authorization": "Bearer test"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "server_time" in data
            assert "status" in data
            assert data["status"] == "ready"

    def test_delta_sync(self):
        """اختبار /sync/delta - يستخدم المعامل last_synced"""
        mock_db = MagicMock()

        from src.api.routes import get_db_manager
        app.dependency_overrides[get_db_manager] = lambda: mock_db

        def side_effect(query, params=None):
            if "PRAGMA table_info" in query:
                return [(0, "id", "INTEGER", 0, None, 1),
                        (1, "name", "TEXT", 0, None, 0),
                        (2, "updated_at", "TIMESTAMP", 0, None, 0)]
            if "products" in str(query):
                return [("1", "Product A", "2023-01-01")]
            return []

        mock_db.fetch_all.side_effect = side_effect

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/api/v1/sync/delta?last_synced=2023-01-01T00:00:00",
                    headers={"Authorization": "Bearer test"}
                )
                assert response.status_code == 200
                items = response.json()["items"]
                assert len(items) > 0
                assert items[0]["table_name"] in ["products", "customers", "sales"]
        finally:
            from src.api.routes import get_db_manager
            if get_db_manager in app.dependency_overrides:
                del app.dependency_overrides[get_db_manager]

    def test_push_sync(self):
        """اختبار /sync/push - يتوقع table_name + items"""
        mock_db = MagicMock()
        from src.api.routes import get_db_manager
        app.dependency_overrides[get_db_manager] = lambda: mock_db

        mock_db.fetch_all.return_value = [
            (0, "id", "INTEGER", 0, None, 1),
            (1, "name", "TEXT", 0, None, 0)
        ]
        mock_db.execute_insert.return_value = 101

        payload = {
            "table_name": "products",
            "items": [{"name": "New Product"}]
        }

        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/sync/push",
                    json=payload,
                    headers={"Authorization": "Bearer test"}
                )
                assert response.status_code == 200
        finally:
            from src.api.routes import get_db_manager
            if get_db_manager in app.dependency_overrides:
                del app.dependency_overrides[get_db_manager]


if __name__ == "__main__":
    pass
