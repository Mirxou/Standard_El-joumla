#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Charts Widgets - مكونات الرسوم البيانية المتقدمة
مكونات QtCharts للرسوم البيانية المتقدمة
"""

from typing import Dict, List, Tuple

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QPieSlice,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LineChartWidget(QWidget):
    """مكون رسم بياني خطي"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            layout.addWidget(title_label)

        self.chart = QChart()
        self.chart.setTitle(self.title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(self.chart_view)

    def add_series(self, name: str, data: List[Tuple[float, float]]):
        """إضافة سلسلة بيانات"""
        series = QLineSeries()
        series.setName(name)

        for x, y in data:
            series.append(x, y)

        self.chart.addSeries(series)

        # إعداد المحاور
        axis_x = QValueAxis()
        axis_y = QValueAxis()

        if data:
            x_values = [point[0] for point in data]
            y_values = [point[1] for point in data]

            axis_x.setRange(min(x_values), max(x_values))
            axis_y.setRange(min(y_values), max(y_values))

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    def clear(self):
        """مسح الرسم البياني"""
        self.chart.removeAllSeries()


class BarChartWidget(QWidget):
    """مكون رسم بياني عمودي"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            layout.addWidget(title_label)

        self.chart = QChart()
        self.chart.setTitle(self.title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(self.chart_view)

    def add_data(self, categories: List[str], data: Dict[str, List[float]]):
        """إضافة البيانات"""
        series = QBarSeries()

        for series_name, values in data.items():
            bar_set = QBarSet(series_name)
            for value in values:
                bar_set.append(value)
            series.append(bar_set)

        self.chart.addSeries(series)

        # إعداد المحاور
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)

        axis_y = QValueAxis()
        if data:
            all_values = [v for values in data.values() for v in values]
            if all_values:
                axis_y.setRange(0, max(all_values) * 1.1)

        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    def clear(self):
        """مسح الرسم البياني"""
        self.chart.removeAllSeries()


class PieChartWidget(QWidget):
    """مكون رسم بياني دائري"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            layout.addWidget(title_label)

        self.chart = QChart()
        self.chart.setTitle(self.title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        layout.addWidget(self.chart_view)

    def add_data(self, data: Dict[str, float]):
        """إضافة البيانات"""
        series = QPieSeries()

        colors = [
            QColor("#4CAF50"),
            QColor("#2196F3"),
            QColor("#FF9800"),
            QColor("#F44336"),
            QColor("#9C27B0"),
            QColor("#00BCD4"),
            QColor("#FFC107"),
            QColor("#795548"),
        ]

        for idx, (label, value) in enumerate(data.items()):
            slice = QPieSlice(label, value)
            slice.setColor(colors[idx % len(colors)])
            slice.setLabelVisible(True)
            series.append(slice)

        self.chart.addSeries(series)

    def clear(self):
        """مسح الرسم البياني"""
        self.chart.removeAllSeries()
