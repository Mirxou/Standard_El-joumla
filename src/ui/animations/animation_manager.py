#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Animation Manager
مدير الحركات - نظام شامل للحركات والتأثيرات
"""

from enum import Enum
from typing import Dict, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Signal,
)
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

        # إنشاء حركة ذهاب وإياب
        from PySide6.QtCore import QAbstractAnimation

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
        ملاحظة: QWidget لا يدعم setTransform مباشرة. سيتم تنفيذ تأثير بديل آمن.
        """
        animation_id = f"scale_{id(widget)}"

        if animation_id in self.active_animations:
            self.active_animations[animation_id].stop()

        # NOTE: Cannot use setTransform on standard QWidgets without QGraphicsProxyWidget
        # For now, we utilize the opacity transition or a slight geometry shift if feasible.
        # To avoid layout breakage, we will primarily animate opacity or a shadow effect.

        # إنشاء animation group
        group = QParallelAnimationGroup()

        # Animation للعرض (opacity) fallback
        opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
        opacity_anim.setDuration(duration)
        # We assume start/end scale implies visibility transition logic in the original code,
        # but if it's just hover effect, opacity might be weird.
        # However, to fix the CRASH, removing setTransform is key.
        # If this is for HOVER, usually we don't change opacity 0->1.
        # Let's check typical usage. If start=1.0, end=1.05 (hover), opacity 0->1 is WRONG.

        # Better safe fallback: just ensure widget is visible.
        # usage in main_window: scale_animation(self, start_scale=1.0, end_scale=1.05, duration=200)

        # If it's a hover effect (scale > 1), maybe we can animate a property like "styleSheet"? Expensive.
        # Let's just do a dummy animation to keep the signal flow working without crashing.
        # Or if available, animate "geometry" slightly? (Requires knowing parent layout).

        # SAFEST FIX: Do the Opacity animation ONLY if it looks like an "Appearance" animation (start < 1).
        # If start >= 1 (Hover), do nothing visual but emit finished, OR animate a shadow.

        if start_scale < 1.0:
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(easing)
            group.addAnimation(opacity_anim)
        else:
            # Dummy animation to maintain timing
            dummy = QPropertyAnimation(widget, b"geometry")
            dummy.setDuration(duration)
            dummy.setStartValue(widget.geometry())
            dummy.setEndValue(widget.geometry())
            group.addAnimation(dummy)

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

    def stop_all_animations(self):
        """إيقاف جميع الحركات"""
        for animation_id in list(self.active_animations.keys()):
            self.stop_animation(animation_id)
        for animation_id in list(self.animation_groups.keys()):
            self.stop_animation(animation_id)

    def _on_animation_finished(self, animation_id: str):
        """عند انتهاء الحركة"""
        if animation_id in self.active_animations:
            del self.active_animations[animation_id]
        if animation_id in self.animation_groups:
            del self.animation_groups[animation_id]
        self.animation_finished.emit(animation_id)
