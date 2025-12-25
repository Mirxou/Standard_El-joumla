#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة التنبؤات بالذكاء الاصطناعي - AI Predictions Window
واجهة شاملة للتنبؤات والتوصيات
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QTabWidget, QToolBar,
    QStatusBar, QSpinBox, QAbstractItemView, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QAction, QColor, QBrush

# إضافة مسار src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.services.ai_prediction_service import AIPredictionService
from src.utils.logger import setup_logger


class PredictionWorker(QThread):
    """عامل التنبؤ في الخلفية"""
    prediction_finished = Signal(dict)
    
    def __init__(self, ai_service: AIPredictionService, prediction_type: str, **kwargs):
        super().__init__()
        self.ai_service = ai_service
        self.prediction_type = prediction_type
        self.kwargs = kwargs
    
    def run(self):
        """تنفيذ التنبؤ"""
        try:
            if self.prediction_type == "sales":
                result = self.ai_service.forecast_sales(**self.kwargs)
            elif self.prediction_type == "demand":
                result = self.ai_service.forecast_demand(**self.kwargs)
            elif self.prediction_type == "churn":
                result = self.ai_service.predict_customer_churn(**self.kwargs)
            elif self.prediction_type == "recommendations":
                result = self.ai_service.get_product_recommendations(**self.kwargs)
            else:
                result = {"error": "نوع تنبؤ غير معروف"}
            
            self.prediction_finished.emit(result)
        except Exception as e:
            self.prediction_finished.emit({"error": str(e)})


class AIPredictionsWindow(QMainWindow):
    """نافذة التنبؤات بالذكاء الاصطناعي"""
    
    # Window Manager attributes
    window_key = "ai_predictions"
    window_singleton = True
    window_title = "🤖 التنبؤات بالذكاء الاصطناعي"
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.ai_service = AIPredictionService(db_manager, self.logger)
        
        self.setWindowTitle("التنبؤات بالذكاء الاصطناعي")
        self.setMinimumSize(1200, 800)
        
        self.prediction_worker = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # Tab Widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Tab 1: Sales Forecasting
        sales_tab = QWidget()
        sales_layout = QVBoxLayout(sales_tab)
        
        form_group = QGroupBox("إعدادات التنبؤ")
        form_layout = QFormLayout()
        
        self.sales_days_spin = QSpinBox()
        self.sales_days_spin.setMinimum(7)
        self.sales_days_spin.setMaximum(365)
        self.sales_days_spin.setValue(30)
        form_layout.addRow("عدد الأيام:", self.sales_days_spin)
        
        self.sales_product_combo = QComboBox()
        self.sales_product_combo.addItem("جميع المنتجات", None)
        # TODO: تحميل المنتجات
        form_layout.addRow("المنتج:", self.sales_product_combo)
        
        forecast_btn = QPushButton("🔮 تنبؤ المبيعات")
        forecast_btn.clicked.connect(self.forecast_sales)
        form_layout.addRow(forecast_btn)
        
        form_group.setLayout(form_layout)
        sales_layout.addWidget(form_group)
        
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            "التاريخ", "المبلغ المتوقع", "الثقة", "الحالة"
        ])
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        self.sales_table.setAlternatingRowColors(True)
        sales_layout.addWidget(self.sales_table)
        
        tab_widget.addTab(sales_tab, "📈 تنبؤات المبيعات")
        
        # Tab 2: Demand Forecasting
        demand_tab = QWidget()
        demand_layout = QVBoxLayout(demand_tab)
        
        demand_form_group = QGroupBox("إعدادات التنبؤ")
        demand_form_layout = QFormLayout()
        
        self.demand_product_combo = QComboBox()
        self.demand_product_combo.addItem("اختر منتج", None)
        # TODO: تحميل المنتجات
        demand_form_layout.addRow("المنتج:", self.demand_product_combo)
        
        self.demand_days_spin = QSpinBox()
        self.demand_days_spin.setMinimum(7)
        self.demand_days_spin.setMaximum(365)
        self.demand_days_spin.setValue(30)
        demand_form_layout.addRow("عدد الأيام:", self.demand_days_spin)
        
        demand_btn = QPushButton("🔮 تنبؤ الطلب")
        demand_btn.clicked.connect(self.forecast_demand)
        demand_form_layout.addRow(demand_btn)
        
        demand_form_group.setLayout(demand_form_layout)
        demand_layout.addWidget(demand_form_group)
        
        self.demand_table = QTableWidget()
        self.demand_table.setColumnCount(3)
        self.demand_table.setHorizontalHeaderLabels([
            "التاريخ", "الكمية المتوقعة", "الحالة"
        ])
        self.demand_table.horizontalHeader().setStretchLastSection(True)
        self.demand_table.setAlternatingRowColors(True)
        demand_layout.addWidget(self.demand_table)
        
        tab_widget.addTab(demand_tab, "📊 تنبؤات الطلب")
        
        # Tab 3: Customer Churn
        churn_tab = QWidget()
        churn_layout = QVBoxLayout(churn_tab)
        
        churn_btn = QPushButton("🔮 تحليل فقدان العملاء")
        churn_btn.clicked.connect(self.predict_churn)
        churn_layout.addWidget(churn_btn)
        
        self.churn_table = QTableWidget()
        self.churn_table.setColumnCount(5)
        self.churn_table.setHorizontalHeaderLabels([
            "العميل", "احتمالية الفقدان", "مستوى الخطر", "التنبؤ", "الحالة"
        ])
        self.churn_table.horizontalHeader().setStretchLastSection(True)
        self.churn_table.setAlternatingRowColors(True)
        churn_layout.addWidget(self.churn_table)
        
        tab_widget.addTab(churn_tab, "⚠️ فقدان العملاء")
        
        # Tab 4: Product Recommendations
        recommendations_tab = QWidget()
        recommendations_layout = QVBoxLayout(recommendations_tab)
        
        rec_form_group = QGroupBox("إعدادات التوصيات")
        rec_form_layout = QFormLayout()
        
        self.rec_type_combo = QComboBox()
        self.rec_type_combo.addItem("الأكثر شعبية", "popular")
        self.rec_type_combo.addItem("توصيات شخصية", "personalized")
        self.rec_type_combo.addItem("منتجات مشابهة", "similar")
        rec_form_layout.addRow("نوع التوصية:", self.rec_type_combo)
        
        self.rec_customer_combo = QComboBox()
        self.rec_customer_combo.addItem("جميع العملاء", None)
        # TODO: تحميل العملاء
        rec_form_layout.addRow("العميل:", self.rec_customer_combo)
        
        self.rec_product_combo = QComboBox()
        self.rec_product_combo.addItem("اختر منتج", None)
        # TODO: تحميل المنتجات
        rec_form_layout.addRow("المنتج:", self.rec_product_combo)
        
        rec_btn = QPushButton("🔮 الحصول على التوصيات")
        rec_btn.clicked.connect(self.get_recommendations)
        rec_form_layout.addRow(rec_btn)
        
        rec_form_group.setLayout(rec_form_layout)
        recommendations_layout.addWidget(rec_form_group)
        
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(4)
        self.recommendations_table.setHorizontalHeaderLabels([
            "المنتج", "السعر", "المبيعات", "الحالة"
        ])
        self.recommendations_table.horizontalHeader().setStretchLastSection(True)
        self.recommendations_table.setAlternatingRowColors(True)
        recommendations_layout.addWidget(self.recommendations_table)
        
        tab_widget.addTab(recommendations_tab, "💡 التوصيات")
        
        # Status Bar
        self.statusBar().showMessage("جاهز")
    
    def forecast_sales(self):
        """تنبؤ المبيعات"""
        days = self.sales_days_spin.value()
        product_id = self.sales_product_combo.currentData()
        
        self.statusBar().showMessage("جاري التنبؤ...")
        
        self.prediction_worker = PredictionWorker(
            self.ai_service,
            "sales",
            days_ahead=days,
            product_id=product_id
        )
        self.prediction_worker.prediction_finished.connect(self.on_sales_forecast_finished)
        self.prediction_worker.start()
    
    def on_sales_forecast_finished(self, result: Dict[str, Any]):
        """عند انتهاء تنبؤ المبيعات"""
        if result.get("error"):
            QMessageBox.critical(self, "خطأ", f"فشل التنبؤ: {result['error']}")
            self.statusBar().showMessage("فشل التنبؤ")
            return
        
        forecast = result.get("forecast", [])
        self.sales_table.setRowCount(len(forecast))
        
        for row, item in enumerate(forecast):
            date = datetime.fromisoformat(item['date']).strftime("%Y-%m-%d")
            self.sales_table.setItem(row, 0, QTableWidgetItem(date))
            self.sales_table.setItem(row, 1, QTableWidgetItem(f"{item['predicted_amount']:.2f}"))
            self.sales_table.setItem(row, 2, QTableWidgetItem(f"{item['confidence']:.1f}%"))
            
            confidence = item.get('confidence', 0)
            status_item = QTableWidgetItem("عالية" if confidence > 70 else "متوسطة" if confidence > 40 else "منخفضة")
            if confidence > 70:
                status_item.setForeground(QBrush(QColor("green")))
            elif confidence > 40:
                status_item.setForeground(QBrush(QColor("orange")))
            else:
                status_item.setForeground(QBrush(QColor("red")))
            self.sales_table.setItem(row, 3, status_item)
        
        total = result.get("total_predicted", 0)
        self.statusBar().showMessage(f"تم التنبؤ: المجموع المتوقع = {total:.2f}")
    
    def forecast_demand(self):
        """تنبؤ الطلب"""
        product_id = self.demand_product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار منتج")
            return
        
        days = self.demand_days_spin.value()
        
        self.statusBar().showMessage("جاري التنبؤ...")
        
        self.prediction_worker = PredictionWorker(
            self.ai_service,
            "demand",
            product_id=product_id,
            days_ahead=days
        )
        self.prediction_worker.prediction_finished.connect(self.on_demand_forecast_finished)
        self.prediction_worker.start()
    
    def on_demand_forecast_finished(self, result: Dict[str, Any]):
        """عند انتهاء تنبؤ الطلب"""
        if result.get("error"):
            QMessageBox.critical(self, "خطأ", f"فشل التنبؤ: {result['error']}")
            self.statusBar().showMessage("فشل التنبؤ")
            return
        
        forecast = result.get("forecast", [])
        self.demand_table.setRowCount(len(forecast))
        
        for row, item in enumerate(forecast):
            date = datetime.fromisoformat(item['date']).strftime("%Y-%m-%d")
            self.demand_table.setItem(row, 0, QTableWidgetItem(date))
            self.demand_table.setItem(row, 1, QTableWidgetItem(f"{item['predicted_quantity']:.0f}"))
            self.demand_table.setItem(row, 2, QTableWidgetItem("✓"))
        
        summary = result.get("summary", {})
        total = summary.get("total_demand", 0)
        self.statusBar().showMessage(f"تم التنبؤ: الطلب الإجمالي = {total:.0f}")
    
    def predict_churn(self):
        """تنبؤ فقدان العملاء"""
        self.statusBar().showMessage("جاري التحليل...")
        
        self.prediction_worker = PredictionWorker(
            self.ai_service,
            "churn"
        )
        self.prediction_worker.prediction_finished.connect(self.on_churn_prediction_finished)
        self.prediction_worker.start()
    
    def on_churn_prediction_finished(self, result: Dict[str, Any]):
        """عند انتهاء تنبؤ فقدان العملاء"""
        if result.get("error"):
            QMessageBox.critical(self, "خطأ", f"فشل التحليل: {result['error']}")
            self.statusBar().showMessage("فشل التحليل")
            return
        
        predictions = result.get("predictions", [])
        self.churn_table.setRowCount(len(predictions))
        
        for row, pred in enumerate(predictions):
            self.churn_table.setItem(row, 0, QTableWidgetItem(pred.get('customer_name', 'N/A')))
            self.churn_table.setItem(row, 1, QTableWidgetItem(f"{pred['churn_probability']*100:.1f}%"))
            
            risk_level = pred.get('risk_level', 'LOW')
            risk_item = QTableWidgetItem(risk_level)
            if risk_level == "HIGH":
                risk_item.setForeground(QBrush(QColor("red")))
            elif risk_level == "MEDIUM":
                risk_item.setForeground(QBrush(QColor("orange")))
            else:
                risk_item.setForeground(QBrush(QColor("green")))
            self.churn_table.setItem(row, 2, risk_item)
            
            churn_status = "نعم" if pred.get('predicted_churn') else "لا"
            self.churn_table.setItem(row, 3, QTableWidgetItem(churn_status))
            self.churn_table.setItem(row, 4, QTableWidgetItem("✓"))
        
        summary = result.get("summary", {})
        high_risk = summary.get("high_risk", 0)
        self.statusBar().showMessage(f"تم التحليل: عملاء عاليو الخطورة = {high_risk}")
    
    def get_recommendations(self):
        """الحصول على التوصيات"""
        rec_type = self.rec_type_combo.currentData()
        customer_id = self.rec_customer_combo.currentData()
        product_id = self.rec_product_combo.currentData()
        
        self.statusBar().showMessage("جاري الحصول على التوصيات...")
        
        kwargs = {"limit": 10}
        if rec_type == "personalized" and customer_id:
            kwargs["customer_id"] = customer_id
        elif rec_type == "similar" and product_id:
            kwargs["product_id"] = product_id
        
        self.prediction_worker = PredictionWorker(
            self.ai_service,
            "recommendations",
            **kwargs
        )
        self.prediction_worker.prediction_finished.connect(self.on_recommendations_finished)
        self.prediction_worker.start()
    
    def on_recommendations_finished(self, result: Dict[str, Any]):
        """عند انتهاء الحصول على التوصيات"""
        if result.get("error"):
            QMessageBox.critical(self, "خطأ", f"فشل الحصول على التوصيات: {result['error']}")
            self.statusBar().showMessage("فشل الحصول على التوصيات")
            return
        
        products = result.get("products", [])
        self.recommendations_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.recommendations_table.setItem(row, 0, QTableWidgetItem(product.get('name', 'N/A')))
            self.recommendations_table.setItem(row, 1, QTableWidgetItem(f"{product.get('price', 0):.2f}"))
            self.recommendations_table.setItem(row, 2, QTableWidgetItem(str(product.get('total_sales', 0))))
            self.recommendations_table.setItem(row, 3, QTableWidgetItem("✓"))
        
        self.statusBar().showMessage(f"تم الحصول على {len(products)} توصية")
    
    def refresh_data(self):
        """تحديث البيانات"""
        # TODO: تحديث قوائم المنتجات والعملاء
        self.statusBar().showMessage("تم التحديث")

