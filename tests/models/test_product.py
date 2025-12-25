"""
اختبارات شاملة لنموذج Product
Comprehensive tests for Product model
"""

import unittest
from decimal import Decimal
from datetime import datetime
from src.models.product import Product, ProductManager


class TestProductDataclass(unittest.TestCase):
    """اختبارات Product dataclass"""

    def test_product_creation_default(self):
        """إنشاء منتج بقيم افتراضية"""
        product = Product()
        self.assertIsNone(product.id)
        self.assertEqual(product.name, "")
        self.assertEqual(product.unit, "قطعة")
        self.assertEqual(product.cost_price, Decimal('0.00'))
        self.assertEqual(product.selling_price, Decimal('0.00'))
        self.assertTrue(product.is_active)

    def test_product_creation_with_values(self):
        """إنشاء منتج بقيم محددة"""
        product = Product(
            id=1,
            name="منتج تجريبي",
            barcode="123456",
            cost_price=Decimal('50.00'),
            selling_price=Decimal('75.00'),
            current_stock=100
        )
        self.assertEqual(product.id, 1)
        self.assertEqual(product.name, "منتج تجريبي")
        self.assertEqual(product.barcode, "123456")
        self.assertEqual(product.cost_price, Decimal('50.00'))
        self.assertEqual(product.selling_price, Decimal('75.00'))
        self.assertEqual(product.current_stock, 100)

    def test_price_conversion_from_int(self):
        """تحويل الأسعار من int إلى Decimal"""
        product = Product(cost_price=100, selling_price=150)
        self.assertIsInstance(product.cost_price, Decimal)
        self.assertIsInstance(product.selling_price, Decimal)
        self.assertEqual(product.cost_price, Decimal('100'))
        self.assertEqual(product.selling_price, Decimal('150'))

    def test_price_conversion_from_float(self):
        """تحويل الأسعار من float إلى Decimal"""
        product = Product(cost_price=99.99, selling_price=149.99)
        self.assertIsInstance(product.cost_price, Decimal)
        self.assertIsInstance(product.selling_price, Decimal)

    def test_price_conversion_from_string(self):
        """تحويل الأسعار من string إلى Decimal"""
        product = Product(cost_price="50.50", selling_price="75.75")
        self.assertIsInstance(product.cost_price, Decimal)
        self.assertIsInstance(product.selling_price, Decimal)
        self.assertEqual(product.cost_price, Decimal('50.50'))
        self.assertEqual(product.selling_price, Decimal('75.75'))


class TestProductProperties(unittest.TestCase):
    """اختبارات خصائص Product المحسوبة"""

    def test_profit_margin_calculation(self):
        """حساب هامش الربح"""
        product = Product(cost_price=Decimal('100'), selling_price=Decimal('150'))
        expected_margin = Decimal('50.00')
        self.assertEqual(product.profit_margin, expected_margin)

    def test_profit_margin_zero_cost(self):
        """هامش الربح عند تكلفة صفر"""
        product = Product(cost_price=Decimal('0'), selling_price=Decimal('100'))
        self.assertEqual(product.profit_margin, Decimal('0.00'))

    def test_profit_amount_calculation(self):
        """حساب مبلغ الربح"""
        product = Product(cost_price=Decimal('80'), selling_price=Decimal('120'))
        self.assertEqual(product.profit_amount, Decimal('40'))

    def test_profit_amount_negative(self):
        """مبلغ الربح سالب (خسارة)"""
        product = Product(cost_price=Decimal('150'), selling_price=Decimal('100'))
        self.assertEqual(product.profit_amount, Decimal('-50'))

    def test_stock_value_calculation(self):
        """حساب قيمة المخزون"""
        product = Product(cost_price=Decimal('25.50'), current_stock=100)
        self.assertEqual(product.stock_value, Decimal('2550.00'))

    def test_stock_value_zero_stock(self):
        """قيمة المخزون عند مخزون صفر"""
        product = Product(cost_price=Decimal('100'), current_stock=0)
        self.assertEqual(product.stock_value, Decimal('0'))

    def test_is_low_stock_true(self):
        """فحص المخزون المنخفض - true"""
        product = Product(current_stock=5, min_stock=10)
        self.assertTrue(product.is_low_stock)

    def test_is_low_stock_equal(self):
        """فحص المخزون المنخفض - متساوي"""
        product = Product(current_stock=10, min_stock=10)
        self.assertTrue(product.is_low_stock)

    def test_is_low_stock_false(self):
        """فحص المخزون المنخفض - false"""
        product = Product(current_stock=20, min_stock=10)
        self.assertFalse(product.is_low_stock)


class TestProductToDict(unittest.TestCase):
    """اختبارات تحويل Product إلى dict"""

    def test_to_dict_basic(self):
        """تحويل منتج أساسي إلى dict"""
        product = Product(
            id=1,
            name="Test Product",
            cost_price=Decimal('100'),
            selling_price=Decimal('150')
        )
        result = product.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "Test Product")
        self.assertEqual(result['cost_price'], 100.0)
        self.assertEqual(result['selling_price'], 150.0)

    def test_to_dict_all_fields(self):
        """تحويل منتج كامل إلى dict"""
        now = datetime.now()
        product = Product(
            id=1,
            name="منتج كامل",
            name_en="Full Product",
            barcode="ABC123",
            category_id=5,
            category_name="إلكترونيات",
            unit="صندوق",
            cost_price=Decimal('200'),
            selling_price=Decimal('300'),
            min_stock=10,
            current_stock=50,
            description="وصف المنتج",
            image_path="/path/to/image.jpg",
            is_active=True,
            created_at=now,
            updated_at=now
        )
        result = product.to_dict()
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], "منتج كامل")
        self.assertEqual(result['name_en'], "Full Product")
        self.assertEqual(result['barcode'], "ABC123")
        self.assertEqual(result['category_id'], 5)
        self.assertEqual(result['category_name'], "إلكترونيات")
        self.assertEqual(result['unit'], "صندوق")
        self.assertEqual(result['cost_price'], 200.0)
        self.assertEqual(result['selling_price'], 300.0)
        self.assertEqual(result['min_stock'], 10)
        self.assertEqual(result['current_stock'], 50)
        self.assertEqual(result['description'], "وصف المنتج")
        self.assertEqual(result['image_path'], "/path/to/image.jpg")
        self.assertTrue(result['is_active'])
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['updated_at'])

    def test_to_dict_computed_properties(self):
        """فحص الخصائص المحسوبة في dict"""
        product = Product(
            cost_price=Decimal('100'),
            selling_price=Decimal('150'),
            current_stock=20,
            min_stock=10
        )
        result = product.to_dict()
        
        self.assertEqual(result['profit_margin'], 50.0)
        self.assertEqual(result['profit_amount'], 50.0)
        self.assertEqual(result['stock_value'], 2000.0)
        self.assertFalse(result['is_low_stock'])

    def test_to_dict_none_dates(self):
        """تحويل منتج مع تواريخ None"""
        product = Product(name="Test")
        result = product.to_dict()
        
        self.assertIsNone(result['created_at'])
        self.assertIsNone(result['updated_at'])

    def test_to_dict_decimal_to_float_conversion(self):
        """التحقق من تحويل Decimal إلى float"""
        product = Product(
            cost_price=Decimal('99.99'),
            selling_price=Decimal('149.95')
        )
        result = product.to_dict()
        
        self.assertIsInstance(result['cost_price'], float)
        self.assertIsInstance(result['selling_price'], float)
        self.assertAlmostEqual(result['cost_price'], 99.99, places=2)
        self.assertAlmostEqual(result['selling_price'], 149.95, places=2)


class TestProductEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_empty_name(self):
        """منتج باسم فارغ"""
        product = Product(name="")
        self.assertEqual(product.name, "")

    def test_negative_stock(self):
        """مخزون سالب"""
        product = Product(current_stock=-10)
        self.assertEqual(product.current_stock, -10)
        # الحساب يعمل حتى مع قيم سالبة
        self.assertTrue(product.is_low_stock)

    def test_very_large_prices(self):
        """أسعار كبيرة جداً"""
        product = Product(
            cost_price=Decimal('999999999.99'),
            selling_price=Decimal('1000000000.00')
        )
        self.assertGreater(product.selling_price, product.cost_price)
        self.assertGreater(product.profit_amount, Decimal('0'))

    def test_unicode_names(self):
        """أسماء بالعربية والإنجليزية"""
        product = Product(
            name="منتج عربي 123",
            name_en="English Product 123"
        )
        self.assertEqual(product.name, "منتج عربي 123")
        self.assertEqual(product.name_en, "English Product 123")

    def test_special_characters_in_barcode(self):
        """رموز خاصة في الباركود"""
        product = Product(barcode="ABC-123-XYZ")
        self.assertEqual(product.barcode, "ABC-123-XYZ")


class DummyProdResult:
    def __init__(self, rowcount=1, lastrowid=1):
        self.rowcount = rowcount
        self.lastrowid = lastrowid


class DummyProductDB:
    def __init__(self):
        self.fetch_one_results = []
        self.fetch_all_results = []
        self.execute_query_calls = []
        self.last_insert_id = 1
        self.last_fetch_all = None
        self.last_fetch_one = None

    def fetch_one(self, query, params=()):
        self.last_fetch_one = (query, params)
        if self.fetch_one_results:
            return self.fetch_one_results.pop(0)
        return None

    def fetch_all(self, query, params=()):
        self.last_fetch_all = (query, params)
        if self.fetch_all_results:
            return self.fetch_all_results.pop(0)
        return []

    def execute_query(self, query, params=()):
        self.execute_query_calls.append((query, params))
        return DummyProdResult(rowcount=1, lastrowid=self.last_insert_id)

    def execute_insert(self, query, params=()):
        return self.last_insert_id


class TestProductManager(unittest.TestCase):
    def test_update_stock_blocks_negative_inventory(self):
        db = DummyProductDB()
        row = (
            1,
            "Product",
            None,
            None,
            None,
            "قطعة",
            10.0,
            15.0,
            0,
            1,
            None,
            None,
            1,
            None,
            None,
            "Category",
        )
        db.fetch_one_results.append(row)
        manager = ProductManager(db)

        result = manager.update_stock(1, -5)

        self.assertFalse(result)
        updates = [c for c in db.execute_query_calls if "UPDATE" in c[0]]
        self.assertEqual(len(updates), 0)

    def test_get_low_stock_products_parses_rows(self):
        db = DummyProductDB()
        low_row = (
            2,
            "Low",
            None,
            None,
            None,
            "قطعة",
            2.0,
            5.0,
            10,
            2,
            None,
            None,
            1,
            None,
            None,
            "Cat",
        )
        db.fetch_all_results.append([low_row])
        manager = ProductManager(db)

        products = manager.get_low_stock_products()

        self.assertEqual(len(products), 1)
        self.assertTrue(products[0].is_low_stock)

    def test_search_products_respects_filters_and_limits(self):
        db = DummyProductDB()
        row = (
            3,
            "Search Hit",
            "Hit",
            "BC",
            5,
            "قطعة",
            4.0,
            8.0,
            1,
            2,
            None,
            None,
            1,
            None,
            None,
            "Cat",
        )
        db.fetch_all_results.append([row])
        manager = ProductManager(db)

        products = manager.search_products(search_term="Hit", category_id=5, active_only=True, limit=1, offset=0)

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].category_id, 5)
        self.assertIn("LIMIT 1", db.last_fetch_all[0])
        self.assertTrue(all("Hit" in p.name or "Hit" in (p.name_en or "") for p in products))

    def test_get_stock_report_maps_tuple(self):
        db = DummyProductDB()
        db.fetch_one_results.append((10, 8, 2, 1234.5, 6.5))
        manager = ProductManager(db)

        report = manager.get_stock_report()

        self.assertEqual(report["total_products"], 10)
        self.assertEqual(report["active_products"], 8)
        self.assertEqual(report["low_stock_products"], 2)
        self.assertAlmostEqual(report["total_stock_value"], 1234.5)
        self.assertAlmostEqual(report["avg_stock_level"], 6.5)
    
    def test_update_product_success(self):
        """اختبار تحديث منتج بنجاح"""
        db = DummyProductDB()
        db.rowcount = 1
        manager = ProductManager(db)
        
        product = Product(
            id=1,
            name="منتج محدث",
            cost_price=Decimal('120.00'),
            selling_price=Decimal('180.00')
        )
        
        result = manager.update_product(product)
        self.assertTrue(result)
        self.assertIn("UPDATE products", db.execute_query_calls[-1][0])
    
    def test_delete_product_soft(self):
        """اختبار حذف منتج بشكل ناعم"""
        db = DummyProductDB()
        db.rowcount = 1
        manager = ProductManager(db)
        
        result = manager.delete_product(1, soft_delete=True)
        self.assertTrue(result)
        self.assertIn("UPDATE", db.execute_query_calls[-1][0])
        self.assertIn("is_active", db.execute_query_calls[-1][0])
    
    def test_delete_product_hard(self):
        """اختبار حذف منتج بشكل صلب"""
        db = DummyProductDB()
        db.rowcount = 1
        manager = ProductManager(db)
        
        result = manager.delete_product(1, soft_delete=False)
        self.assertTrue(result)
        self.assertIn("DELETE", db.execute_query_calls[-1][0])
    
    def test_get_product_by_barcode(self):
        """اختبار الحصول على منتج بالباركود"""
        db = DummyProductDB()
        row = (
            5, "Product Barcode", None, "BC123", None, "قطعة",
            10.0, 15.0, 50, 10, None, None, 1, None, None, "Category"
        )
        db.fetch_one_results.append(row)
        manager = ProductManager(db)
        
        product = manager.get_product_by_barcode("BC123")
        self.assertIsNotNone(product)
        self.assertEqual(product.id, 5)
        self.assertEqual(product.barcode, "BC123")
    
    def test_get_products_by_category(self):
        """اختبار الحصول على منتجات فئة معينة"""
        db = DummyProductDB()
        row = (
            6, "Category Product", None, None, 3, "قطعة",
            20.0, 30.0, 100, 20, None, None, 1, None, None, "Electronics"
        )
        db.fetch_all_results.append([row])
        manager = ProductManager(db)
        
        products = manager.get_products_by_category(3)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].category_id, 3)
    
    def test_get_all_products(self):
        """اختبار الحصول على جميع المنتجات"""
        db = DummyProductDB()
        row = (
            7, "All Product", None, None, None, "قطعة",
            25.0, 35.0, 75, 15, None, None, 1, None, None, "Category"
        )
        db.fetch_all_results.append([row])
        manager = ProductManager(db)
        
        products = manager.get_all_products(active_only=True)
        self.assertIsInstance(products, list)
        self.assertGreaterEqual(len(products), 1)
    
    def test_update_stock_positive(self):
        """اختبار تحديث المخزون بقيمة إيجابية"""
        db = DummyProductDB()
        row = (
            8, "Stock Product", None, None, None, "قطعة",
            15.0, 20.0, 50, 10, None, None, 1, None, None, "Category"
        )
        db.fetch_one_results.append(row)
        db.rowcount = 1
        manager = ProductManager(db)
        
        result = manager.update_stock(8, 10)
        self.assertTrue(result)
        self.assertIn("UPDATE products", db.execute_query_calls[-1][0])


if __name__ == '__main__':
    unittest.main()
