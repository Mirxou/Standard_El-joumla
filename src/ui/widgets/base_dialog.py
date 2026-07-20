from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.custom_title_bar import CustomTitleBar


class BaseDialog(QDialog):
    """
    متحكم رئيسي لجميع النوافذ الثانوية (صناديق الحوار).
    يطبق التصميم الموحد (Aurora Noir v4.0)، يمنع التداخل عند التصغير/التكبير،
    ويزيل الحاجة لتكرار أكواد الشفافية وتأثيرات الظل.
    """

    def __init__(self, title="نافذة", parent=None):
        super().__init__(parent)

        # إعداد النافذة الأساسية لتكون بدون إطار صلب من النظام
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        # إزالة الخلفية الشفافة المسببة للمشاكل، النافذة ستكون صلبة تماماً
        # self.setAttribute(Qt.WA_TranslucentBackground, False)

        # تخطيط جذري (للسماح برسم الظل)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)

        # الإطار الرئيسي الذي يحتوي على التصميم الفعلي
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #181D2E;
                border: 1px solid #2A3150;
                border-radius: 16px;
                color: #F0F2F5;
            }
            QLabel {
                color: #F0F2F5;
            }
        """)

        # إضافة ظل للإطار لتمييز النافذة
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#C8A54E"))  # لون الهوية (gold)
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)

        root_layout.addWidget(self.main_frame)

        # التخطيط الداخلي للنافذة (شريط العنوان + المحتوى)
        self._internal_layout = QVBoxLayout(self.main_frame)
        self._internal_layout.setContentsMargins(0, 0, 0, 10)
        self._internal_layout.setSpacing(0)

        # شريط العنوان المخصص
        self.title_bar = CustomTitleBar(self, title=title, is_dialog=True)
        self._internal_layout.addWidget(self.title_bar)

        # مساحة المحتوى الرئيسية التي سيتم بناء الواجهات داخلها
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # فرض سياسة تمدد لمنع تداخل النصوص عند تعديل حجم النافذة
        self.content_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.content_widget.setMinimumSize(350, 200)  # حجم أدنى لتجنب ضغط العناصر

        self._internal_layout.addWidget(self.content_widget)