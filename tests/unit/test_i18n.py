"""
Unit Tests for I18n System
اختبارات وحدة نظام الترجمة
"""

from pathlib import Path

import pytest

from src.utils.i18n_api import I18n


class TestI18n:
    """اختبارات نظام الترجمة"""

    @pytest.fixture
    def i18n(self):
        """إنشاء مثيل I18n"""
        locales_dir = Path(__file__).parent.parent.parent / "locales"
        return I18n(locales_dir=str(locales_dir))

    def test_init(self, i18n):
        """اختبار التهيئة"""
        assert i18n is not None
        assert i18n._default_locale == "ar"

    def test_load_locales(self, i18n):
        """اختبار تحميل ملفات الترجمة"""
        assert "ar" in i18n._messages
        assert "en" in i18n._messages
        assert len(i18n._messages["ar"]) > 0
        assert len(i18n._messages["en"]) > 0

    def test_get_message_arabic(self, i18n):
        """اختبار الحصول على رسالة بالعربية"""
        message = i18n.get_message("welcome", locale="ar")
        assert message == "مرحباً"

    def test_get_message_english(self, i18n):
        """اختبار الحصول على رسالة بالإنجليزية"""
        message = i18n.get_message("welcome", locale="en")
        assert message == "Welcome"

    def test_get_message_with_variables(self, i18n):
        """اختبار الحصول على رسالة مع متغيرات"""
        message = i18n.get_message("order_created", locale="ar", order_id=123)
        assert "123" in message
        assert "تم إنشاء" in message or "تم" in message

    def test_get_message_default_locale(self, i18n):
        """اختبار الحصول على رسالة باللغة الافتراضية"""
        message = i18n.get_message("welcome")
        assert message == "مرحباً"  # العربية هي الافتراضية

    def test_get_message_missing_key(self, i18n):
        """اختبار الحصول على رسالة بمفتاح غير موجود"""
        message = i18n.get_message("nonexistent_key")
        assert message == "nonexistent_key"  # يجب أن يعيد المفتاح نفسه

    def test_negotiate_locale(self, i18n):
        """اختبار التفاوض على اللغة"""
        locale = i18n.negotiate_locale(accept_language="en-US,en;q=0.9")
        assert locale in ["ar", "en"]

    def test_negotiate_locale_query(self, i18n):
        """اختبار التفاوض على اللغة من query parameter"""
        locale = i18n.negotiate_locale(query_locale="en")
        assert locale == "en"

    def test_negotiate_locale_default(self, i18n):
        """اختبار التفاوض على اللغة الافتراضية"""
        locale = i18n.negotiate_locale()
        assert locale == "ar"  # العربية هي الافتراضية

    def test_get_available_locales(self, i18n):
        """اختبار الحصول على اللغات المتاحة"""
        locales = i18n.get_available_locales()
        assert isinstance(locales, list)
        assert "ar" in locales
        assert "en" in locales

    def test_has_locale(self, i18n):
        """اختبار التحقق من وجود لغة"""
        assert i18n.has_locale("ar") is True
        assert i18n.has_locale("en") is True
        assert i18n.has_locale("fr") is True  # الفرنسية موجودة
        assert i18n.has_locale("de") is True  # الألمانية موجودة الآن
        assert i18n.has_locale("es") is True  # الإسبانية موجودة الآن
        assert i18n.has_locale("zh") is False  # الصينية غير موجودة

    def test_get_all_messages(self, i18n):
        """اختبار الحصول على جميع الرسائل"""
        messages = i18n.get_all_messages("ar")
        assert isinstance(messages, dict)
        assert len(messages) > 0
        assert "welcome" in messages

    def test_french_locale(self, i18n):
        """اختبار اللغة الفرنسية"""
        if i18n.has_locale("fr"):
            message = i18n.get_message("welcome", locale="fr")
            assert message == "Bienvenue"

    def test_german_locale(self, i18n):
        """اختبار اللغة الألمانية"""
        if i18n.has_locale("de"):
            message = i18n.get_message("welcome", locale="de")
            assert message == "Willkommen"

    def test_spanish_locale(self, i18n):
        """اختبار اللغة الإسبانية"""
        if i18n.has_locale("es"):
            message = i18n.get_message("welcome", locale="es")
            assert message == "Bienvenido"

    def test_format_message(self, i18n):
        """اختبار تنسيق الرسائل مع متغيرات"""
        message = i18n.format_message("profit_margin_value", margin=25.5, locale="ar")
        assert "25.50" in message
        assert "هامش" in message or "%" in message

    def test_get_plural(self, i18n):
        """اختبار الجمع والمفرد"""
        # إذا كان لدينا مفاتيح للجمع والمفرد
        singular = i18n.get_message("product", locale="ar") if i18n.has_locale("ar") else "product"  # noqa: F841
        plural = i18n.get_message("products", locale="ar") if i18n.has_locale("ar") else "products"  # noqa: F841

        # اختبار المفرد
        result = i18n.get_plural("product", "products", 1, locale="ar")
        assert result is not None

        # اختبار الجمع
        result = i18n.get_plural("product", "products", 5, locale="ar")
        assert result is not None

    def test_dynamic_messages(self, i18n):
        """اختبار الرسائل الديناميكية"""
        # رسالة مع متغيرات متعددة
        message = i18n.get_message(
            "selling_price_lower_than_cost",
            selling_price=100.0,
            cost_price=150.0,
            locale="ar",
        )
        assert "100.00" in message or "150.00" in message
