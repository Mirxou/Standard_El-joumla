"""
Payment Plans Window - نافذة إدارة خطط الدفع
يدير عرض وتحرير خطط الدفع والأقساط
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QComboBox, QLineEdit, QDateEdit, QMessageBox, QDialog,
    QGroupBox, QGridLayout, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from typing import List, Dict, Optional
from datetime import datetime, date

from ...services.payment_plan_service import PaymentPlanService
from ...models.payment_plan import PaymentPlan, PaymentPlanStatus, InstallmentStatus
from ...core.database_manager import DatabaseManager


class PaymentPlansWindow(QWidget):
    """نافذة إدارة خطط الدفع"""
    
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "payment_plans"
    window_singleton = True
    window_title = "إدارة خطط الدفع"
    
    plan_updated = Signal()  # إشارة عند تحديث خطة
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = PaymentPlanService(db_manager)
        self.current_plan: Optional[PaymentPlan] = None
        
        self.setup_ui()
        self.load_payment_plans()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("إدارة خطط الدفع والتقسيط")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # أدوات التصفية
        filter_group = self.create_filter_section()
        layout.addWidget(filter_group)
        
        # علامات التبويب
        self.tabs = QTabWidget()
        
        # تبويب قائمة الخطط
        plans_tab = QWidget()
        plans_layout = QVBoxLayout(plans_tab)
        
        # أزرار الإجراءات
        actions_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ خطة جديدة")
        self.new_btn.clicked.connect(self.create_new_plan)
        actions_layout.addWidget(self.new_btn)
        
        self.edit_btn = QPushButton("✏️ تعديل")
        self.edit_btn.clicked.connect(self.edit_selected_plan)
        self.edit_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_btn)
        
        self.view_btn = QPushButton("👁️ عرض التفاصيل")
        self.view_btn.clicked.connect(self.view_plan_details)
        self.view_btn.setEnabled(False)
        actions_layout.addWidget(self.view_btn)
        
        self.payment_btn = QPushButton("💰 تسجيل دفعة")
        self.payment_btn.clicked.connect(self.record_payment)
        self.payment_btn.setEnabled(False)
        actions_layout.addWidget(self.payment_btn)
        
        self.cancel_btn = QPushButton("❌ إلغاء الخطة")
        self.cancel_btn.clicked.connect(self.cancel_plan)
        self.cancel_btn.setEnabled(False)
        actions_layout.addWidget(self.cancel_btn)
        
        actions_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.clicked.connect(self.load_payment_plans)
        actions_layout.addWidget(self.refresh_btn)
        
        plans_layout.addLayout(actions_layout)
        
        # جدول خطط الدفع
        self.plans_table = QTableWidget()
        self.plans_table.setColumnCount(14)
        self.plans_table.setHorizontalHeaderLabels([
            "رقم الخطة", "العميل", "الفاتورة", "تاريخ البدء",
            "المبلغ الكلي", "المقدم", "المبلغ المقسط", "عدد الأقساط",
            "المدفوع", "المتبقي", "الغرامات", "نسبة الإنجاز",
            "الحالة", "الملاحظات"
        ])
        
        self.plans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.plans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.plans_table.setSelectionMode(QTableWidget.SingleSelection)
        self.plans_table.setAlternatingRowColors(True)
        self.plans_table.itemSelectionChanged.connect(self.on_plan_selected)
        self.plans_table.cellDoubleClicked.connect(self.view_plan_details)
        
        plans_layout.addWidget(self.plans_table)
        
        self.tabs.addTab(plans_tab, "قائمة الخطط")
        
        # تبويب الأقساط المستحقة
        upcoming_tab = self.create_upcoming_installments_tab()
        self.tabs.addTab(upcoming_tab, "الأقساط القادمة")
        
        # تبويب الأقساط المتأخرة
        overdue_tab = self.create_overdue_installments_tab()
        self.tabs.addTab(overdue_tab, "الأقساط المتأخرة")
        
        # تبويب الإحصائيات
        stats_tab = self.create_statistics_tab()
        self.tabs.addTab(stats_tab, "الإحصائيات")
        
        layout.addWidget(self.tabs)
        
        # شريط الحالة
        status_layout = QHBoxLayout()
        self.status_label = QLabel("جاهز")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
    def create_filter_section(self) -> QGroupBox:
        """إنشاء قسم التصفية"""
        group = QGroupBox("تصفية البحث")
        layout = QHBoxLayout()
        
        # البحث بالعميل
        layout.addWidget(QLabel("العميل:"))
        self.customer_filter = QLineEdit()
        self.customer_filter.setPlaceholderText("اسم العميل...")
        self.customer_filter.textChanged.connect(self.apply_filters)
        layout.addWidget(self.customer_filter)
        
        # حالة الخطة
        layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", None)
        self.status_filter.addItem("مسودة", PaymentPlanStatus.DRAFT.value)
        self.status_filter.addItem("نشطة", PaymentPlanStatus.ACTIVE.value)
        self.status_filter.addItem("مكتملة", PaymentPlanStatus.COMPLETED.value)
        self.status_filter.addItem("ملغية", PaymentPlanStatus.CANCELLED.value)
        self.status_filter.addItem("متعثرة", PaymentPlanStatus.DEFAULTED.value)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        layout.addWidget(self.status_filter)
        
        # من تاريخ
        layout.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        self.from_date.setCalendarPopup(True)
        self.from_date.dateChanged.connect(self.apply_filters)
        layout.addWidget(self.from_date)
        
        # إلى تاريخ
        layout.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate().addMonths(3))
        self.to_date.setCalendarPopup(True)
        self.to_date.dateChanged.connect(self.apply_filters)
        layout.addWidget(self.to_date)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
        
    def create_upcoming_installments_tab(self) -> QWidget:
        """تبويب الأقساط المستحقة قريباً"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # جدول الأقساط القادمة
        self.upcoming_table = QTableWidget()
        self.upcoming_table.setColumnCount(9)
        self.upcoming_table.setHorizontalHeaderLabels([
            "رقم الخطة", "العميل", "رقم القسط", "تاريخ الاستحقاق",
            "المبلغ", "المتبقي", "أيام متبقية", "الحالة", "إجراء"
        ])
        
        self.upcoming_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.upcoming_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.upcoming_table)
        
        return widget
        
    def create_overdue_installments_tab(self) -> QWidget:
        """تبويب الأقساط المتأخرة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # أزرار إجراءات
        actions = QHBoxLayout()
        
        apply_fees_btn = QPushButton("⚠️ تطبيق غرامات التأخير")
        apply_fees_btn.clicked.connect(self.apply_late_fees_to_all)
        actions.addWidget(apply_fees_btn)
        
        actions.addStretch()
        layout.addLayout(actions)
        
        # جدول الأقساط المتأخرة
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(10)
        self.overdue_table.setHorizontalHeaderLabels([
            "رقم الخطة", "العميل", "رقم القسط", "تاريخ الاستحقاق",
            "المبلغ", "المتبقي", "الغرامة", "أيام التأخير",
            "الحالة", "إجراء"
        ])
        
        self.overdue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.overdue_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.overdue_table)
        
        return widget
        
    def create_statistics_tab(self) -> QWidget:
        """تبويب الإحصائيات"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # إحصائيات عامة
        self.stats_labels = {}
        stats = [
            ("total_plans", "إجمالي الخطط"),
            ("active_plans", "الخطط النشطة"),
            ("completed_plans", "الخطط المكتملة"),
            ("total_amount", "المبلغ الكلي"),
            ("total_paid", "المبلغ المدفوع"),
            ("total_remaining", "المبلغ المتبقي"),
            ("total_late_fees", "الغرامات الكلية"),
            ("overdue_count", "الأقساط المتأخرة")
        ]
        
        for i, (key, label) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2
            
            layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 12, QFont.Bold))
            self.stats_labels[key] = value_label
            layout.addWidget(value_label, row, col + 1)
            
        layout.setRowStretch(len(stats) // 2 + 1, 1)
        
        return widget
        
    def load_payment_plans(self):
        """تحميل قائمة خطط الدفع"""
        try:
            self.status_label.setText("جاري تحميل الخطط...")
            
            # الحصول على المرشحات
            customer = self.customer_filter.text() if self.customer_filter.text() else None
            status = self.status_filter.currentData()
            from_date = self.from_date.date().toPython() if hasattr(self.from_date.date(), 'toPython') else None
            to_date = self.to_date.date().toPython() if hasattr(self.to_date.date(), 'toPython') else None
            
            # تحميل الخطط
            plans = self.service.get_all_payment_plans(
                customer_id=None,
                status=status,
                start_date_from=from_date,
                start_date_to=to_date
            )
            
            # تصفية بالعميل إذا تم إدخاله
            if customer:
                plans = [p for p in plans if customer.lower() in (p.customer_name or "").lower()]
            
            self.populate_plans_table(plans)
            
            # تحميل الأقساط القادمة والمتأخرة
            self.load_upcoming_installments()
            self.load_overdue_installments()
            
            # تحديث الإحصائيات
            self.update_statistics()
            
            self.status_label.setText(f"تم تحميل {len(plans)} خطة")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الخطط:\n{str(e)}")
            self.status_label.setText("خطأ في التحميل")
            
    def populate_plans_table(self, plans: List[PaymentPlan]):
        """ملء جدول الخطط"""
        self.plans_table.setRowCount(len(plans))
        
        for row, plan in enumerate(plans):
            # رقم الخطة
            self.plans_table.setItem(row, 0, QTableWidgetItem(plan.plan_number))
            
            # العميل
            self.plans_table.setItem(row, 1, QTableWidgetItem(plan.customer_name or ""))
            
            # الفاتورة
            self.plans_table.setItem(row, 2, QTableWidgetItem(plan.invoice_number or ""))
            
            # تاريخ البدء
            start_str = plan.start_date.strftime("%Y-%m-%d") if plan.start_date else ""
            self.plans_table.setItem(row, 3, QTableWidgetItem(start_str))
            
            # المبالغ
            self.plans_table.setItem(row, 4, QTableWidgetItem(f"{plan.total_amount:,.2f}"))
            self.plans_table.setItem(row, 5, QTableWidgetItem(f"{plan.down_payment:,.2f}"))
            self.plans_table.setItem(row, 6, QTableWidgetItem(f"{plan.financed_amount:,.2f}"))
            self.plans_table.setItem(row, 7, QTableWidgetItem(str(plan.number_of_installments)))
            self.plans_table.setItem(row, 8, QTableWidgetItem(f"{plan.total_paid:,.2f}"))
            self.plans_table.setItem(row, 9, QTableWidgetItem(f"{plan.total_remaining:,.2f}"))
            self.plans_table.setItem(row, 10, QTableWidgetItem(f"{plan.total_late_fees:,.2f}"))
            
            # نسبة الإنجاز
            progress_item = QTableWidgetItem(f"{plan.completion_percentage:.1f}%")
            if plan.completion_percentage >= 100:
                progress_item.setBackground(QColor(200, 255, 200))
            elif plan.completion_percentage >= 50:
                progress_item.setBackground(QColor(255, 255, 200))
            else:
                progress_item.setBackground(QColor(255, 220, 220))
            self.plans_table.setItem(row, 11, progress_item)
            
            # الحالة
            status_item = QTableWidgetItem(self.get_status_text(plan.status))
            status_item.setBackground(self.get_status_color(plan.status))
            self.plans_table.setItem(row, 12, status_item)
            
            # الملاحظات
            self.plans_table.setItem(row, 13, QTableWidgetItem(plan.notes or ""))
            
            # تخزين معرف الخطة
            self.plans_table.item(row, 0).setData(Qt.UserRole, plan.id)
            
    def load_upcoming_installments(self):
        """تحميل الأقساط المستحقة قريباً"""
        try:
            # TODO: إضافة دالة في الخدمة للحصول على الأقساط القادمة
            self.upcoming_table.setRowCount(0)
        except Exception as e:
            print(f"Error loading upcoming installments: {e}")
            
    def load_overdue_installments(self):
        """تحميل الأقساط المتأخرة"""
        try:
            overdue = self.service.get_overdue_installments()
            self.overdue_table.setRowCount(len(overdue))
            
            for row, inst_data in enumerate(overdue):
                # رقم الخطة
                self.overdue_table.setItem(row, 0, QTableWidgetItem(inst_data.get('plan_number', '')))
                
                # العميل
                self.overdue_table.setItem(row, 1, QTableWidgetItem(inst_data.get('customer_name', '')))
                
                # رقم القسط
                self.overdue_table.setItem(row, 2, QTableWidgetItem(str(inst_data.get('installment_number', ''))))
                
                # تاريخ الاستحقاق
                due_date = inst_data.get('due_date')
                due_str = due_date.strftime("%Y-%m-%d") if isinstance(due_date, date) else str(due_date)
                self.overdue_table.setItem(row, 3, QTableWidgetItem(due_str))
                
                # المبالغ
                self.overdue_table.setItem(row, 4, QTableWidgetItem(f"{inst_data.get('total_amount', 0):,.2f}"))
                self.overdue_table.setItem(row, 5, QTableWidgetItem(f"{inst_data.get('remaining_amount', 0):,.2f}"))
                self.overdue_table.setItem(row, 6, QTableWidgetItem(f"{inst_data.get('late_fee', 0):,.2f}"))
                
                # أيام التأخير
                days = inst_data.get('days_overdue', 0)
                days_item = QTableWidgetItem(f"{days} يوم")
                if days > 30:
                    days_item.setBackground(QColor(255, 100, 100))
                elif days > 7:
                    days_item.setBackground(QColor(255, 200, 100))
                self.overdue_table.setItem(row, 7, days_item)
                
                # الحالة
                status = inst_data.get('status', '')
                self.overdue_table.setItem(row, 8, QTableWidgetItem(status))
                
                # زر الدفع
                pay_btn = QPushButton("💰 دفع")
                installment_id = inst_data.get('installment_id')
                pay_btn.clicked.connect(lambda checked, iid=installment_id: self.quick_payment(iid))
                self.overdue_table.setCellWidget(row, 9, pay_btn)
                
        except Exception as e:
            print(f"Error loading overdue installments: {e}")
            
    def update_statistics(self):
        """تحديث الإحصائيات"""
        try:
            stats = self.service.get_payment_plan_statistics()
            
            total_plans = sum(stats.values())
            self.stats_labels['total_plans'].setText(str(total_plans))
            self.stats_labels['active_plans'].setText(str(stats.get(PaymentPlanStatus.ACTIVE.value, 0)))
            self.stats_labels['completed_plans'].setText(str(stats.get(PaymentPlanStatus.COMPLETED.value, 0)))
            
            # TODO: إضافة إحصائيات مالية
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
            
    def apply_filters(self):
        """تطبيق المرشحات"""
        self.load_payment_plans()
        
    def on_plan_selected(self):
        """عند اختيار خطة"""
        selected = self.plans_table.selectedItems()
        has_selection = len(selected) > 0
        
        self.edit_btn.setEnabled(has_selection)
        self.view_btn.setEnabled(has_selection)
        self.payment_btn.setEnabled(has_selection)
        self.cancel_btn.setEnabled(has_selection)
        
        if has_selection:
            row = self.plans_table.currentRow()
            plan_id = self.plans_table.item(row, 0).data(Qt.UserRole)
            self.current_plan = self.service.get_payment_plan(plan_id)
            
    def create_new_plan(self):
        """إنشاء خطة جديدة"""
        from ..dialogs.payment_plan_dialog import PaymentPlanDialog
        
        dialog = PaymentPlanDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_payment_plans()
            self.plan_updated.emit()
            
    def edit_selected_plan(self):
        """تعديل الخطة المحددة"""
        if not self.current_plan:
            return
            
        from ..dialogs.payment_plan_dialog import PaymentPlanDialog
        
        dialog = PaymentPlanDialog(self.db_manager, self.current_plan, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_payment_plans()
            self.plan_updated.emit()
            
    def view_plan_details(self):
        """عرض تفاصيل الخطة"""
        if not self.current_plan:
            return
            
        from ..dialogs.installment_payment_dialog import PaymentPlanDetailsDialog
        
        dialog = PaymentPlanDetailsDialog(self.current_plan, self.db_manager, parent=self)
        dialog.exec()
        
    def record_payment(self):
        """تسجيل دفعة"""
        if not self.current_plan:
            return
            
        from ..dialogs.installment_payment_dialog import InstallmentPaymentDialog
        
        dialog = InstallmentPaymentDialog(self.current_plan, self.db_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.load_payment_plans()
            self.plan_updated.emit()
            
    def quick_payment(self, installment_id: int):
        """دفع سريع لقسط"""
        # TODO: تنفيذ دفع سريع
        QMessageBox.information(self, "دفع", f"تسجيل دفع للقسط #{installment_id}")
        
    def cancel_plan(self):
        """إلغاء الخطة"""
        if not self.current_plan:
            return
            
        reply = QMessageBox.question(
            self,
            "تأكيد الإلغاء",
            f"هل أنت متأكد من إلغاء الخطة {self.current_plan.plan_number}؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.current_plan.cancel()
                self.service.update_payment_plan(self.current_plan)
                self.load_payment_plans()
                self.plan_updated.emit()
                QMessageBox.information(self, "نجح", "تم إلغاء الخطة")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل إلغاء الخطة:\n{str(e)}")
                
    def apply_late_fees_to_all(self):
        """تطبيق غرامات التأخير على جميع الخطط"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد تطبيق غرامات التأخير على جميع الخطط النشطة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                count = self.service.apply_late_fees_to_all()
                self.load_payment_plans()
                QMessageBox.information(self, "نجح", f"تم تطبيق الغرامات على {count} خطة")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل تطبيق الغرامات:\n{str(e)}")
                
    def get_status_text(self, status: str) -> str:
        """الحصول على نص الحالة"""
        status_map = {
            PaymentPlanStatus.DRAFT.value: "مسودة",
            PaymentPlanStatus.ACTIVE.value: "نشطة",
            PaymentPlanStatus.COMPLETED.value: "مكتملة",
            PaymentPlanStatus.CANCELLED.value: "ملغية",
            PaymentPlanStatus.DEFAULTED.value: "متعثرة",
            PaymentPlanStatus.ON_HOLD.value: "معلقة"
        }
        return status_map.get(status, status)
        
    def get_status_color(self, status: str) -> QColor:
        """الحصول على لون الحالة"""
        colors = {
            PaymentPlanStatus.DRAFT.value: QColor(220, 220, 220),
            PaymentPlanStatus.ACTIVE.value: QColor(200, 255, 200),
            PaymentPlanStatus.COMPLETED.value: QColor(150, 200, 255),
            PaymentPlanStatus.CANCELLED.value: QColor(255, 200, 200),
            PaymentPlanStatus.DEFAULTED.value: QColor(255, 100, 100),
            PaymentPlanStatus.ON_HOLD.value: QColor(255, 255, 200)
        }
        return colors.get(status, QColor(255, 255, 255))
