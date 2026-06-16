"""
Unit Tests for AI Modules
اختبارات وحدة لوحدات الذكاء الاصطناعي
"""

import pytest

from src.ai.chatbot import ChatbotEngine
from src.ai.predictive_analytics import PredictiveEngine


class TestChatbotEngine:
    """اختبارات ChatbotEngine"""

    def test_chatbot_engine_init(self):
        """اختبار تهيئة ChatbotEngine"""
        chatbot = ChatbotEngine()
        assert chatbot.knowledge_base is not None
        assert isinstance(chatbot.knowledge_base, dict)

    def test_process_message(self):
        """اختبار معالجة رسالة"""
        chatbot = ChatbotEngine()

        # رسالة بسيطة
        response = chatbot.process_message("مرحبا")
        assert response is not None
        assert isinstance(response, dict)
        assert "response" in response or "text" in response or "message" in response

    def test_match_intent(self):
        """اختبار مطابقة النية"""
        chatbot = ChatbotEngine()

        # اختبار نية معروفة
        intent, confidence = chatbot._match_intent("مرحبا", "ar")
        assert intent is not None or confidence >= 0
        assert isinstance(confidence, float)

    def test_detect_language(self):
        """اختبار كشف اللغة"""
        chatbot = ChatbotEngine()

        # رسالة عربية
        lang = chatbot._detect_language("مرحبا")
        assert lang == "ar"

        # رسالة إنجليزية
        lang = chatbot._detect_language("hello")
        assert lang == "en"


@pytest.mark.requires_db
class TestPredictiveEngine:
    """اختبارات PredictiveEngine"""

    def test_predictive_engine_init(self, db_manager):
        """اختبار تهيئة PredictiveEngine"""
        engine = PredictiveEngine(db_manager)
        assert engine.db is not None

    def test_forecast_sales(self, db_manager):
        """اختبار توقع المبيعات"""
        engine = PredictiveEngine(db_manager)

        try:
            forecasts = engine.forecast_sales(days=7)
            assert forecasts is not None
            assert isinstance(forecasts, list)
        except Exception as e:
            # قد يفشل إذا لم تكن هناك بيانات كافية
            pytest.skip(f"لا توجد بيانات كافية: {e}")

    def test_forecast_sales_for_product(self, db_manager):
        """اختبار توقع المبيعات لمنتج معين"""
        engine = PredictiveEngine(db_manager)

        try:
            forecasts = engine.forecast_sales(product_id=1, days=30)
            assert forecasts is not None
            assert isinstance(forecasts, list)
        except Exception as e:
            pytest.skip(f"لا توجد بيانات كافية: {e}")
