#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المشتريات - Purchase Service
توفّر دوال مساعدة للواجهة لإدارة فواتير الشراء
"""

from typing import List, Dict, Any, Optional
from datetime import date
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.purchase import Purchase, PurchaseManager
from models.purchase import PurchaseStatus, PaymentStatus
from models.supplier import SupplierManager


class PurchaseService:
    """خدمة المشتريات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.purchase_manager = PurchaseManager(db_manager, logger)
        self.supplier_manager = SupplierManager(db_manager, logger)
        self._purchase_cache: Dict[str, Any] = {
            'data': [],
            'summary': {},
            'filters': {}
        }
    
    # ===== العمليات الأساسية =====
    
    def create_purchase(self, purchase: Purchase) -> Optional[int]:
        """إنشاء فاتورة شراء"""
        try:
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

