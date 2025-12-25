#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة سير العمل - Workflow Service
خدمة عالية المستوى لإدارة سير العمل والموافقات
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager
from src.core.workflow_engine import (
    WorkflowEngine, Workflow, WorkflowStep, WorkflowInstance, WorkflowApproval,
    WorkflowStatus, ApprovalStatus, StepType, ApproverType
)

# استيراد WorkflowStatus للاستخدام في المقارنات
from src.core.workflow_engine import WorkflowStatus
from src.utils.logger import setup_logger


class WorkflowService:
    """خدمة سير العمل"""
    
    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.workflow_engine = WorkflowEngine(db_manager, logger)
        self._notification_service = None
    
    @property
    def notification_service(self):
        """Lazy loading لـ NotificationService"""
        if self._notification_service is None:
            try:
                from src.services.notification_service import NotificationService, NotificationType, NotificationPriority, AlertCategory
                self._notification_service = NotificationService(self.db_manager)
            except ImportError:
                if self.logger:
                    self.logger.warning("NotificationService غير متاح")
        return self._notification_service
    
    def _create_workflow_notification(self, title: str, message: str, user_id: Optional[int] = None,
                                       entity_type: Optional[str] = None, entity_id: Optional[int] = None,
                                       priority: int = 2):
        """إنشاء إشعار لسير العمل"""
        if not self.notification_service:
            return
        
        try:
            from src.services.notification_service import NotificationType, NotificationPriority, AlertCategory
            
            notification_priority = NotificationPriority.MEDIUM
            if priority == 1:
                notification_priority = NotificationPriority.LOW
            elif priority == 2:
                notification_priority = NotificationPriority.MEDIUM
            elif priority == 3:
                notification_priority = NotificationPriority.HIGH
            elif priority >= 4:
                notification_priority = NotificationPriority.URGENT
            
            action_url = None
            if entity_type and entity_id:
                if entity_type == "purchase_order":
                    action_url = f"/purchase_order/{entity_id}"
                elif entity_type == "sale":
                    action_url = f"/sale/{entity_id}"
            
            self.notification_service.create_notification(
                title=title,
                message=message,
                notification_type=NotificationType.INFO,
                priority=notification_priority,
                category=AlertCategory.APPROVAL,
                user_id=user_id,
                action_url=action_url,
                data={'entity_type': entity_type, 'entity_id': entity_id}
            )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"فشل إنشاء إشعار سير العمل: {e}")
    
    # ==================== إدارة سير العمل ====================
    
    def create_workflow(self, name: str, entity_type: str, description: str = "",
                       company_id: Optional[int] = None, created_by: Optional[int] = None,
                       is_default: bool = False) -> Optional[int]:
        """إنشاء سير عمل جديد"""
        try:
            query = """
                INSERT INTO workflows (
                    name, description, entity_type, is_active, is_default,
                    company_id, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.now()
            params = (
                name, description, entity_type, 1, 1 if is_default else 0,
                company_id, created_by, now, now
            )
            
            workflow_id = self.db_manager.execute_insert(query, params)
            
            if workflow_id:
                self.logger.info(f"تم إنشاء سير العمل: {name} (ID: {workflow_id})")
                return workflow_id
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء سير العمل: {e}")
            raise
        
        return None
    
    def add_workflow_step(self, workflow_id: int, step_order: int, name: str,
                         step_type: str = StepType.APPROVAL.value,
                         approver_type: Optional[str] = None,
                         approver_id: Optional[int] = None,
                         approver_role: Optional[str] = None,
                         timeout_hours: Optional[int] = None,
                         is_required: bool = True,
                         can_delegate: bool = False,
                         auto_approve: bool = False) -> Optional[int]:
        """إضافة خطوة إلى سير العمل"""
        try:
            query = """
                INSERT INTO workflow_steps (
                    workflow_id, step_order, name, step_type,
                    approver_type, approver_id, approver_role,
                    timeout_hours, is_required, can_delegate, auto_approve,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.now()
            params = (
                workflow_id, step_order, name, step_type,
                approver_type, approver_id, approver_role,
                timeout_hours, 1 if is_required else 0,
                1 if can_delegate else 0, 1 if auto_approve else 0,
                now, now
            )
            
            step_id = self.db_manager.execute_insert(query, params)
            
            if step_id:
                self.logger.info(f"تم إضافة خطوة {step_order} إلى سير العمل {workflow_id}")
                return step_id
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة خطوة: {e}")
            raise
        
        return None
    
    def get_workflows_by_entity_type(self, entity_type: str, 
                                     company_id: Optional[int] = None,
                                     active_only: bool = True) -> List[Workflow]:
        """الحصول على سير العمل لنوع كيان"""
        try:
            query = """
                SELECT id, name, description, entity_type, is_active, is_default,
                       trigger_condition, company_id, created_by,
                       created_at, updated_at
                FROM workflows
                WHERE entity_type = ?
            """
            params = [entity_type]
            
            if active_only:
                query += " AND is_active = 1"
            
            if company_id:
                query += " AND (company_id = ? OR company_id IS NULL)"
                params.append(company_id)
            
            query += " ORDER BY is_default DESC, name ASC"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            return [self.workflow_engine._row_to_workflow(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سير العمل: {e}")
            return []
    
    def get_workflow_with_steps(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على سير العمل مع خطواته"""
        try:
            workflow = self.workflow_engine.get_workflow(workflow_id)
            if not workflow:
                return None
            
            steps = self.workflow_engine.get_workflow_steps(workflow_id)
            
            return {
                'workflow': workflow,
                'steps': steps
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على سير العمل مع الخطوات: {e}")
            return None
    
    # ==================== إدارة مثيلات سير العمل ====================
    
    def start_workflow_for_entity(self, entity_type: str, entity_id: int,
                                  initiated_by: int, workflow_id: Optional[int] = None,
                                  company_id: Optional[int] = None,
                                  notes: str = "", metadata: Dict[str, Any] = None) -> Optional[int]:
        """بدء سير عمل لكيان"""
        try:
            # إذا لم يتم تحديد workflow_id، استخدم الافتراضي
            if not workflow_id:
                workflow = self.workflow_engine.get_workflow_by_entity_type(entity_type, company_id)
                if not workflow:
                    self.logger.warning(f"لا يوجد سير عمل افتراضي لـ {entity_type}")
                    return None
                workflow_id = workflow.id
            
            instance_id = self.workflow_engine.start_workflow(
                workflow_id=workflow_id,
                entity_type=entity_type,
                entity_id=entity_id,
                initiated_by=initiated_by,
                company_id=company_id,
                notes=notes,
                metadata=metadata
            )
            
            if instance_id:
                self.logger.info(f"تم بدء سير العمل {workflow_id} للكيان {entity_type}:{entity_id}")
                
                # إنشاء إشعار للموافقين
                try:
                    instance = self.get_workflow_instance(instance_id)
                    if instance:
                        workflow = self.get_workflow(instance.workflow_id)
                        entity_name = f"{entity_type} #{entity_id}"
                        
                        # الحصول على اسم الكيان
                        conn = self.db_manager.get_connection()
                        cursor = conn.cursor()
                        if entity_type == "purchase_order":
                            po_result = cursor.execute("SELECT po_number FROM purchase_orders WHERE id = ?", (entity_id,)).fetchone()
                            if po_result:
                                entity_name = f"أمر شراء {po_result[0]}"
                        elif entity_type == "sale":
                            sale_result = cursor.execute("SELECT invoice_number FROM sales WHERE id = ?", (entity_id,)).fetchone()
                            if sale_result:
                                entity_name = f"فاتورة {sale_result[0]}"
                        
                        # إشعار للموافق الأول
                        # الحصول على الموافقات المعلقة لهذا المثيل
                        conn = self.db_manager.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT approver_id FROM workflow_approvals
                            WHERE instance_id = ? AND status = 'pending'
                            ORDER BY created_at ASC LIMIT 1
                        """, (instance_id,))
                        approver_result = cursor.fetchone()
                        if approver_result:
                            approver_id = approver_result[0]
                            self._create_workflow_notification(
                                title=f"⏳ موافقة مطلوبة: {workflow.name if workflow else 'سير العمل'}",
                                message=f"يحتاج {entity_name} إلى موافقتك",
                                user_id=approver_id,
                                entity_type=entity_type,
                                entity_id=entity_id,
                                priority=2
                            )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"فشل إنشاء إشعار بدء سير العمل: {e}")
            
            return instance_id
            
        except Exception as e:
            self.logger.error(f"خطأ في بدء سير العمل: {e}")
            raise
    
    def get_pending_approvals_for_user(self, user_id: int, 
                                      company_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """الحصول على الموافقات المعلقة للمستخدم"""
        try:
            query = """
                SELECT 
                    wa.id as approval_id,
                    wa.instance_id,
                    wa.step_id,
                    wa.status,
                    wa.deadline,
                    wa.comments,
                    wi.entity_type,
                    wi.entity_id,
                    wi.status as instance_status,
                    ws.name as step_name,
                    ws.step_order,
                    w.name as workflow_name,
                    u.full_name as initiated_by_name,
                    wi.initiated_at
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                JOIN workflows w ON wi.workflow_id = w.id
                JOIN users u ON wi.initiated_by = u.id
                WHERE wa.approver_id = ? AND wa.status = ?
            """
            params = [user_id, ApprovalStatus.PENDING.value]
            
            if company_id:
                query += " AND wi.company_id = ?"
                params.append(company_id)
            
            query += " ORDER BY wa.deadline ASC, wi.initiated_at DESC"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            return results
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الموافقات المعلقة: {e}")
            return []
    
    def approve(self, approval_id: int, approver_id: int, comments: str = "") -> bool:
        """الموافقة على خطوة"""
        try:
            # الحصول على معلومات الموافقة قبل الموافقة
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wa.instance_id, wi.entity_type, wi.entity_id, ws.name as step_name, wi.initiated_by
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                WHERE wa.id = ?
            """, (approval_id,))
            approval_info = cursor.fetchone()
            
            result = self.workflow_engine.approve_step(approval_id, approver_id, comments)
            if result and approval_info:
                instance_id, entity_type, entity_id, step_name, initiated_by = approval_info
                instance = self.get_workflow_instance(instance_id)
                if instance:
                    entity_name = f"{entity_type} #{entity_id}"
                    
                    # الحصول على اسم الكيان
                    if entity_type == "purchase_order":
                        po_result = cursor.execute("SELECT po_number FROM purchase_orders WHERE id = ?", (entity_id,)).fetchone()
                        if po_result:
                            entity_name = f"أمر شراء {po_result[0]}"
                    elif entity_type == "sale":
                        sale_result = cursor.execute("SELECT invoice_number FROM sales WHERE id = ?", (entity_id,)).fetchone()
                        if sale_result:
                            entity_name = f"فاتورة {sale_result[0]}"
                    
                    # إشعار للموافق التالي
                    conn = self.db_manager.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT approver_id FROM workflow_approvals
                        WHERE instance_id = ? AND status = 'pending'
                        ORDER BY created_at ASC LIMIT 1
                    """, (instance_id,))
                    approver_result = cursor.fetchone()
                    if approver_result:
                        approver_id = approver_result[0]
                        self._create_workflow_notification(
                            title=f"⏳ موافقة مطلوبة: {step_name}",
                            message=f"تمت الموافقة على الخطوة السابقة لـ {entity_name}، تحتاج موافقتك الآن",
                            user_id=approver_id,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            priority=2
                        )
                    
                    # إشعار للمبتدئ عند اكتمال سير العمل (APPROVED)
                    instance_status_query = "SELECT status FROM workflow_instances WHERE id = ?"
                    instance_status_result = cursor.execute(instance_status_query, (instance_id,)).fetchone()
                    if instance_status_result and instance_status_result[0] == WorkflowStatus.APPROVED.value:
                        self._create_workflow_notification(
                            title=f"✅ اكتمال سير العمل: {entity_name}",
                            message=f"تمت الموافقة على جميع الخطوات واكتمل سير العمل",
                            user_id=initiated_by,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            priority=1
                        )
            
            return result
        except Exception as e:
            self.logger.error(f"خطأ في الموافقة: {e}")
            raise
    
    def reject(self, approval_id: int, approver_id: int, comments: str = "") -> bool:
        """رفض خطوة"""
        try:
            # الحصول على معلومات الموافقة قبل الرفض
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wa.instance_id, wi.entity_type, wi.entity_id, ws.name as step_name, wi.initiated_by
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                WHERE wa.id = ?
            """, (approval_id,))
            approval_info = cursor.fetchone()
            
            result = self.workflow_engine.reject_step(approval_id, approver_id, comments)
            if result and approval_info:
                instance_id, entity_type, entity_id, step_name, initiated_by = approval_info
                entity_name = f"{entity_type} #{entity_id}"
                
                # الحصول على اسم الكيان
                if entity_type == "purchase_order":
                    po_result = cursor.execute("SELECT po_number FROM purchase_orders WHERE id = ?", (entity_id,)).fetchone()
                    if po_result:
                        entity_name = f"أمر شراء {po_result[0]}"
                elif entity_type == "sale":
                    sale_result = cursor.execute("SELECT invoice_number FROM sales WHERE id = ?", (entity_id,)).fetchone()
                    if sale_result:
                        entity_name = f"فاتورة {sale_result[0]}"
                
                self._create_workflow_notification(
                    title=f"❌ رفض في سير العمل: {entity_name}",
                    message=f"تم رفض الخطوة '{step_name}' في سير العمل. السبب: {comments or 'لم يتم تحديد سبب'}",
                    user_id=initiated_by,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    priority=3
                )
            
            return result
        except Exception as e:
            self.logger.error(f"خطأ في الرفض: {e}")
            raise
    
    def get_workflow_status(self, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على حالة سير العمل لكيان"""
        try:
            instance = self.workflow_engine.get_instance_by_entity(entity_type, entity_id)
            if not instance:
                return None
            
            workflow = self.workflow_engine.get_workflow(instance.workflow_id)
            current_step = None
            if instance.current_step_id:
                current_step = self.workflow_engine._get_step(instance.current_step_id)
            
            # الحصول على الموافقات الحالية
            approvals = []
            if instance.current_step_id:
                query = """
                    SELECT wa.*, u.full_name as approver_name
                    FROM workflow_approvals wa
                    LEFT JOIN users u ON wa.approver_id = u.id
                    WHERE wa.instance_id = ? AND wa.step_id = ?
                """
                approvals = self.db_manager.fetch_all(query, (instance.id, instance.current_step_id))
            
            # الحصول على التاريخ
            history_query = """
                SELECT wh.*, u.full_name as performed_by_name
                FROM workflow_history wh
                LEFT JOIN users u ON wh.performed_by = u.id
                WHERE wh.instance_id = ?
                ORDER BY wh.performed_at ASC
            """
            history = self.db_manager.fetch_all(history_query, (instance.id,))
            
            return {
                'instance': instance,
                'workflow': workflow,
                'current_step': current_step,
                'approvals': approvals,
                'history': history
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على حالة سير العمل: {e}")
            return None
    
    def cancel_workflow(self, instance_id: int, cancelled_by: int, reason: str = "") -> bool:
        """إلغاء سير العمل"""
        try:
            instance = self.workflow_engine._get_instance(instance_id)
            if not instance:
                raise ValueError(f"مثيل سير العمل غير موجود: {instance_id}")
            
            if instance.status in [WorkflowStatus.APPROVED.value, WorkflowStatus.REJECTED.value]:
                raise ValueError(f"لا يمكن إلغاء سير العمل في حالة {instance.status}")
            
            query = """
                UPDATE workflow_instances
                SET status = ?, completed_at = ?, completed_by = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """
            now = datetime.now()
            notes = f"{instance.notes}\n[ملغي] {reason}" if instance.notes else f"[ملغي] {reason}"
            
            self.db_manager.execute_query(query, (
                WorkflowStatus.CANCELLED.value, now, cancelled_by, notes, now, instance_id
            ))
            
            # تسجيل في التاريخ
            self.workflow_engine._add_history(instance_id, None, "cancelled", cancelled_by, reason)
            
            self.logger.info(f"تم إلغاء سير العمل {instance_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في إلغاء سير العمل: {e}")
            raise
    
    def delegate_approval(self, approval_id: int, approver_id: int,
                         delegated_to_id: int, comments: str = "") -> bool:
        """تفويض الموافقة لمستخدم آخر"""
        try:
            approval = self.workflow_engine._get_approval(approval_id)
            if not approval:
                raise ValueError(f"الموافقة غير موجودة: {approval_id}")
            
            if approval.approver_id != approver_id:
                raise ValueError("ليس لديك صلاحية تفويض هذه الموافقة")
            
            step = self.workflow_engine._get_step(approval.step_id)
            if not step or not step.can_delegate:
                raise ValueError("هذه الخطوة لا تدعم التفويض")
            
            # تحديث الموافقة
            query = """
                UPDATE workflow_approvals
                SET status = ?, decision = 'delegate', delegated_to = ?,
                    comments = ?, updated_at = ?
                WHERE id = ?
            """
            now = datetime.now()
            comments_with_delegation = f"{comments}\n[مفوض إلى: {delegated_to_id}]" if comments else f"[مفوض إلى: {delegated_to_id}]"
            
            self.db_manager.execute_query(query, (
                ApprovalStatus.DELEGATED.value, delegated_to_id,
                comments_with_delegation, now, approval_id
            ))
            
            # إنشاء موافقة جديدة للمفوض إليه
            new_approval_query = """
                INSERT INTO workflow_approvals (
                    instance_id, step_id, approver_id, status,
                    deadline, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            deadline = approval.deadline
            self.db_manager.execute_query(new_approval_query, (
                approval.instance_id, approval.step_id, delegated_to_id,
                ApprovalStatus.PENDING.value, deadline, now, now
            ))
            
            # تسجيل في التاريخ
            self.workflow_engine._add_history(
                approval.instance_id, approval.step_id,
                "delegated", approver_id,
                f"مفوض إلى المستخدم {delegated_to_id}: {comments}"
            )
            
            self.logger.info(f"تم تفويض الموافقة {approval_id} إلى {delegated_to_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في التفويض: {e}")
            raise
    
    def get_workflow_statistics(self, company_id: Optional[int] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """الحصول على إحصائيات سير العمل"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_instances,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count
                FROM workflow_instances
                WHERE 1=1
            """
            params = []
            
            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)
            
            if start_date:
                query += " AND initiated_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND initiated_at <= ?"
                params.append(end_date)
            
            result = self.db_manager.fetch_one(query, tuple(params))
            
            # إحصائيات الموافقات
            approval_query = """
                SELECT 
                    COUNT(*) as total_approvals,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_approvals,
                    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_approvals,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_approvals
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                WHERE 1=1
            """
            approval_params = []
            
            if company_id:
                approval_query += " AND wi.company_id = ?"
                approval_params.append(company_id)
            
            if start_date:
                approval_query += " AND wa.created_at >= ?"
                approval_params.append(start_date)
            
            if end_date:
                approval_query += " AND wa.created_at <= ?"
                approval_params.append(end_date)
            
            approval_result = self.db_manager.fetch_one(approval_query, tuple(approval_params))
            
            return {
                'instances': result or {},
                'approvals': approval_result or {}
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الإحصائيات: {e}")
            return {'instances': {}, 'approvals': {}}
    
    def check_expired_approvals(self) -> List[Dict[str, Any]]:
        """التحقق من الموافقات المنتهية الصلاحية"""
        try:
            query = """
                SELECT wa.*, wi.entity_type, wi.entity_id, ws.name as step_name
                FROM workflow_approvals wa
                JOIN workflow_instances wi ON wa.instance_id = wi.id
                JOIN workflow_steps ws ON wa.step_id = ws.id
                WHERE wa.status = ? AND wa.deadline IS NOT NULL AND wa.deadline < ?
            """
            now = datetime.now()
            results = self.db_manager.fetch_all(query, (ApprovalStatus.PENDING.value, now))
            
            return results
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من الموافقات المنتهية: {e}")
            return []

