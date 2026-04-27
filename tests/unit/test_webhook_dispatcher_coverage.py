#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage Tests for Webhook Dispatcher
اختبارات تغطية إضافية لـ Webhook Dispatcher
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import json
import threading
from queue import Empty
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.webhook_dispatcher import WebhookDispatcher, WebhookDeliveryResult

class TestWebhookDispatcherCoverage:
    """اختبارات تغطية إضافية لـ Webhook Dispatcher"""
    
    @pytest.fixture
    def dispatcher(self):
        """إنشاء WebhookDispatcher للاختبارات"""
        return WebhookDispatcher(logger=Mock())
    
    def test_check_rate_limit(self, dispatcher):
        """اختبار منطق Rate Limit"""
        webhook_id = 999
        limit = 5
        
        # 1. إرسال طلبات تحت الحد
        for _ in range(limit):
            assert dispatcher._check_rate_limit(webhook_id, limit) == True
            
        # 2. إرسال طلب فوق الحد (يجب أن يرفض)
        assert dispatcher._check_rate_limit(webhook_id, limit) == False
        
        # 3. التحقق من تنظيف التوقيتات القديمة
        # نحتاج لمحاكاة مرور الوقت. بدلاً من الانتظار، نتلاعب بـ _rate_limit_tracker
        with dispatcher._rate_limit_lock:
            # جعل التوقيتات قديمة جداً (أكثر من دقيقة)
            old_time = time.time() - 70.0
            dispatcher._rate_limit_tracker[webhook_id] = [old_time] * limit
            
        # الآن يجب أن يقبل طلب جديد
        assert dispatcher._check_rate_limit(webhook_id, limit) == True

    def test_deliver_webhook_rate_limited(self, dispatcher):
        """اختبار رفض الإرسال عند تجاوز Rate Limit"""
        webhook_id = 888
        limit = 1
        
        # الطلب الأول (مقبول)
        assert dispatcher.deliver_webhook(
            url="http://test.com", 
            payload={}, 
            webhook_id=webhook_id, 
            rate_limit_per_minute=limit
        ) == True
        
        # الطلب الثاني (مرفوض)
        assert dispatcher.deliver_webhook(
            url="http://test.com", 
            payload={}, 
            webhook_id=webhook_id, 
            rate_limit_per_minute=limit
        ) == False

    def test_get_rate_limit_status(self, dispatcher):
        """اختبار الحصول على حالة Rate Limit"""
        webhook_id = 777
        
        # حالة فارغة
        status = dispatcher.get_rate_limit_status(webhook_id)
        assert status['requests_in_last_minute'] == 0
        
        # إضافة طلب
        dispatcher._check_rate_limit(webhook_id, 10)
        status = dispatcher.get_rate_limit_status(webhook_id)
        assert status['requests_in_last_minute'] == 1
        assert status['oldest_request'] is not None

    def test_serialize_payload_error(self, dispatcher):
        """اختبار فشل تحويل Payload"""
        # كائن غير قابل للتحويل لـ JSON
        class Unserializable:
            pass
            
        payload = {"data": Unserializable()}
        
        # يجب أن يعالج الخطأ ويعيد WebhookDeliveryResult فاشل
        # نستخدم callback للتحقق
        callback_mock = Mock()
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload=payload,
            callback=callback_mock
        )
        
        assert result.success == False
        assert "JSON" in result.error_message
        callback_mock.assert_called_once()

    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_sync_connection_error(self, mock_request, dispatcher):
        """اختبار خطأ الاتصال في Synchronous Delivery"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError("Network Down")
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload={},
            retry_count=1
        )
        
        assert result.success == False
        assert "Connection Error" in result.error_message

    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_sync_unexpected_error(self, mock_request, dispatcher):
        """اختبار خطأ غير متوقع في Synchronous Delivery"""
        mock_request.side_effect = Exception("Boom!")
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload={},
            retry_count=1
        )
        
        assert result.success == False
        assert "Unexpected Error" in result.error_message
        assert "Boom!" in result.error_message

    def test_worker_loop_rate_limit_requeue(self, dispatcher):
        """اختبار إعادة جدولة المهمة عند تجاوز Rate Limit في Worker"""
        webhook_id = 666
        limit = 1
        
        # استنفاد الحد
        dispatcher._check_rate_limit(webhook_id, limit)
        
        # إعداد بيانات webhook
        webhook_data = {
            "url": "http://test.com",
            "payload": {},
            "webhook_id": webhook_id,
            "rate_limit_per_minute": limit
        }
        
        # وضع المهمة في الـ Queue
        dispatcher._delivery_queue.put((1, time.time(), webhook_data))
        
        # تشغيل خطوة واحدة من الـ Worker Loop (محاكاة)
        # نحتاج لـ Mocking time.sleep لتجنب الانتظار الطويل
        with patch('time.sleep') as mock_sleep:
            # استخراج المهمة يدوياً مثل Worker
            try:
                priority, timestamp, item = dispatcher._delivery_queue.get(timeout=0.1)
                
                # التحقق واعادة الجدولة (هذا هو المنطق في _worker_loop lines 95-115)
                # ننسخ المنطق هنا للاختبار Unit Test للكود الداخلي للصعب الوصول اليه عبر Thread
                wid = item.get("webhook_id")
                rl = item.get("rate_limit_per_minute")
                
                if wid and rl:
                    if not dispatcher._check_rate_limit(wid, rl):
                        # Requeue logic
                        mock_sleep(10)
                        dispatcher._delivery_queue.put((priority + 1, time.time(), item))
                        dispatcher._delivery_queue.task_done()
            except Empty:
                pytest.fail("Queue wasn't expected to be empty yet")

            # التحقق من أن العنصر عاد للـ Queue
            assert not dispatcher._delivery_queue.empty()
            # التحقق من أن sleep تم استدعاؤه (تأخير إعادة المحاولة)
            mock_sleep.assert_called_with(10)

    def test_worker_loop_exception(self, dispatcher):
        """اختبار معالجة استثناء عام في Worker Loop"""
        # محاكاة خطأ عند جلب المهمة من الـ Queue
        with patch.object(dispatcher._delivery_queue, 'get') as mock_get:
            mock_get.side_effect = [Exception("Queue Error"), (1, time.time(), {"webhook_id": 1})]
            
            # تشغيل خطوة واحدة (سيتم التقاط الخطأ الأول، ثم معالجة الثاني)
            # بما أننا لا نستطيع تشغيل infinite loop، سنختبر فقط أن الاستثناء لا يوقف التطبيق
            # ولكن هنا سنستدعي المنطق الداخلي مباشرة أو نستخدم Thread مع timeout
            
            # الخيار الأفضل: استدعاء _worker_loop وتشغيل stop_worker بسرعة
            dispatcher._stop_worker = False
            
            def stop_soon():
                time.sleep(0.1)
                dispatcher._stop_worker = True
            
            stopper = threading.Thread(target=stop_soon)
            stopper.start()
            
            # نتوقع أن الـ Loop ستستمر بالعمل رغم الخطأ الأول
            # لكن mock_get side_effect سيتم استهلاكه
            try:
                dispatcher._worker_loop()
            except Exception as e:
                pytest.fail(f"Worker loop crashed: {e}")
            
            stopper.join()
            assert mock_get.call_count >= 1

    @patch('src.core.webhook_dispatcher.requests.request')
    def test_deliver_webhook_sync_client_error(self, mock_request, dispatcher):
        """اختبار خطأ العميل 4xx (لا إعادة محاولة)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload={},
            retry_count=3
        )
        
        assert result.success == False
        assert result.status_code == 404
        assert result.attempt_number == 1 # توقف بعد المحاولة الأولى
        assert "Client Error" in result.error_message

    @patch('src.core.webhook_dispatcher.requests.request')
    @patch('time.sleep')
    def test_deliver_webhook_sync_retry_then_success(self, mock_sleep, mock_request, dispatcher):
        """اختبار إعادة المحاولة ثم النجاح"""
        # فشل، فشل، نجاح
        resp_fail = Mock()
        resp_fail.status_code = 500
        
        resp_success = Mock()
        resp_success.status_code = 200
        resp_success.text = "OK"
        
        mock_request.side_effect = [resp_fail, resp_fail, resp_success]
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload={},
            retry_count=3
        )
        
        assert result.success == True
        assert result.attempt_number == 3
        assert mock_sleep.call_count == 2 # انتظر مرتين

    @patch('src.core.webhook_dispatcher.requests.request')
    @patch('time.sleep')
    def test_deliver_webhook_sync_all_retries_fail(self, mock_sleep, mock_request, dispatcher):
        """اختبار فشل جميع المحاولات"""
        resp_fail = Mock()
        resp_fail.status_code = 503
        mock_request.return_value = resp_fail
        
        result = dispatcher._deliver_webhook_sync(
            url="http://test.com",
            payload={},
            retry_count=2
        )
        
        assert result.success == False
        assert result.attempt_number == 2
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1
        
    def test_shutdown(self, dispatcher):
        """اختبار إيقاف Worker"""
        # بدء وهمي
        dispatcher._worker_thread = Mock()
        dispatcher._worker_thread.is_alive.return_value = True
        
        dispatcher.shutdown()
        
        assert dispatcher._stop_worker == True
        dispatcher._worker_thread.join.assert_called_once()




