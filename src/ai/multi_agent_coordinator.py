#!/usr/bin/env python3
"""
منسق الوكلاء المتعددين - Multi-Agent Coordinator
ينسق بين الوكلاء الذكية المختلفة في النظام
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


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
    description: str = ""
    agent_type: AgentType = AgentType.SALES_AGENT
    priority: Any = 1
    created_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    status: str = "pending"
    parameters: Optional[Dict[str, Any]] = None

    # Extra fields for test_multi_agent_coordinator compatibility:
    task_type: str = ""
    assigned_agent: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Any = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if not self.task_type and self.agent_type:
            self.task_type = self.agent_type.value


@dataclass
class AgentResult:
    """نتيجة الوكيل"""

    task_id: str
    agent_id: str
    result: Any = None
    confidence: float = 1.0
    execution_time: float = 0.0
    timestamp: Optional[datetime] = None

    # Extra fields for test_multi_agent_coordinator:
    status: str = "completed"
    output: Any = None
    resources_used: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.completed_at is None:
            self.completed_at = self.timestamp
        if self.result is None and self.output is not None:
            self.result = self.output
        elif self.output is None and self.result is not None:
            self.output = self.result


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


class GenericAgent(BaseAgent):
    """وكيل عام للاختبارات والتوافقية"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        type_str = config.get("type", "sales_agent")
        try:
            a_type = AgentType(type_str)
        except ValueError:
            a_type = AgentType.SALES_AGENT
        super().__init__(agent_id, a_type)
        self.name = config.get("name", agent_id)
        self.capabilities = config.get("capabilities", [])

    def get_capabilities(self) -> List[str]:
        return self.capabilities

    def execute_task(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            output={"status": "success"},
            result={"status": "success"},
        )


class MultiAgentCoordinator:
    """منسق الوكلاء المتعددين"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentResult] = []
        self.results: Dict[str, AgentResult] = {}
        self.agent_assignments: Dict[str, List[str]] = {}

    def register_agent(self, agent: Any, config: Optional[Dict[str, Any]] = None) -> bool:
        """تسجيل وكيل جديد"""
        if isinstance(agent, str):
            agent_id = agent
            cfg = config or {}
            agent_obj = GenericAgent(agent_id, cfg)
        else:
            agent_obj = agent

        self.agents[agent_obj.agent_id] = agent_obj
        self.agent_assignments[agent_obj.agent_id] = []
        print(f"تم تسجيل الوكيل: {agent_obj.agent_id}")
        return True

    def unregister_agent(self, agent_id: str) -> bool:
        """إلغاء تسجيل وكيل"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self.agent_assignments:
                del self.agent_assignments[agent_id]
            return True
        return False

    def create_task(self, task_type: str, parameters: Dict[str, Any], assigned_agent: Optional[str] = None, **kwargs) -> AgentTask:
        """إنشاء مهمة جديدة وإضافتها لصف الانتظار"""
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        priority = kwargs.get("priority", "medium")
        
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            assigned_agent=assigned_agent,
            assigned_to=assigned_agent,
            priority=priority,
            status="pending",
            description=kwargs.get("description", f"Task of type {task_type}"),
        )
        self.task_queue.append(task)
        return task

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على حالة المهمة"""
        res = self.results.get(task_id)
        if res:
            return {
                "task_id": task_id,
                "status": getattr(res, "status", "completed"),
                "result": res,
            }
        
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if task:
            return {
                "task_id": task_id,
                "status": task.status,
            }
        
        return None

    def get_task_queue(self) -> List[AgentTask]:
        """الحصول على قائمة انتظار المهام"""
        return self.task_queue

    def find_agents_by_capability(self, capability: str) -> List[str]:
        """البحث عن وكلاء لديهم القدرة المحددة"""
        matched = []
        for agent_id, agent in self.agents.items():
            caps = agent.get_capabilities() if hasattr(agent, "get_capabilities") else getattr(agent, "capabilities", [])
            if capability in caps:
                matched.append(agent_id)
        return matched

    def coordinate_agents(self, workflow: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تنسيق الوكلاء لتنفيذ سير عمل متتابع"""
        executed = {}
        for step in workflow:
            agent_id = step.get("agent")
            task_type = step.get("task")
            task = self.create_task(
                task_type=task_type,
                parameters={"depends_on": step.get("depends_on")},
                assigned_agent=agent_id
            )
            res = self.execute_task(task.task_id)
            executed[agent_id] = res
        return {
            "status": "success",
            "results": executed,
        }

    def submit_task(self, task: AgentTask) -> str:
        """تقديم مهمة جديدة"""
        self.task_queue.append(task)
        print(f"تم تقديم المهمة: {task.task_id} - {task.description}")
        return task.task_id

    def assign_task(self, task: AgentTask) -> Optional[str]:
        """تعيين مهمة لوكيل مناسب"""
        available_agents = [
            agent
            for agent in self.agents.values()
            if agent.agent_type == task.agent_type and agent.status == AgentStatus.IDLE
        ]

        if not available_agents:
            print(f"لا يوجد وكيل متاح للنوع: {task.agent_type.value}")
            return None

        selected_agent = min(available_agents, key=lambda a: a.tasks_completed)

        task.assigned_to = selected_agent.agent_id
        task.assigned_agent = selected_agent.agent_id
        task.status = "assigned"
        selected_agent.update_status(AgentStatus.BUSY)
        self.agent_assignments[selected_agent.agent_id].append(task.task_id)

        print(f"تم تعيين المهمة {task.task_id} لوكيل {selected_agent.agent_id}")
        return selected_agent.agent_id

    def execute_task(self, task_id: str) -> Optional[AgentResult]:
        """تنفيذ مهمة محددة"""
        task = next((t for t in self.task_queue if t.task_id == task_id), None)
        if not task:
            return None

        agent_id = task.assigned_to or task.assigned_agent
        if not agent_id:
            return None

        task.assigned_to = agent_id
        task.assigned_agent = agent_id

        agent = self.agents.get(agent_id)
        if not agent:
            return None

        try:
            result = agent.execute_task(task)

            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result

            if hasattr(agent, "update_status"):
                agent.update_status(AgentStatus.IDLE)
            if hasattr(agent, "tasks_completed"):
                agent.tasks_completed += 1

            self.completed_tasks.append(result)
            self.results[task_id] = result

            if task in self.task_queue:
                self.task_queue.remove(task)

            print(f"تم إنجاز المهمة: {task_id}")
            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            if hasattr(agent, "update_status"):
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
            "type": agent.agent_type.value if hasattr(agent.agent_type, "value") else str(agent.agent_type),
            "status": agent.status.value if hasattr(agent.status, "value") else str(agent.status),
            "tasks_completed": agent.tasks_completed,
            "last_active": agent.last_active.isoformat(),
            "current_tasks": self.agent_assignments.get(agent_id, []),
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
            "completed_tasks": len(self.completed_tasks),
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
            if hasattr(agent, "update_status"):
                agent.update_status(AgentStatus.IDLE)
        print("تم إغلاق منسق الوكلاء")

