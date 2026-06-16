#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Window State Manager - مدير حالة النوافذ المتقدم
Advanced Window State Management System

يقوم بـ:
- حفظ/استعادة آخر تبويب مفتوح
- حفظ/استعادة آخر فلتر مستخدم
- حفظ/استعادة حالة الجداول (ترتيب الأعمدة، العرض، التصفية)
- حفظ/استعادة حالة العناصر الأخرى (QComboBox, QCheckBox, etc.)
"""

from __future__ import annotations
import logging

import json
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, QSettings
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QTableView,
    QTableWidget,
    QTabWidget,
    QWidget,
)

logger = logging.getLogger("window_state_manager")


class WindowStateManager(QObject):
    """
    مدير حالة النوافذ المتقدم

    يوفر:
    - حفظ/استعادة التبويبات
    - حفظ/استعادة الفلاتر
    - حفظ/استعادة حالة الجداول
    - حفظ/استعادة حالة العناصر الأخرى
    """

    def __init__(
        self,
        organization: str = "LogicalVersion",
        appname: str = "ERP",
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.settings = QSettings(organization, appname)
        self.logger = logger

    def save_tab_state(self, window_key: str, tab_widget: QTabWidget, tab_key: str = "main_tabs"):
        """
        حفظ حالة التبويبات

        Args:
            window_key: مفتاح النافذة
            tab_widget: QTabWidget instance
            tab_key: مفتاح التبويبات (لنوافذ متعددة التبويبات)
        """
        try:
            current_index = tab_widget.currentIndex()
            if current_index >= 0:
                tab_name = tab_widget.tabText(current_index)
                state_data = {"current_index": current_index, "tab_name": tab_name}
                key = f"{window_key}/tabs/{tab_key}"
                self.settings.setValue(key, json.dumps(state_data))
                self.settings.sync()
                self.logger.debug(f"Saved tab state for {window_key}/{tab_key}: index={current_index}")
        except Exception as e:
            self.logger.exception(f"Failed to save tab state for {window_key}/{tab_key}: {e}")

    def restore_tab_state(self, window_key: str, tab_widget: QTabWidget, tab_key: str = "main_tabs") -> bool:
        """
        استعادة حالة التبويبات

        Returns:
            True if state was restored, False otherwise
        """
        try:
            key = f"{window_key}/tabs/{tab_key}"
            raw = self.settings.value(key, "")
            if not raw:
                return False

            state_data = json.loads(raw)
            current_index = state_data.get("current_index", -1)

            if 0 <= current_index < tab_widget.count():
                tab_widget.setCurrentIndex(current_index)
                self.logger.debug(f"Restored tab state for {window_key}/{tab_key}: index={current_index}")
                return True
        except Exception as e:
            self.logger.exception(f"Failed to restore tab state for {window_key}/{tab_key}: {e}")

        return False

    def save_filter_state(
        self,
        window_key: str,
        filter_widgets: Dict[str, Any],
        filter_key: str = "main_filters",
    ):
        """
        حفظ حالة الفلاتر

        Args:
            window_key: مفتاح النافذة
            filter_widgets: Dict of filter_name -> widget
            filter_key: مفتاح الفلاتر
        """
        try:
            filter_data = {}

            for filter_name, widget in filter_widgets.items():
                if isinstance(widget, QComboBox):
                    filter_data[filter_name] = {
                        "type": "comboBox",
                        "current_index": widget.currentIndex(),
                        "current_text": widget.currentText(),
                        "current_data": widget.currentData(),
                    }
                elif isinstance(widget, QLineEdit):
                    filter_data[filter_name] = {
                        "type": "lineEdit",
                        "text": widget.text(),
                    }
                elif isinstance(widget, QDateEdit):
                    filter_data[filter_name] = {
                        "type": "dateEdit",
                        "date": widget.date().toString("yyyy-MM-dd"),
                    }
                elif isinstance(widget, QCheckBox):
                    filter_data[filter_name] = {
                        "type": "checkBox",
                        "checked": widget.isChecked(),
                    }
                elif isinstance(widget, QSpinBox):
                    filter_data[filter_name] = {
                        "type": "spinBox",
                        "value": widget.value(),
                    }
                elif isinstance(widget, QDoubleSpinBox):
                    filter_data[filter_name] = {
                        "type": "doubleSpinBox",
                        "value": widget.value(),
                    }

            if filter_data:
                key = f"{window_key}/filters/{filter_key}"
                self.settings.setValue(key, json.dumps(filter_data))
                self.settings.sync()
                self.logger.debug(f"Saved filter state for {window_key}/{filter_key}: {len(filter_data)} filters")
        except Exception as e:
            self.logger.exception(f"Failed to save filter state for {window_key}/{filter_key}: {e}")

    def restore_filter_state(
        self,
        window_key: str,
        filter_widgets: Dict[str, Any],
        filter_key: str = "main_filters",
    ) -> bool:
        """
        استعادة حالة الفلاتر

        Returns:
            True if state was restored, False otherwise
        """
        try:
            key = f"{window_key}/filters/{filter_key}"
            raw = self.settings.value(key, "")
            if not raw:
                return False

            filter_data = json.loads(raw)
            restored_count = 0

            for filter_name, widget in filter_widgets.items():
                if filter_name not in filter_data:
                    continue

                data = filter_data[filter_name]
                widget_type = data.get("type")

                try:
                    if widget_type == "comboBox" and isinstance(widget, QComboBox):
                        current_index = data.get("current_index", -1)
                        if 0 <= current_index < widget.count():
                            widget.setCurrentIndex(current_index)
                            restored_count += 1
                    elif widget_type == "lineEdit" and isinstance(widget, QLineEdit):
                        widget.setText(data.get("text", ""))
                        restored_count += 1
                    elif widget_type == "dateEdit" and isinstance(widget, QDateEdit):
                        from PySide6.QtCore import QDate

                        date_str = data.get("date", "")
                        if date_str:
                            date = QDate.fromString(date_str, "yyyy-MM-dd")
                            if date.isValid():
                                widget.setDate(date)
                                restored_count += 1
                    elif widget_type == "checkBox" and isinstance(widget, QCheckBox):
                        widget.setChecked(data.get("checked", False))
                        restored_count += 1
                    elif widget_type == "spinBox" and isinstance(widget, QSpinBox):
                        widget.setValue(data.get("value", 0))
                        restored_count += 1
                    elif widget_type == "doubleSpinBox" and isinstance(widget, QDoubleSpinBox):
                        widget.setValue(data.get("value", 0.0))
                        restored_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to restore filter {filter_name}: {e}")

            if restored_count > 0:
                self.logger.debug(f"Restored filter state for {window_key}/{filter_key}: {restored_count} filters")
                return True
        except Exception as e:
            self.logger.exception(f"Failed to restore filter state for {window_key}/{filter_key}: {e}")

        return False

    def save_table_state(
        self,
        window_key: str,
        table: QTableWidget | QTableView,
        table_key: str = "main_table",
    ):
        """
        حفظ حالة الجدول

        Args:
            window_key: مفتاح النافذة
            table: QTableWidget or QTableView instance
            table_key: مفتاح الجدول (لنوافذ متعددة الجداول)
        """
        try:
            table_data = {}

            # حفظ ترتيب وعرض الأعمدة
            header = table.horizontalHeader()
            if header:
                column_order = []
                column_widths = {}

                for i in range(header.count()):
                    logical_index = header.logicalIndex(i)
                    column_order.append(logical_index)
                    column_widths[logical_index] = header.sectionSize(logical_index)

                table_data["column_order"] = column_order
                table_data["column_widths"] = column_widths

            # حفظ حالة التصفية والترتيب
            if isinstance(table, QTableView):
                sort_column = table.horizontalHeader().sortIndicatorSection()
                sort_order = table.horizontalHeader().sortIndicatorOrder()
                if sort_column >= 0:
                    table_data["sort_column"] = sort_column
                    table_data["sort_order"] = int(sort_order)

            # حفظ الصف المحدد
            if isinstance(table, QTableWidget):
                current_row = table.currentRow()
                if current_row >= 0:
                    table_data["current_row"] = current_row

            # حفظ حالة التمرير
            if isinstance(table, QAbstractItemView):
                scroll_bar = table.verticalScrollBar()
                if scroll_bar:
                    table_data["scroll_position"] = scroll_bar.value()

            if table_data:
                key = f"{window_key}/tables/{table_key}"
                self.settings.setValue(key, json.dumps(table_data))
                self.settings.sync()
                self.logger.debug(f"Saved table state for {window_key}/{table_key}")
        except Exception as e:
            self.logger.exception(f"Failed to save table state for {window_key}/{table_key}: {e}")

    def restore_table_state(
        self,
        window_key: str,
        table: QTableWidget | QTableView,
        table_key: str = "main_table",
    ) -> bool:
        """
        استعادة حالة الجدول

        Returns:
            True if state was restored, False otherwise
        """
        try:
            key = f"{window_key}/tables/{table_key}"
            raw = self.settings.value(key, "")
            if not raw:
                return False

            table_data = json.loads(raw)
            restored = False

            # استعادة ترتيب وعرض الأعمدة
            header = table.horizontalHeader()
            if header and "column_order" in table_data:
                table_data.get("column_order", [])
                column_widths = table_data.get("column_widths", {})

                # استعادة عرض الأعمدة
                for logical_index, width in column_widths.items():
                    if 0 <= logical_index < header.count():
                        header.resizeSection(logical_index, width)
                        restored = True

                # ملاحظة: ترتيب الأعمدة يتطلب setSectionMovable(True) أولاً
                # ولا يمكن استعادته بسهولة في Qt

            # استعادة حالة التصفية والترتيب
            if isinstance(table, QTableView) and "sort_column" in table_data:
                sort_column = table_data.get("sort_column", -1)
                sort_order = table_data.get("sort_order", 0)
                if 0 <= sort_column < header.count():
                    from PySide6.QtCore import Qt

                    table.sortByColumn(sort_column, Qt.SortOrder(sort_order))
                    restored = True

            # استعادة الصف المحدد
            if isinstance(table, QTableWidget) and "current_row" in table_data:
                current_row = table_data.get("current_row", -1)
                if 0 <= current_row < table.rowCount():
                    table.selectRow(current_row)
                    table.setCurrentCell(current_row, 0)
                    restored = True

            # استعادة حالة التمرير
            if isinstance(table, QAbstractItemView) and "scroll_position" in table_data:
                scroll_position = table_data.get("scroll_position", 0)
                scroll_bar = table.verticalScrollBar()
                if scroll_bar:
                    scroll_bar.setValue(scroll_position)
                    restored = True

            if restored:
                self.logger.debug(f"Restored table state for {window_key}/{table_key}")
                return True
        except Exception as e:
            self.logger.exception(f"Failed to restore table state for {window_key}/{table_key}: {e}")

        return False

    def save_window_state(self, window_key: str, window: QWidget, state_data: Dict[str, Any]):
        """
        حفظ حالة عامة للنافذة

        Args:
            window_key: مفتاح النافذة
            window: QWidget instance
            state_data: Dict of state data to save
        """
        try:
            key = f"{window_key}/state"
            self.settings.setValue(key, json.dumps(state_data))
            self.settings.sync()
            self.logger.debug(f"Saved window state for {window_key}")
        except Exception as e:
            self.logger.exception(f"Failed to save window state for {window_key}: {e}")

    def restore_window_state(self, window_key: str) -> Dict[str, Any]:
        """
        استعادة حالة عامة للنافذة

        Returns:
            Dict of state data or empty dict
        """
        try:
            key = f"{window_key}/state"
            raw = self.settings.value(key, "")
            if raw:
                return json.loads(raw)
        except Exception as e:
            self.logger.exception(f"Failed to restore window state for {window_key}: {e}")

        return {}

    def clear_window_state(self, window_key: str):
        """مسح جميع حالة النافذة"""
        try:
            # مسح جميع المفاتيح المتعلقة بالنافذة
            self.settings.remove(f"{window_key}/tabs")
            self.settings.remove(f"{window_key}/filters")
            self.settings.remove(f"{window_key}/tables")
            self.settings.remove(f"{window_key}/state")
            self.settings.sync()
            self.logger.debug(f"Cleared window state for {window_key}")
        except Exception as e:
            self.logger.exception(f"Failed to clear window state for {window_key}: {e}")
