#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Effects
التأثيرات البصرية - gradients, glows, shadows, aurora, shimmer, elevation, particles

Color Palette:
    GOLD=#C8A54E, GOLD_LIGHT=#E8C96A, TEAL=#2DD4BF, CORAL=#EF6B6B,
    AMBER=#F59E0B, SKY=#38BDF8
    BG_VOID=#06070B, BG_DEEP=#0C0E16, BG_PRIMARY=#111520,
    BG_SURFACE=#181D2E, BG_RAISED=#202640
"""

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)


# ── Color Palette Constants ──────────────────────────────────────────────────
GOLD = QColor("#C8A54E")
GOLD_LIGHT = QColor("#E8C96A")
TEAL = QColor("#2DD4BF")
CORAL = QColor("#EF6B6B")
AMBER = QColor("#F59E0B")
SKY = QColor("#38BDF8")

BG_VOID = QColor("#06070B")
BG_DEEP = QColor("#0C0E16")
BG_PRIMARY = QColor("#111520")
BG_SURFACE = QColor("#181D2E")
BG_RAISED = QColor("#202640")


class VisualEffects:
    """التأثيرات البصرية"""

    # ── Existing Methods (preserved) ──────────────────────────────────────

    @staticmethod
    def draw_gradient_background(
        painter: QPainter,
        rect: QRect,
        start_color: QColor,
        end_color: QColor,
        direction: str = "horizontal",
    ):
        """
        رسم خلفية متدرجة

        Args:
            painter: QPainter
            rect: المنطقة المراد رسمها
            start_color: لون البداية
            end_color: لون النهاية
            direction: الاتجاه (horizontal, vertical, diagonal)
        """
        if direction == "horizontal":
            gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        elif direction == "vertical":
            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        else:  # diagonal
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())

        gradient.setColorAt(0.0, start_color)
        gradient.setColorAt(1.0, end_color)

        painter.fillRect(rect, QBrush(gradient))

    @staticmethod
    def draw_glow_effect(
        painter: QPainter,
        rect: QRect,
        color: QColor,
        intensity: int = 15,
        blur_radius: int = 30,
    ):
        """
        رسم تأثير glow — 15-layer soft falloff for smoother result.

        Args:
            painter: QPainter
            rect: المنطقة
            color: اللون
            intensity: شدة التأثير (عدد الطبقات، الافتراضي 15)
            blur_radius: نصف قطر التمويه (الافتراضي 30)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 15-layer soft glow with exponential falloff
        for i in range(intensity):
            # Softer exponential falloff curve
            progress = i / max(intensity - 1, 1)
            alpha = int(255 * ((1.0 - progress) ** 2.0) * 0.25)
            if alpha <= 0:
                continue
            glow_color = QColor(color)
            glow_color.setAlpha(min(alpha, 255))

            pen = QPen(glow_color, max(blur_radius - i * 2, 1))
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(i, i, -i, -i), 12, 12
            )

    @staticmethod
    def draw_shadow_effect(
        painter: QPainter,
        rect: QRect,
        offset: QPoint = QPoint(4, 6),
        blur: int = 12,
        color: QColor = QColor(6, 7, 11, 120),
    ):
        """
        رسم تأثير shadow

        Args:
            painter: QPainter
            rect: المنطقة
            offset: الإزاحة
            blur: التمويه
            color: لون الظل (default uses BG_VOID tinted)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        shadow_rect = rect.translated(offset)

        for i in range(blur):
            alpha = int(color.alpha() * (1.0 - i / blur) ** 1.5)
            shadow_color = QColor(color)
            shadow_color.setAlpha(max(alpha, 0))
            painter.fillRect(shadow_rect.adjusted(i, i, -i, -i), shadow_color)

    @staticmethod
    def draw_glass_effect(
        painter: QPainter,
        rect: QRect,
        opacity: float = 0.08,
        blur: bool = True,
    ):
        """
        رسم تأثير glass (زجاجي) — tinted for dark theme.

        Args:
            painter: QPainter
            rect: المنطقة
            opacity: الشفافية
            blur: تفعيل التمويه
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # خلفية شفافة مع تلميح من BG_SURFACE
        glass_color = QColor(24, 29, 46, int(255 * opacity))
        painter.fillRect(rect, glass_color)

        # حد فاتح خفيف مع تلميح ذهبي
        pen = QPen(QColor(200, 165, 78, int(255 * opacity * 1.5)))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)

    @staticmethod
    def draw_neon_effect(
        painter: QPainter,
        rect: QRect,
        color: QColor,
        intensity: int = 8,
    ):
        """
        رسم تأثير neon — 8-layer smoother gradient neon glow.

        Args:
            painter: QPainter
            rect: المنطقة
            color: اللون
            intensity: شدة التأثير (عدد الطبقات، الافتراضي 8)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for i in range(intensity):
            progress = i / max(intensity - 1, 1)
            # Smoother falloff: quadratic curve
            alpha = int(255 * ((1.0 - progress) ** 1.8) * 0.9)
            neon_color = QColor(color)
            neon_color.setAlpha(min(max(alpha, 0), 255))

            pen_width = max(3.5 - i * 0.4, 0.5)
            pen = QPen(neon_color, pen_width)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                rect.adjusted(i, i, -i, -i), 12, 12
            )

    @staticmethod
    def draw_gradient_border(
        painter: QPainter,
        rect: QRect,
        start_color: QColor,
        end_color: QColor,
        width: int = 2,
    ):
        """
        رسم حد متدرج

        Args:
            painter: QPainter
            rect: المنطقة
            start_color: لون البداية
            end_color: لون النهاية
            width: عرض الحد
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, start_color)
        gradient.setColorAt(1.0, end_color)

        pen = QPen(QBrush(gradient), width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)

    # ── NEW Methods ──────────────────────────────────────────────────────

    @staticmethod
    def draw_aurora_glow(
        painter: QPainter,
        rect: QRect,
        color: QColor = GOLD,
    ):
        """
        Multi-layered soft aurora glow with 3 concentric layers fading out.
        Uses alpha 0.08, 0.05, 0.02 for a subtle atmospheric effect.

        Args:
            painter: QPainter
            rect: المنطقة المراد تطبيق التوهج عليها
            color: اللون الأساسي (الافتراضي ذهبي)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        alphas = [0.08, 0.05, 0.02]
        expansions = [0, 12, 28]  # pixels to expand outward per layer

        for layer_idx, (alpha_val, expand) in enumerate(zip(alphas, expansions)):
            layer_rect = rect.adjusted(-expand, -expand, expand, expand)

            # Use radial gradient centered on rect for soft natural falloff
            center_x = layer_rect.center().x()
            center_y = layer_rect.center().y()
            outer_radius = max(layer_rect.width(), layer_rect.height()) / 2.0

            radial = QRadialGradient(center_x, center_y, outer_radius)
            alpha_int = int(255 * alpha_val)
            core_color = QColor(color)
            core_color.setAlpha(alpha_int)
            edge_color = QColor(color)
            edge_color.setAlpha(0)

            radial.setColorAt(0.0, core_color)
            radial.setColorAt(
                0.6,
                QColor(color.red(), color.green(), color.blue(), alpha_int // 2),
            )
            radial.setColorAt(1.0, edge_color)

            painter.fillRect(layer_rect, QBrush(radial))

    @staticmethod
    def draw_shimmer_line(
        painter: QPainter,
        start_point: QPoint,
        end_point: QPoint,
        color: QColor = GOLD,
        width: int = 1,
    ):
        """
        A thin gradient line that fades from transparent to color to transparent.
        Creates an elegant shimmer accent line.

        Args:
            painter: QPainter
            start_point: نقطة البداية
            end_point: نقطة النهاية
            color: اللون (الافتراضي ذهبي)
            width: عرض الخط
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        gradient = QLinearGradient(start_point, end_point)

        # transparent -> color -> transparent
        transparent = QColor(color)
        transparent.setAlpha(0)
        solid = QColor(color)
        solid.setAlpha(220)

        gradient.setColorAt(0.0, transparent)
        gradient.setColorAt(0.2, QColor(color.red(), color.green(), color.blue(), 60))
        gradient.setColorAt(0.5, solid)
        gradient.setColorAt(0.8, QColor(color.red(), color.green(), color.blue(), 60))
        gradient.setColorAt(1.0, transparent)

        pen = QPen(QBrush(gradient), width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(start_point, end_point)

    @staticmethod
    def draw_card_elevation(
        painter: QPainter,
        rect: QRect,
        elevation: int = 1,
        accent_color: QColor = GOLD,
    ):
        """
        Card shadow system with 4 elevation levels (sm/md/lg/xl),
        each adding more shadow layers plus subtle gold-tinted edge.

        Elevation levels:
            0 = sm: 2 shadow layers, subtle
            1 = md: 4 shadow layers, standard (default)
            2 = lg: 7 shadow layers, prominent
            3 = xl: 10 shadow layers, dramatic

        Args:
            painter: QPainter
            rect: المنطقة
            elevation: مستوى الارتفاع (0-3)
            accent_color: لون الحافة التمييزية
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        elevation_config = {
            0: {  # sm
                "shadow_layers": 2,
                "offset": QPoint(1, 2),
                "blur": 4,
                "edge_alpha": 15,
            },
            1: {  # md
                "shadow_layers": 4,
                "offset": QPoint(2, 4),
                "blur": 8,
                "edge_alpha": 25,
            },
            2: {  # lg
                "shadow_layers": 7,
                "offset": QPoint(4, 8),
                "blur": 14,
                "edge_alpha": 35,
            },
            3: {  # xl
                "shadow_layers": 10,
                "offset": QPoint(6, 12),
                "blur": 20,
                "edge_alpha": 45,
            },
        }

        # Clamp elevation to valid range
        elevation = max(0, min(elevation, 3))
        config = elevation_config[elevation]

        # Draw shadow layers
        shadow_base = QColor(6, 7, 11)  # BG_VOID based
        for i in range(config["shadow_layers"]):
            progress = i / max(config["shadow_layers"] - 1, 1)
            alpha = int(80 * (1.0 - progress) ** 1.5)
            shadow_color = QColor(shadow_base)
            shadow_color.setAlpha(alpha)

            layer_offset = config["offset"] + QPoint(i, i)
            shadow_rect = rect.translated(layer_offset)
            painter.fillRect(
                shadow_rect.adjusted(i, i, -i, -i), shadow_color
            )

        # Subtle accent-tinted top edge (gold highlight)
        edge_color = QColor(accent_color)
        edge_color.setAlpha(config["edge_alpha"])
        edge_pen = QPen(edge_color, 1)
        edge_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(edge_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw only the top edge line for subtle highlight
        top_left = rect.topLeft()
        top_right = rect.topRight()
        painter.drawLine(top_left, top_right)

        # Optional: very subtle left edge at half alpha for depth
        edge_color.setAlpha(config["edge_alpha"] // 2)
        edge_pen.setColor(edge_color)
        painter.setPen(edge_pen)
        painter.drawLine(rect.topLeft(), rect.bottomLeft())

    @staticmethod
    def draw_particle_dot(
        painter: QPainter,
        center: QPoint,
        radius: float,
        color: QColor,
        alpha: int = 180,
    ):
        """
        A single glowing dot with outer glow ring.
        Creates a luminous particle effect.

        Args:
            painter: QPainter
            center: مركز النقطة
            radius: نصف القطر الأساسي
            color: اللون
            alpha: شفافية النقطة الأساسية (0-255)
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Outer glow ring
        glow_radius = radius * 3.0
        radial_glow = QRadialGradient(center.x(), center.y(), glow_radius)
        glow_color_outer = QColor(color)
        glow_color_outer.setAlpha(0)
        glow_color_mid = QColor(color)
        glow_color_mid.setAlpha(max(alpha // 6, 0))
        glow_color_inner = QColor(color)
        glow_color_inner.setAlpha(max(alpha // 3, 0))

        radial_glow.setColorAt(0.0, glow_color_inner)
        radial_glow.setColorAt(0.4, glow_color_mid)
        radial_glow.setColorAt(1.0, glow_color_outer)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(radial_glow))
        painter.drawEllipse(
            center,
            int(glow_radius),
            int(glow_radius),
        )

        # Core dot
        core_gradient = QRadialGradient(center.x(), center.y(), radius)
        core_bright = QColor(255, 255, 255, min(alpha + 40, 255))
        core_main = QColor(color)
        core_main.setAlpha(alpha)

        core_gradient.setColorAt(0.0, core_bright)
        core_gradient.setColorAt(0.5, core_main)
        core_edge = QColor(color)
        core_edge.setAlpha(max(alpha // 2, 0))
        core_gradient.setColorAt(1.0, core_edge)

        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(center, int(radius), int(radius))

    @staticmethod
    def draw_aurora_border(
        painter: QPainter,
        rect: QRect,
        color: QColor = GOLD,
        opacity: int = 60,
        width: int = 1,
    ):
        """
        Draw a subtle animated aurora gradient border around a widget's edges.
        The border glows brighter at the top and fades toward the bottom,
        creating an aurora-like atmospheric frame.

        Args:
            painter: QPainter
            rect: المنطقة
            color: اللون (الافتراضي ذهبي)
            opacity: شفافية الحد (0-255)
            width: عرض الحد
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Top edge — brightest (aurora peak)
        top_gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        bright = QColor(color)
        bright.setAlpha(opacity)
        mid = QColor(color)
        mid.setAlpha(opacity // 3)
        dim = QColor(color)
        dim.setAlpha(0)
        top_gradient.setColorAt(0.0, dim)
        top_gradient.setColorAt(0.3, mid)
        top_gradient.setColorAt(0.5, bright)
        top_gradient.setColorAt(0.7, mid)
        top_gradient.setColorAt(1.0, dim)

        pen = QPen(QBrush(top_gradient), width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(rect.topLeft(), rect.topRight())

        # Side edges — medium glow
        side_alpha = opacity // 2
        left_gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        left_top = QColor(color)
        left_top.setAlpha(side_alpha)
        left_bot = QColor(color)
        left_bot.setAlpha(0)
        left_gradient.setColorAt(0.0, left_top)
        left_gradient.setColorAt(1.0, left_bot)

        pen = QPen(QBrush(left_gradient), width)
        painter.setPen(pen)
        painter.drawLine(rect.topLeft(), rect.bottomLeft())

        right_gradient = QLinearGradient(rect.topRight(), rect.bottomRight())
        right_gradient.setColorAt(0.0, left_top)
        right_gradient.setColorAt(1.0, left_bot)
        pen = QPen(QBrush(right_gradient), width)
        painter.setPen(pen)
        painter.drawLine(rect.topRight(), rect.bottomRight())

        # Bottom edge — faintest
        bot_alpha = opacity // 5
        bot_color = QColor(color)
        bot_color.setAlpha(bot_alpha)
        pen = QPen(bot_color, width)
        painter.setPen(pen)
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

    @staticmethod
    def draw_gold_shimmer_line(
        painter: QPainter,
        rect: QRect,
        progress: float,
        color: QColor = GOLD,
        line_y_offset: int = 0,
    ):
        """
        Draw a horizontal shimmer line that sweeps across a widget.
        The shimmer position is controlled by `progress` (0.0 to 1.0).

        Args:
            painter: QPainter
            rect: المنطقة
            progress: موضع الشيمر (0.0 = يسار, 1.0 = يمين)
            color: اللون (الافتراضي ذهبي)
            line_y_offset: إزاحة رأسية للخط من منتصف المستطيل
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Calculate shimmer position
        center_y = rect.center().y() + line_y_offset
        shimmer_x = int(rect.left() + rect.width() * progress)
        shimmer_width = rect.width() // 4  # shimmer spans 1/4 of widget width

        start_x = max(rect.left(), shimmer_x - shimmer_width // 2)
        end_x = min(rect.right(), shimmer_x + shimmer_width // 2)

        if start_x >= end_x:
            return

        # Shimmer gradient: transparent -> color -> transparent
        gradient = QLinearGradient(start_x, 0, end_x, 0)
        transparent = QColor(color)
        transparent.setAlpha(0)
        bright = QColor(color)
        bright.setAlpha(120)

        gradient.setColorAt(0.0, transparent)
        gradient.setColorAt(0.4, QColor(color.red(), color.green(), color.blue(), 40))
        gradient.setColorAt(0.5, bright)
        gradient.setColorAt(0.6, QColor(color.red(), color.green(), color.blue(), 40))
        gradient.setColorAt(1.0, transparent)

        pen = QPen(QBrush(gradient), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(start_x, center_y, end_x, center_y)