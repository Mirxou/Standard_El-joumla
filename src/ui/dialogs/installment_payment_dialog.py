"""
Payment Plan Payment Dialog - نافذة تسجيل الدفعات على خطط التقسيط
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
    QDateEdit, QGroupBox, QGridLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from typing import Optional
from datetime import date
from decimal import Decimal

from ...models.payment_plan import PaymentPlan, PaymentInstallment, InstallmentStatus
from ...services.payment_plan_service import PaymentPlanService
from ...core.database_manager import DatabaseManager


class InstallmentPaymentDialog(QDialog):
    """نافذة حوار تسجيل الدفعات على الأقساط"""
    
    def __init__(self, plan: PaymentPlan, db_manager: DatabaseManager, 
                 installment: Optional[PaymentInstallment] = None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.db_manager = db_manager
        self.service = PaymentPlanService(db_manager)
        self.selected_installment = installment
        
        self.setWindowTitle("تسجيل دفعة على القسط")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        self.setup_ui()
        self.load_installments()
        
        if installment:
            self.select_installment(installment)
            
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("تسجيل دفعة على خطة الدفع")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معلومات الخطة
        plan_info = self.create_plan_info_section()
        layout.addWidget(plan_info)
        
        # قائمة الأقساط
        installments_group = self.create_installments_section()
        layout.addWidget(installments_group)
        
        # معلومات الدفعة
        payment_group = self.create_payment_section()
        layout.addWidget(payment_group)
        
        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 حفظ الدفعة")
        self.save_btn.clicked.connect(self.save_payment)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        self.pay_full_btn = QPushButton("💰 دفع كامل القسط")
        self.pay_full_btn.clicked.connect(self.pay_full_installment)
        self.pay_full_btn.setEnabled(False)
        buttons_layout.addWidget(self.pay_full_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def create_plan_info_section(self) -> QGroupBox:
        """قسم معلومات الخطة"""
        group = QGroupBox("معلومات خطة الدفع")
        layout = QGridLayout()
        
        layout.addWidget(QLabel("رقم الخطة:"), 0, 0)
        layout.addWidget(QLabel(self.plan.plan_number or "---"), 0, 1)
        
        layout.addWidget(QLabel("العميل:"), 0, 2)
        layout.addWidget(QLabel(self.plan.customer_name or "---"), 0, 3)
        
        layout.addWidget(QLabel("المبلغ الكلي:"), 1, 0)
        layout.addWidget(QLabel(f"{self.plan.total_amount:,.2f} دج"), 1, 1)
        
        layout.addWidget(QLabel("المدفوع:"), 1, 2)
        paid_label = QLabel(f"{self.plan.total_paid:,.2f} دج")
        paid_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(paid_label, 1, 3)
        
        layout.addWidget(QLabel("المتبقي:"), 2, 0)
        remaining_label = QLabel(f"{self.plan.total_remaining:,.2f} دج")
        remaining_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(remaining_label, 2, 1)
        
        layout.addWidget(QLabel("نسبة الإنجاز:"), 2, 2)
        layout.addWidget(QLabel(f"{self.plan.completion_percentage:.1f}%"), 2, 3)
        
        group.setLayout(layout)
        return group
        
    def create_installments_section(self) -> QGroupBox:
        """قسم قائمة الأقساط"""
        group = QGroupBox("الأقساط المتاحة للدفع")
        layout = QVBoxLayout()
        
        # جدول الأقساط
        self.installments_table = QTableWidget()
        self.installments_table.setColumnCount(8)
        self.installments_table.setHorizontalHeaderLabels([
            "رقم القسط", "تاريخ الاستحقاق", "المبلغ الأصلي",
            "الفائدة", "الغرامة", "الإجمالي", "المتبقي", "الحالة"
        ])
        
        self.installments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.installments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.installments_table.setSelectionMode(QTableWidget.SingleSelection)
        self.installments_table.setAlternatingRowColors(True)
        self.installments_table.itemSelectionChanged.connect(self.on_installment_selected)
        
        layout.addWidget(self.installments_table)
        
        group.setLayout(layout)
        return group
        
    def create_payment_section(self) -> QGroupBox:
        """قسم معلومات الدفعة"""
        group = QGroupBox("معلومات الدفعة")
        layout = QGridLayout()
        
        # تاريخ الدفع
        layout.addWidget(QLabel("تاريخ الدفع:"), 0, 0)
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setDate(QDate.currentDate())
        self.payment_date_edit.setCalendarPopup(True)
        layout.addWidget(self.payment_date_edit, 0, 1)
        
        # مبلغ الدفعة
        layout.addWidget(QLabel("مبلغ الدفعة:"), 0, 2)
        self.payment_amount_spin = QDoubleSpinBox()
        self.payment_amount_spin.setMaximum(10000000)
        self.payment_amount_spin.setDecimals(2)
        self.payment_amount_spin.setSuffix(" دج")
        self.payment_amount_spin.valueChanged.connect(self.on_payment_amount_changed)
        layout.addWidget(self.payment_amount_spin, 0, 3)
        
        # طريقة الدفع
        layout.addWidget(QLabel("طريقة الدفع:"), 1, 0)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            "نقداً", "تحويل بنكي", "بطاقة ائتمان",
            "شيك", "نقاط البيع", "أخرى"
        ])
        layout.addWidget(self.payment_method_combo, 1, 1)
        
        # رقم المرجع
        layout.addWidget(QLabel("رقم المرجع:"), 1, 2)
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("رقم الإيصال/الحوالة...")
        layout.addWidget(self.reference_edit, 1, 3)
        
        # الملاحظات
        layout.addWidget(QLabel("ملاحظات:"), 2, 0)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("ملاحظات على الدفعة...")
        layout.addWidget(self.notes_edit, 2, 1, 1, 3)
        
        # معلومات إضافية
        layout.addWidget(QLabel("المبلغ المتبقي بعد الدفع:"), 3, 0)
        self.remaining_after_label = QLabel("0.00 دج")
        self.remaining_after_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.remaining_after_label, 3, 1)
        
        layout.addWidget(QLabel("الحالة الجديدة:"), 3, 2)
        self.new_status_label = QLabel("---")
        self.new_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.new_status_label, 3, 3)
        
        group.setLayout(layout)
        return group
        
    def load_installments(self):
        """تحميل الأقساط"""
        # تصفية الأقساط غير المدفوعة
        unpaid_installments = [
            inst for inst in self.plan.installments
            if inst.status in [InstallmentStatus.PENDING.value, InstallmentStatus.PARTIALLY_PAID.value]
        ]
        
        self.installments_table.setRowCount(len(unpaid_installments))
        
        for row, inst in enumerate(unpaid_installments):
            # رقم القسط
            self.installments_table.setItem(row, 0, QTableWidgetItem(str(inst.installment_number)))
            
            # تاريخ الاستحقاق
            due_str = inst.due_date.strftime("%Y-%m-%d") if inst.due_date else ""
            due_item = QTableWidgetItem(due_str)
            if inst.is_overdue:
                due_item.setBackground(QColor(255, 200, 200))
            self.installments_table.setItem(row, 1, due_item)
            
            # المبالغ
            self.installments_table.setItem(row, 2, QTableWidgetItem(f"{inst.principal_amount:,.2f}"))
            self.installments_table.setItem(row, 3, QTableWidgetItem(f"{inst.interest_amount:,.2f}"))
            self.installments_table.setItem(row, 4, QTableWidgetItem(f"{inst.late_fee:,.2f}"))
            self.installments_table.setItem(row, 5, QTableWidgetItem(f"{inst.total_amount:,.2f}"))
            self.installments_table.setItem(row, 6, QTableWidgetItem(f"{inst.remaining_amount:,.2f}"))
            
            # الحالة
            status_item = QTableWidgetItem(self.get_status_text(inst.status))
            status_item.setBackground(self.get_status_color(inst.status))
            self.installments_table.setItem(row, 7, status_item)
            
            # تخزين معرف القسط
            self.installments_table.item(row, 0).setData(Qt.UserRole, inst.id)
            
    def on_installment_selected(self):
        """عند اختيار قسط"""
        selected = self.installments_table.selectedItems()
        if not selected:
            self.save_btn.setEnabled(False)
            self.pay_full_btn.setEnabled(False)
            return
            
        row = self.installments_table.currentRow()
        installment_id = self.installments_table.item(row, 0).data(Qt.UserRole)
        
        # البحث عن القسط
        self.selected_installment = None
        for inst in self.plan.installments:
            if inst.id == installment_id:
                self.selected_installment = inst
                break
                
        if self.selected_installment:
            # تعيين المبلغ المتبقي كقيمة افتراضية
            self.payment_amount_spin.setValue(float(self.selected_installment.remaining_amount))
            self.save_btn.setEnabled(True)
            self.pay_full_btn.setEnabled(True)
            
    def on_payment_amount_changed(self):
        """عند تغيير مبلغ الدفعة"""
        if not self.selected_installment:
            return
            
        payment_amount = Decimal(str(self.payment_amount_spin.value()))
        remaining = self.selected_installment.remaining_amount - payment_amount
        
        self.remaining_after_label.setText(f"{remaining:,.2f} دج")
        
        # تحديد الحالة الجديدة
        if remaining <= 0:
            self.new_status_label.setText("مدفوع")
            self.new_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif payment_amount > 0:
            self.new_status_label.setText("مدفوع جزئياً")
            self.new_status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.new_status_label.setText("معلق")
            self.new_status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def select_installment(self, installment: PaymentInstallment):
        """اختيار قسط محدد"""
        for row in range(self.installments_table.rowCount()):
            inst_id = self.installments_table.item(row, 0).data(Qt.UserRole)
            if inst_id == installment.id:
                self.installments_table.selectRow(row)
                break
                
    def save_payment(self):
        """حفظ الدفعة"""
        if not self.selected_installment:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار قسط للدفع")
            return
            
        payment_amount = Decimal(str(self.payment_amount_spin.value()))
        
        if payment_amount <= 0:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال مبلغ صحيح")
            return
            
        if payment_amount > self.selected_installment.remaining_amount:
            reply = QMessageBox.question(
                self,
                "تأكيد",
                f"المبلغ المدخل ({payment_amount:,.2f}) أكبر من المبلغ المتبقي ({self.selected_installment.remaining_amount:,.2f})\n"
                "هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        try:
            payment_date = self.payment_date_edit.date().toPython() if hasattr(self.payment_date_edit.date(), 'toPython') else date.today()
            payment_method = self.payment_method_combo.currentText()
            reference = self.reference_edit.text()
            notes = self.notes_edit.toPlainText()
            
            # تسجيل الدفعة
            self.service.make_payment(
                plan_id=self.plan.id,
                installment_id=self.selected_installment.id,
                amount=payment_amount,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_reference=reference,
                notes=notes
            )
            
            QMessageBox.information(
                self,
                "نجح",
                f"تم تسجيل دفعة بمبلغ {payment_amount:,.2f} دج بنجاح"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تسجيل الدفعة:\n{str(e)}")
            
    def pay_full_installment(self):
        """دفع القسط كاملاً"""
        if not self.selected_installment:
            return
            
        self.payment_amount_spin.setValue(float(self.selected_installment.remaining_amount))
        self.save_payment()
        
    def get_status_text(self, status: str) -> str:
        """الحصول على نص الحالة"""
        status_map = {
            InstallmentStatus.PENDING.value: "معلق",
            InstallmentStatus.PAID.value: "مدفوع",
            InstallmentStatus.PARTIALLY_PAID.value: "مدفوع جزئياً",
            InstallmentStatus.OVERDUE.value: "متأخر",
            InstallmentStatus.CANCELLED.value: "ملغي",
            InstallmentStatus.WAIVED.value: "معفي"
        }
        return status_map.get(status, status)
        
    def get_status_color(self, status: str) -> QColor:
        """الحصول على لون الحالة"""
        colors = {
            InstallmentStatus.PENDING.value: QColor(255, 255, 200),
            InstallmentStatus.PAID.value: QColor(200, 255, 200),
            InstallmentStatus.PARTIALLY_PAID.value: QColor(255, 220, 150),
            InstallmentStatus.OVERDUE.value: QColor(255, 150, 150),
            InstallmentStatus.CANCELLED.value: QColor(220, 220, 220),
            InstallmentStatus.WAIVED.value: QColor(200, 220, 255)
        }
        return colors.get(status, QColor(255, 255, 255))


class PaymentPlanDetailsDialog(QDialog):
    """نافذة حوار عرض تفاصيل خطة الدفع"""
    
    def __init__(self, plan: PaymentPlan, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.db_manager = db_manager
        
        self.setWindowTitle(f"تفاصيل خطة الدفع - {plan.plan_number}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        self.setup_ui()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel(f"تفاصيل خطة الدفع: {self.plan.plan_number}")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معلومات الخطة
        info_group = self.create_plan_info()
        layout.addWidget(info_group)
        
        # جدول الأقساط
        installments_group = self.create_installments_table()
        layout.addWidget(installments_group)
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
    def create_plan_info(self) -> QGroupBox:
        """إنشاء قسم معلومات الخطة"""
        group = QGroupBox("معلومات الخطة")
        layout = QGridLayout()
        
        # الصف الأول
        layout.addWidget(QLabel("رقم الخطة:"), 0, 0)
        layout.addWidget(QLabel(self.plan.plan_number or "---"), 0, 1)
        
        layout.addWidget(QLabel("العميل:"), 0, 2)
        layout.addWidget(QLabel(self.plan.customer_name or "---"), 0, 3)
        
        # الصف الثاني
        layout.addWidget(QLabel("تاريخ البدء:"), 1, 0)
        start_str = self.plan.start_date.strftime("%Y-%m-%d") if self.plan.start_date else "---"
        layout.addWidget(QLabel(start_str), 1, 1)
        
        layout.addWidget(QLabel("تاريخ الانتهاء:"), 1, 2)
        end_str = self.plan.end_date.strftime("%Y-%m-%d") if self.plan.end_date else "---"
        layout.addWidget(QLabel(end_str), 1, 3)
        
        # الصف الثالث
        layout.addWidget(QLabel("المبلغ الكلي:"), 2, 0)
        layout.addWidget(QLabel(f"{self.plan.total_amount:,.2f} دج"), 2, 1)
        
        layout.addWidget(QLabel("المقدم:"), 2, 2)
        layout.addWidget(QLabel(f"{self.plan.down_payment:,.2f} دج"), 2, 3)
        
        # الصف الرابع
        layout.addWidget(QLabel("المبلغ المقسط:"), 3, 0)
        layout.addWidget(QLabel(f"{self.plan.financed_amount:,.2f} دج"), 3, 1)
        
        layout.addWidget(QLabel("عدد الأقساط:"), 3, 2)
        layout.addWidget(QLabel(str(self.plan.number_of_installments)), 3, 3)
        
        # الصف الخامس
        layout.addWidget(QLabel("المدفوع:"), 4, 0)
        paid_label = QLabel(f"{self.plan.total_paid:,.2f} دج")
        paid_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(paid_label, 4, 1)
        
        layout.addWidget(QLabel("المتبقي:"), 4, 2)
        remaining_label = QLabel(f"{self.plan.total_remaining:,.2f} دج")
        remaining_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(remaining_label, 4, 3)
        
        # الصف السادس
        layout.addWidget(QLabel("نسبة الإنجاز:"), 5, 0)
        layout.addWidget(QLabel(f"{self.plan.completion_percentage:.1f}%"), 5, 1)
        
        layout.addWidget(QLabel("الحالة:"), 5, 2)
        layout.addWidget(QLabel(self.plan.status), 5, 3)
        
        group.setLayout(layout)
        return group
        
    def create_installments_table(self) -> QGroupBox:
        """إنشاء جدول الأقساط"""
        group = QGroupBox("جدول الأقساط")
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "رقم القسط", "تاريخ الاستحقاق", "المبلغ الأصلي",
            "الفائدة", "الغرامة", "الإجمالي", "المدفوع",
            "المتبقي", "الحالة"
        ])
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setRowCount(len(self.plan.installments))
        
        for row, inst in enumerate(self.plan.installments):
            table.setItem(row, 0, QTableWidgetItem(str(inst.installment_number)))
            
            due_str = inst.due_date.strftime("%Y-%m-%d") if inst.due_date else ""
            table.setItem(row, 1, QTableWidgetItem(due_str))
            
            table.setItem(row, 2, QTableWidgetItem(f"{inst.principal_amount:,.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"{inst.interest_amount:,.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{inst.late_fee:,.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{inst.total_amount:,.2f}"))
            table.setItem(row, 6, QTableWidgetItem(f"{inst.amount_paid:,.2f}"))
            table.setItem(row, 7, QTableWidgetItem(f"{inst.remaining_amount:,.2f}"))
            
            status_item = QTableWidgetItem(inst.status)
            if inst.status == InstallmentStatus.PAID.value:
                status_item.setBackground(QColor(200, 255, 200))
            elif inst.status == InstallmentStatus.OVERDUE.value:
                status_item.setBackground(QColor(255, 150, 150))
            table.setItem(row, 8, status_item)
            
        layout.addWidget(table)
        
        group.setLayout(layout)
        return group
