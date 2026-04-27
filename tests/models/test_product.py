"""
اختبارات شاملة لنموذج Product
Comprehensive tests for Product model
"""

import unittest
import pytest
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


class TestProductManager:
    """اختبارات ProductManager باستخدام pytest"""
    
    @pytest.mark.usefixtures("db_manager")
    def test_update_stock_blocks_negative_inventory(self, db_manager):
        """اختبار منع تحديث المخزون بقيمة سالبة"""
        # إنشاء منتج بمخزون 0
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Product", "قطعة", 10.0, 15.0, 0, 1, 1))
        product_id = cursor.lastrowid
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        result = manager.update_stock(product_id, -5)  # محاولة طرح 5
        
        assert result is False
        # التحقق من عدم تغيير المخزون
        product = manager.get_product_by_id(product_id)
        assert product.current_stock == 0

    @pytest.mark.usefixtures("db_manager")
    def test_get_low_stock_products_parses_rows(self, db_manager):
        """اختبار الحصول على منتجات المخزون المنخفض"""
        # إنشاء منتج بمخزون منخفض (current_stock <= min_stock)
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, min_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Low Stock Test", "قطعة", 2.0, 5.0, 2, 10, 1, 1))
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        products = manager.get_low_stock_products()
        
        # التحقق من وجود منتج واحد على الأقل
        assert len(products) >= 1
        # التحقق من وجود منتجنا في النتائج
        low_stock_product = next((p for p in products if p.name == "Low Stock Test"), None)
        assert low_stock_product is not None
        assert low_stock_product.is_low_stock is True

    @pytest.mark.usefixtures("db_manager")
    def test_search_products_respects_filters_and_limits(self, db_manager):
        """اختبار البحث مع الفلاتر والحدود"""
        # إنشاء فئة جديدة للاختبار
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT INTO categories (name, is_active) VALUES (?, ?)", ("SearchCat", 1))
        search_cat_id = cursor.lastrowid
        
        # إنشاء منتج للبحث
        cursor.execute("""
            INSERT INTO products (name, name_en, barcode, unit, cost_price, selling_price, 
                                current_stock, category_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Search Hit", "Hit", "BC123", "قطعة", 4.0, 8.0, 5, search_cat_id, 1))
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        products = manager.search_products(search_term="Hit", category_id=search_cat_id, active_only=True, limit=1, offset=0)
        
        assert len(products) == 1
        assert products[0].category_id == search_cat_id

    @pytest.mark.usefixtures("db_manager")
    def test_get_stock_report_maps_tuple(self, db_manager):
        """اختبار تقرير المخزون"""
        # الحصول على التقرير الحالي أولاً
        manager = ProductManager(db_manager)
        initial_report = manager.get_stock_report()
        initial_count = initial_report["total_products"]
        
        # إنشاء منتجات للتقرير
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?),
                (?, ?, ?, ?, ?, ?, ?)
        """, ("Product1", "قطعة", 10.0, 15.0, 50, 1, 1,
              "Product2", "قطعة", 20.0, 30.0, 100, 1, 1))
        db_manager.connection.commit()
        cursor.close()
        
        report = manager.get_stock_report()

        # التحقق من زيادة عدد المنتجات
        assert report["total_products"] == initial_count + 2
        assert report["active_products"] >= 2
        assert report["total_stock_value"] > 0
    
    @pytest.mark.usefixtures("db_manager")
    def test_update_product_success(self, db_manager):
        """اختبار تحديث منتج بنجاح"""
        # إنشاء منتج أولاً
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Original", "قطعة", 100.0, 150.0, 50, 1, 1))
        product_id = cursor.lastrowid
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        
        product = Product(
            id=product_id,
            name="منتج محدث",
            unit="قطعة",
            cost_price=Decimal('120.00'),
            selling_price=Decimal('180.00')
        )
        
        result = manager.update_product(product)
        assert result is True
        
        # التحقق من التحديث
        updated = manager.get_product_by_id(product_id)
        assert updated.name == "منتج محدث"
        assert updated.selling_price == Decimal('180.00')
    
    @pytest.mark.usefixtures("db_manager")
    def test_delete_product_soft(self, db_manager):
        """اختبار حذف منتج بشكل ناعم"""
        # إنشاء منتج
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("To Delete", "قطعة", 10.0, 15.0, 50, 1, 1))
        product_id = cursor.lastrowid
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        result = manager.delete_product(product_id, soft_delete=True)
        
        assert result is True
        # التحقق من الحذف الناعم
        product = manager.get_product_by_id(product_id)
        assert product.is_active is False
    
    @pytest.mark.usefixtures("db_manager")
    def test_delete_product_hard(self, db_manager):
        """اختبار حذف منتج بشكل صلب"""
        # إنشاء منتج
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("To Delete", "قطعة", 10.0, 15.0, 50, 1, 1))
        product_id = cursor.lastrowid
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        result = manager.delete_product(product_id, soft_delete=False)
        
        assert result is True
        # التحقق من الحذف الصلب
        product = manager.get_product_by_id(product_id)
        assert product is None
    
    @pytest.mark.usefixtures("db_manager")
    def test_get_product_by_barcode(self, db_manager):
        """اختبار الحصول على منتج بالباركود"""
        # استخدام باركود فريد
        import uuid
        barcode = f"BC_{uuid.uuid4().hex[:8]}"
        
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, barcode, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Product Barcode", barcode, "قطعة", 10.0, 15.0, 50, 1, 1))
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        product = manager.get_product_by_barcode(barcode)
        
        assert product is not None
        assert product.barcode == barcode
    
    @pytest.mark.usefixtures("db_manager")
    def test_get_products_by_category(self, db_manager):
        """اختبار الحصول على منتجات فئة معينة"""
        # إنشاء فئة جديدة
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT INTO categories (name, is_active) VALUES (?, ?)", ("Electronics", 1))
        cat_id = cursor.lastrowid
        
        # إنشاء منتج في الفئة
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, category_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Category Product", "قطعة", 20.0, 30.0, 100, cat_id, 1))
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        products = manager.get_products_by_category(cat_id)
        
        assert len(products) == 1
        assert products[0].category_id == cat_id
    
    @pytest.mark.usefixtures("db_manager")
    def test_get_all_products(self, db_manager):
        """اختبار الحصول على جميع المنتجات"""
        # إنشاء منتج أولاً
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("All Product", "قطعة", 25.0, 35.0, 75, 1, 1))
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        products = manager.get_all_products(active_only=True)
        
        assert isinstance(products, list)
        assert len(products) >= 1
    
    @pytest.mark.usefixtures("db_manager")
    def test_update_stock_positive(self, db_manager):
        """اختبار تحديث المخزون بقيمة إيجابية"""
        # إنشاء منتج بمخزون 50
        cursor = db_manager.connection.cursor()
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, is_active) VALUES (1, 'General', 1)")
        cursor.execute("""
            INSERT INTO products (name, unit, cost_price, selling_price, current_stock, is_active, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Stock Product", "قطعة", 15.0, 20.0, 50, 1, 1))
        product_id = cursor.lastrowid
        db_manager.connection.commit()
        cursor.close()
        
        manager = ProductManager(db_manager)
        # Note: update_stock يعين القيمة الجديدة وليس يضيف إليها
        result = manager.update_stock(product_id, 60)  # تعيين إلى 60
        
        assert result is True
        # التحقق من تحديث المخزون
        updated = manager.get_product_by_id(product_id)
        assert updated.current_stock == 60


if __name__ == '__main__':
    unittest.main()



