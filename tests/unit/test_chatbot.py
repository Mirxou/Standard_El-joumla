#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Chatbot
اختبارات الروبوت المحادث
"""

import pytest

from src.ai.chatbot import ChatbotEngine, chat


class TestChatbotEngineInitialization:
    """اختبارات تهيئة محرك الروبوت"""

    def test_initialization(self):
        """اختبار التهيئة الأساسية"""
        engine = ChatbotEngine()

        assert engine.conversation_history == []
        assert "ar" in engine.knowledge_base
        assert "en" in engine.knowledge_base

    def test_knowledge_base_structure(self):
        """اختبار بنية قاعدة المعرفة"""
        engine = ChatbotEngine()

        # التحقق من وجود اللغات
        assert "ar" in engine.knowledge_base
        assert "en" in engine.knowledge_base

        # التحقق من وجود النوايا
        ar_kb = engine.knowledge_base["ar"]
        assert "greeting" in ar_kb or "unknown" in ar_kb

        en_kb = engine.knowledge_base["en"]
        assert "greeting" in en_kb or "unknown" in en_kb


class TestProcessMessage:
    """اختبارات معالجة الرسائل"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك جديد لكل اختبار"""
        return ChatbotEngine()

    def test_process_message_basic(self, engine):
        """اختبار معالجة رسالة أساسية"""
        result = engine.process_message("مرحبا")

        assert "response" in result
        assert "language" in result
        assert "intent" in result
        assert "confidence" in result
        assert "timestamp" in result

    def test_process_message_english(self, engine):
        """اختبار معالجة رسالة إنجليزية"""
        result = engine.process_message("Hello")

        assert result["language"] == "en"
        assert "response" in result

    def test_process_message_arabic(self, engine):
        """اختبار معالجة رسالة عربية"""
        result = engine.process_message("مرحبا")

        assert result["language"] == "ar"
        assert "response" in result

    def test_process_message_saves_to_history(self, engine):
        """اختبار حفظ الرسالة في السجل"""
        engine.process_message("test message", user_id="user1")

        assert len(engine.conversation_history) == 1
        assert engine.conversation_history[0]["message"] == "test message"
        assert engine.conversation_history[0]["user_id"] == "user1"

    def test_process_message_with_user_id(self, engine):
        """اختبار معالجة رسالة مع معرف المستخدم"""
        result = engine.process_message("hello", user_id="test_user")

        assert result["response"] is not None
        assert engine.conversation_history[0]["user_id"] == "test_user"


class TestGetConversationHistory:
    """اختبارات الحصول على سجل المحادثات"""

    @pytest.fixture
    def engine_with_history(self):
        """إنشاء محرك مع سجل محادثات"""
        engine = ChatbotEngine()
        engine.process_message("message 1", user_id="user1")
        engine.process_message("message 2", user_id="user1")
        engine.process_message("message 3", user_id="user2")
        return engine

    def test_get_all_history(self, engine_with_history):
        """اختبار الحصول على كل السجل"""
        history = engine_with_history.get_conversation_history()

        assert len(history) == 3

    def test_get_history_by_user(self, engine_with_history):
        """اختبار الحصول على سجل مستخدم محدد"""
        history = engine_with_history.get_conversation_history(user_id="user1")

        assert len(history) == 2
        assert all(h["user_id"] == "user1" for h in history)

    def test_get_history_with_limit(self, engine_with_history):
        """اختبار الحصول على سجل محدود"""
        history = engine_with_history.get_conversation_history(limit=2)

        assert len(history) == 2

    def test_get_history_empty(self):
        """اختبار الحصول على سجل فارغ"""
        engine = ChatbotEngine()
        history = engine.get_conversation_history()

        assert history == []


class TestClearHistory:
    """اختبارات مسح سجل المحادثات"""

    @pytest.fixture
    def engine_with_history(self):
        """إنشاء محرك مع سجل محادثات"""
        engine = ChatbotEngine()
        engine.process_message("message 1", user_id="user1")
        engine.process_message("message 2", user_id="user1")
        engine.process_message("message 3", user_id="user2")
        return engine

    def test_clear_all_history(self, engine_with_history):
        """اختبار مسح كل السجل"""
        engine_with_history.clear_history()

        assert engine_with_history.conversation_history == []

    def test_clear_user_history(self, engine_with_history):
        """اختبار مسح سجل مستخدم محدد"""
        engine_with_history.clear_history(user_id="user1")

        assert len(engine_with_history.conversation_history) == 1
        assert engine_with_history.conversation_history[0]["user_id"] == "user2"


class TestChatFunction:
    """اختبارات الدالة المختصرة للمحادثة"""

    def test_chat_function_returns_string(self):
        """اختبار أن الدالة تعيد نصاً"""
        result = chat("hello")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_chat_function_with_user_id(self):
        """اختبار الدالة مع معرف المستخدم"""
        result = chat("hi", user_id="test_user")

        assert isinstance(result, str)


class TestLanguageDetection:
    """اختبارات كشف اللغة"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك جديد"""
        return ChatbotEngine()

    def test_detect_english(self, engine):
        """اختبار كشف الإنجليزية"""
        result = engine.process_message("Hello world")
        assert result["language"] == "en"

    def test_detect_arabic(self, engine):
        """اختبار كشف العربية"""
        result = engine.process_message("مرحبا بالعالم")
        assert result["language"] == "ar"


class TestIntentMatching:
    """اختبارات مطابقة النوايا"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك جديد"""
        return ChatbotEngine()

    def test_greeting_intent(self, engine):
        """اختبار نية التحية"""
        result = engine.process_message("مرحبا")

        assert "intent" in result
        assert result["confidence"] > 0

    def test_unknown_intent(self, engine):
        """اختبار نية غير معروفة"""
        result = engine.process_message("xyz123random")

        assert "intent" in result
        assert "response" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
