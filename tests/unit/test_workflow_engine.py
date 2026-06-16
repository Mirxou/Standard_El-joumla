"""
Unit Tests for Workflow Engine
اختبارات وحدة محرك سير العمل
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.core.workflow_engine import (
    ApprovalStatus,
    ApproverType,
    StepType,
    Workflow,
    WorkflowApproval,
    WorkflowEngine,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowStep,
)


class TestWorkflowStatus:
    """اختبارات حالات سير العمل"""

    def test_workflow_status_values(self):
        """اختبار قيم حالات سير العمل"""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.IN_PROGRESS.value == "in_progress"
        assert WorkflowStatus.APPROVED.value == "approved"
        assert WorkflowStatus.REJECTED.value == "rejected"
        assert WorkflowStatus.CANCELLED.value == "cancelled"
        assert WorkflowStatus.EXPIRED.value == "expired"

    def test_approval_status_values(self):
        """اختبار قيم حالات الموافقة"""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.DELEGATED.value == "delegated"

    def test_step_type_values(self):
        """اختبار أنواع الخطوات"""
        assert StepType.APPROVAL.value == "approval"
        assert StepType.NOTIFICATION.value == "notification"
        assert StepType.CONDITION.value == "condition"
        assert StepType.ACTION.value == "action"

    def test_approver_type_values(self):
        """اختبار أنواع الموافقين"""
        assert ApproverType.USER.value == "user"
        assert ApproverType.ROLE.value == "role"
        assert ApproverType.DEPARTMENT.value == "department"


class TestWorkflow:
    """اختبارات نموذج Workflow"""

    def test_workflow_creation(self):
        """اختبار إنشاء Workflow"""
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            description="Test description",
            entity_type="sale",
            is_active=True,
            is_default=False,
            company_id=1,
        )

        assert workflow.id == 1
        assert workflow.name == "Test Workflow"
        assert workflow.entity_type == "sale"
        assert workflow.is_active is True
        assert workflow.is_default is False

    def test_workflow_to_dict(self):
        """اختبار تحويل Workflow إلى قاموس"""
        workflow = Workflow(
            id=1,
            name="Test Workflow",
            entity_type="sale",
            is_active=True,
            is_default=False,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        data = workflow.to_dict()

        assert data["id"] == 1
        assert data["name"] == "Test Workflow"
        assert data["is_active"] == 1
        assert data["is_default"] == 0
        assert data["created_at"] == "2024-01-01T12:00:00"

    def test_workflow_defaults(self):
        """اختبار القيم الافتراضية لـ Workflow"""
        workflow = Workflow()

        assert workflow.id is None
        assert workflow.name == ""
        assert workflow.is_active is True
        assert workflow.is_default is False


class TestWorkflowStep:
    """اختبارات نموذج WorkflowStep"""

    def test_workflow_step_creation(self):
        """اختبار إنشاء WorkflowStep"""
        step = WorkflowStep(
            id=1,
            workflow_id=1,
            step_order=1,
            name="Approval Step",
            step_type=StepType.APPROVAL.value,
            approver_type=ApproverType.USER.value,
            approver_id=5,
            is_required=True,
        )

        assert step.id == 1
        assert step.workflow_id == 1
        assert step.step_order == 1
        assert step.name == "Approval Step"
        assert step.step_type == "approval"
        assert step.is_required is True

    def test_workflow_step_to_dict(self):
        """اختبار تحويل WorkflowStep إلى قاموس"""
        step = WorkflowStep(
            id=1,
            workflow_id=1,
            name="Test Step",
            is_required=True,
            can_delegate=False,
            auto_approve=False,
        )

        data = step.to_dict()

        assert data["is_required"] == 1
        assert data["can_delegate"] == 0
        assert data["auto_approve"] == 0


class TestWorkflowInstance:
    """اختبارات نموذج WorkflowInstance"""

    def test_workflow_instance_creation(self):
        """اختبار إنشاء WorkflowInstance"""
        instance = WorkflowInstance(
            id=1,
            workflow_id=1,
            entity_type="sale",
            entity_id=100,
            status=WorkflowStatus.IN_PROGRESS.value,
            initiated_by=5,
        )

        assert instance.id == 1
        assert instance.entity_type == "sale"
        assert instance.entity_id == 100
        assert instance.status == "in_progress"

    def test_workflow_instance_to_dict(self):
        """اختبار تحويل WorkflowInstance إلى قاموس"""
        instance = WorkflowInstance(
            id=1,
            workflow_id=1,
            status=WorkflowStatus.PENDING.value,
            initiated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        data = instance.to_dict()

        assert data["status"] == "pending"
        assert data["initiated_at"] == "2024-01-01T12:00:00"


class TestWorkflowApproval:
    """اختبارات نموذج WorkflowApproval"""

    def test_workflow_approval_creation(self):
        """اختبار إنشاء WorkflowApproval"""
        approval = WorkflowApproval(
            id=1,
            instance_id=1,
            step_id=1,
            approver_id=5,
            status=ApprovalStatus.PENDING.value,
        )

        assert approval.id == 1
        assert approval.approver_id == 5
        assert approval.status == "pending"

    def test_workflow_approval_to_dict(self):
        """اختبار تحويل WorkflowApproval إلى قاموس"""
        approval = WorkflowApproval(
            id=1,
            instance_id=1,
            status=ApprovalStatus.APPROVED.value,
            approved_at=datetime(2024, 1, 1, 12, 0, 0),
            reminder_sent=True,
        )

        data = approval.to_dict()

        assert data["status"] == "approved"
        assert data["reminder_sent"] == 1
        assert data["approved_at"] == "2024-01-01T12:00:00"


class TestWorkflowEngine:
    """اختبارات WorkflowEngine"""

    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager"""
        return MagicMock()

    @pytest.fixture
    def workflow_engine(self, mock_db):
        """WorkflowEngine مع Mock DB"""
        return WorkflowEngine(mock_db)

    def test_workflow_engine_initialization(self, workflow_engine, mock_db):
        """اختبار تهيئة WorkflowEngine"""
        assert workflow_engine.db_manager == mock_db
        assert workflow_engine.logger is not None

    def test_get_workflow_success(self, workflow_engine, mock_db):
        """اختبار الحصول على Workflow موجود"""
        mock_db.fetch_one.return_value = {
            "id": 1,
            "name": "Test Workflow",
            "description": "Description",
            "entity_type": "sale",
            "is_active": 1,
            "is_default": 0,
            "trigger_condition": "{}",
            "company_id": 1,
            "created_by": 1,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }

        result = workflow_engine.get_workflow(1)

        assert result is not None
        assert result.id == 1
        assert result.name == "Test Workflow"
        mock_db.fetch_one.assert_called_once()

    def test_get_workflow_not_found(self, workflow_engine, mock_db):
        """اختبار الحصول على Workflow غير موجود"""
        mock_db.fetch_one.return_value = None

        result = workflow_engine.get_workflow(999)

        assert result is None

    def test_get_workflow_by_entity_type(self, workflow_engine, mock_db):
        """اختبار الحصول على Workflow حسب نوع الكيان"""
        mock_db.fetch_one.return_value = {
            "id": 1,
            "name": "Sale Workflow",
            "entity_type": "sale",
            "is_active": 1,
            "is_default": 1,
            "trigger_condition": "{}",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }

        result = workflow_engine.get_workflow_by_entity_type("sale", company_id=1)

        assert result is not None
        assert result.entity_type == "sale"

    def test_get_workflow_steps(self, workflow_engine, mock_db):
        """اختبار الحصول على خطوات Workflow"""
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "workflow_id": 1,
                "step_order": 1,
                "name": "Step 1",
                "step_type": "approval",
                "approver_type": "user",
                "approver_id": 5,
                "condition_expression": "{}",
                "action_config": "{}",
                "is_required": 1,
                "can_delegate": 0,
                "auto_approve": 0,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
            }
        ]

        result = workflow_engine.get_workflow_steps(1)

        assert len(result) == 1
        assert result[0].name == "Step 1"
        assert result[0].step_order == 1

    def test_get_workflow_steps_empty(self, workflow_engine, mock_db):
        """اختبار الحصول على خطوات Workflow فارغة"""
        mock_db.fetch_all.return_value = []

        result = workflow_engine.get_workflow_steps(1)

        assert result == []

    def test_get_instance_by_entity(self, workflow_engine, mock_db):
        """اختبار الحصول على مثيل Workflow للكيان"""
        mock_db.fetch_one.return_value = {
            "id": 1,
            "workflow_id": 1,
            "entity_type": "sale",
            "entity_id": 100,
            "status": "in_progress",
            "initiated_by": 5,
            "metadata": "{}",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
        }

        result = workflow_engine.get_instance_by_entity("sale", 100)

        assert result is not None
        assert result.entity_type == "sale"
        assert result.entity_id == 100

    def test_get_instance_by_entity_not_found(self, workflow_engine, mock_db):
        """اختبار عدم وجود مثيل للكيان"""
        mock_db.fetch_one.return_value = None

        result = workflow_engine.get_instance_by_entity("sale", 999)

        assert result is None


class TestWorkflowEngineApprovals:
    """اختبارات إدارة الموافقات"""

    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager"""
        return MagicMock()

    @pytest.fixture
    def workflow_engine(self, mock_db):
        """WorkflowEngine مع Mock DB"""
        engine = WorkflowEngine(mock_db)
        # Mock _get_approval method
        engine._get_approval = MagicMock(
            return_value=WorkflowApproval(
                id=1,
                instance_id=1,
                step_id=1,
                approver_id=5,
                status=ApprovalStatus.PENDING.value,
            )
        )
        return engine

    def test_approve_step_success(self, workflow_engine, mock_db):
        """اختبار الموافقة على خطوة بنجاح"""
        mock_db.execute_query.return_value = None
        workflow_engine._check_step_completion = MagicMock()
        workflow_engine._add_history = MagicMock()

        result = workflow_engine.approve_step(1, 5, "Approved")

        assert result is True
        mock_db.execute_query.assert_called_once()

    def test_reject_step_success(self, workflow_engine, mock_db):
        """اختبار رفض خطوة بنجاح"""
        mock_db.execute_query.return_value = None
        workflow_engine._add_history = MagicMock()

        result = workflow_engine.reject_step(1, 5, "Rejected")

        assert result is True
        # Should update both approval and instance
        assert mock_db.execute_query.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
