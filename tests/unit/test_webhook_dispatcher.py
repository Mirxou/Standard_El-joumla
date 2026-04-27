#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Webhook Dispatcher
اختبارات وحدة لـ Webhook Dispatcher
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import json
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.webhook_dispatcher import WebhookDispatcher, WebhookDeliveryResult


class TestWebhookDispatcher:
    """اختبارات Webhook Dispatcher"""
    
    @pytest.fixture
    def dispatcher(self):
        """إنشاء WebhookDispatcher للاختبارات"""
        return WebhookDispatcher(logger=Mock())
    
    @pytest.fixture
    def mock_payload(self):
        """Payload تجريبي"""
        return {
            "event": "test_event",
            "data": {"id": 1, "name": "Test"}
        }
    
    def test_dispatcher_init(self, dispatcher):
        """اختبار تهيئة Dispatcher"""
        assert dispatcher is not None
        assert dispatcher.logger is not None
        assert dispatcher._delivery_queue is not None
    
    def test_serialize_payload(self, dispatcher, mock_payload):
        """اختبار تحويل Payload إلى JSON"""
        result = dispatcher._serialize_payload(mock_payload)
        
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["event"] == "test_event"
        assert parsed["data"]["id"] == 1
    
    def test_serialize_payload_with_decimal(self, dispatcher):
        """اختبار تحويل Payload مع Decimal"""
        from decimal import Decimal
        
        payload = {"amount": Decimal("100.50")}
        result = dispatcher._serialize_payload(payload)
        
        parsed = json.loads(result)
        assert parsed["amount"] == 100.50
    
    def test_serialize_payload_with_datetime(self, dispatcher):
        """اختبار تحويل Payload مع datetime"""
        from datetime import datetime
        
        payload = {"created_at": datetime(2024, 1, 1, 12, 0, 0)}
        result = dispatcher._serialize_payload(payload)
        
        parsed = json.loads(result)
        assert "created_at" in parsed
        assert isinstance(parsed["created_at"], str)
    
    def test_generate_signature(self, dispatcher):
        """اختبار توليد Signature"""
        payload = '{"test": "data"}'
        secret_key = "test-secret-key"
        
        signature = dispatcher._generate_signature(payload, secret_key)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex length
    
    def test_calculate_backoff(self, dispatcher):
        """اختبار حساب Exponential Backoff"""
        # المحاولة 1: 1 ثانية
        assert dispatcher._calculate_backoff(1) == 1.0
        
        # المحاولة 2: 2 ثانية
        assert dispatcher._calculate_backoff(2) == 2.0
        
        # المحاولة 3: 4 ثواني
        assert dispatcher._calculate_backoff(3) == 4.0
        
        # المحاولة 4: 8 ثواني
        assert dispatcher._calculate_backoff(4) == 8.0
    
    def test_should_retry_status_code(self, dispatcher):
        """اختبار تحديد ما إذا كان يجب إعادة المحاولة حسب Status Code"""
        # يجب إعادة المحاولة للأخطاء 5xx
        assert dispatcher._should_retry(500) == True
        assert dispatcher._should_retry(502) == True
        assert dispatcher._should_retry(503) == True
        assert dispatcher._should_retry(504) == True
        
        # لا يجب إعادة المحاولة للأخطاء 4xx
        assert dispatcher._should_retry(400) == False
        assert dispatcher._should_retry(404) == False
        assert dispatcher._should_retry(401) == False
        
        # يجب إعادة المحاولة للنجاح (لا يجب، لكن للاختبار)
        assert dispatcher._should_retry(200) == False
    
    def test_should_retry_exception(self, dispatcher):
        """اختبار تحديد ما إذا كان يجب إعادة المحاولة حسب Exception"""
        import requests
        
        # يجب إعادة المحاولة لأخطاء الاتصال
        assert dispatcher._should_retry(None, requests.exceptions.ConnectionError()) == True
        assert dispatcher._should_retry(None, requests.exceptions.Timeout()) == True
        
        # لا يجب إعادة المحاولة للأخطاء الأخرى
        assert dispatcher._should_retry(None, ValueError()) == False
    
    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_success(self, mock_request, dispatcher, mock_payload):
        """اختبار إرسال Webhook بنجاح"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_request.return_value = mock_response
        
        result = dispatcher._deliver_webhook_sync(
            url="https://example.com/webhook",
            payload=mock_payload,
            http_method="POST",
            retry_count=1
        )
        
        assert result.success == True
        assert result.status_code == 200
        assert result.attempt_number == 1
        mock_request.assert_called_once()
    
    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_retry_on_500(self, mock_request, dispatcher, mock_payload):
        """اختبار إعادة المحاولة عند خطأ 500"""
        # Mock failed response ثم نجاح
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = "OK"
        
        mock_request.side_effect = [mock_response_fail, mock_response_success]
        
        with patch('time.sleep'):  # Skip actual sleep
            result = dispatcher._deliver_webhook_sync(
                url="https://example.com/webhook",
                payload=mock_payload,
                http_method="POST",
                retry_count=2
            )
        
        assert result.success == True
        assert result.status_code == 200
        assert result.attempt_number == 2
        assert mock_request.call_count == 2
    
    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_no_retry_on_400(self, mock_request, dispatcher, mock_payload):
        """اختبار عدم إعادة المحاولة عند خطأ 400"""
        # Mock client error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_request.return_value = mock_response
        
        result = dispatcher._deliver_webhook_sync(
            url="https://example.com/webhook",
            payload=mock_payload,
            http_method="POST",
            retry_count=3
        )
        
        assert result.success == False
        assert result.status_code == 400
        assert result.attempt_number == 1  # لم يتم إعادة المحاولة
        mock_request.assert_called_once()
    
    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_timeout(self, mock_request, dispatcher, mock_payload):
        """اختبار معالجة Timeout"""
        import requests
        
        # Mock timeout exception
        mock_request.side_effect = requests.exceptions.Timeout()
        
        result = dispatcher._deliver_webhook_sync(
            url="https://example.com/webhook",
            payload=mock_payload,
            http_method="POST",
            retry_count=2,
            timeout_seconds=5
        )
        
        assert result.success == False
        assert "Timeout" in result.error_message
        assert result.attempt_number == 2  # تمت محاولتان
    
    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_with_signature(self, mock_request, dispatcher, mock_payload):
        """اختبار إرسال Webhook مع Signature"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_request.return_value = mock_response
        
        result = dispatcher._deliver_webhook_sync(
            url="https://example.com/webhook",
            payload=mock_payload,
            http_method="POST",
            secret_key="test-secret",
            retry_count=1
        )
        
        assert result.success == True
        # التحقق من أن Signature تم إضافتها إلى Headers
        call_args = mock_request.call_args
        headers = call_args.kwargs.get('headers', {})
        assert 'X-Webhook-Signature' in headers
        assert headers['X-Webhook-Signature'].startswith('sha256=')
    
    def test_deliver_webhook_async(self, dispatcher, mock_payload):
        """اختبار إرسال Webhook بشكل Async"""
        callback_called = []
        
        def test_callback(*args):
            callback_called.append(args)
        
        dispatcher.deliver_webhook(
            url="https://example.com/webhook",
            payload=mock_payload,
            callback=test_callback
        )
        
        # التحقق من أن Webhook تم إضافته إلى Queue
        assert not dispatcher._delivery_queue.empty()
        
        # Cleanup
        dispatcher.shutdown()
    
    def test_webhook_delivery_result(self):
        """اختبار WebhookDeliveryResult"""
        result = WebhookDeliveryResult(
            success=True,
            status_code=200,
            response_body="OK",
            execution_time_ms=100,
            attempt_number=1
        )
        
        assert result.success == True
        assert result.status_code == 200
        assert result.response_body == "OK"
        assert result.execution_time_ms == 100
        assert result.attempt_number == 1
        
        # Test failure result
        result_fail = WebhookDeliveryResult(
            success=False,
            error_message="Connection Error",
            attempt_number=3
        )
        
        assert result_fail.success == False
        assert result_fail.error_message == "Connection Error"
        assert result_fail.attempt_number == 3


class TestWebhookRateLimiting:
    """اختبارات Rate Limiting للـ Webhook"""
    
    @pytest.fixture
    def dispatcher(self):
        return WebhookDispatcher(logger=Mock())
    
    def test_check_rate_limit_allowed(self, dispatcher):
        """اختبار السماح بالإرسال ضمن الحد"""
        webhook_id = 1
        rate_limit = 10
        
        # أول 10 طلبات يجب أن تكون مسموحة
        for i in range(10):
            result = dispatcher._check_rate_limit(webhook_id, rate_limit)
            assert result is True, f"Request {i+1} should be allowed"
    
    def test_check_rate_limit_blocked(self, dispatcher):
        """اختبار تجاوز الحد"""
        webhook_id = 1
        rate_limit = 5
        
        # إرسال 5 طلبات
        for i in range(5):
            dispatcher._check_rate_limit(webhook_id, rate_limit)
        
        # الطلب السادس يجب أن يتم رفضه
        result = dispatcher._check_rate_limit(webhook_id, rate_limit)
        assert result is False
    
    def test_rate_limit_different_webhooks(self, dispatcher):
        """اختبار Rate Limit لـ Webhooks مختلفة"""
        # كل Webhook يجب أن يكون له Rate Limit مستقل
        webhook_id_1 = 1
        webhook_id_2 = 2
        
        # إرسال 5 طلبات لـ webhook 1
        for i in range(5):
            dispatcher._check_rate_limit(webhook_id_1, 5)
        
        # webhook 1 يجب أن يتم حظره
        assert dispatcher._check_rate_limit(webhook_id_1, 5) is False
        
        # webhook 2 يجب أن يكون مسموحاً
        assert dispatcher._check_rate_limit(webhook_id_2, 5) is True
    
    def test_get_rate_limit_status(self, dispatcher):
        """اختبار الحصول على حالة Rate Limit"""
        webhook_id = 1
        
        # إرسال 3 طلبات
        for i in range(3):
            dispatcher._check_rate_limit(webhook_id, 10)
        
        status = dispatcher.get_rate_limit_status(webhook_id)
        
        assert status['webhook_id'] == webhook_id
        assert status['requests_in_last_minute'] == 3
    
    def test_get_rate_limit_status_empty(self, dispatcher):
        """اختبار حالة Rate Limit فارغة"""
        webhook_id = 999
        
        status = dispatcher.get_rate_limit_status(webhook_id)
        
        assert status['webhook_id'] == webhook_id
        assert status['requests_in_last_minute'] == 0


class TestWebhookQueue:
    """اختبارات Queue الإرسال"""
    
    @pytest.fixture
    def dispatcher(self):
        return WebhookDispatcher(logger=Mock())
    
    def test_get_queue_size_empty(self, dispatcher):
        """اختبار حجم Queue فارغ"""
        size = dispatcher.get_queue_size()
        assert size == 0
    
    def test_deliver_webhook_adds_to_queue(self, dispatcher):
        """اختبار إضافة Webhook إلى Queue"""
        payload = {"event": "test"}
        
        dispatcher.deliver_webhook(
            url="https://example.com/webhook",
            payload=payload,
            priority=5
        )
        
        assert dispatcher.get_queue_size() == 1
        
        # Cleanup
        dispatcher.shutdown()
    
    def test_deliver_webhook_rate_limit_exceeded(self, dispatcher):
        """اختبار الرفض عند تجاوز Rate Limit"""
        webhook_id = 1
        rate_limit = 3
        
        # إرسال 3 طلبات
        for i in range(3):
            dispatcher.deliver_webhook(
                url="https://example.com/webhook",
                payload={"event": "test"},
                webhook_id=webhook_id,
                rate_limit_per_minute=rate_limit
            )
        
        # الطلب الرابع يجب أن يرفض
        result = dispatcher.deliver_webhook(
            url="https://example.com/webhook",
            payload={"event": "test"},
            webhook_id=webhook_id,
            rate_limit_per_minute=rate_limit
        )
        
        assert result is False
        
        # Cleanup
        dispatcher.shutdown()


class TestWebhookShutdown:
    """اختبارات إيقاف Webhook Dispatcher"""
    
    @pytest.fixture
    def dispatcher(self):
        return WebhookDispatcher(logger=Mock())
    
    def test_shutdown_dispatcher(self, dispatcher):
        """اختبار إيقاف Dispatcher"""
        # إضافة بعض Webhooks
        for i in range(3):
            dispatcher.deliver_webhook(
                url=f"https://example.com/webhook{i}",
                payload={"event": "test"}
            )
        
        # إيقاف Dispatcher
        dispatcher.shutdown()
        
        assert dispatcher._stop_worker is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])




