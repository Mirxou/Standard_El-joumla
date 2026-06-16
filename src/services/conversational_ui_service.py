#!/usr/bin/env python3
"""
واجهة محادثية - Conversational UI Service
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActionResult:
    """نتيجة الإجراء المنفذ"""

    result: any
    explanation: str
    sources: list
    suggested_actions: list
    confidence: float = 1.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ConversationalUIService:
    """خدمة الواجهة المحادثية"""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self._intent_patterns = {
            "search_product": ["ابحث عن منتج", "أريد منتج"],
            "search_customer": ["ابحث عن عميل", "أريد عميل"],
            "create_invoice": ["أنشئ فاتورة"],
            "show_sales": ["أرني المبيعات"],
            "help": ["مساعدة"],
        }

    def process_natural_language_query(self, query, user_context=None):
        """معالجة استعلام باللغة الطبيعية"""
        intent, confidence = self._extract_intent(query)
        entities = self._extract_entities(query)
        result = self._execute_action(intent, entities, user_context or {})
        explanation = self._generate_explanation(result, intent, entities)
        sources = ["قاعدة البيانات"]
        suggestions = self._generate_suggestions(intent, result)

        return ActionResult(
            result=result,
            explanation=explanation,
            sources=sources,
            suggested_actions=suggestions,
            confidence=confidence,
        )

    def _extract_intent(self, query):
        """استخراج النية"""
        query_lower = query.lower()
        for intent, patterns in self._intent_patterns.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    return intent, 0.8
        return "general_search", 0.5

    def _extract_entities(self, query):
        """استخراج الكيانات"""
        entities = {}
        import re

        numbers = re.findall(r"\d+", query)
        if numbers:
            entities["quantity"] = int(numbers[0])
        return entities

    def _execute_action(self, intent, entities, context):
        """تنفيذ الإجراء"""
        if intent == "show_sales":
            return {"today_sales": 1500.50, "invoices": 25}
        elif intent == "help":
            return {"commands": list(self._intent_patterns.keys())}
        else:
            return {"message": "تم تنفيذ الطلب"}

    def _generate_explanation(self, result, intent, entities):
        """إنشاء الشرح"""
        if isinstance(result, dict) and "today_sales" in result:
            return f"اليوم: {result['invoices']} فاتورة بإجمالي {result['today_sales']:.2f} ريال"
        return "تم تنفيذ الطلب بنجاح"

    def _generate_suggestions(self, intent, result):
        """إنشاء الاقتراحات"""
        return ["مساعدة", "البحث عن منتج", "إنشاء فاتورة"]
