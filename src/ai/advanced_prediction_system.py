#!/usr/bin/env python3
"""
نظام التنبؤ المتقدم - Advanced Prediction System
نظام تنبؤ شامل يجمع بين نماذج متعددة للتنبؤ بالمبيعات والمخزون والعملاء
"""

import random  # nosec B311
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .machine_learning_model import InventoryPredictionModel, SalesPredictionModel


class AdvancedPredictionSystem:
    """نظام التنبؤ المتقدم"""

    def __init__(self):
        self.sales_model = SalesPredictionModel()
        self.inventory_model = InventoryPredictionModel()
        self.customer_model = CustomerPredictionModel()
        self.market_model = MarketPredictionModel()
        self.prediction_cache = {}
        self.last_updated = None

    def cache_predictions(self, key: str, predictions: Any) -> None:
        """حفظ التنبؤات في الذاكرة المؤقتة"""
        self.prediction_cache[key] = predictions

    def get_cached_predictions(self, key: str) -> Optional[Any]:
        """استرجاع التنبؤات من الذاكرة المؤقتة"""
        return self.prediction_cache.get(key)

    def initialize_system(self, historical_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """تهيئة النظام مع البيانات التاريخية"""
        results = {}

        # تدريب نموذج المبيعات
        if "sales" in historical_data:
            sales_result = self.sales_model.train(historical_data["sales"])
            results["sales_model"] = sales_result

        # تدريب نموذج المخزون
        if "inventory" in historical_data:
            inventory_results = {}
            for product_data in historical_data["inventory"]:
                product_id = product_data.get("product_id")
                if product_id:
                    result = self.inventory_model.train_for_product(product_id, product_data.get("data", []))
                    inventory_results[product_id] = result
            results["inventory_model"] = inventory_results

        # تدريب نموذج العملاء
        if "customers" in historical_data:
            customer_result = self.customer_model.train(historical_data["customers"])
            results["customer_model"] = customer_result

        # تدريب نموذج السوق
        if "market" in historical_data:
            market_result = self.market_model.train(historical_data["market"])
            results["market_model"] = market_result

        self.last_updated = datetime.now()

        return {
            "status": "initialized",
            "models_trained": len(results),
            "results": results,
            "timestamp": self.last_updated.isoformat(),
        }

    def generate_comprehensive_forecast(
        self, forecast_period_days: int = 30, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """توليد تنبؤ شامل"""
        context = context or {}
        start_date = datetime.now()
        end_date = start_date + timedelta(days=forecast_period_days)

        # تنبؤ المبيعات
        sales_forecast = self.sales_model.predict_range(start_date, end_date, context)

        # تنبؤ المخزون
        inventory_forecast = self._generate_inventory_forecast(forecast_period_days, context)

        # تنبؤ العملاء
        customer_forecast = self.customer_model.predict_customer_behavior(forecast_period_days, context)

        # تنبؤ السوق
        market_forecast = self.market_model.predict_market_trends(context)

        # دمج التنبؤات
        integrated_forecast = self._integrate_forecasts(
            sales_forecast,
            inventory_forecast,
            customer_forecast,
            market_forecast,
            context,
        )

        # حساب المخاطر والفرص
        risk_assessment = self._assess_forecast_risks(integrated_forecast, context)

        # توصيات العمل
        recommendations = self._generate_business_recommendations(integrated_forecast, risk_assessment)

        return {
            "forecast_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": forecast_period_days,
            },
            "forecast_period_days": forecast_period_days,
            "sales_forecast": sales_forecast,
            "inventory_forecast": inventory_forecast,
            "customer_forecast": customer_forecast,
            "market_forecast": market_forecast,
            "integrated_forecast": integrated_forecast,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "confidence_score": self._calculate_overall_confidence(integrated_forecast),
            "generated_at": datetime.now().isoformat(),
        }

    def predict_product_performance(
        self, product_id: str, days_ahead: int = 30, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """تنبؤ أداء منتج محدد"""
        context = context or {}

        # تنبؤ المبيعات للمنتج
        product_sales_forecast = self._predict_product_sales(product_id, days_ahead, context)

        # تنبؤ المخزون للمنتج
        inventory_needs = self.inventory_model.predict_inventory_needs(product_id, days_ahead)

        # تحليل الربحية
        profitability_analysis = self._analyze_product_profitability(product_id, product_sales_forecast)

        # تحليل المنافسة
        competition_analysis = self.market_model.analyze_competition(product_id, context)

        return {
            "product_id": product_id,
            "forecast_period_days": days_ahead,
            "sales_forecast": product_sales_forecast,
            "inventory_needs": inventory_needs,
            "profitability_analysis": profitability_analysis,
            "competition_analysis": competition_analysis,
            "overall_score": self._calculate_product_score(
                product_sales_forecast, profitability_analysis, competition_analysis
            ),
            "recommendations": self._generate_product_recommendations(
                product_id,
                product_sales_forecast,
                inventory_needs,
                profitability_analysis,
            ),
        }

    def predict_customer_segment_behavior(
        self, segment_id: str, days_ahead: int = 30, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """تنبؤ سلوك شريحة عملاء"""
        return self.customer_model.predict_segment_behavior(segment_id, days_ahead, context)

    def update_models(self, new_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """تحديث النماذج ببيانات جديدة"""
        update_results = {}

        if "sales" in new_data:
            update_results["sales"] = self.sales_model.update_model(new_data["sales"])

        if "inventory" in new_data:
            inventory_updates = {}
            for product_data in new_data["inventory"]:
                product_id = product_data.get("product_id")
                if product_id:
                    result = self.inventory_model.train_for_product(product_id, product_data.get("data", []))
                    inventory_updates[product_id] = result
            update_results["inventory"] = inventory_updates

        if "customers" in new_data:
            update_results["customers"] = self.customer_model.update_model(new_data["customers"])

        if "market" in new_data:
            update_results["market"] = self.market_model.update_model(new_data["market"])

        self.last_updated = datetime.now()

        # مسح الذاكرة المؤقتة
        self.prediction_cache.clear()

        return {
            "status": "updated",
            "models_updated": len(update_results),
            "results": update_results,
            "timestamp": self.last_updated.isoformat(),
        }

    def get_system_health(self) -> Dict[str, Any]:
        """حالة النظام"""
        return {
            "models_status": {
                "sales_model": ("trained" if self.sales_model.model_parameters else "not_trained"),
                "inventory_model": f"{len(self.inventory_model.product_models)} products trained",
                "customer_model": (
                    "trained"
                    if hasattr(self.customer_model, "model_parameters") and self.customer_model.model_parameters
                    else "not_trained"
                ),
                "market_model": (
                    "trained"
                    if hasattr(self.market_model, "model_parameters") and self.market_model.model_parameters
                    else "not_trained"
                ),
            },
            "last_updated": (self.last_updated.isoformat() if self.last_updated else None),
            "cache_size": len(self.prediction_cache),
            "overall_health": self._assess_system_health(),
        }

    def get_prediction_summary(self, forecast_result: Dict[str, Any]) -> Dict[str, Any]:
        """الحصول على ملخص التنبؤ"""
        return {
            "summary": "تنبؤ شامل للأداء",
            "confidence": forecast_result.get("confidence_score", 0.5),
            "period": forecast_result.get("forecast_period_days", 30),
        }

    def _generate_inventory_forecast(self, days_ahead: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """توليد تنبؤ المخزون"""
        # افتراض أن لدينا قائمة بالمنتجات الرئيسية
        # في التطبيق الحقيقي، سيتم الحصول عليها من قاعدة البيانات
        key_products = ["PROD001", "PROD002", "PROD003"]  # مثال

        inventory_forecasts = {}
        total_shortage_risk = 0
        total_overstock_risk = 0

        for product_id in key_products:
            forecast = self.inventory_model.predict_inventory_needs(product_id, days_ahead)
            if "recommended_stock_level" in forecast:
                inventory_forecasts[product_id] = forecast

                # تقدير المخاطر
                if forecast.get("predicted_demand", 0) > forecast.get("recommended_stock_level", 0):
                    total_shortage_risk += 1
                elif forecast.get("predicted_demand", 0) * 0.5 > forecast.get("recommended_stock_level", 0):
                    total_overstock_risk += 1

        return {
            "product_forecasts": inventory_forecasts,
            "summary": {
                "total_products": len(inventory_forecasts),
                "shortage_risk_products": total_shortage_risk,
                "overstock_risk_products": total_overstock_risk,
                "healthy_products": len(inventory_forecasts) - total_shortage_risk - total_overstock_risk,
            },
            "recommendations": self._generate_inventory_recommendations(inventory_forecasts),
        }

    def _predict_product_sales(self, product_id: str, days_ahead: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """تنبؤ مبيعات منتج محدد"""
        # في التطبيق الحقيقي، سيتم تخصيص نموذج لكل منتج
        # هنا نستخدم نموذج المبيعات العام مع تعديلات
        base_forecast = self.sales_model.predict_range(
            datetime.now(), datetime.now() + timedelta(days=days_ahead), context
        )

        # افتراض توزيع المبيعات على المنتجات
        product_share = 0.1  # 10% من إجمالي المبيعات

        return {
            "product_id": product_id,
            "predicted_sales": round(base_forecast.get("total_prediction", 0) * product_share, 2),
            "average_daily": round(base_forecast.get("average_daily", 0) * product_share, 2),
            "confidence": base_forecast.get("average_confidence", 0.5),
            "trend": "increasing" if random.random() > 0.5 else "stable",
        }

    def _analyze_product_profitability(self, product_id: str, sales_forecast: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل ربحية المنتج"""
        # افتراضات للربحية
        cost_per_unit = 50.0
        price_per_unit = 100.0
        margin = (price_per_unit - cost_per_unit) / price_per_unit

        predicted_sales = sales_forecast.get("predicted_sales", 0)
        predicted_units = predicted_sales / price_per_unit  # افتراض

        return {
            "gross_margin": round(margin * 100, 2),
            "predicted_profit": round(predicted_units * (price_per_unit - cost_per_unit), 2),
            "break_even_units": round(cost_per_unit / (price_per_unit - cost_per_unit), 2),
            "profitability_score": ("high" if margin > 0.3 else "medium" if margin > 0.2 else "low"),
        }

    def _integrate_forecasts(
        self,
        sales: Dict,
        inventory: Dict,
        customer: Dict,
        market: Dict,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """دمج التنبؤات"""
        # حساب التنبؤ المتكامل
        total_sales = sales.get("total_prediction", 0)
        market_confidence = market.get("overall_confidence", 0.5)
        customer_sentiment = customer.get("average_sentiment", 0.5)

        # تعديل حسب السوق والعملاء
        integrated_sales = total_sales * (0.7 + 0.3 * market_confidence) * (0.8 + 0.2 * customer_sentiment)

        return {
            "integrated_sales_prediction": round(integrated_sales, 2),
            "market_adjustment_factor": round(0.7 + 0.3 * market_confidence, 3),
            "customer_adjustment_factor": round(0.8 + 0.2 * customer_sentiment, 3),
            "overall_confidence": round((market_confidence + customer_sentiment) / 2, 3),
            "key_drivers": self._identify_key_drivers(sales, inventory, customer, market),
        }

    def _assess_forecast_risks(self, integrated_forecast: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """تقييم مخاطر التنبؤ"""
        risks = []

        confidence = integrated_forecast.get("overall_confidence", 0.5)

        if confidence < 0.6:
            risks.append(
                {
                    "type": "low_confidence",
                    "severity": "high",
                    "description": "ثقة التنبؤ منخفضة بسبب محدودية البيانات",
                }
            )

        if context.get("economic_uncertainty"):
            risks.append(
                {
                    "type": "economic",
                    "severity": "medium",
                    "description": "عدم استقرار اقتصادي قد يؤثر على التنبؤات",
                }
            )

        if context.get("competition_increase"):
            risks.append(
                {
                    "type": "competition",
                    "severity": "medium",
                    "description": "زيادة المنافسة قد تقلل من المبيعات المتوقعة",
                }
            )

        return {
            "risk_count": len(risks),
            "high_severity_risks": len([r for r in risks if r["severity"] == "high"]),
            "risks": risks,
            "mitigation_strategies": self._suggest_risk_mitigations(risks),
        }

    def _generate_business_recommendations(
        self, forecast: Dict[str, Any], risks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """توليد توصيات العمل"""
        recommendations = []

        integrated_sales = forecast.get("integrated_sales_prediction", 0)

        # توصيات مبيعات
        if integrated_sales > 10000:  # عتبة عالية
            recommendations.append(
                {
                    "category": "sales",
                    "priority": "high",
                    "action": "زيادة المخزون والتسويق",
                    "reason": "توقعات مبيعات عالية",
                }
            )

        # توصيات مخاطر
        if risks["high_severity_risks"] > 0:
            recommendations.append(
                {
                    "category": "risk_management",
                    "priority": "high",
                    "action": "تطوير خطط طوارئ",
                    "reason": "مخاطر عالية الخطورة",
                }
            )

        # توصيات عامة
        recommendations.append(
            {
                "category": "monitoring",
                "priority": "medium",
                "action": "مراقبة الأداء الأسبوعي",
                "reason": "ضمان دقة التنبؤات",
            }
        )

        return recommendations

    def _calculate_overall_confidence(self, integrated_forecast: Dict[str, Any]) -> float:
        """حساب الثقة الإجمالية"""
        return integrated_forecast.get("overall_confidence", 0.5)

    def _calculate_product_score(self, sales_forecast: Dict, profitability: Dict, competition: Dict) -> float:
        """حساب نقاط المنتج"""
        sales_score = min(sales_forecast.get("confidence", 0.5) * 2, 1.0)
        profit_score = (
            1.0
            if profitability.get("profitability_score") == "high"
            else 0.7 if profitability.get("profitability_score") == "medium" else 0.4
        )
        competition_score = 1.0 - (competition.get("intensity", 0.5) * 0.5)

        return round((sales_score + profit_score + competition_score) / 3, 3)

    def _generate_product_recommendations(
        self, product_id: str, sales: Dict, inventory: Dict, profitability: Dict
    ) -> List[str]:
        """توليد توصيات المنتج"""
        recommendations = []

        if sales.get("trend") == "increasing":
            recommendations.append("زيادة المخزون - اتجاه تصاعدي في المبيعات")

        if profitability.get("profitability_score") == "high":
            recommendations.append("التركيز على التسويق - ربحية عالية")

        if inventory.get("shortage_risk", False):
            recommendations.append("إعادة طلب فورية - خطر نفاد المخزون")

        return recommendations

    def _generate_inventory_recommendations(self, forecasts: Dict[str, Dict]) -> List[str]:
        """توليد توصيات المخزون"""
        recommendations = []

        shortage_products = [
            pid for pid, f in forecasts.items() if f.get("predicted_demand", 0) > f.get("recommended_stock_level", 0)
        ]
        if shortage_products:
            recommendations.append(f"إعادة طلب فورية للمنتجات: {', '.join(shortage_products[:3])}")

        healthy_products = len(
            [f for f in forecasts.values() if f.get("predicted_demand", 0) <= f.get("recommended_stock_level", 0)]
        )
        if healthy_products > len(forecasts) * 0.7:
            recommendations.append("مستويات المخزون متوازنة بشكل عام")

        return recommendations

    def _identify_key_drivers(self, sales: Dict, inventory: Dict, customer: Dict, market: Dict) -> List[str]:
        """تحديد العوامل الرئيسية"""
        drivers = []

        if market.get("growth_rate", 0) > 0.05:
            drivers.append("نمو سوق قوي")

        if customer.get("average_sentiment", 0.5) > 0.7:
            drivers.append("رضا عالي من العملاء")

        if sales.get("average_confidence", 0.5) > 0.8:
            drivers.append("دقة عالية في تنبؤات المبيعات")

        return drivers

    def _suggest_risk_mitigations(self, risks: List[Dict]) -> List[str]:
        """اقتراح استراتيجيات تخفيف المخاطر"""
        mitigations = []

        for risk in risks:
            if risk["type"] == "low_confidence":
                mitigations.append("جمع المزيد من البيانات التاريخية")
            elif risk["type"] == "economic":
                mitigations.append("تطوير سيناريوهات متعددة للظروف الاقتصادية")
            elif risk["type"] == "competition":
                mitigations.append("تعزيز التميز التنافسي وتجربة العملاء")

        return mitigations

    def _assess_system_health(self) -> str:
        """تقييم صحة النظام"""
        trained_models = sum(
            [
                1 if self.sales_model.model_parameters else 0,
                1 if self.inventory_model.product_models else 0,
                (1 if hasattr(self.customer_model, "model_parameters") and self.customer_model.model_parameters else 0),
                (1 if hasattr(self.market_model, "model_parameters") and self.market_model.model_parameters else 0),
            ]
        )

        if trained_models == 4:
            return "excellent"
        elif trained_models >= 2:
            return "good"
        elif trained_models >= 1:
            return "fair"
        else:
            return "poor"


class CustomerPredictionModel:
    """نموذج تنبؤ العملاء"""

    def __init__(self):
        self.model_parameters = {}

    def train(self, customer_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تدريب النموذج"""
        # تنفيذ بسيط للتدريب
        self.model_parameters = {"total_customers": len(customer_data), "trained": True}
        return {"status": "trained"}

    def predict_customer_behavior(self, days_ahead: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """تنبؤ سلوك العملاء"""
        return {
            "average_sentiment": 0.7,
            "predicted_churn_rate": 0.05,
            "predicted_new_customers": 25,
        }

    def predict_segment_behavior(self, segment_id: str, days_ahead: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """تنبؤ سلوك شريحة"""
        return {
            "segment_id": segment_id,
            "predicted_behavior": "stable",
            "confidence": 0.8,
        }

    def update_model(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحديث النموذج"""
        return {"status": "updated"}


class MarketPredictionModel:
    """نموذج تنبؤ السوق"""

    def __init__(self):
        self.model_parameters = {}

    def train(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تدريب النموذج"""
        self.model_parameters = {"total_data_points": len(market_data), "trained": True}
        return {"status": "trained"}

    def predict_market_conditions(
        self, start_date: datetime, end_date: datetime, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تنبؤ ظروف السوق"""
        return {
            "growth_rate": 0.03,
            "overall_confidence": 0.75,
            "market_trend": "growing",
        }

    def predict_market_trends(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """الاسم البديل للتوافق مع الاختبارات"""
        return self.predict_market_conditions(datetime.now(), datetime.now() + timedelta(days=30), context)

    def analyze_competition(self, product_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل المنافسة"""
        return {"intensity": 0.6, "competitive_advantage": "medium"}

    def update_model(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحديث النموذج"""
        return {"status": "updated"}
