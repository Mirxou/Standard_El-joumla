from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.api_client import APIClient, HybridDataService


class TestAPIClient:

    @pytest.fixture
    def client(self):
        return APIClient(
            base_url="http://test-api.com",
            timeout=1,
            max_retries=1,
            retry_backoff_factor=0.0,
        )

    @patch("requests.get")
    def test_is_online_success(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert client.is_online(force_check=True) is True
        mock_get.assert_called_with("http://test-api.com/health", timeout=1)

    @patch("requests.get")
    def test_is_online_failure(self, mock_get, client):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        assert client.is_online(force_check=True) is False

    @patch("requests.post")
    @patch("src.api.api_client.APIClient.is_online")
    def test_login_success(self, mock_is_online, mock_post, client):
        mock_is_online.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "fake-token"}
        mock_post.return_value = mock_response

        assert client.login("user", "pass") is True
        assert client.token == "fake-token"

        # Verify Authorization header usage
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer fake-token"

    @patch("requests.post")
    @patch("src.api.api_client.APIClient.is_online")
    def test_login_failure(self, mock_is_online, mock_post, client):
        mock_is_online.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        assert client.login("user", "pass") is False
        assert client.token is None

    @patch("requests.get")
    @patch("src.api.api_client.APIClient.is_online")
    def test_get_success(self, mock_is_online, mock_get, client):
        mock_is_online.return_value = True
        client.token = "valid-token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        result = client.get("data")
        assert result == {"data": "test"}
        mock_get.assert_called_with(
            "http://test-api.com/data",
            params=None,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer valid-token",
            },
            timeout=1,
        )

    @patch("requests.get")
    def test_retry_logic(self, mock_get, client):
        # Simulate failure then success
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"ok": True}

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        # We need to bypass is_online check or make it return True without doing a request
        # But _make_request doesn't call is_online, methods like get/post do.
        # We call _make_request directly to test retry logic

        response = client._make_request("GET", "retry-test")
        assert response.status_code == 200
        assert mock_get.call_count == 2


class TestHybridDataService:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.get_cursor.return_value.__enter__.return_value = MagicMock()
        return db

    @pytest.fixture
    def mock_api(self):
        return MagicMock(spec=APIClient)

    def test_get_products_online(self, mock_db, mock_api):
        service = HybridDataService(mock_db, mock_api)
        mock_api.is_online.return_value = True
        mock_api.get.return_value = {"items": [{"id": 1, "name": "Online Product"}]}

        products = service.get_products()
        assert len(products) == 1
        assert products[0]["name"] == "Online Product"
        mock_db.get_cursor.assert_not_called()

    def test_get_products_offline(self, mock_db, mock_api):
        service = HybridDataService(mock_db, mock_api)
        mock_api.is_online.return_value = False

        cursor = mock_db.get_cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(1, "Offline Product", "123", "pc", 10.0, 5)]
        cursor.description = [
            ("id",),
            ("name",),
            ("barcode",),
            ("unit",),
            ("selling_price",),
            ("current_stock",),
        ]

        products = service.get_products()
        assert len(products) == 1
        assert products[0]["name"] == "Offline Product"
        assert cursor.execute.called

    def test_create_product_sync(self, mock_db, mock_api):
        service = HybridDataService(mock_db, mock_api)
        mock_api.is_online.return_value = True
        mock_api.post.return_value = {"id": 100, "name": "New Prod"}

        # It should call _sync_product_to_local
        # mocking internal method for simplicity or mock db interaction
        # The code does self._sync_product_to_local(result).
        # Inside it executes DB queries.

        prod_id = service.create_product({"name": "New Prod"})
        assert prod_id == 100
        # Should verify that db insert was called to sync
        cursor = mock_db.get_cursor.return_value.__enter__.return_value
        # Check if INSERT or UPDATE was called
        assert cursor.execute.called

    def test_create_product_offline_queue(self, mock_db, mock_api):
        service = HybridDataService(mock_db, mock_api)
        mock_api.is_online.return_value = False

        cursor = mock_db.get_cursor.return_value.__enter__.return_value
        cursor.lastrowid = 55

        prod_id = service.create_product({"name": "Offline Prod"})
        assert prod_id == 55

        # Verify it was added to sync_queue
        # The code calls _mark_for_sync -> CREATE TABLE IF NOT EXISTS sync_queue ... INSERT INTO sync_queue
        # We check if execute was called with INSERT INTO sync_queue
        calls = cursor.execute.call_args_list
        # There should be insert into products, create table sync_queue, insert into sync_queue

        found_queue_insert = False
        for call in calls:
            if "INSERT INTO sync_queue" in call[0][0]:
                found_queue_insert = True
                break
        assert found_queue_insert is True
