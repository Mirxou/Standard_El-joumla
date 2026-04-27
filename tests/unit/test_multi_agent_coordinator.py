#!/usr/bin/env python3
"""
اختبارات Multi Agent Coordinator
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.ai.multi_agent_coordinator import MultiAgentCoordinator, AgentTask, AgentResult


class TestMultiAgentCoordinator:
    """اختبارات منسق الوكلاء المتعددين"""
    
    @pytest.fixture
    def coordinator(self):
        """إنشاء منسق للاختبارات"""
        return MultiAgentCoordinator()
    
    def test_initialization(self, coordinator):
        """اختبار تهيئة المنسق"""
        assert coordinator is not None
        assert hasattr(coordinator, 'agents')
        assert hasattr(coordinator, 'task_queue')
        assert hasattr(coordinator, 'results')
    
    def test_register_agent(self, coordinator):
        """اختبار تسجيل وكيل"""
        agent_config = {
            "name": "sales_analyzer",
            "type": "analyzer",
            "capabilities": ["sales_analysis", "forecasting"]
        }
        
        result = coordinator.register_agent("agent_001", agent_config)
        
        assert result is True
        assert "agent_001" in coordinator.agents
    
    def test_unregister_agent(self, coordinator):
        """اختبار إلغاء تسجيل وكيل"""
        coordinator.register_agent("agent_001", {"name": "test"})
        
        result = coordinator.unregister_agent("agent_001")
        
        assert result is True
        assert "agent_001" not in coordinator.agents
    
    def test_create_task(self, coordinator):
        """اختبار إنشاء مهمة"""
        coordinator.register_agent("agent_001", {
            "name": "sales_analyzer",
            "capabilities": ["analysis"]
        })
        
        task = coordinator.create_task(
            task_type="analysis",
            parameters={"data": "sales_data"},
            assigned_agent="agent_001"
        )
        
        assert task is not None
        assert isinstance(task, AgentTask)
        assert task.task_type == "analysis"
        assert task.assigned_agent == "agent_001"
    
    def test_execute_task(self, coordinator):
        """اختبار تنفيذ مهمة"""
        coordinator.register_agent("agent_001", {
            "name": "sales_analyzer",
            "capabilities": ["analysis"]
        })
        
        task = coordinator.create_task(
            task_type="analysis",
            parameters={"data": "sales_data"},
            assigned_agent="agent_001"
        )
        
        result = coordinator.execute_task(task.task_id)
        
        assert result is not None
        assert isinstance(result, AgentResult)
    
    def test_get_task_status(self, coordinator):
        """اختبار الحصول على حالة المهمة"""
        coordinator.register_agent("agent_001", {"name": "test"})
        
        task = coordinator.create_task(
            task_type="analysis",
            parameters={},
            assigned_agent="agent_001"
        )
        
        status = coordinator.get_task_status(task.task_id)
        
        assert status is not None
        assert "task_id" in status
        assert "status" in status
    
    def test_coordinate_agents(self, coordinator):
        """اختبار تنسيق الوكلاء"""
        coordinator.register_agent("agent_001", {
            "name": "analyzer",
            "capabilities": ["analysis"]
        })
        coordinator.register_agent("agent_002", {
            "name": "reporter",
            "capabilities": ["reporting"]
        })
        
        workflow = [
            {"agent": "agent_001", "task": "analyze", "depends_on": None},
            {"agent": "agent_002", "task": "report", "depends_on": "agent_001"}
        ]
        
        result = coordinator.coordinate_agents(workflow)
        
        assert result is not None
    
    def test_find_agent_by_capability(self, coordinator):
        """اختبار البحث عن وكيل حسب القدرة"""
        coordinator.register_agent("agent_001", {
            "name": "analyzer",
            "capabilities": ["sales_analysis"]
        })
        coordinator.register_agent("agent_002", {
            "name": "forecaster",
            "capabilities": ["forecasting"]
        })
        
        agents = coordinator.find_agents_by_capability("sales_analysis")
        
        assert len(agents) >= 1
        assert "agent_001" in agents
    
    def test_invalid_agent_id(self, coordinator):
        """اختبار معرف وكيل غير صالح"""
        result = coordinator.unregister_agent("nonexistent_agent")
        
        assert result is False
    
    def test_task_queue_management(self, coordinator):
        """اختبار إدارة قائمة انتظار المهام"""
        coordinator.register_agent("agent_001", {"name": "test"})
        
        # إضافة عدة مهام
        for i in range(3):
            coordinator.create_task(
                task_type=f"task_{i}",
                parameters={},
                assigned_agent="agent_001"
            )
        
        # التحقق من قائمة المهام
        queue = coordinator.get_task_queue()
        assert len(queue) >= 3


class TestAgentTask:
    """اختبارات مهمة الوكيل"""
    
    def test_agent_task_creation(self):
        """اختبار إنشاء مهمة الوكيل"""
        task = AgentTask(
            task_id="task_001",
            task_type="analysis",
            parameters={"data": "test"},
            assigned_agent="agent_001",
            priority="high",
            status="pending",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            result=None,
            error=None
        )
        
        assert task.task_id == "task_001"
        assert task.task_type == "analysis"
        assert task.priority == "high"


class TestAgentResult:
    """اختبارات نتيجة الوكيل"""
    
    def test_agent_result_creation(self):
        """اختبار إنشاء نتيجة الوكيل"""
        result = AgentResult(
            task_id="task_001",
            agent_id="agent_001",
            status="completed",
            output={"analysis": "complete"},
            execution_time=5.0,
            resources_used={"cpu": 10, "memory": 100},
            completed_at=datetime.now()
        )
        
        assert result.task_id == "task_001"
        assert result.status == "completed"
        assert result.execution_time == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



