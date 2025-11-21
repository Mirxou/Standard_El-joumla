"""
معالج الإعداد الأولي للنظام
Setup Wizard for First-Time Configuration
"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QTextEdit,
    QCheckBox, QPushButton, QGroupBox, QGridLayout,
    QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path
import json


class WelcomePage(QWizardPage):
    """صفحة الترحيب"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("مرحباً بك في نظام إدارة المخزون والمبيعات")
        self.setSubTitle("سنساعدك في إعداد النظام للاستخدام لأول مرة")
        
        layout = QVBoxLayout(self)
        
        # شعار أو صورة
        welcome_label = QLabel(
            "هذا المعالج سيساعدك في:\n\n"
            "• إعداد معلومات الشركة\n"
            "• إنشاء المستخدم الرئيسي\n"
            "• تكوين الإعدادات الأساسية\n"
            "• إنشاء البيانات الأولية\n\n"
            "اضغط 'التالي' للبدء"
        )
        welcome_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        welcome_label.setFont(font)
        
        layout.addWidget(welcome_label)
        layout.addStretch()


class CompanyInfoPage(QWizardPage):
    """صفحة معلومات الشركة"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("معلومات الشركة")
        self.setSubTitle("أدخل المعلومات الأساسية لشركتك")
        
        layout = QGridLayout(self)
        
        # اسم الشركة
        layout.addWidget(QLabel("اسم الشركة: *"), 0, 0)
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("مثال: شركة التجارة العامة")
        layout.addWidget(self.company_name, 0, 1)
        self.registerField("company_name*", self.company_name)
        
        # العنوان
        layout.addWidget(QLabel("العنوان:"), 1, 0)
        self.address = QLineEdit()
        layout.addWidget(self.address, 1, 1)
        self.registerField("address", self.address)
        
        # المدينة
        layout.addWidget(QLabel("المدينة:"), 2, 0)
        self.city = QLineEdit()
        layout.addWidget(self.city, 2, 1)
        self.registerField("city", self.city)
        
        # الهاتف
        layout.addWidget(QLabel("الهاتف:"), 3, 0)
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+966 XX XXX XXXX")
        layout.addWidget(self.phone, 3, 1)
        self.registerField("phone", self.phone)
        
        # البريد الإلكتروني
        layout.addWidget(QLabel("البريد الإلكتروني:"), 4, 0)
        self.email = QLineEdit()
        self.email.setPlaceholderText("info@company.com")
        layout.addWidget(self.email, 4, 1)
        self.registerField("email", self.email)
        
        # الرقم الضريبي
        layout.addWidget(QLabel("الرقم الضريبي:"), 5, 0)
        self.tax_number = QLineEdit()
        layout.addWidget(self.tax_number, 5, 1)
        self.registerField("tax_number", self.tax_number)
        
        # السجل التجاري
        layout.addWidget(QLabel("السجل التجاري:"), 6, 0)
        self.commercial_reg = QLineEdit()
        layout.addWidget(self.commercial_reg, 6, 1)
        self.registerField("commercial_reg", self.commercial_reg)
        
        layout.setRowStretch(7, 1)


class AdminUserPage(QWizardPage):
    """صفحة إنشاء المستخدم الرئيسي"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("المستخدم الرئيسي")
        self.setSubTitle("أنشئ حساب المسؤول الرئيسي للنظام")
        
        layout = QGridLayout(self)
        
        # اسم المستخدم
        layout.addWidget(QLabel("اسم المستخدم: *"), 0, 0)
        self.username = QLineEdit()
        self.username.setPlaceholderText("admin")
        self.username.setText("admin")
        layout.addWidget(self.username, 0, 1)
        self.registerField("username*", self.username)
        
        # كلمة المرور
        layout.addWidget(QLabel("كلمة المرور: *"), 1, 0)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("أدخل كلمة مرور قوية")
        layout.addWidget(self.password, 1, 1)
        self.registerField("password*", self.password)
        
        # تأكيد كلمة المرور
        layout.addWidget(QLabel("تأكيد كلمة المرور: *"), 2, 0)
        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_confirm, 2, 1)
        self.registerField("password_confirm*", self.password_confirm)
        
        # الاسم الكامل
        layout.addWidget(QLabel("الاسم الكامل:"), 3, 0)
        self.full_name = QLineEdit()
        layout.addWidget(self.full_name, 3, 1)
        self.registerField("full_name", self.full_name)
        
        # البريد الإلكتروني
        layout.addWidget(QLabel("البريد الإلكتروني:"), 4, 0)
        self.admin_email = QLineEdit()
        layout.addWidget(self.admin_email, 4, 1)
        self.registerField("admin_email", self.admin_email)
        
        # ملاحظة
        note_label = QLabel(
            "ملاحظة: يمكنك تغيير هذه المعلومات لاحقاً من الإعدادات.\n"
            "تأكد من حفظ كلمة المرور في مكان آمن."
        )
        note_label.setStyleSheet("color: #666; font-size: 10px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label, 5, 0, 1, 2)
        
        layout.setRowStretch(6, 1)
    
    def validatePage(self):
        """التحقق من صحة البيانات"""
        if self.password.text() != self.password_confirm.text():
            QMessageBox.warning(
                self,
                "خطأ",
                "كلمتا المرور غير متطابقتين"
            )
            return False
        
        if len(self.password.text()) < 6:
            QMessageBox.warning(
                self,
                "خطأ",
                "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
            )
            return False
        
        return True


class SystemSettingsPage(QWizardPage):
    """صفحة الإعدادات الأساسية"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("الإعدادات الأساسية")
        self.setSubTitle("اختر الإعدادات المفضلة للنظام")
        
        layout = QVBoxLayout(self)
        
        # إعدادات المحاسبة
        accounting_group = QGroupBox("إعدادات المحاسبة")
        accounting_layout = QGridLayout(accounting_group)
        
        accounting_layout.addWidget(QLabel("السنة المالية:"), 0, 0)
        self.fiscal_year = QSpinBox()
        self.fiscal_year.setRange(2020, 2050)
        self.fiscal_year.setValue(2025)
        accounting_layout.addWidget(self.fiscal_year, 0, 1)
        self.registerField("fiscal_year", self.fiscal_year)
        
        accounting_layout.addWidget(QLabel("العملة:"), 1, 0)
        self.currency = QComboBox()
        self.currency.addItems(["دينار جزائري (DZD)", "دولار أمريكي (USD)", "يورو (EUR)"])
        accounting_layout.addWidget(self.currency, 1, 1)
        self.registerField("currency", self.currency, "currentText")
        
        layout.addWidget(accounting_group)
        
        # إعدادات الضرائب
        tax_group = QGroupBox("إعدادات الضرائب")
        tax_layout = QGridLayout(tax_group)
        
        self.enable_tax = QCheckBox("تفعيل الضريبة")
        self.enable_tax.setChecked(True)
        tax_layout.addWidget(self.enable_tax, 0, 0, 1, 2)
        self.registerField("enable_tax", self.enable_tax)
        
        tax_layout.addWidget(QLabel("نسبة الضريبة (%):"), 1, 0)
        self.tax_rate = QSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(15)
        tax_layout.addWidget(self.tax_rate, 1, 1)
        self.registerField("tax_rate", self.tax_rate)
        
        layout.addWidget(tax_group)
        
        # إعدادات المخزون
        inventory_group = QGroupBox("إعدادات المخزون")
        inventory_layout = QVBoxLayout(inventory_group)
        
        self.track_inventory = QCheckBox("تتبع المخزون")
        self.track_inventory.setChecked(True)
        inventory_layout.addWidget(self.track_inventory)
        self.registerField("track_inventory", self.track_inventory)
        
        self.enable_low_stock_alerts = QCheckBox("تنبيهات المخزون المنخفض")
        self.enable_low_stock_alerts.setChecked(True)
        inventory_layout.addWidget(self.enable_low_stock_alerts)
        self.registerField("enable_low_stock_alerts", self.enable_low_stock_alerts)
        
        layout.addWidget(inventory_group)
        
        layout.addStretch()


class InitialDataPage(QWizardPage):
    """صفحة البيانات الأولية"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("البيانات الأولية")
        self.setSubTitle("اختر البيانات الأولية التي تريد إنشاءها")
        
        layout = QVBoxLayout(self)
        
        intro_label = QLabel(
            "سننشئ بعض البيانات الأولية لمساعدتك في البدء. "
            "يمكنك تعديل أو حذف هذه البيانات لاحقاً."
        )
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # خيارات البيانات
        self.create_categories = QCheckBox("إنشاء فئات منتجات أساسية")
        self.create_categories.setChecked(True)
        layout.addWidget(self.create_categories)
        self.registerField("create_categories", self.create_categories)
        
        self.create_accounts = QCheckBox("إنشاء دليل حسابات أساسي")
        self.create_accounts.setChecked(True)
        layout.addWidget(self.create_accounts)
        self.registerField("create_accounts", self.create_accounts)
        
        self.create_warehouses = QCheckBox("إنشاء مستودع افتراضي")
        self.create_warehouses.setChecked(True)
        layout.addWidget(self.create_warehouses)
        self.registerField("create_warehouses", self.create_warehouses)
        
        self.enable_sample_data = QCheckBox("إنشاء بيانات تجريبية (للتدريب)")
        self.enable_sample_data.setChecked(False)
        layout.addWidget(self.enable_sample_data)
        self.registerField("enable_sample_data", self.enable_sample_data)
        
        note_label = QLabel(
            "\nملاحظة: البيانات التجريبية تشمل منتجات وعملاء "
            "وموردين وفواتير للتدريب فقط."
        )
        note_label.setStyleSheet("color: #666; font-size: 10px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        layout.addStretch()


class CompletionPage(QWizardPage):
    """صفحة الإكمال"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("اكتمل الإعداد!")
        self.setSubTitle("تم إعداد النظام بنجاح")
        
        layout = QVBoxLayout(self)
        
        # رسالة النجاح
        success_label = QLabel(
            "✓ تم إعداد النظام بنجاح!\n\n"
            "يمكنك الآن:\n"
            "• تسجيل الدخول باستخدام حسابك\n"
            "• البدء في إدخال البيانات\n"
            "• استكشاف ميزات النظام\n\n"
            "اضغط 'إنهاء' لبدء استخدام النظام."
        )
        success_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        success_label.setFont(font)
        
        layout.addWidget(success_label)
        
        # شريط التقدم (للعرض فقط)
        self.progress = QProgressBar()
        self.progress.setValue(100)
        layout.addWidget(self.progress)
        
        layout.addStretch()


class SetupWizard(QWizard):
    """
    معالج الإعداد الأولي
    يرشد المستخدم خلال إعداد النظام لأول مرة
    """
    
    setup_completed = Signal(dict)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.setWindowTitle("معالج إعداد النظام")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(700, 500)
        
        # إضافة الصفحات
        self.addPage(WelcomePage())
        self.addPage(CompanyInfoPage())
        self.addPage(AdminUserPage())
        self.addPage(SystemSettingsPage())
        self.addPage(InitialDataPage())
        self.addPage(CompletionPage())
        
        # الأزرار
        self.setButtonText(QWizard.NextButton, "التالي")
        self.setButtonText(QWizard.BackButton, "السابق")
        self.setButtonText(QWizard.FinishButton, "إنهاء")
        self.setButtonText(QWizard.CancelButton, "إلغاء")
    
    def accept(self):
        """عند الانتهاء"""
        # جمع البيانات
        setup_data = {
            'company': {
                'name': self.field('company_name'),
                'address': self.field('address'),
                'city': self.field('city'),
                'phone': self.field('phone'),
                'email': self.field('email'),
                'tax_number': self.field('tax_number'),
                'commercial_reg': self.field('commercial_reg'),
            },
            'admin': {
                'username': self.field('username'),
                'password': self.field('password'),
                'full_name': self.field('full_name'),
                'email': self.field('admin_email'),
            },
            'settings': {
                'fiscal_year': self.field('fiscal_year'),
                'currency': self.field('currency'),
                'enable_tax': self.field('enable_tax'),
                'tax_rate': self.field('tax_rate'),
                'track_inventory': self.field('track_inventory'),
                'enable_low_stock_alerts': self.field('enable_low_stock_alerts'),
            },
            'initial_data': {
                'create_categories': self.field('create_categories'),
                'create_accounts': self.field('create_accounts'),
                'create_warehouses': self.field('create_warehouses'),
                'enable_sample_data': self.field('enable_sample_data'),
            }
        }
        
        # تطبيق الإعدادات
        try:
            self._apply_setup(setup_data)
            
            # حفظ علامة اكتمال الإعداد
            self._mark_setup_completed()
            
            # إرسال إشارة
            self.setup_completed.emit(setup_data)
            
            QMessageBox.information(
                self,
                "نجح",
                "تم إعداد النظام بنجاح!\nسيتم إعادة تشغيل التطبيق."
            )
            
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل تطبيق الإعدادات:\n{str(e)}"
            )
    
    def _apply_setup(self, data: dict):
        """تطبيق إعدادات الإعداد الأولي"""
        cursor = self.db_manager.connection.cursor()
        
        try:
            # 1. حفظ معلومات الشركة في system_settings
            for key, value in data['company'].items():
                cursor.execute("""
                    UPDATE system_settings 
                    SET value = ?
                    WHERE key = ?
                """, (value, f"company_{key}"))
            
            # 2. إنشاء المستخدم الرئيسي
            from src.services.permission_service import PermissionService
            perm_service = PermissionService(self.db_manager)
            
            admin_user = perm_service.create_user(
                username=data['admin']['username'],
                password=data['admin']['password'],
                full_name=data['admin']['full_name'],
                email=data['admin']['email']
            )
            
            # منح دور Admin
            admin_role = perm_service.get_role_by_name('Admin')
            if admin_role:
                perm_service.assign_role_to_user(admin_user['id'], admin_role.id)
            
            # 3. حفظ الإعدادات
            for key, value in data['settings'].items():
                cursor.execute("""
                    UPDATE system_settings 
                    SET value = ?
                    WHERE key = ?
                """, (str(value), key))
            
            # 4. إنشاء البيانات الأولية
            if data['initial_data']['create_categories']:
                self._create_default_categories()
            
            if data['initial_data']['create_accounts']:
                self._create_default_accounts()
            
            if data['initial_data']['create_warehouses']:
                self._create_default_warehouse()
            
            if data['initial_data']['enable_sample_data']:
                self._create_sample_data()
            
            self.db_manager.connection.commit()
            
        except Exception as e:
            self.db_manager.connection.rollback()
            raise e
    
    def _create_default_categories(self):
        """إنشاء فئات افتراضية"""
        cursor = self.db_manager.connection.cursor()
        
        categories = [
            "إلكترونيات",
            "ملابس",
            "أطعمة ومشروبات",
            "أدوات منزلية",
            "أدوات مكتبية",
            "أخرى"
        ]
        
        for cat in categories:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, active)
                VALUES (?, 1)
            """, (cat,))
    
    def _create_default_accounts(self):
        """إنشاء حسابات افتراضية"""
        # يمكن استخدام الكود الموجود في accounting_service
        pass
    
    def _create_default_warehouse(self):
        """إنشاء مستودع افتراضي"""
        cursor = self.db_manager.connection.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO warehouses (name, location, active)
            VALUES ('المستودع الرئيسي', 'الموقع الافتراضي', 1)
        """)
    
    def _create_sample_data(self):
        """إنشاء بيانات تجريبية"""
        # يمكن إضافة منتجات وعملاء وموردين تجريبيين
        pass
    
    def _mark_setup_completed(self):
        """تعليم الإعداد كمكتمل"""
        cursor = self.db_manager.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings (key, value, category)
            VALUES ('setup_completed', 'true', 'general')
        """)
        self.db_manager.connection.commit()


def is_setup_required(db_manager) -> bool:
    """
    التحقق من الحاجة لإعداد أولي
    
    Args:
        db_manager: مدير قاعدة البيانات
        
    Returns:
        True إذا كان الإعداد مطلوباً
    """
    cursor = db_manager.connection.cursor()
    cursor.execute("""
        SELECT value FROM system_settings 
        WHERE key = 'setup_completed'
    """)
    
    result = cursor.fetchone()
    return not result or result[0] != 'true'
