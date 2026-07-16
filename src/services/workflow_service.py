"""
خدمة سير العمل - WorkflowService
Rules engine + CRUD wrapper around WorkflowEngine tables.
"""
import logging

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.workflow_engine import Workflow, WorkflowEngine
from src.utils.logger import setup_logger


class WorkflowService:
    """
    The 'Autopilot': Automated Rules Engine.
    Executes actions based on triggers, and manages workflow CRUD.
    """

    def __init__(self, db_manager, notification_manager=None):
        self.db = db_manager
        self.notify = notification_manager
        self._engine = WorkflowEngine(db_manager)
        self.logger = setup_logger(__name__)

    # ------------------------------------------------------------------
    # Trigger-based Autopilot (original logic)
    # ------------------------------------------------------------------

    def check_triggers(self, event_type, data):
        """
        Evaluate rules for a given event.
        Events: 'sale_created', 'stock_updated', 'invoice_paid'
        """
        if event_type == "stock_updated":
            self._check_low_stock(data)
        elif event_type == "sale_created":
            self._check_high_value_sale(data)

    def _check_low_stock(self, product_data):
        """Rule: If Stock < Min Stock -> Notify Manager"""
        current = product_data.get("current_stock", 0)
        minimum = product_data.get("min_stock", 0)
        if current <= minimum:
            msg = f"⚠️ Low Stock Alert: {product_data.get('name')} " f"is below minimum ({current}/{minimum})"
            print(f"[Autopilot] {msg}")
            if self.notify:
                self.notify.show_warning(msg)

    def _check_high_value_sale(self, sale_data):
        """Rule: If Sale > 100,000 DA -> Flag as VIP"""
        total = sale_data.get("total_amount", 0)
        if total > 100000:
            msg = f"🌟 VIP Sale: Invoice #{sale_data.get('invoice_number')} " f"is {total:,.2f} DA!"
            print(f"[Autopilot] {msg}")
            if self.notify:
                self.notify.show_success(msg)

    # ------------------------------------------------------------------
    # Workflow CRUD – used by WorkflowDesignerWindow
    # ------------------------------------------------------------------

    def get_workflows_by_entity_type(self, entity_type: str, active_only: bool = True) -> List[Workflow]:
        """Return ALL workflows for the given entity type (not just the default)."""
        try:
            query = """
                SELECT id, name, description, entity_type, is_active, is_default,
                       trigger_condition, company_id, created_by,
                       created_at, updated_at
                FROM workflows
                WHERE entity_type = ?
            """
            params: list = [entity_type]
            if active_only:
                query += " AND is_active = 1"
            query += " ORDER BY is_default DESC, id DESC"

            rows = self.db.fetch_all(query, tuple(params))
            return [self._engine._row_to_workflow(row) for row in rows]
        except Exception as e:
            self.logger.error(f"get_workflows_by_entity_type error: {e}")
            return []

    def get_workflow_with_steps(self, workflow_id: int) -> Optional[Dict[str, Any]]:
        """Return {'workflow': Workflow, 'steps': [WorkflowStep]} or None."""
        try:
            workflow = self._engine.get_workflow(workflow_id)
            if not workflow:
                return None
            steps = self._engine.get_workflow_steps(workflow_id)
            return {"workflow": workflow, "steps": steps}
        except Exception as e:
            self.logger.error(f"get_workflow_with_steps error: {e}")
            return None

    def create_workflow(
        self,
        name: str,
        entity_type: str,
        description: str = "",
        is_active: bool = True,
        is_default: bool = False,
    ) -> Optional[int]:
        """Insert a new workflow row. Returns the new ID or None on failure."""
        try:
            now = datetime.now().isoformat()
            query = """
                INSERT INTO workflows
                    (name, description, entity_type, is_active, is_default,
                     trigger_condition, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, '', ?, ?)
            """
            params = (
                name,
                description,
                entity_type,
                1 if is_active else 0,
                1 if is_default else 0,
                now,
                now,
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"create_workflow error: {e}")
            return None

    def add_workflow_step(
        self,
        workflow_id: int,
        step_order: int,
        name: str,
        step_type: str,
        approver_type: Optional[str] = None,
        approver_id: Optional[int] = None,
        approver_role: Optional[str] = None,
        timeout_hours: Optional[int] = None,
        is_required: bool = True,
        can_delegate: bool = False,
        auto_approve: bool = False,
    ) -> Optional[int]:
        """Insert a workflow step. Returns the new step ID or None on failure."""
        try:
            now = datetime.now().isoformat()
            query = """
                INSERT INTO workflow_steps
                    (workflow_id, step_order, name, step_type,
                     approver_type, approver_id, approver_role,
                     condition_expression, action_config,
                     timeout_hours, is_required, can_delegate, auto_approve,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, '', '', ?, ?, ?, ?, ?, ?)
            """
            params = (
                workflow_id,
                step_order,
                name,
                step_type,
                approver_type,
                approver_id,
                approver_role,
                timeout_hours,
                1 if is_required else 0,
                1 if can_delegate else 0,
                1 if auto_approve else 0,
                now,
                now,
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"add_workflow_step error: {e}")
            return None
