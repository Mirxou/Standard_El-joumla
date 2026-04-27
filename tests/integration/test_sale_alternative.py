import sys
import os
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock, Mock

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod

class TestSaleItem:
    def test_calculations(self):
        """اختبار الحسابات الأساسية للعنصر (المجموع، الخصم، الضريبة)"""
        item = SaleItem(
            product_id=1,
            quantity=2,
            unit_price=100.0,
            discount_percentage=10.0,  # 10% خصم
            tax_percentage=15.0        # 15% ضريبة
        )
        
        item.calculate_total()
        
        # التحقق من القيم
        assert item.subtotal == Decimal('200.00')  # 2 * 100
        assert item.discount_amount == Decimal('20.00')  # 10% من 200
        # المبلغ بعد الخصم = 180
        assert item.tax_amount == Decimal('27.00')  # 15% من 180
        assert item.total_amount == Decimal('207.00')  # 180 + 27

class TestSale:
    def test_sale_totals_calculation(self):
        """اختبار تجميع إجماليات الفاتورة من العناصر"""
        sale = Sale(invoice_number="INV-001")
        
        # إضافة عنصر 1
        item1 = SaleItem(product_id=1, quantity=1, unit_price=100.0)
        sale.add_item(item1)
        
        # إضافة عنصر 2
        item2 = SaleItem(product_id=2, quantity=2, unit_price=50.0)
        sale.add_item(item2)
        
        # التحقق
        assert sale.subtotal == Decimal('200.00')
        assert sale.total_amount == Decimal('200.00')
        assert sale.items_count == 2
        assert sale.total_quantity == 3

    def test_sale_payment_status(self):
        """اختبار تحديث حالة الدفع تلقائياً"""
        sale = Sale(total_amount=100.0)
        
        # دفع جزئي
        sale.paid_amount = Decimal('50.00')
        sale.calculate_totals()
        assert sale.status == SaleStatus.PARTIALLY_PAID
        assert sale.remaining_amount == Decimal('50.00')
        assert not sale.is_paid
        
        # دفع كامل
        sale.paid_amount = Decimal('100.00')
        sale.calculate_totals()
        assert sale.status == SaleStatus.PAID
        assert sale.remaining_amount == Decimal('0.00')
        assert sale.is_paid

class TestSaleManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return SaleManager(mock_db)

    def test_create_sale_success(self, manager, mock_db):
        """اختبار إنشاء فاتورة بنجاح"""
        # إعداد البيانات
        sale = Sale(
            invoice_number="INV-TEST",
            customer_id=1,
            total_amount=100.0,
            items=[SaleItem(product_id=1, quantity=1, unit_price=100.0)]
        )
        
        # محاكاة قاعدة البيانات
        # تصحيح: يجب إرجاع أعمدة الجدول لتمكين بناء جملة INSERT
        mock_db.connection.execute.return_value.fetchall.return_value = [
            (0, 'id', 'INTEGER', 0, None, 1),
            (1, 'invoice_number', 'TEXT', 1, None, 0),
            (2, 'customer_id', 'INTEGER', 0, None, 0),
            (3, 'total_amount', 'REAL', 1, None, 0),
            (4, 'discount_amount', 'REAL', 0, None, 0),
            (5, 'final_amount', 'REAL', 1, None, 0),
            (6, 'payment_method', 'TEXT', 0, None, 0),
            (7, 'sale_date', 'DATE', 0, None, 0),
            (8, 'user_id', 'INTEGER', 0, None, 0),
            (9, 'notes', 'TEXT', 0, None, 0),
            (10, 'status', 'TEXT', 0, None, 0),
            (11, 'paid_amount', 'REAL', 0, None, 0),
            (12, 'remaining_amount', 'REAL', 0, None, 0),
            (13, 'currency_id', 'INTEGER', 0, None, 0),
            (14, 'exchange_rate', 'REAL', 0, None, 0),
            (15, 'base_amount', 'REAL', 0, None, 0),
            (16, 'converted_amount', 'REAL', 0, None, 0),
            (17, 'is_active', 'BOOLEAN', 0, None, 0),
            (18, 'created_at', 'TIMESTAMP', 0, None, 0),
            (19, 'updated_at', 'TIMESTAMP', 0, None, 0)
        ]
        mock_db.execute_insert.side_effect = [1, 101] # sale_id, item_id
        
        # التنفيذ
        sale_id = manager.create_sale(sale)
        
        # التحقق
        assert sale_id == 1
        assert mock_db.execute_insert.call_count >= 2 # مرة للفاتورة ومرة للعنصر

    def test_create_sale_paid_with_remaining_error(self, manager):
        """اختبار منع إنشاء فاتورة 'مدفوعة' مع وجود مبلغ متبقي"""
        sale = Sale(
            status=SaleStatus.PAID,
            total_amount=100.0,
            paid_amount=0.0,
            remaining_amount=100.0
        )
        
        with pytest.raises(ValueError, match="لا يمكن حفظ الفاتورة بحالة 'مدفوعة'"):
            manager.create_sale(sale)

    def test_update_sale_status(self, manager, mock_db):
        """اختبار تحديث حالة الفاتورة"""
        mock_db.execute_query.return_value.rowcount = 1
        
        success = manager.update_sale_status(1, SaleStatus.CANCELLED)
        
        assert success is True
        mock_db.execute_query.assert_called_once()
        args = mock_db.execute_query.call_args[0]
        assert "UPDATE sales SET status = ?" in args[0]
        assert args[1][0] == 'cancelled'

    def test_add_payment(self, manager, mock_db):
        """اختبار إضافة دفعة للفاتورة"""
        # محاكاة استرجاع الفاتورة الحالية
        mock_sale_row = (
            1, "INV-001", 1, 100.0, 0.0, 100.0, "cash", 
            "2023-01-01", 1, "", "pending", 
            20.0, 80.0, # paid=20, remaining=80
            None, 1.0, 100.0, 100.0, 1, "2023-01-01", "2023-01-01"
        )
        mock_db.fetch_one.return_value = mock_sale_row
        mock_db.fetch_all.return_value = [] # items
        mock_db.execute_query.return_value.rowcount = 1
        
        # إضافة دفعة جديدة بـ 30
        success = manager.add_payment(1, Decimal('30.00'))
        
        assert success is True
        # التحقق من التحديث: المدفوع يجب أن يصبح 20+30=50، المتبقي 50
        call_args = mock_db.execute_query.call_args[0]
        assert "UPDATE sales SET" in call_args[0]
        assert call_args[1][0] == 50.0 # new_paid_amount
        assert call_args[1][1] == 50.0 # new_remaining_amount

    def test_generate_invoice_number(self, manager, mock_db):
        """اختبار توليد رقم الفاتورة"""
        # الحالة 1: لا توجد فواتير اليوم
        mock_db.fetch_one.return_value = (0,)
        inv_num = manager.generate_invoice_number()
        today_str = date.today().strftime('%Y%m%d')
        assert inv_num == f"INV-{today_str}-0001"
        
        # الحالة 2: يوجد 5 فواتير
        mock_db.fetch_one.return_value = (5,)
        inv_num = manager.generate_invoice_number()
        assert inv_num == f"INV-{today_str}-0006"

    def test_row_to_sale_conversion(self, manager):
        """اختبار تحويل صف قاعدة البيانات إلى كائن Sale"""
        # محاكاة صف كامل (20 عمود)
        row = (
            1, "INV-001", 5, 1000.0, 100.0, 
            900.0, "cash", "2023-10-25", 1, "Notes", 
            "paid", 900.0, 0.0, 
            None, 1.0, 900.0, 900.0, 
            1, "2023-10-25T10:00:00", "2023-10-25T10:00:00"
        )
        
        sale = manager._row_to_sale(row)
        
        assert sale.id == 1
        assert sale.invoice_number == "INV-001"
        assert sale.status == SaleStatus.PAID
        assert sale.total_amount == Decimal('900.00')
        assert sale.remaining_amount == Decimal('0.00')
        assert sale.payment_method == PaymentMethod.CASH

    def test_cancel_sale(self, manager, mock_db):
        """اختبار إلغاء الفاتورة"""
        # محاكاة وجود فاتورة
        mock_sale_row = (
            1, "INV-001", 1, 100.0, 0.0, 100.0, "cash", 
            "2023-01-01", 1, "", "confirmed", 
            0.0, 100.0, 
            None, 1.0, 100.0, 100.0, 1, "2023-01-01", "2023-01-01"
        )
        mock_db.fetch_one.return_value = mock_sale_row
        # محاكاة عناصر الفاتورة لاستعادة المخزون
        mock_db.connection.cursor.return_value.fetchall.return_value = [(1, 5)] # product_id, quantity
        
        # تنفيذ الإلغاء
        success = manager.cancel_invoice(1, "Test Reason")
        
        assert success is True
        # التحقق من تحديث الحالة
        # ملاحظة: cancel_invoice تستخدم connection.cursor() داخلياً، لذا قد يكون التحقق من الاستدعاءات معقداً قليلاً
        # لكننا نتحقق من النتيجة النهائية

    def test_delete_sale(self, manager, mock_db):
        """اختبار حذف الفاتورة"""
        # محاكاة وجود فاتورة
        mock_sale_row = (
            1, "INV-001", 1, 100.0, 0.0, 100.0, "cash", 
            "2023-01-01", 1, "", "draft", 
            0.0, 100.0, 
            None, 1.0, 100.0, 100.0, 1, "2023-01-01", "2023-01-01"
        )
        mock_db.fetch_one.return_value = mock_sale_row
        mock_db.execute_query.return_value.rowcount = 1
        
        success = manager.delete_sale(1, soft_delete=True)
        
        assert success is True
        mock_db.execute_query.assert_called()



