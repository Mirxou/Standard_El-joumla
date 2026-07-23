import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك التحليلات الذكية - AI Analytics Engine
محرك الذكاء الاصطناعي للتحليلات والرؤى التنبؤية
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


@dataclass
class SalesPrediction:
    """تنبؤ المبيعات"""

    product_id: int
    predicted_sales: float
    confidence_score: float
    prediction_date: datetime
    factors: Dict[str, Any]


@dataclass
class CustomerInsight:
    """رؤية عميل"""

    customer_id: int
    insight_type: str  # 'churn_risk', 'upsell_opportunity', 'loyalty_score'
    score: float
    description: str
    recommendations: List[str]
    generated_at: datetime


@dataclass
class ProductRecommendation:
    """توصية منتج"""

    customer_id: int
    recommended_products: List[Dict[str, Any]]
    reasoning: str
    confidence_score: float
    generated_at: datetime


class AIAnalyticsEngine:
    """محرك التحليلات الذكية المتقدم"""

    def __init__(self, db_manager: DatabaseManager):
        self.logger = setup_logger(__name__)
        from src.utils.db_utils import SafeDatabaseWrapper
        self.db = SafeDatabaseWrapper(db_manager, self.logger)
        self.config = ConfigManager()

        # نماذج التعلم الآلي
        self.sales_model = None
        self.customer_model = None
        self.scaler = StandardScaler()

        # معلمات التكوين
        self.prediction_horizon_days = self.config.get("ai.prediction_horizon_days", 30)
        self.min_training_samples = self.config.get("ai.min_training_samples", 100)
        self.model_update_frequency_hours = self.config.get("ai.model_update_frequency_hours", 24)

        # تحميل النماذج المدربة
        self._load_trained_models()

    def predict_sales(self, product_id: int, days_ahead: int = 30) -> SalesPrediction:
        """
        التنبؤ بالمبيعات لمنتج محدد

        Args:
            product_id: معرف المنتج
            days_ahead: عدد الأيام المستقبلية للتنبؤ

        Returns:
            كائن التنبؤ بالمبيعات
        """
        try:
            # جمع البيانات التاريخية
            historical_data = self._get_product_sales_history(product_id, days=90)

            if len(historical_data) < self.min_training_samples:
                # استخدام تنبؤ بسيط إذا لم تكن هناك بيانات كافية
                return self._simple_sales_prediction(product_id, days_ahead)

            # إعداد البيانات للتدريب
            X, y = self._prepare_sales_training_data(historical_data)

            # تدريب النموذج أو استخدام النموذج المحمل
            if self.sales_model is None:
                self.sales_model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.sales_model.fit(X, y)

            # إعداد البيانات للتنبؤ
            prediction_features = self._get_prediction_features(product_id, days_ahead)

            # التنبؤ
            predicted_sales = self.sales_model.predict(prediction_features.reshape(1, -1))[0]

            # حساب الثقة
            confidence_score = self._calculate_prediction_confidence(historical_data, predicted_sales)

            # تحديد العوامل المؤثرة
            factors = self._analyze_sales_factors(product_id, historical_data)

            return SalesPrediction(
                product_id=product_id,
                predicted_sales=float(predicted_sales),
                confidence_score=confidence_score,
                prediction_date=datetime.now() + timedelta(days=days_ahead),
                factors=factors,
            )

        except Exception as e:
            self.logger.error(f"Error predicting sales: {e}")
            return self._fallback_sales_prediction(product_id, days_ahead)

    def analyze_customer_behavior(self, customer_id: int) -> List[CustomerInsight]:
        """
        تحليل سلوك العميل وتوليد رؤى

        Args:
            customer_id: معرف العميل

        Returns:
            قائمة بالرؤى المتعلقة بالعميل
        """
        insights = []

        try:
            # جمع بيانات العميل
            customer_data = self._get_customer_behavior_data(customer_id)

            # تحليل خطر الخسارة
            churn_risk = self._analyze_churn_risk(customer_data)
            if churn_risk["score"] > 0.3:
                insights.append(
                    CustomerInsight(
                        customer_id=customer_id,
                        insight_type="churn_risk",
                        score=churn_risk["score"],
                        description=f"خطر خسارة العميل: {churn_risk['description']}",
                        recommendations=churn_risk["recommendations"],
                        generated_at=datetime.now(),
                    )
                )

            # تحليل فرص البيع الإضافي
            upsell_opportunities = self._analyze_upsell_opportunities(customer_data)
            if upsell_opportunities["score"] > 0.4:
                insights.append(
                    CustomerInsight(
                        customer_id=customer_id,
                        insight_type="upsell_opportunity",
                        score=upsell_opportunities["score"],
                        description=f"فرصة بيع إضافي: {upsell_opportunities['description']}",
                        recommendations=upsell_opportunities["recommendations"],
                        generated_at=datetime.now(),
                    )
                )

            # حساب درجة الولاء
            loyalty_score = self._calculate_loyalty_score(customer_data)
            insights.append(
                CustomerInsight(
                    customer_id=customer_id,
                    insight_type="loyalty_score",
                    score=loyalty_score["score"],
                    description=f"درجة الولاء: {loyalty_score['description']}",
                    recommendations=loyalty_score["recommendations"],
                    generated_at=datetime.now(),
                )
            )

        except Exception as e:
            self.logger.error(f"Error analyzing customer behavior: {e}")

        return insights

    def recommend_products(self, customer_id: int, limit: int = 5) -> ProductRecommendation:
        """
        توصية منتجات للعميل بناءً على سلوكه

        Args:
            customer_id: معرف العميل
            limit: عدد التوصيات المرغوبة

        Returns:
            كائن التوصية بالمنتجات
        """
        try:
            # جمع بيانات العميل والمنتجات
            customer_history = self._get_customer_purchase_history(customer_id)
            all_products = self._get_all_products()

            # حساب درجات التوصية
            recommendations = []

            for product in all_products:
                if product["id"] in [p["product_id"] for p in customer_history]:
                    continue  # لا نوصي بمنتجات تم شراؤها مؤخراً

                score = self._calculate_product_recommendation_score(customer_history, product, customer_id)

                if score > 0.3:  # حد أدنى للثقة
                    recommendations.append(
                        {
                            "product_id": product["id"],
                            "name": product["name"],
                            "score": score,
                            "reason": self._get_recommendation_reason(customer_history, product),
                        }
                    )

            # ترتيب وتحديد العدد المطلوب
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            top_recommendations = recommendations[:limit]

            # بناء المنطق
            if top_recommendations:
                reasoning = f"بناءً على مشترياتك السابقة، نوصي بالمنتجات التالية: {', '.join([r['name'] for r in top_recommendations[:3]])}"  # noqa: E501
            else:
                reasoning = "لا توجد توصيات محددة حالياً"

            confidence_score = (
                sum(r["score"] for r in top_recommendations) / len(top_recommendations) if top_recommendations else 0
            )

            return ProductRecommendation(
                customer_id=customer_id,
                recommended_products=top_recommendations,
                reasoning=reasoning,
                confidence_score=confidence_score,
                generated_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error generating product recommendations: {e}")
            return ProductRecommendation(
                customer_id=customer_id,
                recommended_products=[],
                reasoning="خطأ في توليد التوصيات",
                confidence_score=0,
                generated_at=datetime.now(),
            )

    def generate_business_insights(self) -> Dict[str, Any]:
        """
        توليد رؤى أعمال شاملة

        Returns:
            قاموس يحتوي على الرؤى المختلفة
        """
        insights = {
            "sales_trends": {},
            "customer_segments": {},
            "inventory_alerts": {},
            "pricing_opportunities": {},
            "generated_at": datetime.now().isoformat(),
        }

        try:
            # تحليل اتجاهات المبيعات
            insights["sales_trends"] = self._analyze_sales_trends()

            # تحليل شرائح العملاء
            insights["customer_segments"] = self._analyze_customer_segments()

            # تنبيهات المخزون
            insights["inventory_alerts"] = self._analyze_inventory_alerts()

            # فرص التسعير
            insights["pricing_opportunities"] = self._analyze_pricing_opportunities()

        except Exception as e:
            self.logger.error(f"Error generating business insights: {e}")

        return insights

    def _get_product_sales_history(self, product_id: int, days: int = 90) -> List[Dict[str, Any]]:
        """الحصول على تاريخ مبيعات المنتج"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT DATE(s.created_at) as sale_date, SUM(si.quantity) as quantity,
                       SUM(si.unit_price * si.quantity) as revenue
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? AND s.created_at >= ?
                GROUP BY DATE(s.created_at)
                ORDER BY sale_date
            """

            data = self.db.execute_query(query, (product_id, start_date), fetch_all=True)

            return [{"date": row["sale_date"], "quantity": row["quantity"], "revenue": float(row["revenue"])} for row in data]

        except Exception as e:
            self.logger.error(f"Error getting sales history: {e}")
            return []

    def _prepare_sales_training_data(self, historical_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """إعداد بيانات التدريب للتنبؤ بالمبيعات"""
        try:
            df = pd.DataFrame(historical_data)

            # إنشاء ميزات
            df["date"] = pd.to_datetime(df["date"])
            df["day_of_week"] = df["date"].dt.dayofweek
            df["month"] = df["date"].dt.month
            df["day_of_month"] = df["date"].dt.day
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

            # ميزات إضافية
            df["quantity_lag_1"] = df["quantity"].shift(1)
            df["quantity_lag_7"] = df["quantity"].shift(7)
            df["quantity_rolling_mean_7"] = df["quantity"].rolling(window=7).mean()

            # إزالة الصفوف التي تحتوي على NaN
            df = df.dropna()

            # تحديد الميزات والهدف
            features = [
                "day_of_week",
                "month",
                "day_of_month",
                "is_weekend",
                "quantity_lag_1",
                "quantity_lag_7",
                "quantity_rolling_mean_7",
            ]

            X = df[features].values
            y = df["quantity"].values

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return np.array([]), np.array([])

    def _get_prediction_features(self, product_id: int, days_ahead: int) -> np.ndarray:
        """الحصول على ميزات التنبؤ"""
        prediction_date = datetime.now() + timedelta(days=days_ahead)

        # ميزات أساسية
        features = [
            prediction_date.weekday(),  # day_of_week
            prediction_date.month,  # month
            prediction_date.day,  # day_of_month
            1 if prediction_date.weekday() >= 5 else 0,  # is_weekend
        ]

        # إضافة ميزات متأخرة (سنحتاج للبيانات الأخيرة)
        try:
            recent_sales = self._get_product_sales_history(product_id, days=7)
            if recent_sales:
                last_quantity = recent_sales[-1]["quantity"]
                week_ago_quantity = recent_sales[0]["quantity"] if len(recent_sales) > 1 else last_quantity

                features.extend(
                    [
                        last_quantity,  # quantity_lag_1
                        week_ago_quantity,  # quantity_lag_7
                        np.mean([s["quantity"] for s in recent_sales]),  # rolling_mean_7
                    ]
                )
            else:
                features.extend([0, 0, 0])  # قيم افتراضية

        except Exception as e:  # noqa: F841
            features.extend([0, 0, 0])

        return np.array(features)

    def _calculate_prediction_confidence(self, historical_data: List[Dict[str, Any]], prediction: float) -> float:
        """حساب ثقة التنبؤ"""
        if not historical_data:
            return 0.0

        quantities = [d["quantity"] for d in historical_data]
        mean_quantity = np.mean(quantities)
        std_quantity = np.std(quantities)

        if std_quantity == 0:
            return 0.5  # ثقة متوسطة إذا كانت البيانات ثابتة

        # حساب الثقة بناءً على الانحراف المعياري
        z_score = abs(prediction - mean_quantity) / std_quantity

        # تحويل z-score إلى نسبة ثقة
        confidence = max(0, min(1, 1 - (z_score / 3)))

        return confidence

    def _analyze_sales_factors(self, product_id: int, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل العوامل المؤثرة على المبيعات"""
        factors = {}

        try:
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])

            # تحليل تأثير يوم الأسبوع
            df["day_of_week"] = df["date"].dt.dayofweek
            weekday_avg = df.groupby("day_of_week")["quantity"].mean()

            best_day = weekday_avg.idxmax()
            worst_day = weekday_avg.idxmin()

            factors["best_sales_day"] = int(best_day)
            factors["worst_sales_day"] = int(worst_day)
            factors["day_variation"] = float((weekday_avg.max() - weekday_avg.min()) / weekday_avg.mean())

            # تحليل الاتجاه
            if len(df) > 7:
                recent_avg = df["quantity"].tail(7).mean()
                older_avg = df["quantity"].head(len(df) - 7).mean()

                if older_avg > 0:
                    trend = (recent_avg - older_avg) / older_avg
                    factors["sales_trend"] = float(trend)
                    factors["trend_direction"] = (
                        "increasing" if trend > 0.1 else "decreasing" if trend < -0.1 else "stable"
                    )

        except Exception as e:
            self.logger.error(f"Error analyzing sales factors: {e}")

        return factors

    def _simple_sales_prediction(self, product_id: int, days_ahead: int) -> SalesPrediction:
        """تنبؤ مبيعات بسيط عندما تكون البيانات محدودة"""
        try:
            # حساب متوسط المبيعات الأخيرة
            recent_sales = self._get_product_sales_history(product_id, days=30)
            avg_sales = np.mean([s["quantity"] for s in recent_sales]) if recent_sales else 0
            confidence_score = 0.3 if recent_sales else 0.0

            return SalesPrediction(
                product_id=product_id,
                predicted_sales=float(avg_sales),
                confidence_score=confidence_score,
                prediction_date=datetime.now() + timedelta(days=days_ahead),
                factors={"method": "simple_average", "data_points": len(recent_sales)},
            )

        except Exception as e:  # noqa: F841
            return SalesPrediction(
                product_id=product_id,
                predicted_sales=0,
                confidence_score=0,
                prediction_date=datetime.now() + timedelta(days=days_ahead),
                factors={"error": "no_data"},
            )

    def _fallback_sales_prediction(self, product_id: int, days_ahead: int) -> SalesPrediction:
        """تنبؤ احتياطي في حالة الخطأ"""
        return SalesPrediction(
            product_id=product_id,
            predicted_sales=0,
            confidence_score=0,
            prediction_date=datetime.now() + timedelta(days=days_ahead),
            factors={"method": "fallback", "reason": "error"},
        )

    def _get_customer_behavior_data(self, customer_id: int) -> Dict[str, Any]:
        """جمع بيانات سلوك العميل"""
        try:
            # إجمالي المشتريات
            total_purchases_query = """
                SELECT COUNT(*) as order_count, SUM(total_amount) as total_spent,
                       AVG(total_amount) as avg_order_value, MAX(created_at) as last_order_date
                FROM sales WHERE customer_id = ?
            """

            purchase_data = self.db.execute_query(total_purchases_query, (customer_id,), fetch_one=True)

            # فترة الخمول
            days_since_last_order = (
                (datetime.now() - purchase_data["last_order_date"]).days if purchase_data and purchase_data.get("last_order_date") else 999
            )

            # تنوع المنتجات المشتراة
            product_diversity_query = """
                SELECT COUNT(DISTINCT si.product_id) as unique_products
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE s.customer_id = ?
            """

            diversity_data = self.db.execute_query(product_diversity_query, (customer_id,), fetch_one=True)

            return {
                "order_count": purchase_data.get("order_count", 0) if purchase_data else 0,
                "total_spent": float(purchase_data.get("total_spent", 0) or 0) if purchase_data else 0,
                "avg_order_value": float(purchase_data.get("avg_order_value", 0) or 0) if purchase_data else 0,
                "days_since_last_order": days_since_last_order,
                "unique_products": diversity_data.get("unique_products", 0) if diversity_data else 0,
                "customer_id": customer_id,
            }

        except Exception as e:
            self.logger.error(f"Error getting customer behavior data: {e}")
            return {}

    def _analyze_churn_risk(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل خطر خسارة العميل"""
        risk_score = 0
        reasons = []
        recommendations = []

        # تحليل بناءً على فترة الخمول
        days_inactive = customer_data.get("days_since_last_order", 999)

        if days_inactive > 90:
            risk_score += 0.4
            reasons.append(f"غير نشط منذ {days_inactive} يوم")
            recommendations.append("إرسال عرض ترويجي لإعادة الجذب")
        elif days_inactive > 30:
            risk_score += 0.2
            reasons.append(f"غير نشط منذ {days_inactive} يوم")
            recommendations.append("إرسال تذكير بالعروض المتاحة")

        # تحليل بناءً على عدد الطلبات
        order_count = customer_data.get("order_count", 0)

        if order_count < 3:
            risk_score += 0.3
            reasons.append("عدد الطلبات قليل")
            recommendations.append("تقديم خصومات للطلب الأول")

        # تحليل بناءً على قيمة الطلب المتوسطة
        avg_order_value = customer_data.get("avg_order_value", 0)

        if avg_order_value < 50:
            risk_score += 0.1
            reasons.append("قيمة الطلب المتوسطة منخفضة")

        description = "; ".join(reasons) if reasons else "خطر خسارة منخفض"

        return {
            "score": min(1.0, risk_score),
            "description": description,
            "recommendations": recommendations,
        }

    def _analyze_upsell_opportunities(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل فرص البيع الإضافي"""
        opportunity_score = 0
        reasons = []
        recommendations = []

        # تحليل بناءً على قيمة الطلب المتوسطة
        avg_order_value = customer_data.get("avg_order_value", 0)

        if avg_order_value > 200:
            opportunity_score += 0.4
            reasons.append("قيمة الطلب المتوسطة عالية")
            recommendations.append("اقتراح منتجات مكملة أغلى")
        elif avg_order_value > 100:
            opportunity_score += 0.2
            reasons.append("قيمة الطلب المتوسطة متوسطة")
            recommendations.append("اقتراح ترقيات للمنتجات")

        # تحليل بناءً على تنوع المنتجات
        unique_products = customer_data.get("unique_products", 0)

        if unique_products < 5:
            opportunity_score += 0.3
            reasons.append("تنوع المنتجات المشتراة محدود")
            recommendations.append("اقتراح فئات منتجات جديدة")

        # تحليل بناءً على النشاط الأخير
        days_inactive = customer_data.get("days_since_last_order", 999)

        if days_inactive < 7:
            opportunity_score += 0.2
            reasons.append("العميل نشط مؤخراً")
            recommendations.append("اقتراح مشتريات متكررة")

        description = "; ".join(reasons) if reasons else "فرص بيع إضافي محدودة"

        return {
            "score": min(1.0, opportunity_score),
            "description": description,
            "recommendations": recommendations,
        }

    def _calculate_loyalty_score(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب درجة ولاء العميل"""
        loyalty_score = 0
        reasons = []
        recommendations = []

        # تحليل بناءً على عدد الطلبات
        order_count = customer_data.get("order_count", 0)

        if order_count > 50:
            loyalty_score += 0.4
            reasons.append("عدد كبير من الطلبات")
        elif order_count > 20:
            loyalty_score += 0.3
            reasons.append("عدد جيد من الطلبات")
        elif order_count > 10:
            loyalty_score += 0.2
            reasons.append("عدد مقبول من الطلبات")

        # تحليل بناءً على إجمالي المشتريات
        total_spent = customer_data.get("total_spent", 0)

        if total_spent > 10000:
            loyalty_score += 0.3
            reasons.append("إجمالي مشتريات عالي")
        elif total_spent > 5000:
            loyalty_score += 0.2
            reasons.append("إجمالي مشتريات جيد")
        elif total_spent > 1000:
            loyalty_score += 0.1
            reasons.append("إجمالي مشتريات مقبول")

        # تحليل بناءً على النشاط الأخير
        days_inactive = customer_data.get("days_since_last_order", 999)

        if days_inactive < 7:
            loyalty_score += 0.2
            reasons.append("نشط جداً")
        elif days_inactive < 30:
            loyalty_score += 0.1
            reasons.append("نشط")

        # تحديد المستوى والتوصيات
        if loyalty_score > 0.7:
            level = "ممتاز"
            recommendations.append("برنامج ولاء VIP")
        elif loyalty_score > 0.5:
            level = "جيد جداً"
            recommendations.append("خصومات إضافية")
        elif loyalty_score > 0.3:
            level = "جيد"
            recommendations.append("عروض خاصة")
        else:
            level = "يحتاج تحسين"
            recommendations.append("حملات جذب")

        description = f"مستوى الولاء: {level} ({loyalty_score:.1%})"

        return {
            "score": loyalty_score,
            "description": description,
            "recommendations": recommendations,
        }

    def _get_customer_purchase_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """الحصول على تاريخ مشتريات العميل"""
        try:
            query = """
                SELECT si.product_id, p.name, SUM(si.quantity) as total_quantity,
                       AVG(si.unit_price) as avg_price, MAX(s.created_at) as last_purchase
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                JOIN products p ON si.product_id = p.id
                WHERE s.customer_id = ?
                GROUP BY si.product_id, p.name
                ORDER BY total_quantity DESC
            """

            data = self.db.execute_query(query, (customer_id,), fetch_all=True)

            return [
                {
                    "product_id": row["product_id"],
                    "product_name": row["name"],
                    "total_quantity": row["total_quantity"],
                    "avg_price": float(row["avg_price"]),
                    "last_purchase": row["last_purchase"],
                }
                for row in data
            ]

        except Exception as e:
            self.logger.error(f"Error getting customer purchase history: {e}")
            return []

    def _get_all_products(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المنتجات"""
        try:
            query = "SELECT id, name, category_id FROM products WHERE is_active = 1"
            data = self.db.execute_query(query, fetch_all=True)

            return [{"id": row["id"], "name": row["name"], "category_id": row["category_id"]} for row in data]

        except Exception as e:
            self.logger.error(f"Error getting all products: {e}")
            return []

    def _calculate_product_recommendation_score(
        self,
        customer_history: List[Dict[str, Any]],
        product: Dict[str, Any],
        customer_id: int,
    ) -> float:
        """حساب درجة توصية المنتج"""
        score = 0

        try:
            # المنتجات المشتراة مؤخراً (للتوصية بالمنتجات المكملة)
            purchased_categories = set()
            for purchase in customer_history:
                # افتراض أن لدينا معلومات الفئة
                purchased_categories.add(f"category_{purchase.get('category_id', 0)}")

            # المنتجات من نفس الفئة تحصل على درجة أعلى
            if f"category_{product.get('category_id', 0)}" in purchased_categories:
                score += 0.3

            # المنتجات الشائعة تحصل على درجة أساسية
            score += 0.2

            # إضافة عنصر عشوائي صغير للتنويع
            score += np.random.uniform(0, 0.1)

        except Exception as e:
            self.logger.error(f"Error calculating recommendation score: {e}")
            score = 0.1

        return min(1.0, score)

    def _get_recommendation_reason(self, customer_history: List[Dict[str, Any]], product: Dict[str, Any]) -> str:
        """الحصول على سبب التوصية"""
        reasons = []

        purchased_product_names = [p["product_name"] for p in customer_history]

        if purchased_product_names:
            reasons.append(f"بناءً على مشترياتك السابقة: {', '.join(purchased_product_names[:2])}")

        reasons.append("منتج شائع بين عملائنا")

        return "; ".join(reasons)

    def _analyze_sales_trends(self) -> Dict[str, Any]:
        """تحليل اتجاهات المبيعات"""
        trends = {}

        try:
            # مقارنة هذا الشهر مع الشهر الماضي
            current_month = datetime.now().replace(day=1)
            last_month = (current_month - timedelta(days=1)).replace(day=1)

            current_sales_query = """
                SELECT SUM(total_amount) FROM sales
                WHERE created_at >= ? AND created_at < ?
            """

            current_sales = self.db.execute_query(
                current_sales_query,
                (
                    current_month,
                    (
                        current_month.replace(month=current_month.month + 1)
                        if current_month.month < 12
                        else current_month.replace(year=current_month.year + 1, month=1)
                    ),
                ),
                fetch_one=True,
            )

            last_sales = self.db.execute_query(current_sales_query, (last_month, current_month), fetch_one=True)

            current_total = float(current_sales.get("SUM(total_amount)") or 0) if current_sales else 0
            last_total = float(last_sales.get("SUM(total_amount)") or 0) if last_sales else 0

            if last_total > 0:
                growth_rate = (current_total - last_total) / last_total
                trends["monthly_growth"] = growth_rate
                trends["growth_description"] = (
                    f"{'زيادة' if growth_rate > 0 else 'انخفاض'} بنسبة {abs(growth_rate):.1%}"
                )

            trends["current_month_sales"] = current_total
            trends["last_month_sales"] = last_total

        except Exception as e:
            self.logger.error(f"Error analyzing sales trends: {e}")

        return trends

    def _analyze_customer_segments(self) -> Dict[str, Any]:
        """تحليل شرائح العملاء"""
        segments = {}

        try:
            # تحليل توزيع العملاء حسب القيمة
            segment_query = """
                SELECT
                    CASE
                        WHEN total_spent > 10000 THEN 'VIP'
                        WHEN total_spent > 1000 THEN 'High Value'
                        WHEN total_spent > 100 THEN 'Regular'
                        ELSE 'Low Value'
                    END as segment,
                    COUNT(*) as customer_count,
                    AVG(total_spent) as avg_spent
                FROM (
                    SELECT customer_id, SUM(total_amount) as total_spent
                    FROM sales
                    GROUP BY customer_id
                ) customer_totals
                GROUP BY segment
            """

            data = self.db.execute_query(segment_query, fetch_all=True)

            for row in data:
                segment_name = row["segment"]
                segments[segment_name] = {
                    "count": row["customer_count"],
                    "avg_spent": float(row["avg_spent"] or 0),
                }

        except Exception as e:
            self.logger.error(f"Error analyzing customer segments: {e}")

        return segments

    def _analyze_inventory_alerts(self) -> Dict[str, Any]:
        """تحليل تنبيهات المخزون"""
        alerts = {}

        try:
            # منتجات منخفضة المخزون
            low_stock_query = """
                SELECT id, name, current_stock, min_stock
                FROM products
                WHERE current_stock <= min_stock * 1.5 AND is_active = 1
                ORDER BY current_stock / NULLIF(min_stock, 0) ASC
            """

            low_stock_products = self.db.execute_query(low_stock_query, fetch_all=True)

            alerts["low_stock_products"] = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "current_stock": row["current_stock"],
                    "min_stock": row["min_stock"],
                    "urgency": "high" if row["current_stock"] <= row["min_stock"] else "medium",
                }
                for row in low_stock_products
            ]

            # منتجات زائدة المخزون
            excess_stock_query = """
                SELECT id, name, current_stock, min_stock
                FROM products
                WHERE current_stock > min_stock * 3 AND is_active = 1
                ORDER BY current_stock DESC
            """

            excess_stock_products = self.db.execute_query(excess_stock_query, fetch_all=True)

            alerts["excess_stock_products"] = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "current_stock": row["current_stock"],
                    "min_stock": row["min_stock"],
                }
                for row in excess_stock_products
            ]

        except Exception as e:
            self.logger.error(f"Error analyzing inventory alerts: {e}")

        return alerts

    def _analyze_pricing_opportunities(self) -> Dict[str, Any]:
        """تحليل فرص التسعير"""
        opportunities = {}

        try:
            # منتجات يمكن زيادة أسعارها
            price_increase_opportunities = """
                SELECT p.id, p.name, p.selling_price,
                       AVG(si.unit_price) as avg_sold_price,
                       COUNT(si.id) as sales_count
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                WHERE p.is_active = 1
                GROUP BY p.id, p.name, p.selling_price
                HAVING AVG(si.unit_price) < p.selling_price * 0.9 AND COUNT(si.id) > 10
            """

            data = self.db.execute_query(price_increase_opportunities, fetch_all=True)

            opportunities["price_increase_candidates"] = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "current_price": float(row["selling_price"]),
                    "avg_sold_price": float(row["avg_sold_price"] or 0),
                    "sales_count": row["sales_count"],
                    "potential_increase": float(row["selling_price"] - (row["avg_sold_price"] or 0)),
                }
                for row in data
            ]

        except Exception as e:
            self.logger.error(f"Error analyzing pricing opportunities: {e}")

        return opportunities

    def _load_trained_models(self):
        """تحميل النماذج المدربة المحفوظة"""
        try:
            # في التطبيق الحقيقي، سنحمل النماذج من الملفات
            # للآن، سنتركها None وسيتم تدريبها عند الحاجة
            pass
        except Exception as e:
            self.logger.error(f"Error loading trained models: {e}")

    def update_models(self):
        """تحديث النماذج بناءً على البيانات الجديدة"""
        try:
            # إعادة تدريب النماذج باستخدام البيانات الأحدث
            self.logger.info("Updating AI models with latest data...")

            # تحديث نموذج المبيعات
            all_products = self._get_all_products()
            for product in all_products[:10]:  # تدريب على أول 10 منتجات للاختبار
                sales_data = self._get_product_sales_history(product["id"], days=90)
                if len(sales_data) >= self.min_training_samples:
                    X, y = self._prepare_sales_training_data(sales_data)
                    if len(X) > 0:
                        self.sales_model = RandomForestRegressor(n_estimators=100, random_state=42)
                        self.sales_model.fit(X, y)

            self.logger.info("AI models updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating models: {e}")
