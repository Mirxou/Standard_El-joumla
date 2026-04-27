from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QBrush

class WholesaleDashboardDialog(QDialog):
    """
    لوحة قيادة الجملة (Wholesale Dashboard)
    Visualizes KPIs and Lists.
    """
    def __init__(self, analytics_service, parent=None):
        super().__init__(parent)
        self.service = analytics_service
        self.setWindowTitle("📊 لوحة قيادة الجملة")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background-color: #f4f6f9;")
        
        self.layout = QVBoxLayout(self)
        self._setup_ui()
        self._load_data()
        
    def _setup_ui(self):
        # Header
        title = QLabel("Global Analytics Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #343a40; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)
        
        # KPI Section
        self.kpi_layout = QHBoxLayout()
        self.layout.addLayout(self.kpi_layout)
        
        # Lists Section (Split View)
        lists_layout = QHBoxLayout()
        
        # Top Customers
        cust_layout = QVBoxLayout()
        cust_label = QLabel("🏆 أفضل الزبائن (Revenue)")
        cust_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        cust_layout.addWidget(cust_label)
        self.cust_table = self._create_table(["العميل", "عدد الصفقات", "إجمالي المشتريات"])
        cust_layout.addWidget(self.cust_table)
        lists_layout.addLayout(cust_layout)
        
        # Top Products
        prod_layout = QVBoxLayout()
        prod_label = QLabel("📦 المنتجات الأكثر حركة (Qty)")
        prod_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        prod_layout.addWidget(prod_label)
        self.prod_table = self._create_table(["المنتج", "الكمية المباعة", "القيمة الإجمالية"])
        prod_layout.addWidget(self.prod_table)
        lists_layout.addLayout(prod_layout)
        
        self.layout.addLayout(lists_layout)
        
        # Close Button
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton { background-color: #6c757d; color: white; padding: 10px; border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #5a6268; }
        """)
        close_btn.clicked.connect(self.reject)
        self.layout.addWidget(close_btn)

    def _create_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("background-color: white; border-radius: 8px;")
        return table

    def _create_kpi_card(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ 
                background-color: white; 
                border-left: 5px solid {color}; 
                border-radius: 8px; 
                padding: 20px;
            }}
        """)
        layout = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #6c757d; font-size: 14px;")
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return frame

    def _load_data(self):
        # KPIs
        data = self.service.get_kpi_summary()
        
        # Clear previous KPIs if reload
        # (For now just add them once)
        if self.kpi_layout.count() == 0:
            self.kpi_layout.addWidget(self._create_kpi_card("إجمالي المبيعات", f"{data['total_revenue']:,.2f}", "#0d6efd")) # Blue
            self.kpi_layout.addWidget(self._create_kpi_card("صافي الأرباح", f"{data['total_profit']:,.2f}", "#198754"))   # Green
            self.kpi_layout.addWidget(self._create_kpi_card("عدد الصفقات", str(data['deal_count']), "#fd7e14"))       # Orange

        # Top Customers
        customers = self.service.get_top_customers()
        self.cust_table.setRowCount(len(customers))
        for i, c in enumerate(customers):
            self.cust_table.setItem(i, 0, QTableWidgetItem(c['name']))
            self.cust_table.setItem(i, 1, QTableWidgetItem(str(c['count'])))
            self.cust_table.setItem(i, 2, QTableWidgetItem(f"{c['total']:,.2f}"))

        # Top Products
        products = self.service.get_top_products()
        self.prod_table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.prod_table.setItem(i, 0, QTableWidgetItem(p['name']))
            self.prod_table.setItem(i, 1, QTableWidgetItem(str(p['qty'])))
            self.prod_table.setItem(i, 2, QTableWidgetItem(f"{p['value']:,.2f}"))
