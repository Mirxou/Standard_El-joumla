#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المشتريات - Purchase Service
توفّر دوال مساعدة للواجهة لإدارة فواتير الشراء
"""

from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.purchase import Purchase, PurchaseManager
from models.purchase import PurchaseStatus, PaymentStatus
from models.supplier import SupplierManager
from services.exchange_rate_service import ExchangeRateService


class PurchaseService:
    """خدمة المشتريات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.purchase_manager = PurchaseManager(db_manager, logger)
        self.supplier_manager = SupplierManager(db_manager, logger)
        self.exchange_rate_service = ExchangeRateService(db_manager, logger)
        self._purchase_cache: Dict[str, Any] = {
            'data': [],
            'summary': {},
            'filters': {}
        }
    
    # ===== العمليات الأساسية =====
    
    def create_purchase(self, purchase: Purchase) -> Optional[int]:
        """إنشاء فاتورة شراء"""
        try:
            # Multi-Currency: حساب المبالغ بالعملة الأساسية
            if purchase.currency_id:
                try:
                    # الحصول على العملة الأساسية
                    base_currency = self.exchange_rate_service.currency_manager.get_base_currency()
                    if base_currency:
                        # الحصول على سعر الصرف
                        exchange_rate = self.exchange_rate_service.get_exchange_rate(
                            purchase.currency_id,
                            base_currency.id,
                            purchase.purchase_date
                        )
                        
                        if exchange_rate:
                            purchase.exchange_rate = exchange_rate
                            # حساب المبلغ بالعملة الأساسية
                            purchase.base_amount = purchase.total_amount * exchange_rate
                            purchase.converted_amount = purchase.total_amount
                            
                            if self.logger:
                                self.logger.debug(
                                    f"تم حساب المبلغ بالعملة الأساسية: {purchase.base_amount} "
                                    f"(سعر الصرف: {exchange_rate})"
                                )
                        else:
                            # إذا لم يوجد سعر صرف، استخدم المبلغ الأساسي
                            purchase.base_amount = purchase.total_amount
                            purchase.converted_amount = purchase.total_amount
                            purchase.exchange_rate = Decimal('1.0')
                    else:
                        # إذا لم توجد عملة أساسية، استخدم المبلغ الأساسي
                        purchase.base_amount = purchase.total_amount
                        purchase.converted_amount = purchase.total_amount
                        purchase.exchange_rate = Decimal('1.0')
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"خطأ في حساب سعر الصرف: {str(e)}")
                    # في حالة الخطأ، استخدم المبلغ الأساسي
                    purchase.base_amount = purchase.total_amount
                    purchase.converted_amount = purchase.total_amount
                    purchase.exchange_rate = Decimal('1.0')
            else:
                # إذا لم تكن هناك عملة محددة، استخدم المبلغ الأساسي
                purchase.base_amount = purchase.total_amount
                purchase.converted_amount = purchase.total_amount
                purchase.exchange_rate = Decimal('1.0')
            
            return self.purchase_manager.create_purchase(purchase)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فاتورة الشراء: {e}")
            return None
    
    def get_purchase_by_id(self, purchase_id: int) -> Optional[Purchase]:
        """جلب فاتورة شراء بالمعرّف"""
        return self.purchase_manager.get_purchase_by_id(purchase_id)
    
    def list_purchases(self, search_term: str = "", supplier_id: Optional[int] = None,
                       status: Optional[str] = None, payment_status: Optional[str] = None,
                       start_date: Optional[date] = None, end_date: Optional[date] = None,
                       limit: int = 200) -> List[Dict[str, Any]]:
        """إرجاع قائمة مبسطة للاستخدام في الواجهة"""
        try:
            normalized_status = self._normalize_status(status)
            normalized_payment = self._normalize_payment_status(payment_status)
            
            results = self.purchase_manager.list_purchases(
                search_term=search_term,
                supplier_id=supplier_id,
                status=normalized_status,
                payment_status=normalized_payment,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            self._purchase_cache['filters'] = {
                'search_term': search_term,
                'supplier_id': supplier_id,
                'status': status,
                'payment_status': payment_status,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            }
            self._purchase_cache['data'] = results
            
            return results
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب قائمة المشتريات: {e}")
            return []
    
    def get_purchases_summary(self, start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> Dict[str, Any]:
        """ملخص رقمي للمشتريات"""
        try:
            summary = self.purchase_manager.get_purchases_summary(start_date, end_date)
            self._purchase_cache['summary'] = summary
            return summary
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في جلب ملخص المشتريات: {e}")
            return {
                'total_purchases': 0,
                'total_amount': 0.0,
                'total_paid': 0.0,
                'total_remaining': 0.0,
                'avg_purchase_value': 0.0,
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None
            }
    
    def refresh_data(self) -> Dict[str, Any]:
        """إعادة تحميل البيانات حسب آخر مرشّحات"""
        filters = self._purchase_cache.get('filters') or {}
        data = self.list_purchases(
            search_term=filters.get('search_term', ""),
            supplier_id=filters.get('supplier_id'),
            status=filters.get('status'),
            payment_status=filters.get('payment_status'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            limit=filters.get('limit', 200)
        )
        summary = self.get_purchases_summary(
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date')
        )
        return {'data': data, 'summary': summary}
    
    def cancel_purchase(self, purchase_id: int, reason: str = "") -> bool:
        """إلغاء فاتورة شراء"""
        return self.purchase_manager.cancel_purchase(purchase_id, reason)
    
    # ===== دوال مساعدة =====
    
    def _normalize_status(self, status_value: Optional[str]) -> Optional[str]:
        if not status_value or status_value == "الكل":
            return None
        if isinstance(status_value, PurchaseStatus):
            return status_value.value
        mapping = {
            'معلقة': PurchaseStatus.PENDING.value,
            'مستلمة': PurchaseStatus.RECEIVED.value,
            'جزئية': PurchaseStatus.PARTIAL.value,
            'ملغية': PurchaseStatus.CANCELLED.value,
            'مرتجعة': PurchaseStatus.RETURNED.value,
            'pending': PurchaseStatus.PENDING.value,
            'received': PurchaseStatus.RECEIVED.value,
            'partial': PurchaseStatus.PARTIAL.value,
            'cancelled': PurchaseStatus.CANCELLED.value,
            'returned': PurchaseStatus.RETURNED.value
        }
        key = status_value.strip().lower()
        return mapping.get(status_value, mapping.get(key, status_value))
    
    def _normalize_payment_status(self, payment_value: Optional[str]) -> Optional[str]:
        if not payment_value or payment_value == "الكل":
            return None
        if isinstance(payment_value, PaymentStatus):
            return payment_value.value
        mapping = {
            'غير مدفوعة': PaymentStatus.UNPAID.value,
            'مدفوعة جزئياً': PaymentStatus.PARTIAL.value,
            'مدفوعة': PaymentStatus.PAID.value,
            'متأخرة': PaymentStatus.OVERDUE.value,
            'unpaid': PaymentStatus.UNPAID.value,
            'partial': PaymentStatus.PARTIAL.value,
            'paid': PaymentStatus.PAID.value,
            'overdue': PaymentStatus.OVERDUE.value
        }
        key = payment_value.strip().lower()
        return mapping.get(payment_value, mapping.get(key, payment_value))

    # ===== Agentic AI Capabilities (Vision 2030) =====

    def create_auto_reorder_draft(self, product_id: int, quantity: int = 10) -> Optional[int]:
        """
        إنشاء مسودة طلب شراء تلقائياً (Agentic Action)
        يقوم النظام بتحديد المورد المناسب وإنشاء الفاتورة
        """
        try:
            # 1. جلب المنتج لمعرفة المورد الافتراضي
            from src.models.product import ProductManager
            product_manager = ProductManager(self.db_manager, self.logger)
            product = product_manager.get_product_by_id(product_id)
            
            if not product:
                raise ValueError("المنتج غير موجود")
                
            supplier_id = getattr(product, 'supplier_id', None)
            
            # 2. إذا لم يوجد مورد، نحاول إيجاد آخر مورد تم الشراء منه
            if not supplier_id:
                last_purchase_query = """
                SELECT supplier_id FROM purchases p
                JOIN purchase_items pi ON p.id = pi.purchase_id
                WHERE pi.product_id = ?
                ORDER BY p.purchase_date DESC LIMIT 1
                """
                result = self.db_manager.fetch_one(last_purchase_query, (product_id,))
                if result:
                    supplier_id = result[0]
            
            if not supplier_id:
                # Fallback: Pick the first active supplier (Not ideal but "Agentic" attempt for demo)
                # In production, we should ask user.
                raise ValueError("لا يوجد مورد محدد للمنتج")

            # 3. حساب السعر (آخر سعر شراء أو سعر التكلفة)
            cost_price = product.cost_price
            
            # 4. إنشاء الفاتورة
            purchase = Purchase(
                supplier_id=supplier_id,
                purchase_date=date.today(),
                status=PurchaseStatus.PENDING,  # مسودة
                payment_status=PaymentStatus.UNPAID,
                total_amount=Decimal(quantity) * cost_price,
                notes="Created by Vision 2030 Agentic AI (Auto-Reorder)"
            )
            
            purchase_id = self.create_purchase(purchase)
            if not purchase_id:
                return None
                
            # 5. إضافة البند (نحتاج إلى purchase_items table insertion logic)
            # بما أن add_purchase_item قد لا يكون موجوداً مباشرة كطريقة عامة هنا، 
            # سنستخدم purchase_manager.add_item إذا توفر، أو SQL مباشر
            
            # للتبسيط، سنفترض وجود purchase_manager.add_item أو ننفذ SQL
            # سنقوم بإضافة البند يدوياً هنا لضمان العمل
            
            item_query = """
            INSERT INTO purchase_items (purchase_id, product_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?)
            """
            item_total = Decimal(quantity) * cost_price
            self.db_manager.execute_query(item_query, (purchase_id, product_id, quantity, float(cost_price), float(item_total)))
            
            return purchase_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Agentic Auto-Reorder Failed: {e}")
            return None

