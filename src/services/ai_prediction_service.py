from datetime import timedelta

import numpy as np
import pandas as pd

from src.ai.predictive_analytics import PredictiveEngine


class AIPredictionService:
    """
    The 'Oracle': AI-driven insights for Sales and Inventory.
    Uses simple statistical learning (Regression/Moving Average) to forecast trends.
    """

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self.engine = PredictiveEngine(db_manager)

    def get_proactive_insights(self):
        """Delegate to PredictiveEngine"""
        return self.engine.generate_proactive_insights()

    def predict_sales_next_month(self):
        """
        Predict total sales for the upcoming month based on historical daily sales.
        """
        # 1. Fetch Historical Data (Last 90 days)
        query = """
            SELECT sale_date, SUM(final_amount) as daily_total
            FROM sales
            WHERE status NOT IN ('cancelled', 'ملغية')
            GROUP BY sale_date
            ORDER BY sale_date ASC
        """
        conn = self.db.get_connection()
        df = pd.read_sql_query(query, conn)

        if df.empty or len(df) < 10:
            return 0.0, "Insufficient data for prediction"

        # 2. Preprocess
        df["sale_date"] = pd.to_datetime(df["sale_date"])
        # Convert dates to ordinal for linear regression
        df["date_ordinal"] = df["sale_date"].map(pd.Timestamp.toordinal)

        # 3. Simple Linear Regression (y = mx + b)
        X = df["date_ordinal"].values
        y = df["daily_total"].values

        # Calculate slope (m) and intercept (b)
        n = len(X)
        m = (n * np.sum(X * y) - np.sum(X) * np.sum(y)) / (n * np.sum(X**2) - (np.sum(X)) ** 2)
        b = (np.sum(y) - m * np.sum(X)) / n

        # 4. Forecast next 30 days
        last_date = df["sale_date"].max()
        future_total = 0

        for i in range(1, 31):
            future_date = last_date + timedelta(days=i)
            future_ordinal = future_date.toordinal()
            prediction = m * future_ordinal + b
            if prediction < 0:
                prediction = 0
            future_total += prediction

        return round(future_total, 2), "Growth Trend" if m > 0 else "Decline Trend"

    def detect_anomalies(self):
        """
        Flags sales transactions that are > 3 standard deviations from the mean.
        """
        query = "SELECT id, invoice_number, final_amount as total_amount FROM sales WHERE status NOT IN ('cancelled', 'ملغية')"  # noqa: E501
        conn = self.db.get_connection()
        df = pd.read_sql_query(query, conn)

        if df.empty:
            return []

        mean = df["total_amount"].mean()
        std = df["total_amount"].std()

        # Z-Score Anomaly Detection
        threshold = 3 * std
        anomalies = df[df["total_amount"] > (mean + threshold)]

        return anomalies[["invoice_number", "total_amount"]].to_dict("records")

    def forecast_sales(self, **kwargs):
        """تنبؤ المبيعات التفصيلي"""
        try:
            days = kwargs.get('days', 30)
            query = """
                SELECT sale_date, SUM(final_amount) as daily_total
                FROM sales
                WHERE status NOT IN ('cancelled', 'ملغية')
                  AND sale_date >= DATE('now', '-90 days')
                GROUP BY sale_date
                ORDER BY sale_date ASC
            """
            conn = self.db.get_connection()
            df = pd.read_sql_query(query, conn)

            if df.empty or len(df) < 7:
                return {"forecast": [], "total_predicted": 0, "trend": "insufficient_data"}

            df["sale_date"] = pd.to_datetime(df["sale_date"])
            avg_daily = df["daily_total"].mean()
            std_daily = df["daily_total"].std()

            # Simple trend using last 7 vs previous 7 days
            if len(df) >= 14:
                recent_avg = df.tail(7)["daily_total"].mean()
                previous_avg = df.head(7)["daily_total"].mean()
                trend_factor = recent_avg / previous_avg if previous_avg > 0 else 1.0
            else:
                trend_factor = 1.0

            from datetime import datetime as _dt
            forecast = []
            last_date = df["sale_date"].max()
            total = 0.0
            for i in range(1, days + 1):
                pred_date = last_date + timedelta(days=i)
                predicted = avg_daily * trend_factor
                if predicted < 0:
                    predicted = 0
                total += predicted
                forecast.append({
                    "date": pred_date.strftime('%Y-%m-%d'),
                    "predicted_sales": round(float(predicted), 2),
                })

            trend = "growth" if trend_factor > 1.05 else ("decline" if trend_factor < 0.95 else "stable")
            return {"forecast": forecast, "total_predicted": round(total, 2), "trend": trend}
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in forecast_sales: {e}")
            return {"forecast": [], "total_predicted": 0, "trend": "error"}

    def forecast_demand(self, **kwargs):
        """تنبؤ الطلب"""
        try:
            product_id = kwargs.get('product_id')
            days = kwargs.get('days', 30)

            query = """
                SELECT si.product_id, DATE(s.sale_date) as sale_date,
                       SUM(si.quantity) as daily_demand
                FROM sale_items si
                JOIN sales s ON s.id = si.sale_id
                WHERE s.status NOT IN ('cancelled', 'ملغية')
                  AND s.sale_date >= DATE('now', '-90 days')
            """
            params = []
            if product_id:
                query += " AND si.product_id = ?"
                params.append(product_id)

            query += " GROUP BY si.product_id, DATE(s.sale_date) ORDER BY sale_date"
            conn = self.db.get_connection()
            df = pd.read_sql_query(query, conn, params=params if params else None)

            if df.empty:
                return {
                    "forecast": [{"date": _dt.now().strftime('%Y-%m-%d'), "predicted_demand": 0}],
                    "summary": {"total_demand": 0, "avg_daily_demand": 0},
                }

            avg_demand = df["daily_demand"].mean()

            from datetime import datetime as _dt
            last_date = pd.to_datetime(df["sale_date"]).max()
            forecast = []
            total_demand = 0.0
            for i in range(1, days + 1):
                pred_date = last_date + timedelta(days=i)
                forecast.append({
                    "date": pred_date.strftime('%Y-%m-%d'),
                    "predicted_demand": round(float(avg_demand), 2),
                })
                total_demand += avg_demand

            return {
                "forecast": forecast,
                "summary": {"total_demand": round(total_demand, 2), "avg_daily_demand": round(float(avg_demand), 2)},
            }
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in forecast_demand: {e}")
            from datetime import datetime as _dt
            return {
                "forecast": [{"date": _dt.now().strftime('%Y-%m-%d'), "predicted_demand": 0}],
                "summary": {"total_demand": 0, "avg_daily_demand": 0},
            }

    def predict_customer_churn(self, **kwargs):
        """تحليل فقدان العملاء"""
        try:
            query = """
                SELECT
                    c.id, c.name, c.phone,
                    COUNT(DISTINCT s.id) as total_orders,
                    MAX(s.sale_date) as last_order_date,
                    COALESCE(SUM(s.final_amount), 0) as total_spent
                FROM customers c
                LEFT JOIN sales s ON c.id = s.customer_id
                    AND s.status NOT IN ('cancelled', 'ملغية')
                GROUP BY c.id, c.name, c.phone
            """
            conn = self.db.get_connection()
            df = pd.read_sql_query(query, conn)

            if df.empty:
                return {"predictions": [], "summary": {"high_risk": 0, "medium_risk": 0, "total_analyzed": 0}}

            predictions = []
            high_risk = 0
            medium_risk = 0

            for _, row in df.iterrows():
                last_order = pd.to_datetime(row['last_order_date']) if pd.notna(row['last_order_date']) else None
                days_since = (pd.Timestamp.now() - last_order).days if last_order else 999

                # Simple churn scoring based on recency and frequency
                if days_since > 60 or (row['total_orders'] == 0):
                    risk = 'high'
                    high_risk += 1
                elif days_since > 30:
                    risk = 'medium'
                    medium_risk += 1
                else:
                    risk = 'low'

                predictions.append({
                    "customer_id": row['id'],
                    "customer_name": row['name'],
                    "phone": row['phone'],
                    "risk_level": risk,
                    "days_since_last_order": days_since,
                    "total_orders": int(row['total_orders']),
                    "total_spent": float(row['total_spent']),
                })

            predictions.sort(key=lambda x: (0 if x['risk_level'] == 'high' else (1 if x['risk_level'] == 'medium' else 2)))

            return {
                "predictions": predictions,
                "summary": {"high_risk": high_risk, "medium_risk": medium_risk, "total_analyzed": len(predictions)},
            }
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in predict_customer_churn: {e}")
            return {"predictions": [], "summary": {"high_risk": 0, "medium_risk": 0, "total_analyzed": 0}}

    def get_product_recommendations(self, **kwargs):
        """التوصيات الذكية للمنتجات"""
        try:
            # Find products that sell well together (co-purchased) using simple association
            query = """
                SELECT
                    si1.product_id as product_a,
                    si2.product_id as product_b,
                    p2.name as product_b_name,
                    p2.sku as product_b_sku,
                    p2.selling_price,
                    COUNT(*) as co_occurrence,
                    p2.current_stock
                FROM sale_items si1
                JOIN sale_items si2 ON si1.sale_id = si2.sale_id AND si1.product_id != si2.product_id
                JOIN products p2 ON p2.id = si2.product_id
                WHERE si1.product_id = ?
                GROUP BY si2.product_id
                ORDER BY co_occurrence DESC
                LIMIT 10
            """
            product_id = kwargs.get('product_id')
            if not product_id:
                # Return top trending products instead
                trend_query = """
                    SELECT p.id, p.name, p.sku, p.selling_price, p.current_stock,
                           SUM(si.quantity) as recent_qty
                    FROM products p
                    JOIN sale_items si ON p.id = si.product_id
                    JOIN sales s ON s.id = si.sale_id
                    WHERE s.sale_date >= DATE('now', '-30 days')
                      AND s.status NOT IN ('cancelled', 'ملغية')
                    GROUP BY p.id
                    ORDER BY recent_qty DESC
                    LIMIT 10
                """
                conn = self.db.get_connection()
                df = pd.read_sql_query(trend_query, conn)
                if df.empty:
                    return {"products": [], "recommendation_type": "trending"}
                products = df.to_dict('records')
                return {"products": products, "recommendation_type": "trending"}

            conn = self.db.get_connection()
            df = pd.read_sql_query(query, conn, params=(product_id,))

            if df.empty:
                return {"products": [], "recommendation_type": "co_purchase"}

            products = df.to_dict('records')
            return {"products": products, "recommendation_type": "co_purchase"}
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error in get_product_recommendations: {e}")
            return {"products": [], "recommendation_type": "error"}
