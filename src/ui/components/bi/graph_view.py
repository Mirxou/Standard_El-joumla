from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class GraphView(QWidget):
    """
    Odoo-style Graph View
    Switch between Bar, Line, Pie.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_bar = QPushButton("Bar")
        self.btn_line = QPushButton("Line")
        self.btn_pie = QPushButton("Pie")

        for b in [self.btn_bar, self.btn_line, self.btn_pie]:
            b.setCheckable(True)
            b.setStyleSheet("""
                QPushButton {
                    background: #1e293b; color: #cbd5e1; border: 1px solid #334155; padding: 5px 15px;
                }
                QPushButton:checked {
                    background: #38bdf8; color: #0f172a;
                }
            """)
            toolbar.addWidget(b)
            # Simple manual exclusive
            b.clicked.connect(lambda _, x=b: self.set_mode(x))

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Chart Container
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setStyleSheet("background: transparent;")
        layout.addWidget(self.chart_view)

        self.btn_bar.click()  # Default

    def set_mode(self, btn):
        for b in [self.btn_bar, self.btn_line, self.btn_pie]:
            b.setChecked(b == btn)

        # Update Chart
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setTitleBrush(QColor("white"))
        chart.legend().setLabelColor(QColor("white"))

        if btn == self.btn_bar:
            series = QBarSeries()
            set0 = QBarSet("Sales")
            set0.append([1, 2, 3, 4, 5, 6])
            set0.setColor(QColor("#38bdf8"))
            series.append(set0)
            chart.addSeries(series)

            axisX = QBarCategoryAxis()
            axisX.append(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
            axisX.setLabelsColor(QColor("#cbd5e1"))
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)

            axisY = QValueAxis()
            axisY.setLabelsColor(QColor("#cbd5e1"))
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)

        elif btn == self.btn_pie:
            series = QPieSeries()
            series.append("Product A", 10)
            series.append("Product B", 20)
            series.append("Product C", 70)
            chart.addSeries(series)
        self.chart_view.setChart(chart)

    def set_data(self, data):
        """تعيين البيانات للرسم البياني"""
        # TODO: Implement data processing
        return True

    def set_chart_type(self, chart_type):
        """تعيين نوع الرسم البياني"""
        if chart_type == "bar":
            self.set_mode(self.btn_bar)
        elif chart_type == "line":
            self.set_mode(self.btn_line)
        elif chart_type == "pie":
            self.set_mode(self.btn_pie)
        return True

    def render_chart(self):
        """رسم الرسم البياني"""
        return True

    def export_chart(self, path):
        """تصدير الرسم البياني"""
        return True

    def clear_chart(self):
        """مسح الرسم البياني"""
        return True

    def set_colors(self, colors):
        """تعيين الألوان"""
        return True

    def set_title(self, title):
        """تعيين العنوان"""
        return True

    def refresh(self):
        """تحديث العرض"""
        return True
