import random  # nosec B311
import re


class SmartAssistantService:
    """
    Service for parsing natural language commands and determining user intent.
    Bridging the gap towards Goal 2030 (Conversational AI).
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.intents = {
            "SHOW_SALES": [
                r"مبيعات",
                r"sales",
                r"sold",
                r"بعنا",
                r"income",
                r"revenue",
                r"دخل",
            ],
            "CHECK_STOCK": [
                r"stock",
                r"inventory",
                r"qty",
                r"quantity",
                r"مخزون",
                r"كمية",
                r"باقي",
                r"توفر",
            ],
            "ADD_PRODUCT": [
                r"add product",
                r"new product",
                r"create product",
                r"منتج جديد",
                r"إضافة منتج",
            ],
            "NAVIGATE": [r"go to", r"open", r"show", r"افتح", r"إذهب", r"عرض"],
            "AGENTIC_FIX": [
                r"fix",
                r"reorder",
                r"order",
                r"draft",
                r"طلب",
                r"إعادة طلب",
                r"شراء",
            ],
            "GREETING": [r"hello", r"hi", r"salam", r"مرحبا", r"اهلين", r"السلام"],
        }

    def parse_command(self, text: str):
        """
        Parse the input text and return an intent and entities.
        """
        text = text.lower().strip()

        # 1. Identify Intent
        detected_intent = None
        for intent, patterns in self.intents.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    detected_intent = intent
                    break
            if detected_intent:
                break

        # Default fallback
        if not detected_intent:
            return {
                "intent": "UNKNOWN",
                "response": "عذراً، لم أفهم طلبك. هل يمكن صياغته بطريقة أخرى؟",
                "action": None,
            }

        # 2. Extract Entities (Basic)
        entities = {}

        # Extract numbers (quantity)
        num_match = re.search(r"\d+", text)
        if num_match:
            entities["number"] = int(num_match.group())

        # Extract product names (Simulated: assumes words after specific keywords are products)
        # In a real NLP engine, this would use NER (Named Entity Recognition)
        if detected_intent == "CHECK_STOCK":
            # Try to grab everything after the keyword
            pass

        # 3. Formulate Response & Action
        response = ""
        action = None

        if detected_intent == "GREETING":
            response = random.choice(
                [
                    "مرحباً بك! كيف يمكنني مساعدتك اليوم؟",
                    "أهلاً! أنا هنا لمساعدتك في إدارة متجرك.",
                    "وعليكم السلام! جاهز للأوامر.",
                ]
            )

        elif detected_intent == "SHOW_SALES":
            response = "جاري عرض تقرير المبيعات..."
            action = {"type": "NAVIGATE", "target": "sales_dashboard"}

        elif detected_intent == "CHECK_STOCK":
            response = "سأتحقق من المخزون لك."
            action = {"type": "NAVIGATE", "target": "inventory"}

        elif detected_intent == "ADD_PRODUCT":
            response = "فتح نموذج إضافة منتج جديد."
            action = {"type": "OPEN_DIALOG", "target": "add_product"}

        elif detected_intent == "AGENTIC_FIX":
            response = "تحليل المنتجات المنخفضة لاقتراح طلبات شراء..."
            action = {"type": "TRIGGER_AGENT", "action": "REORDER"}

        return {
            "intent": detected_intent,
            "response": response,
            "action": action,
            "entities": entities,
        }

    def get_suggestions(self):
        """Return suggestion chips for the UI"""
        return ["عرض المبيعات", "فحص المخزون", "منتج جديد", "تنبيهات الذكاء الاصطناعي"]
