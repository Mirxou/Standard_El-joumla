#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج المشتريات - Purchase Model
يحتوي على جميع العمليات المتعلقة بالمشتريات وعناصر المشتريات
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

class PurchaseStatus(Enum):
    """حالات المشتريات"""
    PENDING = "معلقة"
    RECEIVED = "مستلمة"
    PARTIAL = "جزئية"
    CANCELLED = "ملغية"
    RETURNED = "مرتجعة"

class PaymentStatus(Enum):
    """حالات الدفع"""
    UNPAID = "غير مدفوعة"
    PARTIAL = "مدفوعة جزئياً"
    PAID = "مدفوعة"
    OVERDUE = "متأخرة"

@dataclass
class PurchaseItem:
    """عنصر المشتريات"""
    id: Optional[int] = None
    purchase_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""
    product_barcode: Optional[str] = None
    quantity_ordered: Decimal = Decimal('0')
    quantity_received: Decimal = Decimal('0')
    unit_cost: Decimal = Decimal('0.00')
    discount_percent: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_percent: Decimal = Decimal('15.00')  # ضريبة القيمة المضافة
    tax_amount: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    expiry_date: Optional[date] = None
    batch_number: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        decimal_fields = ['quantity_ordered', 'quantity_received', 'unit_cost', 
                         'discount_percent', 'discount_amount', 'tax_percent', 
                         'tax_amount', 'total_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
    
    @property
    def subtotal(self) -> Decimal:
        """المجموع الفرعي قبل الخصم والضريبة"""
        return self.quantity_ordered * self.unit_cost
    
    @property
    def net_amount(self) -> Decimal:
        """المبلغ الصافي بعد الخصم وقبل الضريبة"""
        return self.subtotal - self.discount_amount
    
    @property
    def pending_quantity(self) -> Decimal:
        """الكمية المعلقة (غير المستلمة)"""
        return self.quantity_ordered - self.quantity_received
    
    @property
    def is_fully_received(self) -> bool:
        """هل تم استلام الكمية كاملة؟"""
        return self.quantity_received >= self.quantity_ordered
    
    def calculate_totals(self):
        """حساب المجاميع"""
        # حساب الخصم إذا كان بالنسبة المئوية
        if self.discount_percent > 0 and self.discount_amount == 0:
            self.discount_amount = (self.subtotal * self.discount_percent) / 100
        
        # حساب المبلغ الصافي
        net_amount = self.subtotal - self.discount_amount
        
        # حساب الضريبة
        if self.tax_percent > 0:
            self.tax_amount = (net_amount * self.tax_percent) / 100
        
        # حساب المجموع النهائي
        self.total_amount = net_amount + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_barcode': self.product_barcode,
            'quantity_ordered': float(self.quantity_ordered),
            'quantity_received': float(self.quantity_received),
            'unit_cost': float(self.unit_cost),
            'discount_percent': float(self.discount_percent),
            'discount_amount': float(self.discount_amount),
            'tax_percent': float(self.tax_percent),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'batch_number': self.batch_number,
            'notes': self.notes,
            'subtotal': float(self.subtotal),
            'net_amount': float(self.net_amount),
            'pending_quantity': float(self.pending_quantity),
            'is_fully_received': self.is_fully_received
        }

@dataclass
class Purchase:
    """فاتورة المشتريات"""
    id: Optional[int] = None
    invoice_number: str = ""
    supplier_invoice_number: Optional[str] = None
    supplier_id: int = 0
    supplier_name: str = ""
    purchase_date: date = field(default_factory=date.today)
    expected_delivery_date: Optional[date] = None
    received_date: Optional[date] = None
    status: str = PurchaseStatus.PENDING.value
    payment_status: str = PaymentStatus.UNPAID.value
    payment_terms: str = "نقدي"
    subtotal_amount: Decimal = Decimal('0.00')
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    shipping_cost: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    paid_amount: Decimal = Decimal('0.00')
    remaining_amount: Decimal = Decimal('0.00')
    # Multi-Currency Support
    currency_id: Optional[int] = None  # معرف العملة المستخدمة
    exchange_rate: Decimal = Decimal('1.0')  # سعر الصرف المستخدم
    base_amount: Optional[Decimal] = None  # المبلغ بالعملة الأساسية
    converted_amount: Optional[Decimal] = None  # المبلغ بالعملة المحددة
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[PurchaseItem] = field(default_factory=list)
    
    def __post_init__(self):
        """تحويل القيم بعد الإنشاء"""
        decimal_fields = ['subtotal_amount', 'discount_amount', 'tax_amount', 
                         'shipping_cost', 'total_amount', 'paid_amount', 'remaining_amount',
                         'exchange_rate', 'base_amount', 'converted_amount']
        for field_name in decimal_fields:
            value = getattr(self, field_name)
            if value is not None and isinstance(value, (int, float, str)):
                setattr(self, field_name, Decimal(str(value)))
    
    @property
    def items_count(self) -> int:
        """عدد الأصناف"""
        return len(self.items)
    
    @property
    def total_quantity_ordered(self) -> Decimal:
        """إجمالي الكمية المطلوبة"""
        return sum(item.quantity_ordered for item in self.items)
    
    @property
    def total_quantity_received(self) -> Decimal:
        """إجمالي الكمية المستلمة"""
        return sum(item.quantity_received for item in self.items)
    
    @property
    def is_fully_received(self) -> bool:
        """هل تم استلام الفاتورة كاملة؟"""
        return all(item.is_fully_received for item in self.items) if self.items else False
    
    @property
    def is_partially_received(self) -> bool:
        """هل تم استلام جزء من الفاتورة؟"""
        return any(item.quantity_received > 0 for item in self.items) and not self.is_fully_received
    
    @property
    def is_overdue(self) -> bool:
        """هل الفاتورة متأخرة؟"""
        if self.payment_status == PaymentStatus.PAID.value:
            return False
        
        if self.expected_delivery_date and self.expected_delivery_date < date.today():
            return True
        
        return False
    
    def add_item(self, item: PurchaseItem):
        """إضافة عنصر للفاتورة"""
        item.purchase_id = self.id
        self.items.append(item)
        self.calculate_totals()
    
    def remove_item(self, item_id: int) -> bool:
        """حذف عنصر من الفاتورة"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self.calculate_totals()
                return True
        return False
    
    def calculate_totals(self):
        """حساب مجاميع الفاتورة"""
        # حساب مجاميع العناصر
        for item in self.items:
            item.calculate_totals()
        
        # حساب المجموع الفرعي
        self.subtotal_amount = sum(item.total_amount for item in self.items)
        
        # حساب المجموع النهائي
        self.total_amount = self.subtotal_amount - self.discount_amount + self.shipping_cost
        
        # حساب المبلغ المتبقي
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # Multi-Currency: حساب المبالغ بالعملة المحددة والأساسية
        if self.currency_id:
            # المبلغ بالعملة المحددة
            self.converted_amount = self.total_amount
            # المبلغ بالعملة الأساسية (سيتم حسابه من ExchangeRateService)
            # سيتم تعيينه من Service Layer
        else:
            # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
            self.base_amount = self.total_amount
            self.converted_amount = self.total_amount
        
        # تحديث حالة الدفع
        self._update_payment_status()
    
    def _update_payment_status(self):
        """تحديث حالة الدفع"""
        if self.paid_amount <= 0:
            self.payment_status = PaymentStatus.UNPAID.value
        elif self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID.value
        else:
            self.payment_status = PaymentStatus.PARTIAL.value
        
        # التحقق من التأخير
        if self.is_overdue and self.payment_status != PaymentStatus.PAID.value:
            self.payment_status = PaymentStatus.OVERDUE.value
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'supplier_invoice_number': self.supplier_invoice_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'purchase_date': self.purchase_date.isoformat(),
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'payment_terms': self.payment_terms,
            'subtotal_amount': float(self.subtotal_amount),
            'discount_amount': float(self.discount_amount),
            'tax_amount': float(self.tax_amount),
            'shipping_cost': float(self.shipping_cost),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount),
            # Multi-Currency Support
            'currency_id': self.currency_id,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else 1.0,
            'base_amount': float(self.base_amount) if self.base_amount else None,
            'converted_amount': float(self.converted_amount) if self.converted_amount else None,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
            'items_count': self.items_count,
            'total_quantity_ordered': float(self.total_quantity_ordered),
            'total_quantity_received': float(self.total_quantity_received),
            'is_fully_received': self.is_fully_received,
            'is_partially_received': self.is_partially_received,
            'is_overdue': self.is_overdue
        }

class PurchaseManager:
    """مدير المشتريات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        # Multi-Company Support
        self._tenant_manager = None
    
    @property
    def tenant_manager(self):
        """Lazy loading لـ TenantIsolationManager"""
        if self._tenant_manager is None:
            try:
                from src.core.tenant_isolation import TenantIsolationManager
                self._tenant_manager = TenantIsolationManager(self.db_manager)
            except ImportError:
                if self.logger:
                    self.logger.warning("TenantIsolationManager غير متاح - Multi-Company غير مفعل")
        return self._tenant_manager
    
    def _get_company_id(self) -> Optional[int]:
        """الحصول على معرف الشركة الحالية"""
        if self.tenant_manager:
            return self.tenant_manager.get_current_company_id()
        return None
    
    def _add_company_filter(self, query: str, params: list, company_id: Optional[int] = None) -> tuple:
        """إضافة فلتر الشركة إلى الاستعلام"""
        if company_id is None:
            company_id = self._get_company_id()
        
        if company_id is not None:
            if "WHERE" in query.upper():
                query += " AND company_id = ?"
            else:
                query += " WHERE company_id = ?"
            params.append(company_id)
        
        return query, params
    
    def create_purchase(self, purchase: Purchase) -> Optional[int]:
        """إنشاء فاتورة شراء جديدة"""
        try:
            # إنشاء رقم فاتورة إذا لم يكن موجوداً
            if not purchase.invoice_number:
                purchase.invoice_number = self.generate_invoice_number()
            
            # حساب المجاميع
            purchase.calculate_totals()
            
            # إدراج الفاتورة
            query = """
            INSERT INTO purchases (
                invoice_number, supplier_invoice_number, supplier_id, purchase_date,
                expected_delivery_date, status, payment_status, payment_terms,
                subtotal_amount, discount_amount, tax_amount, shipping_cost,
                total_amount, paid_amount, remaining_amount, currency_id, exchange_rate,
                base_amount, converted_amount, notes, created_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now()
            # Multi-Currency: حساب المبالغ
            base_amount = purchase.base_amount if purchase.base_amount is not None else purchase.total_amount
            converted_amount = purchase.converted_amount if purchase.converted_amount is not None else purchase.total_amount
            exchange_rate = float(purchase.exchange_rate) if purchase.exchange_rate else 1.0
            
            params = (
                purchase.invoice_number,
                purchase.supplier_invoice_number,
                purchase.supplier_id,
                purchase.purchase_date,
                purchase.expected_delivery_date,
                purchase.status,
                purchase.payment_status,
                purchase.payment_terms,
                float(purchase.subtotal_amount),
                float(purchase.discount_amount),
                float(purchase.tax_amount),
                float(purchase.shipping_cost),
                float(purchase.total_amount),
                float(purchase.paid_amount),
                float(purchase.remaining_amount),
                # Multi-Currency Support
                purchase.currency_id,
                exchange_rate,
                float(base_amount) if base_amount else None,
                float(converted_amount) if converted_amount else None,
                purchase.notes,
                purchase.created_by,
                now.isoformat(),
                now.isoformat()
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                purchase_id = result.lastrowid
                purchase.id = purchase_id
                
                # إدراج عناصر الفاتورة
                for item in purchase.items:
                    item.purchase_id = purchase_id
                    self._create_purchase_item(item)
                
                # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                try:
                    from ...core.signals import signals
                    signals.purchases_updated.emit()
                    signals.purchase_created.emit(purchase_id)
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات: purchases_updated, purchase_created")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
                
                # 🔔 إطلاق Webhook: إرسال Webhook عند إنشاء فاتورة شراء
                try:
                    from ...services.webhook_service import WebhookService
                    webhook_service = WebhookService(self.db_manager, self.logger)
                    
                    # بناء Payload للـ Webhook
                    webhook_payload = {
                        "event": "purchase_created",
                        "purchase_id": purchase_id,
                        "invoice_number": purchase.invoice_number,
                        "supplier_id": purchase.supplier_id,
                        "total_amount": float(purchase.total_amount) if purchase.total_amount else 0.0,
                        "created_at": datetime.now().isoformat(),
                        "purchase": purchase.to_dict() if hasattr(purchase, 'to_dict') else {}
                    }
                    
                    webhook_service.trigger_webhook(
                        event_type="purchase_created",
                        payload=webhook_payload,
                        entity_id=purchase_id,
                        company_id=purchase.company_id if hasattr(purchase, 'company_id') else None
                    )
                    
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق Webhook: purchase_created (Purchase ID: {purchase_id})")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق Webhook: {e}")
                
                if self.logger:
                    self.logger.info(f"تم إنشاء فاتورة شراء جديدة: {purchase.invoice_number} (ID: {purchase_id})")
                
                return purchase_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فاتورة الشراء: {str(e)}")
            return None
    
    def _create_purchase_item(self, item: PurchaseItem) -> Optional[int]:
        """إنشاء عنصر فاتورة شراء"""
        try:
            item.calculate_totals()
            
            query = """
            INSERT INTO purchase_items (
                purchase_id, product_id, quantity_ordered, quantity_received,
                unit_cost, discount_percent, discount_amount, tax_percent,
                tax_amount, total_amount, expiry_date, batch_number, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                item.purchase_id,
                item.product_id,
                float(item.quantity_ordered),
                float(item.quantity_received),
                float(item.unit_cost),
                float(item.discount_percent),
                float(item.discount_amount),
                float(item.tax_percent),
                float(item.tax_amount),
                float(item.total_amount),
                item.expiry_date,
                item.batch_number,
                item.notes
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                return result.lastrowid
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء عنصر فاتورة الشراء: {str(e)}")
            return None
    
    def get_purchase_by_id(self, purchase_id: int) -> Optional[Purchase]:
        """الحصول على فاتورة شراء بالمعرف"""
        try:
            # الحصول على بيانات الفاتورة
            query = """
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
            """
            
            result = self.db_manager.fetch_one(query, (purchase_id,))
            if not result:
                return None
            
            purchase = self._row_to_purchase(result)
            
            # الحصول على عناصر الفاتورة
            items_query = """
            SELECT pi.*, pr.name as product_name, pr.barcode as product_barcode
            FROM purchase_items pi
            LEFT JOIN products pr ON pi.product_id = pr.id
            WHERE pi.purchase_id = ?
            ORDER BY pi.id
            """
            
            items_results = self.db_manager.fetch_all(items_query, (purchase_id,))
            purchase.items = [self._row_to_purchase_item(row) for row in items_results]
            
            return purchase
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على فاتورة الشراء {purchase_id}: {str(e)}")
            return None
    
    def get_purchase_by_invoice_number(self, invoice_number: str) -> Optional[Purchase]:
        """الحصول على فاتورة شراء برقم الفاتورة"""
        try:
            query = """
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.invoice_number = ?
            """
            
            result = self.db_manager.fetch_one(query, (invoice_number,))
            if result:
                purchase = self._row_to_purchase(result)
                # تحميل العناصر
                purchase = self.get_purchase_by_id(purchase.id)
                return purchase
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث بالفاتورة {invoice_number}: {str(e)}")
        
        return None
    
    def search_purchases(self, search_term: str = "", supplier_id: Optional[int] = None,
                        status: Optional[str] = None, start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> List[Purchase]:
        """البحث في فواتير الشراء"""
        try:
            query = """
            SELECT p.*, s.name as supplier_name
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
            """
            params = []
            
            if search_term:
                query += " AND (p.invoice_number LIKE ? OR p.supplier_invoice_number LIKE ? OR s.name LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 3)
            
            if supplier_id:
                query += " AND p.supplier_id = ?"
                params.append(supplier_id)
            
            if status:
                query += " AND p.status = ?"
                params.append(status)
            
            if start_date:
                query += " AND p.purchase_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND p.purchase_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY p.purchase_date DESC, p.id DESC"
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_purchase(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في فواتير الشراء: {str(e)}")
            return []
    
    def list_purchases(self, search_term: str = "", supplier_id: Optional[int] = None,
                       status: Optional[str] = None, payment_status: Optional[str] = None,
                       start_date: Optional[date] = None, end_date: Optional[date] = None,
                       limit: int = 200) -> List[Dict[str, Any]]:
        """جلب قائمة مبسطة من فواتير الشراء للاستخدام في الواجهة"""
        try:
            query = """
            SELECT
                p.id,
                p.invoice_number,
                COALESCE(s.name, '') as supplier_name,
                p.purchase_date,
                p.total_amount,
                p.paid_amount,
                p.remaining_amount,
                p.status,
                p.payment_status
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
            """
            params: List[Any] = []
            
            if search_term:
                query += " AND (p.invoice_number LIKE ? OR p.supplier_invoice_number LIKE ? OR s.name LIKE ?)"
                pattern = f"%{search_term}%"
                params.extend([pattern, pattern, pattern])
            
            if supplier_id:
                query += " AND p.supplier_id = ?"
                params.append(supplier_id)
            
            if status:
                query += " AND p.status = ?"
                params.append(status)
            
            if payment_status:
                query += " AND p.payment_status = ?"
                params.append(payment_status)
            
            if start_date:
                query += " AND p.purchase_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND p.purchase_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY p.purchase_date DESC, p.id DESC"
            if limit > 0:
                query += " LIMIT ?"
                params.append(limit)
            
            results = self.db_manager.fetch_all(query, params)
            return [self._row_to_purchase_dict(row) for row in results]
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب قائمة المشتريات: {str(e)}")
            return []
    
    def get_purchases_summary(self, start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> Dict[str, Any]:
        """ملخص رقمي لفواتير الشراء"""
        if not start_date and not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        elif start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date
        
        try:
            query = """
            SELECT
                COUNT(*) as total_purchases,
                SUM(total_amount) as total_amount,
                SUM(paid_amount) as total_paid,
                SUM(remaining_amount) as total_remaining
            FROM purchases
            WHERE purchase_date BETWEEN ? AND ? AND (status IS NULL OR status != 'ملغية')
            """
            result = self.db_manager.fetch_one(query, (start_date, end_date))
            total_invoices = int(result[0] or 0) if result else 0
            total_amount = float(result[1] or 0) if result else 0.0
            total_paid = float(result[2] or 0) if result else 0.0
            total_remaining = float(result[3] or 0) if result else 0.0
            avg_value = total_amount / total_invoices if total_invoices else 0.0
            
            return {
                'total_purchases': total_invoices,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'total_remaining': total_remaining,
                'avg_purchase_value': avg_value,
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب ملخص المشتريات: {str(e)}")
            return {
                'total_purchases': 0,
                'total_amount': 0.0,
                'total_paid': 0.0,
                'total_remaining': 0.0,
                'avg_purchase_value': 0.0,
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
    
    def get_recent_purchases(self, limit: int = 5) -> List[Dict[str, Any]]:
        """الحصول على أحدث فواتير الشراء"""
        return self.list_purchases(limit=limit)
    
    def update_purchase(self, purchase: Purchase) -> bool:
        """تحديث فاتورة شراء"""
        try:
            purchase.calculate_totals()
            
            query = """
            UPDATE purchases SET
                supplier_invoice_number = ?, expected_delivery_date = ?,
                received_date = ?, status = ?, payment_status = ?,
                payment_terms = ?, subtotal_amount = ?, discount_amount = ?,
                tax_amount = ?, shipping_cost = ?, total_amount = ?,
                paid_amount = ?, remaining_amount = ?, currency_id = ?,
                exchange_rate = ?, base_amount = ?, converted_amount = ?,
                notes = ?, updated_at = ?
            WHERE id = ?
            """
            
            # Multi-Currency: حساب المبالغ
            base_amount = purchase.base_amount if purchase.base_amount is not None else purchase.total_amount
            converted_amount = purchase.converted_amount if purchase.converted_amount is not None else purchase.total_amount
            exchange_rate = float(purchase.exchange_rate) if purchase.exchange_rate else 1.0
            
            params = (
                purchase.supplier_invoice_number,
                purchase.expected_delivery_date,
                purchase.received_date,
                purchase.status,
                purchase.payment_status,
                purchase.payment_terms,
                float(purchase.subtotal_amount),
                float(purchase.discount_amount),
                float(purchase.tax_amount),
                float(purchase.shipping_cost),
                float(purchase.total_amount),
                float(purchase.paid_amount),
                float(purchase.remaining_amount),
                # Multi-Currency Support
                purchase.currency_id,
                exchange_rate,
                float(base_amount) if base_amount else None,
                float(converted_amount) if converted_amount else None,
                purchase.notes,
                datetime.now().isoformat(),
                purchase.id
            )
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                if self.logger:
                    self.logger.info(f"تم تحديث فاتورة الشراء: {purchase.invoice_number}")
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث فاتورة الشراء {purchase.id}: {str(e)}")
        
        return False
    
    def receive_purchase_items(self, purchase_id: int, received_items: List[Dict[str, Any]]) -> bool:
        """استلام أصناف فاتورة الشراء"""
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False
            
            # تحديث الكميات المستلمة
            for received_item in received_items:
                item_id = received_item.get('item_id')
                quantity_received = Decimal(str(received_item.get('quantity_received', 0)))
                
                # العثور على العنصر وتحديثه
                for item in purchase.items:
                    if item.id == item_id:
                        item.quantity_received = min(quantity_received, item.quantity_ordered)
                        
                        # تحديث في قاعدة البيانات
                        update_query = """
                        UPDATE purchase_items 
                        SET quantity_received = ? 
                        WHERE id = ?
                        """
                        self.db_manager.execute_non_query(update_query, (float(item.quantity_received), item_id))
                        
                        # تحديث المخزون إذا تم الاستلام
                        if item.quantity_received > 0:
                            self._update_product_stock(item.product_id, item.quantity_received, 
                                                     item.unit_cost, item.expiry_date, item.batch_number)
                        break
            
            # تحديث حالة الفاتورة
            if purchase.is_fully_received:
                purchase.status = PurchaseStatus.RECEIVED.value
                purchase.received_date = date.today()
            elif purchase.is_partially_received:
                purchase.status = PurchaseStatus.PARTIAL.value
            
            # حفظ التحديثات
            success = self.update_purchase(purchase)
            
            if success:
                # 🔥 إطلاق الإشارات: إعلام النظام بالتغييرات
                try:
                    from ...core.signals import signals
                    signals.purchases_updated.emit()
                    signals.purchase_received.emit(purchase_id)
                    signals.inventory_updated.emit()  # المخزون تغير
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات: purchases_updated, purchase_received, inventory_updated")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في استلام أصناف فاتورة الشراء {purchase_id}: {str(e)}")
            return False
    
    def _update_product_stock(self, product_id: int, quantity: Decimal, 
                            unit_cost: Decimal, expiry_date: Optional[date] = None,
                            batch_number: Optional[str] = None):
        """تحديث مخزون المنتج"""
        try:
            # تحديث كمية المنتج
            update_query = """
            UPDATE products 
            SET current_stock = current_stock + ?,
                cost_price = ?,
                updated_at = ?
            WHERE id = ?
            """
            
            self.db_manager.execute_non_query(update_query, (
                float(quantity), float(unit_cost), datetime.now(), product_id
            ))
            
            # إضافة دفعة جديدة إذا كانت موجودة
            if batch_number or expiry_date:
                batch_query = """
                INSERT INTO batches (
                    product_id, batch_number, quantity, cost_price,
                    expiry_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                self.db_manager.execute_query(batch_query, (
                    product_id, batch_number, float(quantity), 
                    float(unit_cost), expiry_date, datetime.now()
                ))
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث مخزون المنتج {product_id}: {str(e)}")
    
    def cancel_purchase(self, purchase_id: int, reason: str = "") -> bool:
        """إلغاء فاتورة شراء"""
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False
            
            # التحقق من إمكانية الإلغاء
            if purchase.status == PurchaseStatus.RECEIVED.value:
                if self.logger:
                    self.logger.warning(f"لا يمكن إلغاء فاتورة الشراء {purchase_id} - تم استلامها")
                return False
            
            # إلغاء الفاتورة
            purchase.status = PurchaseStatus.CANCELLED.value
            if reason:
                purchase.notes = f"{purchase.notes or ''}\nسبب الإلغاء: {reason}".strip()
            
            return self.update_purchase(purchase)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء فاتورة الشراء {purchase_id}: {str(e)}")
            return False
    
    def generate_invoice_number(self) -> str:
        """إنشاء رقم فاتورة شراء"""
        try:
            # الحصول على آخر رقم فاتورة
            query = "SELECT MAX(CAST(SUBSTR(invoice_number, 4) AS INTEGER)) FROM purchases WHERE invoice_number LIKE 'PUR%'"
            result = self.db_manager.fetch_one(query)
            
            last_number = result[0] if result and result[0] else 0
            new_number = last_number + 1
            
            return f"PUR{new_number:06d}"
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء رقم فاتورة الشراء: {str(e)}")
            # رقم افتراضي في حالة الخطأ
            return f"PUR{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_purchases_report(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> Dict[str, Any]:
        """تقرير المشتريات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_purchases,
                COUNT(CASE WHEN status = 'معلقة' THEN 1 END) as pending_purchases,
                COUNT(CASE WHEN status = 'مستلمة' THEN 1 END) as received_purchases,
                COUNT(CASE WHEN status = 'جزئية' THEN 1 END) as partial_purchases,
                COUNT(CASE WHEN status = 'ملغية' THEN 1 END) as cancelled_purchases,
                SUM(CASE WHEN status != 'ملغية' THEN total_amount ELSE 0 END) as total_amount,
                SUM(CASE WHEN status != 'ملغية' THEN paid_amount ELSE 0 END) as total_paid,
                SUM(CASE WHEN status != 'ملغية' THEN remaining_amount ELSE 0 END) as total_remaining
            FROM purchases
            WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND purchase_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND purchase_date <= ?"
                params.append(end_date)
            
            result = self.db_manager.fetch_one(query, params)
            if result:
                return {
                    'total_purchases': result[0] or 0,
                    'pending_purchases': result[1] or 0,
                    'received_purchases': result[2] or 0,
                    'partial_purchases': result[3] or 0,
                    'cancelled_purchases': result[4] or 0,
                    'total_amount': float(result[5] or 0),
                    'total_paid': float(result[6] or 0),
                    'total_remaining': float(result[7] or 0)
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المشتريات: {str(e)}")
        
        return {
            'total_purchases': 0,
            'pending_purchases': 0,
            'received_purchases': 0,
            'partial_purchases': 0,
            'cancelled_purchases': 0,
            'total_amount': 0.0,
            'total_paid': 0.0,
            'total_remaining': 0.0
        }
    
    def _row_to_purchase(self, row) -> Purchase:
        """تحويل صف قاعدة البيانات إلى كائن فاتورة شراء
        
        Schema المتوقع: id, invoice_number, supplier_invoice_number, supplier_id, purchase_date,
        expected_delivery_date, received_date, status, payment_status, payment_terms,
        subtotal_amount, discount_amount, tax_amount, shipping_cost, total_amount,
        paid_amount, remaining_amount, currency_id, exchange_rate, base_amount, converted_amount,
        notes, created_by, created_at, updated_at (25 عمود) + supplier_name (26)
        """
        row_len = len(row)
        
        # قراءة حقول Multi-Currency - الأعمدة 17-20
        currency_id = row[17] if row_len > 17 and row[17] is not None else None
        exchange_rate = Decimal(str(row[18])) if row_len > 18 and row[18] is not None else Decimal('1.0')
        base_amount = Decimal(str(row[19])) if row_len > 19 and row[19] is not None else None
        converted_amount = Decimal(str(row[20])) if row_len > 20 and row[20] is not None else None
        
        return Purchase(
            id=row[0] if row_len > 0 else None,
            invoice_number=row[1] if row_len > 1 else "",
            supplier_invoice_number=row[2] if row_len > 2 else None,
            supplier_id=row[3] if row_len > 3 else 0,
            purchase_date=date.fromisoformat(row[4]) if row_len > 4 and row[4] else date.today(),
            expected_delivery_date=date.fromisoformat(row[5]) if row_len > 5 and row[5] else None,
            received_date=date.fromisoformat(row[6]) if row_len > 6 and row[6] else None,
            status=row[7] if row_len > 7 else PurchaseStatus.PENDING.value,
            payment_status=row[8] if row_len > 8 else PaymentStatus.UNPAID.value,
            payment_terms=row[9] if row_len > 9 else "نقدي",
            subtotal_amount=Decimal(str(row[10])) if row_len > 10 and row[10] is not None else Decimal('0'),
            discount_amount=Decimal(str(row[11])) if row_len > 11 and row[11] is not None else Decimal('0'),
            tax_amount=Decimal(str(row[12])) if row_len > 12 and row[12] is not None else Decimal('0'),
            shipping_cost=Decimal(str(row[13])) if row_len > 13 and row[13] is not None else Decimal('0'),
            total_amount=Decimal(str(row[14])) if row_len > 14 and row[14] is not None else Decimal('0'),
            paid_amount=Decimal(str(row[15])) if row_len > 15 and row[15] is not None else Decimal('0'),
            remaining_amount=Decimal(str(row[16])) if row_len > 16 and row[16] is not None else Decimal('0'),
            # Multi-Currency Support
            currency_id=currency_id,
            exchange_rate=exchange_rate,
            base_amount=base_amount,
            converted_amount=converted_amount,
            notes=row[21] if row_len > 21 else None,
            created_by=row[22] if row_len > 22 else None,
            created_at=datetime.fromisoformat(row[23]) if row_len > 23 and row[23] else None,
            updated_at=datetime.fromisoformat(row[24]) if row_len > 24 and row[24] else None,
            supplier_name=row[25] if row_len > 25 else ""
        )
    
    def _row_to_purchase_item(self, row) -> PurchaseItem:
        """تحويل صف قاعدة البيانات إلى كائن عنصر فاتورة شراء"""
        return PurchaseItem(
            id=row[0],
            purchase_id=row[1],
            product_id=row[2],
            quantity_ordered=Decimal(str(row[3])),
            quantity_received=Decimal(str(row[4])),
            unit_cost=Decimal(str(row[5])),
            discount_percent=Decimal(str(row[6])),
            discount_amount=Decimal(str(row[7])),
            tax_percent=Decimal(str(row[8])),
            tax_amount=Decimal(str(row[9])),
            total_amount=Decimal(str(row[10])),
            expiry_date=date.fromisoformat(row[11]) if row[11] else None,
            batch_number=row[12],
            notes=row[13],
            product_name=row[14] if len(row) > 14 else "",
            product_barcode=row[15] if len(row) > 15 else None
        )
    
    def _row_to_purchase_dict(self, row) -> Dict[str, Any]:
        """تحويل صف مختصر إلى قاموس مبسط"""
        try:
            purchase_date = row[3]
            if isinstance(purchase_date, datetime):
                purchase_date_str = purchase_date.date().isoformat()
            elif isinstance(purchase_date, date):
                purchase_date_str = purchase_date.isoformat()
            else:
                purchase_date_str = purchase_date
            
            return {
                'id': row[0],
                'invoice_number': row[1],
                'supplier_name': row[2] or "",
                'purchase_date': purchase_date_str,
                'total_amount': float(row[4] or 0),
                'paid_amount': float(row[5] or 0),
                'remaining_amount': float(row[6] or 0),
                'status': row[7] or "",
                'payment_status': row[8] or ""
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحويل صف المشتريات إلى قاموس: {e}")
            return {
                'id': row[0],
                'invoice_number': row[1],
                'supplier_name': "",
                'purchase_date': None,
                'total_amount': 0.0,
                'paid_amount': 0.0,
                'remaining_amount': 0.0,
                'status': "",
                'payment_status': ""
            }