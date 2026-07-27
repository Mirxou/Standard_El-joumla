import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة التنبؤ بالمبيعات - Sales Prediction Service
خدمة متخصصة في التنبؤ بالمبيعات والطلب
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.services.ai_analytics_engine import AIAnalyticsEngine
from src.utils.logger import setup_logger


@dataclass
class DemandForecast:
    """تنبؤ بالطلب"""

    product_id: int
    forecast_date: datetime
    predicted_demand: float
    confidence_interval: Tuple[float, float]
    accuracy_score: float
    factors: Dict[str, Any]


@dataclass
class SeasonalPattern:
    """نمط موسمي"""

    product_id: int
    pattern_type: str  # 'weekly', 'monthly', 'yearly'
    peak_periods: List[str]
    low_periods: List[str]
    seasonality_strength: float
    detected_at: datetime


@dataclass
class InventoryRecommendation:
    """توصية مخزون"""

    product_id: int
    recommended_stock_level: int
    safety_stock: int
    reorder_point: int
    reasoning: str
    confidence_score: float
    generated_at: datetime


class SalesPredictionService:
    """خدمة التنبؤ بالمبيعات المتقدمة"""

    def __init__(self, db_manager: DatabaseManager, ai_engine: AIAnalyticsEngine):
        self.logger = setup_logger(__name__)
        from src.utils.db_utils import SafeDatabaseWrapper
        self.db = SafeDatabaseWrapper(db_manager, self.logger)
        self.ai_engine = ai_engine
        self.config = ConfigManager()

        # نماذج التعلم الآلي
        self.demand_model = None
        self.seasonal_model = None
        self.scaler = StandardScaler()

        # معلمات التكوين
        self.forecast_horizon_days = self.config.get("prediction.forecast_horizon_days", 90)
        self.min_training_samples = self.config.get("prediction.min_training_samples", 30)
        self.model_accuracy_threshold = self.config.get("prediction.accuracy_threshold", 0.7)
        self.seasonal_analysis_period = self.config.get("prediction.seasonal_period_days", 365)

        # تحميل النماذج المدربة
        self._load_prediction_models()

    def forecast_demand(self, product_id: int, days_ahead: int = 30) -> DemandForecast:
        """
        التنبؤ بالطلب لمنتج محدد

        Args:
            product_id: معرف المنتج
            days_ahead: عدد الأيام المستقبلية للتنبؤ

        Returns:
            كائن التنبؤ بالطلب
        """
        try:
            # جمع البيانات التاريخية
            historical_data = self._get_demand_history(product_id, days=self.seasonal_analysis_period)

            if len(historical_data) < self.min_training_samples:
                return self._simple_demand_forecast(product_id, days_ahead)

            # تحليل الأنماط الموسمية
            seasonal_patterns = self._analyze_seasonal_patterns(historical_data)

            # إعداد البيانات للتدريب
            X, y = self._prepare_demand_training_data(historical_data, seasonal_patterns)

            # تدريب النموذج
            if self.demand_model is None:
                self.demand_model = self._select_best_model(X, y)

            # التنبؤ
            forecast_date = datetime.now() + timedelta(days=days_ahead)
            prediction_features = self._get_forecast_features(product_id, forecast_date, seasonal_patterns)

            predicted_demand = self.demand_model.predict(prediction_features.reshape(1, -1))[0]

            # حساب فترة الثقة
            confidence_interval = self._calculate_confidence_interval(X, y, predicted_demand)

            # حساب دقة النموذج
            accuracy_score = self._evaluate_model_accuracy(X, y)

            # تحديد العوامل المؤثرة
            factors = self._analyze_demand_factors(product_id, historical_data, seasonal_patterns)

            return DemandForecast(
                product_id=product_id,
                forecast_date=forecast_date,
                predicted_demand=float(max(0, predicted_demand)),
                confidence_interval=confidence_interval,
                accuracy_score=accuracy_score,
                factors=factors,
            )

        except Exception as e:
            self.logger.error(f"Error forecasting demand: {e}")
            return self._fallback_demand_forecast(product_id, days_ahead)

    def analyze_seasonal_patterns(self, product_id: int) -> SeasonalPattern:
        """
        تحليل الأنماط الموسمية للمنتج

        Args:
            product_id: معرف المنتج

        Returns:
            كائن النمط الموسمي
        """
        try:
            # جمع البيانات التاريخية
            historical_data = self._get_demand_history(product_id, days=self.seasonal_analysis_period)

            if len(historical_data) < 60:  # تحتاج 60 يوم على الأقل للتحليل الموسمي
                return SeasonalPattern(
                    product_id=product_id,
                    pattern_type="insufficient_data",
                    peak_periods=[],
                    low_periods=[],
                    seasonality_strength=0,
                    detected_at=datetime.now(),
                )

            # تحليل النمط الأسبوعي
            weekly_patterns = self._analyze_weekly_patterns(historical_data)

            # تحليل النمط الشهري
            monthly_patterns = self._analyze_monthly_patterns(historical_data)

            # تحديد النمط الأقوى
            if weekly_patterns["strength"] > monthly_patterns["strength"]:
                pattern_type = "weekly"
                peak_periods = weekly_patterns["peaks"]
                low_periods = weekly_patterns["lows"]
                strength = weekly_patterns["strength"]
            else:
                pattern_type = "monthly"
                peak_periods = monthly_patterns["peaks"]
                low_periods = monthly_patterns["lows"]
                strength = monthly_patterns["strength"]

            return SeasonalPattern(
                product_id=product_id,
                pattern_type=pattern_type,
                peak_periods=peak_periods,
                low_periods=low_periods,
                seasonality_strength=strength,
                detected_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing seasonal patterns: {e}")
            return SeasonalPattern(
                product_id=product_id,
                pattern_type="error",
                peak_periods=[],
                low_periods=[],
                seasonality_strength=0,
                detected_at=datetime.now(),
            )

    def recommend_inventory_levels(self, product_id: int) -> InventoryRecommendation:
        """
        توصية مستويات المخزون المثالية

        Args:
            product_id: معرف المنتج

        Returns:
            كائن توصية المخزون
        """
        try:
            # الحصول على بيانات المنتج
            product_data = self._get_product_inventory_data(product_id)

            # التنبؤ بالطلب للأشهر القادمة
            forecast = self.forecast_demand(product_id, days_ahead=90)

            # حساب المتوسط اليومي للطلب
            daily_demand_avg = forecast.predicted_demand / 90

            # حساب مستوى المخزون الموصى به
            lead_time_days = product_data.get("lead_time_days", 7)
            self.config.get("inventory.safety_stock_days", 14)
            service_level = self.config.get("inventory.service_level", 0.95)

            # حساب الطلب أثناء وقت الانتظار
            lead_time_demand = daily_demand_avg * lead_time_days

            # حساب المخزون الآمن
            demand_std = self._calculate_demand_std(product_id)
            safety_stock = demand_std * np.sqrt(lead_time_days) * self._get_safety_factor(service_level)

            # نقطة إعادة الطلب
            reorder_point = lead_time_demand + safety_stock

            # المخزون الموصى به الكلي
            recommended_stock = reorder_point + (daily_demand_avg * 30)  # 30 يوم من المخزون

            reasoning_parts = [
                f"الطلب اليومي المتوقع: {daily_demand_avg:.1f}",
                f"وقت الانتظار: {lead_time_days} أيام",
                f"المخزون الآمن: {safety_stock:.1f}",
                f"نقطة إعادة الطلب: {reorder_point:.1f}",
            ]

            reasoning = "; ".join(reasoning_parts)

            return InventoryRecommendation(
                product_id=product_id,
                recommended_stock_level=int(np.ceil(recommended_stock)),
                safety_stock=int(np.ceil(safety_stock)),
                reorder_point=int(np.ceil(reorder_point)),
                reasoning=reasoning,
                confidence_score=forecast.accuracy_score,
                generated_at=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error recommending inventory levels: {e}")
            return InventoryRecommendation(
                product_id=product_id,
                recommended_stock_level=0,
                safety_stock=0,
                reorder_point=0,
                reasoning="خطأ في حساب التوصية",
                confidence_score=0,
                generated_at=datetime.now(),
            )

    def predict_seasonal_demand(self, product_id: int, target_date: datetime) -> float:
        """
        التنبؤ بالطلب في تاريخ محدد بناءً على الأنماط الموسمية

        Args:
            product_id: معرف المنتج
            target_date: التاريخ المستهدف

        Returns:
            الطلب المتوقع
        """
        try:
            seasonal_pattern = self.analyze_seasonal_patterns(product_id)

            if seasonal_pattern.pattern_type == "insufficient_data":
                return 0

            # الحصول على متوسط الطلب التاريخي
            historical_data = self._get_demand_history(product_id, days=365)
            avg_demand = np.mean([d["quantity"] for d in historical_data])

            # تطبيق المعامل الموسمي
            seasonal_multiplier = self._get_seasonal_multiplier(target_date, seasonal_pattern)

            return avg_demand * seasonal_multiplier

        except Exception as e:
            self.logger.error(f"Error predicting seasonal demand: {e}")
            return 0

    def _get_demand_history(self, product_id: int, days: int = 365) -> List[Dict[str, Any]]:
        """الحصول على تاريخ الطلب"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT DATE(s.created_at) as sale_date, SUM(si.quantity) as quantity,
                       COUNT(DISTINCT s.id) as order_count
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? AND s.created_at >= ?
                GROUP BY DATE(s.created_at)
                ORDER BY sale_date
            """

            data = self.db.execute_query(query, (product_id, start_date), fetch_all=True)

            return [{"date": row.get('sale_date'), "quantity": row.get('quantity', 0), "order_count": row.get('order_count', 0)} for row in data]

        except Exception as e:
            self.logger.error(f"Error getting demand history: {e}")
            return []

    def _prepare_demand_training_data(
        self, historical_data: List[Dict[str, Any]], seasonal_patterns: SeasonalPattern
    ) -> Tuple[np.ndarray, np.ndarray]:
        """إعداد بيانات التدريب للتنبؤ بالطلب"""
        try:
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])

            # ميزات زمنية
            df["day_of_week"] = df["date"].dt.dayofweek
            df["month"] = df["date"].dt.month
            df["day_of_month"] = df["date"].dt.day
            df["week_of_year"] = df["date"].dt.isocalendar().week
            df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

            # ميزات متأخرة
            df["quantity_lag_1"] = df["quantity"].shift(1)
            df["quantity_lag_7"] = df["quantity"].shift(7)
            df["quantity_lag_30"] = df["quantity"].shift(30)

            # متوسطات متحركة
            df["quantity_rolling_mean_7"] = df["quantity"].rolling(window=7).mean()
            df["quantity_rolling_std_7"] = df["quantity"].rolling(window=7).std()

            # ميزات موسمية
            df["seasonal_multiplier"] = df.apply(
                lambda row: self._get_seasonal_multiplier(row["date"], seasonal_patterns),
                axis=1,
            )

            # إزالة الصفوف التي تحتوي على NaN
            df = df.dropna()

            # تحديد الميزات والهدف
            features = [
                "day_of_week",
                "month",
                "day_of_month",
                "week_of_year",
                "is_weekend",
                "quantity_lag_1",
                "quantity_lag_7",
                "quantity_lag_30",
                "quantity_rolling_mean_7",
                "quantity_rolling_std_7",
                "seasonal_multiplier",
            ]

            X = df[features].values
            y = df["quantity"].values

            return X, y

        except Exception as e:
            self.logger.error(f"Error preparing demand training data: {e}")
            return np.array([]), np.array([])

    def _select_best_model(self, X: np.ndarray, y: np.ndarray) -> Any:
        """اختيار أفضل نموذج للتنبؤ"""
        try:
            models = {
                "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
                "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
                "LinearRegression": LinearRegression(),
            }

            best_model = None
            best_score = -np.inf
            cv_val = min(3, len(X))

            for name, model in models.items():
                if cv_val >= 2:
                    try:
                        scores = cross_val_score(model, X, y, cv=cv_val, scoring="r2")
                        avg_score = np.mean(scores)
                    except Exception:
                        try:
                            model.fit(X, y)
                            from sklearn.metrics import r2_score
                            avg_score = float(r2_score(y, model.predict(X)))
                        except Exception:
                            avg_score = -1.0
                else:
                    try:
                        model.fit(X, y)
                        from sklearn.metrics import r2_score
                        avg_score = float(r2_score(y, model.predict(X)))
                    except Exception:
                        avg_score = -1.0

                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model

            # تدريب النموذج الأفضل
            best_model.fit(X, y)

            self.logger.info(f"Selected model: {best_model.__class__.__name__} with R² score: {best_score:.3f}")

            return best_model

        except Exception as e:
            self.logger.error(f"Error selecting best model: {e}")
            return RandomForestRegressor(n_estimators=100, random_state=42)

    def _get_forecast_features(
        self,
        product_id: int,
        forecast_date: datetime,
        seasonal_patterns: SeasonalPattern,
    ) -> np.ndarray:
        """الحصول على ميزات التنبؤ"""
        try:
            # ميزات زمنية أساسية
            features = [
                forecast_date.weekday(),  # day_of_week
                forecast_date.month,  # month
                forecast_date.day,  # day_of_month
                forecast_date.isocalendar()[1],  # week_of_year
                1 if forecast_date.weekday() >= 5 else 0,  # is_weekend
            ]

            # ميزات متأخرة (من البيانات الأخيرة)
            recent_data = self._get_demand_history(product_id, days=30)
            if recent_data:
                last_quantity = recent_data[-1]["quantity"]
                week_ago = recent_data[-7]["quantity"] if len(recent_data) > 7 else last_quantity
                month_ago = recent_data[0]["quantity"] if recent_data else last_quantity

                features.extend([last_quantity, week_ago, month_ago])

                # حساب المتوسطات المتحركة
                quantities = [d["quantity"] for d in recent_data[-7:]]
                rolling_mean = np.mean(quantities)
                rolling_std = np.std(quantities)

                features.extend([rolling_mean, rolling_std])
            else:
                features.extend([0, 0, 0, 0, 0])

            # المعامل الموسمي
            seasonal_multiplier = self._get_seasonal_multiplier(forecast_date, seasonal_patterns)
            features.append(seasonal_multiplier)

            return np.array(features)

        except Exception as e:
            self.logger.error(f"Error getting forecast features: {e}")
            return np.array([0] * 11)

    def _calculate_confidence_interval(self, X: np.ndarray, y: np.ndarray, prediction: float) -> Tuple[float, float]:
        """حساب فترة الثقة للتنبؤ"""
        try:
            # استخدام الانحراف المعياري للهدف كتقدير للخطأ
            y_std = np.std(y)

            # فترة ثقة 95%
            margin = 1.96 * y_std

            lower_bound = max(0, prediction - margin)
            upper_bound = prediction + margin

            return (float(lower_bound), float(upper_bound))

        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {e}")
            return (max(0, prediction * 0.8), prediction * 1.2)

    def _evaluate_model_accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        """تقييم دقة النموذج"""
        try:
            if self.demand_model is None:
                return 0

            # تقييم باستخدام cross-validation
            cv_val = min(3, len(X))
            if cv_val >= 2:
                scores = cross_val_score(self.demand_model, X, y, cv=cv_val, scoring="r2")
                return float(np.mean(scores))
            else:
                from sklearn.metrics import r2_score
                return float(r2_score(y, self.demand_model.predict(X)))

        except Exception as e:
            self.logger.error(f"Error evaluating model accuracy: {e}")
            return 0

    def _analyze_demand_factors(
        self,
        product_id: int,
        historical_data: List[Dict[str, Any]],
        seasonal_patterns: SeasonalPattern,
    ) -> Dict[str, Any]:
        """تحليل العوامل المؤثرة على الطلب"""
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
            factors["day_variation_coefficient"] = float(weekday_avg.std() / weekday_avg.mean())

            # قوة النمط الموسمي
            factors["seasonality_strength"] = seasonal_patterns.seasonality_strength

            # اتجاه الطلب
            if len(df) > 30:
                recent_avg = df["quantity"].tail(30).mean()
                older_avg = df["quantity"].head(len(df) - 30).mean()

                if older_avg > 0:
                    trend = (recent_avg - older_avg) / older_avg
                    factors["demand_trend"] = float(trend)
                    factors["trend_direction"] = (
                        "increasing" if trend > 0.05 else "decreasing" if trend < -0.05 else "stable"
                    )

        except Exception as e:
            self.logger.error(f"Error analyzing demand factors: {e}")

        return factors

    def _analyze_weekly_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل الأنماط الأسبوعية"""
        try:
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df["day_of_week"] = df["date"].dt.dayofweek

            # حساب متوسط المبيعات لكل يوم من الأسبوع
            weekly_avg = df.groupby("day_of_week")["quantity"].mean()

            # تحديد الأيام ذات المبيعات العالية والمنخفضة
            mean_quantity = weekly_avg.mean()
            std_quantity = weekly_avg.std()

            high_threshold = mean_quantity + (std_quantity * 0.5)
            low_threshold = mean_quantity - (std_quantity * 0.5)

            peaks = [f"day_{int(day)}" for day, qty in weekly_avg.items() if qty > high_threshold]
            lows = [f"day_{int(day)}" for day, qty in weekly_avg.items() if qty < low_threshold]

            # حساب قوة النمط الموسمي
            strength = std_quantity / mean_quantity if mean_quantity > 0 else 0

            return {
                "peaks": peaks,
                "lows": lows,
                "strength": float(strength),
                "daily_averages": weekly_avg.to_dict(),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing weekly patterns: {e}")
            return {"peaks": [], "lows": [], "strength": 0, "daily_averages": {}}

    def _analyze_monthly_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل الأنماط الشهرية"""
        try:
            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.month

            # حساب متوسط المبيعات لكل شهر
            monthly_avg = df.groupby("month")["quantity"].mean()

            # تحديد الأشهر ذات المبيعات العالية والمنخفضة
            mean_quantity = monthly_avg.mean()
            std_quantity = monthly_avg.std()

            high_threshold = mean_quantity + (std_quantity * 0.5)
            low_threshold = mean_quantity - (std_quantity * 0.5)

            peaks = [f"month_{int(month)}" for month, qty in monthly_avg.items() if qty > high_threshold]
            lows = [f"month_{int(month)}" for month, qty in monthly_avg.items() if qty < low_threshold]

            # حساب قوة النمط الموسمي
            strength = std_quantity / mean_quantity if mean_quantity > 0 else 0

            return {
                "peaks": peaks,
                "lows": lows,
                "strength": float(strength),
                "monthly_averages": monthly_avg.to_dict(),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing monthly patterns: {e}")
            return {"peaks": [], "lows": [], "strength": 0, "monthly_averages": {}}

    def _get_seasonal_multiplier(self, target_date: datetime, seasonal_pattern: SeasonalPattern) -> float:
        """الحصول على المعامل الموسمي لتاريخ محدد"""
        try:
            if seasonal_pattern.pattern_type == "weekly":
                day_of_week = target_date.weekday()
                day_key = f"day_{day_of_week}"

                if day_key in seasonal_pattern.peak_periods:
                    return 1.2  # زيادة 20% في الأيام ذات الذروة
                elif day_key in seasonal_pattern.low_periods:
                    return 0.8  # انخفاض 20% في الأيام المنخفضة
                else:
                    return 1.0

            elif seasonal_pattern.pattern_type == "monthly":
                month = target_date.month
                month_key = f"month_{month}"

                if month_key in seasonal_pattern.peak_periods:
                    return 1.3  # زيادة 30% في الأشهر ذات الذروة
                elif month_key in seasonal_pattern.low_periods:
                    return 0.7  # انخفاض 30% في الأشهر المنخفضة
                else:
                    return 1.0

            else:
                return 1.0

        except Exception as e:
            self.logger.error(f"Error getting seasonal multiplier: {e}")
            return 1.0

    def _simple_demand_forecast(self, product_id: int, days_ahead: int) -> DemandForecast:
        """تنبؤ بسيط بالطلب عندما تكون البيانات محدودة"""
        try:
            recent_data = self._get_demand_history(product_id, days=30)
            avg_demand = np.mean([d["quantity"] for d in recent_data]) if recent_data else 0

            return DemandForecast(
                product_id=product_id,
                forecast_date=datetime.now() + timedelta(days=days_ahead),
                predicted_demand=float(avg_demand),
                confidence_interval=(max(0, avg_demand * 0.7), avg_demand * 1.3),
                accuracy_score=0.5,
                factors={"method": "simple_average", "data_points": len(recent_data)},
            )

        except Exception as e:  # noqa: F841
            return DemandForecast(
                product_id=product_id,
                forecast_date=datetime.now() + timedelta(days=days_ahead),
                predicted_demand=0,
                confidence_interval=(0, 0),
                accuracy_score=0,
                factors={"error": "no_data"},
            )

    def _fallback_demand_forecast(self, product_id: int, days_ahead: int) -> DemandForecast:
        """تنبؤ احتياطي في حالة الخطأ"""
        return DemandForecast(
            product_id=product_id,
            forecast_date=datetime.now() + timedelta(days=days_ahead),
            predicted_demand=0,
            confidence_interval=(0, 0),
            accuracy_score=0,
            factors={"method": "fallback", "reason": "error"},
        )

    def _get_product_inventory_data(self, product_id: int) -> Dict[str, Any]:
        """الحصول على بيانات مخزون المنتج"""
        try:
            query = """
                SELECT current_stock, min_stock, max_stock
                FROM products
                WHERE id = ?
            """

            data = self.db.execute_query(query, (product_id,), fetch_one=True)

            return {
                "current_stock": data[0] if data else 0,
                "min_stock": data[1] if data else 0,
                "max_stock": data[2] if data else 0,
                "lead_time_days": 7,  # قيمة افتراضية، يمكن تخصيصها
            }

        except Exception as e:
            self.logger.error(f"Error getting product inventory data: {e}")
            return {
                "current_stock": 0,
                "min_stock": 0,
                "max_stock": 0,
                "lead_time_days": 7,
            }

    def _calculate_demand_std(self, product_id: int) -> float:
        """حساب انحراف معياري الطلب"""
        try:
            historical_data = self._get_demand_history(product_id, days=90)
            quantities = [d["quantity"] for d in historical_data]

            return np.std(quantities) if quantities else 0

        except Exception as e:
            self.logger.error(f"Error calculating demand std: {e}")
            return 0

    def _get_safety_factor(self, service_level: float) -> float:
        """الحصول على معامل الأمان بناءً على مستوى الخدمة"""
        # جدول تقريبي لمعامل الأمان
        safety_factors = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}

        # إيجاد أقرب قيمة
        closest_level = min(safety_factors.keys(), key=lambda x: abs(x - service_level))
        return safety_factors[closest_level]

    def _load_prediction_models(self):
        """تحميل نماذج التنبؤ المدربة"""
        try:
            # في التطبيق الحقيقي، سنحمل النماذج من الملفات
            pass
        except Exception as e:
            self.logger.error(f"Error loading prediction models: {e}")

    def update_prediction_models(self):
        """تحديث نماذج التنبؤ بالبيانات الجديدة"""
        try:
            self.logger.info("Updating prediction models with latest data...")

            # تحديث نموذج الطلب
            all_products = self._get_all_products()
            for product in all_products[:5]:  # تدريب على أول 5 منتجات للاختبار
                demand_data = self._get_demand_history(product["id"], days=180)
                if len(demand_data) >= self.min_training_samples:
                    seasonal_patterns = self._analyze_seasonal_patterns(demand_data)
                    X, y = self._prepare_demand_training_data(demand_data, seasonal_patterns)
                    if len(X) > 0:
                        self.demand_model = self._select_best_model(X, y)

            self.logger.info("Prediction models updated successfully")

        except Exception as e:
            self.logger.error(f"Error updating prediction models: {e}")

    def _get_all_products(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المنتجات"""
        try:
            query = "SELECT id, name FROM products WHERE is_active = 1"
            data = self.db.execute_query(query, fetch_all=True)

            return [{"id": row.get('id'), "name": row.get('name')} for row in data]

        except Exception as e:
            self.logger.error(f"Error getting all products: {e}")
            return []
