#!/usr/bin/env python3
"""
منسق الوكلاء المتعددين - Multi-Agent Coordinator
ينسق بين الوكلاء الذكية المختلفة في النظام
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AgentStatus(Enum):
    """حالة الوكيل"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"


class AgentType(Enum):
    """نوع الوكيل"""
    SALES_AGENT = "sales_agent"
    INVENTORY_AGENT = "inventory_agent"
    CUSTOMER_AGENT = "customer_agent"
    ANALYTICS_AGENT = "analytics_agent"
    VOICE_AGENT = "voice_agent"
    UI_AGENT = "ui_agent"


@dataclass
class AgentTask:
    """مهمة الوكيل"""
    task_id: str
    agent_type: AgentType
    description: str
    priority: int = 1
    created_at: datetime = None
    assigned_to: Optional[str] = None
    status: str = "pending"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentResult:
    """نتيجة الوكيل"""
    task_id: str
    agent_id: str
    result: Any
    confidence: float = 1.0
    execution_time: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseAgent:
    """الوكيل الأساسي"""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.tasks_completed = 0
        self.last_active = datetime.now()

    def execute_task(self, task: AgentTask) -> AgentResult:
        """تنفيذ المهمة"""
        raise NotImplementedError("يجب تنفيذ هذه الطريقة في الفئة الفرعية")

    def get_capabilities(self) -> List[str]:
        """الحصول على القدرات"""
        return []

    def update_status(self, status: AgentStatus):
        """تحديث الحالة"""
        self.status = status
        self.last_active = datetime.now()


class MultiAgentCoordinator:
    """منسق الوكلاء المتعددين"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentResult] = []
        self.agent_assignments: Dict[str, List[str]] = {}

    def register_agent(self, agent: BaseAgent):
        """تسجيل وكيل جديد"""
        self.agents[agent.agent_id] = agent
        self.agent_assignments[agent.agent_id] = []
        print(f"تم تسجيل الوكيل: {agent.agent_id} ({agent.agent_type.value})")

    def submit_task(self, task: AgentTask) -> str:
        """تقديم مهمة جديدة"""
        self.task_queue.append(task)
        print(f"تم تقديم المهمة: {task.task_id} - {task.description}")
        return task.task_id

    def assign_task(self, task: AgentTask) -> Optional[str]:
        """تعيين مهمة لوكيل مناسب"""
        # البحث عن وكيل متاح من النوع المناسب
        available_agents = [
            agent for agent in self.agents.values()
            if agent.agent_type == task.agent_type and agent.status == AgentStatus.IDLE
        ]

        if not available_agents:
            print(f"لا يوجد وكيل متاح للنوع: {task.agent_type.value}")
            return None

        # اختيار الوكيل الأقل تحميلاً
        selected_agent = min(available_agents, key=lambda a: a.tasks_completed)

        # تعيين المهمة
        task.assigned_to = selected_agent.agent_id
        task.status = "assigned"
        selected_agent.update_status(AgentStatus.BUSY)
        self.agent_assignments[selected_agent.agent_id].append(task.task_id)

        print(f"تم تعيين المهمة {task.task_id} لوكيل {selected_agent.agent_id}")
        return selected_agent.agent_id

    def execute_task(self, task_id: str) -> Optional[AgentResult]:
        """تنفيذ مهمة محددة"""
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if not task or not task.assigned_to:
            return None

        agent = self.agents.get(task.assigned_to)
        if not agent:
            return None

        try:
            # تنفيذ المهمة
            result = agent.execute_task(task)

            # تحديث الحالات
            task.status = "completed"
            agent.update_status(AgentStatus.IDLE)
            agent.tasks_completed += 1
            self.completed_tasks.append(result)

            # إزالة المهمة من قائمة الانتظار
            self.task_queue.remove(task)

            print(f"تم إنجاز المهمة: {task_id}")
            return result

        except Exception as e:
            task.status = "failed"
            agent.update_status(AgentStatus.ERROR)
            print(f"فشل في تنفيذ المهمة {task_id}: {str(e)}")
            return None

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على حالة وكيل محدد"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        return {
            "agent_id": agent.agent_id,
            "type": agent.agent_type.value,
            "status": agent.status.value,
            "tasks_completed": agent.tasks_completed,
            "last_active": agent.last_active.isoformat(),
            "current_tasks": self.agent_assignments.get(agent_id, [])
        }

    def get_system_status(self) -> Dict[str, Any]:
        """الحصول على حالة النظام العامة"""
        return {
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]),
            "busy_agents": len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]),
            "idle_agents": len([a for a in self.agents.values() if a.status == AgentStatus.IDLE]),
            "pending_tasks": len([t for t in self.task_queue if t.status == "pending"]),
            "assigned_tasks": len([t for t in self.task_queue if t.status == "assigned"]),
            "completed_tasks": len(self.completed_tasks)
        }

    def process_pending_tasks(self):
        """معالجة المهام المعلقة"""
        pending_tasks = [t for t in self.task_queue if t.status == "pending"]
        for task in pending_tasks:
            if self.assign_task(task):
                self.execute_task(task.task_id)

    def shutdown(self):
        """إغلاق النظام"""
        for agent in self.agents.values():
            agent.update_status(AgentStatus.IDLE)
        print("تم إغلاق منسق الوكلاء")