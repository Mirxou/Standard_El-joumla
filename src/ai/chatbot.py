"""
نظام الذكاء الاصطناعي - Chatbot
AI Chatbot System for Customer and Employee Support

Features:
- معالجة اللغة الطبيعية (NLP) بالعربية والإنجليزية
- الإجابة على الاستفسارات التلقائية
- التكامل مع قاعدة البيانات
- دعم متعدد اللغات
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random  # nosec B311


class ChatbotEngine:
    """محرك Chatbot الذكي مع دعم NLP"""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        تهيئة محرك Chatbot

        Args:
            knowledge_base_path: مسار ملف قاعدة المعرفة (JSON)
        """
        self.knowledge_base_path = knowledge_base_path or "locales/chatbot_knowledge.json"
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history: List[Dict] = []

    def _load_knowledge_base(self) -> Dict:
        """تحميل قاعدة المعرفة"""
        kb_path = Path(self.knowledge_base_path)
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # قاعدة معرفة افتراضية
        return {
            "ar": {
                "greetings": {
                    "patterns": [
                        "مرحبا",
                        "السلام عليكم",
                        "أهلا",
                        "صباح الخير",
                        "مساء الخير",
                    ],
                    "responses": [
                        "مرحباً بك! كيف يمكنني مساعدتك؟",
                        "أهلاً وسهلاً! أنا هنا للمساعدة.",
                        "السلام عليكم! كيف أستطيع خدمتك؟",
                    ],
                },
                "products": {
                    "patterns": ["منتج", "سلعة", "صنف", "بضاعة", "مخزون", "توفر"],
                    "responses": [
                        "يمكنك استعراض المنتجات من قائمة 'المنتجات' أو البحث عن منتج معين.",
                        "لدينا نظام متكامل لإدارة المنتجات. ما الذي تبحث عنه؟",
                        "المنتجات متوفرة في قسم المخزون. هل تريد البحث عن منتج محدد؟",
                    ],
                },
                "sales": {
                    "patterns": ["مبيعات", "فاتورة", "طلب", "بيع", "زبون", "عميل"],
                    "responses": [
                        "يمكنك إنشاء فاتورة مبيعات من قائمة 'المبيعات' → 'فاتورة جديدة'.",
                        "نظام المبيعات يدعم الفواتير، عروض الأسعار، والمرتجعات.",
                        "لإدارة طلبات العملاء، انتقل إلى قسم المبيعات في القائمة الرئيسية.",
                    ],
                },
                "inventory": {
                    "patterns": ["مخزون", "جرد", "كمية", "رصيد", "حركة"],
                    "responses": [
                        "المخزون يتم تحديثه تلقائياً مع كل عملية بيع أو شراء.",
                        "يمكنك الاطلاع على حركات المخزون من تقارير المخزون.",
                        "نظام إدارة المخزون يدعم التتبع الكامل والتنبيهات التلقائية.",
                    ],
                },
                "reports": {
                    "patterns": ["تقرير", "تقارير", "إحصائيات", "تحليل", "بيانات"],
                    "responses": [
                        "التقارير متوفرة في قائمة 'التقارير' مع خيارات تصدير Excel و PDF.",
                        "يمكنك الحصول على تقارير مبيعات، مخزون، ومالية شاملة.",
                        "نظام التقارير يوفر تحليلات مفصلة لجميع العمليات.",
                    ],
                },
                "help": {
                    "patterns": ["مساعدة", "دعم", "كيف", "ساعدني", "شرح", "توضيح"],
                    "responses": [
                        "أنا هنا للمساعدة! ما الذي تحتاج معرفته؟",
                        "يمكنني مساعدتك في: المنتجات، المبيعات، المخزون، التقارير.",
                        "هل تريد شرحاً لميزة معينة؟ اسألني عنها!",
                    ],
                },
                "thanks": {
                    "patterns": ["شكرا", "شكراً", "ممتن", "مشكور"],
                    "responses": [
                        "العفو! سعيد بمساعدتك.",
                        "لا شكر على واجب! أنا هنا دائماً.",
                        "تسرني خدمتك! 😊",
                    ],
                },
                "unknown": {
                    "responses": [
                        "عذراً، لم أفهم سؤالك. هل يمكنك إعادة الصياغة؟",
                        "يمكنني المساعدة في: المنتجات، المبيعات، المخزون، التقارير. ما الذي تحتاجه؟",
                        "للأسف، لا أستطيع الإجابة على هذا السؤال. جرب سؤالاً آخر!",
                    ]
                },
            },
            "en": {
                "greetings": {
                    "patterns": ["hello", "hi", "hey", "good morning", "good evening"],
                    "responses": [
                        "Hello! How can I help you?",
                        "Hi there! I'm here to assist you.",
                        "Welcome! How may I serve you?",
                    ],
                },
                "products": {
                    "patterns": ["product", "item", "goods", "inventory", "stock"],
                    "responses": [
                        "You can browse products from the 'Products' menu or search for a specific item.",
                        "We have a complete product management system. What are you looking for?",
                        "Products are available in the inventory section. Would you like to search for something?",
                    ],
                },
                "sales": {
                    "patterns": ["sales", "invoice", "order", "sell", "customer"],
                    "responses": [
                        "You can create a sales invoice from 'Sales' → 'New Invoice'.",
                        "The sales system supports invoices, quotes, and returns.",
                        "To manage customer orders, go to the Sales section in the main menu.",
                    ],
                },
                "inventory": {
                    "patterns": [
                        "inventory",
                        "stock",
                        "quantity",
                        "balance",
                        "movement",
                    ],
                    "responses": [
                        "Inventory is updated automatically with every sale or purchase.",
                        "You can view stock movements from inventory reports.",
                        "The inventory management system supports full tracking and automatic alerts.",
                    ],
                },
                "reports": {
                    "patterns": ["report", "reports", "statistics", "analysis", "data"],
                    "responses": [
                        "Reports are available in the 'Reports' menu with Excel and PDF export options.",
                        "You can get comprehensive sales, inventory, and financial reports.",
                        "The reporting system provides detailed analytics for all operations.",
                    ],
                },
                "help": {
                    "patterns": ["help", "support", "how", "explain", "clarify"],
                    "responses": [
                        "I'm here to help! What would you like to know?",
                        "I can assist you with: Products, Sales, Inventory, Reports.",
                        "Would you like an explanation of a specific feature? Ask me!",
                    ],
                },
                "thanks": {
                    "patterns": ["thanks", "thank you", "appreciated"],
                    "responses": [
                        "You're welcome! Happy to help.",
                        "No problem! I'm always here.",
                        "Glad to be of service! 😊",
                    ],
                },
                "unknown": {
                    "responses": [
                        "Sorry, I didn't understand your question. Could you rephrase it?",
                        "I can help with: Products, Sales, Inventory, Reports. What do you need?",
                        "Unfortunately, I can't answer that question. Try another one!",
                    ]
                },
            },
        }

    def _detect_language(self, message: str) -> str:
        """كشف لغة الرسالة"""
        # تحقق من وجود أحرف عربية
        arabic_pattern = re.compile(r"[\u0600-\u06FF]")
        if arabic_pattern.search(message):
            return "ar"
        return "en"

    def _match_intent(self, message: str, language: str) -> Tuple[Optional[str], float]:
        """
        تحديد النية من الرسالة

        Returns:
            (intent_name, confidence_score)
        """
        message_lower = message.lower()
        best_intent = None
        best_score = 0.0

        kb = self.knowledge_base.get(language, {})

        for intent_name, intent_data in kb.items():
            if intent_name == "unknown":
                continue

            patterns = intent_data.get("patterns", [])
            if not patterns:
                continue

            # حساب عدد التطابقات
            matches = sum(1 for pattern in patterns if pattern.lower() in message_lower)

            if matches > 0:
                # حساب النتيجة بناءً على عدد التطابقات ونسبة الأنماط المطابقة
                score = matches / max(len(patterns), 1)
                # زيادة النتيجة إذا كان هناك تطابق كامل
                if any(pattern.lower() == message_lower.strip() for pattern in patterns):
                    score = min(score + 0.3, 1.0)
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

        return best_intent, best_score

    def process_message(self, message: str, user_id: Optional[str] = None) -> Dict:
        """
        معالجة رسالة المستخدم وإرجاع الرد

        Args:
            message: رسالة المستخدم
            user_id: معرف المستخدم (اختياري)

        Returns:
            Dict مع الرد والبيانات الوصفية
        """
        language = self._detect_language(message)
        intent, confidence = self._match_intent(message, language)

        # اختيار الرد المناسب
        kb = self.knowledge_base.get(language, {})

        if intent and confidence > 0.2:
            intent_data = kb.get(intent, {})
            responses = intent_data.get("responses", [])
            if not responses:
                responses = kb.get("unknown", {}).get("responses", ["I cannot answer this question."])
        else:
            responses = kb.get("unknown", {}).get("responses", ["I cannot answer this question."])

        # اختيار رد عشوائي من القائمة

        response_text = random.choice(responses)

        # حفظ في سجل المحادثة
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "language": language,
            "intent": intent,
            "confidence": confidence,
            "response": response_text,
        }
        self.conversation_history.append(conversation_entry)

        return {
            "response": response_text,
            "language": language,
            "intent": intent,
            "confidence": confidence,
            "timestamp": conversation_entry["timestamp"],
        }

    def get_conversation_history(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        الحصول على سجل المحادثات

        Args:
            user_id: تصفية حسب معرف المستخدم
            limit: الحد الأقصى للنتائج

        Returns:
            قائمة بسجلات المحادثات
        """
        history = self.conversation_history

        if user_id:
            history = [h for h in history if h.get("user_id") == user_id]

        return history[-limit:]

    def clear_history(self, user_id: Optional[str] = None):
        """مسح سجل المحادثات"""
        if user_id:
            self.conversation_history = [h for h in self.conversation_history if h.get("user_id") != user_id]
        else:
            self.conversation_history = []


# مثيل عام للـ Chatbot
chatbot = ChatbotEngine()


def chat(message: str, user_id: Optional[str] = None) -> str:
    """
    دالة مختصرة للتحدث مع الـ Chatbot

    Args:
        message: رسالة المستخدم
        user_id: معرف المستخدم

    Returns:
        الرد النصي
    """
    result = chatbot.process_message(message, user_id)
    return result["response"]


if __name__ == "__main__":
    # اختبار الـ Chatbot
    print("🤖 Chatbot Test - اختبار الروبوت")
    print("=" * 50)

    test_messages = [
        "مرحبا",
        "كيف أضيف منتج جديد؟",
        "أريد تقرير المبيعات",
        "Hello",
        "How do I check inventory?",
        "Thanks!",
    ]

    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        response = chat(msg, user_id="test_user")
        print(f"🤖 Bot: {response}")

    print("\n" + "=" * 50)
    print("✅ Chatbot test completed!")
