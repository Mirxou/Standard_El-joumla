#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Animation Manager
مدير الحركات - نظام شامل للحركات والتأثيرات

Color Palette:
    GOLD=#C8A54E, GOLD_LIGHT=#E8C96A, TEAL=#2DD4BF, CORAL=#EF6B6B,
    AMBER=#F59E0B, SKY=#38BDF8
"""

from enum import Enum
from typing import Dict, List, Optional

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QPoint,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from src.utils.logger import setup_logger


class AnimationType(Enum):
    """أنواع الحركات"""

    FADE = "fade"
    SLIDE = "slide"
    FLOAT = "float"
    GRADIENT = "gradient"
    SCALE = "scale"
    ROTATE = "rotate"


class AnimationManager(QObject):
    """مدير الحركات"""

    animation_finished = Signal(str)  # animation_id

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = setup_logger(__name__)
        self.active_animations: Dict[str, QPropertyAnimation] = {}
        self.animation_groups: Dict[str, QParallelAnimationGroup | QSequentialAnimationGroup] = {}
        self._pulse_timers: Dict[str, QTimer] = {}

    # ── Existing Methods (preserved) ─────────────────────────────────────

    def fade_in(
        self,
        widget: QWidget,
        duration: int = 300,
        easing: QEasingCurve.Type = QEasingCurve.OutCubic,
    ) -> str:
        """
        حركة fade in

        Args:
            widget: الـ widget المراد تحريكه
            duration: مدة الحركة (ملي ثانية)
            easing: نوع التخفيف

        Returns:
            معرف الحركة
        """
        animation_id = f"fade_in_{id(widget)}"

        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()

        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(easing)
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.active_animations[animation_id] = animation
        animation.start()

        return animation_id

    def fade_out(
        self,
        widget: QWidget,
        duration: int = 300,
        easing: QEasingCurve.Type = QEasingCurve.InCubic,
    ) -> str:
        """
        حركة fade out

        Args:
            widget: الـ widget المراد تحريكه
            duration: مدة الحركة (ملي ثانية)
            easing: نوع التخفيف

        Returns:
            معرف الحركة
        """
        animation_id = f"fade_out_{id(widget)}"

        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()

        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(easing)
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.active_animations[animation_id] = animation
        animation.start()

        return animation_id

    def slide_in(
        self,
        widget: QWidget,
        direction: str = "right",
        duration: int = 300,
        easing: QEasingCurve.Type = QEasingCurve.OutCubic,
    ) -> str:
        """
        حركة slide in

        Args:
            widget: الـ widget المراد تحريكه
            direction: الاتجاه (right, left, up, down)
            duration: مدة الحركة (ملي ثانية)
            easing: نوع التخفيف

        Returns:
            معرف الحركة
        """
        animation_id = f"slide_in_{direction}_{id(widget)}"

        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()

        # حفظ الموضع الأصلي
        original_pos = widget.pos()

        # تحديد نقطة البداية حسب الاتجاه
        if direction == "right":
            start_pos = widget.mapToParent(widget.rect().topRight())
            end_pos = original_pos
        elif direction == "left":
            start_pos = widget.mapToParent(widget.rect().topLeft() - widget.rect().topRight())
            end_pos = original_pos
        elif direction == "up":
            start_pos = widget.mapToParent(widget.rect().topLeft() - widget.rect().bottomLeft())
            end_pos = original_pos
        else:  # down
            start_pos = widget.mapToParent(widget.rect().bottomLeft())
            end_pos = original_pos

        widget.move(start_pos)

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(easing)
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.active_animations[animation_id] = animation
        animation.start()

        return animation_id

    def float_animation(
        self,
        widget: QWidget,
        amplitude: int = 10,
        duration: int = 2000,
        easing: QEasingCurve.Type = QEasingCurve.InOutSine,
    ) -> str:
        """
        حركة float (طفو)

        Args:
            widget: الـ widget المراد تحريكه
            amplitude: سعة الحركة (بكسل)
            duration: مدة الدورة الكاملة (ملي ثانية)
            easing: نوع التخفيف

        Returns:
            معرف الحركة
        """
        animation_id = f"float_{id(widget)}"

        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()

        original_pos = widget.pos()

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(original_pos)
        animation.setEndValue(
            original_pos + widget.mapFromParent(widget.rect().topLeft() + widget.rect().bottomLeft()) * amplitude / 100
        )
        animation.setEasingCurve(easing)
        animation.setLoopCount(-1)  # تكرار لا نهائي

        animation.setDirection(QAbstractAnimation.Forward)

        self.active_animations[animation_id] = animation
        animation.start()

        return animation_id

    def scale_animation(
        self,
        widget: QWidget,
        start_scale: float = 0.8,
        end_scale: float = 1.0,
        duration: int = 300,
        easing: QEasingCurve.Type = QEasingCurve.OutBack,
    ) -> str:
        """
        حركة scale (تكبير/تصغير)
        Since QWidget doesn't support setTransform directly, this animates:
        - minimumWidth/minimumHeight for a subtle 1% size pulse (when start >= 1.0)
        - windowOpacity fade (when start < 1.0, appearance animation)
        """
        animation_id = f"scale_{id(widget)}"

        if animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()

        group = QParallelAnimationGroup()

        if start_scale < 1.0:
            # Appearance animation: fade in with opacity
            opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
            opacity_anim.setDuration(duration)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(easing)
            group.addAnimation(opacity_anim)
        else:
            # Hover / pulse effect: subtle 1% size pulse via geometry
            # This gives a visible micro-bounce without breaking layouts
            geo = widget.geometry()
            w, h = geo.width(), geo.height()

            # Calculate pixel offsets based on 1% of each dimension
            # We animate from start_scale to end_scale around the base size
            base_w = int(w / start_scale) if start_scale > 0 else w
            base_h = int(h / start_scale) if start_scale > 0 else h

            start_w = int(base_w * start_scale)
            start_h = int(base_h * start_scale)
            end_w = int(base_w * end_scale)
            end_h = int(base_h * end_scale)

            # Keep the center anchored
            delta_w = end_w - start_w
            delta_h = end_h - start_h

            start_geo = geo
            end_geo = geo.adjusted(
                -delta_w // 2,
                -delta_h // 2,
                delta_w // 2,
                delta_h // 2,
            )

            size_anim = QPropertyAnimation(widget, b"geometry")
            size_anim.setDuration(duration)
            size_anim.setStartValue(start_geo)
            size_anim.setEndValue(end_geo)
            size_anim.setEasingCurve(easing)
            group.addAnimation(size_anim)

        group.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.animation_groups[animation_id] = group
        group.start()

        return animation_id

    def stop_animation(self, animation_id: str):
        """إيقاف حركة"""
        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()
            del self.active_animations[animation_id]
        elif animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            del self.animation_groups[animation_id]
        # Also check pulse timers
        if animation_id in self._pulse_timers:
            self._pulse_timers[animation_id].stop()
            del self._pulse_timers[animation_id]

    def stop_all_animations(self):
        """إيقاف جميع الحركات"""
        for animation_id in list(self.active_animations.keys()):
            self.stop_animation(animation_id)
        for animation_id in list(self.animation_groups.keys()):
            self.stop_animation(animation_id)
        for timer_id in list(self._pulse_timers.keys()):
            self.stop_animation(timer_id)

    # ── NEW Methods ─────────────────────────────────────────────────────

    def stagger_fade_in(
        self,
        widgets: List[QWidget],
        delay_ms: int = 50,
        duration: int = 250,
    ) -> List[str]:
        """
        Fade in a list of widgets one after another with staggered delay.

        Args:
            widgets: قائمة الـ widgets المراد تحريكها
            delay_ms: التأخير بين كل widget (ملي ثانية)
            duration: مدة كل حركة fade (ملي ثانية)

        Returns:
            قائمة معرفات الحركات
        """
        animation_ids: List[str] = []

        for idx, widget in enumerate(widgets):
            # Hide all widgets first
            widget.setWindowOpacity(0.0)

            # Schedule each fade-in with increasing delay
            delay_timer = QTimer(self)
            delay_timer.setSingleShot(True)

            captured_widget = widget
            captured_idx = idx

            def _do_fade(w=captured_widget, i=captured_idx):
                aid = self.fade_in(w, duration=duration)
                animation_ids.append(aid)

            delay_timer.timeout.connect(_do_fade)
            # Store timer for cleanup
            timer_id = f"stagger_timer_{i}_{id(widget)}"
            self._pulse_timers[timer_id] = delay_timer
            delay_timer.start(i * delay_ms)

            animation_ids.append(f"stagger_{i}_{id(widget)}")

        return animation_ids

    def slide_fade_in(
        self,
        widget: QWidget,
        direction: str = "right",
        duration: int = 350,
    ) -> str:
        """
        Combined slide + fade animation using QParallelAnimationGroup.
        Animates both pos and windowOpacity simultaneously.

        Args:
            widget: الـ widget المراد تحريكه
            direction: الاتجاه (right, left, up, down)
            duration: مدة الحركة (ملي ثانية)

        Returns:
            معرف الحركة
        """
        animation_id = f"slide_fade_{direction}_{id(widget)}"

        if animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()

        original_pos = widget.pos()

        # Calculate slide offset based on direction
        offset_x, offset_y = 0, 0
        slide_distance = 40  # pixels

        if direction == "right":
            offset_x = slide_distance
        elif direction == "left":
            offset_x = -slide_distance
        elif direction == "up":
            offset_y = -slide_distance
        else:  # down
            offset_y = slide_distance

        start_pos = original_pos - QPoint(offset_x, offset_y)

        # Move widget to start position and set transparent
        widget.move(start_pos)
        widget.setWindowOpacity(0.0)

        # Create parallel group
        group = QParallelAnimationGroup()

        # Slide animation (pos)
        slide_anim = QPropertyAnimation(widget, b"pos")
        slide_anim.setDuration(duration)
        slide_anim.setStartValue(start_pos)
        slide_anim.setEndValue(original_pos)
        slide_anim.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(slide_anim)

        # Fade animation (windowOpacity)
        fade_anim = QPropertyAnimation(widget, b"windowOpacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(fade_anim)

        group.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.animation_groups[animation_id] = group
        group.start()

        return animation_id

    def pulse_glow(
        self,
        widget: QWidget,
        color_hex: str = "#C8A54E",
        duration: int = 2000,
    ) -> str:
        """
        Continuous pulsing glow effect on a widget.
        Uses geometry animation + style property changes to create
        a breathing glow border effect. Loops indefinitely until stopped.

        Args:
            widget: الـ widget المراد تطبيق التأثير عليه
            color_hex: لون التوهج (hex string)
            duration: مدة الدورة الكاملة (ملي ثانية)

        Returns:
            معرف الحركة
        """
        animation_id = f"pulse_glow_{id(widget)}"

        # Stop existing pulse for this widget
        if animation_id in self._pulse_timers:
            self._pulse_timers[animation_id].stop()
            del self._pulse_timers[animation_id]
        if animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            del self.animation_groups[animation_id]

        color = QColor(color_hex)

        # Store original geometry for restoration
        base_geo = widget.geometry()
        base_style = widget.styleSheet()

        # Create sequential group: pulse out -> pulse in -> repeat
        seq = QSequentialAnimationGroup()

        # Half-cycle duration for each direction
        half = duration // 2

        # Phase 1: expand slightly + glow up
        expand_group = QParallelAnimationGroup()

        expand_geo_anim = QPropertyAnimation(widget, b"geometry")
        expand_geo_anim.setDuration(half)
        expanded = base_geo.adjusted(-2, -2, 2, 2)
        expand_geo_anim.setStartValue(base_geo)
        expand_geo_anim.setEndValue(expanded)
        expand_geo_anim.setEasingCurve(QEasingCurve.OutSine)
        expand_group.addAnimation(expand_geo_anim)

        seq.addAnimation(expand_group)

        # Style update at midpoint — inject glow border
        def _apply_glow_on():
            widget.setStyleSheet(
                f"{base_style}\n"
                f"{{ border: 1px solid {color_hex}; "
                f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 15); }}"
            )

        # Phase 2: contract back + glow down
        contract_group = QParallelAnimationGroup()

        contract_geo_anim = QPropertyAnimation(widget, b"geometry")
        contract_geo_anim.setDuration(half)
        contract_geo_anim.setStartValue(expanded)
        contract_geo_anim.setEndValue(base_geo)
        contract_geo_anim.setEasingCurve(QEasingCurve.InSine)
        contract_group.addAnimation(contract_geo_anim)

        seq.addAnimation(contract_group)

        # Style update at cycle end — restore
        def _apply_glow_off():
            widget.setStyleSheet(base_style)

        # Connect style changes to group finished signals
        expand_group.finished.connect(_apply_glow_on)
        contract_group.finished.connect(_apply_glow_off)

        # Loop infinitely
        seq.setLoopCount(-1)

        seq.finished.connect(lambda: self._on_animation_finished(animation_id))

        self.animation_groups[animation_id] = seq
        seq.start()

        # Also track via a cleanup timer reference
        self._pulse_timers[animation_id] = QTimer(self)  # placeholder for stop

        return animation_id

    # ── Internal ─────────────────────────────────────────────────────────

    def pulse_border(self, widget: QWidget, color_hex: str = "#C8A54E", duration: int = 2000):
        """
        Pulse a widget's border color from transparent to full color and back.
        Creates a breathing border effect.

        Args:
            widget: عنصر واجهة المستخدم
            color_hex: لون الحد بصيغة hex
            duration: مدة الدورة الكاملة (ميلي ثانية)
        """
        animation_id = f"pulse_border_{id(widget)}"

        if animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            del self.animation_groups[animation_id]

        base_style = widget.styleSheet()
        half = duration // 2

        # Phase 1: fade border in
        anim_in = QPropertyAnimation(widget, b"windowOpacity")
        anim_in.setDuration(half)
        anim_in.setStartValue(0.85)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.InOutSine)

        def _border_on():
            widget.setStyleSheet(
                f"{base_style}\n"
                f"{{ border: 1px solid {color_hex}; }}"
            )

        # Phase 2: fade border out
        anim_out = QPropertyAnimation(widget, b"windowOpacity")
        anim_out.setDuration(half)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.85)
        anim_out.setEasingCurve(QEasingCurve.InOutSine)

        def _border_off():
            widget.setStyleSheet(base_style)

        seq = QSequentialAnimationGroup()
        seq.addAnimation(anim_in)
        seq.addAnimation(anim_out)

        anim_in.finished.connect(_border_on)
        anim_out.finished.connect(_border_off)
        seq.setLoopCount(-1)

        self.animation_groups[animation_id] = seq
        seq.start()
        return animation_id

    def shimmer_effect(self, widget: QWidget, duration: int = 1500):
        """
        Create a subtle opacity shimmer sweep effect on a widget.
        Rapidly pulses opacity to create a shimmer/loading feel.

        Args:
            widget: عنصر واجهة المستخدم
            duration: مدة الدورة (ميلي ثانية)
        """
        animation_id = f"shimmer_{id(widget)}"

        if animation_id in self.animation_groups:
            self.animation_groups[animation_id].stop()
            del self.animation_groups[animation_id]

        seq = QSequentialAnimationGroup()
        steps = 6
        step_dur = duration // steps

        for i in range(steps):
            anim = QPropertyAnimation(widget, b"windowOpacity")
            anim.setDuration(step_dur)
            # Alternate between 0.7 and 1.0 for shimmer
            target = 0.7 if i % 2 == 0 else 1.0
            anim.setStartValue(1.0 if i % 2 == 0 else 0.7)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            seq.addAnimation(anim)

        seq.setLoopCount(3)  # shimmer 3 times then stop

        def _cleanup():
            widget.setWindowOpacity(1.0)
            self._on_animation_finished(animation_id)

        seq.finished.connect(_cleanup)
        self.animation_groups[animation_id] = seq
        seq.start()
        return animation_id

    def _on_animation_finished(self, animation_id: str):
        """عند انتهاء الحركة"""
        if animation_id in self.active_animations:
            del self.active_animations[animation_id]
        if animation_id in self.animation_groups:
            del self.animation_groups[animation_id]
        self.animation_finished.emit(animation_id)