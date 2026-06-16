"""
نافذة عرض الأخطاء للمستخدم
User Error Display Dialog

نافذة حوار لعرض الأخطاء بطريقة مفهومة ومناسبة للمستخدم
Dialog window for displaying errors in a user-friendly manner
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..utils.i18n_api import I18n


class ErrorDialog(QDialog):
    """نافذة عرض الأخطاء - Error Display Dialog"""

    # إشارات - Signals
    error_reported = Signal(dict)  # عند الإبلاغ عن خطأ

    def __init__(self, parent=None):
        super().__init__(parent)

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent / "locales"))

        self.setWindowTitle(self.i18n.get_message("system_error_title"))
        self.setModal(True)
        self.setMinimumSize(500, 300)
        self.setMaximumSize(800, 600)

        # إعداد الواجهة
        self._setup_ui()
        self._setup_styles()

        # متغيرات
        self.error_info = {}
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.accept)

    def _setup_ui(self):
        """إعداد واجهة المستخدم - Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # رأس النافذة - Header
        self._create_header(layout)

        # محتوى الخطأ - Error content
        self._create_content(layout)

        # أزرار التحكم - Control buttons
        self._create_buttons(layout)

    def _create_header(self, layout: QVBoxLayout):
        """إنشاء رأس النافذة - Create header"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_layout = QHBoxLayout(header_frame)

        # أيقونة الخطأ - Error icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.icon_label)

        # معلومات الخطأ الأساسية - Basic error info
        info_layout = QVBoxLayout()

        self.title_label = QLabel(self.i18n.get_message("system_error_occurred"))
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        info_layout.addWidget(self.title_label)

        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Arial", 10))
        info_layout.addWidget(self.message_label)

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 8))
        self.time_label.setStyleSheet("color: gray;")
        info_layout.addWidget(self.time_label)

        header_layout.addLayout(info_layout, 1)
        layout.addWidget(header_frame)

    def _create_content(self, layout: QVBoxLayout):
        """إنشاء محتوى النافذة - Create content"""
        # منطقة التفاصيل - Details area
        self.details_frame = QFrame()
        self.details_frame.setFrameStyle(QFrame.Box)
        self.details_frame.hide()

        details_layout = QVBoxLayout(self.details_frame)

        # تفاصيل الخطأ - Error details
        details_label = QLabel(self.i18n.get_message("error_details"))
        details_label.setFont(QFont("Arial", 10, QFont.Bold))
        details_layout.addWidget(details_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        self.details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.details_text)

        layout.addWidget(self.details_frame)

    def _create_buttons(self, layout: QVBoxLayout):
        """إنشاء أزرار التحكم - Create control buttons"""
        buttons_layout = QHBoxLayout()

        # زر عرض التفاصيل - Show details button
        self.details_button = QPushButton(self.i18n.get_message("show_details"))
        self.details_button.clicked.connect(self._toggle_details)
        buttons_layout.addWidget(self.details_button)

        # زر الإبلاغ عن الخطأ - Report error button
        self.report_button = QPushButton(self.i18n.get_message("report_error"))
        self.report_button.clicked.connect(self._report_error)
        buttons_layout.addWidget(self.report_button)

        # مساحة فارغة - Spacer
        buttons_layout.addStretch()

        # زر الإغلاق - Close button
        self.close_button = QPushButton(self.i18n.get_message("close_button"))
        self.close_button.clicked.connect(self.accept)
        self.close_button.setDefault(True)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    def _setup_styles(self):
        """إعداد الأنماط - Setup styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }

            QLabel {
                color: #333;
                background: transparent;
                border: none;
            }

            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #005a9e;
            }

            QPushButton:pressed {
                background-color: #004578;
            }

            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)

    def show_error(self, error_info: Dict[str, Any], auto_close_seconds: Optional[int] = None):
        """
        عرض الخطأ في النافذة
        Display error in dialog
        """
        self.error_info = error_info

        # تحديث المحتوى - Update content
        self._update_content()

        # إعداد الإغلاق التلقائي - Setup auto close
        if auto_close_seconds and auto_close_seconds > 0:
            self.auto_close_timer.start(auto_close_seconds * 1000)
            self.close_button.setText(f"{self.i18n.get_message('close_button')} ({auto_close_seconds})")
            self._start_countdown(auto_close_seconds)

        # عرض النافذة - Show dialog
        self.show()
        self.raise_()
        self.activateWindow()

    def _update_content(self):
        """تحديث محتوى النافذة - Update dialog content"""
        # الحصول على معلومات الخطأ - Get error info
        severity = self.error_info.get("severity", "medium")
        category = self.error_info.get("category", "system")
        message = self.error_info.get("user_message", self.error_info.get("message", "خطأ غير محدد"))
        timestamp = self.error_info.get("timestamp", datetime.now().isoformat())

        # تحديث الأيقونة - Update icon
        self._update_icon(severity)

        # تحديث العنوان - Update title
        title = self._get_title_by_category(category)
        self.title_label.setText(title)

        # تحديث الرسالة - Update message
        self.message_label.setText(message)

        # تحديث الوقت - Update time
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_str = timestamp

        self.time_label.setText(self.i18n.get_message("time_label", time=time_str))

        # تحديث التفاصيل - Update details
        self._update_details()

    def _update_icon(self, severity: str):
        """تحديث أيقونة الخطأ - Update error icon"""
        # يمكن إضافة أيقونات مخصصة هنا
        # Custom icons can be added here
        icon_text = "⚠️"

        if severity == "critical":
            icon_text = "🚨"
            self.icon_label.setStyleSheet("color: #d32f2f; font-size: 32px;")
        elif severity == "high":
            icon_text = "❌"
            self.icon_label.setStyleSheet("color: #f44336; font-size: 32px;")
        elif severity == "medium":
            icon_text = "⚠️"
            self.icon_label.setStyleSheet("color: #ff9800; font-size: 32px;")
        else:
            icon_text = "ℹ️"
            self.icon_label.setStyleSheet("color: #2196f3; font-size: 32px;")

        self.icon_label.setText(icon_text)

    def _get_title_by_category(self, category: str) -> str:
        """الحصول على العنوان حسب الفئة - Get title by category"""
        titles = {
            "database": self.i18n.get_message("error_database"),
            "authentication": self.i18n.get_message("error_authentication"),
            "validation": self.i18n.get_message("error_validation"),
            "business_logic": self.i18n.get_message("error_business_logic"),
            "ui": self.i18n.get_message("error_ui"),
            "network": self.i18n.get_message("error_network"),
            "file_system": self.i18n.get_message("error_file_system"),
            "system": self.i18n.get_message("error_system"),
        }
        return titles.get(category, self.i18n.get_message("error_system"))

    def _update_details(self):
        """تحديث تفاصيل الخطأ - Update error details"""
        details = []

        # معلومات أساسية - Basic info
        details.append(f"{self.i18n.get_message('error_code')} {self.error_info.get('error_code', 'غير محدد')}")
        details.append(f"{self.i18n.get_message('error_category')} {self.error_info.get('category', 'غير محدد')}")
        details.append(f"{self.i18n.get_message('error_severity')} {self.error_info.get('severity', 'غير محدد')}")

        # تفاصيل إضافية - Additional details
        if self.error_info.get("details"):
            details.append(f"\n{self.i18n.get_message('additional_details')}")
            for key, value in self.error_info["details"].items():
                details.append(f"  {key}: {value}")

        # السياق - Context
        if self.error_info.get("context"):
            details.append(f"\n{self.i18n.get_message('context_label')} {self.error_info['context']}")

        # تتبع المكدس - Stack trace
        if self.error_info.get("traceback"):
            details.append(f"\n{self.i18n.get_message('stack_trace')}:\n{self.error_info['traceback']}")

        self.details_text.setPlainText("\n".join(details))

    def _toggle_details(self):
        """تبديل عرض التفاصيل - Toggle details display"""
        if self.details_frame.isVisible():
            self.details_frame.hide()
            self.details_button.setText(self.i18n.get_message("show_details"))
            self.resize(self.width(), self.minimumHeight())
        else:
            self.details_frame.show()
            self.details_button.setText(self.i18n.get_message("hide_details"))
            self.resize(self.width(), 600)

    def _report_error(self):
        """إبلاغ عن الخطأ - Report error"""
        # إرسال إشارة الإبلاغ عن الخطأ
        self.error_reported.emit(self.error_info)

        # تغيير نص الزر
        self.report_button.setText(self.i18n.get_message("error_reported"))
        self.report_button.setEnabled(False)

        # إعادة تفعيل الزر بعد 3 ثوان
        QTimer.singleShot(
            3000,
            lambda: (
                self.report_button.setText(self.i18n.get_message("report_error")),
                self.report_button.setEnabled(True),
            ),
        )

    def _start_countdown(self, seconds: int):
        """بدء العد التنازلي للإغلاق - Start countdown for auto close"""

        def update_countdown():
            nonlocal seconds
            seconds -= 1
            if seconds > 0:
                self.close_button.setText(f"{self.i18n.get_message('close_button')} ({seconds})")
                QTimer.singleShot(1000, update_countdown)
            else:
                self.close_button.setText(self.i18n.get_message("close_button"))

        QTimer.singleShot(1000, update_countdown)

    def closeEvent(self, event):
        """حدث إغلاق النافذة - Window close event"""
        self.auto_close_timer.stop()
        super().closeEvent(event)


class ErrorNotification(QWidget):
    """إشعار خطأ مبسط - Simple error notification"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 80)

        # إعداد الواجهة
        self._setup_ui()

        # مؤقت الإخفاء
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide)

    def _setup_ui(self):
        """إعداد واجهة المستخدم - Setup user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # أيقونة
        self.icon_label = QLabel("⚠️")
        self.icon_label.setFont(QFont("Arial", 20))
        layout.addWidget(self.icon_label)

        # النص
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.text_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.text_label, 1)

        # الأنماط
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 235, 235, 240);
                border: 2px solid #f44336;
                border-radius: 10px;
            }
            QLabel {
                color: #d32f2f;
                background: transparent;
                border: none;
            }
        """)

    def show_notification(self, message: str, duration: int = 3000):
        """عرض الإشعار - Show notification"""
        self.text_label.setText(message)

        # تحديد الموقع
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 20
            self.move(x, y)

        # عرض الإشعار
        self.show()
        self.raise_()

        # إخفاء تلقائي
        self.hide_timer.start(duration)


def show_error_dialog(error_info: Dict[str, Any], parent=None, auto_close_seconds: Optional[int] = None) -> ErrorDialog:
    """
    دالة مساعدة لعرض نافذة الخطأ
    Helper function to show error dialog
    """
    dialog = ErrorDialog(parent)
    dialog.show_error(error_info, auto_close_seconds)
    return dialog


def show_error_notification(message: str, parent=None, duration: int = 3000) -> ErrorNotification:
    """
    دالة مساعدة لعرض إشعار الخطأ
    Helper function to show error notification
    """
    notification = ErrorNotification(parent)
    notification.show_notification(message, duration)
    return notification
