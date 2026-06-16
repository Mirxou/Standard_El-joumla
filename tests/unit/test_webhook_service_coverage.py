#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage Tests for Webhook Service
اختبارات تغطية إضافية لـ Webhook Service
"""

from datetime import datetime
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.webhook_service import Webhook, WebhookService


class TestWebhookServiceCoverage:
    """اختبارات تغطية إضافية لـ Webhook Service"""

    @pytest.fixture
    def db_manager(self):
        """Mock DatabaseManager"""
        return Mock()

    @pytest.fixture
    def service(self, db_manager):
        """WebhookService Instance"""
        return WebhookService(db_manager, logger=Mock())

    def test_create_webhook_exception(self, service, db_manager):
        """اختبار الفشل في إنشاء Webhook"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        result = service.create_webhook(name="Test", url="http://test.com", event_type="test")

        assert result is None
        service.logger.error.assert_called()

    def test_get_webhook_exception(self, service, db_manager):
        """اختبار الفشل في جلب Webhook"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        result = service.get_webhook(1)

        assert result is None
        service.logger.error.assert_called()

    def test_get_all_webhooks_exception(self, service, db_manager):
        """اختبار الفشل في جلب جميع Webhooks"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        result = service.get_all_webhooks()

        assert result == []
        service.logger.error.assert_called()

    def test_get_all_webhooks_filters(self, service, db_manager):
        """اختبار الفلاتر المتعددة في get_all_webhooks"""
        # Mock result to allow iteration
        db_manager.execute_query.return_value = []

        service.get_all_webhooks(event_type="sale", is_active=True, company_id=1)

        # Check query parameters
        call_args = db_manager.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "event_type = ?" in query
        assert "is_active = ?" in query
        assert params == (1, "sale", 1)

    def test_update_webhook_exception(self, service, db_manager):
        """اختبار الفشل في تحديث Webhook"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        result = service.update_webhook(1, name="New Name")

        assert result is False
        service.logger.error.assert_called()

    def test_update_webhook_all_fields(self, service, db_manager):
        """اختبار تحديث جميع الحقول"""
        result = service.update_webhook(
            webhook_id=1,
            name="Updated",
            url="http://new.com",
            event_type="new_event",
            http_method="PUT",
            headers={"k": "v"},
            payload_template={"t": "v"},
            is_active=False,
            retry_count=5,
            timeout_seconds=60,
            secret_key="secret",
            priority=1,
            rate_limit_per_minute=100,
            company_id=1,
        )

        assert result is True
        # Check that query contains all fields
        call_args = db_manager.execute_query.call_args
        query = call_args[0][0]
        assert "name = ?" in query
        assert "url = ?" in query
        assert "rate_limit_per_minute = ?" in query

    def test_update_webhook_no_fields(self, service, db_manager):
        """اختبار تحديث بدون حقول"""
        result = service.update_webhook(1)
        assert result is True
        # execute_query should NOT be called
        db_manager.execute_query.assert_not_called()

    def test_delete_webhook_exception(self, service, db_manager):
        """اختبار الفشل في حذف Webhook"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        result = service.delete_webhook(1)

        assert result is False
        service.logger.error.assert_called()

    def test_trigger_webhook_no_webhooks(self, service):
        """اختبار trigger_webhook عند عدم وجود webhooks"""
        with patch.object(service, "get_all_webhooks", return_value=[]):
            service.trigger_webhook("test_event", {})
            service.logger.debug.assert_called_with("لا توجد Webhooks نشطة للحدث: test_event")

    def test_trigger_webhook_exception(self, service):
        """اختبار Exception في trigger_webhook"""
        with patch.object(service, "get_all_webhooks", side_effect=Exception("Boom")):
            service.trigger_webhook("test_event", {})
            service.logger.error.assert_called()

    def test_trigger_webhook_delivery_exception(self, service):
        """اختبار Exception أثناء إرسال webhook واحد"""
        webhook = Webhook(
            id=1,
            name="Test",
            url="url",
            event_type="event",
            headers="invalid json",  # This forces json.loads exception
            priority=5,
            rate_limit_per_minute=60,
        )

        with patch.object(service, "get_all_webhooks", return_value=[webhook]):
            # We want to test exception INSIDE the loop
            # But invalid headers is handled by a try/except block passing doing nothing
            # Let's mock _build_payload to raise exception
            with patch.object(service, "_build_payload", side_effect=Exception("Payload Error")):
                service.trigger_webhook("event", {})
                # Should log error for specific webhook
                service.logger.error.assert_called()

    def test_trigger_webhook_rate_limit_warning(self, service):
        """اختبار تسجيل تحذير عند تجاوز Rate Limit"""
        webhook = Webhook(
            id=1,
            name="Test",
            url="url",
            event_type="event",
            priority=5,
            rate_limit_per_minute=60,
        )

        with patch.object(service, "get_all_webhooks", return_value=[webhook]):
            with patch.object(service.dispatcher, "deliver_webhook", return_value=False):
                service.trigger_webhook("event", {})
                # Should verify logger warning
                args, _ = service.logger.warning.call_args
                assert "تم تجاوز Rate Limit" in args[0]

    def test_build_payload_template_exception(self, service):
        """اختبار فشل _build_payload"""
        webhook = Webhook(
            id=1,
            name="Test",
            url="url",
            event_type="event",
            payload_template="{invalid_json}",  # Invalid JSON
            priority=5,
            rate_limit_per_minute=60,
        )

        result = service._build_payload(webhook, {"data": 1})
        # Should return original payload on error
        assert result == {"data": 1}
        service.logger.warning.assert_called()

    def test_on_webhook_delivered_exception(self, service, db_manager):
        """اختبار Exception في callback التسجيل"""
        db_manager.execute_query.side_effect = Exception("DB Error")

        from src.core.webhook_dispatcher import WebhookDeliveryResult

        result = WebhookDeliveryResult(success=True)

        service._on_webhook_delivered(result, 1, "event", 1, "{}")
        service.logger.error.assert_called()

    def test_get_webhook_logs_exception(self, service, db_manager):
        """اختبار Exception في get_webhook_logs"""
        db_manager.execute_query.side_effect = Exception("DB Error")
        result = service.get_webhook_logs()
        assert result == []
        service.logger.error.assert_called()

    def test_parse_datetime(self, service):
        """اختبار حالات _parse_datetime المختلفة"""
        assert service._parse_datetime(None) is None

        dt = datetime.now()
        assert service._parse_datetime(dt) == dt

        # Valid strings
        s1 = "2023-01-01T12:00:00"
        assert service._parse_datetime(s1) is not None

        s2 = "2023-01-01 12:00:00"
        assert service._parse_datetime(s2) is not None

        # Invalid string
        assert service._parse_datetime("invalid") is None

    def test_row_to_webhook_from_dict_parsing(self, service):
        """اختبار Webhook.from_dict لتحليل التواريخ"""
        data = {
            "name": "Test",
            "url": "url",
            "event_type": "e",
            "created_at": "2023-01-01T10:00:00",
            "updated_at": datetime.now(),  # Object case
        }
        w = Webhook.from_dict(data)
        assert isinstance(w.created_at, datetime)
        assert isinstance(w.updated_at, datetime)
