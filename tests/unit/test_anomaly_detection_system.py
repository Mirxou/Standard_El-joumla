#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Anomaly Detection System
اختبارات نظام اكتشاف الشذوذ
"""

from datetime import datetime, timedelta

import pytest

from src.ai.anomaly_detection_system import AnomalyDetectionSystem, SeverityLevel


class TestSeverityLevel:
    """اختبارات مستويات الخطورة"""

    def test_severity_level_values(self):
        """اختبار قيم مستويات الخطورة"""
        assert SeverityLevel.LOW.value == "low"
        assert SeverityLevel.MEDIUM.value == "medium"
        assert SeverityLevel.HIGH.value == "high"
        assert SeverityLevel.CRITICAL.value == "critical"


class TestAnomalyDetectionSystem:
    """اختبارات نظام اكتشاف الشذوذ"""

    @pytest.fixture
    def detector(self):
        """إنشاء Anomaly Detection System"""
        return AnomalyDetectionSystem()

    def test_initialization(self, detector):
        """اختبار التهيئة"""
        assert detector is not None
        assert detector.baseline_models == {}
        assert isinstance(detector.anomaly_history, dict)
        assert "sales" in detector.alert_thresholds

    def test_update_baseline(self, detector):
        """اختبار تحديث خط الأساس"""
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        detector.update_baseline("test_metric", data)

        assert "test_metric" in detector.baseline_models
        assert detector.baseline_models["test_metric"]["mean"] == 30.0
        assert detector.baseline_models["test_metric"]["sample_size"] == 5

    def test_detect_sales_anomalies(self, detector):
        """اختبار كشف شذوذ المبيعات"""
        sales_data = [
            {"date": "2026-01-01T10:00:00", "amount": 100.0},
            {"date": "2026-01-01T11:00:00", "amount": 5000.0},  # شاذ
            {"date": "2026-01-01T12:00:00", "amount": 150.0},
        ]

        # تعيين خط أساس منخفض لضمان كشف الشذوذ
        detector.baseline_models["sales"] = {"mean": 100.0, "stdev": 20.0}

        result = detector.detect_sales_anomalies(sales_data)

        assert "anomalies" in result
        assert len(result["anomalies"]) > 0
        assert any(a["type"] == "sales_volume" for a in result["anomalies"])

    def test_alert_thresholds(self, detector):
        """اختبار حدود التنبيهات"""
        detector.set_alert_threshold("custom", "high", 5.0)
        thresholds = detector.get_alert_thresholds()

        assert thresholds["custom"]["high"] == 5.0

    def test_reset_baseline(self, detector):
        """اختبار إعادة تعيين خط الأساس"""
        detector.baseline_models["test"] = {"mean": 100}
        detector.reset_baseline("test")
        assert "test" not in detector.baseline_models

    def test_get_anomaly_summary(self, detector):
        """اختبار ملخص الشذوذ"""
        detector.anomaly_history["sales"] = [
            {"timestamp": datetime.now().isoformat(), "severity": "high"},
            {
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                "severity": "low",
            },
        ]

        summary = detector.get_anomaly_summary(days=7)
        assert summary["total_anomalies"] == 1
        assert summary["by_type"]["sales"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
