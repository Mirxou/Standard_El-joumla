#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual Effects
التأثيرات البصرية - gradients, glows, shadows
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush
from PySide6.QtCore import Qt, QRect, QPoint
from typing import Optional, Tuple, List
from src.utils.logger import setup_logger


class VisualEffects:
    """التأثيرات البصرية"""
    
    @staticmethod
    def draw_gradient_background(painter: QPainter, rect: QRect, start_color: QColor, end_color: QColor, direction: str = "horizontal"):
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
    def draw_glow_effect(painter: QPainter, rect: QRect, color: QColor, intensity: int = 10, blur_radius: int = 20):
        """
        رسم تأثير glow
        
        Args:
            painter: QPainter
            rect: المنطقة
            color: اللون
            intensity: شدة التأثير
            blur_radius: نصف قطر التمويه
        """
        # رسم طبقات متعددة للـ glow
        for i in range(intensity):
            alpha = int(255 * (1.0 - i / intensity) * 0.3)
            glow_color = QColor(color)
            glow_color.setAlpha(alpha)
            
            pen = QPen(glow_color, blur_radius - i * 2)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(i, i, -i, -i), 10, 10)
    
    @staticmethod
    def draw_shadow_effect(painter: QPainter, rect: QRect, offset: QPoint = QPoint(5, 5), blur: int = 10, color: QColor = QColor(0, 0, 0, 100)):
        """
        رسم تأثير shadow
        
        Args:
            painter: QPainter
            rect: المنطقة
            offset: الإزاحة
            blur: التمويه
            color: لون الظل
        """
        shadow_rect = rect.translated(offset)
        
        # رسم طبقات متعددة للظل
        for i in range(blur):
            alpha = int(color.alpha() * (1.0 - i / blur))
            shadow_color = QColor(color)
            shadow_color.setAlpha(alpha)
            
            painter.fillRect(
                shadow_rect.adjusted(i, i, -i, -i),
                shadow_color
            )
    
    @staticmethod
    def draw_glass_effect(painter: QPainter, rect: QRect, opacity: float = 0.1, blur: bool = True):
        """
        رسم تأثير glass (زجاجي)
        
        Args:
            painter: QPainter
            rect: المنطقة
            opacity: الشفافية
            blur: تفعيل التمويه
        """
        # خلفية شفافة
        glass_color = QColor(255, 255, 255, int(255 * opacity))
        painter.fillRect(rect, glass_color)
        
        # حد فاتح
        pen = QPen(QColor(255, 255, 255, int(255 * opacity * 2)))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)
    
    @staticmethod
    def draw_neon_effect(painter: QPainter, rect: QRect, color: QColor, intensity: int = 5):
        """
        رسم تأثير neon
        
        Args:
            painter: QPainter
            rect: المنطقة
            color: اللون
            intensity: شدة التأثير
        """
        # رسم طبقات متعددة للـ neon
        for i in range(intensity):
            alpha = int(255 * (1.0 - i / intensity))
            neon_color = QColor(color)
            neon_color.setAlpha(alpha)
            
            pen = QPen(neon_color, 3 - i * 0.5)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(i, i, -i, -i), 10, 10)
    
    @staticmethod
    def draw_gradient_border(painter: QPainter, rect: QRect, start_color: QColor, end_color: QColor, width: int = 2):
        """
        رسم حد متدرج
        
        Args:
            painter: QPainter
            rect: المنطقة
            start_color: لون البداية
            end_color: لون النهاية
            width: عرض الحد
        """
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, start_color)
        gradient.setColorAt(1.0, end_color)
        
        pen = QPen(QBrush(gradient), width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)
