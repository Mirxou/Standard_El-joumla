from decimal import Decimal
from pathlib import Path  # noqa: F811

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.sale import Sale, SaleItem, SaleStatus


class TestSaleItem:
    """اختبارات وحدة لعنصر الفاتورة"""

    def test_item_calculations(self):
        """اختبار حسابات السطر الواحد (المجموع، الخصم، الضريبة)"""
        item = SaleItem(
            product_id=1,
            quantity=2,
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10.00"),  # خصم 10%
            tax_percentage=Decimal("15.00"),  # ضريبة 15%
        )

        item.calculate_total()

        # المجموع الفرعي: 2 * 100 = 200
        assert item.subtotal == Decimal("200.00")

        # قيمة الخصم: 200 * 0.10 = 20
        assert item.discount_amount == Decimal("20.00")

        # الصافي بعد الخصم: 180
        # الضريبة: 180 * 0.15 = 27
        assert item.tax_amount == Decimal("27.00")

        # الإجمالي النهائي: 180 + 27 = 207
        assert item.total_amount == Decimal("207.00")


class TestSale:
    """اختبارات وحدة لفاتورة المبيعات"""

    def test_sale_totals_aggregation(self):
        """اختبار تجميع مبالغ الفاتورة من العناصر"""
        sale = Sale(
            invoice_number="INV-TEST-001",
            discount_percentage=Decimal("0.00"),
            tax_percentage=Decimal("0.00"),
        )

        # إضافة عنصر 1: 1 * 100 = 100
        item1 = SaleItem(product_id=1, quantity=1, unit_price=Decimal("100.00"))
        item1.calculate_total()

        # إضافة عنصر 2: 2 * 50 = 100
        item2 = SaleItem(product_id=2, quantity=2, unit_price=Decimal("50.00"))
        item2.calculate_total()

        sale.add_item(item1)
        sale.add_item(item2)

        # التحقق من المجاميع
        assert sale.subtotal == Decimal("200.00")
        assert sale.total_amount == Decimal("200.00")
        assert sale.items_count == 2
        assert sale.total_quantity == 3

    def test_payment_status_updates(self):
        """اختبار تحديث حالة الفاتورة بناءً على المدفوعات"""
        sale = Sale()
        item = SaleItem(product_id=1, quantity=1, unit_price=Decimal("100.00"))
        item.calculate_total()
        sale.add_item(item)

        # حالة 1: لم يتم الدفع
        sale.paid_amount = Decimal("0.00")
        sale.calculate_totals()  # هذا يستدعي تحديث الحالة داخلياً
        # الحالة الافتراضية هي مسودة، أو يمكن أن تكون معلقة حسب المنطق
        assert sale.remaining_amount == Decimal("100.00")

        # حالة 2: دفع جزئي
        sale.paid_amount = Decimal("50.00")
        sale.calculate_totals()
        assert sale.status == SaleStatus.PARTIALLY_PAID
        assert sale.remaining_amount == Decimal("50.00")

        # حالة 3: دفع كامل
        sale.paid_amount = Decimal("100.00")
        sale.calculate_totals()
        assert sale.status == SaleStatus.PAID
        assert sale.remaining_amount == Decimal("0.00")
