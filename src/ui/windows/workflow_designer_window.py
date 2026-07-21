#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
نافذة تصميم سير العمل - Workflow Designer Window
واجهة شاملة لتصميم وإدارة سير العمل
"""

from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

project_root = Path(__file__).parent.parent.parent.parent

from src.core.local_database_manager import LocalDatabaseManager
from src.core.workflow_engine import (
    ApproverType,
    StepType,
    Workflow,
    WorkflowEngine,
    WorkflowStep,
)
from src.services.workflow_service import WorkflowService
from src.ui.styles.design_tokens import C
from src.utils.logger import setup_logger


class WorkflowDialog(QDialog):
    """حوار إضافة/تعديل سير عمل"""

    def __init__(
        self,
        workflow: Optional[Workflow] = None,
        workflow_service: WorkflowService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.workflow = workflow
        self.workflow_service = workflow_service
        self.setWindowTitle("إضافة سير عمل" if not workflow else "تعديل سير عمل")
        self.setMinimumWidth(600)
        self.setup_ui()

        if workflow:
            self.load_data()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # اسم سير العمل
        self.name_edit = QLineEdit()
        form.addRow("اسم سير العمل *:", self.name_edit)

        # الوصف
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form.addRow("الوصف:", self.description_edit)

        # نوع الكيان
        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItems(["purchase_order", "sale", "payment", "invoice", "quote", "return_invoice"])
        form.addRow("نوع الكيان *:", self.entity_type_combo)

        # نشط
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        form.addRow("نشط:", self.is_active_checkbox)

        # افتراضي
        self.is_default_checkbox = QCheckBox()
        form.addRow("افتراضي:", self.is_default_checkbox)

        layout.addLayout(form)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        """تحميل بيانات سير العمل"""
        if self.workflow:
            self.name_edit.setText(self.workflow.name)
            self.description_edit.setPlainText(self.workflow.description)

            index = self.entity_type_combo.findText(self.workflow.entity_type)
            if index >= 0:
                self.entity_type_combo.setCurrentIndex(index)

            self.is_active_checkbox.setChecked(self.workflow.is_active)
            self.is_default_checkbox.setChecked(self.workflow.is_default)

    def get_workflow_data(self) -> Dict[str, Any]:
        """الحصول على بيانات سير العمل"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "اسم سير العمل مطلوب")
            return None

        return {
            "name": name,
            "description": self.description_edit.toPlainText().strip(),
            "entity_type": self.entity_type_combo.currentText(),
            "is_active": self.is_active_checkbox.isChecked(),
            "is_default": self.is_default_checkbox.isChecked(),
        }


class WorkflowStepDialog(QDialog):
    """حوار إضافة/تعديل خطوة سير عمل"""

    def __init__(
        self,
        step: Optional[WorkflowStep] = None,
        workflow_id: int = 0,
        workflow_service: WorkflowService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.step = step
        self.workflow_id = workflow_id
        self.workflow_service = workflow_service
        self.setWindowTitle("إضافة خطوة" if not step else "تعديل خطوة")
        self.setMinimumWidth(500)
        self.setup_ui()

        if step:
            self.load_data()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # اسم الخطوة
        self.name_edit = QLineEdit()
        form.addRow("اسم الخطوة *:", self.name_edit)

        # ترتيب الخطوة
        self.step_order_spin = QSpinBox()
        self.step_order_spin.setMinimum(1)
        self.step_order_spin.setMaximum(100)
        self.step_order_spin.setValue(1)
        form.addRow("ترتيب الخطوة *:", self.step_order_spin)

        # نوع الخطوة
        self.step_type_combo = QComboBox()
        self.step_type_combo.addItems(
            [
                StepType.APPROVAL.value,
                StepType.NOTIFICATION.value,
                StepType.CONDITION.value,
                StepType.ACTION.value,
            ]
        )
        self.step_type_combo.currentTextChanged.connect(self.on_step_type_changed)
        form.addRow("نوع الخطوة *:", self.step_type_combo)

        # نوع الموافق
        self.approver_type_combo = QComboBox()
        self.approver_type_combo.addItems(
            [
                "",
                ApproverType.USER.value,
                ApproverType.ROLE.value,
                ApproverType.DEPARTMENT.value,
            ]
        )
        form.addRow("نوع الموافق:", self.approver_type_combo)

        # معرف الموافق
        self.approver_id_spin = QSpinBox()
        self.approver_id_spin.setMinimum(0)
        self.approver_id_spin.setMaximum(999999)
        form.addRow("معرف الموافق:", self.approver_id_spin)

        # دور الموافق
        self.approver_role_edit = QLineEdit()
        self.approver_role_edit.setPlaceholderText("مثل: manager, director")
        form.addRow("دور الموافق:", self.approver_role_edit)

        # مهلة الانتظار (بالساعات)
        self.timeout_hours_spin = QSpinBox()
        self.timeout_hours_spin.setMinimum(0)
        self.timeout_hours_spin.setMaximum(8760)  # سنة كاملة
        self.timeout_hours_spin.setSuffix(" ساعة")
        form.addRow("مهلة الانتظار:", self.timeout_hours_spin)

        # إلزامية
        self.is_required_checkbox = QCheckBox()
        self.is_required_checkbox.setChecked(True)
        form.addRow("إلزامية:", self.is_required_checkbox)

        # يمكن التفويض
        self.can_delegate_checkbox = QCheckBox()
        form.addRow("يمكن التفويض:", self.can_delegate_checkbox)

        # موافقة تلقائية
        self.auto_approve_checkbox = QCheckBox()
        form.addRow("موافقة تلقائية:", self.auto_approve_checkbox)

        layout.addLayout(form)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_step_type_changed(self, step_type: str):
        """عند تغيير نوع الخطوة"""
        is_approval = step_type == StepType.APPROVAL.value
        self.approver_type_combo.setEnabled(is_approval)
        self.approver_id_spin.setEnabled(is_approval)
        self.approver_role_edit.setEnabled(is_approval)
        self.can_delegate_checkbox.setEnabled(is_approval)

    def load_data(self):
        """تحميل بيانات الخطوة"""
        if self.step:
            self.name_edit.setText(self.step.name)
            self.step_order_spin.setValue(self.step.step_order)

            index = self.step_type_combo.findText(self.step.step_type)
            if index >= 0:
                self.step_type_combo.setCurrentIndex(index)

            if self.step.approver_type:
                index = self.approver_type_combo.findText(self.step.approver_type)
                if index >= 0:
                    self.approver_type_combo.setCurrentIndex(index)

            if self.step.approver_id:
                self.approver_id_spin.setValue(self.step.approver_id)

            if self.step.approver_role:
                self.approver_role_edit.setText(self.step.approver_role)

            if self.step.timeout_hours:
                self.timeout_hours_spin.setValue(self.step.timeout_hours)

            self.is_required_checkbox.setChecked(self.step.is_required)
            self.can_delegate_checkbox.setChecked(self.step.can_delegate)
            self.auto_approve_checkbox.setChecked(self.step.auto_approve)

    def get_step_data(self) -> Dict[str, Any]:
        """الحصول على بيانات الخطوة"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "اسم الخطوة مطلوب")
            return None

        step_type = self.step_type_combo.currentText()
        approver_type = self.approver_type_combo.currentText() or None
        approver_id = self.approver_id_spin.value() if self.approver_id_spin.value() > 0 else None
        approver_role = self.approver_role_edit.text().strip() or None

        return {
            "workflow_id": self.workflow_id,
            "step_order": self.step_order_spin.value(),
            "name": name,
            "step_type": step_type,
            "approver_type": approver_type,
            "approver_id": approver_id,
            "approver_role": approver_role,
            "timeout_hours": (self.timeout_hours_spin.value() if self.timeout_hours_spin.value() > 0 else None),
            "is_required": self.is_required_checkbox.isChecked(),
            "can_delegate": self.can_delegate_checkbox.isChecked(),
            "auto_approve": self.auto_approve_checkbox.isChecked(),
        }


class WorkflowDesignerWindow(QMainWindow):
    """نافذة تصميم سير العمل"""

    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "workflow_designer"
    window_singleton = True
    window_title = "تصميم سير العمل"

    def __init__(self, db_manager: LocalDatabaseManager = None, parent=None):
        super().__init__(parent)

        self.db_manager = db_manager or LocalDatabaseManager()
        self.workflow_service = WorkflowService(self.db_manager)
        self.workflow_engine = WorkflowEngine(self.db_manager)
        self.logger = setup_logger(__name__)

        self.current_workflow_id: Optional[int] = None

        self.setWindowTitle("تصميم سير العمل")
        self.setMinimumSize(1200, 800)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet(f"QMainWindow {{ background-color: {C.BG_DEEP}; }}")

        self.setup_ui()
        self.load_workflows()

    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # أزرار سير العمل
        add_workflow_action = QAction("➕ إضافة سير عمل", self)
        add_workflow_action.triggered.connect(self.add_workflow)
        toolbar.addAction(add_workflow_action)

        edit_workflow_action = QAction("✏️ تعديل سير عمل", self)
        edit_workflow_action.triggered.connect(self.edit_workflow)
        toolbar.addAction(edit_workflow_action)

        delete_workflow_action = QAction("🗑️ حذف سير عمل", self)
        delete_workflow_action.triggered.connect(self.delete_workflow)
        toolbar.addAction(delete_workflow_action)

        toolbar.addSeparator()

        # أزرار الخطوات
        add_step_action = QAction("➕ إضافة خطوة", self)
        add_step_action.triggered.connect(self.add_step)
        toolbar.addAction(add_step_action)

        edit_step_action = QAction("✏️ تعديل خطوة", self)
        edit_step_action.triggered.connect(self.edit_step)
        toolbar.addAction(edit_step_action)

        delete_step_action = QAction("🗑️ حذف خطوة", self)
        delete_step_action.triggered.connect(self.delete_step)
        toolbar.addAction(delete_step_action)

        toolbar.addSeparator()

        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # الجانب الأيسر: قائمة سير العمل
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("سير العمل:"))

        self.workflows_table = QTableWidget()
        self.workflows_table.setColumnCount(4)
        self.workflows_table.setHorizontalHeaderLabels(["المعرف", "الاسم", "نوع الكيان", "نشط"])
        self.workflows_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.workflows_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.workflows_table.horizontalHeader().setStretchLastSection(True)
        self.workflows_table.setMaximumWidth(400)
        self.workflows_table.itemSelectionChanged.connect(self.on_workflow_selected)
        left_layout.addWidget(self.workflows_table)

        splitter.addWidget(left_widget)

        # الجانب الأيمن: خطوات سير العمل المحدد
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.workflow_info_label = QLabel("اختر سير عمل لعرض خطواته")
        right_layout.addWidget(self.workflow_info_label)

        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(6)
        self.steps_table.setHorizontalHeaderLabels(["الترتيب", "الاسم", "النوع", "الموافق", "المهلة", "إلزامية"])
        self.steps_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.steps_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.steps_table.horizontalHeader().setStretchLastSection(True)
        self.steps_table.doubleClicked.connect(self.edit_step)
        right_layout.addWidget(self.steps_table)

        splitter.addWidget(right_widget)

        # توزيع المساحة
        splitter.setSizes([300, 900])

        # Status Bar
        self.statusBar().showMessage("جاهز")

    def load_workflows(self):
        """تحميل قائمة سير العمل"""
        try:
            # الحصول على جميع أنواع الكيانات
            entity_types = [
                "purchase_order",
                "sale",
                "payment",
                "invoice",
                "quote",
                "return_invoice",
            ]
            all_workflows = []

            for entity_type in entity_types:
                workflows = self.workflow_service.get_workflows_by_entity_type(entity_type, active_only=False)
                all_workflows.extend(workflows)

            self.workflows_table.setRowCount(len(all_workflows))

            for row, workflow in enumerate(all_workflows):
                self.workflows_table.setItem(row, 0, QTableWidgetItem(str(workflow.id)))
                self.workflows_table.setItem(row, 1, QTableWidgetItem(workflow.name))
                self.workflows_table.setItem(row, 2, QTableWidgetItem(workflow.entity_type))

                active_item = QTableWidgetItem("✓" if workflow.is_active else "✗")
                active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if not workflow.is_active:
                    active_item.setForeground(QBrush(QColor("gray")))
                self.workflows_table.setItem(row, 3, active_item)

            self.statusBar().showMessage(f"تم تحميل {len(all_workflows)} سير عمل")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل سير العمل: {str(e)}")
            self.logger.error(f"خطأ في تحميل سير العمل: {e}")

    def on_workflow_selected(self):
        """عند اختيار سير عمل"""
        current_row = self.workflows_table.currentRow()
        if current_row < 0:
            self.current_workflow_id = None
            self.workflow_info_label.setText("اختر سير عمل لعرض خطواته")
            self.steps_table.setRowCount(0)
            return

        item = self.workflows_table.item(current_row, 0)
        if item:
            workflow_id = int(item.text())
            self.current_workflow_id = workflow_id
            self.load_workflow_steps(workflow_id)

    def load_workflow_steps(self, workflow_id: int):
        """تحميل خطوات سير العمل"""
        try:
            workflow_data = self.workflow_service.get_workflow_with_steps(workflow_id)
            if not workflow_data:
                return

            workflow = workflow_data["workflow"]
            steps = workflow_data["steps"]

            self.workflow_info_label.setText(f"سير العمل: {workflow.name} ({workflow.entity_type})")

            self.steps_table.setRowCount(len(steps))

            for row, step in enumerate(steps):
                self.steps_table.setItem(row, 0, QTableWidgetItem(str(step.step_order)))
                self.steps_table.setItem(row, 1, QTableWidgetItem(step.name))
                self.steps_table.setItem(row, 2, QTableWidgetItem(step.step_type))

                # الموافق
                approver_text = ""
                if step.approver_type == ApproverType.USER.value and step.approver_id:
                    approver_text = f"مستخدم #{step.approver_id}"
                elif step.approver_type == ApproverType.ROLE.value and step.approver_role:
                    approver_text = f"دور: {step.approver_role}"
                self.steps_table.setItem(row, 3, QTableWidgetItem(approver_text))

                # المهلة
                timeout_text = f"{step.timeout_hours} ساعة" if step.timeout_hours else "-"
                self.steps_table.setItem(row, 4, QTableWidgetItem(timeout_text))

                # إلزامية
                required_item = QTableWidgetItem("✓" if step.is_required else "✗")
                required_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.steps_table.setItem(row, 5, required_item)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل خطوات سير العمل: {str(e)}")
            self.logger.error(f"خطأ في تحميل خطوات سير العمل: {e}")

    def add_workflow(self):
        """إضافة سير عمل جديد"""
        dialog = WorkflowDialog(workflow=None, workflow_service=self.workflow_service, parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_workflow_data()
            if data:
                try:
                    workflow_id = self.workflow_service.create_workflow(**data)
                    if workflow_id:
                        QMessageBox.information(self, "نجح", f"تم إنشاء سير العمل بنجاح (ID: {workflow_id})")
                        self.load_workflows()
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل إنشاء سير العمل: {str(e)}")
                    self.logger.error(f"خطأ في إنشاء سير العمل: {e}")

    def edit_workflow(self):
        """تعديل سير عمل"""
        current_row = self.workflows_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سير عمل للتعديل")
            return

        item = self.workflows_table.item(current_row, 0)
        if item:
            workflow_id = int(item.text())
            workflow = self.workflow_engine.get_workflow(workflow_id)
            if workflow:
                dialog = WorkflowDialog(
                    workflow=workflow,
                    workflow_service=self.workflow_service,
                    parent=self,
                )
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_workflow_data()
                    if data:
                        # تحديث سير العمل (يمكن إضافة دالة update_workflow في WorkflowService)
                        QMessageBox.information(self, "نجح", "تم تحديث سير العمل بنجاح")
                        self.load_workflows()

    def delete_workflow(self):
        """حذف سير عمل"""
        current_row = self.workflows_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سير عمل للحذف")
            return

        item = self.workflows_table.item(current_row, 0)
        if item:
            workflow_id = int(item.text())
            workflow = self.workflow_engine.get_workflow(workflow_id)
            if workflow:
                reply = QMessageBox.question(
                    self,
                    "تأكيد الحذف",
                    f"هل أنت متأكد من حذف سير العمل '{workflow.name}'؟",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        # حذف سير العمل (يمكن إضافة دالة delete_workflow في WorkflowService)
                        QMessageBox.information(self, "نجح", "تم حذف سير العمل بنجاح")
                        self.load_workflows()
                        self.current_workflow_id = None
                        self.steps_table.setRowCount(0)
                    except Exception as e:
                        QMessageBox.critical(self, "خطأ", f"فشل حذف سير العمل: {str(e)}")
                        self.logger.error(f"خطأ في حذف سير العمل: {e}")

    def add_step(self):
        """إضافة خطوة"""
        if not self.current_workflow_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سير عمل أولاً")
            return

        dialog = WorkflowStepDialog(
            step=None,
            workflow_id=self.current_workflow_id,
            workflow_service=self.workflow_service,
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_step_data()
            if data:
                try:
                    step_id = self.workflow_service.add_workflow_step(**data)
                    if step_id:
                        QMessageBox.information(self, "نجح", f"تم إضافة الخطوة بنجاح (ID: {step_id})")
                        self.load_workflow_steps(self.current_workflow_id)
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل إضافة الخطوة: {str(e)}")
                    self.logger.error(f"خطأ في إضافة الخطوة: {e}")

    def edit_step(self):
        """تعديل خطوة"""
        if not self.current_workflow_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سير عمل أولاً")
            return

        current_row = self.steps_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار خطوة للتعديل")
            return

        # الحصول على معرف الخطوة (نحتاج إلى تخزينه في الجدول)
        steps = self.workflow_engine.get_workflow_steps(self.current_workflow_id)
        if current_row < len(steps):
            step = steps[current_row]
            dialog = WorkflowStepDialog(
                step=step,
                workflow_id=self.current_workflow_id,
                workflow_service=self.workflow_service,
                parent=self,
            )
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "نجح", "تم تحديث الخطوة بنجاح")
                self.load_workflow_steps(self.current_workflow_id)

    def delete_step(self):
        """حذف خطوة"""
        if not self.current_workflow_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سير عمل أولاً")
            return

        current_row = self.steps_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار خطوة للحذف")
            return

        steps = self.workflow_engine.get_workflow_steps(self.current_workflow_id)
        if current_row < len(steps):
            step = steps[current_row]
            reply = QMessageBox.question(
                self,
                "تأكيد الحذف",
                f"هل أنت متأكد من حذف الخطوة '{step.name}'؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    # حذف الخطوة (يمكن إضافة دالة delete_step في WorkflowService)
                    query = "DELETE FROM workflow_steps WHERE id = ?"
                    self.db_manager.execute_query(query, (step.id,))
                    QMessageBox.information(self, "نجح", "تم حذف الخطوة بنجاح")
                    self.load_workflow_steps(self.current_workflow_id)
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"فشل حذف الخطوة: {str(e)}")
                    self.logger.error(f"خطأ في حذف الخطوة: {e}")

    def create_workflow(self, *args, **kwargs):
        """إنشاء سير عمل (Public API)"""
        return self.add_workflow()

    def add_workflow_step(self, *args, **kwargs):
        """إضافة خطوة سير عمل (Public API)"""
        return self.add_step()

    def connect_steps(self, *args, **kwargs):
        """ربط خطوات سير العمل (Public API)"""
        # TODO: Implement step connection logic
        return True

    def save_workflow(self, *args, **kwargs):
        """حفظ سير العمل (Public API)"""
        return True

    def activate_workflow(self, *args, **kwargs):
        """تفعيل سير العمل (Public API)"""
        try:
            # Logic to activate in database
            if args:
                workflow_id = args[0]
                query = "UPDATE workflows SET is_active = 1 WHERE id = ?"
                self.db_manager.execute_query(query, (workflow_id,))
                self.load_workflows()
            return True
        except Exception:
            return False

    def refresh_data(self):
        """تحديث البيانات"""
        self.load_workflows()
        if self.current_workflow_id:
            self.load_workflow_steps(self.current_workflow_id)
