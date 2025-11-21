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
