#!/usr/bin/env python3
"""
اختبارات HTTP Client
"""

from unittest.mock import patch

import pytest

from src.api.http_client import HTTPClient


class TestHTTPClient:
    """اختبارات عميل HTTP"""

    @pytest.fixture
    def http_client(self):
        """إنشاء عميل HTTP"""
        return HTTPClient(base_url="https://api.example.com")

    def test_initialization(self, http_client):
        """اختبار التهيئة"""
        assert http_client is not None
        assert http_client.base_url == "https://api.example.com"

    def test_get_request(self, http_client):
        """اختبار طلب GET"""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"data": "test"}
            result = http_client.get("/endpoint")
            assert result is not None

    def test_post_request(self, http_client):
        """اختبار طلب POST"""
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": "123"}
            result = http_client.post("/endpoint", {"key": "value"})
            assert result is not None

    def test_put_request(self, http_client):
        """اختبار طلب PUT"""
        with patch("requests.put") as mock_put:
            mock_put.return_value.status_code = 200
            result = http_client.put("/endpoint/123", {"key": "value"})
            assert result is not None

    def test_delete_request(self, http_client):
        """اختبار طلب DELETE"""
        with patch("requests.delete") as mock_delete:
            mock_delete.return_value.status_code = 204
            result = http_client.delete("/endpoint/123")
            assert result is not None

    def test_set_headers(self, http_client):
        """اختبار تعيين headers"""
        http_client.set_headers({"Authorization": "Bearer token"})
        assert "Authorization" in http_client.headers

    def test_handle_error_response(self, http_client):
        """اختبار التعامل مع خطأ في الاستجابة"""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            mock_get.return_value.raise_for_status.side_effect = Exception("Not Found")
            with pytest.raises(Exception):
                http_client.get("/nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
