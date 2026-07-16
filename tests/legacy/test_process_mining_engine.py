#!/usr/bin/env python3
"""
اختبارات Process Mining Engine
"""

from datetime import datetime

import pytest

from src.ai.process_mining_engine import (
    EventType,
    ProcessEvent,
    ProcessMiningEngine,
    ProcessModel,
    ProcessType,
)


class TestProcessMiningEngine:
    """اختبارات محرك استخراج العمليات"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك للاختبارات"""
        return ProcessMiningEngine()

    @pytest.fixture
    def sample_events(self):
        """إنشاء أحداث نموذجية"""
        return [
            ProcessEvent(
                event_id="e1",
                case_id="case_1",
                activity="start",
                timestamp=datetime(2025, 1, 1, 10, 0),
                event_type=EventType.START,
            ),
            ProcessEvent(
                event_id="e2",
                case_id="case_1",
                activity="process",
                timestamp=datetime(2025, 1, 1, 10, 5),
                event_type=EventType.NORMAL,
            ),
            ProcessEvent(
                event_id="e3",
                case_id="case_1",
                activity="complete",
                timestamp=datetime(2025, 1, 1, 10, 10),
                event_type=EventType.COMPLETE,
            ),
        ]

    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert hasattr(engine, "event_logs")
        assert hasattr(engine, "process_models")
        assert hasattr(engine, "logger")

    def test_load_event_log(self, engine, sample_events):
        """اختبار تحميل سجل الأحداث"""
        result = engine.load_event_log("log_001", sample_events)

        assert result is not None
        assert result["status"] == "loaded"
        assert result["log_id"] == "log_001"
        assert result["events_count"] == 3
        assert result["cases_count"] >= 1
        assert result["activities_count"] >= 1
        assert "log_001" in engine.event_logs

    def test_discover_process_model(self, engine, sample_events):
        """اختبار استخراج نموذج العملية"""
        engine.load_event_log("log_001", sample_events)

        process_id = engine.discover_process_model("log_001", ProcessType.SALES)

        assert process_id is not None
        assert process_id.startswith("process_log_001")
        assert process_id in engine.process_models

        model = engine.process_models[process_id]
        assert model.process_type == ProcessType.SALES
        assert len(model.activities) >= 1

    def test_discover_process_model_invalid_log(self, engine):
        """اختبار استخراج نموذج من سجل غير موجود"""
        with pytest.raises(ValueError):
            engine.discover_process_model("invalid_log")

    def test_analyze_process_performance(self, engine, sample_events):
        """اختبار تحليل أداء العملية"""
        engine.load_event_log("log_001", sample_events)
        process_id = engine.discover_process_model("log_001")

        result = engine.analyze_process_performance(process_id)

        assert result is not None
        assert "process_id" in result
        assert "cycle_time" in result
        assert "throughput" in result
        assert "bottlenecks" in result
        assert "recommendations" in result

    def test_analyze_process_performance_invalid(self, engine):
        """اختبار تحليل أداء عملية غير موجودة"""
        with pytest.raises(ValueError):
            engine.analyze_process_performance("invalid_process")

    def test_compare_process_variants(self, engine, sample_events):
        """اختبار مقارنة متغيرات العملية"""
        # إضافة أحداث إضافية لمتغير آخر
        variant_2_events = [
            ProcessEvent(
                event_id="e4",
                case_id="case_2",
                activity="start",
                timestamp=datetime(2025, 1, 1, 11, 0),
                event_type=EventType.START,
            ),
            ProcessEvent(
                event_id="e5",
                case_id="case_2",
                activity="alternate_process",
                timestamp=datetime(2025, 1, 1, 11, 5),
                event_type=EventType.NORMAL,
            ),
            ProcessEvent(
                event_id="e6",
                case_id="case_2",
                activity="complete",
                timestamp=datetime(2025, 1, 1, 11, 10),
                event_type=EventType.COMPLETE,
            ),
        ]

        all_events = sample_events + variant_2_events
        engine.load_event_log("log_001", all_events)
        process_id = engine.discover_process_model("log_001")

        result = engine.compare_process_variants(process_id)

        assert result is not None
        assert "process_id" in result
        assert "variant_count" in result

    def test_detect_process_anomalies(self, engine):
        """اختبار كشف شذوذ العملية"""
        # إنشاء أحداث مع شذوذ (وقت طويل جداً)
        anomalous_events = [
            ProcessEvent(
                event_id="e1",
                case_id="case_1",
                activity="start",
                timestamp=datetime(2025, 1, 1, 10, 0),
                event_type=EventType.START,
            ),
            ProcessEvent(
                event_id="e2",
                case_id="case_1",
                activity="process",
                timestamp=datetime(2025, 1, 1, 15, 0),  # 5 ساعات فرق
                event_type=EventType.NORMAL,
            ),
            ProcessEvent(
                event_id="e3",
                case_id="case_1",
                activity="complete",
                timestamp=datetime(2025, 1, 1, 20, 0),
                event_type=EventType.COMPLETE,
            ),
        ]

        engine.load_event_log("log_001", anomalous_events)
        process_id = engine.discover_process_model("log_001")

        result = engine.detect_process_anomalies(process_id)

        assert result is not None
        assert "process_id" in result
        assert "anomalies_detected" in result
        assert "anomaly_list" in result

    def test_generate_process_report(self, engine, sample_events):
        """اختبار توليد تقرير العملية"""
        engine.load_event_log("log_001", sample_events)
        process_id = engine.discover_process_model("log_001")

        result = engine.generate_process_report(process_id)

        assert result is not None
        assert "process_id" in result
        assert "process_type" in result
        assert "activities" in result
        assert "transitions" in result
        assert "bottlenecks" in result
        assert "variants" in result
        assert "performance_metrics" in result
        assert "generated_at" in result

    def test_analyze_event_log(self, engine, sample_events):
        """اختبار تحليل سجل الأحداث"""
        analysis = engine._analyze_event_log(sample_events)

        assert analysis is not None
        assert "cases_count" in analysis
        assert "activities_count" in analysis
        assert "events_count" in analysis
        assert "avg_case_duration" in analysis

    def test_extract_activities_and_transitions(self, engine, sample_events):
        """اختبار استخراج الأنشطة والانتقالات"""
        model = ProcessModel("test_process", ProcessType.SALES)

        engine._extract_activities_and_transitions(sample_events, model)

        assert len(model.activities) >= 1
        assert len(model.transitions) >= 1

    def test_identify_start_end_activities(self, engine, sample_events):
        """اختبار تحديد أنشطة البداية والنهاية"""
        model = ProcessModel("test_process", ProcessType.SALES)

        engine._identify_start_end_activities(sample_events, model)

        assert len(model.start_activities) >= 1
        assert len(model.end_activities) >= 1

    def test_discover_bottlenecks(self, engine):
        """اختبار اكتشاف الاختناقات"""
        # أحداث مع اختناق واضح
        events = [
            ProcessEvent(
                event_id="e1",
                case_id="case_1",
                activity="start",
                timestamp=datetime(2025, 1, 1, 10, 0),
                event_type=EventType.START,
            ),
            ProcessEvent(
                event_id="e2",
                case_id="case_1",
                activity="bottleneck_activity",
                timestamp=datetime(2025, 1, 1, 10, 30),  # 30 دقيقة
                event_type=EventType.NORMAL,
            ),
            ProcessEvent(
                event_id="e3",
                case_id="case_1",
                activity="complete",
                timestamp=datetime(2025, 1, 1, 10, 35),
                event_type=EventType.COMPLETE,
            ),
        ]

        bottlenecks = engine._discover_bottlenecks(events)

        assert isinstance(bottlenecks, list)
        # قد يكتشف الاختناق أو لا حسب المنطق

    def test_calculate_performance_metrics(self, engine, sample_events):
        """اختبار حساب مقاييس الأداء"""
        metrics = engine._calculate_performance_metrics(sample_events)

        assert metrics is not None
        assert "total_cases" in metrics
        assert "total_events" in metrics
        assert "avg_case_duration" in metrics

    def test_generate_performance_recommendations(self, engine, sample_events):
        """اختبار توليد توصيات الأداء"""
        engine.load_event_log("log_001", sample_events)
        process_id = engine.discover_process_model("log_001")
        model = engine.process_models[process_id]

        recommendations = engine._generate_performance_recommendations(model)

        assert isinstance(recommendations, list)


class TestProcessEvent:
    """اختبارات حدث العملية"""

    def test_process_event_creation(self):
        """اختبار إنشاء حدث عملية"""
        event = ProcessEvent(
            event_id="e1",
            case_id="case_1",
            activity="start",
            timestamp=datetime(2025, 1, 1, 10, 0),
            event_type=EventType.START,
            resource="user_1",
            attributes={"priority": "high"},
        )

        assert event.event_id == "e1"
        assert event.case_id == "case_1"
        assert event.activity == "start"
        assert event.event_type == EventType.START
        assert event.resource == "user_1"
        assert event.attributes["priority"] == "high"


class TestProcessModel:
    """اختبارات نموذج العملية"""

    def test_process_model_creation(self):
        """اختبار إنشاء نموذج العملية"""
        model = ProcessModel(process_id="process_001", process_type=ProcessType.SALES)

        assert model.process_id == "process_001"
        assert model.process_type == ProcessType.SALES
        assert isinstance(model.activities, set)
        assert isinstance(model.transitions, dict)
        assert isinstance(model.bottlenecks, list)
        assert isinstance(model.variants, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
