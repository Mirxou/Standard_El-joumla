#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المبيعات المحسّنة - Enhanced Sales Service
يدير أوامر البيع، بنود الفاتورة، المرتجعات، والرصيد/المدفوعات
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from models.sale import Sale, SaleItem, SaleManager, SaleStatus
from enum import Enum

# Enum جديد لحالة الطلب
class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class SalesService:

    def update_order_status(self, order_id: int, new_status: str, user_id: int = None) -> bool:
        """تحديث حالة الطلب (OrderStatus)"""
        try:
            sale_manager = SaleManager(self.db, self.logger)
            sale = sale_manager.get_sale(order_id)
            if not sale:
                return False
            sale.status = new_status
            sale_manager.update_sale_status(order_id, new_status, user_id)
            if self.logger:
                self.logger.info(f"تم تحديث حالة الطلب {order_id} إلى {new_status}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث حالة الطلب: {e}")
            return False

    def track_payment(self, order_id: int) -> dict:
        """إرجاع معلومات المدفوعات المرتبطة بالطلب"""
        try:
            sale_manager = SaleManager(self.db, self.logger)
            payments = sale_manager.get_payments_for_sale(order_id)
            total_paid = sum(p.get('amount', 0) for p in payments)
            return {
                "order_id": order_id,
                "payments": payments,
                "total_paid": total_paid
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تتبع المدفوعات: {e}")
            return {"order_id": order_id, "payments": [], "total_paid": 0}

    def create_refund(self, order_id: int, amount: float, reason: str = "") -> bool:
        """إنشاء عملية استرداد (Refund) لطلب"""
        try:
            sale_manager = SaleManager(self.db, self.logger)
            result = sale_manager.create_refund(order_id, amount, reason)
            if self.logger:
                self.logger.info(f"تم إنشاء استرداد للطلب {order_id} بمبلغ {amount}")
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الاسترداد: {e}")
            return False

    def create_return(self, order_id: int, items: list, reason: str = "") -> bool:
        """إنشاء عملية مرتجع (Return) لطلب"""
        try:
            sale_manager = SaleManager(self.db, self.logger)
            result = sale_manager.create_return(order_id, items, reason)
            if self.logger:
                self.logger.info(f"تم إنشاء مرتجع للطلب {order_id}")
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء المرتجع: {e}")
            return False

    """خدمة شاملة للمبيعات"""
    def __init__(self, db_manager, logger=None, inventory_service=None, product_service=None):
        self.db = db_manager
        self.logger = logger
        self.inventory_service = inventory_service
        self.product_service = product_service

    def create_order(self, customer_id: int, items: List[Dict[str, Any]], order_meta: Dict[str, Any] = None) -> Optional[int]:
        """إنشاء أمر بيع (غير مفوتر بعد)؛ items = [{product_id, variant_id, quantity, unit_price}]
        يعالج حجز المخزون تلقائياً إن أمكن"""
        try:
            # Prefer using legacy SaleManager to ensure compatibility with existing DB schema
            try:
                sale_manager = SaleManager(self.db, self.logger)
                invoice_no = sale_manager.generate_invoice_number()
            except Exception:
                sale_manager = None

            total = sum(Decimal(str(i.get('quantity', 1))) * Decimal(str(i.get('unit_price', 0))) for i in items)

            if sale_manager:
                sale = Sale(
                    invoice_number=invoice_no,
                    customer_id=customer_id,
                    sale_date=datetime.now().date(),
                    status=SaleStatus.DRAFT,
                    subtotal=total,
                    total_amount=total,
                    items=[]
                )

                for it in items:
                    si = SaleItem(
                        product_id=it.get('product_id'),
                        quantity=int(it.get('quantity', 1)),
                        unit_price=Decimal(str(it.get('unit_price', 0)))
                    )
                    si.calculate_total()
                    sale.items.append(si)

                order_id = sale_manager.create_sale(sale)
                if order_id:
                    if self.logger:
                        self.logger.info(f'تم إنشاء أمر بيع (عن طريق SaleManager) ID={order_id}، المجموع={total}')
                    return order_id

            # Fallback: try raw insert using core schema (invoice_number, customer_id, total_amount, final_amount, sale_date...)
            now = datetime.now()
            invoice_no = f"ORD-{int(now.timestamp())}"
            query = """
            INSERT INTO sales (
                invoice_number, customer_id, total_amount, final_amount, sale_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (invoice_no, customer_id, float(total), float(total), now.date(), now, now)
            res = self.db.execute_query(query, params)
            try:
                order_id = self.db.get_last_insert_id()
            except Exception:
                order_id = None

            if not order_id:
                return None

            # حفظ البنود باستخدام SaleManager helper to ensure batch/cost/profit handling
            try:
                helper_sm = SaleManager(self.db, self.logger)
            except Exception:
                helper_sm = None

            for it in items:
                # construct a SaleItem-like object for helper
                si = None
                try:
                    si = SaleItem(
                        sale_id=order_id,
                        product_id=it.get('product_id'),
                        quantity=int(it.get('quantity', 1)),
                        unit_price=Decimal(str(it.get('unit_price', 0)))
                    )
                    si.calculate_total()
                except Exception:
                    si = None

                if si and helper_sm:
                    helper_sm._create_sale_item(si)

                # حجز المخزون
                try:
                    if self.inventory_service and si:
                        self.inventory_service.reserve_stock(si.product_id, int(si.quantity), reference_id=order_id, reference_type='sale')
                except Exception:
                    if self.logger:
                        self.logger.warning('فشل حجز المخزون لبند في الطلب')

            if self.logger:
                self.logger.info(f'تم إنشاء أمر بيع ID={order_id}، المجموع={total}')
            return order_id
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء أمر البيع: {e}')
            else:
                print('ERROR creating order:', e)
            return None

    def confirm_order(self, order_id: int) -> bool:
        """تأكيد أمر البيع، تحويله لفاتورة وتخفيض المخزون الفعلي"""
        try:
            # محاولة تحديث حالة الطلب إذا كانت العمود موجوداً
            q = "UPDATE sales SET status = ?, updated_at = ? WHERE id = ?"
            try:
                # Use 'confirmed' (string) directly instead of enum value to ensure compatibility
                self.db.execute_query(q, ('confirmed', datetime.now(), order_id))
            except Exception as e:
                # تخطي الخطأ إذا لم يكن العمود موجوداً في مخطط قاعدة البيانات
                msg = str(e)
                if 'no such column' in msg and 'status' in msg:
                    if self.logger:
                        self.logger.info('عمود status غير موجود في جدول sales؛ تخطي تحديث الحالة')
                    else:
                        print('WARN: sales.status column not present; skipping status update')
                else:
                    raise

            # تسجيل حركة المخزون للبنود
            items = self.db.fetch_all('SELECT product_id, quantity FROM sale_items WHERE sale_id = ?', (order_id,))
            for row in items:
                product_id, qty = row[0], row[1]
                if self.inventory_service:
                    try:
                        # InventoryService.StockMovement is defined at module-level in inventory_service_enhanced
                        from services.inventory_service_enhanced import StockMovement as InvStockMovement
                        movement = InvStockMovement(product_id=product_id, movement_type='بيع', quantity=int(qty), reference_id=order_id, reference_type='sale')
                        self.inventory_service.record_stock_movement(movement)
                    except Exception:
                        try:
                            # last-resort: call reserve_stock if available
                            if hasattr(self.inventory_service, 'record_stock_movement'):
                                # create a minimal movement-like object
                                movement = type('M', (), {'product_id': product_id, 'movement_type': 'بيع', 'quantity': int(qty), 'reference_id': order_id, 'reference_type': 'sale'})()
                                self.inventory_service.record_stock_movement(movement)
                        except Exception:
                            if self.logger:
                                self.logger.warning('فشل تسجيل حركة المخزون لبند الطلب')

            if self.logger:
                self.logger.info(f'تم تأكيد أمر البيع ID={order_id}')
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تأكيد أمر البيع {order_id}: {e}')
            else:
                print('ERROR confirming order:', e)
            return False

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.db.fetch_one('SELECT * FROM sales WHERE id = ?', (order_id,))
            if not row:
                return None
            items = self.db.fetch_all('SELECT * FROM sale_items WHERE sale_id = ?', (order_id,))
            return {'order': row, 'items': items}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في قراءة الطلب {order_id}: {e}')
            return None

    def process_return(self, sale_id: int, items: List[Dict[str, Any]], reason: str = '') -> Optional[int]:
        """معالجة مرتجع؛ يعيد المخزون ويولد مستند مرتجع"""
        try:
            now = datetime.now()
            q = "INSERT INTO returns (sale_id, reason, created_at) VALUES (?, ?, ?)"
            res = self.db.execute_query(q, (sale_id, reason, now))
            try:
                return_id = self.db.get_last_insert_id()
            except Exception:
                return None
            for it in items:
                self.db.execute_query('INSERT INTO return_items (return_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)', (return_id, it.get('product_id'), it.get('quantity',1), float(it.get('unit_price',0))))
                if self.inventory_service:
                    self.inventory_service.record_stock_movement(self.inventory_service.__class__.StockMovement(product_id=it.get('product_id'), movement_type='إرجاع', quantity=int(it.get('quantity',1)), reference_id=return_id, reference_type='return'))
            if self.logger:
                self.logger.info(f'تم إنشاء مرتجع ID={return_id} للطلب {sale_id}')
            return return_id
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في معالجة المرتجع: {e}')
            return None
