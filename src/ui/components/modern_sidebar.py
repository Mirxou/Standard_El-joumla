from pathlib import Path
from typing import Dict

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from src.ui.styles.design_tokens import C


# ═══════════════════════════════════════════════════════════════════════════
#  Aurora Noir v4.0 Sidebar — Gold + Deep Void
# ═══════════════════════════════════════════════════════════════════════════

class ModernSidebar(QFrame):
    """
    Aurora Noir Sidebar v4.0
    Features:
    - Collapsible (Icon-only mode vs Full mode)
    - Animated transitions
    - Gold accent on active items
    - Deep void gradient background
    """

    # Signal: page_id, button_text
    page_changed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modernSidebar")

        # Current state
        self.is_collapsed = False
        self.expanded_width = 260
        self.collapsed_width = 72

        # Mapping: button_id -> QPushButton
        self.buttons: Dict[str, QPushButton] = {}

        self.setup_ui()
        self._apply_aurora_noir_styles()

    def setup_ui(self):
        """Initialize the UI layout"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 20, 12, 20)
        self.layout.setSpacing(4)
        self.menu_layout = self.layout  # Alias for tests

        # 1. Header (Logo/Title)
        self._setup_header()

        # 2. Toggle Button (Burger Menu)
        self._setup_toggle_btn()

        # Spacer
        self.layout.addSpacing(12)

        # 3. Navigation Buttons
        self._setup_nav_buttons()

        # Checkable logic
        self._current_active_btn = None

        # Bottom Spacer
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 4. Settings/Logout at bottom
        self._setup_bottom_buttons()

        # Fixed width initially
        self.setFixedWidth(self.expanded_width)

    def _apply_aurora_noir_styles(self):
        """Apply Aurora Noir v4.0 styles — Gold + Deep Void"""
        self.setStyleSheet(f"""
            QFrame#modernSidebar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {C.BG_PRIMARY}, stop:1 {C.BG_DEEP});
                border-left: 1px solid {C.BORDER_SUBTLE};
                border-radius: 0px;
            }}
            QLabel#sidebarTitle {{
                font-size: 15px;
                font-weight: 900;
                color: {C.ACCENT_GOLD};
                letter-spacing: 0.5px;
            }}
            QLabel#sidebarSubtitle {{
                font-size: 11px;
                color: {C.TEXT_MUTED};
                font-weight: 400;
            }}
            QPushButton#sidebarToggleBtn {{
                background: transparent;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                color: {C.TEXT_MUTED};
                padding: 6px;
            }}
            QPushButton#sidebarToggleBtn:hover {{
                background-color: {C.ACCENT_GOLD_SUBTLE};
                color: {C.ACCENT_GOLD};
            }}
            QPushButton#modernSidebarBtn {{
                background: transparent;
                border: none;
                border-right: 3px solid transparent;
                border-radius: 10px;
                text-align: right;
                padding: 10px 14px;
                color: {C.TEXT_SECONDARY};
                font-weight: 500;
                font-size: 13px;
            }}
            QPushButton#modernSidebarBtn:hover {{
                background-color: {C.ACCENT_GOLD_SUBTLE};
                color: {C.TEXT_PRIMARY};
                border-right: 3px solid {C.ACCENT_GOLD_GLOW};
            }}
            QPushButton#modernSidebarBtn:checked {{
                background: qlineargradient(x1:1,y1:0,x2:0,y2:0,
                    stop:0 {C.ACCENT_GOLD_GLOW}, stop:1 {C.ACCENT_GOLD_SHIMMER});
                color: {C.ACCENT_GOLD};
                border-right: 3px solid {C.ACCENT_GOLD};
                font-weight: 700;
            }}
            QPushButton#sidebarLogoutBtn {{
                color: {C.ACCENT_CORAL};
            }}
            QPushButton#sidebarLogoutBtn:hover {{
                background-color: {C.ACCENT_CORAL_SUBTLE};
                color: {C.ACCENT_CORAL};
            }}
        """)

    def _setup_header(self):
        """Header with App Title — Aurora Noir branding"""
        self.header_container = QFrame()
        self.header_container.setStyleSheet(
            f"background: transparent; border-bottom: 1px solid {C.BORDER_SUBTLE}; padding-bottom: 8px;"
        )
        self.header_layout = QVBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 8)
        self.header_layout.setSpacing(2)

        self.app_logo = QLabel()
        self.app_logo.setAlignment(Qt.AlignCenter)
        self.app_logo.setContentsMargins(0, 8, 0, 4)
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            self.app_logo.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.app_logo.setText("🛒")
            self.app_logo.setStyleSheet(f"font-size: 26px; background: transparent; color: {C.ACCENT_GOLD};")

        from ...utils.i18n_api import I18n

        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        self.app_title = QLabel(self.i18n.get_message("app_name_short"))
        self.app_title.setObjectName("sidebarTitle")
        self.app_title.setAlignment(Qt.AlignCenter)

        self.app_subtitle = QLabel(self.i18n.get_message("app_description"))
        self.app_subtitle.setObjectName("sidebarSubtitle")
        self.app_subtitle.setAlignment(Qt.AlignCenter)

        self.header_layout.addWidget(self.app_logo)
        self.header_layout.addWidget(self.app_title)
        self.header_layout.addWidget(self.app_subtitle)

        self.layout.addWidget(self.header_container)

    def _setup_toggle_btn(self):
        """Button to toggle collapse state"""
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setObjectName("sidebarToggleBtn")
        self.toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_btn.setToolTip("تبديل القائمة")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)

        self.layout.insertWidget(0, self.toggle_btn, 0, Qt.AlignRight)

    def _setup_nav_buttons(self):
        """Create main navigation items"""
        menu_items = [
            ("home", self.i18n.get_message("dashboard"), "🏠"),
            ("inventory", self.i18n.get_message("inventory"), "📦"),
            ("sales", self.i18n.get_message("sales"), "💰"),
            ("purchases", self.i18n.get_message("purchases"), "🛒"),
            ("payments", self.i18n.get_message("payments"), "💳"),
            ("reports", self.i18n.get_message("reports"), "📊"),
            ("contacts", self.i18n.get_message("customers"), "👥"),
            (
                "performance",
                self.i18n.get_message("performance", default="الأداء"),
                "🚀",
            ),
            # Application Features
            ("users", self.i18n.get_message("users", default="المستخدمين"), "👤"),
            ("system", self.i18n.get_message("settings"), "💻"),
            ("audit", self.i18n.get_message("audit", default="السجلات"), "📝"),
            (
                "notifications",
                self.i18n.get_message("notifications", default="الإشعارات"),
                "🔔",
            ),
        ]

        for btn_id, label, icon_char in menu_items:
            btn = self._create_btn(btn_id, label, icon_char)
            self.layout.addWidget(btn)
            self.buttons[btn_id] = btn

    def _setup_bottom_buttons(self):
        """Bottom actions like Settings"""
        bottom_items = [
            ("settings", self.i18n.get_message("settings"), "⚙️"),
            ("logout", self.i18n.get_message("logout"), "🚪"),
        ]

        for btn_id, label, icon_char in bottom_items:
            btn = self._create_btn(btn_id, label, icon_char)
            if btn_id == "logout":
                btn.setObjectName("sidebarLogoutBtn")
            self.layout.addWidget(btn)
            self.buttons[btn_id] = btn

    def _create_btn(self, btn_id: str, label: str, icon_char: str) -> QPushButton:
        """Helper to create a unified sidebar button with Icon + Text"""
        btn = QPushButton(f"{icon_char}   {label}")
        btn.setProperty("icon_char", icon_char)
        btn.setProperty("full_text", label)
        btn.setObjectName("modernSidebarBtn")
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.PointingHandCursor))

        btn.clicked.connect(lambda checked=False, b_id=btn_id, b_text=label: self._on_btn_clicked(b_id, b_text))

        return btn

    def _on_btn_clicked(self, btn_id: str, btn_text: str):
        """Handle button selection"""
        for bid, btn in self.buttons.items():
            if bid != btn_id:
                btn.setChecked(False)

        self.buttons[btn_id].setChecked(True)
        self.page_changed.emit(btn_id, btn_text)

    def toggle_sidebar(self):
        """Animate expand/collapse"""
        width_start = self.width()
        width_end = self.collapsed_width if not self.is_collapsed else self.expanded_width

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(width_start)
        self.animation.setEndValue(width_end)
        self.animation.setEasingCurve(QEasingCurve.InOutQuart)

        self.setMaximumWidth(width_end)

        self.animation.start()

        self.is_collapsed = not self.is_collapsed
        self._update_ui_state()

    def _update_ui_state(self):
        """Update labels and icons based on collapsed state"""
        for btn in self.buttons.values():
            icon = btn.property("icon_char")
            label = btn.property("full_text")

            if self.is_collapsed:
                btn.setText(icon)
                btn.setToolTip(label)
                btn.setStyleSheet("text-align: center; padding: 10px 0;")
            else:
                btn.setText(f"{icon}   {label}")
                btn.setToolTip("")
                btn.setStyleSheet("text-align: right; padding: 10px 14px;")

        if self.is_collapsed:
            self.app_title.hide()
            self.app_subtitle.hide()
            self.app_logo.show()
        else:
            self.app_title.show()
            self.app_subtitle.show()
            self.app_logo.show()

    def set_active(self, page_id: str):
        """Programmatically set active page"""
        if page_id in self.buttons:
            self.buttons[page_id].click()

    # --- Test Suite Compatibility Methods ---
    def add_menu_item(self, label, icon, callback):
        """إضافة عنصر قائمة (توافق مع الاختبارات)"""
        btn_id = label.lower().replace(" ", "_")
        btn = self._create_btn(btn_id, label, icon)
        btn.clicked.connect(callback)
        self.layout.insertWidget(self.layout.count() - 1, btn)
        self.buttons[btn_id] = btn
        return btn

    def add_separator(self):
        """إضافة فاصل"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {C.BORDER_SUBTLE}; margin: 8px 4px; max-height: 1px;")
        self.layout.insertWidget(self.layout.count() - 1, line)
        return line

    def set_active_item(self, label):
        """تعيين العنصر النشط حسب الاسم"""
        for btn in self.buttons.values():
            if btn.property("full_text") == label:
                btn.click()
                return True
        return False

    def collapse(self):
        if not self.is_collapsed:
            self.toggle_sidebar()

    def expand(self):
        if self.is_collapsed:
            self.toggle_sidebar()

    def toggle(self):
        self.toggle_sidebar()

    def set_width(self, width):
        self.setFixedWidth(width)

    def get_menu_items(self) -> list:
        return list(self.buttons.values())

    def clear_menu(self):
        for btn in self.buttons.values():
            self.layout.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()