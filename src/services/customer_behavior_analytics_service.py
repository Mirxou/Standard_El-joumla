import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة تحليل سلوك العملاء - Customer Behavior Analytics Service
خدمة متخصصة في تحليل سلوك العملاء وتوقع احتياجاتهم
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import networkx as nx
from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.services.ai_analytics_engine import AIAnalyticsEngine
from src.utils.logger import setup_logger


@dataclass
class CustomerSegment:
    """شريحة عميل"""

    segment_id: str
    segment_name: str
    customer_count: int
    characteristics: Dict[str, Any]
    average_metrics: Dict[str, float]
    recommended_actions: List[str]
    created_at: datetime


@dataclass
class CustomerJourney:
    """رحلة العميل"""

    customer_id: int
    journey_stages: List[Dict[str, Any]]
    current_stage: str
    next_predicted_stage: str
    journey_score: float
    bottlenecks: List[str]
    generated_at: datetime


@dataclass
class ChurnPrediction:
    """تنبؤ بالخسارة"""

    customer_id: int
    churn_probability: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    predicted_churn_date: Optional[datetime]
    risk_factors: List[str]
    retention_recommendations: List[str]
    confidence_score: float
    generated_at: datetime


@dataclass
class CustomerLifetimeValue:
    """قيمة عمر العميل"""

    customer_id: int
    clv_value: float
    clv_category: str  # 'low', 'medium', 'high', 'vip'
    predicted_lifetime_months: int
    monthly_revenue: float
    retention_probability: float
    growth_potential: float
    calculated_at: datetime


class CustomerBehaviorAnalyticsService:
    """خدمة تحليل سلوك العملاء المتقدمة"""

    def __init__(self, db_manager: DatabaseManager, ai_engine: AIAnalyticsEngine):
        self.logger = setup_logger(__name__)
        from src.utils.db_utils import SafeDatabaseWrapper
        self.db = SafeDatabaseWrapper(db_manager, self.logger)
        self.ai_engine = ai_engine
        self.config = ConfigManager()

        # نماذج التعلم الآلي
        self.segmentation_model = None
        self.churn_model = None
        self.clv_model = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)

        # معلمات التكوين
        self.min_customers_for_segmentation = self.config.get("analytics.min_customers_segmentation", 50)
        self.churn_prediction_window_days = self.config.get("analytics.churn_window_days", 90)
        self.customer_journey_stages = self.config.get(
            "analytics.journey_stages",
            ["awareness", "consideration", "purchase", "retention", "advocacy"],
        )

        # تحميل النماذج المدربة
        self._load_analytics_models()

    def segment_customers(self, n_clusters: int = 4) -> List[CustomerSegment]:
        """
        تقسيم العملاء إلى شرائح

        Args:
            n_clusters: عدد الشرائح المرغوبة

        Returns:
            قائمة بشرائح العملاء
        """
        try:
            # جمع بيانات العملاء
            customer_data = self._get_customer_segmentation_data()

            if len(customer_data) < self.min_customers_for_segmentation:
                return [self._create_default_segment(customer_data)]

            # إعداد البيانات للتجميع
            X = self._prepare_segmentation_features(customer_data)

            # تطبيق PCA لتقليل الأبعاد
            X_pca = self.pca.fit_transform(X)

            # تدريب نموذج التجميع
            if self.segmentation_model is None:
                self.segmentation_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

            clusters = self.segmentation_model.fit_predict(X_pca)

            # تحليل الشرائح
            segments = []
            for i in range(n_clusters):
                segment_customers = [customer_data[j] for j in range(len(customer_data)) if clusters[j] == i]

                if segment_customers:
                    segment = self._analyze_customer_segment(i, segment_customers)
                    segments.append(segment)

            return segments

        except Exception as e:
            self.logger.error(f"Error segmenting customers: {e}", exc_info=True)
            return []

    def analyze_customer_journey(self, customer_id: int) -> CustomerJourney:
        """
        تحليل رحلة العميل

        Args:
            customer_id: معرف العميل

        Returns:
            كائن رحلة العميل
        """
        try:
            # جمع تاريخ تفاعلات العميل
            journey_data = self._get_customer_journey_data(customer_id)

            # تحديد مراحل الرحلة
            journey_stages = self._identify_journey_stages(journey_data)

            # تحديد المرحلة الحالية
            current_stage = self._determine_current_stage(journey_stages)

            # التنبؤ بالمرحلة التالية
            next_stage = self._predict_next_stage(journey_stages, current_stage)

            # حساب درجة الرحلة
            journey_score = self._calculate_journey_score(journey_stages)

            # تحديد العقبات
            bottlenecks = self._identify_journey_bottlenecks(journey_stages)

            return CustomerJourney(
                customer_id=customer_id,
                journey_stages=journey_stages,
                current_stage=current_stage,
                next_predicted_stage=next_stage,
                journey_score=journey_score,
                bottlenecks=bottlenecks,
                generated_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing customer journey: {e}", exc_info=True)
            return CustomerJourney(
                customer_id=customer_id,
                journey_stages=[],
                current_stage="unknown",
                next_predicted_stage="unknown",
                journey_score=0,
                bottlenecks=[],
                generated_at=datetime.now(),
            )

    def predict_churn(self, customer_id: int) -> ChurnPrediction:
        """
        التنبؤ بخطر خسارة العميل

        Args:
            customer_id: معرف العميل

        Returns:
            كائن تنبؤ الخسارة
        """
        try:
            # جمع بيانات العميل
            customer_features = self._get_customer_churn_features(customer_id)

            # حساب احتمالية الخسارة
            churn_probability = self._calculate_churn_probability(customer_features)

            # تحديد مستوى الخطر
            risk_level = self._determine_risk_level(churn_probability)

            # التنبؤ بتاريخ الخسارة المحتمل
            predicted_churn_date = self._predict_churn_date(customer_features, churn_probability)

            # تحديد عوامل الخطر
            risk_factors = self._identify_risk_factors(customer_features)

            # توصيات الاحتفاظ
            retention_recommendations = self._generate_retention_recommendations(risk_factors, risk_level)

            # حساب درجة الثقة
            confidence_score = self._calculate_prediction_confidence(customer_features)

            return ChurnPrediction(
                customer_id=customer_id,
                churn_probability=churn_probability,
                risk_level=risk_level,
                predicted_churn_date=predicted_churn_date,
                risk_factors=risk_factors,
                retention_recommendations=retention_recommendations,
                confidence_score=confidence_score,
                generated_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error predicting churn: {e}", exc_info=True)
            return ChurnPrediction(
                customer_id=customer_id,
                churn_probability=0.0,
                risk_level="low",
                predicted_churn_date=None,
                risk_factors=[],
                retention_recommendations=[],
                confidence_score=0.0,
                generated_at=datetime.now(),
            )

    def calculate_customer_lifetime_value(self, customer_id: int) -> CustomerLifetimeValue:
        """
        حساب قيمة عمر العميل

        Args:
            customer_id: معرف العميل

        Returns:
            كائن قيمة عمر العميل
        """
        try:
            # جمع بيانات العميل
            customer_data = self._get_customer_clv_data(customer_id)

            # حساب قيمة عمر العميل
            clv_value = self._calculate_clv_value(customer_data)

            # تحديد الفئة
            clv_category = self._categorize_clv(clv_value)

            # التنبؤ بطول العمر المتوقع
            predicted_lifetime = self._predict_customer_lifetime(customer_data)

            # حساب الإيراد الشهري
            monthly_revenue = customer_data.get("avg_monthly_revenue", 0)

            # احتمالية الاحتفاظ
            retention_probability = self._calculate_retention_probability(customer_data)

            # إمكانية النمو
            growth_potential = self._assess_growth_potential(customer_data)

            return CustomerLifetimeValue(
                customer_id=customer_id,
                clv_value=clv_value,
                clv_category=clv_category,
                predicted_lifetime_months=predicted_lifetime,
                monthly_revenue=monthly_revenue,
                retention_probability=retention_probability,
                growth_potential=growth_potential,
                calculated_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error calculating CLV: {e}", exc_info=True)
            return CustomerLifetimeValue(
                customer_id=customer_id,
                clv_value=0.0,
                clv_category="unknown",
                predicted_lifetime_months=0,
                monthly_revenue=0.0,
                retention_probability=0.0,
                growth_potential=0.0,
                calculated_at=datetime.now(),
            )

    def analyze_customer_network(self) -> Dict[str, Any]:
        """
        تحليل شبكة العلاقات بين العملاء

        Returns:
            تحليل الشبكة
        """
        try:
            # بناء شبكة العلاقات
            G = self._build_customer_network()

            # حساب المقاييس الأساسية
            network_metrics = {
                "number_of_nodes": G.number_of_nodes(),
                "number_of_edges": G.number_of_edges(),
                "average_degree": (
                    sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
                ),
                "density": nx.density(G),
                "connected_components": nx.number_connected_components(G),
            }

            # تحديد العملاء المؤثرين
            centrality = nx.degree_centrality(G)
            influential_customers = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]

            # تحليل المجتمعات
            communities = self._detect_communities(G)

            return {
                "network_metrics": network_metrics,
                "influential_customers": influential_customers,
                "communities": communities,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing customer network: {e}", exc_info=True)
            return {"error": str(e)}

    def _get_customer_segmentation_data(self) -> List[Dict[str, Any]]:
        """جمع بيانات العملاء للتقسيم"""
        try:
            query = """
                SELECT
                    c.id,
                    COUNT(s.id) as order_count,
                    SUM(s.total_amount) as total_spent,
                    AVG(s.total_amount) as avg_order_value,
                    MAX(s.created_at) as last_order_date,
                    MIN(s.created_at) as first_order_date,
                    COUNT(DISTINCT si.product_id) as unique_products,
                    DATEDIFF(day, MIN(s.created_at), MAX(s.created_at)) as customer_age_days
                FROM customers c
                LEFT JOIN sales s ON c.id = s.customer_id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                GROUP BY c.id
                HAVING order_count > 0
            """

            data = self.db.execute_query(query, fetch_all=True)

            customers = []
            for row in data:
                customer_age_days = row[7] or 1  # تجنب القسمة على صفر

                customers.append(
                    {
                        "customer_id": row[0],
                        "order_count": row[1] or 0,
                        "total_spent": float(row[2] or 0),
                        "avg_order_value": float(row[3] or 0),
                        "last_order_date": row[4],
                        "first_order_date": row[5],
                        "unique_products": row[6] or 0,
                        "customer_age_days": customer_age_days,
                        "avg_order_frequency": (row[1] or 0) / customer_age_days * 30,  # مرات الشراء شهرياً
                        "recency_days": ((datetime.now() - row[4]).days if row[4] else 999),
                    }
                )

            return customers

        except Exception as e:
            self.logger.error(f"Error getting segmentation data: {e}", exc_info=True)
            return []

    def _prepare_segmentation_features(self, customer_data: List[Dict[str, Any]]) -> np.ndarray:
        """إعداد ميزات التقسيم"""
        try:
            df = pd.DataFrame(customer_data)

            # اختيار الميزات الرقمية
            features = [
                "order_count",
                "total_spent",
                "avg_order_value",
                "unique_products",
                "customer_age_days",
                "avg_order_frequency",
                "recency_days",
            ]

            X = df[features].values

            # توحيد المقياس
            X_scaled = self.scaler.fit_transform(X)

            return X_scaled

        except Exception as e:
            self.logger.error(f"Error preparing segmentation features: {e}", exc_info=True)
            return np.array([])

    def _analyze_customer_segment(self, segment_id: int, customers: List[Dict[str, Any]]) -> CustomerSegment:
        """تحليل شريحة عميل محددة"""
        try:
            df = pd.DataFrame(customers)

            # حساب المقاييس المتوسطة
            average_metrics = {
                "avg_order_count": float(df["order_count"].mean()),
                "avg_total_spent": float(df["total_spent"].mean()),
                "avg_order_value": float(df["avg_order_value"].mean()),
                "avg_unique_products": float(df["unique_products"].mean()),
                "avg_order_frequency": float(df["avg_order_frequency"].mean()),
                "avg_recency_days": float(df["recency_days"].mean()),
            }

            # تحديد الخصائص
            characteristics = self._determine_segment_characteristics(average_metrics)

            # توليد التوصيات
            recommended_actions = self._generate_segment_recommendations(characteristics)

            # تحديد اسم الشريحة
            segment_name = self._name_customer_segment(characteristics)

            return CustomerSegment(
                segment_id=f"segment_{segment_id}",
                segment_name=segment_name,
                customer_count=len(customers),
                characteristics=characteristics,
                average_metrics=average_metrics,
                recommended_actions=recommended_actions,
                created_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing customer segment: {e}", exc_info=True)
            return CustomerSegment(
                segment_id=f"segment_{segment_id}",
                segment_name="Unknown Segment",
                customer_count=len(customers),
                characteristics={},
                average_metrics={},
                recommended_actions=[],
                created_at=datetime.now(),
            )

    def _create_default_segment(self, customer_data: List[Dict[str, Any]]) -> CustomerSegment:
        """إنشاء شريحة افتراضية عندما تكون البيانات محدودة"""
        return CustomerSegment(
            segment_id="default_segment",
            segment_name="All Customers",
            customer_count=len(customer_data),
            characteristics={"data_limited": True},
            average_metrics={},
            recommended_actions=["Collect more customer data for better segmentation"],
            created_at=datetime.now(),
        )

    def _determine_segment_characteristics(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """تحديد خصائص الشريحة"""
        characteristics = {}

        # تحليل الإنفاق
        if metrics["avg_total_spent"] > 10000:
            characteristics["spending_level"] = "high"
        elif metrics["avg_total_spent"] > 1000:
            characteristics["spending_level"] = "medium"
        else:
            characteristics["spending_level"] = "low"

        # تحليل التكرار
        if metrics["avg_order_frequency"] > 2:
            characteristics["purchase_frequency"] = "frequent"
        elif metrics["avg_order_frequency"] > 0.5:
            characteristics["purchase_frequency"] = "regular"
        else:
            characteristics["purchase_frequency"] = "occasional"

        # تحليل الولاء
        if metrics["avg_recency_days"] < 30:
            characteristics["loyalty_level"] = "high"
        elif metrics["avg_recency_days"] < 90:
            characteristics["loyalty_level"] = "medium"
        else:
            characteristics["loyalty_level"] = "low"

        return characteristics

    def _generate_segment_recommendations(self, characteristics: Dict[str, Any]) -> List[str]:
        """توليد توصيات للشريحة"""
        recommendations = []

        spending = characteristics.get("spending_level", "medium")
        frequency = characteristics.get("purchase_frequency", "regular")
        loyalty = characteristics.get("loyalty_level", "medium")

        if spending == "high" and loyalty == "high":
            recommendations.extend(["برنامج ولاء VIP", "عروض حصرية وعالية القيمة", "خدمة عملاء مخصصة"])
        elif spending == "high" and loyalty == "low":
            recommendations.extend(["حملات إعادة جذب", "تحليل أسباب الابتعاد", "عروض محدودة الوقت"])
        elif spending == "low" and frequency == "frequent":
            recommendations.extend(
                [
                    "تشجيع على شراء منتجات أغلى",
                    "برامج ترقية المنتجات",
                    "خصومات على الكميات الكبيرة",
                ]
            )

        return recommendations

    def _name_customer_segment(self, characteristics: Dict[str, Any]) -> str:
        """تسمية الشريحة"""
        spending = characteristics.get("spending_level", "medium")
        frequency = characteristics.get("purchase_frequency", "regular")
        loyalty = characteristics.get("loyalty_level", "medium")

        if spending == "high" and loyalty == "high":
            return "عملاء VIP مخلصين"
        elif spending == "high" and loyalty == "low":
            return "عملاء عالي القيمة غير مخلصين"
        elif spending == "low" and frequency == "frequent":
            return "عملاء متكررون منخفضي القيمة"
        elif loyalty == "low":
            return "عملاء غير نشطين"
        else:
            return "عملاء عاديون"

    def _get_customer_journey_data(self, customer_id: int) -> List[Dict[str, Any]]:
        """جمع بيانات رحلة العميل"""
        try:
            query = """
                SELECT s.created_at, s.total_amount, COUNT(si.id) as item_count,
                       GROUP_CONCAT(p.category_id) as categories
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.id
                WHERE s.customer_id = ?
                ORDER BY s.created_at
            """

            data = self.db.execute_query(query, (customer_id,), fetch_all=True)

            journey_events = []
            for row in data:
                journey_events.append(
                    {
                        "date": row[0],
                        "amount": float(row[1] or 0),
                        "item_count": row[2] or 0,
                        "categories": row[3].split(",") if row[3] else [],
                    }
                )

            return journey_events

        except Exception as e:
            self.logger.error(f"Error getting customer journey data: {e}", exc_info=True)
            return []

    def _identify_journey_stages(self, journey_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """تحديد مراحل رحلة العميل"""
        stages = []

        try:
            for event in journey_data:
                # تحديد المرحلة بناءً على الخصائص
                if event["item_count"] == 1 and event["amount"] < 100:
                    stage = "awareness"
                elif event["item_count"] <= 3 and event["amount"] < 500:
                    stage = "consideration"
                elif event["amount"] >= 500 or event["item_count"] > 5:
                    stage = "purchase"
                else:
                    stage = "retention"

                stages.append(
                    {
                        "date": event["date"],
                        "stage": stage,
                        "amount": event["amount"],
                        "item_count": event["item_count"],
                    }
                )

        except Exception as e:
            self.logger.error(f"Error identifying journey stages: {e}", exc_info=True)

        return stages

    def _determine_current_stage(self, journey_stages: List[Dict[str, Any]]) -> str:
        """تحديد المرحلة الحالية"""
        if not journey_stages:
            return "awareness"

        # المرحلة الحالية هي مرحلة آخر حدث
        return journey_stages[-1]["stage"]

    def _predict_next_stage(self, journey_stages: List[Dict[str, Any]], current_stage: str) -> str:
        """التنبؤ بالمرحلة التالية"""
        stage_progression = {
            "awareness": "consideration",
            "consideration": "purchase",
            "purchase": "retention",
            "retention": "advocacy",
            "advocacy": "advocacy",
        }

        return stage_progression.get(current_stage, "unknown")

    def _calculate_journey_score(self, journey_stages: List[Dict[str, Any]]) -> float:
        """حساب درجة الرحلة"""
        if not journey_stages:
            return 0

        # حساب بناءً على التقدم والإنفاق
        total_amount = sum(stage["amount"] for stage in journey_stages)
        stage_count = len(journey_stages)
        avg_amount = total_amount / stage_count

        # درجة بسيطة
        score = min(1.0, (stage_count * 0.1) + (avg_amount * 0.001))

        return score

    def _identify_journey_bottlenecks(self, journey_stages: List[Dict[str, Any]]) -> List[str]:
        """تحديد العقبات في الرحلة"""
        bottlenecks = []

        if not journey_stages:
            return bottlenecks

        # فحص الفجوات الزمنية الطويلة
        for i in range(1, len(journey_stages)):
            days_diff = (journey_stages[i]["date"] - journey_stages[i - 1]["date"]).days
            if days_diff > 90:
                bottlenecks.append(f"فجوة زمنية طويلة ({days_diff} يوم) بين المشتريات")

        # فحص الانخفاض في القيمة
        for i in range(1, len(journey_stages)):
            if journey_stages[i]["amount"] < journey_stages[i - 1]["amount"] * 0.5:
                bottlenecks.append("انخفاض كبير في قيمة المشتريات")

        return bottlenecks

    def _get_customer_churn_features(self, customer_id: int) -> Dict[str, Any]:
        """جمع ميزات العميل للتنبؤ بالخسارة"""
        try:
            # بيانات أساسية
            base_query = """
                SELECT
                    COUNT(s.id) as order_count,
                    SUM(s.total_amount) as total_spent,
                    AVG(s.total_amount) as avg_order_value,
                    MAX(s.created_at) as last_order_date,
                    MIN(s.created_at) as first_order_date,
                    DATEDIFF(day, MAX(s.created_at), GETDATE()) as days_since_last_order
                FROM sales s
                WHERE s.customer_id = ?
            """

            base_data = self.db.execute_query(base_query, (customer_id,), fetch_one=True)

            if not base_data:
                return {}

            features = {
                "order_count": base_data[0] or 0,
                "total_spent": float(base_data[1] or 0),
                "avg_order_value": float(base_data[2] or 0),
                "days_since_last_order": base_data[5] or 0,
                "customer_age_days": ((datetime.now() - base_data[4]).days if base_data[4] else 0),
            }

            # معدل الشراء الشهري
            if features["customer_age_days"] > 0:
                features["monthly_purchase_rate"] = features["order_count"] / (features["customer_age_days"] / 30)
            else:
                features["monthly_purchase_rate"] = 0

            return features

        except Exception as e:
            self.logger.error(f"Error getting churn features: {e}", exc_info=True)
            return {}

    def _calculate_churn_probability(self, features: Dict[str, Any]) -> float:
        """حساب احتمالية الخسارة"""
        if not features:
            return 0.0

        probability = 0.0

        # عامل فترة الخمول
        days_since_last = features.get("days_since_last_order", 0)
        if days_since_last > 90:
            probability += 0.4
        elif days_since_last > 30:
            probability += 0.2

        # عامل عدد الطلبات
        order_count = features.get("order_count", 0)
        if order_count < 3:
            probability += 0.3
        elif order_count < 10:
            probability += 0.1

        # عامل معدل الشراء
        monthly_rate = features.get("monthly_purchase_rate", 0)
        if monthly_rate < 0.5:
            probability += 0.2
        elif monthly_rate < 1:
            probability += 0.1

        return min(1.0, probability)

    def _determine_risk_level(self, probability: float) -> str:
        """تحديد مستوى الخطر"""
        if probability > 0.7:
            return "critical"
        elif probability > 0.5:
            return "high"
        elif probability > 0.3:
            return "medium"
        else:
            return "low"

    def _predict_churn_date(self, features: Dict[str, Any], probability: float) -> Optional[datetime]:
        """التنبؤ بتاريخ الخسارة المحتمل"""
        if probability < 0.3:
            return None

        features.get("days_since_last_order", 0)

        # تقدير بناءً على النمط الحالي
        if probability > 0.7:
            additional_days = 30
        elif probability > 0.5:
            additional_days = 60
        else:
            additional_days = 90

        return datetime.now() + timedelta(days=additional_days)

    def _identify_risk_factors(self, features: Dict[str, Any]) -> List[str]:
        """تحديد عوامل الخطر"""
        factors = []

        if features.get("days_since_last_order", 0) > 90:
            factors.append("فترة خمول طويلة")
        if features.get("order_count", 0) < 3:
            factors.append("عدد طلبات قليل")
        if features.get("monthly_purchase_rate", 0) < 0.5:
            factors.append("معدل شراء منخفض")
        if features.get("avg_order_value", 0) < 50:
            factors.append("قيمة طلب متوسطة منخفضة")

        return factors

    def _generate_retention_recommendations(self, risk_factors: List[str], risk_level: str) -> List[str]:
        """توليد توصيات الاحتفاظ"""
        recommendations = []

        if risk_level in ["high", "critical"]:
            recommendations.append("اتصال فوري من خدمة العملاء")
            recommendations.append("عرض خاص لإعادة الجذب")

        if "فترة خمول طويلة" in risk_factors:
            recommendations.append("إرسال تذكير بالعروض الحالية")

        if "عدد طلبات قليل" in risk_factors:
            recommendations.append("برنامج إدخال للعملاء الجدد")

        if "معدل شراء منخفض" in risk_factors:
            recommendations.append("اقتراح مشتريات متكررة")

        return recommendations

    def _calculate_prediction_confidence(self, features: Dict[str, Any]) -> float:
        """حساب ثقة التنبؤ"""
        if not features:
            return 0.2

        # ثقة أساسية بناءً على كمية البيانات
        data_completeness = sum(1 for v in features.values() if v is not None and v != 0) / len(features)

        return min(1.0, data_completeness * 0.8 + 0.2)  # ثقة أساسية 20%

    def _get_customer_clv_data(self, customer_id: int) -> Dict[str, Any]:
        """جمع بيانات قيمة عمر العميل"""
        try:
            query = """
                SELECT
                    COUNT(s.id) as order_count,
                    SUM(s.total_amount) as total_spent,
                    AVG(s.total_amount) as avg_order_value,
                    MAX(s.created_at) as last_order_date,
                    MIN(s.created_at) as first_order_date,
                    DATEDIFF(day, MIN(s.created_at), MAX(s.created_at)) as customer_age_days
                FROM sales s
                WHERE s.customer_id = ?
            """

            data = self.db.execute_query(query, (customer_id,), fetch_one=True)

            if not data:
                return {}

            customer_age_days = data[5] or 1

            return {
                "order_count": data[0] or 0,
                "total_spent": float(data[1] or 0),
                "avg_order_value": float(data[2] or 0),
                "last_order_date": data[3],
                "first_order_date": data[4],
                "customer_age_days": customer_age_days,
                "avg_monthly_revenue": float(data[1] or 0) / max(1, customer_age_days / 30),
            }

        except Exception as e:
            self.logger.error(f"Error getting CLV data: {e}", exc_info=True)
            return {}

    def _calculate_clv_value(self, customer_data: Dict[str, Any]) -> float:
        """حساب قيمة عمر العميل"""
        if not customer_data:
            return 0.0

        # نموذج CLV بسيط
        avg_monthly_revenue = customer_data.get("avg_monthly_revenue", 0)
        customer_data.get("customer_age_days", 0) / 30

        # افتراض عمر متوقع إضافي (متوسط 24 شهر)
        expected_additional_months = 24

        # معدل الخصم (شهري)
        discount_rate = 0.01

        # حساب CLV
        clv = 0.0
        for month in range(1, int(expected_additional_months) + 1):
            monthly_value = avg_monthly_revenue / ((1 + discount_rate) ** month)
            clv += monthly_value

        return float(clv)

    def _categorize_clv(self, clv_value: float) -> str:
        """تصنيف قيمة عمر العميل"""
        if clv_value > 10000:
            return "vip"
        elif clv_value > 1000:
            return "high"
        elif clv_value > 100:
            return "medium"
        else:
            return "low"

    def _predict_customer_lifetime(self, customer_data: Dict[str, Any]) -> int:
        """التنبؤ بطول عمر العميل بالأشهر"""
        base_lifetime = 24  # 24 شهر كأساس

        # تعديل بناءً على النشاط
        order_count = customer_data.get("order_count", 0)
        if order_count > 50:
            base_lifetime += 12
        elif order_count > 20:
            base_lifetime += 6

        return base_lifetime

    def _calculate_retention_probability(self, customer_data: Dict[str, Any]) -> float:
        """حساب احتمالية الاحتفاظ"""
        probability = 0.5  # أساس

        # تعديل بناءً على النشاط
        order_count = customer_data.get("order_count", 0)
        if order_count > 20:
            probability += 0.3
        elif order_count > 10:
            probability += 0.2
        elif order_count > 5:
            probability += 0.1

        # تعديل بناءً على العمر
        customer_age_days = customer_data.get("customer_age_days", 0)
        if customer_age_days > 365:
            probability += 0.1

        return min(1.0, probability)

    def _assess_growth_potential(self, customer_data: Dict[str, Any]) -> float:
        """تقييم إمكانية النمو"""
        potential = 0

        # بناءً على متوسط قيمة الطلب
        avg_order_value = customer_data.get("avg_order_value", 0)
        if avg_order_value < 200:
            potential += 0.4  # إمكانية زيادة كبيرة
        elif avg_order_value < 500:
            potential += 0.2

        # بناءً على عدد الطلبات
        order_count = customer_data.get("order_count", 0)
        if order_count < 10:
            potential += 0.3  # إمكانية زيادة التكرار

        return min(1.0, potential)

    def _build_customer_network(self) -> nx.Graph:
        """بناء شبكة العلاقات بين العملاء"""
        G = nx.Graph()

        try:
            # إضافة العملاء كعقد
            customers_query = "SELECT id, name FROM customers"
            customers = self.db.execute_query(customers_query, fetch_all=True)

            for customer in customers:
                G.add_node(customer[0], name=customer[1])

            # إضافة الحواف بناءً على مشتريات المنتجات نفسها
            product_sharing_query = """
                SELECT DISTINCT c1.customer_id, c2.customer_id, COUNT(*) as shared_products
                FROM sale_items si1
                JOIN sale_items si2 ON si1.product_id = si2.product_id AND si1.sale_id != si2.sale_id
                JOIN sales s1 ON si1.sale_id = s1.id
                JOIN sales s2 ON si2.sale_id = s2.id
                JOIN customers c1 ON s1.customer_id = c1.id
                JOIN customers c2 ON s2.customer_id = c2.id
                WHERE c1.customer_id < c2.customer_id
                GROUP BY c1.customer_id, c2.customer_id
                HAVING shared_products > 2
            """

            connections = self.db.execute_query(product_sharing_query, fetch_all=True)

            for conn in connections:
                G.add_edge(conn[0], conn[1], weight=conn[2])

        except Exception as e:
            self.logger.error(f"Error building customer network: {e}", exc_info=True)

        return G

    def _detect_communities(self, G: nx.Graph) -> List[List[int]]:
        """كشف المجتمعات في الشبكة"""
        try:
            # استخدام خوارزمية Louvain إذا كانت متوفرة
            from community import community_louvain

            partition = community_louvain.best_partition(G)

            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(node)

            return list(communities.values())

        except ImportError:
            # استخدام خوارزمية بسيطة
            return list(nx.connected_components(G))

    def _load_analytics_models(self):
        """تحميل نماذج التحليل المدربة"""
        try:
            # في التطبيق الحقيقي، سنحمل النماذج من الملفات
            pass
        except Exception as e:
            self.logger.error(f"Error loading analytics models: {e}", exc_info=True)

    def update_analytics_models(self):
        """تحديث نماذج التحليل بالبيانات الجديدة"""
        try:
            self.logger.info("Updating analytics models with latest data...")

            # تحديث نموذج التقسيم
            customer_data = self._get_customer_segmentation_data()
            if len(customer_data) >= self.min_customers_for_segmentation:
                X = self._prepare_segmentation_features(customer_data)
                if len(X) > 0:
                    X_pca = self.pca.fit_transform(X)
                    self.segmentation_model = KMeans(n_clusters=4, random_state=42, n_init=10)
                    self.segmentation_model.fit(X_pca)

            self.logger.info("Analytics models updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating analytics models: {e}", exc_info=True)
