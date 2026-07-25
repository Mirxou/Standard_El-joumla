#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accessibility Utilities for UI - Compliance with WCAG 2.1
Based on ui-ux-pro-max guidelines
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton
from src.ui.styles.design_tokens import C


class AccessibilityUtils:
    """Utilities for improving UI accessibility"""

    # Minimum touch target size (WCAG recommendation)
    MIN_TOUCH_TARGET_SIZE = 44

    # Color contrast ratio (WCAG requires 4.5:1 for normal text)
    MIN_CONTRAST_RATIO = 4.5

    @staticmethod
    def ensure_minimum_size(widget, min_width=None, min_height=None):
        """
        Ensure widget meets minimum size requirements for touch targets

        Args:
            widget: QWidget to resize
            min_width: Minimum width (default: 44)
            min_height: Minimum height (default: 44)
        """
        if min_width is None:
            min_width = AccessibilityUtils.MIN_TOUCH_TARGET_SIZE
        if min_height is None:
            min_height = AccessibilityUtils.MIN_TOUCH_TARGET_SIZE

        current = widget.size()
        new_width = max(current.width(), min_width)
        new_height = max(current.height(), min_height)

        widget.setFixedSize(new_width, new_height)
        return widget

    @staticmethod
    def add_accessible_label(widget, name, description=None):
        """
        Add accessible name and description to widget

        Args:
            widget: QWidget to enhance
            name: Accessible name (e.g., "إدخال اسم العميل")
            description: Detailed description (optional)
        """
        widget.setAccessibleName(name)
        if description:
            widget.setAccessibleDescription(description)
        return widget

    @staticmethod
    def create_accessible_button(text, object_name, accessible_name, min_size=(100, 44)):
        """
        Create an accessible push button with proper sizing

        Args:
            text: Button text
            object_name: Qt object name
            accessible_name: Accessible name
            min_size: Minimum size (width, height)
        """
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setAccessibleName(accessible_name)

        if min_size:
            button.setFixedSize(min_size[0], min_size[1])

        return button

    @staticmethod
    def create_accessible_label(text, object_name, accessible_name, align=Qt.AlignLeft):
        """
        Create an accessible label

        Args:
            text: Label text
            object_name: Qt object name
            accessible_name: Accessible name
            align: Alignment
        """
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAccessibleName(accessible_name)
        label.setAlignment(align)
        return label

    @staticmethod
    def create_accessible_input(
        object_name,
        accessible_name,
        accessible_description,
        placeholder="",
        min_width=200,
        min_height=44,
    ):
        """
        Create an accessible line edit input

        Args:
            object_name: Qt object name
            accessible_name: Accessible name
            accessible_description: Accessible description
            placeholder: Placeholder text
            min_width: Minimum width
            min_height: Minimum height
        """
        line_edit = QLineEdit()
        line_edit.setObjectName(object_name)
        line_edit.setAccessibleName(accessible_name)
        line_edit.setAccessibleDescription(accessible_description)
        line_edit.setPlaceholderText(placeholder)

        if min_width or min_height:
            line_edit.setMinimumSize(min_width or 0, min_height or 0)

        return line_edit

    @staticmethod
    def create_accessible_combo(
        object_name,
        accessible_name,
        accessible_description,
        items=None,
        min_width=200,
        min_height=44,
    ):
        """
        Create an accessible combo box

        Args:
            object_name: Qt object name
            accessible_name: Accessible name
            accessible_description: Accessible description
            items: List of items
            min_width: Minimum width
            min_height: Minimum height
        """
        combo = QComboBox()
        combo.setObjectName(object_name)
        combo.setAccessibleName(accessible_name)
        combo.setAccessibleDescription(accessible_description)

        if items:
            combo.addItems(items)

        if min_width or min_height:
            combo.setMinimumSize(min_width or 0, min_height or 0)

        return combo

    @staticmethod
    def apply_focus_style(widget):
        """
        Apply clear focus style for keyboard navigation

        Args:
            widget: Widget to apply focus style
        """
        widget.setFocusPolicy(Qt.TabFocus)
        return widget


class AccessibleFormBuilder:
    """Builder for creating accessible forms"""

    def __init__(self):
        self.widgets = []

    def add_label(self, text, object_name, accessible_name):
        label = AccessibilityUtils.create_accessible_label(text, object_name, accessible_name)
        self.widgets.append(("label", label))
        return self

    def add_input(self, object_name, accessible_name, description, placeholder=""):
        input_field = AccessibilityUtils.create_accessible_input(object_name, accessible_name, description, placeholder)
        self.widgets.append(("input", input_field))
        return self

    def add_combo(self, object_name, accessible_name, description, items):
        combo = AccessibilityUtils.create_accessible_combo(object_name, accessible_name, description, items)
        self.widgets.append(("combo", combo))
        return self

    def add_checkbox(self, text, object_name, accessible_name):
        checkbox = QCheckBox(text)
        checkbox.setObjectName(object_name)
        checkbox.setAccessibleName(accessible_name)
        self.widgets.append(("checkbox", checkbox))
        return self

    def add_button(self, text, object_name, accessible_name):
        button = AccessibilityUtils.create_accessible_button(text, object_name, accessible_name)
        self.widgets.append(("button", button))
        return self

    def get_widgets(self):
        return self.widgets


# Color contrast checker
class ContrastChecker:
    """Check color contrast ratios for WCAG compliance"""

    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def get_luminance(r, g, b):
        """Calculate relative luminance"""

        def adjust(c):
            c = c / 255
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    @staticmethod
    def contrast_ratio(color1, color2):
        """Calculate contrast ratio between two colors"""
        rgb1 = ContrastChecker.hex_to_rgb(color1)
        rgb2 = ContrastChecker.hex_to_rgb(color2)

        l1 = ContrastChecker.get_luminance(*rgb1)
        l2 = ContrastChecker.get_luminance(*rgb2)

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def is_contrast_valid(foreground, background, min_ratio=4.5):
        """Check if contrast meets WCAG requirements"""
        ratio = ContrastChecker.contrast_ratio(foreground, background)
        return ratio >= min_ratio


# Predefined accessible color palettes
ACCESSIBLE_PALETTES = {
    "business": {
        "primary": "#1E3A5F",
        "secondary": "#4A5568",
        "accent": "#D4AF37",
        "success": "#059669",
        "warning": "C.ACCENT_AMBER_DARK",
        "error": "#DC2626",
        "bg_light": "#F3F4F6",
        "bg_white": "C.TEXT_BRIGHT",
        "text_primary": "#1F2937",
        "text_secondary": "#6B7280",
    },
    "nature": {
        "primary": "#2F5233",
        "secondary": "#4A6741",
        "accent": "#84CC16",
        "success": "#22C55E",
        "warning": "#EAB308",
        "error": "#DC2626",
        "bg_light": "#F7FEE7",
        "bg_white": "C.TEXT_BRIGHT",
        "text_primary": "#1F2937",
        "text_secondary": "#4B5563",
    },
}
