"""
Quick Actions Toolbar - شريط الإجراءات السريعة
شريط أدوات عائم/مثبت للوصول السريع للوظائف المستخدمة بكثرة
"""

from PySide6.QtWidgets import (
    QToolBar, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QDialog, QListWidget, QListWidgetItem,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QSettings, QSize, Signal
from PySide6.QtGui import QIcon, QFont
from typing import List, Dict, Callable, Optional


class QuickAction:
    """تمثيل إجراء سريع واحد"""
    
    def __init__(self, 
                 id: str,
                 name: str,
                 icon: str,
                 tooltip: str,
                 handler: Callable,
                 category: str = "عام",
                 enabled_by_default: bool = True):
        self.id = id
        self.name = name
        self.icon = icon
        self.tooltip = tooltip
        self.handler = handler
        self.category = category
        self.enabled_by_default = enabled_by_default


class QuickActionsConfigDialog(QDialog):
    """نافذة تخصيص الإجراءات السريعة"""
    
    def __init__(self, toolbar, parent=None):
        super().__init__(parent)
        self.toolbar = toolbar
        self.setup_ui()
        self.load_current_actions()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تخصيص شريط الإجراءات السريعة")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("<h2>⚙️ تخصيص الإجراءات السريعة</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # الوصف
        desc = QLabel(
            "اختر الإجراءات التي تريد عرضها في شريط الأدوات. "
            "يمكنك تفعيل/تعطيل أي إجراء حسب احتياجاتك."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # القائمة
        self.actions_list = QListWidget()
        self.actions_list.setAlternatingRowColors(True)
        layout.addWidget(self.actions_list)
        
        # معلومات
        info = QLabel(
            "💡 <b>ملاحظة:</b> سيتم تطبيق التغييرات فوراً عند الضغط على 'حفظ'."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        select_all_btn = QPushButton("✓ اختيار الكل")
        select_all_btn.clicked.connect(self.select_all)
        buttons_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ إلغاء الكل")
        deselect_all_btn.clicked.connect(self.deselect_all)
        buttons_layout.addWidget(deselect_all_btn)
        
        reset_btn = QPushButton("🔄 إعادة تعيين")
        reset_btn.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_and_close)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("✗ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_current_actions(self):
        """تحميل الإجراءات الحالية"""
        self.actions_list.clear()
        
        # تجميع حسب الفئات
        categories = {}
        for action in self.toolbar.available_actions.values():
            if action.category not in categories:
                categories[action.category] = []
            categories[action.category].append(action)
        
        # عرض الإجراءات
        for category in sorted(categories.keys()):
            # عنوان الفئة
            category_item = QListWidgetItem(f"📁 {category}")
            category_font = QFont()
            category_font.setBold(True)
            category_item.setFont(category_font)
            category_item.setBackground(Qt.lightGray)
            category_item.setFlags(Qt.NoItemFlags)
            self.actions_list.addItem(category_item)
            
            # الإجراءات
            for action in categories[category]:
                item = QListWidgetItem(f"   {action.icon} {action.name}")
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                
                # التحقق من التفعيل
                is_enabled = action.id in self.toolbar.enabled_actions
                item.setCheckState(Qt.Checked if is_enabled else Qt.Unchecked)
                item.setData(Qt.UserRole, action.id)
                
                self.actions_list.addItem(item)
    
    def select_all(self):
        """اختيار جميع الإجراءات"""
        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """إلغاء جميع الإجراءات"""
        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)
    
    def reset_to_defaults(self):
        """إعادة تعيين للافتراضي"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد إعادة تعيين جميع الإجراءات للإعدادات الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for i in range(self.actions_list.count()):
                item = self.actions_list.item(i)
                if item.flags() & Qt.ItemIsUserCheckable:
                    action_id = item.data(Qt.UserRole)
                    action = self.toolbar.available_actions.get(action_id)
                    if action:
                        item.setCheckState(Qt.Checked if action.enabled_by_default else Qt.Unchecked)
    
    def save_and_close(self):
        """حفظ وإغلاق"""
        # جمع الإجراءات المفعلة
        enabled_actions = []
        for i in range(self.actions_list.count()):
            item = self.actions_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                if item.checkState() == Qt.Checked:
                    action_id = item.data(Qt.UserRole)
                    enabled_actions.append(action_id)
        
        # تطبيق التغييرات
        self.toolbar.update_enabled_actions(enabled_actions)
        self.accept()


class QuickActionsToolbar(QToolBar):
    """
    شريط الإجراءات السريعة
    
    Features:
    - أزرار سريعة للوظائف الأكثر استخداماً
    - قابل للتخصيص من قبل المستخدم
    - يحفظ التفضيلات
    - عرض أيقونات + نصوص
    """
    
    def __init__(self, main_window, parent=None):
        super().__init__("شريط الإجراءات السريعة", parent)
        self.main_window = main_window
        self.settings = QSettings('LogicalVersion', 'ERP')
        
        # تعريف جميع الإجراءات المتاحة
        self.available_actions: Dict[str, QuickAction] = {}
        self.enabled_actions: List[str] = []
        
        # إعداد الشريط
        self.setup_actions()
        self.setup_toolbar()
        self.load_enabled_actions()
        self.populate_toolbar()
    
    def setup_actions(self):
        """تعريف جميع الإجراءات المتاحة"""
        # فئة: ملف
        self.available_actions['new_invoice'] = QuickAction(
            'new_invoice',
            'فاتورة جديدة',
            '📝',
            'إنشاء فاتورة بيع جديدة (Ctrl+N)',
            lambda: self.main_window.new_sale() if hasattr(self.main_window, 'new_sale') else None,
            'ملف',
            True
        )
        
        self.available_actions['backup'] = QuickAction(
            'backup',
            'نسخة احتياطية',
            '💾',
            'إنشاء نسخة احتياطية من البيانات (Ctrl+B)',
            lambda: self.main_window.backup_database() if hasattr(self.main_window, 'backup_database') else None,
            'ملف',
            True
        )
        
        # فئة: مخزون
        self.available_actions['new_product'] = QuickAction(
            'new_product',
            'منتج جديد',
            '📦',
            'إضافة منتج جديد للمخزون',
            lambda: self.main_window.add_product() if hasattr(self.main_window, 'add_product') else None,
            'مخزون',
            True
        )
        
        self.available_actions['inventory_report'] = QuickAction(
            'inventory_report',
            'تقرير المخزون',
            '📊',
            'عرض تقرير حالة المخزون',
            lambda: self.main_window.inventory_report() if hasattr(self.main_window, 'inventory_report') else None,
            'مخزون',
            False
        )
        
        # فئة: مبيعات
        self.available_actions['pos'] = QuickAction(
            'pos',
            'نقطة بيع',
            '🛒',
            'فتح شاشة نقطة البيع',
            lambda: self.main_window.open_pos() if hasattr(self.main_window, 'open_pos') else None,
            'مبيعات',
            True
        )
        
        self.available_actions['sales_report'] = QuickAction(
            'sales_report',
            'تقرير المبيعات',
            '💰',
            'عرض تقرير المبيعات',
            lambda: self.main_window.sales_report() if hasattr(self.main_window, 'sales_report') else None,
            'مبيعات',
            False
        )
        
        # فئة: عملاء
        self.available_actions['new_customer'] = QuickAction(
            'new_customer',
            'عميل جديد',
            '👤',
            'إضافة عميل جديد',
            lambda: self.main_window.add_customer() if hasattr(self.main_window, 'add_customer') else None,
            'عملاء',
            False
        )
        
        # فئة: تقارير
        self.available_actions['daily_report'] = QuickAction(
            'daily_report',
            'تقرير يومي',
            '📅',
            'عرض التقرير اليومي',
            lambda: self.main_window.daily_report() if hasattr(self.main_window, 'daily_report') else None,
            'تقارير',
            True
        )
        
        self.available_actions['dashboard'] = QuickAction(
            'dashboard',
            'لوحة المعلومات',
            '📈',
            'عرض لوحة المعلومات الرئيسية (Ctrl+D)',
            lambda: self.main_window.show_main_dashboard() if hasattr(self.main_window, 'show_main_dashboard') else None,
            'تقارير',
            True
        )
        
        # فئة: إعدادات
        self.available_actions['notifications'] = QuickAction(
            'notifications',
            'الإشعارات',
            '🔔',
            'مركز الإشعارات (Ctrl+Shift+N)',
            lambda: self.main_window.show_notifications_center() if hasattr(self.main_window, 'show_notifications_center') else None,
            'إعدادات',
            True
        )
        
        self.available_actions['theme'] = QuickAction(
            'theme',
            'تغيير السمة',
            '🎨',
            'التبديل بين الوضع الفاتح والداكن (Ctrl+T)',
            lambda: self.main_window.show_theme_selector() if hasattr(self.main_window, 'show_theme_selector') else None,
            'إعدادات',
            False
        )
        
        # فئة: مساعدة
        self.available_actions['refresh'] = QuickAction(
            'refresh',
            'تحديث',
            '🔄',
            'تحديث البيانات (F5)',
            lambda: self.main_window.refresh_data() if hasattr(self.main_window, 'refresh_data') else None,
            'أدوات',
            True
        )
    
    def setup_toolbar(self):
        """إعداد خصائص الشريط"""
        self.setMovable(True)
        self.setFloatable(True)
        self.setAllowedAreas(Qt.TopToolBarArea | Qt.BottomToolBarArea | Qt.LeftToolBarArea | Qt.RightToolBarArea)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(24, 24))
        
        # زر تخصيص في نهاية الشريط
        self.addSeparator()
        customize_action = self.addAction("⚙️ تخصيص")
        customize_action.setToolTip("تخصيص الإجراءات المعروضة في الشريط")
        customize_action.triggered.connect(self.show_customize_dialog)
    
    def load_enabled_actions(self):
        """تحميل الإجراءات المفعلة من الإعدادات"""
        saved = self.settings.value('quick_actions/enabled', None)
        
        if saved:
            self.enabled_actions = saved
        else:
            # استخدام الافتراضية
            self.enabled_actions = [
                action_id for action_id, action in self.available_actions.items()
                if action.enabled_by_default
            ]
    
    def save_enabled_actions(self):
        """حفظ الإجراءات المفعلة"""
        self.settings.setValue('quick_actions/enabled', self.enabled_actions)
    
    def populate_toolbar(self):
        """ملء الشريط بالأزرار"""
        # إزالة جميع الأزرار الحالية (ماعدا زر التخصيص)
        actions = self.actions()[:-2]  # آخر اثنان هما separator و customize
        for action in actions:
            self.removeAction(action)
        
        # إضافة الأزرار المفعلة
        for action_id in self.enabled_actions:
            if action_id in self.available_actions:
                action = self.available_actions[action_id]
                btn_action = self.addAction(f"{action.icon} {action.name}")
                btn_action.setToolTip(action.tooltip)
                btn_action.triggered.connect(action.handler)
    
    def update_enabled_actions(self, new_enabled: List[str]):
        """تحديث الإجراءات المفعلة"""
        self.enabled_actions = new_enabled
        self.save_enabled_actions()
        self.populate_toolbar()
    
    def show_customize_dialog(self):
        """عرض نافذة التخصيص"""
        dialog = QuickActionsConfigDialog(self, self.main_window)
        dialog.exec()


def add_quick_actions_toolbar(main_window) -> QuickActionsToolbar:
    """
    إضافة شريط الإجراءات السريعة للنافذة الرئيسية
    
    Args:
        main_window: النافذة الرئيسية
    
    Returns:
        QuickActionsToolbar: الشريط المنشأ
    """
    toolbar = QuickActionsToolbar(main_window, main_window)
    main_window.addToolBar(Qt.TopToolBarArea, toolbar)
    return toolbar
