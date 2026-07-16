#!/usr/bin/env python3
"""
نظام كشف الشذوذ - Anomaly Detection System
نظام ذكي لكشف الأنماط الشاذة والتنبيه عنها
"""

import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List


class SeverityLevel(Enum):
    """مستوى الشدة"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyDetectionSystem:
    """نظام كشف الشذوذ المتقدم"""

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.baseline_models = {}
        self.anomaly_history = defaultdict(list)
        self.alert_thresholds = self._load_default_thresholds()

    def perform_comprehensive_anomaly_detection(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """إجراء كشف شامل للشذوذ"""
        context = context or {}
        sales_anomalies = self.detect_sales_anomalies([])  # تمرير قائمة فارغة للمحاكاة
        inventory_anomalies = self.detect_inventory_anomalies([])
        transaction_anomalies = self.detect_transaction_anomalies([])
        user_anomalies = self.detect_user_behavior_anomalies([])

        total_anomalies = (
            len(sales_anomalies["anomalies"])
            + len(inventory_anomalies["anomalies"])
            + len(transaction_anomalies["anomalies"])
            + len(user_anomalies["anomalies"])
        )

        return {
            "total_anomalies_detected": total_anomalies,
            "sales_anomalies": sales_anomalies,
            "inventory_anomalies": inventory_anomalies,
            "transaction_anomalies": transaction_anomalies,
            "user_anomalies": user_anomalies,
            "timestamp": datetime.now().isoformat(),
        }

    def detect_real_time_anomalies(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """كشف الشذوذ في الوقت الفعلي"""
        # محاكاة كشف الشذوذ في المقاييس
        detected = []
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage > 90:
            detected.append(
                {
                    "type": "high_cpu",
                    "severity": "high",
                    "description": f"استخدام CPU مرتفع جداً: {cpu_usage}%",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return {
            "detected_anomalies": detected,
            "anomaly_count": len(detected),
            "status": "warning" if detected else "healthy",
        }

    def detect_sales_anomalies(self, current_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """كشف شذوذ المبيعات"""
        anomalies = []

        # تحليل المبيعات اليومية
        daily_sales = self._aggregate_daily_sales(current_data)
        baseline = self._get_baseline("sales")

        for date, amount in daily_sales.items():
            anomaly_score = self._calculate_anomaly_score(amount, baseline)

            if anomaly_score > self.alert_thresholds["sales"]["high"]:
                anomalies.append(
                    {
                        "type": "sales_volume",
                        "date": date,
                        "value": amount,
                        "expected": baseline["mean"],
                        "deviation": amount - baseline["mean"],
                        "severity": "high",
                        "score": anomaly_score,
                        "description": f"مبيعات استثنائية: {amount:.2f} (متوقع: {baseline['mean']:.2f})",
                    }
                )
            elif anomaly_score > self.alert_thresholds["sales"]["medium"]:
                anomalies.append(
                    {
                        "type": "sales_volume",
                        "date": date,
                        "value": amount,
                        "expected": baseline["mean"],
                        "deviation": amount - baseline["mean"],
                        "severity": "medium",
                        "score": anomaly_score,
                        "description": f"مبيعات غير طبيعية: {amount:.2f}",
                    }
                )

        return {
            "anomalies": anomalies,
            "total_analyzed": len(daily_sales),
            "anomaly_rate": len(anomalies) / len(daily_sales) if daily_sales else 0,
            "most_severe": (max(anomalies, key=lambda x: x["score"]) if anomalies else None),
            "recommendations": self._generate_anomaly_recommendations(anomalies, "sales"),
        }

    def detect_inventory_anomalies(self, inventory_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """كشف شذوذ المخزون"""
        anomalies = []

        # تجميع بيانات المخزون حسب المنتج
        product_inventory = defaultdict(list)
        for item in inventory_data:
            product_inventory[item["product"]].append(item)

        for product, records in product_inventory.items():
            baseline = self._get_baseline(f"inventory_{product}")

            for record in records:
                stock_level = record.get("stock_level", 0)
                anomaly_score = self._calculate_anomaly_score(stock_level, baseline)

                if anomaly_score > self.alert_thresholds["inventory"]["high"]:
                    anomalies.append(
                        {
                            "type": "inventory_level",
                            "product": product,
                            "date": record.get("date"),
                            "value": stock_level,
                            "expected": baseline["mean"],
                            "severity": "high",
                            "score": anomaly_score,
                            "description": f"مستوى مخزون استثنائي لـ {product}: {stock_level}",
                        }
                    )

                # كشف نقص المخزون
                reorder_point = record.get("reorder_point", 20)
                if stock_level <= reorder_point and stock_level > 0:
                    anomalies.append(
                        {
                            "type": "low_inventory",
                            "product": product,
                            "date": record.get("date"),
                            "value": stock_level,
                            "threshold": reorder_point,
                            "severity": "medium",
                            "score": 0.7,
                            "description": f"مخزون منخفض لـ {product}: {stock_level} (نقطة إعادة الطلب: {reorder_point})",  # noqa: E501
                        }
                    )

        return {
            "anomalies": anomalies,
            "products_analyzed": len(product_inventory),
            "anomaly_rate": (len(anomalies) / len(product_inventory) if product_inventory else 0),
            "recommendations": self._generate_anomaly_recommendations(anomalies, "inventory"),
        }

    def detect_transaction_anomalies(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """كشف شذوذ المعاملات"""
        anomalies = []

        baseline = self._get_baseline("transactions")

        for transaction in transactions:
            amount = transaction.get("amount", 0)
            anomaly_score = self._calculate_anomaly_score(amount, baseline)

            # كشف معاملات كبيرة جداً
            if anomaly_score > self.alert_thresholds["transactions"]["high"]:
                anomalies.append(
                    {
                        "type": "large_transaction",
                        "transaction_id": transaction.get("id"),
                        "amount": amount,
                        "expected": baseline["mean"],
                        "severity": "high",
                        "score": anomaly_score,
                        "description": f"معاملة كبيرة جداً: {amount:.2f}",
                    }
                )

            # كشف معاملات مشبوهة (نمط غير طبيعي)
            if self._is_suspicious_pattern(transaction):
                anomalies.append(
                    {
                        "type": "suspicious_pattern",
                        "transaction_id": transaction.get("id"),
                        "amount": amount,
                        "severity": "high",
                        "score": 0.9,
                        "description": "نمط معاملة مشبوه",
                    }
                )

        return {
            "anomalies": anomalies,
            "transactions_analyzed": len(transactions),
            "anomaly_rate": len(anomalies) / len(transactions) if transactions else 0,
            "recommendations": self._generate_anomaly_recommendations(anomalies, "transactions"),
        }

    def detect_user_behavior_anomalies(self, user_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """كشف شذوذ سلوك المستخدمين"""
        anomalies = []

        # تجميع الأنشطة حسب المستخدم
        user_activities = defaultdict(list)
        for action in user_actions:
            user_activities[action["user_id"]].append(action)

        for user_id, actions in user_activities.items():
            baseline = self._get_baseline(f"user_{user_id}")

            # تحليل تردد الأنشطة
            activity_count = len(actions)
            anomaly_score = self._calculate_anomaly_score(activity_count, baseline)

            if anomaly_score > self.alert_thresholds["user_behavior"]["high"]:
                anomalies.append(
                    {
                        "type": "unusual_activity",
                        "user_id": user_id,
                        "activity_count": activity_count,
                        "expected": baseline["mean"],
                        "severity": "high",
                        "score": anomaly_score,
                        "description": f"نشاط غير طبيعي للمستخدم {user_id}: {activity_count} عملية",
                    }
                )

            # كشف أنماط مشبوهة
            suspicious_patterns = self._detect_suspicious_user_patterns(actions)
            for pattern in suspicious_patterns:
                anomalies.append(
                    {
                        "type": "suspicious_user_pattern",
                        "user_id": user_id,
                        "pattern": pattern["type"],
                        "severity": "medium",
                        "score": 0.8,
                        "description": f"نمط مشبوه: {pattern['description']}",
                    }
                )

        return {
            "anomalies": anomalies,
            "users_analyzed": len(user_activities),
            "anomaly_rate": (len(anomalies) / len(user_activities) if user_activities else 0),
            "recommendations": self._generate_anomaly_recommendations(anomalies, "user_behavior"),
        }

    def update_baseline(self, data_type: str, data: List[float]):
        """تحديث خط الأساس لنوع البيانات"""
        if len(data) < 3:
            return

        self.baseline_models[data_type] = {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "last_updated": datetime.now(),
            "sample_size": len(data),
        }

    def get_anomaly_summary(self, days: int = 7) -> Dict[str, Any]:
        """ملخص الشذوذ لفترة زمنية"""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_anomalies = {}
        for anomaly_type, anomalies in self.anomaly_history.items():
            recent_anomalies[anomaly_type] = [
                a for a in anomalies if datetime.fromisoformat(a.get("timestamp", "2000-01-01")) > cutoff_date
            ]

        return {
            "period_days": days,
            "total_anomalies": sum(len(anoms) for anoms in recent_anomalies.values()),
            "by_type": {k: len(v) for k, v in recent_anomalies.items()},
            "severity_distribution": self._calculate_severity_distribution(recent_anomalies),
            "trend": self._calculate_anomaly_trend(recent_anomalies, days),
        }

    def _load_default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """تحميل الحدود الافتراضية للتنبيهات"""
        return {
            "sales": {"low": 1.5, "medium": 2.0, "high": 2.5},  # انحراف معياري
            "inventory": {"low": 1.0, "medium": 1.5, "high": 2.0},
            "transactions": {"low": 2.0, "medium": 3.0, "high": 4.0},
            "user_behavior": {"low": 1.5, "medium": 2.0, "high": 2.5},
        }

    def _aggregate_daily_sales(self, sales_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """تجميع المبيعات يومياً"""
        daily_totals = defaultdict(float)

        for sale in sales_data:
            date = datetime.fromisoformat(sale["date"]).date().isoformat()
            daily_totals[date] += sale.get("amount", 0)

        return dict(daily_totals)

    def _get_baseline(self, data_type: str) -> Dict[str, float]:
        """الحصول على خط الأساس"""
        if data_type in self.baseline_models:
            return self.baseline_models[data_type]

        # خطوط أساس افتراضية
        defaults = {
            "sales": {"mean": 1500.0, "stdev": 300.0},
            "inventory_laptop": {"mean": 25.0, "stdev": 5.0},
            "inventory_phone": {"mean": 40.0, "stdev": 8.0},
            "transactions": {"mean": 150.0, "stdev": 50.0},
            "user_default": {"mean": 10.0, "stdev": 3.0},
        }

        # إنشاء خط أساس عام إذا لم يكن محدد
        if data_type.startswith("inventory_"):
            return defaults.get("inventory_laptop", defaults["inventory_laptop"])
        elif data_type.startswith("user_"):
            return defaults["user_default"]

        return defaults.get(data_type, {"mean": 100.0, "stdev": 20.0})

    def _calculate_anomaly_score(self, value: float, baseline: Dict[str, float]) -> float:
        """حساب درجة الشذوذ"""
        mean = baseline.get("mean", 100.0)
        stdev = baseline.get("stdev", 20.0)

        if stdev == 0:
            return 0.0

        z_score = abs(value - mean) / stdev
        return z_score

    def _is_suspicious_pattern(self, transaction: Dict[str, Any]) -> bool:
        """فحص الأنماط المشبوهة في المعاملات"""
        amount = transaction.get("amount", 0)
        payment_method = transaction.get("payment_method", "")

        # معاملات كبيرة جداً مع طرق دفع غير شائعة
        if amount > 5000 and payment_method in ["cash"]:
            return True

        # معاملات متكررة بنفس المبلغ
        # (في التطبيق الحقيقي، سيتم فحص التاريخ)

        return False

    def _detect_suspicious_user_patterns(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """كشف الأنماط المشبوهة في سلوك المستخدم"""
        patterns = []

        # فحص محاولات تسجيل دخول فاشلة متكررة
        failed_logins = [a for a in actions if a.get("action") == "failed_login"]
        if len(failed_logins) > 5:
            patterns.append(
                {
                    "type": "multiple_failed_logins",
                    "description": f"{len(failed_logins)} محاولة تسجيل دخول فاشلة",
                }
            )

        # فحص الوصول إلى مناطق محظورة
        unauthorized_access = [a for a in actions if a.get("action") == "unauthorized_access"]
        if unauthorized_access:
            patterns.append(
                {
                    "type": "unauthorized_access_attempts",
                    "description": f"{len(unauthorized_access)} محاولة وصول غير مصرح",
                }
            )

        # فحص الأنشطة في أوقات غير طبيعية
        late_night_actions = []
        for action in actions:
            if "timestamp" in action:
                hour = datetime.fromisoformat(action["timestamp"]).hour
                if hour < 6 or hour > 22:  # قبل 6 صباحاً أو بعد 10 مساءً
                    late_night_actions.append(action)

        if len(late_night_actions) > len(actions) * 0.3:  # أكثر من 30%
            patterns.append(
                {
                    "type": "unusual_timing",
                    "description": f"{len(late_night_actions)} نشاط في أوقات غير طبيعية",
                }
            )

        return patterns

    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]], anomaly_type: str) -> List[str]:
        """توليد توصيات للتعامل مع الشذوذ"""
        recommendations = []

        if not anomalies:
            return ["لا توجد شذوذ كبيرة تحتاج إلى تدخل"]

        high_severity = [a for a in anomalies if a.get("severity") == "high"]

        if anomaly_type == "sales":
            if high_severity:
                recommendations.append("فحص المعاملات ذات المبالغ الاستثنائية للتأكد من صحتها")
            recommendations.append("مراجعة استراتيجية التسعير والعروض الترويجية")

        elif anomaly_type == "inventory":
            recommendations.append("مراجعة سياسات إدارة المخزون ونقاط إعادة الطلب")
            recommendations.append("تحسين التنبؤ بالطلب لتجنب نقص المخزون")

        elif anomaly_type == "transactions":
            recommendations.append("تعزيز التحقق من الهوية للمعاملات الكبيرة")
            recommendations.append("تطبيق حدود على المعاملات اليومية")

        elif anomaly_type == "user_behavior":
            recommendations.append("مراجعة سياسات الأمان وسجلات الوصول")
            recommendations.append("تدريب المستخدمين على الممارسات الأمنية")

        # توصيات عامة
        recommendations.extend(
            [
                "إعداد تنبيهات تلقائية للشذوذ المستقبلي",
                "توثيق الحالات الاستثنائية وأسبابها",
                "مراجعة دورية للحدود والمعايير",
            ]
        )

        return recommendations

    def _calculate_severity_distribution(self, anomalies: Dict[str, List]) -> Dict[str, int]:
        """حساب توزيع الشدة"""
        severity_count = {"low": 0, "medium": 0, "high": 0}

        for anomaly_list in anomalies.values():
            for anomaly in anomaly_list:
                severity = anomaly.get("severity", "low")
                severity_count[severity] += 1

        return severity_count

    def _calculate_anomaly_trend(self, anomalies: Dict[str, List], days: int) -> Dict[str, Any]:
        """حساب اتجاه الشذوذ"""
        # تقسيم الفترة إلى نصفين
        half_days = days // 2
        recent_cutoff = datetime.now() - timedelta(days=half_days)

        recent_count = 0
        older_count = 0

        for anomaly_list in anomalies.values():
            for anomaly in anomaly_list:
                anomaly_date = datetime.fromisoformat(anomaly.get("timestamp", "2000-01-01"))
                if anomaly_date > recent_cutoff:
                    recent_count += 1
                else:
                    older_count += 1

        total_anomalies = recent_count + older_count

        if total_anomalies == 0:
            return {"trend": "stable", "change_percent": 0.0}

        if older_count == 0:
            change_percent = float("inf") if recent_count > 0 else 0.0
        else:
            change_percent = ((recent_count - older_count) / older_count) * 100

        if change_percent > 20:
            trend = "increasing"
        elif change_percent < -20:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "change_percent": change_percent,
            "recent_period": recent_count,
            "older_period": older_count,
        }

    def set_alert_threshold(self, data_type: str, severity: str, threshold: float):
        """تحديد حد التنبيه"""
        if data_type not in self.alert_thresholds:
            self.alert_thresholds[data_type] = {}

        self.alert_thresholds[data_type][severity] = threshold

    def get_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """الحصول على حدود التنبيهات"""
        return self.alert_thresholds.copy()

    def reset_baseline(self, data_type: str):
        """إعادة تعيين خط الأساس"""
        if data_type in self.baseline_models:
            del self.baseline_models[data_type]

    def export_anomaly_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """تصدير تقرير الشذوذ"""
        # جمع الشذوذ في الفترة المحددة
        report_anomalies = {}
        for anomaly_type, anomalies in self.anomaly_history.items():
            report_anomalies[anomaly_type] = [
                a
                for a in anomalies
                if start_date <= datetime.fromisoformat(a.get("timestamp", "2000-01-01")) <= end_date
            ]

        return {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "summary": {
                "total_anomalies": sum(len(anoms) for anoms in report_anomalies.values()),
                "by_type": {k: len(v) for k, v in report_anomalies.items()},
                "severity_breakdown": self._calculate_severity_distribution(report_anomalies),
            },
            "details": report_anomalies,
            "recommendations": [
                "مراجعة دورية للشذوذ المكتشفة",
                "تحديث خطوط الأساس بانتظام",
                "تطوير آليات الاستجابة التلقائية",
            ],
        }
