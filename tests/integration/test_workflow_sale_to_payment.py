import pytest
from decimal import Decimal
from datetime import datetime
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.models.product import Product, ProductManager
from src.models.customer import Customer, CustomerManager
from src.models.sale import Sale, SaleItem
from src.services.sales_service import SalesService
from src.services.inventory_service import InventoryService
from src.services.accounting_service import AccountingService

@pytest.mark.integration
@pytest.mark.requires_db
class TestSaleToPaymentWorkflow:
    """
    اختبار تكامل لسير عمل كامل: من إنشاء المنتج إلى إتمام عملية البيع.
    يستخدم قاعدة بيانات حقيقية (مؤقتة) وخدمات حقيقية.
    """

    @pytest.fixture(scope="class")
    def db_manager(self):
        """إنشاء مدير قاعدة بيانات مؤقتة للاختبار"""
        db_path = ":memory:"
        db = DatabaseManager(db_path)
        db.initialize()
        return db

    @pytest.fixture(scope="class")
    def setup_data(self, db_manager):
        """إعداد البيانات الأساسية للاختبار (منتج، عميل)"""
        # إنشاء الخدمات
        product_manager = ProductManager(db_manager)
        customer_manager = CustomerManager(db_manager)
        inventory_service = InventoryService(db_manager)

        # 1. إنشاء منتج
        product = Product(
            name="لابتوب اختبار التكامل",
            barcode="INT-TEST-LP-01",
            cost_price=Decimal("1000.00"),
            selling_price=Decimal("1500.00"),
            category_id=1
        )
        product_id = product_manager.create_product(product)
        assert product_id is not None

        # 2. إضافة مخزون للمنتج
        inventory_service.adjust_stock(product_id, 10, "initial_stock")

        # 3. إنشاء عميل
        customer = Customer(
            name="عميل اختبار التكامل",
            phone="123456789"
        )
        customer_id = customer_manager.create_customer(customer)
        assert customer_id is not None

        return {
            "product_id": product_id,
            "customer_id": customer_id,
            "initial_stock": 10
        }

    def test_full_sale_workflow(self, db_manager, setup_data):
        """
        اختبار عملية بيع كاملة والتحقق من تأثيرها على المخزون والمحاسبة.
        """
        # 1. إعداد
        sales_service = SalesService(db_manager)
        inventory_service = InventoryService(db_manager)
        accounting_service = AccountingService(db_manager)

        product_id = setup_data["product_id"]
        customer_id = setup_data["customer_id"]
        initial_stock = setup_data["initial_stock"]
        sale_quantity = 2

        # 2. إنشاء فاتورة بيع
        sale = Sale(
            customer_id=customer_id,
            sale_date=datetime.now(),
            status="confirmed"
        )
        sale.items.append(SaleItem(
            product_id=product_id,
            quantity=sale_quantity,
            unit_price=Decimal("1500.00")
        ))

        sale_id = sales_service.create_sale(sale)
        assert sale_id is not None

        # 3. التحقق من النتائج

        # 3.1. التحقق من تحديث المخزون
        final_stock = inventory_service.get_product_stock(product_id)
        expected_stock = initial_stock - sale_quantity
        assert final_stock == expected_stock, f"المخزون المتوقع {expected_stock} لكن الفعلي {final_stock}"

        # 3.2. التحقق من إنشاء قيد محاسبي
        # (نفترض أن create_sale تنشئ قيداً)
        query = "SELECT COUNT(*) as count FROM general_journal WHERE reference_type = 'sale' AND reference_id = ?"
        result = db_manager.fetch_one(query, (sale_id,))
        assert result is not None
        assert result['count'] > 0, "لم يتم إنشاء قيد محاسبي للمبيعات"

        # 3.3. التحقق من رصيد العميل (اختياري، يعتمد على منطق العمل)
        customer_manager = CustomerManager(db_manager)
        customer = customer_manager.get_customer_by_id(customer_id)
        assert customer.balance == sale.grand_total, "رصيد العميل لم يتم تحديثه بشكل صحيح"