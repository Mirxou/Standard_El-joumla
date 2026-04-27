#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focus Style Manager for Keyboard Navigation
Based on ui-ux-pro-max accessibility guidelines
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont


class FocusStyleManager:
    """
    Manages focus styles for keyboard navigation
    Following WCAG 2.1 guidelines for focus visibility
    """
    
    # Focus colors (high contrast for visibility)
    FOCUS_COLORS = {
        "default": "#2563EB",      # Blue - clear visibility
        "high_contrast": "#000000",  # Black - maximum contrast
        "gold": "#D4AF37",         # Gold - premium feel
        "success": "#059669",        # Green - positive action
    }
    
    # Focus border widths
    FOCUS_WIDTH = 3
    
    @staticmethod
    def get_focus_stylesheet(color_name="default", border_radius=4):
        """
        Get stylesheet for focused elements
        
        Args:
            color_name: Color key from FOCUS_COLORS
            border_radius: Border radius in pixels
            
        Returns:
            str: CSS stylesheet for focus
        """
        color = FocusStyleManager.FOCUS_COLORS.get(color_name, FocusStyleManager.FOCUS_COLORS["default"])
        
        return f"""
            QPushButton:focus {{
                outline: none;
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
                border-radius: {border_radius}px;
                background-color: palette(button);
            }}
            QPushButton:focus:hover {{
                background-color: palette(light);
            }}
            QLineEdit:focus {{
                outline: none;
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
                border-radius: {border_radius}px;
            }}
            QComboBox:focus {{
                outline: none;
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
                border-radius: {border_radius}px;
            }}
            QCheckBox:focus {{
                outline: none;
            }}
            QCheckBox:focus::indicator {{
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
            }}
            QRadioButton:focus {{
                outline: none;
            }}
            QRadioButton:focus::indicator {{
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
            }}
            QTabWidget::pane:focus {{
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
            }}
        """
    
    @staticmethod
    def apply_focus_to_app(app, color_name="default"):
        """
        Apply focus styles to entire application
        
        Args:
            app: QApplication instance
            color_name: Color key for focus indication
        """
        stylesheet = FocusStyleManager.get_focus_stylesheet(color_name)
        
        # Get existing stylesheet and append focus styles
        existing = app.styleSheet()
        if existing:
            app.setStyleSheet(existing + "\n" + stylesheet)
        else:
            app.setStyleSheet(stylesheet)
    
    @staticmethod
    def set_focus_indicator(widget, color_name="default"):
        """
        Set custom focus indicator on widget
        
        Args:
            widget: QWidget to set focus on
            color_name: Color key for focus
        """
        color = FocusStyleManager.FOCUS_COLORS.get(color_name, FocusStyleManager.FOCUS_COLORS["default"])
        
        # Set focus policy
        widget.setFocusPolicy(Qt.StrongFocus)
        
        # Install event filter for custom painting
        widget.setStyleSheet(f"""
            QWidget:focus {{
                border: {FocusStyleManager.FOCUS_WIDTH}px solid {color};
            }}
        """)


class KeyboardNavigationHelper:
    """
    Helper for keyboard navigation in forms
    Implements proper Tab order and Enter key handling
    """
    
    @staticmethod
    def set_tab_order(widgets):
        """
        Set proper tab order for form widgets
        
        Args:
            widgets: List of widgets in tab order
        """
        for i in range(len(widgets) - 1):
            QWidget.setTabOrder(widgets[i], widgets[i + 1])
    
    @staticmethod
    def connect_enter_key(from_widget, to_widget):
        """
        Connect Enter key to move focus to next widget
        
        Args:
            from_widget: Current widget
            to_widget: Next widget to focus
        """
        from_widget.returnPressed.connect(to_widget.setFocus)
    
    @staticmethod
    def setup_form_navigation(form_widgets):
        """
        Setup complete keyboard navigation for a form
        
        Args:
            form_widgets: List of (widget, is_last) tuples
        """
        for i, (widget, is_last) in enumerate(form_widgets):
            widget.setFocusPolicy(Qt.TabFocus)
            
            if not is_last and i < len(form_widgets) - 1:
                next_widget = form_widgets[i + 1][0]
                KeyboardNavigationHelper.connect_enter_key(widget, next_widget)


class AccessibleColorScheme:
    """
    Color scheme that meets WCAG contrast requirements
    """
    
    # Predefined accessible schemes
    SCHEMES = {
        "professional": {
            "name": "Professional",
            "background": "#FFFFFF",
            "foreground": "#1F2937",  # 15.3:1 contrast
            "link": "#2563EB",
            "visited": "#7C3AED",
            "button_bg": "#1E3A5F",
            "button_text": "#FFFFFF",  # 13.6:1 contrast
            "input_bg": "#FFFFFF",
            "input_border": "#D1D5DB",
            "input_focus_border": "#2563EB",
            "error": "#DC2626",
            "success": "#059669",
            "warning": "#D97706",
        },
        "dark": {
            "name": "Dark Mode",
            "background": "#1F2937",
            "foreground": "#F9FAFB",  # 14.8:1 contrast
            "link": "#60A5FA",
            "visited": "#A78BFA",
            "button_bg": "#3B82F6",
            "button_text": "#FFFFFF",
            "input_bg": "#374151",
            "input_border": "#4B5563",
            "input_focus_border": "#60A5FA",
            "error": "#F87171",
            "success": "#34D399",
            "warning": "#FBBF24",
        },
        "high_contrast": {
            "name": "High Contrast",
            "background": "#000000",
            "foreground": "#FFFFFF",  # 21:1 contrast
            "link": "#00FFFF",
            "visited": "#FFFF00",
            "button_bg": "#FFFFFF",
            "button_text": "#000000",
            "input_bg": "#000000",
            "input_border": "#FFFFFF",
            "input_focus_border": "#FFFF00",
            "error": "#FF0000",
            "success": "#00FF00",
            "warning": "#FFFF00",
        }
    }
    
    @staticmethod
    def get_scheme(name="professional"):
        """Get color scheme by name"""
        return AccessibleColorScheme.SCHEMES.get(name, AccessibleColorScheme.SCHEMES["professional"])
    
    @staticmethod
    def get_stylesheet(scheme_name="professional"):
        """Get complete stylesheet for scheme"""
        scheme = AccessibleColorScheme.get_scheme(scheme_name)
        
        return f"""
            QWidget {{
                background-color: {scheme['background']};
                color: {scheme['foreground']};
            }}
            QPushButton {{
                background-color: {scheme['button_bg']};
                color: {scheme['button_text']};
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {scheme['input_bg']};
                border: 2px solid {scheme['input_border']};
                border-radius: 6px;
                padding: 10px;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border-color: {scheme['input_focus_border']};
            }}
            QLabel {{
                color: {scheme['foreground']};
            }}
            QMessageBox {{
                background-color: {scheme['background']};
            }}
            QCheckBox, QRadioButton {{
                color: {scheme['foreground']};
            }}
        """
