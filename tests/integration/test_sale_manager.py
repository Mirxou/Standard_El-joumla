"""
Integration Tests for Sale Manager
اختبارات تكامل لـ SaleManager
"""

import random
from datetime import date
from decimal import Decimal

import pytest

from src.models.customer import Customer, CustomerManager
from src.models.product import Product, ProductManager
from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus


@pytest.mark.requires_db
class TestSaleManager:
    """اختبارات SaleManager"""

    def test_create_sale(self, db_manager, sample_product_data, sample_customer_data):
        """اختبار إنشاء فاتورة مبيعات"""
        # إنشاء عميل
        customer_manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)
        customer_id = customer_manager.create_customer(customer)

        if customer_id is None:
            pytest.skip("فشل في إنشاء العميل")

        # إنشاء منتج
        product_manager = ProductManager(db_manager)
        product_data = sample_product_data.copy()
        product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"
        product = Product(**product_data)
        product_id = product_manager.create_product(product)

        if product_id is None:
            pytest.skip("فشل في إنشاء المنتج")

        # إنشاء فاتورة
        sale_manager = SaleManager(db_manager)
        sale = Sale(
            customer_id=customer_id,
            invoice_number=f"INV-{random.randint(1000, 9999)}",
            items=[SaleItem(product_id=product_id, quantity=5, unit_price=product.selling_price)],
            status=SaleStatus.CONFIRMED,
        )

        sale_id = sale_manager.create_sale(sale)
        assert sale_id is not None
        assert sale_id > 0

    def test_get_sale_by_id(self, db_manager, sample_product_data, sample_customer_data):
        """اختبار الحصول على فاتورة بالمعرف"""
        # إنشاء عميل ومنتج وفاتورة
        customer_manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)
        customer_id = customer_manager.create_customer(customer)

        if customer_id is None:
            pytest.skip("فشل في إنشاء العميل")

        product_manager = ProductManager(db_manager)
        product_data = sample_product_data.copy()
        product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"
        product = Product(**product_data)
        product_id = product_manager.create_product(product)

        if product_id is None:
            pytest.skip("فشل في إنشاء المنتج")

        sale_manager = SaleManager(db_manager)
        sale = Sale(
            customer_id=customer_id,
            invoice_number=f"INV-{random.randint(1000, 9999)}",
            items=[SaleItem(product_id=product_id, quantity=3, unit_price=product.selling_price)],
            status=SaleStatus.CONFIRMED,
        )

        sale_id = sale_manager.create_sale(sale)
        assert sale_id is not None

        # الحصول على الفاتورة
        retrieved_sale = sale_manager.get_sale_by_id(sale_id)
        assert retrieved_sale is not None
        assert retrieved_sale.id == sale_id
        assert retrieved_sale.customer_id == customer_id

    def test_get_sales_summary(self, db_manager):
        """اختبار الحصول على ملخص المبيعات"""
        sale_manager = SaleManager(db_manager)

        summary = sale_manager.get_sales_summary()

        assert summary is not None
        assert isinstance(summary, dict)
        assert "total_sales" in summary or "total_amount" in summary

    def test_search_sales(self, db_manager):
        """اختبار البحث في المبيعات"""
        sale_manager = SaleManager(db_manager)

        # البحث بمعايير مختلفة
        results = sale_manager.search_sales(search_term="INV")
        assert isinstance(results, list)

        results = sale_manager.search_sales(status=SaleStatus.CONFIRMED)
        assert isinstance(results, list)

        results = sale_manager.search_sales(start_date=date.today())
        assert isinstance(results, list)

    def test_create_sale_with_auto_conversion(self, db_manager, sample_customer_data):
        """اختبار إنشاء فاتورة مبيعات مع تفعيل التفكيك التلقائي للكرتون"""
        # 1. إنشاء العميل
        customer_manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)
        customer_id = customer_manager.create_customer(customer)

        # 2. إنشاء المنتج الأب (الكرتون)
        cursor = db_manager.connection.cursor()
        cursor.execute("""
            INSERT INTO products (name, barcode, unit, cost_price, selling_price, current_stock, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, ("كرتون حليب", "PARENTBARCODE", "كرتون", 100.0, 120.0, 10))
        parent_id = cursor.lastrowid

        # إنشاء دفعة للمنتج الأب (الكرتون)
        cursor.execute("""
            INSERT INTO batches (product_id, batch_number, quantity, cost_price, selling_price, expiry_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (parent_id, "B-PARENT-01", 10, 100.0, 120.0, "2027-01-01"))
        parent_batch_id = cursor.lastrowid

        # 3. إنشاء المنتج الابن (الحبة) مرتبط بالكرتون
        cursor.execute("""
            INSERT INTO products (name, barcode, unit, cost_price, selling_price, current_stock, parent_product_id, conversion_factor, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, ("علبة حليب", "CHILDBARCODE", "قطعة", 10.0, 12.0, 0, parent_id, 12))
        child_id = cursor.lastrowid

        # 4. إعداد الفاتورة بطلب 5 حبات
        sale_manager = SaleManager(db_manager)
        sale = Sale(
            customer_id=customer_id,
            invoice_number=f"INV-AUTO-CONV-{random.randint(1000, 9999)}",
            items=[SaleItem(product_id=child_id, quantity=5, unit_price=Decimal("12.00"))],
            status=SaleStatus.CONFIRMED,
        )

        # 5. تشغيل إنشاء المبيعات
        sale_id = sale_manager.create_sale(sale)
        assert sale_id is not None
        assert sale_id > 0

        # 6. التحقق من صحة الأرصدة بعد البيع والتحويل التلقائي
        # رصيد الكرتون (الأب) يجب أن يصبح 9 كراتين
        cursor.execute("SELECT current_stock FROM products WHERE id = ?", (parent_id,))
        assert cursor.fetchone()[0] == 9

        # دفعة الكرتون يجب أن تصبح 9
        cursor.execute("SELECT quantity FROM batches WHERE id = ?", (parent_batch_id,))
        assert cursor.fetchone()[0] == 9

        # رصيد الحبات (الابن) يجب أن يصبح 7 حبات (12 حبة الناتجة من الكرتون - 5 حبات مباعة)
        cursor.execute("SELECT current_stock FROM products WHERE id = ?", (child_id,))
        assert cursor.fetchone()[0] == 7

        # دفعة الحبات المنشأة حديثاً يجب أن يكون رصيدها 7
        cursor.execute("SELECT quantity FROM batches WHERE product_id = ? AND batch_number = 'AUTO_CONV'", (child_id,))
        assert cursor.fetchone()[0] == 7

        # التحقق من تسجيل حركات المخزون للتحويل التلقائي
        cursor.execute("SELECT COUNT(*) FROM stock_movements WHERE product_id = ? AND notes LIKE '%تلقائي%'", (parent_id,))
        assert cursor.fetchone()[0] == 1

        cursor.execute("SELECT COUNT(*) FROM stock_movements WHERE product_id = ? AND notes LIKE '%تلقائي%'", (child_id,))
        assert cursor.fetchone()[0] == 1
