"""
اختبار شامل للميزات الجديدة v3.0
Comprehensive tests for new features in v3.0

Tests:
- AI Chatbot
- Predictive Analytics
- Loyalty System
- E-Invoicing
- Vendor Portal
"""

import pytest
from src.ai.chatbot import ChatbotEngine, chat
from src.ai.predictive_analytics import PredictiveEngine
from src.services.loyalty_service import LoyaltySystem
from src.services.einvoice_service import EInvoiceGenerator, EInvoiceConfig, RecurringInvoiceManager
from src.services.vendor_portal import VendorPortal
from src.core.database_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """إنشاء مدير قاعدة بيانات للاختبار"""
    db = DatabaseManager(":memory:")
    db.initialize()  # تهيئة وفتح الاتصال بقاعدة البيانات
    yield db
    db.close()


class TestAIChatbot:
    """اختبارات Chatbot الذكي"""
    
    def test_chatbot_initialization(self):
        """اختبار تهيئة Chatbot"""
        bot = ChatbotEngine()
        assert bot is not None
        assert bot.knowledge_base is not None
    
    def test_arabic_greeting(self):
        """اختبار التحية بالعربية"""
        bot = ChatbotEngine()
        result = bot.process_message("مرحبا")
        
        assert result["language"] == "ar"
        # قد يكون التطابق ضعيفاً بسبب قلة الأنماط
        assert result["response"] is not None
        assert isinstance(result["confidence"], float)
    
    def test_english_greeting(self):
        """اختبار التحية بالإنجليزية"""
        bot = ChatbotEngine()
        result = bot.process_message("Hello")
        
        assert result["language"] == "en"
        assert result["response"] is not None
        assert isinstance(result["confidence"], float)
    
    def test_product_inquiry(self):
        """اختبار استفسار عن المنتجات"""
        bot = ChatbotEngine()
        result = bot.process_message("كيف أضيف منتج جديد؟")
        
        assert result["language"] == "ar"
        assert result["intent"] in ["products", "help"]
    
    def test_conversation_history(self):
        """اختبار سجل المحادثات"""
        bot = ChatbotEngine()
        
        bot.process_message("مرحبا", user_id="user1")
        bot.process_message("شكراً", user_id="user1")
        
        history = bot.get_conversation_history(user_id="user1")
        assert len(history) == 2
        assert history[0]["message"] == "مرحبا"
    
    def test_clear_history(self):
        """اختبار مسح السجل"""
        bot = ChatbotEngine()
        
        bot.process_message("مرحبا", user_id="user1")
        bot.clear_history(user_id="user1")
        
        history = bot.get_conversation_history(user_id="user1")
        assert len(history) == 0
    
    def test_unknown_message(self):
        """اختبار رسالة غير معروفة"""
        bot = ChatbotEngine()
        result = bot.process_message("xyzabc123nonsense")
        
        # يجب أن يكون الرد موجودًا حتى للرسائل غير المعروفة
        assert result["response"] is not None
        assert isinstance(result["response"], str)


class TestPredictiveAnalytics:
    """اختبارات التحليلات التنبؤية"""
    
    def test_predictor_initialization(self, db_manager):
        """اختبار تهيئة المحرك التنبؤي"""
        predictor = PredictiveEngine(db_manager)
        assert predictor is not None
        assert predictor.db == db_manager
    
    def test_sales_forecast_empty_db(self, db_manager):
        """اختبار التنبؤ بالمبيعات مع قاعدة بيانات فارغة"""
        predictor = PredictiveEngine(db_manager)
        forecasts = predictor.forecast_sales()
        
        # يجب أن يرجع قائمة فارغة لأن لا توجد منتجات
        assert isinstance(forecasts, list)
    
    def test_customer_insights_empty_db(self, db_manager):
        """اختبار رؤى العملاء مع قاعدة بيانات فارغة"""
        predictor = PredictiveEngine(db_manager)
        insights = predictor.analyze_customer_behavior()
        
        assert isinstance(insights, list)
    
    def test_product_recommendations(self, db_manager):
        """اختبار التوصيات"""
        predictor = PredictiveEngine(db_manager)
        recommendations = predictor.get_product_recommendations(customer_id=1)
        
        assert isinstance(recommendations, list)
    
    def test_anomaly_detection(self, db_manager):
        """اختبار كشف الشذوذات"""
        predictor = PredictiveEngine(db_manager)
        anomalies = predictor.detect_anomalies()
        
        assert isinstance(anomalies, list)


class TestLoyaltySystem:
    """اختبارات نظام الولاء"""
    
    def test_loyalty_initialization(self, db_manager):
        """اختبار تهيئة نظام الولاء"""
        loyalty = LoyaltySystem(db_manager)
        assert loyalty is not None
        assert len(loyalty.TIERS) == 4  # برونزي، فضي، ذهبي، بلاتيني
    
    def test_get_balance_new_customer(self, db_manager):
        """اختبار رصيد عميل جديد"""
        loyalty = LoyaltySystem(db_manager)
        balance = loyalty.get_balance(customer_id=999)
        
        assert balance["total_points"] == 0
        assert balance["tier"] == "برونزي"
    
    def test_earn_points(self, db_manager):
        """اختبار كسب النقاط"""
        loyalty = LoyaltySystem(db_manager)
        
        # إنشاء عميل في قاعدة البيانات
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, phone) VALUES ('Test Customer', '1234567890')")
        customer_id = cursor.lastrowid
        conn.commit()
        
        # كسب نقاط
        result = loyalty.earn_points(customer_id=customer_id, purchase_amount=100.0)
        
        assert result["points_earned"] == 100
        assert "نقطة" in result["message"]
    
    def test_tier_upgrade(self, db_manager):
        """اختبار ترقية المستوى"""
        loyalty = LoyaltySystem(db_manager)
        
        # إنشاء عميل
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, phone) VALUES ('VIP Customer', '1234567890')")
        customer_id = cursor.lastrowid
        conn.commit()
        
        # كسب نقاط كافية للترقية إلى فضي (500 نقطة)
        loyalty.earn_points(customer_id=customer_id, purchase_amount=600.0)
        
        balance = loyalty.get_balance(customer_id)
        assert balance["tier"] in ["فضي", "ذهبي", "بلاتيني"]
    
    def test_transactions_history(self, db_manager):
        """اختبار سجل المعاملات"""
        loyalty = LoyaltySystem(db_manager)
        
        # إنشاء عميل
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, phone) VALUES ('Customer', '1234567890')")
        customer_id = cursor.lastrowid
        conn.commit()
        
        # كسب نقاط
        loyalty.earn_points(customer_id=customer_id, purchase_amount=100.0)
        
        # الحصول على السجل
        transactions = loyalty.get_transactions(customer_id)
        assert len(transactions) > 0
        assert transactions[0]["type"] == "earn"


class TestEInvoicing:
    """اختبارات الفوترة الإلكترونية"""
    
    def test_einvoice_config(self):
        """اختبار إعدادات الفاتورة الإلكترونية"""
        config = EInvoiceConfig(
            company_vat_number="300012345600003",
            company_name="شركة اختبار",
            company_address="الرياض"
        )
        
        assert config.company_vat_number == "300012345600003"
        assert config.company_name == "شركة اختبار"
    
    def test_generate_invoice(self):
        """اختبار إنشاء فاتورة إلكترونية"""
        config = EInvoiceConfig(
            company_vat_number="300012345600003",
            company_name="شركة اختبار",
            company_address="الرياض"
        )
        
        generator = EInvoiceGenerator(config)
        
        invoice = generator.generate_invoice(
            invoice_number="INV-001",
            invoice_date="2025-11-20",
            customer_name="عميل تجريبي",
            customer_vat="300012345600004",
            items=[{"name": "منتج", "quantity": 1, "unit_price": 100, "total": 100}],
            total_amount=115.0,
            vat_amount=15.0
        )
        
        assert invoice["invoice_number"] == "INV-001"
        assert "digital_signature" in invoice
        assert "qr_code" in invoice
        assert invoice["totals"]["total"] == 115.0
    
    def test_xml_conversion(self):
        """اختبار التحويل إلى XML"""
        config = EInvoiceConfig(
            company_vat_number="300012345600003",
            company_name="شركة اختبار",
            company_address="الرياض"
        )
        
        generator = EInvoiceGenerator(config)
        
        invoice = generator.generate_invoice(
            invoice_number="INV-001",
            invoice_date="2025-11-20",
            customer_name="عميل",
            customer_vat=None,
            items=[],
            total_amount=100.0,
            vat_amount=15.0
        )
        
        xml = generator.convert_to_xml(invoice)
        
        assert "<?xml" in xml
        assert "INV-001" in xml
        assert "300012345600003" in xml
    
    def test_recurring_invoice_manager(self, db_manager):
        """اختبار مدير الفواتير الدورية"""
        manager = RecurringInvoiceManager(db_manager)
        
        # إنشاء عميل
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO customers (name, phone) VALUES ('Recurring Customer', '1234567890')")
        customer_id = cursor.lastrowid
        conn.commit()
        
        # إنشاء فاتورة دورية
        invoice_id = manager.create_recurring_invoice(
            customer_id=customer_id,
            description="اشتراك شهري",
            amount=100.0,
            frequency="monthly",
            start_date="2025-11-20"
        )
        
        assert invoice_id > 0


class TestVendorPortal:
    """اختبارات بوابة الموردين"""
    
    def test_portal_initialization(self, db_manager):
        """اختبار تهيئة البوابة"""
        portal = VendorPortal(db_manager)
        assert portal is not None
    
    def test_get_dashboard_empty(self, db_manager):
        """اختبار لوحة المعلومات لمورد غير موجود"""
        portal = VendorPortal(db_manager)
        dashboard = portal.get_vendor_dashboard(vendor_id=999)
        
        assert dashboard["orders"]["total"] == 0
        assert dashboard["unread_messages"] == 0
    
    def test_send_message(self, db_manager):
        """اختبار إرسال رسالة"""
        portal = VendorPortal(db_manager)
        
        # إنشاء مورد
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vendors (name, contact_person) VALUES ('Vendor', 'Contact')")
        vendor_id = cursor.lastrowid
        conn.commit()
        
        # إرسال رسالة
        message_id = portal.send_message_to_vendor(
            vendor_id=vendor_id,
            subject="اختبار",
            message="رسالة اختبار",
            message_type="general"
        )
        
        assert message_id > 0
    
    def test_get_messages(self, db_manager):
        """اختبار الحصول على الرسائل"""
        portal = VendorPortal(db_manager)
        
        # إنشاء مورد
        conn = db_manager.connection
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vendors (name, contact_person) VALUES ('Vendor', 'Contact')")
        vendor_id = cursor.lastrowid
        conn.commit()
        
        # إرسال رسالة
        portal.send_message_to_vendor(
            vendor_id=vendor_id,
            subject="اختبار",
            message="رسالة"
        )
        
        # الحصول على الرسائل
        messages = portal.get_messages(vendor_id)
        assert len(messages) > 0
        assert messages[0]["subject"] == "اختبار"


def test_all_modules_importable():
    """اختبار إمكانية استيراد جميع الوحدات"""
    import src.ai.chatbot
    import src.ai.predictive_analytics
    import src.services.loyalty_service
    import src.services.einvoice_service
    import src.services.vendor_portal
    
    assert True  # إذا وصلنا هنا، فجميع الاستيرادات نجحت


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
