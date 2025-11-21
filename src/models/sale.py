#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المبيعات - Sale Model
يحتوي على جميع العمليات المتعلقة بالمبيعات والفواتير
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

class SaleStatus(Enum):
    """حالات الفاتورة"""
    DRAFT = "مسودة"
    CONFIRMED = "مؤكدة"
    PAID = "مدفوعة"
    PARTIALLY_PAID = "مدفوعة جزئياً"
    CANCELLED = "ملغية"
    RETURNED = "مرتجعة"

class PaymentMethod(Enum):
    """طرق الدفع"""
    CASH = "نقدي"
    CARD = "بطاقة"
    BANK_TRANSFER = "تحويل بنكي"
    CREDIT = "آجل"
    MIXED = "مختلط"

@dataclass
class SaleItem:
    """عنصر في فاتورة المبيعات"""
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    product_barcode: Optional[str] = None
    quantity: int = 1
    unit_price: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    tax_percentage: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        for field in ['unit_price', 'discount_amount', 'discount_percentage', 
                     'tax_amount', 'tax_percentage', 'total_amount']:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))
    
    def calculate_total(self):
        """حساب المجموع"""
        subtotal = self.unit_price * self.quantity
        
        # خصم
        if self.discount_percentage > 0:
            self.discount_amount = subtotal * (self.discount_percentage / 100)
        
        after_discount = subtotal - self.discount_amount
        
        # ضريبة
        if self.tax_percentage > 0:
            self.tax_amount = after_discount * (self.tax_percentage / 100)
        
        self.total_amount = after_discount + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_barcode': self.product_barcode,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_amount': float(self.discount_amount),
            'discount_percentage': float(self.discount_percentage),
            'tax_amount': float(self.tax_amount),
            'tax_percentage': float(self.tax_percentage),
            'total_amount': float(self.total_amount)
        }

@dataclass
class Sale:
    """نموذج بيانات المبيعات"""
    id: Optional[int] = None
    invoice_number: str = ""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    sale_date: Optional[date] = None
    due_date: Optional[date] = None
    status: SaleStatus = SaleStatus.DRAFT
    payment_method: PaymentMethod = PaymentMethod.CASH
    subtotal: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    discount_percentage: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    tax_percentage: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    paid_amount: Decimal = Decimal('0.00')
    remaining_amount: Decimal = Decimal('0.00')
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[SaleItem] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        if self.items is None:
            self.items = []
        
        for field in ['subtotal', 'discount_amount', 'discount_percentage', 
                     'tax_amount', 'tax_percentage', 'total_amount', 
                     'paid_amount', 'remaining_amount']:
            value = getattr(self, field)
            if isinstance(value, (int, float, str)):
                setattr(self, field, Decimal(str(value)))
        
        if isinstance(self.status, str):
            self.status = SaleStatus(self.status)
        if isinstance(self.payment_method, str):
            self.payment_method = PaymentMethod(self.payment_method)
    
    def add_item(self, item: SaleItem):
        """إضافة عنصر للفاتورة"""
        item.calculate_total()
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: int):
        """حذف عنصر من الفاتورة"""
        self.items = [item for item in self.items if item.id != item_id]
        self.calculate_totals()
    
    def calculate_totals(self):
        """حساب المجاميع"""
        self.subtotal = sum(item.unit_price * item.quantity for item in self.items)
        
        # خصم إجمالي
        if self.discount_percentage > 0:
            self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        
        after_discount = self.subtotal - self.discount_amount
        
        # ضريبة إجمالية
        if self.tax_percentage > 0:
            self.tax_amount = after_discount * (self.tax_percentage / 100)
        
        self.total_amount = after_discount + self.tax_amount
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # تحديث حالة الدفع
        if self.paid_amount >= self.total_amount:
            self.status = SaleStatus.PAID
        elif self.paid_amount > 0:
            self.status = SaleStatus.PARTIALLY_PAID
    
    @property
    def is_paid(self) -> bool:
        """هل الفاتورة مدفوعة بالكامل؟"""
        return self.paid_amount >= self.total_amount
    
    @property
    def items_count(self) -> int:
        """عدد الأصناف"""
        return len(self.items)
    
    @property
    def total_quantity(self) -> int:
        """إجمالي الكمية"""
        return sum(item.quantity for item in self.items)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status.value if isinstance(self.status, SaleStatus) else self.status,
            'payment_method': self.payment_method.value if isinstance(self.payment_method, PaymentMethod) else self.payment_method,
            'subtotal': float(self.subtotal),
            'discount_amount': float(self.discount_amount),
            'discount_percentage': float(self.discount_percentage),
            'tax_amount': float(self.tax_amount),
            'tax_percentage': float(self.tax_percentage),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount),
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
            'is_paid': self.is_paid,
            'items_count': self.items_count,
            'total_quantity': self.total_quantity
        }

class SaleManager:
    """مدير المبيعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
    
    def create_sale(self, sale: Sale) -> Optional[int]:
        """إنشاء فاتورة مبيعات جديدة"""
        try:
            # إنشاء الفاتورة الرئيسية
            query = """
            INSERT INTO sales (
                invoice_number, customer_id, customer_name, customer_phone,
                sale_date, due_date, status, payment_method,
                subtotal, discount_amount, discount_percentage,
                tax_amount, tax_percentage, total_amount,
                paid_amount, remaining_amount, notes, created_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            params = (
                sale.invoice_number,
                sale.customer_id,
                sale.customer_name,
                sale.customer_phone,
                sale.sale_date or date.today(),
                sale.due_date,
                sale.status.value,
                sale.payment_method.value,
                float(sale.subtotal),
                float(sale.discount_amount),
                float(sale.discount_percentage),
                float(sale.tax_amount),
                float(sale.tax_percentage),
                float(sale.total_amount),
                float(sale.paid_amount),
                float(sale.remaining_amount),
                sale.notes,
                sale.created_by,
                now,
                now
            )
            
            result = self.db_manager.execute_query(query, params)
            if result:
                try:
                    sale_id = self.db_manager.get_last_insert_id()
                except Exception:
                    # fallback to cursor.lastrowid if available
                    sale_id = getattr(result, 'lastrowid', None)
                
                # إضافة عناصر الفاتورة
                for item in sale.items:
                    item.sale_id = sale_id
                    self._create_sale_item(item)
                
                # تحديث المخزون
                self._update_stock_for_sale(sale.items, operation="sale")
                
                if self.logger:
                    self.logger.info(f"تم إنشاء فاتورة مبيعات جديدة: {sale.invoice_number} (ID: {sale_id})")
                return sale_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فاتورة المبيعات: {str(e)}")
            return None
    
    def _create_sale_item(self, item: SaleItem) -> Optional[int]:
        """إنشاء عنصر فاتورة"""
        try:
            # Try to adapt to current sale_items schema (may include batch_id, total_price, cost_price, profit)
            # Fetch product cost_price
            prod = self.db_manager.fetch_one('SELECT cost_price FROM products WHERE id = ?', (item.product_id,))
            cost_price = float(prod[0]) if prod and prod[0] is not None else 0.0

            # Find or create a batch for this product
            batch = self.db_manager.fetch_one('SELECT id FROM batches WHERE product_id = ? LIMIT 1', (item.product_id,))
            if batch and batch[0]:
                batch_id = batch[0]
            else:
                # create placeholder batch
                batch_number = f'auto-{item.product_id}-{int(datetime.now().timestamp())}'
                bq = """
                INSERT INTO batches (product_id, batch_number, quantity, cost_price, selling_price, purchase_date)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
                """
                bparams = (item.product_id, batch_number, 0, cost_price, float(item.unit_price))
                self.db_manager.execute_query(bq, bparams)
                try:
                    batch_id = self.db_manager.get_last_insert_id()
                except Exception:
                    batch_id = None

            total_price = float(item.unit_price) * int(item.quantity)
            profit = total_price - (cost_price * int(item.quantity))

            query = """
            INSERT INTO sale_items (
                sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                item.sale_id,
                item.product_id,
                batch_id,
                item.quantity,
                float(item.unit_price),
                total_price,
                cost_price,
                profit
            )

            result = self.db_manager.execute_query(query, params)
            if result:
                try:
                    return self.db_manager.get_last_insert_id()
                except Exception:
                    return getattr(result, 'lastrowid', None)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء عنصر الفاتورة: {str(e)}")
            return None
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """الحصول على فاتورة بالمعرف"""
        try:
            # الحصول على بيانات الفاتورة الرئيسية
            query = """
            SELECT * FROM sales WHERE id = ?
            """
            
            result = self.db_manager.fetch_one(query, (sale_id,))
            if not result:
                return None
            
            sale = self._row_to_sale(result)
            
            # الحصول على عناصر الفاتورة
            items_query = """
            SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id
            """
            
            items_results = self.db_manager.fetch_all(items_query, (sale_id,))
            sale.items = [self._row_to_sale_item(row) for row in items_results]
            
            return sale
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على فاتورة المبيعات {sale_id}: {str(e)}")
        
        return None
    
    def get_sale_by_invoice_number(self, invoice_number: str) -> Optional[Sale]:
        """الحصول على فاتورة برقم الفاتورة"""
        try:
            query = "SELECT * FROM sales WHERE invoice_number = ?"
            result = self.db_manager.fetch_one(query, (invoice_number,))
            
            if result:
                sale = self._row_to_sale(result)
                # الحصول على العناصر
                items_query = "SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id"
                items_results = self.db_manager.fetch_all(items_query, (sale.id,))
                sale.items = [self._row_to_sale_item(row) for row in items_results]
                return sale
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالفاتورة {invoice_number}: {str(e)}")
        
        return None
    
    def search_sales(self, search_term: str = "", start_date: Optional[date] = None,
                    end_date: Optional[date] = None, status: Optional[SaleStatus] = None,
                    customer_id: Optional[int] = None) -> List[Sale]:
        """البحث في المبيعات"""
        try:
            query = "SELECT * FROM sales WHERE 1=1"
            params = []
            
            if search_term:
                query += " AND (invoice_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if start_date:
                query += " AND sale_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND sale_date <= ?"
                params.append(end_date)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            
            query += " ORDER BY sale_date DESC, id DESC"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_sale(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في المبيعات: {str(e)}")
            return []
    
    def get_daily_sales(self, target_date: Optional[date] = None) -> List[Sale]:
        """الحصول على مبيعات يوم معين"""
        if not target_date:
            target_date = date.today()
        
        return self.search_sales(start_date=target_date, end_date=target_date)
    
    def update_sale_status(self, sale_id: int, new_status: SaleStatus) -> bool:
        """تحديث حالة الفاتورة"""
        try:
            query = "UPDATE sales SET status = ?, updated_at = ? WHERE id = ?"
            params = (new_status.value, datetime.now(), sale_id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث حالة الفاتورة {sale_id} إلى {new_status.value}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث حالة الفاتورة {sale_id}: {str(e)}")
        
        return False
    
    def add_payment(self, sale_id: int, payment_amount: Decimal) -> bool:
        """إضافة دفعة للفاتورة"""
        try:
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False
            
            new_paid_amount = sale.paid_amount + payment_amount
            new_remaining_amount = sale.total_amount - new_paid_amount
            
            # تحديد الحالة الجديدة
            if new_remaining_amount <= 0:
                new_status = SaleStatus.PAID
                new_remaining_amount = Decimal('0.00')
            elif new_paid_amount > 0:
                new_status = SaleStatus.PARTIALLY_PAID
            else:
                new_status = sale.status
            
            query = """
            UPDATE sales SET 
                paid_amount = ?, remaining_amount = ?, status = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (
                float(new_paid_amount),
                float(new_remaining_amount),
                new_status.value,
                datetime.now(),
                sale_id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم إضافة دفعة {payment_amount} للفاتورة {sale_id}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة دفعة للفاتورة {sale_id}: {str(e)}")
        
        return False
    
    def cancel_sale(self, sale_id: int) -> bool:
        """إلغاء فاتورة"""
        try:
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False
            
            # إرجاع المخزون
            self._update_stock_for_sale(sale.items, operation="return")
            
            # تحديث حالة الفاتورة
            return self.update_sale_status(sale_id, SaleStatus.CANCELLED)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء الفاتورة {sale_id}: {str(e)}")
            return False
    
    def _update_stock_for_sale(self, items: List[SaleItem], operation: str):
        """تحديث المخزون للمبيعات"""
        try:
            for item in items:
                if operation == "sale":
                    # خصم من المخزون
                    quantity_change = -item.quantity
                elif operation == "return":
                    # إضافة للمخزون
                    quantity_change = item.quantity
                else:
                    continue
                
                query = """
                UPDATE products SET 
                    current_stock = current_stock + ?, 
                    updated_at = ?
                WHERE id = ?
                """
                
                params = (quantity_change, datetime.now(), item.product_id)
                self.db_manager.execute_query(query, params)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث المخزون للمبيعات: {str(e)}")
    
    def generate_invoice_number(self) -> str:
        """إنشاء رقم فاتورة جديد"""
        try:
            today = date.today()
            prefix = f"INV-{today.strftime('%Y%m%d')}"
            
            query = """
            SELECT COUNT(*) FROM sales 
            WHERE invoice_number LIKE ? AND DATE(sale_date) = ?
            """
            
            result = self.db_manager.fetch_one(query, (f"{prefix}%", today))
            count = (result[0] if result else 0) + 1
            
            return f"{prefix}-{count:04d}"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء رقم الفاتورة: {str(e)}")
            return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_sales_report(self, start_date: Optional[date] = None, 
                        end_date: Optional[date] = None) -> Dict[str, Any]:
        """تقرير المبيعات"""
        try:
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date
            
            query = """
            SELECT 
                COUNT(*) as total_invoices,
                COUNT(CASE WHEN status = 'مدفوعة' THEN 1 END) as paid_invoices,
                COUNT(CASE WHEN status = 'مدفوعة جزئياً' THEN 1 END) as partially_paid_invoices,
                COUNT(CASE WHEN status = 'آجل' THEN 1 END) as credit_invoices,
                SUM(total_amount) as total_sales,
                SUM(paid_amount) as total_paid,
                SUM(remaining_amount) as total_remaining,
                AVG(total_amount) as avg_invoice_value
            FROM sales
            WHERE sale_date BETWEEN ? AND ? AND status != 'ملغية'
            """
            
            result = self.db_manager.fetch_one(query, (start_date, end_date))
            if result:
                return {
                    'period': f"{start_date} إلى {end_date}",
                    'total_invoices': result[0] or 0,
                    'paid_invoices': result[1] or 0,
                    'partially_paid_invoices': result[2] or 0,
                    'credit_invoices': result[3] or 0,
                    'total_sales': float(result[4] or 0),
                    'total_paid': float(result[5] or 0),
                    'total_remaining': float(result[6] or 0),
                    'avg_invoice_value': float(result[7] or 0)
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المبيعات: {str(e)}")
        
        return {}
    
    def _row_to_sale(self, row) -> Sale:
        """تحويل صف قاعدة البيانات إلى كائن مبيعات"""
        return Sale(
            id=row[0],
            invoice_number=row[1],
            customer_id=row[2],
            customer_name=row[3],
            customer_phone=row[4],
            sale_date=date.fromisoformat(row[5]) if row[5] else None,
            due_date=date.fromisoformat(row[6]) if row[6] else None,
            status=SaleStatus(row[7]),
            payment_method=PaymentMethod(row[8]),
            subtotal=Decimal(str(row[9])),
            discount_amount=Decimal(str(row[10])),
            discount_percentage=Decimal(str(row[11])),
            tax_amount=Decimal(str(row[12])),
            tax_percentage=Decimal(str(row[13])),
            total_amount=Decimal(str(row[14])),
            paid_amount=Decimal(str(row[15])),
            remaining_amount=Decimal(str(row[16])),
            notes=row[17],
            created_by=row[18],
            created_at=datetime.fromisoformat(row[19]) if row[19] else None,
            updated_at=datetime.fromisoformat(row[20]) if row[20] else None
        )
    
    def _row_to_sale_item(self, row) -> SaleItem:
        """تحويل صف قاعدة البيانات إلى عنصر فاتورة"""
        return SaleItem(
            id=row[0],
            sale_id=row[1],
            product_id=row[2],
            product_name=row[3],
            product_barcode=row[4],
            quantity=row[5],
            unit_price=Decimal(str(row[6])),
            discount_amount=Decimal(str(row[7])),
            discount_percentage=Decimal(str(row[8])),
            tax_amount=Decimal(str(row[9])),
            tax_percentage=Decimal(str(row[10])),
            total_amount=Decimal(str(row[11]))
        )