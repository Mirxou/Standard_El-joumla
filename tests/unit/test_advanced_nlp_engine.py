#!/usr/bin/env python3
"""
اختبارات Advanced NLP Engine - محدثة لتتوافق مع API الفعلي
"""

from datetime import datetime

import pytest

from src.ai.advanced_nlp_engine import (
    AdvancedNLPEngine,
    BusinessReport,
    ConversationContext,
    QueryIntent,
    Response,
)


class TestAdvancedNLPEngine:
    """اختبارات محرك NLP المتقدم"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك NLP للاختبارات"""
        return AdvancedNLPEngine()

    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert hasattr(engine, "language_models")  # plural - it's a dict of models
        assert hasattr(engine, "intent_classifier")
        assert hasattr(engine, "entity_extractor")
        assert hasattr(engine, "conversation_contexts")

    def test_process_query_arabic(self, engine):
        """اختبار معالجة استعلام بالعربية - الدالة الفعلية understand_business_queries"""
        query = "ما هي مبيعات اليوم؟"

        result = engine.understand_business_queries(query, language="ar")

        assert result is not None
        assert isinstance(result, QueryIntent)
        assert result.intent is not None
        assert result.confidence >= 0
        assert result.original_query == query

    def test_process_query_english(self, engine):
        """اختبار معالجة استعلام بالإنجليزية"""
        query = "What are today's sales?"

        result = engine.understand_business_queries(query, language="en")

        assert result is not None
        assert isinstance(result, QueryIntent)
        assert result.intent is not None

    def test_process_query_empty(self, engine):
        """اختبار معالجة استعلام فارغ"""
        result = engine.understand_business_queries("")

        assert result is not None
        assert result.intent in ("unknown", "general_query")

    def test_generate_response(self, engine):
        """اختبار توليد الرد - عبر understand_business_queries"""
        result = engine.understand_business_queries("What are today's sales?")
        assert result is not None
        assert isinstance(result, QueryIntent)

    def test_extract_entities(self, engine):
        """اختبار استخراج الكيانات - عبر _extract_entities"""
        query = "Show me sales for product ABC123 from January to March"

        # الدالة الفعلية
        entities = engine._extract_entities(query)

        assert isinstance(entities, dict)

    def test_generate_business_report(self, engine):
        """اختبار توليد تقرير الأعمال - الدالة الفعلية generate_business_reports"""
        data = {
            "sales_data": [
                {"product": "A", "amount": 100},
                {"product": "B", "amount": 200},
            ]
        }

        result = engine.generate_business_reports(data, report_type="sales_report")

        assert result is not None
        assert isinstance(result, BusinessReport)
        assert result.title is not None
        assert result.content is not None
        assert isinstance(result.key_insights, list)
        assert isinstance(result.recommendations, list)

    def test_manage_conversation_context(self, engine):
        """اختبار إدارة سياق المحادثة"""
        session_id = "test_session_001"
        assert isinstance(engine.conversation_contexts, dict)

        messages = [{"text": "What are sales?", "sender": "user"}]
        context = ConversationContext(
            session_id=session_id,
            history=messages,
            current_intent=None,
            entities={},
            context_variables={},
            last_updated=datetime.now(),
        )
        result = engine.chat_with_business_data(messages, context=context)
        assert result is not None

    def test_conversational_ai_response(self, engine):
        """اختبار رد AI المحادثي"""
        messages = [
            {"text": "What are sales?", "sender": "user"},
        ]

        result = engine.chat_with_business_data(messages)

        assert result is not None
        assert isinstance(result, Response)

    def test_multi_language_support(self, engine):
        """اختبار دعم متعدد اللغات"""
        queries = {
            "ar": "ما هي المخزونات؟",
            "en": "What is the inventory?",
        }

        for lang, query in queries.items():
            result = engine.understand_business_queries(query, language=lang)
            assert result is not None

    def test_confidence_score_range(self, engine):
        """اختبار نطاق درجة الثقة"""
        query = "Show sales report"

        result = engine.understand_business_queries(query)

        if result:
            assert 0 <= result.confidence <= 1

    def test_processing_time_tracking(self, engine):
        """اختبار تتبع وقت المعالجة"""
        query = "What are today's sales?"

        result = engine.understand_business_queries(query)

        if result:
            assert result.processing_time >= 0


class TestQueryIntent:
    """اختبارات نية الاستعلام"""

    def test_query_intent_creation(self):
        """اختبار إنشاء نية الاستعلام"""
        intent = QueryIntent(
            intent="sales_query",
            confidence=0.95,
            entities={"date": "today", "product": "ABC"},
            original_query="What are today's sales for ABC?",
            processing_time=0.15,
        )

        assert intent.intent == "sales_query"
        assert intent.confidence == 0.95
        assert intent.processing_time == 0.15


class TestResponse:
    """اختبارات الرد"""

    def test_response_creation(self):
        """اختبار إنشاء الرد"""
        response = Response(
            text="Today's sales are $1,000",
            confidence=0.9,
            intent="sales_query",
            entities={"amount": 1000},
            suggestions=["View detailed report", "Compare with yesterday"],
            processing_time=0.2,
        )

        assert response.text == "Today's sales are $1,000"
        assert response.confidence == 0.9
        assert len(response.suggestions) == 2


class TestBusinessReport:
    """اختبارات تقرير الأعمال"""

    def test_business_report_creation(self):
        """اختبار إنشاء تقرير الأعمال"""
        report = BusinessReport(
            title="Monthly Sales Report",
            content="Sales increased by 20% this month.",
            summary="Positive growth trend",
            key_insights=["Revenue up 20%", "New customers increased"],
            recommendations=["Increase marketing spend", "Expand product line"],
            generated_at=datetime.now(),
            data_sources=["sales_db", "customer_db"],
        )

        assert report.title == "Monthly Sales Report"
        assert len(report.key_insights) == 2
        assert len(report.recommendations) == 2


class TestConversationContext:
    """اختبارات سياق المحادثة"""

    def test_conversation_context_creation(self):
        """اختبار إنشاء سياق المحادثة"""
        context = ConversationContext(
            session_id="session_001",
            history=[{"role": "user", "content": "Hello"}],
            current_intent="greeting",
            entities={"name": "User"},
            context_variables={"theme": "light"},
            last_updated=datetime.now(),
        )

        assert context.session_id == "session_001"
        assert context.current_intent == "greeting"
        assert len(context.history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
