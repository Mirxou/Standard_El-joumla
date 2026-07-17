#!/usr/bin/env python3
"""
نافذة تسجيل الدخول - Login Dialog — "Royal Gate" Design
واجهة تسجيل دخول فاخرة بتصميم ذهبي احترافي مع دعم اللغة العربية
"""

import logging
import math
import random
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.base_dialog import BaseDialog

from ...services.security_service import SecurityService
from ...services.user_service import UserService, UserSession
from ...ui.animations.animation_manager import AnimationManager
from ...ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from ...ui.widgets.quantum_notification import NotificationManager
from ...utils.i18n_api import I18n

# ── Design Tokens ──────────────────────────────────────────────────────────
BG_VOID = "#08090d"
BG_PRIMARY = "#0f1117"
BG_SECONDARY = "#161822"
BG_TERTIARY = "#1e2030"
BORDER_DEFAULT = "#2a2d45"
BORDER_FOCUS = "#d4a853"
TEXT_PRIMARY = "#f0f0f5"
TEXT_SECONDARY = "#9496b0"
TEXT_MUTED = "#5d5f7a"
ACCENT_GOLD = "#d4a853"
ACCENT_GOLD_LIGHT = "#e8c878"
GOLD_SUBTLE = "rgba(212,168,83,0.12)"


# ═══════════════════════════════════════════════════════════════════════════
#  Gold Particle Canvas — QPainter animated background for left panel
# ═══════════════════════════════════════════════════════════════════════════
class _GoldParticleCanvas(QWidget):
    """Animated gold geometric particles painted with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._particles: list[dict] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(60)  # ~16 FPS
        self._opacity = 0.0

    def showEvent(self, event):
        super().showEvent(event)
        self._init_particles()
        self._timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _init_particles(self):
        self._particles = []
        w = max(self.width(), 200)
        h = max(self.height(), 400)
        for _ in range(35):
            self._particles.append(
                {
                    "x": random.uniform(0, w),
                    "y": random.uniform(0, h),
                    "r": random.uniform(1.0, 3.0),
                    "vx": random.uniform(-0.3, 0.3),
                    "vy": random.uniform(-0.5, -0.1),
                    "alpha": random.uniform(0.15, 0.55),
                }
            )

    def _tick(self):
        if self._opacity < 1.0:
            self._opacity = min(1.0, self._opacity + 0.04)
        w = max(self.width(), 200)
        h = max(self.height(), 400)
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -10:
                p["y"] = h + 10
                p["x"] = random.uniform(0, w)
            if p["x"] < -10:
                p["x"] = w + 10
            elif p["x"] > w + 10:
                p["x"] = -10
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        gold = QColor(ACCENT_GOLD)
        for p in self._particles:
            c = QColor(gold)
            c.setAlphaF(p["alpha"])
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QRectF(p["x"] - p["r"], p["y"] - p["r"], p["r"] * 2, p["r"] * 2))

        # Subtle connecting lines between close particles
        pen = QPen(QColor(ACCENT_GOLD))
        pen.setWidthF(0.5)
        for i in range(len(self._particles)):
            for j in range(i + 1, len(self._particles)):
                dx = self._particles[i]["x"] - self._particles[j]["x"]
                dy = self._particles[i]["y"] - self._particles[j]["y"]
                dist = math.hypot(dx, dy)
                if dist < 120:
                    c = QColor(ACCENT_GOLD)
                    c.setAlphaF(0.08 * (1 - dist / 120))
                    pen.setColor(c)
                    painter.setPen(pen)
                    painter.drawLine(
                        int(self._particles[i]["x"]),
                        int(self._particles[i]["y"]),
                        int(self._particles[j]["x"]),
                        int(self._particles[j]["y"]),
                    )
        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
#  LoginWorker — runs authentication in a background thread
# ═══════════════════════════════════════════════════════════════════════════
class LoginWorker(QThread):
    """عامل تسجيل الدخول في خيط منفصل"""

    login_completed = Signal(bool, object, str)  # success, session, message

    def __init__(self, user_service: UserService, username: str, password: str, remember_me: bool):
        super().__init__()
        self.user_service = user_service
        self.username = username
        self.password = password
        self.remember_me = remember_me

    def run(self):
        try:
            success, session, message = self.user_service.authenticate_user(
                self.username,
                self.password,
                ip_address="127.0.0.1",
                user_agent="Standard El Joumla Desktop App",
            )
            self.login_completed.emit(success, session, message or "")
        except Exception as e:
            self.login_completed.emit(False, None, f"خطأ في النظام: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  LoginDialog — "Royal Gate" premium login experience
# ═══════════════════════════════════════════════════════════════════════════
class LoginDialog(BaseDialog):
    """نافذة تسجيل الدخول — تصميم Royal Gate الذهبي"""

    login_successful = Signal(object)  # UserSession

    def __init__(self, user_service: UserService, parent=None):
        from PySide6.QtWidgets import QWidget as _W

        if parent is not None and not isinstance(parent, _W):
            parent = None
        super().__init__(title="", parent=parent)

        self.user_service = user_service
        self.current_session: Optional[UserSession] = None
        self.login_worker: Optional[LoginWorker] = None
        self.security_service = SecurityService(user_service.db)

        # i18n
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        # Animation manager
        self.animation_manager = AnimationManager(self)

        # ── Override BaseDialog chrome for the Royal Gate ───────────────
        self._apply_royal_chrome()

        # Warning label (kept for API compatibility, hidden by default)
        self.warning_label = QLabel()
        self.warning_label.setVisible(False)
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)

        # Build UI
        self.setup_ui()
        self.setup_connections()

        # Load saved credentials
        self.load_saved_credentials()

        # Fix layout after first paint
        QTimer.singleShot(0, self._fix_layout)
        QTimer.singleShot(10, self._ensure_proper_display)

        # Fade-in on show
        self.setWindowOpacity(0.0)

        # Notification manager
        self.notify = NotificationManager(self)

    # ── Chrome overrides ────────────────────────────────────────────────
    def _apply_royal_chrome(self):
        """Override BaseDialog frame & title bar for the Royal Gate look."""
        # Hide the default title bar — we draw our own left panel header
        self.title_bar.setVisible(False)
        self.title_bar.setFixedHeight(0)
        self.title_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # Force zero margins around the title bar
        self._internal_layout.setContentsMargins(0, 0, 0, 0)
        self._internal_layout.setSpacing(0)

        # Restyle main_frame
        self.main_frame.setStyleSheet(
            """
            QFrame#MainFrame {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 16px;
                color: %s;
            }
            """
            % (BG_PRIMARY, BORDER_DEFAULT, TEXT_PRIMARY)
        )

        # Change shadow to gold
        shadow = self.main_frame.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            shadow.setColor(QColor(ACCENT_GOLD))

        # Content widget — full bleed, no extra margins
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_widget.setMinimumSize(780, 520)

    # ── UI Construction ─────────────────────────────────────────────────
    def setup_ui(self):
        self.setWindowTitle(self.i18n.get_message("login_title"))
        self.setMinimumSize(780, 520)
        self.setModal(True)

        # Master horizontal split
        master = QHBoxLayout(self.content_widget)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        # ── LEFT PANEL (40%) ────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("RoyalLeftPanel")
        left.setMinimumWidth(280)
        left.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # Particle canvas (fills background)
        self._particle_canvas = _GoldParticleCanvas(left)

        left_lay.addWidget(self._particle_canvas)

        # Overlay content on top of particles (using a transparent container)
        overlay = QWidget(left)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        overlay.setGeometry(left.rect())
        overlay.raise_()
        olay = QVBoxLayout(overlay)
        olay.setAlignment(Qt.AlignCenter)
        olay.setContentsMargins(30, 40, 30, 40)
        olay.setSpacing(18)

        # Logo
        self.logo_label = QLabel()
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            self.logo_label.setPixmap(pm.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🛒")
            self.logo_label.setStyleSheet("font-size:72px; color:%s;" % ACCENT_GOLD)
        self.logo_label.setAlignment(Qt.AlignCenter)
        olay.addWidget(self.logo_label)

        # Gold decorative line
        line_top = QFrame()
        line_top.setFixedHeight(2)
        line_top.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 transparent, stop:0.2 %s, stop:0.8 %s, stop:1 transparent);" % (ACCENT_GOLD, ACCENT_GOLD)
        )
        olay.addWidget(line_top)

        # App name
        name_lbl = QLabel(self.i18n.get_message("app_name_short"))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            "color: %s; font-family: 'Cairo'; font-size: 26px; font-weight: 800; background: transparent;"
            % ACCENT_GOLD
        )
        olay.addWidget(name_lbl)

        # Tagline
        tagline = QLabel("نظام إدارة الأعمال المتكامل")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            "color: %s; font-family: 'Cairo'; font-size: 13px; font-weight: 500; background: transparent;"
            % TEXT_SECONDARY
        )
        olay.addWidget(tagline)

        # Bottom decorative line
        line_bot = QFrame()
        line_bot.setFixedHeight(2)
        line_bot.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 transparent, stop:0.3 %s, stop:0.7 %s, stop:1 transparent);" % (ACCENT_GOLD_LIGHT, ACCENT_GOLD_LIGHT)
        )
        olay.addWidget(line_bot)

        # Overlay resize tracking
        def _resize_overlay(event):
            overlay.setGeometry(left.rect())

        left.resizeEvent = _resize_overlay

        # Left panel stylesheet
        left.setStyleSheet(
            """
            QFrame#RoyalLeftPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 %s, stop:1 %s);
                border-top-right-radius: 16px;
                border-bottom-right-radius: 16px;
            }
            """
            % (BG_PRIMARY, BG_TERTIARY)
        )

        master.addWidget(left, stretch=4)

        # ── RIGHT PANEL (60%) ───────────────────────────────────────────
        right = QFrame()
        right.setObjectName("RoyalRightPanel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(48, 40, 48, 28)
        right_lay.setSpacing(6)
        right_lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Spacer to push form down a bit
        right_lay.addSpacing(16)

        # Welcome heading
        welcome = QLabel("مرحباً بعودتك")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(
            "color: %s; font-family: 'Cairo'; font-size: 26px; font-weight: 800; background: transparent;"
            % TEXT_PRIMARY
        )
        right_lay.addWidget(welcome)

        # Subtitle
        sub = QLabel("سجّل دخولك للمتابعة")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            "color: %s; font-family: 'Cairo'; font-size: 14px; font-weight: 400; background: transparent; margin-bottom: 24px;"
            % TEXT_SECONDARY
        )
        right_lay.addWidget(sub)

        right_lay.addSpacing(12)

        # ── Username field ──────────────────────────────────────────────
        self._build_username_field(right_lay)

        # ── Password field ──────────────────────────────────────────────
        self._build_password_field(right_lay)

        # ── Remember me ─────────────────────────────────────────────────
        self._build_remember_me(right_lay)

        right_lay.addSpacing(6)

        # ── Warning label (inserted here for layout) ────────────────────
        self.warning_label.setStyleSheet(
            """
            QLabel {
                color: #ef4444;
                background-color: rgba(239,68,68,0.1);
                border: 1px solid rgba(239,68,68,0.25);
                border-radius: 8px;
                padding: 10px 14px;
                font-family: 'Cairo';
                font-size: 13px;
                font-weight: 600;
            }
            """
        )
        right_lay.addWidget(self.warning_label)

        # ── Login button ────────────────────────────────────────────────
        self._build_login_button(right_lay)

        # ── Forgot password link ────────────────────────────────────────
        self.forgot_password_button = QPushButton("نسيت كلمة المرور؟")
        self.forgot_password_button.setCursor(Qt.PointingHandCursor)
        self.forgot_password_button.setStyleSheet(
            """
            QPushButton {
                border: none;
                color: %s;
                font-family: 'Cairo';
                font-size: 13px;
                background: transparent;
                padding: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: %s;
                text-decoration: underline;
            }
            """
            % (ACCENT_GOLD, ACCENT_GOLD_LIGHT)
        )
        right_lay.addWidget(self.forgot_password_button, alignment=Qt.AlignCenter)

        # Spacer to push version to bottom
        right_lay.addStretch()

        # Version info
        ver = QLabel(self.i18n.get_message("app_version_copyright"))
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(
            "color: %s; font-family: 'Cairo'; font-size: 10px; font-weight: 500; background: transparent;"
            % TEXT_MUTED
        )
        right_lay.addWidget(ver)

        # Progress bar (thin, gold, hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: %s;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 %s, stop:1 %s);
                border-radius: 10px;
            }
            """
            % (BG_TERTIARY, ACCENT_GOLD, ACCENT_GOLD_LIGHT)
        )
        right_lay.addWidget(self.progress_bar)

        # Right panel style
        right.setStyleSheet(
            """
            QFrame#RoyalRightPanel {
                background-color: %s;
                border-top-left-radius: 16px;
                border-bottom-left-radius: 16px;
            }
            """
            % BG_SECONDARY
        )

        master.addWidget(right, stretch=6)

    # ── Field builders ──────────────────────────────────────────────────
    def _build_username_field(self, parent_layout: QVBoxLayout):
        """Username field with gold focus ring and user icon."""
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("اسم المستخدم")
        self.username_edit.setMinimumHeight(50)
        self.username_edit.setTextMargins(44, 0, 16, 0)
        self.username_edit.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid %s;
                border-radius: 10px;
                padding: 0 16px 0 44px;
                font-family: 'Cairo';
                font-size: 14px;
                background-color: %s;
                color: %s;
                selection-background-color: %s;
                selection-color: %s;
            }
            QLineEdit:hover {
                border-color: %s;
            }
            QLineEdit:focus {
                border-color: %s;
                background-color: %s;
            }
            """
            % (BORDER_DEFAULT, BG_TERTIARY, TEXT_PRIMARY, ACCENT_GOLD, BG_PRIMARY, TEXT_MUTED, BORDER_FOCUS, BG_PRIMARY)
        )

        # Wrap in a container to overlay the icon
        container = QFrame()
        container.setStyleSheet("background:transparent; border:none;")
        cont_lay = QHBoxLayout(container)
        cont_lay.setContentsMargins(0, 0, 0, 0)
        cont_lay.setSpacing(0)

        # User icon (overlaid via absolute positioning)
        icon = QLabel("👤")
        icon.setFixedWidth(44)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            "color: %s; font-size: 18px; background: transparent; border: none;" % TEXT_MUTED
        )

        # Use a stacked-like approach: icon on left, field fills rest
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        icon_container = QFrame()
        icon_container.setFixedWidth(50)
        icon_container.setStyleSheet("background:transparent; border:none;")
        ic_lay = QVBoxLayout(icon_container)
        ic_lay.setAlignment(Qt.AlignCenter)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        ic_lay.addWidget(icon)
        row.addWidget(icon_container)
        row.addWidget(self.username_edit)
        parent_layout.addLayout(row)

    def _build_password_field(self, parent_layout: QVBoxLayout):
        """Password field with gold focus ring, lock icon, show/hide toggle."""
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("كلمة المرور")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(50)
        self.password_edit.setStyleSheet(
            """
            QLineEdit {
                border: 2px solid %s;
                border-radius: 10px;
                padding: 0 50px 0 44px;
                font-family: 'Cairo';
                font-size: 14px;
                background-color: %s;
                color: %s;
                selection-background-color: %s;
                selection-color: %s;
            }
            QLineEdit:hover {
                border-color: %s;
            }
            QLineEdit:focus {
                border-color: %s;
                background-color: %s;
            }
            """
            % (BORDER_DEFAULT, BG_TERTIARY, TEXT_PRIMARY, ACCENT_GOLD, BG_PRIMARY, TEXT_MUTED, BORDER_FOCUS, BG_PRIMARY)
        )

        # Show/hide toggle button
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(44, 44)
        self.show_password_btn.setCursor(Qt.PointingHandCursor)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setToolTip("إظهار/إخفاء كلمة المرور")
        self.show_password_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                color: %s;
                border: none;
                font-size: 18px;
                border-radius: 8px;
            }
            QPushButton:hover {
                color: %s;
                background: %s;
            }
            """
            % (TEXT_MUTED, ACCENT_GOLD, GOLD_SUBTLE)
        )
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)

        # Lock icon
        lock_icon = QLabel("🔒")
        lock_icon.setFixedWidth(44)
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet(
            "color: %s; font-size: 18px; background: transparent; border: none;" % TEXT_MUTED
        )
        lock_container = QFrame()
        lock_container.setFixedWidth(50)
        lock_container.setStyleSheet("background:transparent; border:none;")
        lc_lay = QVBoxLayout(lock_container)
        lc_lay.setAlignment(Qt.AlignCenter)
        lc_lay.setContentsMargins(0, 0, 0, 0)
        lc_lay.addWidget(lock_icon)

        # Build row: [lock icon] [field] [eye button]
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(lock_container)
        row.addWidget(self.password_edit)
        row.addWidget(self.show_password_btn)

        # Wrap in a frame so the border looks unified
        wrapper = QFrame()
        wrapper.setStyleSheet("background:transparent; border:none;")
        w_lay = QVBoxLayout(wrapper)
        w_lay.setContentsMargins(0, 0, 0, 0)
        w_lay.addLayout(row)
        parent_layout.addWidget(wrapper)

    def _build_remember_me(self, parent_layout: QVBoxLayout):
        """Remember-me checkbox with gold accent."""
        self.remember_checkbox = QCheckBox("تذكرني")
        self.remember_checkbox.setStyleSheet(
            """
            QCheckBox {
                color: %s;
                font-family: 'Cairo';
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid %s;
                border-radius: 6px;
                background-color: %s;
            }
            QCheckBox::indicator:hover {
                border-color: %s;
            }
            QCheckBox::indicator:checked {
                background-color: %s;
                border-color: %s;
            }
            """
            % (TEXT_SECONDARY, BORDER_DEFAULT, BG_TERTIARY, ACCENT_GOLD, ACCENT_GOLD, ACCENT_GOLD)
        )
        parent_layout.addWidget(self.remember_checkbox, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    def _build_login_button(self, parent_layout: QVBoxLayout):
        """Large gold gradient login button."""
        self.login_button = QPushButton(self.i18n.get_message("login_button", default="تسجيل الدخول"))
        self.login_button.setMinimumHeight(52)
        self.login_button.setDefault(True)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 %s, stop:1 %s);
                color: %s;
                border: none;
                border-radius: 12px;
                font-family: 'Cairo';
                font-size: 16px;
                font-weight: 700;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 %s, stop:1 #f0d98a);
            }
            QPushButton:pressed {
                background: %s;
            }
            QPushButton:disabled {
                background-color: %s;
                color: %s;
            }
            """
            % (
                ACCENT_GOLD,
                ACCENT_GOLD_LIGHT,
                BG_PRIMARY,
                ACCENT_GOLD_LIGHT,
                ACCENT_GOLD,
                BG_TERTIARY,
                TEXT_MUTED,
            )
        )
        parent_layout.addWidget(self.login_button)

    # ── Connections ─────────────────────────────────────────────────────
    def setup_connections(self):
        self.login_button.clicked.connect(self.handle_login)
        self.forgot_password_button.clicked.connect(self.handle_forgot_password)
        self.username_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)

    # ── Events ──────────────────────────────────────────────────────────
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        QTimer.singleShot(0, self._fix_layout_on_show)
        QTimer.singleShot(50, lambda: self.animation_manager.fade_in(self, duration=300))

    def toggle_password_visibility(self, checked: bool):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🔒")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁")

    # ── Layout helpers ──────────────────────────────────────────────────
    def _fix_layout_on_show(self):
        try:
            self.updateGeometry()
            if self.layout():
                self.layout().update()
            for w in self.findChildren(QWidget):
                w.updateGeometry()
                w.update()
            self.repaint()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def _fix_layout(self):
        try:
            self.updateGeometry()
            self.update()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def _ensure_proper_display(self):
        try:
            self.updateGeometry()
            self.repaint()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    # ── Login logic ─────────────────────────────────────────────────────
    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username:
            self.show_error("يرجى إدخال اسم المستخدم")
            self.username_edit.setFocus()
            return

        if not password:
            self.show_error("يرجى إدخال كلمة المرور")
            self.password_edit.setFocus()
            return

        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

        try:
            success, session, message = self.user_service.authenticate_user(
                username,
                password,
                ip_address="127.0.0.1",
                user_agent="Standard El Joumla Desktop App",
            )
            self.on_login_completed(success, session, message or "")
        except Exception as e:
            self.on_login_completed(False, None, f"خطأ في النظام: {str(e)}")

    def on_login_completed(self, success: bool, session: Optional[UserSession], message: str):
        self.progress_bar.setVisible(False)
        QApplication.processEvents()

        if success and session:
            self.set_ui_enabled(False)
            self.current_session = session

            # 2FA check
            try:
                needs_2fa = False
                rows = self.user_service.db.execute_query(
                    "SELECT 1 FROM user_2fa WHERE user_id = ?", (session.user_id,)
                )
                needs_2fa = bool(rows)
            except Exception:
                needs_2fa = False

            if needs_2fa:
                from PySide6.QtWidgets import QInputDialog

                code, ok = QInputDialog.getText(
                    self,
                    self.i18n.get_message("two_factor_title", default="التحقق بخطوتين"),
                    self.i18n.get_message("two_factor_prompt", default="أدخل رمز التحقق (TOTP):"),
                )
                if not ok or not code:
                    try:
                        self.user_service._terminate_session(session.session_id, "إلغاء التحقق الثنائي")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")
                    self.show_error("تم إلغاء التحقق الثنائي")
                    return

                if not self.security_service.verify_2fa(session.user_id, code):
                    try:
                        self.security_service.record_login_attempt(
                            session.username,
                            False,
                            session.ip_address,
                            session.user_agent,
                        )
                        self.user_service._terminate_session(session.session_id, "فشل التحقق الثنائي")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")
                    self.show_error("رمز التحقق غير صحيح")
                    return

            if self.remember_checkbox.isChecked():
                QTimer.singleShot(0, self.save_credentials)

            self.current_session = session
            self.login_successful.emit(session)
            QTimer.singleShot(50, self.accept)
        else:
            self.set_ui_enabled(True)
            self.show_error(message or "فشل في تسجيل الدخول")
            self.password_edit.clear()
            QTimer.singleShot(100, lambda: self.password_edit.setFocus())

    def handle_forgot_password(self):
        dialog = ForgotPasswordDialog(self.user_service, self)
        dialog.exec()

    # ── UI state helpers ────────────────────────────────────────────────
    def set_ui_enabled(self, enabled: bool):
        self.username_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
        self.show_password_btn.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        self.forgot_password_button.setEnabled(enabled)

    def show_error(self, message: str):
        self.notify.show_error(self.i18n.get_message("error"), message)

    def show_info(self, message: str):
        self.notify.show_info(self.i18n.get_message("info"), message)

    # ── Credential persistence ──────────────────────────────────────────
    def save_credentials(self):
        try:
            import json
            import os

            config_dir = os.path.join(os.path.expanduser("~"), ".standard_eljoumla")
            os.makedirs(config_dir, exist_ok=True)

            config_file = os.path.join(config_dir, "login_config.json")
            config = {
                "last_username": self.username_edit.text(),
                "remember_username": True,
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def load_saved_credentials(self):
        try:
            import json
            import os

            config_file = os.path.join(os.path.expanduser("~"), ".standard_eljoumla", "login_config.json")

            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if config.get("remember_username") and config.get("last_username"):
                    self.username_edit.setText(config["last_username"])
                    self.remember_checkbox.setChecked(True)
                    self.password_edit.setFocus()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    # ── Public API ──────────────────────────────────────────────────────
    def get_current_session(self) -> Optional[UserSession]:
        return self.current_session

    def set_warning_message(self, message: str):
        self.warning_label.setText(message)
        self.warning_label.setVisible(True)

    def hide_warning_message(self):
        self.warning_label.setVisible(False)

    # ── Close with fade-out ─────────────────────────────────────────────
    def closeEvent(self, event):
        if getattr(self, "_is_closing", False):
            event.accept()
            return

        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()

        if hasattr(self, "animation_manager"):
            event.ignore()
            self._is_closing = True
            self.animation_manager.fade_out(self, duration=200)
            QTimer.singleShot(250, self._finalize_close)
        else:
            event.accept()

    def _finalize_close(self):
        self.close()


# ── Standalone test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    font = QFont("Cairo", 10)
    app.setFont(font)
    app.setLayoutDirection(Qt.RightToLeft)

    from ...core.database_manager import DatabaseManager

    db = DatabaseManager(":memory:")

    dialog = LoginDialog(db)

    if dialog.exec() == QDialog.Accepted:
        session = dialog.get_current_session()
        pass  # Login successful
    else:
        pass  # Login cancelled

    sys.exit()