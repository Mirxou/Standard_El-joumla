"""
Payment Plan Dialog - نافذة إنشاء/تعديل خطة الدفع
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QGroupBox, QGridLayout,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from ...models.payment_plan import (
    PaymentPlan, PaymentPlanStatus, PaymentFrequency, LateFeeType
)
from ...services.payment_plan_service import PaymentPlanService
from ...core.database_manager import DatabaseManager


class PaymentPlanDialog(QDialog):
    """نافذة حوار خطة الدفع"""
    
    def __init__(self, db_manager: DatabaseManager, plan: Optional[PaymentPlan] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = PaymentPlanService(db_manager)
        self.plan = plan
        self.is_edit_mode = plan is not None
        
        self.setWindowTitle("تعديل خطة الدفع" if self.is_edit_mode else "خطة دفع جديدة")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        self.setup_ui()
        
        if self.is_edit_mode:
            self.load_plan_data()
            
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("تعديل خطة الدفع" if self.is_edit_mode else "إنشاء خطة دفع جديدة")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معلومات أساسية
        basic_group = self.create_basic_info_section()
        layout.addWidget(basic_group)
        
        # معلومات العميل
        customer_group = self.create_customer_section()
        layout.addWidget(customer_group)
        
        # معلومات مالية
        financial_group = self.create_financial_section()
        layout.addWidget(financial_group)
        
        # شروط التقسيط
        installment_group = self.create_installment_terms_section()
        layout.addWidget(installment_group)
        
        # غرامات التأخير
        late_fee_group = self.create_late_fee_section()
        layout.addWidget(late_fee_group)
        
        # معاينة الأقساط
        preview_group = self.create_installments_preview()
        layout.addWidget(preview_group)
        
        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("👁️ معاينة الأقساط")
        self.preview_btn.clicked.connect(self.preview_installments)
        buttons_layout.addWidget(self.preview_btn)
        
        buttons_layout.addStretch()
        
        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.clicked.connect(self.save_plan)
        buttons_layout.addWidget(self.save_btn)
        
        self.activate_btn = QPushButton("✅ حفظ وتفعيل")
        self.activate_btn.clicked.connect(self.save_and_activate)
        buttons_layout.addWidget(self.activate_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def create_basic_info_section(self) -> QGroupBox:
        """قسم المعلومات الأساسية"""
        group = QGroupBox("المعلومات الأساسية")
        layout = QGridLayout()
        
        # رقم الخطة
        layout.addWidget(QLabel("رقم الخطة:"), 0, 0)
        self.plan_number_edit = QLineEdit()
        self.plan_number_edit.setReadOnly(True)
        self.plan_number_edit.setPlaceholderText("يتم إنشاؤه تلقائياً")
        layout.addWidget(self.plan_number_edit, 0, 1)
        
        # اسم الخطة
        layout.addWidget(QLabel("اسم الخطة:"), 0, 2)
        self.plan_name_edit = QLineEdit()
        self.plan_name_edit.setPlaceholderText("اسم مميز للخطة...")
        layout.addWidget(self.plan_name_edit, 0, 3)
        
        # رقم الفاتورة
        layout.addWidget(QLabel("رقم الفاتورة:"), 1, 0)
        self.invoice_number_edit = QLineEdit()
        self.invoice_number_edit.setPlaceholderText("اختياري")
        layout.addWidget(self.invoice_number_edit, 1, 1)
        
        # تاريخ البدء
        layout.addWidget(QLabel("تاريخ البدء:"), 1, 2)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        layout.addWidget(self.start_date_edit, 1, 3)
        
        # الحالة
        layout.addWidget(QLabel("الحالة:"), 2, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItem("مسودة", PaymentPlanStatus.DRAFT.value)
        self.status_combo.addItem("نشطة", PaymentPlanStatus.ACTIVE.value)
        self.status_combo.addItem("معلقة", PaymentPlanStatus.ON_HOLD.value)
        layout.addWidget(self.status_combo, 2, 1)
        
        # الوصف
        layout.addWidget(QLabel("الوصف:"), 2, 2)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText("وصف الخطة...")
        layout.addWidget(self.description_edit, 2, 3, 2, 1)
        
        group.setLayout(layout)
        return group
        
    def create_customer_section(self) -> QGroupBox:
        """قسم معلومات العميل"""
        group = QGroupBox("معلومات العميل")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("اسم العميل:"))
        self.customer_name_edit = QLineEdit()
        self.customer_name_edit.setPlaceholderText("اسم العميل...")
        layout.addWidget(self.customer_name_edit)
        
        # TODO: إضافة زر لاختيار العميل من قائمة
        select_customer_btn = QPushButton("📋 اختيار عميل")
        layout.addWidget(select_customer_btn)
        
        group.setLayout(layout)
        return group
        
    def create_financial_section(self) -> QGroupBox:
        """قسم المعلومات المالية"""
        group = QGroupBox("المعلومات المالية")
        layout = QGridLayout()
        
        # المبلغ الكلي
        layout.addWidget(QLabel("المبلغ الكلي:"), 0, 0)
        self.total_amount_spin = QDoubleSpinBox()
        self.total_amount_spin.setMaximum(10000000)
        self.total_amount_spin.setDecimals(2)
        self.total_amount_spin.setSuffix(" دج")
        self.total_amount_spin.valueChanged.connect(self.calculate_financed_amount)
        layout.addWidget(self.total_amount_spin, 0, 1)
        
        # الدفعة المقدمة
        layout.addWidget(QLabel("الدفعة المقدمة:"), 0, 2)
        self.down_payment_spin = QDoubleSpinBox()
        self.down_payment_spin.setMaximum(10000000)
        self.down_payment_spin.setDecimals(2)
        self.down_payment_spin.setSuffix(" دج")
        self.down_payment_spin.valueChanged.connect(self.calculate_financed_amount)
        layout.addWidget(self.down_payment_spin, 0, 3)
        
        # المبلغ المقسط
        layout.addWidget(QLabel("المبلغ المقسط:"), 1, 0)
        self.financed_amount_label = QLabel("0.00 دج")
        self.financed_amount_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.financed_amount_label, 1, 1)
        
        # نسبة الفائدة
        layout.addWidget(QLabel("نسبة الفائدة السنوية %:"), 1, 2)
        self.interest_rate_spin = QDoubleSpinBox()
        self.interest_rate_spin.setMaximum(100)
        self.interest_rate_spin.setDecimals(2)
        self.interest_rate_spin.setSuffix(" %")
        layout.addWidget(self.interest_rate_spin, 1, 3)
        
        group.setLayout(layout)
        return group
        
    def create_installment_terms_section(self) -> QGroupBox:
        """قسم شروط التقسيط"""
        group = QGroupBox("شروط التقسيط")
        layout = QGridLayout()
        
        # عدد الأقساط
        layout.addWidget(QLabel("عدد الأقساط:"), 0, 0)
        self.installments_count_spin = QSpinBox()
        self.installments_count_spin.setMinimum(1)
        self.installments_count_spin.setMaximum(120)
        self.installments_count_spin.setValue(12)
        self.installments_count_spin.valueChanged.connect(self.calculate_installment_amount)
        layout.addWidget(self.installments_count_spin, 0, 1)
        
        # التكرار
        layout.addWidget(QLabel("التكرار:"), 0, 2)
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItem("يومي", PaymentFrequency.DAILY.value)
        self.frequency_combo.addItem("أسبوعي", PaymentFrequency.WEEKLY.value)
        self.frequency_combo.addItem("نصف شهري", PaymentFrequency.BIWEEKLY.value)
        self.frequency_combo.addItem("شهري", PaymentFrequency.MONTHLY.value)
        self.frequency_combo.addItem("ربع سنوي", PaymentFrequency.QUARTERLY.value)
        self.frequency_combo.addItem("نصف سنوي", PaymentFrequency.SEMIANNUAL.value)
        self.frequency_combo.addItem("سنوي", PaymentFrequency.ANNUAL.value)
        self.frequency_combo.setCurrentText("شهري")
        layout.addWidget(self.frequency_combo, 0, 3)
        
        # مبلغ القسط
        layout.addWidget(QLabel("مبلغ القسط:"), 1, 0)
        self.installment_amount_label = QLabel("0.00 دج")
        self.installment_amount_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.installment_amount_label, 1, 1)
        
        # تاريخ الانتهاء المتوقع
        layout.addWidget(QLabel("تاريخ الانتهاء المتوقع:"), 1, 2)
        self.end_date_label = QLabel("---")
        layout.addWidget(self.end_date_label, 1, 3)
        
        group.setLayout(layout)
        return group
        
    def create_late_fee_section(self) -> QGroupBox:
        """قسم غرامات التأخير"""
        group = QGroupBox("غرامات التأخير")
        layout = QGridLayout()
        
        # نوع الغرامة
        layout.addWidget(QLabel("نوع الغرامة:"), 0, 0)
        self.late_fee_type_combo = QComboBox()
        self.late_fee_type_combo.addItem("بدون غرامة", LateFeeType.NONE.value)
        self.late_fee_type_combo.addItem("مبلغ ثابت", LateFeeType.FIXED.value)
        self.late_fee_type_combo.addItem("نسبة مئوية", LateFeeType.PERCENTAGE.value)
        self.late_fee_type_combo.addItem("مركبة يومياً", LateFeeType.COMPOUNDING.value)
        self.late_fee_type_combo.currentIndexChanged.connect(self.on_late_fee_type_changed)
        layout.addWidget(self.late_fee_type_combo, 0, 1)
        
        # قيمة الغرامة
        layout.addWidget(QLabel("قيمة الغرامة:"), 0, 2)
        self.late_fee_value_spin = QDoubleSpinBox()
        self.late_fee_value_spin.setMaximum(100000)
        self.late_fee_value_spin.setDecimals(2)
        self.late_fee_value_spin.setEnabled(False)
        layout.addWidget(self.late_fee_value_spin, 0, 3)
        
        # فترة السماح
        layout.addWidget(QLabel("فترة السماح (أيام):"), 1, 0)
        self.grace_period_spin = QSpinBox()
        self.grace_period_spin.setMaximum(90)
        self.grace_period_spin.setValue(0)
        layout.addWidget(self.grace_period_spin, 1, 1)
        
        group.setLayout(layout)
        return group
        
    def create_installments_preview(self) -> QGroupBox:
        """قسم معاينة الأقساط"""
        group = QGroupBox("معاينة جدول الأقساط")
        layout = QVBoxLayout()
        
        self.installments_table = QTableWidget()
        self.installments_table.setColumnCount(7)
        self.installments_table.setHorizontalHeaderLabels([
            "رقم القسط", "تاريخ الاستحقاق", "المبلغ الأصلي",
            "الفائدة", "الإجمالي", "الحالة", "ملاحظات"
        ])
        self.installments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.installments_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.installments_table)
        
        group.setLayout(layout)
        return group
        
    def calculate_financed_amount(self):
        """حساب المبلغ المقسط"""
        total = self.total_amount_spin.value()
        down = self.down_payment_spin.value()
        financed = total - down
        
        self.financed_amount_label.setText(f"{financed:,.2f} دج")
        self.calculate_installment_amount()
        
    def calculate_installment_amount(self):
        """حساب مبلغ القسط"""
        total = self.total_amount_spin.value()
        down = self.down_payment_spin.value()
        financed = total - down
        count = self.installments_count_spin.value()
        
        if count > 0:
            installment = financed / count
            self.installment_amount_label.setText(f"{installment:,.2f} دج")
        else:
            self.installment_amount_label.setText("0.00 دج")
            
    def on_late_fee_type_changed(self):
        """عند تغيير نوع الغرامة"""
        fee_type = self.late_fee_type_combo.currentData()
        enabled = fee_type != LateFeeType.NONE.value
        
        self.late_fee_value_spin.setEnabled(enabled)
        
        if fee_type == LateFeeType.FIXED.value:
            self.late_fee_value_spin.setSuffix(" دج")
            self.late_fee_value_spin.setMaximum(100000)
        elif fee_type in [LateFeeType.PERCENTAGE.value, LateFeeType.COMPOUNDING.value]:
            self.late_fee_value_spin.setSuffix(" %")
            self.late_fee_value_spin.setMaximum(100)
            
    def preview_installments(self):
        """معاينة جدول الأقساط"""
        try:
            # إنشاء خطة مؤقتة
            plan = self.create_plan_from_inputs()
            
            # إنشاء الأقساط
            plan.generate_installments()
            
            # عرض الأقساط
            self.installments_table.setRowCount(len(plan.installments))
            
            for row, inst in enumerate(plan.installments):
                self.installments_table.setItem(row, 0, QTableWidgetItem(str(inst.installment_number)))
                
                due_str = inst.due_date.strftime("%Y-%m-%d") if inst.due_date else ""
                self.installments_table.setItem(row, 1, QTableWidgetItem(due_str))
                
                self.installments_table.setItem(row, 2, QTableWidgetItem(f"{inst.principal_amount:,.2f}"))
                self.installments_table.setItem(row, 3, QTableWidgetItem(f"{inst.interest_amount:,.2f}"))
                self.installments_table.setItem(row, 4, QTableWidgetItem(f"{inst.total_amount:,.2f}"))
                self.installments_table.setItem(row, 5, QTableWidgetItem("معلق"))
                self.installments_table.setItem(row, 6, QTableWidgetItem(""))
                
            # تحديث تاريخ الانتهاء
            if plan.end_date:
                self.end_date_label.setText(plan.end_date.strftime("%Y-%m-%d"))
                
            QMessageBox.information(self, "نجح", f"تم إنشاء {len(plan.installments)} قسط")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إنشاء جدول الأقساط:\n{str(e)}")
            
    def create_plan_from_inputs(self) -> PaymentPlan:
        """إنشاء خطة من المدخلات"""
        start_date = self.start_date_edit.date().toPython() if hasattr(self.start_date_edit.date(), 'toPython') else date.today()
        
        plan = PaymentPlan(
            id=self.plan.id if self.plan else None,
            plan_number=self.plan_number_edit.text() or None,
            plan_name=self.plan_name_edit.text() or None,
            invoice_number=self.invoice_number_edit.text() or None,
            customer_name=self.customer_name_edit.text(),
            description=self.description_edit.toPlainText() or None,
            start_date=start_date,
            total_amount=Decimal(str(self.total_amount_spin.value())),
            down_payment=Decimal(str(self.down_payment_spin.value())),
            number_of_installments=self.installments_count_spin.value(),
            frequency=self.frequency_combo.currentData(),
            interest_rate=Decimal(str(self.interest_rate_spin.value())),
            late_fee_type=self.late_fee_type_combo.currentData(),
            late_fee_value=Decimal(str(self.late_fee_value_spin.value())),
            grace_period_days=self.grace_period_spin.value(),
            status=self.status_combo.currentData()
        )
        
        return plan
        
    def save_plan(self):
        """حفظ الخطة"""
        try:
            plan = self.create_plan_from_inputs()
            
            if self.is_edit_mode:
                self.service.update_payment_plan(plan)
                QMessageBox.information(self, "نجح", "تم تحديث الخطة بنجاح")
            else:
                self.service.create_payment_plan(plan)
                QMessageBox.information(self, "نجح", "تم إنشاء الخطة بنجاح")
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الخطة:\n{str(e)}")
            
    def save_and_activate(self):
        """حفظ وتفعيل الخطة"""
        try:
            plan = self.create_plan_from_inputs()
            
            if self.is_edit_mode:
                self.service.update_payment_plan(plan)
            else:
                self.service.create_payment_plan(plan)
                
            # تفعيل الخطة
            plan.activate()
            self.service.update_payment_plan(plan)
            
            QMessageBox.information(self, "نجح", "تم حفظ وتفعيل الخطة بنجاح")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ وتفعيل الخطة:\n{str(e)}")
            
    def load_plan_data(self):
        """تحميل بيانات الخطة للتعديل"""
        if not self.plan:
            return
            
        self.plan_number_edit.setText(self.plan.plan_number or "")
        self.plan_name_edit.setText(self.plan.plan_name or "")
        self.invoice_number_edit.setText(self.plan.invoice_number or "")
        self.customer_name_edit.setText(self.plan.customer_name or "")
        self.description_edit.setPlainText(self.plan.description or "")
        
        if self.plan.start_date:
            qdate = QDate(self.plan.start_date.year, self.plan.start_date.month, self.plan.start_date.day)
            self.start_date_edit.setDate(qdate)
            
        self.total_amount_spin.setValue(float(self.plan.total_amount))
        self.down_payment_spin.setValue(float(self.plan.down_payment))
        self.installments_count_spin.setValue(self.plan.number_of_installments)
        self.interest_rate_spin.setValue(float(self.plan.interest_rate))
        
        # تعيين التكرار
        for i in range(self.frequency_combo.count()):
            if self.frequency_combo.itemData(i) == self.plan.frequency:
                self.frequency_combo.setCurrentIndex(i)
                break
                
        # تعيين نوع الغرامة
        for i in range(self.late_fee_type_combo.count()):
            if self.late_fee_type_combo.itemData(i) == self.plan.late_fee_type:
                self.late_fee_type_combo.setCurrentIndex(i)
                break
                
        self.late_fee_value_spin.setValue(float(self.plan.late_fee_value))
        self.grace_period_spin.setValue(self.plan.grace_period_days)
        
        # تعيين الحالة
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == self.plan.status:
                self.status_combo.setCurrentIndex(i)
                break
                
        # عرض الأقساط إذا كانت موجودة
        if self.plan.installments:
            self.installments_table.setRowCount(len(self.plan.installments))
            for row, inst in enumerate(self.plan.installments):
                self.installments_table.setItem(row, 0, QTableWidgetItem(str(inst.installment_number)))
                
                due_str = inst.due_date.strftime("%Y-%m-%d") if inst.due_date else ""
                self.installments_table.setItem(row, 1, QTableWidgetItem(due_str))
                
                self.installments_table.setItem(row, 2, QTableWidgetItem(f"{inst.principal_amount:,.2f}"))
                self.installments_table.setItem(row, 3, QTableWidgetItem(f"{inst.interest_amount:,.2f}"))
                self.installments_table.setItem(row, 4, QTableWidgetItem(f"{inst.total_amount:,.2f}"))
                self.installments_table.setItem(row, 5, QTableWidgetItem(inst.status))
                self.installments_table.setItem(row, 6, QTableWidgetItem(inst.notes or ""))
