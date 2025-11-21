"""
Reorder Recommendations Window - نافذة توصيات إعادة الطلب
عرض توصيات ذكية لإعادة طلب المنتجات
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QComboBox, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from typing import List
from decimal import Decimal
from datetime import datetime

from ...core.database_manager import DatabaseManager
from ...services.inventory_optimization_service import InventoryOptimizationService
from ...models.inventory_optimization import ReorderRecommendation


class ReorderRecommendationsWindow(QWidget):
    """نافذة توصيات إعادة الطلب"""
    
    # إشارات
    create_purchase_order = Signal(int, float)  # product_id, quantity
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = InventoryOptimizationService(db_manager)
        self.recommendations: List[ReorderRecommendation] = []
        
        self.setWindowTitle("توصيات إعادة الطلب")
        self.setMinimumSize(1400, 700)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("توصيات إعادة الطلب الذكية")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # أدوات التحكم
        controls = self.create_controls_section()
        layout.addWidget(controls)
        
        # الملخص
        summary = self.create_summary_section()
        layout.addWidget(summary)
        
        # جدول التوصيات
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "الأولوية", "الإلحاح", "كود المنتج", "اسم المنتج",
            "المخزون الحالي", "نقطة إعادة الطلب", "المخزون الآمن",
            "الكمية المقترحة", "متوسط الطلب اليومي", "أيام حتى النفاد",
            "تاريخ النفاد المتوقع", "الأسباب", "الحالة", "إجراءات"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.table)
    
    def create_controls_section(self) -> QGroupBox:
        """قسم أدوات التحكم"""
        group = QGroupBox("أدوات التحكم والفلاتر")
        layout = QHBoxLayout()
        
        # فلتر الإلحاح
        layout.addWidget(QLabel("تصفية حسب الإلحاح:"))
        self.urgency_filter = QComboBox()
        self.urgency_filter.addItem("الكل", None)
        self.urgency_filter.addItem("🔴 عاجل", "URGENT")
        self.urgency_filter.addItem("🟠 مرتفع", "HIGH")
        self.urgency_filter.addItem("🟡 متوسط", "MEDIUM")
        self.urgency_filter.addItem("🟢 منخفض", "LOW")
        self.urgency_filter.currentIndexChanged.connect(self.apply_filters)
        layout.addWidget(self.urgency_filter)
        
        # فلتر الأولوية
        layout.addWidget(QLabel("الأولوية:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("الكل", None)
        self.priority_filter.addItem("أولوية 5 (الأعلى)", 5)
        self.priority_filter.addItem("أولوية 4", 4)
        self.priority_filter.addItem("أولوية 3", 3)
        self.priority_filter.addItem("أولوية 2", 2)
        self.priority_filter.addItem("أولوية 1", 1)
        self.priority_filter.currentIndexChanged.connect(self.apply_filters)
        layout.addWidget(self.priority_filter)
        
        layout.addStretch()
        
        # الأزرار
        refresh_btn = QPushButton("🔄 تحديث التوصيات")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        
        create_all_btn = QPushButton("📝 إنشاء أوامر للكل")
        create_all_btn.setToolTip("إنشاء أوامر شراء لجميع التوصيات")
        create_all_btn.clicked.connect(self.create_all_purchase_orders)
        layout.addWidget(create_all_btn)
        
        group.setLayout(layout)
        return group
    
    def create_summary_section(self) -> QGroupBox:
        """قسم الملخص"""
        group = QGroupBox("ملخص التوصيات")
        layout = QHBoxLayout()
        
        self.summary_labels = {}
        
        items = [
            ("total", "إجمالي التوصيات", QColor(200, 230, 255)),
            ("urgent", "عاجل", QColor(255, 180, 180)),
            ("high", "مرتفع", QColor(255, 220, 200)),
            ("medium", "متوسط", QColor(255, 255, 200)),
            ("low", "منخفض", QColor(200, 255, 200)),
            ("estimated_cost", "التكلفة المقدرة", QColor(220, 220, 255))
        ]
        
        for key, label, color in items:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 5, 10, 5)
            
            title_label = QLabel(label)
            title_label.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(title_label)
            
            count_label = QLabel("0")
            count_label.setFont(QFont("Arial", 14, QFont.Bold))
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setStyleSheet(f"background-color: {color.name()}; padding: 5px; border-radius: 5px;")
            self.summary_labels[key] = count_label
            container_layout.addWidget(count_label)
            
            layout.addWidget(container)
        
        group.setLayout(layout)
        return group
    
    def load_data(self):
        """تحميل البيانات"""
        try:
            # إنشاء التوصيات
            self.recommendations = self.service.generate_reorder_recommendations()
            
            # ملء الجدول
            self.populate_table()
            
            # تحديث الملخص
            self.update_summary()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل التوصيات:\n{str(e)}")
    
    def populate_table(self):
        """ملء الجدول"""
        self.table.setRowCount(len(self.recommendations))
        
        for row, rec in enumerate(self.recommendations):
            # الأولوية
            priority_item = QTableWidgetItem(str(rec.priority))
            priority_color = self.get_priority_color(rec.priority)
            priority_item.setBackground(priority_color)
            priority_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.table.setItem(row, 0, priority_item)
            
            # الإلحاح
            urgency_item = QTableWidgetItem(self.get_urgency_label(rec.urgency))
            urgency_color = self.get_urgency_color(rec.urgency)
            urgency_item.setBackground(urgency_color)
            self.table.setItem(row, 1, urgency_item)
            
            # معلومات المنتج
            self.table.setItem(row, 2, QTableWidgetItem(rec.product_code))
            self.table.setItem(row, 3, QTableWidgetItem(rec.product_name))
            
            # معلومات المخزون
            current_item = QTableWidgetItem(f"{rec.current_stock:,.2f}")
            if rec.current_stock <= 0:
                current_item.setBackground(QColor(255, 100, 100))
            self.table.setItem(row, 4, current_item)
            
            self.table.setItem(row, 5, QTableWidgetItem(f"{rec.reorder_point:,.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{rec.safety_stock:,.2f}"))
            
            # الكمية المقترحة
            suggested_item = QTableWidgetItem(f"{rec.suggested_order_quantity:,.2f}")
            suggested_item.setFont(QFont("Arial", 10, QFont.Bold))
            suggested_item.setBackground(QColor(200, 255, 200))
            self.table.setItem(row, 7, suggested_item)
            
            # معلومات الطلب
            self.table.setItem(row, 8, QTableWidgetItem(f"{rec.average_daily_demand:,.2f}"))
            
            # أيام حتى النفاد
            days_item = QTableWidgetItem(str(rec.days_until_stockout) if rec.days_until_stockout else "N/A")
            if rec.days_until_stockout:
                if rec.days_until_stockout <= 3:
                    days_item.setBackground(QColor(255, 100, 100))
                elif rec.days_until_stockout <= 7:
                    days_item.setBackground(QColor(255, 200, 100))
            self.table.setItem(row, 9, days_item)
            
            # تاريخ النفاد المتوقع
            stockout_date = "N/A"
            if rec.estimated_stockout_date:
                if isinstance(rec.estimated_stockout_date, str):
                    stockout_date = rec.estimated_stockout_date
                else:
                    stockout_date = rec.estimated_stockout_date.strftime("%Y-%m-%d")
            self.table.setItem(row, 10, QTableWidgetItem(stockout_date))
            
            # الأسباب
            reasons_text = "\n".join(rec.reasons) if rec.reasons else ""
            self.table.setItem(row, 11, QTableWidgetItem(reasons_text))
            
            # الحالة
            status_item = QTableWidgetItem(rec.reorder_status_label)
            status_color = self.get_status_color(rec.reorder_status)
            status_item.setBackground(status_color)
            self.table.setItem(row, 12, status_item)
            
            # زر الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            create_po_btn = QPushButton("📝 أمر شراء")
            create_po_btn.setToolTip("إنشاء أمر شراء لهذا المنتج")
            create_po_btn.clicked.connect(lambda checked, r=rec: self.create_single_purchase_order(r))
            actions_layout.addWidget(create_po_btn)
            
            self.table.setCellWidget(row, 13, actions_widget)
    
    def update_summary(self):
        """تحديث الملخص"""
        total = len(self.recommendations)
        urgent = sum(1 for r in self.recommendations if r.urgency == "URGENT")
        high = sum(1 for r in self.recommendations if r.urgency == "HIGH")
        medium = sum(1 for r in self.recommendations if r.urgency == "MEDIUM")
        low = sum(1 for r in self.recommendations if r.urgency == "LOW")
        
        # حساب التكلفة المقدرة
        estimated_cost = Decimal('0')
        for rec in self.recommendations:
            if rec.estimated_order_cost:
                estimated_cost += rec.estimated_order_cost
        
        self.summary_labels['total'].setText(str(total))
        self.summary_labels['urgent'].setText(str(urgent))
        self.summary_labels['high'].setText(str(high))
        self.summary_labels['medium'].setText(str(medium))
        self.summary_labels['low'].setText(str(low))
        self.summary_labels['estimated_cost'].setText(f"{estimated_cost:,.2f} ريال")
    
    def apply_filters(self):
        """تطبيق الفلاتر"""
        urgency = self.urgency_filter.currentData()
        priority = self.priority_filter.currentData()
        
        for row in range(self.table.rowCount()):
            show = True
            
            # فلتر الإلحاح
            if urgency:
                urgency_item = self.table.item(row, 1)
                if urgency_item and urgency not in urgency_item.text():
                    show = False
            
            # فلتر الأولوية
            if priority and show:
                priority_item = self.table.item(row, 0)
                if priority_item and int(priority_item.text()) != priority:
                    show = False
            
            self.table.setRowHidden(row, not show)
    
    def create_single_purchase_order(self, recommendation: ReorderRecommendation):
        """إنشاء أمر شراء لتوصية واحدة"""
        reply = QMessageBox.question(
            self,
            "إنشاء أمر شراء",
            f"المنتج: {recommendation.product_name}\n"
            f"الكمية المقترحة: {recommendation.suggested_order_quantity:,.2f}\n"
            f"التكلفة المقدرة: {recommendation.estimated_order_cost:,.2f} ريال\n\n"
            "هل تريد إنشاء أمر شراء؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # إصدار إشارة لإنشاء أمر شراء
            self.create_purchase_order.emit(
                recommendation.product_id,
                float(recommendation.suggested_order_quantity)
            )
            
            QMessageBox.information(
                self,
                "نجح",
                "سيتم فتح نافذة أمر الشراء\n"
                f"المنتج: {recommendation.product_name}\n"
                f"الكمية: {recommendation.suggested_order_quantity:,.2f}"
            )
    
    def create_all_purchase_orders(self):
        """إنشاء أوامر شراء لجميع التوصيات"""
        if not self.recommendations:
            QMessageBox.information(self, "معلومة", "لا توجد توصيات حالياً")
            return
        
        reply = QMessageBox.question(
            self,
            "إنشاء أوامر شراء",
            f"سيتم إنشاء {len(self.recommendations)} أمر شراء\n"
            f"التكلفة الإجمالية المقدرة: {sum(r.estimated_order_cost or Decimal('0') for r in self.recommendations):,.2f} ريال\n\n"
            "هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "معلومة",
                "سيتم إضافة وظيفة إنشاء أوامر شراء متعددة في التحديث القادم"
            )
    
    def get_priority_color(self, priority: int) -> QColor:
        """الحصول على لون الأولوية"""
        colors = {
            5: QColor(255, 100, 100),  # أحمر
            4: QColor(255, 180, 180),  # أحمر فاتح
            3: QColor(255, 220, 200),  # برتقالي
            2: QColor(255, 255, 200),  # أصفر
            1: QColor(200, 255, 200)   # أخضر
        }
        return colors.get(priority, QColor(255, 255, 255))
    
    def get_urgency_label(self, urgency: str) -> str:
        """الحصول على تسمية الإلحاح"""
        labels = {
            "URGENT": "🔴 عاجل",
            "HIGH": "🟠 مرتفع",
            "MEDIUM": "🟡 متوسط",
            "LOW": "🟢 منخفض"
        }
        return labels.get(urgency, urgency)
    
    def get_urgency_color(self, urgency: str) -> QColor:
        """الحصول على لون الإلحاح"""
        colors = {
            "URGENT": QColor(255, 100, 100),
            "HIGH": QColor(255, 200, 100),
            "MEDIUM": QColor(255, 255, 200),
            "LOW": QColor(200, 255, 200)
        }
        return colors.get(urgency, QColor(255, 255, 255))
    
    def get_status_color(self, status: str) -> QColor:
        """الحصول على لون الحالة"""
        from ...models.inventory_optimization import ReorderStatus
        
        colors = {
            ReorderStatus.NORMAL.value: QColor(200, 255, 200),
            ReorderStatus.APPROACHING_REORDER.value: QColor(255, 255, 200),
            ReorderStatus.REORDER_NEEDED.value: QColor(255, 220, 200),
            ReorderStatus.CRITICAL.value: QColor(255, 180, 180),
            ReorderStatus.STOCKOUT.value: QColor(255, 100, 100)
        }
        return colors.get(status, QColor(255, 255, 255))
