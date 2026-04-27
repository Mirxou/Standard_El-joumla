#!/usr/bin/env python3
"""
محرك التحليلات المتقدمة - Advanced Analytics Engine
نظام تحليلات ذكي يقدم رؤى عميقة عن البيانات
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Any, Optional, Tuple
import statistics
import math
from collections import defaultdict, Counter


class AdvancedAnalyticsEngine:
    """محرك التحليلات المتقدمة"""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.analytics_cache = {}
        self.insights_history = []

    def analyze_business_performance(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """تحليل أداء الأعمال الشامل"""
        context = context or {}
        start_date = context.get("start_date")
        end_date = context.get("end_date")

        sales_analysis = self.analyze_sales_performance(start_date, end_date)
        customer_analysis = self.analyze_customer_behavior()

        return {
            "overall_performance_score": random.uniform(0.6, 0.95),
            "total_sales": sales_analysis["summary"]["total_sales"],
            "sales_analysis": sales_analysis,
            "customer_analysis": customer_analysis,
            "timestamp": datetime.now().isoformat()
        }

    def analyze_sales_performance(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:

        """تحليل أداء المبيعات المتقدم"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # محاكاة بيانات المبيعات
        sales_data = self._get_sales_data(start_date, end_date)

        analysis = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_sales": sum(sale["amount"] for sale in sales_data),
                "total_transactions": len(sales_data),
                "average_transaction": statistics.mean([sale["amount"] for sale in sales_data]) if sales_data else 0,
                "median_transaction": statistics.median([sale["amount"] for sale in sales_data]) if sales_data else 0
            },
            "trends": self._analyze_trends(sales_data),
            "segmentation": self._customer_segmentation(sales_data),
            "forecasting": self._sales_forecasting(sales_data),
            "insights": self._generate_insights(sales_data),
            "recommendations": self._generate_recommendations(sales_data)
        }

        return analysis

    def analyze_customer_behavior(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """تحليل سلوك العملاء"""
        # محاكاة بيانات العملاء
        customers_data = self._get_customers_data(customer_id)

        analysis = {
            "customer_analysis": {},
            "behavior_patterns": {},
            "lifetime_value": {},
            "churn_risk": {},
            "personalization": {}
        }

        if customer_id:
            customer_data = next((c for c in customers_data if c["id"] == customer_id), None)
            if customer_data:
                analysis["customer_analysis"] = self._analyze_single_customer(customer_data)
        else:
            analysis["behavior_patterns"] = self._analyze_behavior_patterns(customers_data)
            analysis["lifetime_value"] = self._calculate_lifetime_value(customers_data)

        return analysis

    def detect_anomalies(self, data_type: str = "sales", threshold: float = 2.0) -> Dict[str, Any]:
        """كشف الشذوذ في البيانات"""
        if data_type == "sales":
            data = self._get_sales_data()
        elif data_type == "inventory":
            data = self._get_inventory_data()
        else:
            return {"error": "نوع البيانات غير مدعوم"}

        anomalies = self._statistical_anomaly_detection(data, threshold)

        return {
            "data_type": data_type,
            "total_records": len(data),
            "anomalies_detected": len(anomalies),
            "anomaly_percentage": (len(anomalies) / len(data)) * 100 if data else 0,
            "anomalies": anomalies,
            "severity_levels": self._categorize_anomalies(anomalies),
            "recommendations": self._anomaly_recommendations(anomalies, data_type)
        }

    def generate_predictive_insights(self, prediction_type: str) -> Dict[str, Any]:
        """توليد رؤى تنبؤية"""
        if prediction_type == "sales":
            return self._predict_sales_trends()
        elif prediction_type == "inventory":
            return self._predict_inventory_needs()
        elif prediction_type == "customers":
            return self._predict_customer_behavior()
        else:
            return {"error": "نوع التنبؤ غير مدعوم"}

    def _get_sales_data(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """الحصول على بيانات المبيعات"""
        # محاكاة بيانات المبيعات
        import random
        days = 30 if not start_date else (end_date - start_date).days

        sales = []
        for i in range(days):
            date = (start_date or (datetime.now() - timedelta(days=30))) + timedelta(days=i)
            daily_sales = random.randint(5, 20)  # عدد الفواتير يومياً

            for j in range(daily_sales):
                sale = {
                    "id": f"SALE_{i}_{j}",
                    "date": date.isoformat(),
                    "amount": random.uniform(50, 500),
                    "customer_id": f"CUST_{random.randint(1, 100)}",
                    "items": random.randint(1, 10),
                    "payment_method": random.choice(["cash", "card", "transfer"]),
                    "category": random.choice(["electronics", "clothing", "food", "other"])
                }
                sales.append(sale)

        return sales

    def _get_customers_data(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """الحصول على بيانات العملاء"""
        # محاكاة بيانات العملاء
        customers = []
        for i in range(1, 101):  # 100 عميل
            customer = {
                "id": f"CUST_{i}",
                "name": f"Customer {i}",
                "total_purchases": random.randint(1, 50),
                "total_spent": random.uniform(500, 10000),
                "last_purchase": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                "preferred_category": random.choice(["electronics", "clothing", "food", "other"]),
                "loyalty_tier": random.choice(["bronze", "silver", "gold", "platinum"])
            }
            customers.append(customer)

        if customer_id:
            return [c for c in customers if c["id"] == customer_id]

        return customers

    def _get_inventory_data(self) -> List[Dict[str, Any]]:
        """الحصول على بيانات المخزون"""
        # محاكاة بيانات المخزون
        products = ["Product_A", "Product_B", "Product_C", "Product_D", "Product_E"]
        inventory = []

        for product in products:
            for i in range(30):  # 30 يوم
                date = datetime.now() - timedelta(days=i)
                record = {
                    "product": product,
                    "date": date.isoformat(),
                    "stock_level": random.randint(0, 100),
                    "sales_velocity": random.uniform(0.5, 5.0),
                    "reorder_point": 20
                }
                inventory.append(record)

        return inventory

    def _analyze_trends(self, sales_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل الاتجاهات"""
        if not sales_data:
            return {"error": "لا توجد بيانات كافية"}

        # تجميع المبيعات يومياً
        daily_sales = defaultdict(float)
        for sale in sales_data:
            date_value = sale.get("date")
            try:
                if isinstance(date_value, str):
                    date = datetime.fromisoformat(date_value).date()
                elif isinstance(date_value, datetime):
                    date = date_value.date()
                else:
                    date = datetime.now().date()
            except Exception:
                try:
                    date = datetime.strptime(str(date_value), "%Y-%m-%d").date()
                except Exception:
                    date = datetime.now().date()
            daily_sales[date] += sale["amount"]

        # حساب المتوسطات والتقلبات
        amounts = list(daily_sales.values())
        trend_analysis = {
            "daily_average": statistics.mean(amounts) if amounts else 0,
            "daily_median": statistics.median(amounts) if amounts else 0,
            "volatility": statistics.stdev(amounts) if len(amounts) > 1 else 0,
            "growth_rate": self._calculate_growth_rate(list(daily_sales.values())),
            "peak_days": sorted(daily_sales.items(), key=lambda x: x[1], reverse=True)[:5],
            "low_days": sorted(daily_sales.items(), key=lambda x: x[1])[:5]
        }

        return trend_analysis

    def _calculate_growth_rate(self, values: List[float]) -> float:
        """حساب معدل النمو"""
        if len(values) < 2:
            return 0.0

        first_half = statistics.mean(values[:len(values)//2])
        second_half = statistics.mean(values[len(values)//2:])

        if first_half == 0:
            return float('inf') if second_half > 0 else 0.0

        return ((second_half - first_half) / first_half) * 100

    def _customer_segmentation(self, sales_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تقسيم العملاء"""
        customer_spending = defaultdict(float)
        customer_frequency = defaultdict(int)

        # استخدم معرّف عميل افتراضي إذا غاب في بيانات المبيعات
        anon_counter = 0

        for sale in sales_data:
            customer_id = sale.get("customer_id")
            if not customer_id:
                customer_id = f"ANON_{anon_counter}"
                anon_counter += 1
            amount = sale.get("amount", 0.0)
            customer_spending[customer_id] += amount
            customer_frequency[customer_id] += 1

        # تصنيف العملاء
        segments = {
            "high_value": [],
            "regular": [],
            "occasional": [],
            "new": []
        }

        for customer_id, total_spent in customer_spending.items():
            frequency = customer_frequency[customer_id]

            if total_spent > 2000 and frequency > 10:
                segments["high_value"].append({"id": customer_id, "spent": total_spent, "frequency": frequency})
            elif total_spent > 500 and frequency > 3:
                segments["regular"].append({"id": customer_id, "spent": total_spent, "frequency": frequency})
            elif total_spent > 100:
                segments["occasional"].append({"id": customer_id, "spent": total_spent, "frequency": frequency})
            else:
                segments["new"].append({"id": customer_id, "spent": total_spent, "frequency": frequency})

        return segments

    def _sales_forecasting(self, sales_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """توقع المبيعات"""
        # نموذج بسيط للتوقع
        daily_sales = defaultdict(float)
        for sale in sales_data:
            date_value = sale.get("date")
            if isinstance(date_value, str):
                date = datetime.fromisoformat(date_value).date()
            elif isinstance(date_value, datetime):
                date = date_value.date()
            else:
                date = datetime.now().date()
            daily_sales[date] += sale["amount"]

        values = list(daily_sales.values())
        if len(values) < 7:
            return {"error": "بيانات غير كافية للتوقع"}

        # حساب المتوسط المرجح
        recent_avg = statistics.mean(values[-7:])  # آخر أسبوع
        overall_avg = statistics.mean(values)

        # توقع بسيط
        forecast = {
            "next_week": recent_avg * 1.05,  # 5% نمو متوقع
            "next_month": recent_avg * 30 * 1.08,  # 8% نمو شهري
            "confidence": 0.75,
            "method": "weighted_average",
            "factors": ["seasonal_trend", "recent_performance", "market_conditions"]
        }

        return forecast

    def _generate_insights(self, sales_data: List[Dict[str, Any]]) -> List[str]:
        """توليد الرؤى"""
        insights = []

        if not sales_data:
            return ["لا توجد بيانات كافية لتوليد رؤى"]

        # رؤى أساسية
        total_sales = sum(s["amount"] for s in sales_data)
        avg_transaction = total_sales / len(sales_data)

        insights.append(f"إجمالي المبيعات: {total_sales:.2f} ريال")
        insights.append(f"متوسط قيمة المعاملة: {avg_transaction:.2f} ريال")

        # تحليل الفئات
        category_sales = defaultdict(float)
        for sale in sales_data:
            category_sales[sale.get("category", "other")] += sale["amount"]

        top_category = max(category_sales.items(), key=lambda x: x[1])
        insights.append(f"الفئة الأكثر مبيعاً: {top_category[0]} بقيمة {top_category[1]:.2f} ريال")

        # تحليل الاتجاهات
        daily_totals = defaultdict(float)
        for sale in sales_data:
            date_value = sale.get("date")
            if isinstance(date_value, str):
                date = datetime.fromisoformat(date_value).date()
            elif isinstance(date_value, datetime):
                date = date_value.date()
            else:
                date = datetime.now().date()
            daily_totals[date] += sale["amount"]

        values = list(daily_totals.values())
        if len(values) > 1:
            growth = self._calculate_growth_rate(values)
            if growth > 10:
                insights.append(f"نمو إيجابي في المبيعات بنسبة {growth:.1f}%")
            elif growth < -10:
                insights.append(f"انخفاض في المبيعات بنسبة {abs(growth):.1f}%")

        return insights

    def _generate_recommendations(self, sales_data: List[Dict[str, Any]]) -> List[str]:
        """توليد التوصيات"""
        recommendations = []

        if not sales_data:
            return ["جمع المزيد من البيانات للحصول على توصيات دقيقة"]

        # توصيات بناءً على التحليل
        total_sales = sum(s["amount"] for s in sales_data)

        if total_sales < 10000:
            recommendations.append("زيادة التركيز على التسويق لرفع المبيعات")

        # تحليل الفئات
        category_sales = defaultdict(float)
        for sale in sales_data:
            category_sales[sale.get("category", "other")] += sale["amount"]

        top_category = max(category_sales.items(), key=lambda x: x[1])
        recommendations.append(f"التركيز على فئة {top_category[0]} لزيادة المبيعات")

        # توصيات عامة
        recommendations.extend([
            "تحسين خدمة العملاء لزيادة الولاء",
            "تنويع طرق الدفع المتاحة",
            "تطوير برامج الولاء للعملاء",
            "مراقبة المخزون بانتظام"
        ])

        return recommendations

    def _analyze_single_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل عميل واحد"""
        return {
            "customer_id": customer_data["id"],
            "spending_pattern": "regular" if customer_data["total_purchases"] > 10 else "occasional",
            "loyalty_score": min(customer_data["total_purchases"] / 50 * 100, 100),
            "next_purchase_prediction": (datetime.now() + timedelta(days=30)).isoformat(),
            "recommended_products": [customer_data["preferred_category"]],
            "risk_level": "low" if customer_data["total_spent"] > 1000 else "medium"
        }

    def _analyze_behavior_patterns(self, customers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل أنماط السلوك"""
        patterns = {
            "preferred_payment_methods": Counter(),
            "purchase_frequency": defaultdict(int),
            "spending_ranges": {"low": 0, "medium": 0, "high": 0}
        }

        for customer in customers_data:
            # تصنيف الإنفاق
            spent = customer["total_spent"]
            if spent < 1000:
                patterns["spending_ranges"]["low"] += 1
            elif spent < 5000:
                patterns["spending_ranges"]["medium"] += 1
            else:
                patterns["spending_ranges"]["high"] += 1

            # تكرار الشراء
            freq = customer["total_purchases"]
            if freq < 5:
                patterns["purchase_frequency"]["rare"] += 1
            elif freq < 15:
                patterns["purchase_frequency"]["regular"] += 1
            else:
                patterns["purchase_frequency"]["frequent"] += 1

        return patterns

    def _calculate_lifetime_value(self, customers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """حساب قيمة العمر الزمني للعملاء"""
        total_customers = len(customers_data)
        total_revenue = sum(c["total_spent"] for c in customers_data)
        avg_lifetime_value = total_revenue / total_customers if total_customers > 0 else 0

        return {
            "total_customers": total_customers,
            "total_revenue": total_revenue,
            "average_lifetime_value": avg_lifetime_value,
            "segments": {
                "high_value": len([c for c in customers_data if c["total_spent"] > 5000]),
                "medium_value": len([c for c in customers_data if 1000 <= c["total_spent"] <= 5000]),
                "low_value": len([c for c in customers_data if c["total_spent"] < 1000])
            }
        }

    def _statistical_anomaly_detection(self, data: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
        """كشف الشذوذ الإحصائي"""
        if not data:
            return []

        # استخراج القيم الرقمية
        values = []
        for item in data:
            if "amount" in item:
                values.append(item["amount"])
            elif "stock_level" in item:
                values.append(item["stock_level"])
            elif "sales_velocity" in item:
                values.append(item["sales_velocity"])

        if not values:
            return []

        # حساب المتوسط والانحراف المعياري
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        if stdev == 0:
            return []

        # تحديد الشذوذ
        anomalies = []
        for i, item in enumerate(data):
            value = values[i]
            z_score = abs(value - mean) / stdev if stdev > 0 else 0

            if z_score > threshold:
                anomaly = {
                    "record": item,
                    "value": value,
                    "z_score": z_score,
                    "deviation": value - mean,
                    "severity": "high" if z_score > 3 else "medium"
                }
                anomalies.append(anomaly)

        return anomalies

    def _categorize_anomalies(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """تصنيف الشذوذ"""
        categories = {"low": 0, "medium": 0, "high": 0}

        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            categories[severity] += 1

        return categories

    def _anomaly_recommendations(self, anomalies: List[Dict[str, Any]], data_type: str) -> List[str]:
        """توصيات للتعامل مع الشذوذ"""
        recommendations = []

        if not anomalies:
            return ["لا توجد شذوذ كبير في البيانات"]

        high_severity = len([a for a in anomalies if a.get("severity") == "high"])

        if data_type == "sales":
            if high_severity > 0:
                recommendations.append("فحص المعاملات ذات القيم الاستثنائية للتأكد من صحتها")
            recommendations.append("مراجعة سياسات التسعير والخصومات")

        elif data_type == "inventory":
            recommendations.append("فحص مستويات المخزون الاستثنائية")
            recommendations.append("مراجعة نظام إدارة المخزون")

        recommendations.append("إعداد تنبيهات تلقائية للشذوذ المستقبلي")

        return recommendations

    def _predict_sales_trends(self) -> Dict[str, Any]:
        """توقع اتجاهات المبيعات"""
        return {
            "short_term": {
                "prediction": "استمرار النمو بنسبة 8-12%",
                "confidence": 0.8,
                "timeframe": "الأسابيع الـ3 القادمة"
            },
            "long_term": {
                "prediction": "نمو مستقر بنسبة 15-20%",
                "confidence": 0.6,
                "timeframe": "الأشهر الـ6 القادمة"
            },
            "seasonal_factors": ["عيد الفطر", "العودة للمدارس", "الأعياد"],
            "risk_factors": ["تقلبات اقتصادية", "منافسة", "تغييرات في الطلب"]
        }

    def _predict_inventory_needs(self) -> Dict[str, Any]:
        """توقع احتياجات المخزون"""
        return {
            "recommended_stock_levels": {
                "Product_A": {"current": 45, "recommended": 60, "urgency": "high"},
                "Product_B": {"current": 30, "recommended": 40, "urgency": "medium"},
                "Product_C": {"current": 80, "recommended": 70, "urgency": "low"}
            },
            "reorder_schedule": {
                "next_week": ["Product_A", "Product_D"],
                "next_month": ["Product_B", "Product_E"]
            },
            "optimization_opportunities": [
                "تقليل المخزون الزائد لـ Product_C",
                "زيادة مخزون Product_A لتلبية الطلب"
            ]
        }

    def _predict_customer_behavior(self) -> Dict[str, Any]:
        """توقع سلوك العملاء"""
        return {
            "churn_prediction": {
                "at_risk_customers": 15,
                "retention_rate": 85,
                "recommended_actions": ["برامج ولاء", "خصومات خاصة", "تواصل منتظم"]
            },
            "purchase_predictions": {
                "expected_new_customers": 25,
                "repeat_purchase_rate": 65,
                "average_order_value": 175.50
            },
            "segment_evolution": {
                "high_value_growth": "+5%",
                "medium_value_stability": "0%",
                "low_value_churn": "-3%"
            }
        }
