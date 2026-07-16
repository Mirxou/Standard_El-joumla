"""
اختبارات شاملة لنموذج Currency
Comprehensive tests for Currency model
"""

import unittest
from datetime import datetime

from src.models.currency import Currency


class TestCurrencyCreation(unittest.TestCase):
    """اختبارات إنشاء عملة"""

    def test_currency_creation_basic(self):
        """إنشاء عملة أساسي"""
        currency = Currency(code="USD", name="الدولار الأمريكي", symbol="$")
        self.assertEqual(currency.code, "USD")
        self.assertEqual(currency.name, "الدولار الأمريكي")
        self.assertEqual(currency.symbol, "$")
        self.assertFalse(currency.is_base)
        self.assertTrue(currency.is_active)
        self.assertEqual(currency.decimal_places, 2)

    def test_currency_creation_with_id(self):
        """إنشاء عملة مع معرف"""
        currency = Currency(id=1, code="DZD", name="الدينار الجزائري", symbol="د.ج")
        self.assertEqual(currency.id, 1)
        self.assertEqual(currency.code, "DZD")

    def test_currency_base_currency(self):
        """عملة أساسية"""
        currency = Currency(code="DZD", name="الدينار الجزائري", symbol="د.ج", is_base=True)
        self.assertTrue(currency.is_base)

    def test_currency_inactive(self):
        """عملة غير نشطة"""
        currency = Currency(code="GBP", name="الجنيه الإسترليني", symbol="£", is_active=False)
        self.assertFalse(currency.is_active)

    def test_currency_custom_decimal_places(self):
        """عملة برقم عشري مخصص"""
        currency = Currency(code="KWD", name="الدينار الكويتي", symbol="د.ك", decimal_places=3)
        self.assertEqual(currency.decimal_places, 3)


class TestCurrencyCodes(unittest.TestCase):
    """اختبارات رموز العملات"""

    def test_common_currency_codes(self):
        """رموز العملات الشائعة"""
        codes = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]
        for code in codes:
            currency = Currency(code=code, name=f"Currency {code}", symbol=code[0])
            self.assertEqual(currency.code, code)
            self.assertEqual(len(currency.code), 3)

    def test_arabic_currency_codes(self):
        """رموز العملات العربية"""
        currencies = [
            ("DZD", "الدينار الجزائري", "د.ج"),
            ("EGP", "الجنيه المصري", "ج.م"),
            ("AED", "الدرهم الإماراتي", "د.إ"),
            ("SAR", "الريال السعودي", "﷼"),
        ]
        for code, name, symbol in currencies:
            currency = Currency(code=code, name=name, symbol=symbol)
            self.assertEqual(currency.code, code)
            self.assertEqual(currency.name, name)
            self.assertEqual(currency.symbol, symbol)


class TestCurrencySymbols(unittest.TestCase):
    """اختبارات رموز العملات"""

    def test_currency_symbols(self):
        """رموز عملات مختلفة"""
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "DZD": "د.ج",
        }
        for code, symbol in currency_symbols.items():
            currency = Currency(code=code, name="Test", symbol=symbol)
            self.assertEqual(currency.symbol, symbol)

    def test_currency_symbol_empty(self):
        """رمز عملة فارغ"""
        currency = Currency(code="TEST", name="Test Currency", symbol="")
        self.assertEqual(currency.symbol, "")


class TestCurrencyDecimalPlaces(unittest.TestCase):
    """اختبارات الأرقام العشرية"""

    def test_decimal_places_common(self):
        """الأرقام العشرية الشائعة"""
        # معظم العملات تستخدم 2
        currency_2 = Currency(code="USD", name="Dollar", symbol="$", decimal_places=2)
        self.assertEqual(currency_2.decimal_places, 2)

        # بعض العملات تستخدم 0 (JPY)
        currency_0 = Currency(code="JPY", name="Yen", symbol="¥", decimal_places=0)
        self.assertEqual(currency_0.decimal_places, 0)

        # بعض العملات تستخدم 3 (KWD)
        currency_3 = Currency(code="KWD", name="Dinar", symbol="د.ك", decimal_places=3)
        self.assertEqual(currency_3.decimal_places, 3)

    def test_decimal_places_zero(self):
        """صفر أرقام عشرية"""
        currency = Currency(code="JPY", name="اليين الياباني", symbol="¥", decimal_places=0)
        self.assertEqual(currency.decimal_places, 0)

    def test_decimal_places_high_precision(self):
        """دقة عالية للأرقام العشرية"""
        currency = Currency(code="BTC", name="Bitcoin", symbol="₿", decimal_places=8)
        self.assertEqual(currency.decimal_places, 8)


class TestCurrencyToDict(unittest.TestCase):
    """اختبارات تحويل العملة إلى قاموس"""

    def test_to_dict_basic(self):
        """تحويل أساسي إلى قاموس"""
        currency = Currency(id=1, code="USD", name="الدولار الأمريكي", symbol="$")
        result = currency.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["code"], "USD")
        self.assertEqual(result["name"], "الدولار الأمريكي")
        self.assertEqual(result["symbol"], "$")
        self.assertEqual(result["is_base"], 0)
        self.assertEqual(result["is_active"], 1)

    def test_to_dict_with_timestamps(self):
        """تحويل مع طوابع زمنية"""
        now = datetime.now()
        currency = Currency(
            code="DZD",
            name="الدينار الجزائري",
            symbol="د.ج",
            created_at=now,
            updated_at=now,
        )
        result = currency.to_dict()

        self.assertIsNotNone(result["created_at"])
        self.assertIsNotNone(result["updated_at"])

    def test_to_dict_boolean_conversion(self):
        """تحويل القيم المنطقية إلى 1/0"""
        currency = Currency(code="USD", name="Dollar", symbol="$", is_base=True, is_active=False)
        result = currency.to_dict()

        self.assertEqual(result["is_base"], 1)
        self.assertEqual(result["is_active"], 0)


class TestCurrencyFromDict(unittest.TestCase):
    """اختبارات إنشاء عملة من قاموس"""

    def test_from_dict_basic(self):
        """إنشاء عملة من قاموس أساسي"""
        data = {
            "code": "EUR",
            "name": "اليورو",
            "symbol": "€",
            "is_base": 0,
            "is_active": 1,
            "decimal_places": 2,
        }
        currency = Currency.from_dict(data)

        self.assertEqual(currency.code, "EUR")
        self.assertEqual(currency.name, "اليورو")
        self.assertEqual(currency.symbol, "€")
        self.assertFalse(currency.is_base)
        self.assertTrue(currency.is_active)

    def test_from_dict_with_id(self):
        """إنشاء عملة مع معرف"""
        data = {"id": 5, "code": "GBP", "name": "الجنيه الإسترليني", "symbol": "£"}
        currency = Currency.from_dict(data)

        self.assertEqual(currency.id, 5)
        self.assertEqual(currency.code, "GBP")

    def test_from_dict_with_timestamps(self):
        """إنشاء عملة مع طوابع زمنية"""
        iso_time = "2024-01-15T10:30:00"
        data = {
            "code": "USD",
            "name": "Dollar",
            "symbol": "$",
            "created_at": iso_time,
            "updated_at": iso_time,
        }
        currency = Currency.from_dict(data)

        self.assertIsNotNone(currency.created_at)
        self.assertIsNotNone(currency.updated_at)

    def test_from_dict_default_values(self):
        """استخدام القيم الافتراضية"""
        data = {"code": "CHF", "name": "الفرنك السويسري"}
        currency = Currency.from_dict(data)

        self.assertEqual(currency.code, "CHF")
        self.assertEqual(currency.decimal_places, 2)
        self.assertFalse(currency.is_base)
        self.assertTrue(currency.is_active)


class TestCurrencyRoundTrip(unittest.TestCase):
    """اختبارات التحويل في كلا الاتجاهين"""

    def test_to_dict_from_dict(self):
        """تحويل إلى قاموس ثم العودة"""
        original = Currency(
            id=1,
            code="USD",
            name="الدولار",
            symbol="$",
            is_base=False,
            is_active=True,
            decimal_places=2,
        )

        as_dict = original.to_dict()
        restored = Currency.from_dict(as_dict)

        self.assertEqual(restored.code, original.code)
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.symbol, original.symbol)
        self.assertEqual(restored.is_active, original.is_active)


class TestCurrencyEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_currency_unicode_names(self):
        """أسماء بـ Unicode"""
        currency = Currency(code="DZD", name="دينار جزائري 🇩🇿", symbol="د.ج")
        self.assertIn("🇩🇿", currency.name)

    def test_currency_code_lowercase(self):
        """رمز العملة بأحرف صغيرة"""
        currency = Currency(code="usd", name="Dollar", symbol="$")
        self.assertEqual(currency.code, "usd")

    def test_currency_long_name(self):
        """اسم عملة طويل"""
        long_name = "الدينار الجزائري الرسمي للجمهورية الجزائرية الديمقراطية الشعبية"
        currency = Currency(code="DZD", name=long_name, symbol="د.ج")
        self.assertEqual(currency.name, long_name)


if __name__ == "__main__":
    unittest.main()
