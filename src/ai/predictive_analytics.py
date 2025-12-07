"""
التحليلات التنبؤية - Predictive Analytics
ML-based predictions for sales, inventory, and customer behavior

Features:
- التنبؤ بالمبيعات (Sales forecasting)
- التنبؤ بنفاذ المخزون (Stock-out prediction)
- تحليل سلوك العملاء (Customer behavior analysis)
- التوصيات الذكية (Smart recommendations)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics


@dataclass
class SalesForecast:
    """نموذج توقعات المبيعات"""
    product_id: int
    product_name: str
    current_stock: float
    predicted_sales: float
    days_until_stockout: Optional[int]
    recommended_reorder_quantity: float
    confidence: float


@dataclass
class CustomerInsight:
    """رؤى العملاء"""
    customer_id: int
    customer_name: str
    total_purchases: float
    average_order_value: float
    purchase_frequency: float
    predicted_next_purchase: Optional[str]
    customer_segment: str
    lifetime_value: float


class PredictiveEngine:
    """محرك التحليلات التنبؤية"""
    
    def __init__(self, db_manager):
        """
        تهيئة محرك التنبؤات
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
    
    def forecast_sales(self, product_id: Optional[int] = None, days: int = 30) -> List[SalesForecast]:
        """
        التنبؤ بالمبيعات للمنتجات
        
        Args:
            product_id: معرف المنتج (None للجميع)
            days: عدد الأيام للتنبؤ
            
        Returns:
            قائمة بتوقعات المبيعات
        """
        forecasts = []
        
        # الحصول على المنتجات
        if product_id:
            # محاولة الحصول على المنتج من قاعدة البيانات
            try:
                products = self.db.execute_query(
                    "SELECT * FROM products WHERE id = ?", 
                    (product_id,)
                )
                products = products if products else []
            except Exception:
                products = []
        else:
            # الحصول على جميع المنتجات
            try:
                products = self.db.execute_query("SELECT * FROM products")
                products = products if products else []
            except Exception:
                products = []
        
        for product in products:
            if not product:
                continue
                
            # حساب معدل المبيعات اليومي من البيانات التاريخية
            sales_history = self._get_sales_history(product['id'], days=90)
            
            if not sales_history:
                continue
            
            # حساب المتوسط والاتجاه
            daily_sales = self._calculate_daily_sales(sales_history)
            avg_daily_sales = statistics.mean(daily_sales) if daily_sales else 0
            
            # التنبؤ
            predicted_sales = avg_daily_sales * days
            current_stock = product.get('quantity', 0)
            
            # حساب أيام حتى نفاذ المخزون
            if avg_daily_sales > 0:
                days_until_stockout = int(current_stock / avg_daily_sales)
            else:
                days_until_stockout = None
            
            # كمية إعادة الطلب الموصى بها
            reorder_point = product.get('reorder_point', 0)
            recommended_reorder = max(
                predicted_sales * 1.2,  # 20% احتياطي
                reorder_point * 2
            )
            
            # درجة الثقة (بناءً على كمية البيانات)
            confidence = min(len(sales_history) / 30, 1.0)  # max 1.0
            
            forecast = SalesForecast(
                product_id=product['id'],
                product_name=product.get('name', 'Unknown'),
                current_stock=current_stock,
                predicted_sales=predicted_sales,
                days_until_stockout=days_until_stockout,
                recommended_reorder_quantity=recommended_reorder,
                confidence=confidence
            )
            forecasts.append(forecast)
        
        # ترتيب حسب أولوية النفاذ
        forecasts.sort(key=lambda x: x.days_until_stockout if x.days_until_stockout else 999)
        
        return forecasts
    
    def analyze_customer_behavior(self, customer_id: Optional[int] = None) -> List[CustomerInsight]:
        """
        تحليل سلوك العملاء
        
        Args:
            customer_id: معرف العميل (None للجميع)
            
        Returns:
            قائمة برؤى العملاء
        """
        insights = []
        
        # الحصول على العملاء
        if customer_id:
            try:
                customers = self.db.execute_query(
                    "SELECT * FROM customers WHERE id = ?",
                    (customer_id,)
                )
                customers = customers if customers else []
            except Exception:
                customers = []
        else:
            try:
                customers = self.db.execute_query("SELECT * FROM customers")
                customers = customers if customers else []
            except Exception:
                customers = []
        
        for customer in customers:
            if not customer:
                continue
            
            # الحصول على تاريخ المشتريات
            purchases = self._get_customer_purchases(customer['id'])
            
            if not purchases:
                continue
            
            # حساب المقاييس
            total_purchases = sum(p.get('total', 0) for p in purchases)
            avg_order_value = total_purchases / len(purchases) if purchases else 0
            
            # حساب تكرار الشراء (أيام بين المشتريات)
            purchase_dates = [
                datetime.fromisoformat(p['date']) 
                for p in purchases 
                if p.get('date')
            ]
            purchase_dates.sort()
            
            if len(purchase_dates) > 1:
                intervals = [
                    (purchase_dates[i+1] - purchase_dates[i]).days
                    for i in range(len(purchase_dates) - 1)
                ]
                avg_interval = statistics.mean(intervals)
                purchase_frequency = 30 / avg_interval if avg_interval > 0 else 0
                
                # التنبؤ بالشراء التالي
                last_purchase = purchase_dates[-1]
                predicted_next = last_purchase + timedelta(days=avg_interval)
                predicted_next_str = predicted_next.strftime('%Y-%m-%d')
            else:
                purchase_frequency = 0
                predicted_next_str = None
            
            # تصنيف العميل
            customer_segment = self._segment_customer(
                total_purchases, 
                purchase_frequency,
                len(purchases)
            )
            
            # حساب القيمة الدائمة للعميل (LTV)
            # تقدير بسيط: الإنفاق السنوي × 3 سنوات
            annual_spending = total_purchases * (365 / max(
                (purchase_dates[-1] - purchase_dates[0]).days, 1
            )) if len(purchase_dates) > 1 else total_purchases
            lifetime_value = annual_spending * 3
            
            insight = CustomerInsight(
                customer_id=customer['id'],
                customer_name=customer.get('name', 'Unknown'),
                total_purchases=total_purchases,
                average_order_value=avg_order_value,
                purchase_frequency=purchase_frequency,
                predicted_next_purchase=predicted_next_str,
                customer_segment=customer_segment,
                lifetime_value=lifetime_value
            )
            insights.append(insight)
        
        # ترتيب حسب القيمة الدائمة
        insights.sort(key=lambda x: x.lifetime_value, reverse=True)
        
        return insights
    
    def get_product_recommendations(
        self, 
        customer_id: int, 
        limit: int = 5
    ) -> List[Dict]:
        """
        الحصول على توصيات المنتجات للعميل
        
        Args:
            customer_id: معرف العميل
            limit: عدد التوصيات
            
        Returns:
            قائمة بالمنتجات الموصى بها
        """
        # الحصول على مشتريات العميل السابقة
        purchases = self._get_customer_purchases(customer_id)
        purchased_product_ids = set()
        
        for purchase in purchases:
            items = purchase.get('items', [])
            for item in items:
                purchased_product_ids.add(item.get('product_id'))
        
        # الحصول على جميع المنتجات
        try:
            all_products = self.db.execute_query("SELECT * FROM products")
            all_products = all_products if all_products else []
        except Exception:
            all_products = []
        
        # تصفية المنتجات التي لم يشتريها
        recommendations = []
        for product in all_products:
            if product['id'] not in purchased_product_ids:
                # حساب درجة التوصية (بناءً على الشعبية والمخزون)
                sales_count = self._get_product_sales_count(product['id'])
                score = sales_count * (1 if product.get('quantity', 0) > 0 else 0.5)
                
                recommendations.append({
                    'product_id': product['id'],
                    'name': product.get('name', ''),
                    'price': product.get('price', 0),
                    'score': score,
                    'in_stock': product.get('quantity', 0) > 0
                })
        
        # ترتيب حسب الدرجة
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:limit]
    
    def detect_anomalies(self, days: int = 7) -> List[Dict]:
        """
        اكتشاف الشذوذات في المبيعات
        
        Args:
            days: عدد الأيام للفحص
            
        Returns:
            قائمة بالشذوذات المكتشفة
        """
        anomalies = []
        
        # الحصول على جميع المنتجات
        try:
            products = self.db.execute_query("SELECT * FROM products")
            products = products if products else []
        except Exception:
            products = []
        
        for product in products:
            # الحصول على المبيعات الأخيرة
            recent_sales = self._get_sales_history(product['id'], days=days)
            historical_sales = self._get_sales_history(product['id'], days=90)
            
            if not historical_sales:
                continue
            
            # حساب المتوسط والانحراف المعياري
            historical_daily = self._calculate_daily_sales(historical_sales)
            if not historical_daily:
                continue
                
            avg = statistics.mean(historical_daily)
            stdev = statistics.stdev(historical_daily) if len(historical_daily) > 1 else 0
            
            # حساب المبيعات الأخيرة
            recent_daily = self._calculate_daily_sales(recent_sales)
            recent_avg = statistics.mean(recent_daily) if recent_daily else 0
            
            # كشف الشذوذ (إذا كان الفرق > 2 انحراف معياري)
            if stdev > 0 and abs(recent_avg - avg) > 2 * stdev:
                anomaly_type = "زيادة غير عادية" if recent_avg > avg else "انخفاض غير عادي"
                
                anomalies.append({
                    'product_id': product['id'],
                    'product_name': product.get('name', ''),
                    'type': anomaly_type,
                    'expected_daily_sales': avg,
                    'actual_daily_sales': recent_avg,
                    'deviation': abs(recent_avg - avg) / stdev if stdev > 0 else 0
                })
        
        return anomalies
    
    # ========== Helper Methods ==========
    
    def _get_sales_history(self, product_id: int, days: int) -> List[Dict]:
        """
        الحصول على تاريخ المبيعات للمنتج
        
        Args:
            product_id: معرف المنتج
            days: عدد الأيام للرجوع
            
        Returns:
            قائمة ببيانات المبيعات
        """
        try:
            if not self.db:
                return []
            
            # استعلام للحصول على المبيعات التاريخية
            query = """
                SELECT 
                    si.quantity,
                    s.sale_date as date,
                    si.unit_price,
                    si.total_amount
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ?
                AND s.sale_date >= date('now', '-' || ? || ' days')
                ORDER BY s.sale_date DESC
            """
            
            results = self.db.execute_query(query, (product_id, days))
            return results if results else []
        except Exception:
            return []
    
    def _calculate_daily_sales(self, sales_history: List[Dict]) -> List[float]:
        """حساب المبيعات اليومية"""
        daily_sales = {}
        
        for sale in sales_history:
            date = sale.get('date', '')[:10]  # YYYY-MM-DD
            quantity = sale.get('quantity', 0)
            
            if date not in daily_sales:
                daily_sales[date] = 0
            daily_sales[date] += quantity
        
        return list(daily_sales.values())
    
    def _get_customer_purchases(self, customer_id: int) -> List[Dict]:
        """
        الحصول على مشتريات العميل
        
        Args:
            customer_id: معرف العميل
            
        Returns:
            قائمة ببيانات المشتريات
        """
        try:
            if not self.db:
                return []
            
            # استعلام للحصول على مشتريات العميل
            query = """
                SELECT 
                    s.id as sale_id,
                    s.sale_date as date,
                    s.total_amount,
                    s.payment_method,
                    COUNT(si.id) as item_count
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                WHERE s.customer_id = ?
                GROUP BY s.id, s.sale_date, s.total_amount, s.payment_method
                ORDER BY s.sale_date DESC
            """
            
            results = self.db.execute_query(query, (customer_id,))
            return results if results else []
        except Exception:
            return []
    
    def _segment_customer(
        self, 
        total_purchases: float, 
        frequency: float,
        order_count: int
    ) -> str:
        """تصنيف العميل"""
        if total_purchases > 10000 and frequency > 2:
            return "VIP"
        elif total_purchases > 5000 or frequency > 1:
            return "عميل دائم"
        elif order_count > 3:
            return "عميل نشط"
        else:
            return "عميل جديد"
    
    def _get_product_sales_count(self, product_id: int) -> int:
        """
        عدد مرات بيع المنتج
        
        Args:
            product_id: معرف المنتج
            
        Returns:
            عدد مرات البيع
        """
        try:
            if not self.db:
                return 0
            
            # استعلام للحصول على عدد مرات البيع
            query = """
                SELECT COUNT(DISTINCT sale_id) as sale_count
                FROM sale_items
                WHERE product_id = ?
            """
            
            result = self.db.execute_scalar(query, (product_id,))
            return int(result) if result else 0
        except Exception:
            return 0


if __name__ == "__main__":
    print("📊 Predictive Analytics Test")
    print("=" * 50)
    print("✅ Module loaded successfully!")
    print("Note: Full testing requires database integration")
