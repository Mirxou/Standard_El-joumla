#!/usr/bin/env python3
"""
اختبارات Cognitive Automation Engine
"""

from datetime import datetime

import pytest

from src.ai.cognitive_automation_engine import (
    AutomationRule,
    AutomationStatus,
    AutomationTask,
    AutomationType,
    CognitiveAutomationEngine,
)


class TestCognitiveAutomationEngine:
    """اختبارات محرك الأتمتة المعرفية"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك للاختبارات"""
        return CognitiveAutomationEngine()

    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert hasattr(engine, "rules")
        assert hasattr(engine, "tasks")
        assert hasattr(engine, "active_tasks")

    def test_add_rule(self, engine):
        """اختبار إضافة قاعدة أتمتة"""
        rule = AutomationRule(
            rule_id="rule_001",
            name="Test Rule",
            description="Testing rule addition",
            trigger_conditions={"schedule": "daily"},
            actions=[{"type": "send_notification", "message": "test"}],
        )

        result = engine.add_rule(rule)
        assert result["status"] == "added"
        assert "rule_001" in engine.rules

    def test_execute_task(self, engine):
        """اختبار تنفيذ مهمة"""
        task = AutomationTask(
            task_id="task_001",
            automation_type=AutomationType.BUSINESS_PROCESS,
            description="Test task execution",
            parameters={"steps": []},
        )

        result = engine.execute_task(task)
        assert result["status"] == "started"
        assert task.task_id in engine.tasks
        assert task.status in [AutomationStatus.RUNNING, AutomationStatus.COMPLETED]

    def test_get_task_status(self, engine):
        """اختبار الحصول على حالة المهمة"""
        task = AutomationTask(
            task_id="task_002",
            automation_type=AutomationType.DATA_PROCESSING,
            description="Test status",
            parameters={},
        )
        engine.tasks[task.task_id] = task

        status = engine.get_task_status(task.task_id)
        assert status["task_id"] == "task_002"
        assert status["status"] == AutomationStatus.IDLE.value

    def test_remove_rule(self, engine):
        """اختبار إزالة قاعدة أتمتة"""
        rule = AutomationRule(
            rule_id="rule_to_remove",
            name="Remove Me",
            description="Test removal",
            trigger_conditions={},
            actions=[],
        )
        engine.add_rule(rule)

        result = engine.remove_rule("rule_to_remove")
        assert result["status"] == "removed"
        assert "rule_to_remove" not in engine.rules

    def test_get_engine_status(self, engine):
        """اختبار الحصول على حالة المحرك"""
        status = engine.get_engine_status()
        assert "is_running" in status
        assert "rules_count" in status
        assert "active_tasks_count" in status

    def test_start_stop_engine(self, engine):
        """اختبار بدء وإيقاف المحرك"""
        start_res = engine.start_engine()
        assert start_res["status"] == "started"
        assert engine.is_running is True

        stop_res = engine.stop_engine()
        assert stop_res["status"] == "stopped"
        assert engine.is_running is False


class TestAutomationTask:
    """اختبارات مهمة الأتمتة"""

    def test_automation_task_creation(self):
        """اختبار إنشاء مهمة الأتمتة"""
        task = AutomationTask(
            task_id="task_001",
            automation_type=AutomationType.DATA_PROCESSING,
            description="Data processing task",
            parameters={"key": "value"},
            priority=2,
            status=AutomationStatus.IDLE,
            created_at=datetime.now(),
        )

        assert task.task_id == "task_001"
        assert task.automation_type == AutomationType.DATA_PROCESSING
        assert task.status == AutomationStatus.IDLE

    def test_automation_task_default_values(self):
        """اختبار القيم الافتراضية لمهمة الأتمتة"""
        task = AutomationTask(
            task_id="task_002",
            automation_type=AutomationType.REPORTING,
            description="Backup task",
            parameters={},
        )

        assert task.status == AutomationStatus.IDLE
        assert task.priority == 1
        assert task.result is None
        assert task.error_message is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
