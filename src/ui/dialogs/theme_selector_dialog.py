"""
Theme Selector Dialog - نافذة اختيار السمة
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QRadioButton, QButtonGroup, QGroupBox,
    QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .theme_manager import get_theme_manager


class ThemePreview(QFrame):
    """معاينة صغيرة للسمة"""
    
    def __init__(self, theme_name: str, colors: dict):
        super().__init__()
        self.setFixedSize(200, 150)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # عنوان
        title = QLabel(f"<b>{'الوضع الداكن' if theme_name == 'dark' else 'الوضع الفاتح'}</b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # معاينة الألوان
        colors_widget = QWidget()
        colors_layout = QHBoxLayout(colors_widget)
        colors_layout.setSpacing(4)
        
        color_keys = ['primary', 'background', 'surface', 'text_primary']
        for key in color_keys:
            color_box = QFrame()
            color_box.setFixedSize(40, 40)
            color_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors[key]};
                    border: 1px solid #999;
                    border-radius: 4px;
                }}
            """)
            colors_layout.addWidget(color_box)
        
        layout.addWidget(colors_widget)
        layout.addStretch()


class ThemeSelectorDialog(QDialog):
    """
    نافذة اختيار السمة
    """
    
    theme_changed = Signal(str)  # يُصدر اسم السمة الجديدة
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        self.setup_ui()
        self.load_current_theme()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("اختيار السمة - Theme Selector")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # عنوان
        title = QLabel("<h2>⚙️ اختيار سمة النظام</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # وصف
        desc = QLabel(
            "اختر السمة المناسبة لك. يمكنك التبديل بين الوضع الفاتح والداكن في أي وقت."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # مجموعة السمات
        themes_group = QGroupBox("السمات المتاحة")
        themes_layout = QVBoxLayout(themes_group)
        
        # Radio buttons
        self.theme_buttons = QButtonGroup(self)
        
        # Light theme
        light_container = QWidget()
        light_layout = QHBoxLayout(light_container)
        light_layout.setContentsMargins(0, 0, 0, 0)
        
        self.light_radio = QRadioButton("☀️ الوضع الفاتح (Light Mode)")
        self.theme_buttons.addButton(self.light_radio, 0)
        light_layout.addWidget(self.light_radio)
        
        light_preview = ThemePreview('light', self.theme_manager.LIGHT_COLORS)
        light_layout.addWidget(light_preview)
        light_layout.addStretch()
        
        themes_layout.addWidget(light_container)
        
        # Dark theme
        dark_container = QWidget()
        dark_layout = QHBoxLayout(dark_container)
        dark_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dark_radio = QRadioButton("🌙 الوضع الداكن (Dark Mode)")
        self.theme_buttons.addButton(self.dark_radio, 1)
        dark_layout.addWidget(self.dark_radio)
        
        dark_preview = ThemePreview('dark', self.theme_manager.DARK_COLORS)
        dark_layout.addWidget(dark_preview)
        dark_layout.addStretch()
        
        themes_layout.addWidget(dark_container)
        
        layout.addWidget(themes_group)
        
        # معلومات إضافية
        info = QLabel(
            "💡 <b>ملاحظة:</b> سيتم تطبيق السمة على جميع نوافذ البرنامج فورًا."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        preview_btn = QPushButton("👁️ معاينة")
        preview_btn.clicked.connect(self.preview_theme)
        buttons_layout.addWidget(preview_btn)
        
        apply_btn = QPushButton("✓ تطبيق")
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self.apply_theme)
        buttons_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("✗ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def load_current_theme(self):
        """تحميل السمة الحالية"""
        current = self.theme_manager.get_current_theme()
        if current == 'dark':
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)
    
    def get_selected_theme(self) -> str:
        """الحصول على السمة المختارة"""
        return 'dark' if self.dark_radio.isChecked() else 'light'
    
    def preview_theme(self):
        """معاينة السمة"""
        theme = self.get_selected_theme()
        self.theme_manager.apply_theme(theme)
        self.theme_changed.emit(theme)
    
    def apply_theme(self):
        """تطبيق السمة وإغلاق النافذة"""
        theme = self.get_selected_theme()
        self.theme_manager.apply_theme(theme)
        self.theme_changed.emit(theme)
        self.accept()
    
    def reject(self):
        """إلغاء - إعادة السمة الأصلية"""
        # Restore original theme
        original = self.theme_manager.settings.value('theme', 'light')
        self.theme_manager.apply_theme(original)
        super().reject()
