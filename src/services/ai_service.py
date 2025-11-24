#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الذكاء الاصطناعي والتنبؤات (AI Service)
توفر وظائف تنبؤية مبسطة تعتمد على بيانات محلية (لا تتطلب مكتبات خارجية)
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import deque
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class AIService:
    """خدمة بسيطة للتنبؤ والتحليل"""
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def demand_forecast_linear_regression(self, product_id: int, days: int = 30, forecast_days: int = 7) -> List[Dict[str, Any]]:
        """تنبؤ الطلب باستخدام الانحراف الخطي البسيط (Linear Regression)"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            q = 'SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)'
            rows = self.db.fetch_all(q, (product_id, 'بيع', start))
            
            if not rows or len(rows) < 2:
                return []

            # تحويل التواريخ إلى أرقام (أيام من البداية)
            dates = [datetime.strptime(r[0], "%Y-%m-%d") for r in rows]
            start_date = dates[0]
            x = [(d - start_date).days for d in dates]
            y = [float(r[1] or 0) for r in rows]

            # حساب الانحدار الخطي: y = mx + c
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_xx = sum(xi * xi for xi in x)

            denominator = (n * sum_xx - sum_x * sum_x)
            if denominator == 0:
                return []

            m = (n * sum_xy - sum_x * sum_y) / denominator
            c = (sum_y - m * sum_x) / n

            # التنبؤ للمستقبل
            forecast = []
            last_day_idx = x[-1]
            for i in range(1, forecast_days + 1):
                future_day_idx = last_day_idx + i
                predicted_qty = m * future_day_idx + c
                future_date = start_date + timedelta(days=future_day_idx)
                forecast.append({
                    'date': future_date.strftime("%Y-%m-%d"),
                    'predicted_quantity': max(0, round(predicted_qty, 2))
                })
            
            return forecast

        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في التنبؤ الخطي للمنتج {product_id}: {e}')
            return []

    def demand_forecast_moving_average(self, product_id: int, days: int = 30, window: int = 7) -> float:
        """تنبؤ الطلب باستخدام متوسط متحرك على مبيعات الأيام الماضية"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            # افترض أن هناك جدول stock_movements حيث الحركة من نوع بيع
            q = 'SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)'
            rows = self.db.fetch_all(q, (product_id, 'بيع', start))
            daily = [r[1] or 0 for r in rows]
            if not daily:
                return 0.0
            # حساب متوسط متحرك بسيط آخر نافذة
            if len(daily) < window:
                return float(statistics.mean(daily))
            window_vals = daily[-window:]
            return float(statistics.mean(window_vals))
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تقدير الطلب للمنتج {product_id}: {e}')
            return 0.0

    def detect_sales_anomalies(self, product_id: int, days: int = 30, z_thresh: float = 3.0) -> List[Dict[str, Any]]:
        """بحث عن أيام مبيعات شاذة بناءً على الانحراف المعياري (تبسيط)"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            q = 'SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)'
            rows = self.db.fetch_all(q, (product_id, 'بيع', start))
            daily = [r[1] or 0 for r in rows]
            dates = [r[0] for r in rows]
            if not daily or len(daily) < 2:
                return []
            mean = statistics.mean(daily)
            stdev = statistics.pstdev(daily) if len(daily)>1 else 0
            anomalies = []
            for d, v in zip(dates, daily):
                z = (v - mean) / stdev if stdev>0 else 0
                if abs(z) >= z_thresh:
                    anomalies.append({'date': d, 'quantity': v, 'z_score': z})
            return anomalies
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في كشف الشذوذ للمبيعات للمنتج {product_id}: {e}')
            return []

    def generate_insight_summary(self, start_date=None, end_date=None) -> Dict[str, Any]:
        """توليد ملخصات بسيطة - مثال تجريبي لاستخدام الذكاء التوليدي لاحقاً"""
        try:
            # تبسيط: إرجاع بعض مؤشرات الأداء من قواعد البيانات
            q_sales = 'SELECT SUM(total_amount), COUNT(*) FROM sales WHERE status = "confirmed"'
            params = []
            if start_date:
                q_sales += ' AND created_at >= ?'
                params.append(start_date)
            if end_date:
                q_sales += ' AND created_at <= ?'
                params.append(end_date)
            row = self.db.fetch_one(q_sales, tuple(params))
            total_revenue = float(row[0] or 0)
            orders = int(row[1] or 0)
            return {'total_revenue': total_revenue, 'orders_count': orders, 'note': 'هذا ملخص تجريبي — استبدل بنموذج ML متقدم عند الحاجة.'}
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في توليد الملخص: {e}')
            return {}

    def detect_fraud_patterns(self, days: int = 60, min_refund_rate: float = 0.3, min_large_sales: int = 3) -> Dict[str, Any]:
        """تحليل أنماط المبيعات والمرتجعات لكشف العمليات المشبوهة (مؤشرات أولية)"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            # المنتجات ذات معدل مرتجعات مرتفع
            q = '''
                SELECT p.id, p.name, 
                    COALESCE(SUM(CASE WHEN s.type = 'sale' THEN si.quantity ELSE 0 END),0) as sold_qty,
                    COALESCE(SUM(CASE WHEN s.type = 'refund' THEN si.quantity ELSE 0 END),0) as refund_qty
                FROM products p
                LEFT JOIN sale_items si ON si.product_id = p.id
                LEFT JOIN sales s ON si.sale_id = s.id AND s.created_at >= ?
                GROUP BY p.id
                HAVING sold_qty > 0 AND (refund_qty * 1.0 / sold_qty) >= ?
                ORDER BY refund_qty DESC
            '''
            suspicious_products = self.db.fetch_all(q, (start, min_refund_rate))
            suspicious = []
            for row in suspicious_products:
                suspicious.append({
                    'product_id': row[0],
                    'product_name': row[1],
                    'sold_qty': row[2],
                    'refund_qty': row[3],
                    'refund_rate': round(row[3]/row[2], 2) if row[2] else 0
                })
            # العملاء الذين قاموا بمبيعات كبيرة متكررة ثم مرتجعات
            q2 = '''
                SELECT c.id, c.name, COUNT(s.id) as sales_count, SUM(s.total_amount) as total_sales
                FROM customers c
                JOIN sales s ON s.customer_id = c.id AND s.created_at >= ?
                GROUP BY c.id
                HAVING sales_count >= ? AND total_sales > 0
                ORDER BY total_sales DESC
            '''
            suspicious_customers = self.db.fetch_all(q2, (start, min_large_sales))
            customers = []
            for row in suspicious_customers:
                customers.append({
                    'customer_id': row[0],
                    'customer_name': row[1],
                    'sales_count': row[2],
                    'total_sales': row[3]
                })
            return {
                'suspicious_products': suspicious,
                'suspicious_customers': customers
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في كشف الاحتيال: {e}')
            return {'suspicious_products': [], 'suspicious_customers': []}
