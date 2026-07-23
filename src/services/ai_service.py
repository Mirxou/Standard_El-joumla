import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الذكاء الاصطناعي والتنبؤات (AI Service)
توفر وظائف تنبؤية مبسطة تعتمد على بيانات محلية (لا تتطلب مكتبات خارجية)
"""

import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List


class AIService:
    """خدمة بسيطة للتنبؤ والتحليل"""

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def demand_forecast_linear_regression(
        self,
        product_id: int,
        days: int = 30,
        forecast_days: int = 7,
        seasonal_period: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        تنبؤ الطلب باستخدام الانحدار الخطي مع تحليل الموسمية الأسبوعية.
        De-seasonalizes data, performs linear regression, and re-seasonalizes the forecast.
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            q = "SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)"  # noqa: E501
            rows = self.db.fetch_all(q, (product_id, "بيع", start))

            if not rows or len(rows) < seasonal_period:
                # لا يمكن حساب الموسمية ببيانات قليلة، العودة إلى التنبؤ البسيط
                return self._simple_linear_regression_forecast(rows, forecast_days)

            dates = [datetime.strptime(r["DATE(created_at)"], "%Y-%m-%d") for r in rows]
            y = [float(r["SUM(quantity)"] or 0) for r in rows]

            # 1. حساب المؤشرات الموسمية (للأسبوع)
            seasonal_indices = self._calculate_seasonal_indices(dates, y, seasonal_period)
            if not seasonal_indices:
                return self._simple_linear_regression_forecast(rows, forecast_days)

            # 2. إزالة تأثير الموسمية من البيانات
            deseasonalized_y = []
            for i, val in enumerate(y):
                day_of_week = dates[i].weekday()
                seasonal_index = seasonal_indices.get(day_of_week, 1.0)
                deseasonalized_y.append(val / seasonal_index if seasonal_index != 0 else 0)

            # 3. تطبيق الانحدار الخطي على البيانات منزوعة الموسمية
            start_date = dates[0]
            x = [(d - start_date).days for d in dates]

            n = len(x)
            sum_x = sum(x)
            sum_y_deseasonalized = sum(deseasonalized_y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, deseasonalized_y))
            sum_xx = sum(xi * xi for xi in x)

            denominator = n * sum_xx - sum_x * sum_x
            if denominator == 0:
                return self._simple_linear_regression_forecast(rows, forecast_days)

            m = (n * sum_xy - sum_x * sum_y_deseasonalized) / denominator
            c = (sum_y_deseasonalized - m * sum_x) / n

            # 4. التنبؤ بالاتجاه المستقبلي وإعادة إضافة الموسمية
            forecast = []
            last_day_idx = x[-1]
            for i in range(1, forecast_days + 1):
                future_day_idx = last_day_idx + i
                trend_forecast = m * future_day_idx + c

                future_date = start_date + timedelta(days=future_day_idx)
                day_of_week = future_date.weekday()
                seasonal_index = seasonal_indices.get(day_of_week, 1.0)

                final_forecast = trend_forecast * seasonal_index

                forecast.append(
                    {
                        "date": future_date.strftime("%Y-%m-%d"),
                        "predicted_quantity": max(0, round(final_forecast, 2)),
                    }
                )

            return forecast

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في التنبؤ الخطي المعزز بالموسمية للمنتج {product_id}: {e}")
            return []

    def _calculate_seasonal_indices(self, dates: List[datetime], y: List[float], period: int) -> Dict[int, float]:
        """حساب المؤشرات الموسمية لأيام الأسبوع"""
        day_sales = {i: [] for i in range(period)}
        for date, val in zip(dates, y):
            day_sales[date.weekday()].append(val)

        avg_day_sales = {day: statistics.mean(sales) if sales else 0 for day, sales in day_sales.items()}

        overall_avg = statistics.mean(y)
        if overall_avg == 0:
            return {}

        seasonal_indices = {day: avg / overall_avg for day, avg in avg_day_sales.items()}
        return seasonal_indices

    def _simple_linear_regression_forecast(self, rows: List[Any], forecast_days: int) -> List[Dict[str, Any]]:
        """تنبؤ خطي بسيط كخيار احتياطي"""
        if not rows or len(rows) < 2:
            return []

        dates = [datetime.strptime(r["DATE(created_at)"], "%Y-%m-%d") for r in rows]
        start_date = dates[0]
        x = [(d - start_date).days for d in dates]
        y = [float(r["SUM(quantity)"] or 0) for r in rows]

        n = len(x)
        sum_x, sum_y = sum(x), sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return []

        m = (n * sum_xy - sum_x * sum_y) / denominator
        c = (sum_y - m * sum_x) / n

        forecast = []
        last_day_idx = x[-1]
        for i in range(1, forecast_days + 1):
            future_day_idx = last_day_idx + i
            predicted_qty = m * future_day_idx + c
            future_date = start_date + timedelta(days=future_day_idx)
            forecast.append(
                {
                    "date": future_date.strftime("%Y-%m-%d"),
                    "predicted_quantity": max(0, round(predicted_qty, 2)),
                }
            )
        return forecast

    def demand_forecast_moving_average(self, product_id: int, days: int = 30, window: int = 7) -> float:
        """تنبؤ الطلب باستخدام متوسط متحرك على مبيعات الأيام الماضية"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            # افترض أن هناك جدول stock_movements حيث الحركة من نوع بيع
            q = "SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)"  # noqa: E501
            rows = self.db.fetch_all(q, (product_id, "بيع", start))
            daily = [r["SUM(quantity)"] or 0 for r in rows]
            if not daily:
                return 0.0
            # حساب متوسط متحرك بسيط آخر نافذة
            if len(daily) < window:
                return float(statistics.mean(daily))
            window_vals = daily[-window:]
            return float(statistics.mean(window_vals))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تقدير الطلب للمنتج {product_id}: {e}")
            return 0.0

    def detect_sales_anomalies(self, product_id: int, days: int = 30, z_thresh: float = 3.0) -> List[Dict[str, Any]]:
        """بحث عن أيام مبيعات شاذة بناءً على الانحراف المعياري (تبسيط)"""
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            q = "SELECT DATE(created_at), SUM(quantity) FROM stock_movements WHERE product_id = ? AND movement_type = ? AND created_at >= ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)"  # noqa: E501
            rows = self.db.fetch_all(q, (product_id, "بيع", start))
            daily = [r["SUM(quantity)"] or 0 for r in rows]
            dates = [r["DATE(created_at)"] for r in rows]
            if not daily or len(daily) < 2:
                return []
            mean = statistics.mean(daily)
            stdev = statistics.pstdev(daily) if len(daily) > 1 else 0
            anomalies = []
            for d, v in zip(dates, daily):
                z = (v - mean) / stdev if stdev > 0 else 0
                if abs(z) >= z_thresh:
                    anomalies.append({"date": d, "quantity": v, "z_score": z})
            return anomalies
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في كشف الشذوذ للمبيعات للمنتج {product_id}: {e}")
            return []

    def generate_insight_summary(self, start_date=None, end_date=None) -> Dict[str, Any]:
        """توليد ملخصات بسيطة - مثال تجريبي لاستخدام الذكاء التوليدي لاحقاً"""
        try:
            # تبسيط: إرجاع بعض مؤشرات الأداء من قواعد البيانات
            q_sales = 'SELECT SUM(total_amount), COUNT(*) FROM sales WHERE status = "confirmed"'
            params = []
            if start_date:
                q_sales += " AND created_at >= ?"
                params.append(start_date)
            if end_date:
                q_sales += " AND created_at <= ?"
                params.append(end_date)
            row = self.db.fetch_one(q_sales, tuple(params))
            total_revenue = float(row["SUM(total_amount)"] or 0)
            orders = int(row["COUNT(*)"] or 0)
            return {
                "total_revenue": total_revenue,
                "orders_count": orders,
                "note": "هذا ملخص تجريبي — استبدل بنموذج ML متقدم عند الحاجة.",
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توليد الملخص: {e}")
            return {}

    def detect_fraud_patterns(
        self, days: int = 60, min_refund_rate: float = 0.3, high_sales_count: int = 5
    ) -> Dict[str, Any]:
        """
        تحليل أنماط المبيعات والمرتجعات، ووضع علامات على المبيعات المشبوهة للمراجعة.
        """
        flagged_sales = set()
        actions_taken = []
        try:
            end = datetime.now()
            start = end - timedelta(days=days)

            # 1. المنتجات ذات معدل المرتجعات المرتفع
            # نحدد المبيعات المرتجعة مباشرة
            q_refunds = """
                SELECT s.id, p.name, si.quantity, s.total_amount
                FROM sales s
                JOIN sale_items si ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.type = 'refund' AND s.created_at >= ?
            """
            high_refund_sales = self.db.fetch_all(q_refunds, (start,))
            for sale in high_refund_sales:
                sale_id = sale["id"]
                product_name = sale["name"]
                if sale_id not in flagged_sales:
                    self._flag_sale_for_review(sale_id)
                    flagged_sales.add(sale_id)
                    actions_taken.append(f"Flagged sale {sale_id} (high-refund product: {product_name})")

            # 2. العملاء ذوو نشاط مرتجع متكرر أو مبالغ فيه
            q_customers = """
                SELECT s.customer_id, c.name, COUNT(s.id) as refund_count
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.type = 'refund' AND s.created_at >= ?
                GROUP BY s.customer_id
                HAVING refund_count >= ?
            """
            suspicious_customers = self.db.fetch_all(q_customers, (start, high_sales_count))
            for cust in suspicious_customers:
                customer_id = cust["customer_id"]
                customer_name = cust["name"]
                refund_count = cust["refund_count"]
                # ضع علامة على آخر معاملة مرتجعة لهذا العميل
                q_last_refund = (
                    "SELECT id FROM sales WHERE customer_id = ? AND type = 'refund' ORDER BY created_at DESC LIMIT 1"
                )
                last_sale = self.db.fetch_one(q_last_refund, (customer_id,))
                if last_sale and last_sale["id"] not in flagged_sales:
                    sale_id = last_sale["id"]
                    self._flag_sale_for_review(sale_id)
                    flagged_sales.add(sale_id)
                    actions_taken.append(
                        f"Flagged sale {sale_id} for suspicious customer '{customer_name}' (total refunds: {refund_count})"  # noqa: E501
                    )

            return {
                "status": "success",
                "flagged_sales_count": len(flagged_sales),
                "actions": actions_taken,
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في كشف الاحتيال ووضع العلامات: {e}")
            return {"status": "error", "message": str(e)}

    def _flag_sale_for_review(self, sale_id: int):
        """تحديث حالة البيع إلى 'under_review'."""
        try:
            # التحقق من أن الحالة الحالية ليست نهائية (مثل ملغاة)
            current_status = self.db.fetch_one("SELECT status FROM sales WHERE id = ?", (sale_id,))
            if current_status and current_status["status"] not in ["canceled", "under_review"]:
                self.db.execute("UPDATE sales SET status = 'under_review' WHERE id = ?", (sale_id,))
                if self.logger:
                    self.logger.info(f"Sale {sale_id} flagged for fraud review.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to flag sale {sale_id}: {e}")

    def smart_assistant_query(self, query: str) -> Dict[str, Any]:
        """
        تحليل استعلامات اللغة الطبيعية البسيطة باستخدام الكلمات المفتاحية.
        """
        query = query.lower()
        response = {"query": query, "intent": "unknown", "data": None, "message": ""}

        try:
            # نية: الحصول على ملخص المبيعات
            if "مبيعات" in query or "إيرادات" in query:
                response["intent"] = "get_revenue_summary"
                summary = self.generate_insight_summary()
                total_revenue = summary.get("total_revenue", 0)
                response["data"] = {"total_revenue": total_revenue}
                response["message"] = f"إجمالي الإيرادات هو: {total_revenue:,.2f} د.ج."
                return response

            # نية: الحصول على عدد الطلبات
            if "طلبات" in query or "فواتير" in query:
                response["intent"] = "get_orders_count"
                summary = self.generate_insight_summary()
                orders_count = summary.get("orders_count", 0)
                response["data"] = {"orders_count": orders_count}
                response["message"] = f"لدينا {orders_count} طلب مؤكد."
                return response

            # نية: الحصول على المنتجات ذات المخزون المنخفض
            if "مخزون منخفض" in query or "نواقص" in query:
                response["intent"] = "get_low_stock_products"
                # افتراض وجود حقل reorder_level في جدول products
                q = "SELECT name, stock_quantity, reorder_level FROM products WHERE stock_quantity < reorder_level ORDER BY stock_quantity ASC LIMIT 5"  # noqa: E501
                low_stock_products = self.db.fetch_all(q)
                response["data"] = [{"name": r["name"], "quantity": r["stock_quantity"], "reorder_level": r["reorder_level"]} for r in low_stock_products]
                if not low_stock_products:
                    response["message"] = "لا توجد منتجات حالياً تحت مستوى إعادة الطلب."
                else:
                    response["message"] = "المنتجات التالية لديها مخزون منخفض:"
                return response

            # نية: الحصول على المنتجات الأكثر مبيعاً
            if "أفضل مبيعات" in query or "أكثر منتج" in query:
                response["intent"] = "get_top_selling_products"
                q = """
                    SELECT p.name, SUM(si.quantity) as total_sold
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.id
                    GROUP BY p.name
                    ORDER BY total_sold DESC
                    LIMIT 5
                """
                top_products = self.db.fetch_all(q)
                response["data"] = [{"name": r["name"], "total_sold": r["total_sold"]} for r in top_products]
                response["message"] = "المنتجات الأكثر مبيعاً هي:"
                return response

            # في حال عدم العثور على نية واضحة
            response["message"] = (
                "عفواً، لم أفهم طلبك. يمكنك أن تسألني عن: 'المبيعات'، 'الطلبات'، 'المخزون المنخفض'، أو 'أفضل المبيعات'."
            )
            return response

        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في المساعد الذكي للاستعلام "{query}": {e}')
            response["message"] = "عفواً، حدث خطأ أثناء معالجة طلبك."
            return response
