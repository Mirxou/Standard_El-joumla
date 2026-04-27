#!/usr/bin/env python3
"""
اختبارات RPA System
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.ai.rpa_system import RPASystem, AutomationScript, AutomationResult, TaskType


class TestRPASystem:
    """اختبارات نظام RPA"""
    
    @pytest.fixture
    def rpa(self):
        """إنشاء نظام RPA للاختبارات"""
        return RPASystem()
    
    def test_initialization(self, rpa):
        """اختبار تهيئة النظام"""
        assert rpa is not None
        assert hasattr(rpa, 'scripts')
        assert hasattr(rpa, 'running_tasks')
        assert hasattr(rpa, 'task_history')
    
    def test_create_automation_script(self, rpa):
        """اختبار إنشاء سكربت أتمتة"""
        script = rpa.create_script(
            script_id="script_001",
            name="Data Entry Automation",
            task_type=TaskType.DATA_ENTRY,
            steps=[
                {"action": "open_app", "target": "Excel"},
                {"action": "read_data", "source": "database"},
                {"action": "enter_data", "target": "Excel"}
            ]
        )
        
        assert script is not None
        assert isinstance(script, AutomationScript)
        assert script.script_id == "script_001"
        assert script.name == "Data Entry Automation"
        assert script.task_type == TaskType.DATA_ENTRY
        assert len(script.steps) == 3
        assert "script_001" in rpa.scripts
    
    def test_execute_script(self, rpa):
        """اختبار تنفيذ سكربت"""
        rpa.create_script("script_001", "Test Script", TaskType.DATA_ENTRY, [
            {"action": "test", "target": "test_target"}
        ])
        
        result = rpa.execute_script("script_001", parameters={"input": "test"})
        
        assert result is not None
        assert isinstance(result, AutomationResult)
        assert result.script_id == "script_001"
        assert result.status in ["success", "failed", "running"]
    
    def test_execute_nonexistent_script(self, rpa):
        """اختبار تنفيذ سكربت غير موجود"""
        result = rpa.execute_script("nonexistent_script")
        
        assert result is not None
        assert result.status == "failed"
    
    def test_get_script_status(self, rpa):
        """اختبار الحصول على حالة السكربت"""
        rpa.create_script("script_001", "Test", TaskType.DATA_ENTRY, [])
        execution = rpa.execute_script("script_001")
        
        status = rpa.get_script_status(execution.execution_id)
        
        assert status is not None
        assert "execution_id" in status
        assert "script_id" in status
        assert "status" in status
    
    def test_stop_script(self, rpa):
        """اختبار إيقاف سكربت"""
        rpa.create_script("script_001", "Test", TaskType.DATA_ENTRY, [])
        execution = rpa.execute_script("script_001")
        
        result = rpa.stop_script(execution.execution_id)
        
        assert result is True
    
    def test_get_script_history(self, rpa):
        """اختبار الحصول على سجل السكربتات"""
        # تنفيذ عدة سكربتات
        rpa.create_script("script_001", "Test 1", TaskType.DATA_ENTRY, [])
        rpa.create_script("script_002", "Test 2", TaskType.REPORT_GENERATION, [])
        
        for i in range(3):
            rpa.execute_script("script_001")
        
        history = rpa.get_script_history(script_id="script_001")
        
        assert isinstance(history, list)
        assert len(history) >= 3
    
    def test_schedule_script(self, rpa):
        """اختبار جدولة سكربت"""
        rpa.create_script("script_001", "Test", TaskType.DATA_ENTRY, [])
        
        schedule = rpa.schedule_script(
            script_id="script_001",
            schedule_time=datetime.now() + timedelta(hours=1),
            recurrence="daily"
        )
        
        assert schedule is not None
        assert "schedule_id" in schedule
        assert "script_id" in schedule
        assert schedule["script_id"] == "script_001"
    
    def test_record_script(self, rpa):
        """اختبار تسجيل سكربت"""
        actions = [
            {"action": "click", "target": "button_1"},
            {"action": "type", "target": "input_1", "value": "test"},
            {"action": "click", "target": "button_2"}
        ]
        
        script = rpa.record_script(
            script_id="recorded_001",
            name="Recorded Script",
            actions=actions
        )
        
        assert script is not None
        assert script.script_id == "recorded_001"
        assert len(script.steps) == 3
    
    def test_delete_script(self, rpa):
        """اختبار حذف سكربت"""
        rpa.create_script("script_001", "Test", TaskType.DATA_ENTRY, [])
        
        assert "script_001" in rpa.scripts
        
        result = rpa.delete_script("script_001")
        
        assert result is True
        assert "script_001" not in rpa.scripts
    
    def test_delete_nonexistent_script(self, rpa):
        """اختبار حذف سكربت غير موجود"""
        result = rpa.delete_script("nonexistent_script")
        
        assert result is False
    
    def test_clone_script(self, rpa):
        """اختبار استنساخ سكربت"""
        rpa.create_script("script_001", "Original", TaskType.DATA_ENTRY, [
            {"action": "step1"},
            {"action": "step2"}
        ])
        
        cloned = rpa.clone_script("script_001", "script_002", "Cloned Script")
        
        assert cloned is not None
        assert cloned.script_id == "script_002"
        assert cloned.name == "Cloned Script"
        assert len(cloned.steps) == 2
        assert "script_002" in rpa.scripts
    
    def test_get_all_scripts(self, rpa):
        """اختبار الحصول على جميع السكربتات"""
        rpa.create_script("script_001", "Script 1", TaskType.DATA_ENTRY, [])
        rpa.create_script("script_002", "Script 2", TaskType.REPORT_GENERATION, [])
        rpa.create_script("script_003", "Script 3", TaskType.DATA_SYNC, [])
        
        scripts = rpa.get_all_scripts()
        
        assert isinstance(scripts, list)
        assert len(scripts) == 3
    
    def test_validate_script(self, rpa):
        """اختبار التحقق من سكربت"""
        valid_script = AutomationScript(
            script_id="valid_001",
            name="Valid Script",
            task_type=TaskType.DATA_ENTRY,
            steps=[
                {"action": "open_app", "target": "Excel"},
                {"action": "read_data", "source": "db"}
            ],
            created_at=datetime.now()
        )
        
        result = rpa.validate_script(valid_script)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "valid" in result or "is_valid" in result
    
    def test_different_task_types(self, rpa):
        """اختبار أنواع مختلفة من المهام"""
        task_types = [
            TaskType.DATA_ENTRY,
            TaskType.DATA_EXTRACTION,
            TaskType.REPORT_GENERATION,
            TaskType.DATA_SYNC,
            TaskType.EMAIL_PROCESSING,
            TaskType.FILE_PROCESSING
        ]
        
        for i, task_type in enumerate(task_types):
            script = rpa.create_script(
                f"script_{i}",
                f"Script {task_type.value}",
                task_type,
                [{"action": "test"}]
            )
            
            assert script.task_type == task_type


class TestAutomationScript:
    """اختبارات سكربت الأتمتة"""
    
    def test_automation_script_creation(self):
        """اختبار إنشاء سكربت الأتمتة"""
        script = AutomationScript(
            script_id="script_001",
            name="Test Script",
            task_type=TaskType.DATA_ENTRY,
            steps=[
                {"action": "click", "target": "button"},
                {"action": "type", "target": "input", "value": "test"}
            ],
            created_at=datetime.now(),
            modified_at=datetime.now(),
            version="1.0"
        )
        
        assert script.script_id == "script_001"
        assert script.name == "Test Script"
        assert len(script.steps) == 2
        assert script.version == "1.0"


class TestAutomationResult:
    """اختبارات نتيجة الأتمتة"""
    
    def test_automation_result_creation(self):
        """اختبار إنشاء نتيجة الأتمتة"""
        result = AutomationResult(
            execution_id="exec_001",
            script_id="script_001",
            status="success",
            output={"records_processed": 100},
            execution_time=15.5,
            error_message=None,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        assert result.execution_id == "exec_001"
        assert result.status == "success"
        assert result.output["records_processed"] == 100
        assert result.execution_time == 15.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



