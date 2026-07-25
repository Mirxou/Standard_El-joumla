#!/usr/bin/env python3
"""
نافذة تسجيل الدخول - Login Dialog — "Aurora Gate" Design
واجهة تسجيل دخول استثنائية بتصميم Aurora Noir — Gold + Deep Void
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
    QRadialGradient,
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
from ...ui.styles.design_tokens import C


# ═══════════════════════════════════════════════════════════════════════════
#  Rose Particle Canvas — animated geometric network background
# ═══════════════════════════════════════════════════════════════════════════
class _RoseParticleCanvas(QWidget):
    """Animated gold geometric particles with network connections and shimmer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._particles: list[dict] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(50)  # 20 FPS
        self._opacity = 0.0
        self._time = 0.0

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
        for _ in range(60):
            self._particles.append(
                {
                    "x": random.uniform(0, w),
                    "y": random.uniform(0, h),
                    "r": random.uniform(0.8, 2.8),
                    "vx": random.uniform(-0.25, 0.25),
                    "vy": random.uniform(-0.4, -0.05),
                    "alpha": random.uniform(0.12, 0.5),
                    "phase": random.uniform(0, math.pi * 2),
                    "shimmer_phase": random.uniform(0, math.pi * 2),
                }
            )

    def _tick(self):
        if self._opacity < 1.0:
            self._opacity = min(1.0, self._opacity + 0.035)
        self._time += 0.02
        w = max(self.width(), 200)
        h = max(self.height(), 400)
        for p in self._particles:
            # Gentle oscillation
            p["x"] += p["vx"] + math.sin(self._time + p["phase"]) * 0.15
            p["y"] += p["vy"]
            # Shimmer pulse
            p["shimmer_phase"] += 0.03
            # Wrap around
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

        # Draw network connections first
        pen = QPen(QColor(C.ACCENT_GOLD))
        pen.setWidthF(0.5)
        for i in range(len(self._particles)):
            for j in range(i + 1, len(self._particles)):
                dx = self._particles[i]["x"] - self._particles[j]["x"]
                dy = self._particles[i]["y"] - self._particles[j]["y"]
                dist = math.hypot(dx, dy)
                if dist < 100:
                    alpha = 0.10 * (1 - dist / 100)
                    c = QColor(C.ACCENT_GOLD)
                    c.setAlphaF(alpha)
                    pen.setColor(c)
                    painter.setPen(pen)
                    painter.drawLine(
                        int(self._particles[i]["x"]),
                        int(self._particles[i]["y"]),
                        int(self._particles[j]["x"]),
                        int(self._particles[j]["y"]),
                    )

        # Draw particles
        for p in self._particles:
            # Shimmer brightness modulation
            shimmer = 0.5 + 0.5 * math.sin(p["shimmer_phase"])
            effective_alpha = p["alpha"] * (0.7 + 0.3 * shimmer)

            # Outer glow
            glow_color = QColor(C.ACCENT_GOLD)
            glow_color.setAlphaF(effective_alpha * 0.35)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(
                QRectF(p["x"] - p["r"] * 2.5, p["y"] - p["r"] * 2.5, p["r"] * 5, p["r"] * 5)
            )
            # Core — brighter with shimmer
            if shimmer > 0.7:
                c = QColor(C.ACCENT_GOLD_LIGHT)
            else:
                c = QColor(C.ACCENT_GOLD)
            c.setAlphaF(effective_alpha)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(
                QRectF(p["x"] - p["r"], p["y"] - p["r"], p["r"] * 2, p["r"] * 2)
            )

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
#  LoginWorker — runs authentication in a background thread
# ═══════════════════════════════════════════════════════════════════════════
class LoginWorker(QThread):
    """عامل تسجيل الدخول في خيط منفصل"""

    login_completed = Signal(bool, object, str)

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
#  LoginDialog — "Aurora Gate" premium login experience
# ═══════════════════════════════════════════════════════════════════════════
class LoginDialog(BaseDialog):
    """نافذة تسجيل الدخول — تصميم Aurora Gate الفاخر"""

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

        # ── Override BaseDialog chrome for the Aurora Gate ───────────────
        self._apply_obsidian_chrome()

        # Warning label
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
    def _apply_obsidian_chrome(self):
        """Override BaseDialog frame & title bar for the Aurora Gate look."""
        self.title_bar.setVisible(False)
        self.title_bar.setFixedHeight(0)
        self.title_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._internal_layout.setContentsMargins(0, 0, 0, 0)
        self._internal_layout.setSpacing(0)

        # Restyle main_frame — Deep void with gold glow
        self.main_frame.setStyleSheet(
            f"""
            QFrame#MainFrame {{
                background-color: {C.BG_PRIMARY};
                border: 1px solid {C.BORDER_DEFAULT};
                border-radius: 20px;
                color: {C.TEXT_PRIMARY};
            }}
            """
        )

        # Gold shadow
        shadow = self.main_frame.graphicsEffect()
        if isinstance(shadow, QGraphicsDropShadowEffect):
            shadow.setColor(QColor(C.ACCENT_GOLD))
            shadow.setOffset(0, 8)
            shadow.setBlurRadius(60)

        # Content widget — full bleed
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_widget.setMinimumSize(820, 540)

    # ── UI Construction ─────────────────────────────────────────────────
    def setup_ui(self):
        self.setWindowTitle(self.i18n.get_message("login_title"))
        self.setMinimumSize(820, 540)
        self.setModal(True)

        # Master horizontal split
        master = QHBoxLayout(self.content_widget)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        # ── LEFT PANEL (40%) — Brand showcase ──────────────────────────
        left = QFrame()
        left.setObjectName("ObsidianLeftPanel")
        left.setMinimumWidth(300)
        left.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # Particle canvas
        self._particle_canvas = _RoseParticleCanvas(left)
        left_lay.addWidget(self._particle_canvas)

        # Overlay content
        overlay = QWidget(left)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        overlay.setGeometry(left.rect())
        overlay.raise_()
        olay = QVBoxLayout(overlay)
        olay.setAlignment(Qt.AlignCenter)
        olay.setContentsMargins(32, 48, 32, 48)
        olay.setSpacing(20)

        # Logo
        self.logo_label = QLabel()
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            pm = QPixmap(str(logo_path))
            self.logo_label.setPixmap(pm.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🛒")
            self.logo_label.setStyleSheet(f"font-size:68px; color:{C.ACCENT_GOLD};")
        self.logo_label.setAlignment(Qt.AlignCenter)
        olay.addWidget(self.logo_label)

        # Decorative gold line (top)
        line_top = QFrame()
        line_top.setFixedHeight(1)
        line_top.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 transparent, stop:0.15 {C.ACCENT_GOLD}, stop:0.85 {C.ACCENT_GOLD}, stop:1 transparent);"
        )
        olay.addWidget(line_top)

        # App name — Gold
        name_lbl = QLabel(self.i18n.get_message("app_name_short"))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            f"color: {C.ACCENT_GOLD}; font-family: 'Cairo'; font-size: 28px; font-weight: 900; "
            f"background: transparent; letter-spacing: 0.5px;"
        )
        olay.addWidget(name_lbl)

        # Tagline
        tagline = QLabel("نظام إدارة الأعمال المتكامل")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(
            f"color: {C.TEXT_SECONDARY}; font-family: 'Cairo'; font-size: 13px; "
            f"font-weight: 400; background: transparent;"
        )
        olay.addWidget(tagline)

        # Decorative gold line (bottom)
        line_bot = QFrame()
        line_bot.setFixedHeight(1)
        line_bot.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 transparent, stop:0.25 {C.ACCENT_GOLD_LIGHT}, stop:0.75 {C.ACCENT_GOLD_LIGHT}, stop:1 transparent);"
        )
        olay.addWidget(line_bot)

        # Version badge
        version_badge = QLabel("v4.0 — Aurora Noir")
        version_badge.setAlignment(Qt.AlignCenter)
        version_badge.setStyleSheet(
            f"color: {C.TEXT_GHOST}; font-family: 'Cairo'; font-size: 10px; "
            f"font-weight: 500; background: transparent; margin-top: 4px;"
        )
        olay.addWidget(version_badge)

        # Overlay resize tracking
        def _resize_overlay(event):
            overlay.setGeometry(left.rect())
        left.resizeEvent = _resize_overlay

        # Left panel stylesheet — deep void gradient
        left.setStyleSheet(
            f"""
            QFrame#ObsidianLeftPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0.3, y2:1,
                    stop:0 {C.BG_PRIMARY}, stop:0.5 {C.BG_SURFACE}, stop:1 {C.BG_RAISED});
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
            }}
            """
        )

        master.addWidget(left, stretch=4)

        # ── RIGHT PANEL (60%) — Login form ─────────────────────────────
        right = QFrame()
        right.setObjectName("ObsidianRightPanel")
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(52, 44, 52, 32)
        right_lay.setSpacing(4)
        right_lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # Top spacer
        right_lay.addSpacing(12)

        # Welcome heading
        welcome = QLabel("مرحباً بعودتك")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(
            f"color: {C.TEXT_BRIGHT}; font-family: 'Cairo'; font-size: 28px; "
            f"font-weight: 900; background: transparent; letter-spacing: 0.3px;"
        )
        right_lay.addWidget(welcome)

        # Subtitle
        sub = QLabel("سجّل دخولك للمتابعة إلى لوحة التحكم")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(
            f"color: {C.TEXT_SECONDARY}; font-family: 'Cairo'; font-size: 14px; "
            f"font-weight: 400; background: transparent; margin-bottom: 28px;"
        )
        right_lay.addWidget(sub)

        right_lay.addSpacing(8)

        # ── Username field ──────────────────────────────────────────────
        self._build_username_field(right_lay)

        right_lay.addSpacing(4)

        # ── Password field ──────────────────────────────────────────────
        self._build_password_field(right_lay)

        # ── Remember me ─────────────────────────────────────────────────
        self._build_remember_me(right_lay)

        right_lay.addSpacing(4)

        # ── Warning label ───────────────────────────────────────────────
        self.warning_label.setStyleSheet(
            f"""
            QLabel {{
                color: {C.ACCENT_CORAL};
                background-color: rgba(239,107,107,0.08);
                border: 1px solid rgba(239,107,107,0.20);
                border-radius: 10px;
                padding: 10px 16px;
                font-family: 'Cairo';
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )
        right_lay.addWidget(self.warning_label)

        # ── Login button ────────────────────────────────────────────────
        self._build_login_button(right_lay)

        right_lay.addSpacing(4)

        # ── Forgot password link ────────────────────────────────────────
        self.forgot_password_button = QPushButton("نسيت كلمة المرور؟")
        self.forgot_password_button.setCursor(Qt.PointingHandCursor)
        self.forgot_password_button.setStyleSheet(
            f"""
            QPushButton {{
                border: none;
                color: {C.ACCENT_GOLD};
                font-family: 'Cairo';
                font-size: 13px;
                background: transparent;
                padding: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {C.ACCENT_GOLD_LIGHT};
                text-decoration: underline;
            }}
            """
        )
        right_lay.addWidget(self.forgot_password_button, alignment=Qt.AlignCenter)

        # Spacer
        right_lay.addStretch()

        # Version info
        ver = QLabel(self.i18n.get_message("app_version_copyright"))
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(
            f"color: {C.TEXT_GHOST}; font-family: 'Cairo'; font-size: 10px; "
            f"font-weight: 500; background: transparent;"
        )
        right_lay.addWidget(ver)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                border-radius: 10px;
                background-color: {C.BORDER_SUBTLE};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {C.ACCENT_GOLD}, stop:1 {C.ACCENT_GOLD_LIGHT});
                border-radius: 10px;
            }}
            """
        )
        right_lay.addWidget(self.progress_bar)

        # Right panel style
        right.setStyleSheet(
            f"""
            QFrame#ObsidianRightPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {C.BG_SURFACE}, stop:1 {C.BG_PRIMARY});
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }}
            """
        )

        master.addWidget(right, stretch=6)

    # ── Field builders ──────────────────────────────────────────────────
    def _build_username_field(self, parent_layout: QVBoxLayout):
        """Username field with gold focus ring and icon."""
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("اسم المستخدم")
        self.username_edit.setMinimumHeight(54)
        self.username_edit.setTextMargins(46, 0, 16, 0)
        self.username_edit.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1.5px solid {C.BORDER_DEFAULT};
                border-radius: 12px;
                padding: 0 16px 0 46px;
                font-family: 'Cairo';
                font-size: 14px;
                background-color: {C.BG_RAISED};
                color: {C.TEXT_PRIMARY};
                selection-background-color: {C.ACCENT_GOLD_SUBTLE};
                selection-color: {C.ACCENT_GOLD_LIGHT};
            }}
            QLineEdit:hover {{
                border-color: {C.BORDER_MEDIUM};
            }}
            QLineEdit:focus {{
                border-color: {C.ACCENT_GOLD};
                background-color: {C.BG_SURFACE};
            }}
            """
        )

        # User icon
        icon = QLabel("👤")
        icon.setFixedWidth(46)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(
            f"color: {C.TEXT_MUTED}; font-size: 17px; background: transparent; border: none;"
        )
        icon_container = QFrame()
        icon_container.setFixedWidth(52)
        icon_container.setStyleSheet("background:transparent; border:none;")
        ic_lay = QVBoxLayout(icon_container)
        ic_lay.setAlignment(Qt.AlignCenter)
        ic_lay.setContentsMargins(0, 0, 0, 0)
        ic_lay.addWidget(icon)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(icon_container)
        row.addWidget(self.username_edit)
        parent_layout.addLayout(row)

    def _build_password_field(self, parent_layout: QVBoxLayout):
        """Password field with gold focus ring, lock icon, show/hide toggle."""
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("كلمة المرور")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(54)
        self.password_edit.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1.5px solid {C.BORDER_DEFAULT};
                border-radius: 12px;
                padding: 0 50px 0 46px;
                font-family: 'Cairo';
                font-size: 14px;
                background-color: {C.BG_RAISED};
                color: {C.TEXT_PRIMARY};
                selection-background-color: {C.ACCENT_GOLD_SUBTLE};
                selection-color: {C.ACCENT_GOLD_LIGHT};
            }}
            QLineEdit:hover {{
                border-color: {C.BORDER_MEDIUM};
            }}
            QLineEdit:focus {{
                border-color: {C.ACCENT_GOLD};
                background-color: {C.BG_SURFACE};
            }}
            """
        )

        # Show/hide toggle button
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(46, 46)
        self.show_password_btn.setCursor(Qt.PointingHandCursor)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setToolTip("إظهار/إخفاء كلمة المرور")
        self.show_password_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {C.TEXT_MUTED};
                border: none;
                font-size: 17px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                color: {C.ACCENT_GOLD};
                background: {C.ACCENT_GOLD_SUBTLE};
            }}
            """
        )
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)

        # Lock icon
        lock_icon = QLabel("🔒")
        lock_icon.setFixedWidth(46)
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet(
            f"color: {C.TEXT_MUTED}; font-size: 17px; background: transparent; border: none;"
        )
        lock_container = QFrame()
        lock_container.setFixedWidth(52)
        lock_container.setStyleSheet("background:transparent; border:none;")
        lc_lay = QVBoxLayout(lock_container)
        lc_lay.setAlignment(Qt.AlignCenter)
        lc_lay.setContentsMargins(0, 0, 0, 0)
        lc_lay.addWidget(lock_icon)

        # Build row
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(lock_container)
        row.addWidget(self.password_edit)
        row.addWidget(self.show_password_btn)

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
            f"""
            QCheckBox {{
                color: {C.TEXT_SECONDARY};
                font-family: 'Cairo';
                font-size: 13px;
                spacing: 10px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {C.BORDER_DEFAULT};
                border-radius: 6px;
                background-color: {C.BG_RAISED};
            }}
            QCheckBox::indicator:hover {{
                border-color: {C.ACCENT_GOLD};
            }}
            QCheckBox::indicator:checked {{
                background-color: {C.ACCENT_GOLD};
                border-color: {C.ACCENT_GOLD};
            }}
            """
        )
        parent_layout.addWidget(self.remember_checkbox, alignment=Qt.AlignLeft | Qt.AlignVCenter)

    def _build_login_button(self, parent_layout: QVBoxLayout):
        """Large gold gradient login button with glow effect."""
        self.login_button = QPushButton(self.i18n.get_message("login_button", default="تسجيل الدخول"))
        self.login_button.setMinimumHeight(54)
        self.login_button.setDefault(True)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {C.ACCENT_GOLD}, stop:1 {C.ACCENT_GOLD_LIGHT});
                color: {C.BG_VOID};
                border: none;
                border-radius: 14px;
                font-family: 'Cairo';
                font-size: 16px;
                font-weight: 800;
                padding: 0 28px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {C.ACCENT_GOLD_LIGHT}, stop:1 {C.ACCENT_TEAL_LIGHT});
            }}
            QPushButton:pressed {{
                background: {C.ACCENT_GOLD_DARK};
            }}
            QPushButton:disabled {{
                background-color: {C.BG_RAISED};
                color: {C.TEXT_GHOST};
            }}
            """
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
        pass
    else:
        pass

    sys.exit()