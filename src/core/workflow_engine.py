#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك سير العمل - Workflow Engine
نظام متقدم لإدارة سير العمل والموافقات
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class WorkflowStatus(Enum):
    """حالات سير العمل"""
    PENDING = "pending"              # في الانتظار
    IN_PROGRESS = "in_progress"      # قيد التنفيذ
    APPROVED = "approved"            # موافق عليه
    REJECTED = "rejected"            # مرفوض
    CANCELLED = "cancelled"          # ملغي
    EXPIRED = "expired"              # منتهي الصلاحية


class ApprovalStatus(Enum):
    """حالات الموافقة"""
    PENDING = "pending"              # في الانتظار
    APPROVED = "approved"            # موافق عليه
    REJECTED = "rejected"            # مرفوض
    DELEGATED = "delegated"          # مفوض


class StepType(Enum):
    """أنواع الخطوات"""
    APPROVAL = "approval"            # موافقة
    NOTIFICATION = "notification"    # إشعار
    CONDITION = "condition"          # شرط
    ACTION = "action"                # إجراء


class ApproverType(Enum):
    """أنواع الموافقين"""
    USER = "user"                    # مستخدم محدد
    ROLE = "role"                    # دور محدد
    DEPARTMENT = "department"        # قسم محدد


@dataclass
class Workflow:
    """نموذج بيانات سير العمل"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    entity_type: str = ""            # purchase_order, sale, payment, etc.
    is_active: bool = True
    is_default: bool = False
    trigger_condition: str = ""      # JSON
    company_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'entity_type': self.entity_type,
            'is_active': 1 if self.is_active else 0,
            'is_default': 1 if self.is_default else 0,
            'trigger_condition': self.trigger_condition,
            'company_id': self.company_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class WorkflowStep:
    """نموذج بيانات خطوة سير العمل"""
    id: Optional[int] = None
    workflow_id: int = 0
    step_order: int = 0
    name: str = ""
    step_type: str = StepType.APPROVAL.value
    approver_type: Optional[str] = None
    approver_id: Optional[int] = None
    approver_role: Optional[str] = None
    condition_expression: str = ""   # JSON
    action_type: Optional[str] = None
    action_config: str = ""          # JSON
    timeout_hours: Optional[int] = None
    is_required: bool = True
    can_delegate: bool = False
    auto_approve: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'step_order': self.step_order,
            'name': self.name,
            'step_type': self.step_type,
            'approver_type': self.approver_type,
            'approver_id': self.approver_id,
            'approver_role': self.approver_role,
            'condition_expression': self.condition_expression,
            'action_type': self.action_type,
            'action_config': self.action_config,
            'timeout_hours': self.timeout_hours,
            'is_required': 1 if self.is_required else 0,
            'can_delegate': 1 if self.can_delegate else 0,
            'auto_approve': 1 if self.auto_approve else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class WorkflowInstance:
    """نموذج بيانات مثيل سير العمل"""
    id: Optional[int] = None
    workflow_id: int = 0
    entity_type: str = ""
    entity_id: int = 0
    status: str = WorkflowStatus.PENDING.value
    current_step_id: Optional[int] = None
    initiated_by: int = 0
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[int] = None
    notes: str = ""
    metadata: str = ""               # JSON
    company_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'status': self.status,
            'current_step_id': self.current_step_id,
            'initiated_by': self.initiated_by,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'notes': self.notes,
            'metadata': self.metadata,
            'company_id': self.company_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class WorkflowApproval:
    """نموذج بيانات موافقة"""
    id: Optional[int] = None
    instance_id: int = 0
    step_id: int = 0
    approver_id: int = 0
    status: str = ApprovalStatus.PENDING.value
    decision: Optional[str] = None
    comments: str = ""
    delegated_to: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    reminder_sent: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'step_id': self.step_id,
            'approver_id': self.approver_id,
            'status': self.status,
            'decision': self.decision,
            'comments': self.comments,
            'delegated_to': self.delegated_to,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'notified_at': self.notified_at.isoformat() if self.notified_at else None,
            'reminder_sent': 1 if self.reminder_sent else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WorkflowEngine:
    """محرك سير العمل"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
    
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """الحصول على سير عمل بالمعرف"""
        try:
            query = """
                SELECT id, name, description, entity_type, is_active, is_default,
                       trigger_condition, company_id, created_by,
                       created_at, updated_at
                FROM workflows
                WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (workflow_id,))
            if result:
                return self._row_to_workflow(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سير العمل {workflow_id}: {e}")
        return None
    
    def get_workflow_by_entity_type(self, entity_type: str, company_id: Optional[int] = None) -> Optional[Workflow]:
        """الحصول على سير العمل الافتراضي لنوع كيان"""
        try:
            query = """
                SELECT id, name, description, entity_type, is_active, is_default,
                       trigger_condition, company_id, created_by,
                       created_at, updated_at
                FROM workflows
                WHERE entity_type = ? AND is_active = 1
            """
            params = [entity_type]
            
            if company_id:
                query += " AND (company_id = ? OR company_id IS NULL)"
                params.append(company_id)
            else:
                query += " AND company_id IS NULL"
            
            query += " ORDER BY is_default DESC, id DESC LIMIT 1"
            
            result = self.db_manager.fetch_one(query, tuple(params))
            if result:
                return self._row_to_workflow(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سير العمل لـ {entity_type}: {e}")
        return None
    
    def get_workflow_steps(self, workflow_id: int) -> List[WorkflowStep]:
        """الحصول على خطوات سير العمل"""
        try:
            query = """
                SELECT id, workflow_id, step_order, name, step_type,
                       approver_type, approver_id, approver_role,
                       condition_expression, action_type, action_config,
                       timeout_hours, is_required, can_delegate, auto_approve,
                       created_at, updated_at
                FROM workflow_steps
                WHERE workflow_id = ?
                ORDER BY step_order ASC
            """
            results = self.db_manager.fetch_all(query, (workflow_id,))
            return [self._row_to_workflow_step(row) for row in results]
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على خطوات سير العمل {workflow_id}: {e}")
            return []
    
    def start_workflow(self, workflow_id: int, entity_type: str, entity_id: int,
                      initiated_by: int, company_id: Optional[int] = None,
                      notes: str = "", metadata: Dict[str, Any] = None) -> Optional[int]:
        """بدء سير عمل جديد"""
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"سير العمل غير موجود: {workflow_id}")
            
            if not workflow.is_active:
                raise ValueError(f"سير العمل غير نشط: {workflow_id}")
            
            # التحقق من عدم وجود مثيل نشط لنفس الكيان
            existing = self.get_instance_by_entity(entity_type, entity_id)
            if existing and existing.status in [WorkflowStatus.PENDING.value, WorkflowStatus.IN_PROGRESS.value]:
                raise ValueError(f"يوجد سير عمل نشط بالفعل للكيان {entity_type}:{entity_id}")
            
            # الحصول على الخطوة الأولى
            steps = self.get_workflow_steps(workflow_id)
            if not steps:
                raise ValueError(f"لا توجد خطوات في سير العمل {workflow_id}")
            
            first_step = steps[0]
            
            # إنشاء مثيل سير العمل
            metadata_str = json.dumps(metadata) if metadata else ""
            query = """
                INSERT INTO workflow_instances (
                    workflow_id, entity_type, entity_id, status,
                    current_step_id, initiated_by, initiated_at,
                    notes, metadata, company_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.now()
            params = (
                workflow_id, entity_type, entity_id, WorkflowStatus.IN_PROGRESS.value,
                first_step.id, initiated_by, now,
                notes, metadata_str, company_id, now, now
            )
            
            instance_id = self.db_manager.execute_insert(query, params)
            
            if instance_id:
                # إنشاء موافقات للخطوة الأولى
                self._create_approvals_for_step(instance_id, first_step)
                
                # تسجيل في التاريخ
                self._add_history(instance_id, first_step.id, "started", initiated_by)
                
                self.logger.info(f"تم بدء سير العمل {workflow_id} للكيان {entity_type}:{entity_id}")
                return instance_id
            
        except Exception as e:
            self.logger.error(f"خطأ في بدء سير العمل: {e}")
            raise
        
        return None
    
    def approve_step(self, approval_id: int, approver_id: int, comments: str = "") -> bool:
        """الموافقة على خطوة"""
        try:
            approval = self._get_approval(approval_id)
            if not approval:
                raise ValueError(f"الموافقة غير موجودة: {approval_id}")
            
            if approval.approver_id != approver_id:
                raise ValueError("ليس لديك صلاحية الموافقة على هذه الخطوة")
            
            if approval.status != ApprovalStatus.PENDING.value:
                raise ValueError(f"الموافقة في حالة {approval.status} ولا يمكن الموافقة عليها")
            
            # تحديث الموافقة
            query = """
                UPDATE workflow_approvals
                SET status = ?, decision = 'approve', comments = ?,
                    approved_at = ?, updated_at = ?
                WHERE id = ?
            """
            now = datetime.now()
            self.db_manager.execute_query(query, (
                ApprovalStatus.APPROVED.value, comments, now, now, approval_id
            ))
            
            # تسجيل في التاريخ
            self._add_history(approval.instance_id, approval.step_id, "approved", approver_id, comments)
            
            # التحقق من إكمال الخطوة
            self._check_step_completion(approval.instance_id, approval.step_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في الموافقة على الخطوة: {e}")
            raise
    
    def reject_step(self, approval_id: int, approver_id: int, comments: str = "") -> bool:
        """رفض خطوة"""
        try:
            approval = self._get_approval(approval_id)
            if not approval:
                raise ValueError(f"الموافقة غير موجودة: {approval_id}")
            
            if approval.approver_id != approver_id:
                raise ValueError("ليس لديك صلاحية رفض هذه الخطوة")
            
            if approval.status != ApprovalStatus.PENDING.value:
                raise ValueError(f"الموافقة في حالة {approval.status} ولا يمكن رفضها")
            
            # تحديث الموافقة
            query = """
                UPDATE workflow_approvals
                SET status = ?, decision = 'reject', comments = ?,
                    rejected_at = ?, updated_at = ?
                WHERE id = ?
            """
            now = datetime.now()
            self.db_manager.execute_query(query, (
                ApprovalStatus.REJECTED.value, comments, now, now, approval_id
            ))
            
            # تحديث حالة المثيل
            instance_query = """
                UPDATE workflow_instances
                SET status = ?, completed_at = ?, completed_by = ?, updated_at = ?
                WHERE id = ?
            """
            self.db_manager.execute_query(instance_query, (
                WorkflowStatus.REJECTED.value, now, approver_id, now, approval.instance_id
            ))
            
            # تسجيل في التاريخ
            self._add_history(approval.instance_id, approval.step_id, "rejected", approver_id, comments)
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في رفض الخطوة: {e}")
            raise
    
    def get_instance_by_entity(self, entity_type: str, entity_id: int) -> Optional[WorkflowInstance]:
        """الحصول على مثيل سير العمل للكيان"""
        try:
            query = """
                SELECT id, workflow_id, entity_type, entity_id, status,
                       current_step_id, initiated_by, initiated_at,
                       completed_at, completed_by, notes, metadata,
                       company_id, created_at, updated_at
                FROM workflow_instances
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = self.db_manager.fetch_one(query, (entity_type, entity_id))
            if result:
                return self._row_to_workflow_instance(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على مثيل سير العمل: {e}")
        return None
    
    def _create_approvals_for_step(self, instance_id: int, step: WorkflowStep):
        """إنشاء موافقات للخطوة"""
        try:
            if step.step_type != StepType.APPROVAL.value:
                return
            
            # تحديد الموافقين
            approvers = self._get_approvers_for_step(step)
            
            if not approvers:
                self.logger.warning(f"لا يوجد موافقون للخطوة {step.id}")
                return
            
            # إنشاء موافقات
            now = datetime.now()
            deadline = None
            if step.timeout_hours:
                deadline = now + timedelta(hours=step.timeout_hours)
            
            for approver_id in approvers:
                query = """
                    INSERT INTO workflow_approvals (
                        instance_id, step_id, approver_id, status,
                        deadline, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                self.db_manager.execute_query(query, (
                    instance_id, step.id, approver_id, ApprovalStatus.PENDING.value,
                    deadline, now, now
                ))
                
                # إرسال إشعار (يمكن تنفيذه لاحقاً)
                # self._notify_approver(approver_id, instance_id, step)
        
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الموافقات: {e}")
    
    def _get_approvers_for_step(self, step: WorkflowStep) -> List[int]:
        """الحصول على قائمة الموافقين للخطوة"""
        approvers = []
        
        try:
            if step.approver_type == ApproverType.USER.value and step.approver_id:
                approvers.append(step.approver_id)
            
            elif step.approver_type == ApproverType.ROLE.value and step.approver_role:
                # الحصول على المستخدمين بالدور المحدد
                query = """
                    SELECT id FROM users
                    WHERE role = ? AND is_active = 1
                """
                results = self.db_manager.fetch_all(query, (step.approver_role,))
                approvers.extend([row['id'] for row in results])
            
            # يمكن إضافة منطق إضافي للـ DEPARTMENT هنا
        
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الموافقين: {e}")
        
        return approvers
    
    def _check_step_completion(self, instance_id: int, step_id: int):
        """التحقق من إكمال الخطوة"""
        try:
            instance = self._get_instance(instance_id)
            if not instance:
                return
            
            step = self._get_step(step_id)
            if not step:
                return
            
            # الحصول على جميع الموافقات للخطوة
            query = """
                SELECT * FROM workflow_approvals
                WHERE instance_id = ? AND step_id = ?
            """
            approvals = self.db_manager.fetch_all(query, (instance_id, step_id))
            
            if not approvals:
                return
            
            # التحقق من الموافقات المطلوبة
            required_approvals = [a for a in approvals if step.is_required]
            approved_count = sum(1 for a in required_approvals if a['status'] == ApprovalStatus.APPROVED.value)
            
            # إذا كانت جميع الموافقات المطلوبة موافق عليها
            if approved_count >= len(required_approvals):
                # الانتقال للخطوة التالية
                self._move_to_next_step(instance_id, step_id)
        
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من إكمال الخطوة: {e}")
    
    def _move_to_next_step(self, instance_id: int, current_step_id: int):
        """الانتقال للخطوة التالية"""
        try:
            instance = self._get_instance(instance_id)
            if not instance:
                return
            
            workflow = self.get_workflow(instance.workflow_id)
            steps = self.get_workflow_steps(workflow.id)
            
            # العثور على الخطوة الحالية
            current_step = None
            for step in steps:
                if step.id == current_step_id:
                    current_step = step
                    break
            
            if not current_step:
                return
            
            # العثور على الخطوة التالية
            next_step = None
            for step in steps:
                if step.step_order > current_step.step_order:
                    next_step = step
                    break
            
            if next_step:
                # تحديث المثيل للخطوة التالية
                query = """
                    UPDATE workflow_instances
                    SET current_step_id = ?, updated_at = ?
                    WHERE id = ?
                """
                self.db_manager.execute_query(query, (next_step.id, datetime.now(), instance_id))
                
                # إنشاء موافقات للخطوة التالية
                self._create_approvals_for_step(instance_id, next_step)
                
                # تسجيل في التاريخ
                self._add_history(instance_id, next_step.id, "step_started", instance.initiated_by)
            else:
                # إكمال سير العمل
                query = """
                    UPDATE workflow_instances
                    SET status = ?, completed_at = ?, updated_at = ?
                    WHERE id = ?
                """
                now = datetime.now()
                self.db_manager.execute_query(query, (
                    WorkflowStatus.APPROVED.value, now, now, instance_id
                ))
                
                # تسجيل في التاريخ
                self._add_history(instance_id, None, "completed", instance.initiated_by)
        
        except Exception as e:
            self.logger.error(f"خطأ في الانتقال للخطوة التالية: {e}")
    
    def _get_instance(self, instance_id: int) -> Optional[WorkflowInstance]:
        """الحصول على مثيل سير العمل"""
        try:
            query = """
                SELECT id, workflow_id, entity_type, entity_id, status,
                       current_step_id, initiated_by, initiated_at,
                       completed_at, completed_by, notes, metadata,
                       company_id, created_at, updated_at
                FROM workflow_instances
                WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (instance_id,))
            if result:
                return self._row_to_workflow_instance(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المثيل: {e}")
        return None
    
    def _get_step(self, step_id: int) -> Optional[WorkflowStep]:
        """الحصول على خطوة"""
        try:
            query = """
                SELECT id, workflow_id, step_order, name, step_type,
                       approver_type, approver_id, approver_role,
                       condition_expression, action_type, action_config,
                       timeout_hours, is_required, can_delegate, auto_approve,
                       created_at, updated_at
                FROM workflow_steps
                WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (step_id,))
            if result:
                return self._row_to_workflow_step(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الخطوة: {e}")
        return None
    
    def _get_approval(self, approval_id: int) -> Optional[WorkflowApproval]:
        """الحصول على موافقة"""
        try:
            query = """
                SELECT id, instance_id, step_id, approver_id, status,
                       decision, comments, delegated_to,
                       approved_at, rejected_at, deadline,
                       notified_at, reminder_sent,
                       created_at, updated_at
                FROM workflow_approvals
                WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (approval_id,))
            if result:
                return self._row_to_workflow_approval(result)
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الموافقة: {e}")
        return None
    
    def _add_history(self, instance_id: int, step_id: Optional[int], action: str,
                    performed_by: int, details: str = ""):
        """إضافة سجل في التاريخ"""
        try:
            query = """
                INSERT INTO workflow_history (
                    instance_id, step_id, action, performed_by,
                    performed_at, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db_manager.execute_query(query, (
                instance_id, step_id, action, performed_by,
                datetime.now(), details
            ))
        except Exception as e:
            self.logger.error(f"خطأ في إضافة السجل: {e}")
    
    def _row_to_workflow(self, row: Dict[str, Any]) -> Workflow:
        """تحويل صف إلى Workflow"""
        return Workflow(
            id=row.get('id'),
            name=row.get('name', ''),
            description=row.get('description', ''),
            entity_type=row.get('entity_type', ''),
            is_active=bool(row.get('is_active', 1)),
            is_default=bool(row.get('is_default', 0)),
            trigger_condition=row.get('trigger_condition', ''),
            company_id=row.get('company_id'),
            created_by=row.get('created_by'),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )
    
    def _row_to_workflow_step(self, row: Dict[str, Any]) -> WorkflowStep:
        """تحويل صف إلى WorkflowStep"""
        return WorkflowStep(
            id=row.get('id'),
            workflow_id=row.get('workflow_id', 0),
            step_order=row.get('step_order', 0),
            name=row.get('name', ''),
            step_type=row.get('step_type', StepType.APPROVAL.value),
            approver_type=row.get('approver_type'),
            approver_id=row.get('approver_id'),
            approver_role=row.get('approver_role'),
            condition_expression=row.get('condition_expression', ''),
            action_type=row.get('action_type'),
            action_config=row.get('action_config', ''),
            timeout_hours=row.get('timeout_hours'),
            is_required=bool(row.get('is_required', 1)),
            can_delegate=bool(row.get('can_delegate', 0)),
            auto_approve=bool(row.get('auto_approve', 0)),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )
    
    def _row_to_workflow_instance(self, row: Dict[str, Any]) -> WorkflowInstance:
        """تحويل صف إلى WorkflowInstance"""
        return WorkflowInstance(
            id=row.get('id'),
            workflow_id=row.get('workflow_id', 0),
            entity_type=row.get('entity_type', ''),
            entity_id=row.get('entity_id', 0),
            status=row.get('status', WorkflowStatus.PENDING.value),
            current_step_id=row.get('current_step_id'),
            initiated_by=row.get('initiated_by', 0),
            initiated_at=datetime.fromisoformat(row['initiated_at']) if row.get('initiated_at') else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None,
            completed_by=row.get('completed_by'),
            notes=row.get('notes', ''),
            metadata=row.get('metadata', ''),
            company_id=row.get('company_id'),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )
    
    def _row_to_workflow_approval(self, row: Dict[str, Any]) -> WorkflowApproval:
        """تحويل صف إلى WorkflowApproval"""
        return WorkflowApproval(
            id=row.get('id'),
            instance_id=row.get('instance_id', 0),
            step_id=row.get('step_id', 0),
            approver_id=row.get('approver_id', 0),
            status=row.get('status', ApprovalStatus.PENDING.value),
            decision=row.get('decision'),
            comments=row.get('comments', ''),
            delegated_to=row.get('delegated_to'),
            approved_at=datetime.fromisoformat(row['approved_at']) if row.get('approved_at') else None,
            rejected_at=datetime.fromisoformat(row['rejected_at']) if row.get('rejected_at') else None,
            deadline=datetime.fromisoformat(row['deadline']) if row.get('deadline') else None,
            notified_at=datetime.fromisoformat(row['notified_at']) if row.get('notified_at') else None,
            reminder_sent=bool(row.get('reminder_sent', 0)),
            created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row.get('updated_at') else None
        )

