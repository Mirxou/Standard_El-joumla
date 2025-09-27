#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المبيعات - Sales Service
تحتوي على جميع العمليات المتعلقة بالمبيعات ونقاط البيع
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from decimal import Decimal
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from models.product import Product, ProductManager
from models.customer import Customer, CustomerManager

@dataclass
class SalesReport:
    """تقرير المبيعات"""
    total_sales: int
    total_revenue: float
    total_profit: float
    average_sale_value: float
    top_products: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]
    sales_by_day: List[Dict[str, Any]]
    sales_by_payment_method: List[Dict[str, Any]]
    period_start: date
    period_end: date

@dataclass
class DailySummary:
    """ملخص يومي للمبيعات"""
    date: date
    total_sales: int
    total_revenue: float
    total_profit: float
    cash_sales: float
    card_sales: float
    credit_sales: float
    returns: float
    net_sales: float

@dataclass
class POSSession:
    """جلسة نقطة البيع"""
    id: Optional[int] = None
    user_id: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    opening_cash: float = 0.0
    closing_cash: float = 0.0
    total_sales: float = 0.0
    total_returns: float = 0.0
    cash_in_drawer: float = 0.0
    is_active: bool = True

class SalesService:
    """خدمة المبيعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger
        self.sale_manager = SaleManager(db_manager, logger)
        self.product_manager = ProductManager(db_manager, logger)
        self.customer_manager = CustomerManager(db_manager, logger)
        self.current_session: Optional[POSSession] = None
    
    # ===== إدارة المبيعات =====
    
    def create_sale(self, sale: Sale, user_id: Optional[int] = None) -> Optional[int]:
        """إنشاء فاتورة مبيعات جديدة"""
        try:
            # التحقق من توفر المنتجات
            for item in sale.items:
                product = self.product_manager.get_product_by_id(item.product_id)
                if not product:
                    if self.logger:
                        self.logger.warning(f"المنتج {item.product_id} غير موجود")
                    return None
                
                if product.current_stock < item.quantity:
                    if self.logger:
                        self.logger.warning(f"كمية غير كافية للمنتج {product.name}")
                    return None
            
            # إنشاء الفاتورة
            sale_id = self.sale_manager.create_sale(sale)
            if sale_id:
                # تحديث جلسة نقطة البيع
                if self.current_session:
                    self._update_session_sales(sale.total_amount)
                
                if self.logger:
                    self.logger.info(f"تم إنشاء فاتورة مبيعات جديدة: {sale_id}")
            
            return sale_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فاتورة المبيعات: {str(e)}")
            return None
    
    def add_sale_item(self, sale_id: int, product_id: int, quantity: float, 
                     unit_price: Optional[float] = None, discount: float = 0.0) -> bool:
        """إضافة منتج لفاتورة المبيعات"""
        try:
            # الحصول على المنتج
            product = self.product_manager.get_product_by_id(product_id)
            if not product:
                if self.logger:
                    self.logger.warning(f"المنتج {product_id} غير موجود")
                return False
            
            # التحقق من توفر الكمية
            if product.current_stock < quantity:
                if self.logger:
                    self.logger.warning(f"كمية غير كافية للمنتج {product.name}")
                return False
            
            # استخدام سعر البيع الافتراضي إذا لم يتم تحديد سعر
            if unit_price is None:
                unit_price = product.selling_price
            
            # إنشاء عنصر المبيعات
            sale_item = SaleItem(
                sale_id=sale_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount
            )
            
            # إضافة العنصر
            success = self.sale_manager.add_sale_item(sale_item)
            if success:
                # تحديث إجمالي الفاتورة
                self._update_sale_total(sale_id)
                
                if self.logger:
                    self.logger.info(f"تم إضافة منتج {product.name} للفاتورة {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة منتج للفاتورة: {str(e)}")
            return False
    
    def remove_sale_item(self, sale_id: int, product_id: int) -> bool:
        """حذف منتج من فاتورة المبيعات"""
        try:
            success = self.sale_manager.remove_sale_item(sale_id, product_id)
            if success:
                # تحديث إجمالي الفاتورة
                self._update_sale_total(sale_id)
                
                if self.logger:
                    self.logger.info(f"تم حذف المنتج {product_id} من الفاتورة {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف منتج من الفاتورة: {str(e)}")
            return False
    
    def complete_sale(self, sale_id: int, payment_method: str, 
                     amount_paid: float, user_id: Optional[int] = None) -> bool:
        """إتمام فاتورة المبيعات"""
        try:
            # الحصول على الفاتورة
            sale = self.sale_manager.get_sale_by_id(sale_id)
            if not sale:
                return False
            
            # التحقق من حالة الفاتورة
            if sale.status != SaleStatus.PENDING.value:
                if self.logger:
                    self.logger.warning(f"لا يمكن إتمام الفاتورة {sale_id} - الحالة: {sale.status}")
                return False
            
            # التحقق من المبلغ المدفوع
            if amount_paid < sale.total_amount:
                if self.logger:
                    self.logger.warning(f"المبلغ المدفوع أقل من إجمالي الفاتورة")
                return False
            
            # إتمام الفاتورة
            success = self.sale_manager.complete_sale(sale_id, payment_method, amount_paid)
            if success:
                # تحديث رصيد العميل إذا كان الدفع آجل
                if payment_method == PaymentMethod.CREDIT.value and sale.customer_id:
                    self.customer_manager.update_balance(
                        sale.customer_id, 
                        sale.total_amount, 
                        "increase"
                    )
                
                # تحديث جلسة نقطة البيع
                if self.current_session and payment_method == PaymentMethod.CASH.value:
                    self.current_session.cash_in_drawer += amount_paid
                
                if self.logger:
                    self.logger.info(f"تم إتمام فاتورة المبيعات {sale_id}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إتمام فاتورة المبيعات {sale_id}: {str(e)}")
            return False
    
    def cancel_sale(self, sale_id: int, reason: str = "", user_id: Optional[int] = None) -> bool:
        """إلغاء فاتورة المبيعات"""
        try:
            success = self.sale_manager.cancel_sale(sale_id, reason)
            if success:
                # تحديث جلسة نقطة البيع
                if self.current_session:
                    sale = self.sale_manager.get_sale_by_id(sale_id)
                    if sale:
                        self.current_session.total_returns += sale.total_amount
                
                if self.logger:
                    self.logger.info(f"تم إلغاء فاتورة المبيعات {sale_id}: {reason}")
            
            return success
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إلغاء فاتورة المبيعات {sale_id}: {str(e)}")
            return False
    
    def search_sales(self, query: str = "", customer_id: Optional[int] = None,
                    start_date: Optional[date] = None, end_date: Optional[date] = None,
                    status: Optional[str] = None, limit: int = 100) -> List[Sale]:
        """البحث في المبيعات"""
        try:
            return self.sale_manager.search_sales(query, customer_id, start_date, end_date, status, limit)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في البحث في المبيعات: {str(e)}")
            return []
    
    # ===== إدارة جلسات نقطة البيع =====
    
    def start_pos_session(self, user_id: int, opening_cash: float = 0.0) -> Optional[int]:
        """بدء جلسة نقطة البيع"""
        try:
            # التحقق من عدم وجود جلسة نشطة
            if self.current_session and self.current_session.is_active:
                if self.logger:
                    self.logger.warning("يوجد جلسة نشطة بالفعل")
                return None
            
            # إنشاء جلسة جديدة
            query = """
            INSERT INTO pos_sessions (user_id, start_time, opening_cash, cash_in_drawer, is_active)
            VALUES (?, ?, ?, ?, 1)
            """
            
            now = datetime.now()
            params = (user_id, now, opening_cash, opening_cash)
            
            result = self.db_manager.execute_query(query, params)
            if result and hasattr(result, 'lastrowid'):
                session_id = result.lastrowid
                
                self.current_session = POSSession(
                    id=session_id,
                    user_id=user_id,
                    start_time=now,
                    opening_cash=opening_cash,
                    cash_in_drawer=opening_cash,
                    is_active=True
                )
                
                if self.logger:
                    self.logger.info(f"تم بدء جلسة نقطة البيع {session_id}")
                
                return session_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في بدء جلسة نقطة البيع: {str(e)}")
        
        return None
    
    def end_pos_session(self, closing_cash: float, user_id: Optional[int] = None) -> bool:
        """إنهاء جلسة نقطة البيع"""
        try:
            if not self.current_session or not self.current_session.is_active:
                if self.logger:
                    self.logger.warning("لا توجد جلسة نشطة لإنهائها")
                return False
            
            # تحديث الجلسة
            query = """
            UPDATE pos_sessions SET
                end_time = ?, closing_cash = ?, is_active = 0
            WHERE id = ?
            """
            
            now = datetime.now()
            params = (now, closing_cash, self.current_session.id)
            
            result = self.db_manager.execute_query(query, params)
            if result and result.rowcount > 0:
                self.current_session.end_time = now
                self.current_session.closing_cash = closing_cash
                self.current_session.is_active = False
                
                if self.logger:
                    self.logger.info(f"تم إنهاء جلسة نقطة البيع {self.current_session.id}")
                
                return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنهاء جلسة نقطة البيع: {str(e)}")
        
        return False
    
    def get_current_session(self) -> Optional[POSSession]:
        """الحصول على الجلسة الحالية"""
        return self.current_session
    
    # ===== التقارير والإحصائيات =====
    
    def generate_sales_report(self, start_date: date, end_date: date) -> SalesReport:
        """إنشاء تقرير المبيعات"""
        try:
            # إحصائيات عامة
            sales_stats = self._get_sales_statistics(start_date, end_date)
            
            # أفضل المنتجات
            top_products = self._get_top_selling_products(start_date, end_date)
            
            # أفضل العملاء
            top_customers = self._get_top_customers(start_date, end_date)
            
            # المبيعات حسب اليوم
            sales_by_day = self._get_sales_by_day(start_date, end_date)
            
            # المبيعات حسب طريقة الدفع
            sales_by_payment = self._get_sales_by_payment_method(start_date, end_date)
            
            report = SalesReport(
                total_sales=sales_stats['total_sales'],
                total_revenue=sales_stats['total_revenue'],
                total_profit=sales_stats['total_profit'],
                average_sale_value=sales_stats['average_sale_value'],
                top_products=top_products,
                top_customers=top_customers,
                sales_by_day=sales_by_day,
                sales_by_payment_method=sales_by_payment,
                period_start=start_date,
                period_end=end_date
            )
            
            return report
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء تقرير المبيعات: {str(e)}")
            return SalesReport(
                total_sales=0, total_revenue=0, total_profit=0, average_sale_value=0,
                top_products=[], top_customers=[], sales_by_day=[], sales_by_payment_method=[],
                period_start=start_date, period_end=end_date
            )
    
    def get_daily_summary(self, target_date: date) -> DailySummary:
        """الحصول على ملخص يومي للمبيعات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                SUM(CASE WHEN payment_method = 'نقدي' THEN total_amount ELSE 0 END) as cash_sales,
                SUM(CASE WHEN payment_method = 'بطاقة' THEN total_amount ELSE 0 END) as card_sales,
                SUM(CASE WHEN payment_method = 'آجل' THEN total_amount ELSE 0 END) as credit_sales,
                SUM(CASE WHEN status = 'ملغي' THEN total_amount ELSE 0 END) as returns
            FROM sales
            WHERE DATE(sale_date) = ? AND status != 'ملغي'
            """
            
            result = self.db_manager.fetch_one(query, (target_date.isoformat(),))
            
            if result:
                total_revenue = result[1] or 0
                returns = result[5] or 0
                net_sales = total_revenue - returns
                
                # حساب الربح (يتطلب تكلفة المنتجات)
                profit = self._calculate_daily_profit(target_date)
                
                summary = DailySummary(
                    date=target_date,
                    total_sales=result[0] or 0,
                    total_revenue=total_revenue,
                    total_profit=profit,
                    cash_sales=result[2] or 0,
                    card_sales=result[3] or 0,
                    credit_sales=result[4] or 0,
                    returns=returns,
                    net_sales=net_sales
                )
                
                return summary
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الملخص اليومي: {str(e)}")
        
        return DailySummary(
            date=target_date, total_sales=0, total_revenue=0, total_profit=0,
            cash_sales=0, card_sales=0, credit_sales=0, returns=0, net_sales=0
        )
    
    # ===== الدوال المساعدة =====
    
    def _update_sale_total(self, sale_id: int):
        """تحديث إجمالي الفاتورة"""
        try:
            query = """
            UPDATE sales SET
                total_amount = (
                    SELECT SUM((quantity * unit_price) - discount)
                    FROM sale_items
                    WHERE sale_id = ?
                ),
                updated_at = ?
            WHERE id = ?
            """
            
            params = (sale_id, datetime.now(), sale_id)
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث إجمالي الفاتورة {sale_id}: {str(e)}")
    
    def _update_session_sales(self, amount: float):
        """تحديث مبيعات الجلسة"""
        if self.current_session:
            self.current_session.total_sales += amount
    
    def _get_sales_statistics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """الحصول على إحصائيات المبيعات"""
        try:
            query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as average_sale_value
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (start_date.isoformat(), end_date.isoformat()))
            
            if result:
                # حساب الربح الإجمالي
                total_profit = self._calculate_period_profit(start_date, end_date)
                
                return {
                    'total_sales': result[0] or 0,
                    'total_revenue': result[1] or 0,
                    'average_sale_value': result[2] or 0,
                    'total_profit': total_profit
                }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على إحصائيات المبيعات: {str(e)}")
        
        return {'total_sales': 0, 'total_revenue': 0, 'average_sale_value': 0, 'total_profit': 0}
    
    def _get_top_selling_products(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أفضل المنتجات مبيعاً"""
        try:
            query = """
            SELECT 
                p.id, p.name, 
                SUM(si.quantity) as total_quantity,
                SUM(si.quantity * si.unit_price - si.discount) as total_revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            GROUP BY p.id, p.name
            ORDER BY total_quantity DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat(), limit))
            
            return [
                {
                    'product_id': row[0],
                    'product_name': row[1],
                    'total_quantity': row[2],
                    'total_revenue': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل المنتجات: {str(e)}")
            return []
    
    def _get_top_customers(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على أفضل العملاء"""
        try:
            query = """
            SELECT 
                c.id, c.name,
                COUNT(s.id) as total_purchases,
                SUM(s.total_amount) as total_spent
            FROM customers c
            JOIN sales s ON c.id = s.customer_id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat(), limit))
            
            return [
                {
                    'customer_id': row[0],
                    'customer_name': row[1],
                    'total_purchases': row[2],
                    'total_spent': row[3]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على أفضل العملاء: {str(e)}")
            return []
    
    def _get_sales_by_day(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على المبيعات حسب اليوم"""
        try:
            query = """
            SELECT 
                DATE(sale_date) as sale_date,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            GROUP BY DATE(sale_date)
            ORDER BY sale_date
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            
            return [
                {
                    'date': row[0],
                    'total_sales': row[1],
                    'total_revenue': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المبيعات حسب اليوم: {str(e)}")
            return []
    
    def _get_sales_by_payment_method(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """الحصول على المبيعات حسب طريقة الدفع"""
        try:
            query = """
            SELECT 
                payment_method,
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM sales
            WHERE DATE(sale_date) BETWEEN ? AND ? AND status = 'مكتمل'
            GROUP BY payment_method
            ORDER BY total_revenue DESC
            """
            
            results = self.db_manager.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            
            return [
                {
                    'payment_method': row[0],
                    'total_sales': row[1],
                    'total_revenue': row[2]
                }
                for row in results
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المبيعات حسب طريقة الدفع: {str(e)}")
            return []
    
    def _calculate_daily_profit(self, target_date: date) -> float:
        """حساب ربح يوم محدد"""
        try:
            query = """
            SELECT SUM(
                (si.unit_price - p.cost_price) * si.quantity - si.discount
            ) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) = ? AND s.status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (target_date.isoformat(),))
            return result[0] if result and result[0] else 0.0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب الربح اليومي: {str(e)}")
            return 0.0
    
    def _calculate_period_profit(self, start_date: date, end_date: date) -> float:
        """حساب ربح فترة محددة"""
        try:
            query = """
            SELECT SUM(
                (si.unit_price - p.cost_price) * si.quantity - si.discount
            ) as total_profit
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE DATE(s.sale_date) BETWEEN ? AND ? AND s.status = 'مكتمل'
            """
            
            result = self.db_manager.fetch_one(query, (start_date.isoformat(), end_date.isoformat()))
            return result[0] if result and result[0] else 0.0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حساب ربح الفترة: {str(e)}")
            return 0.0