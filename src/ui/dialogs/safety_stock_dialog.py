"""
Safety Stock Configuration Dialog - حوار تكوين الأرصدة الآمنة
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QGroupBox, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import Optional
from decimal import Decimal

from ...core.database_manager import DatabaseManager
from ...services.inventory_optimization_service import InventoryOptimizationService
from ...services.product_service_enhanced import ProductService
from ...models.inventory_optimization import SafetyStockConfig


class SafetyStockDialog(QDialog):
    """حوار تكوين الأرصدة الآمنة"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None, config: Optional[SafetyStockConfig] = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.service = InventoryOptimizationService(db_manager)
        self.product_service = ProductService(db_manager)
        self.config = config
        
        self.setWindowTitle("تكوين الأرصدة الآمنة" if not config else "تعديل الأرصدة الآمنة")
        self.setMinimumWidth(600)
        
        self.setup_ui()
        if config:
            self.load_config_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("تكوين الأرصدة الآمنة ونقطة إعادة الطلب")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # اختيار المنتج
        product_group = self.create_product_section()
        layout.addWidget(product_group)
        
        # المعلومات الأساسية
        basic_group = self.create_basic_section()
        layout.addWidget(basic_group)
        
        # معلومات متقدمة
        advanced_group = self.create_advanced_section()
        layout.addWidget(advanced_group)
        
        # الحسابات التلقائية
        calc_group = self.create_calculations_section()
        layout.addWidget(calc_group)
        
        # الأزرار
        buttons = self.create_buttons()
        layout.addLayout(buttons)
    
    def create_product_section(self) -> QGroupBox:
        """قسم اختيار المنتج"""
        group = QGroupBox("معلومات المنتج")
        layout = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        # تحميل المنتجات
        # ProductService لا يوفّر get_all_products؛ نستخدم search_products لإرجاع جميع النشطة
        products = self.product_service.search_products("")
        for product in products:
            display_code = getattr(product, 'sku', None) or getattr(product, 'barcode', None) or "#"
            self.product_combo.addItem(
                f"{display_code} - {product.name}",
                product.id
            )
        
        layout.addRow("المنتج:", self.product_combo)
        
        self.current_stock_label = QLabel("0.00")
        self.current_stock_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addRow("المخزون الحالي:", self.current_stock_label)
        
        group.setLayout(layout)
        return group
    
    def create_basic_section(self) -> QGroupBox:
        """القسم الأساسي"""
        group = QGroupBox("الإعدادات الأساسية")
        layout = QFormLayout()
        
        # متوسط الطلب اليومي
        self.avg_demand_spin = QDoubleSpinBox()
        self.avg_demand_spin.setRange(0, 999999)
        self.avg_demand_spin.setDecimals(2)
        self.avg_demand_spin.valueChanged.connect(self.calculate_values)
        layout.addRow("متوسط الطلب اليومي:", self.avg_demand_spin)
        
        # مدة التوريد
        self.lead_time_spin = QSpinBox()
        self.lead_time_spin.setRange(1, 365)
        self.lead_time_spin.setValue(7)
        self.lead_time_spin.valueChanged.connect(self.calculate_values)
        layout.addRow("مدة التوريد (أيام):", self.lead_time_spin)
        
        # مستوى الخدمة
        self.service_level_combo = QComboBox()
        self.service_level_combo.addItem("90% (Z=1.28)", 0.90)
        self.service_level_combo.addItem("95% (Z=1.65)", 0.95)
        self.service_level_combo.addItem("98% (Z=2.05)", 0.98)
        self.service_level_combo.addItem("99% (Z=2.33)", 0.99)
        self.service_level_combo.setCurrentIndex(1)  # 95% افتراضي
        self.service_level_combo.currentIndexChanged.connect(self.calculate_values)
        layout.addRow("مستوى الخدمة:", self.service_level_combo)
        
        # الانحراف المعياري
        self.std_dev_spin = QDoubleSpinBox()
        self.std_dev_spin.setRange(0, 999999)
        self.std_dev_spin.setDecimals(2)
        self.std_dev_spin.valueChanged.connect(self.calculate_values)
        layout.addRow("الانحراف المعياري للطلب:", self.std_dev_spin)
        
        group.setLayout(layout)
        return group
    
    def create_advanced_section(self) -> QGroupBox:
        """القسم المتقدم"""
        group = QGroupBox("إعدادات متقدمة (اختياري)")
        layout = QFormLayout()
        
        # كلفة الطلب
        self.order_cost_spin = QDoubleSpinBox()
        self.order_cost_spin.setRange(0, 999999)
        self.order_cost_spin.setDecimals(2)
        self.order_cost_spin.setValue(100)
        self.order_cost_spin.valueChanged.connect(self.calculate_eoq)
        layout.addRow("كلفة الطلب (دج):", self.order_cost_spin)
        
        # كلفة الاحتفاظ
        self.holding_cost_spin = QDoubleSpinBox()
        self.holding_cost_spin.setRange(0, 100)
        self.holding_cost_spin.setDecimals(2)
        self.holding_cost_spin.setValue(20)
        self.holding_cost_spin.setSuffix("%")
        self.holding_cost_spin.valueChanged.connect(self.calculate_eoq)
        layout.addRow("كلفة الاحتفاظ (%):", self.holding_cost_spin)
        
        # سعر التكلفة
        self.unit_cost_spin = QDoubleSpinBox()
        self.unit_cost_spin.setRange(0, 999999)
        self.unit_cost_spin.setDecimals(2)
        self.unit_cost_spin.valueChanged.connect(self.calculate_eoq)
        layout.addRow("سعر التكلفة:", self.unit_cost_spin)
        
        group.setLayout(layout)
        return group
    
    def create_calculations_section(self) -> QGroupBox:
        """قسم الحسابات"""
        group = QGroupBox("النتائج المحسوبة")
        layout = QFormLayout()
        
        # نقطة إعادة الطلب
        self.reorder_point_label = QLabel("0.00")
        self.reorder_point_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.reorder_point_label.setStyleSheet("color: blue;")
        layout.addRow("نقطة إعادة الطلب:", self.reorder_point_label)
        
        # المخزون الآمن
        self.safety_stock_label = QLabel("0.00")
        self.safety_stock_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.safety_stock_label.setStyleSheet("color: green;")
        layout.addRow("المخزون الآمن:", self.safety_stock_label)
        
        # الحد الأدنى والأقصى
        self.min_stock_label = QLabel("0.00")
        layout.addRow("الحد الأدنى:", self.min_stock_label)
        
        self.max_stock_label = QLabel("0.00")
        layout.addRow("الحد الأقصى:", self.max_stock_label)
        
        # EOQ
        self.eoq_label = QLabel("0.00")
        self.eoq_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.eoq_label.setStyleSheet("color: orange;")
        layout.addRow("كمية الطلب الاقتصادية (EOQ):", self.eoq_label)
        
        # زر الحساب التلقائي
        auto_calc_btn = QPushButton("🤖 حساب تلقائي من البيانات التاريخية")
        auto_calc_btn.clicked.connect(self.auto_calculate)
        layout.addRow("", auto_calc_btn)
        
        group.setLayout(layout)
        return group
    
    def create_buttons(self) -> QHBoxLayout:
        """أزرار الحوار"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self.save_configuration)
        layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        return layout
    
    def on_product_changed(self):
        """عند تغيير المنتج"""
        product_id = self.product_combo.currentData()
        if product_id:
            product = self.product_service.get_product_by_id(product_id)
            if product:
                self.current_stock_label.setText(f"{product.quantity:,.2f}")
                # الحقول في ProductService: current_stock و cost_price
                self.current_stock_label.setText(f"{getattr(product, 'current_stock', 0):,.2f}")
                self.unit_cost_spin.setValue(float(getattr(product, 'cost_price', 0) or 0))
                
                # محاولة تحميل التكوين الموجود
                existing_config = self.service.get_safety_stock_config(product_id)
                if existing_config:
                    self.load_config_data(existing_config)
    
    def auto_calculate(self):
        """حساب تلقائي من البيانات التاريخية"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار منتج أولاً")
            return
        
        try:
            # حساب إحصائيات الطلب
            stats = self.service.calculate_demand_statistics(product_id, days=90)
            
            if stats['avg_daily_demand'] > 0:
                self.avg_demand_spin.setValue(float(stats['avg_daily_demand']))
                self.std_dev_spin.setValue(float(stats['demand_std_dev']))
                
                QMessageBox.information(
                    self,
                    "نجح",
                    f"تم حساب الإحصائيات من بيانات آخر 90 يوم:\n"
                    f"متوسط الطلب اليومي: {stats['avg_daily_demand']:.2f}\n"
                    f"الانحراف المعياري: {stats['demand_std_dev']:.2f}"
                )
                
                self.calculate_values()
            else:
                QMessageBox.information(
                    self,
                    "معلومة",
                    "لا توجد بيانات مبيعات كافية لهذا المنتج"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحساب التلقائي:\n{str(e)}")
    
    def calculate_values(self):
        """حساب القيم"""
        avg_demand = Decimal(str(self.avg_demand_spin.value()))
        lead_time = self.lead_time_spin.value()
        service_level = Decimal(str(self.service_level_combo.currentData()))
        std_dev = Decimal(str(self.std_dev_spin.value()))
        
        if avg_demand <= 0:
            return
        
        # حساب Z-score
        z_scores = {
            Decimal('0.90'): Decimal('1.28'),
            Decimal('0.95'): Decimal('1.65'),
            Decimal('0.98'): Decimal('2.05'),
            Decimal('0.99'): Decimal('2.33')
        }
        z_score = z_scores.get(service_level, Decimal('1.65'))
        
        # حساب المخزون الآمن: Safety Stock = Z × σ × √LT
        import math
        safety_stock = z_score * std_dev * Decimal(str(math.sqrt(lead_time)))
        
        # حساب نقطة إعادة الطلب: ROP = (Avg Demand × Lead Time) + Safety Stock
        reorder_point = (avg_demand * Decimal(str(lead_time))) + safety_stock
        
        # الحد الأدنى = Safety Stock
        min_stock = safety_stock
        
        # الحد الأقصى = ROP + EOQ (سنضعه لاحقاً)
        max_stock = reorder_point * Decimal('2')  # تقدير
        
        # تحديث العرض
        self.reorder_point_label.setText(f"{reorder_point:,.2f}")
        self.safety_stock_label.setText(f"{safety_stock:,.2f}")
        self.min_stock_label.setText(f"{min_stock:,.2f}")
        self.max_stock_label.setText(f"{max_stock:,.2f}")
        
        # حساب EOQ
        self.calculate_eoq()
    
    def calculate_eoq(self):
        """حساب كمية الطلب الاقتصادية"""
        avg_demand = Decimal(str(self.avg_demand_spin.value()))
        order_cost = Decimal(str(self.order_cost_spin.value()))
        holding_cost_pct = Decimal(str(self.holding_cost_spin.value())) / Decimal('100')
        unit_cost = Decimal(str(self.unit_cost_spin.value()))
        
        if avg_demand <= 0 or order_cost <= 0 or unit_cost <= 0 or holding_cost_pct <= 0:
            return
        
        # EOQ = √((2 × Annual Demand × Order Cost) / Holding Cost per Unit)
        annual_demand = avg_demand * Decimal('365')
        holding_cost_per_unit = unit_cost * holding_cost_pct
        
        import math
        try:
            eoq = Decimal(str(math.sqrt(
                float((2 * annual_demand * order_cost) / holding_cost_per_unit)
            )))
            self.eoq_label.setText(f"{eoq:,.2f}")
        except:
            self.eoq_label.setText("N/A")
    
    def load_config_data(self, config: Optional[SafetyStockConfig] = None):
        """تحميل بيانات التكوين"""
        if config is None:
            config = self.config
        
        if not config:
            return
        
        # تحديد المنتج
        index = self.product_combo.findData(config.product_id)
        if index >= 0:
            self.product_combo.setCurrentIndex(index)
        
        # تحميل القيم
        self.avg_demand_spin.setValue(float(config.average_daily_demand))
        self.lead_time_spin.setValue(config.lead_time_days)
        
        # تحديد مستوى الخدمة
        service_index = 1  # 95% افتراضي
        if config.service_level:
            sl = float(config.service_level)
            if sl >= 0.99:
                service_index = 3
            elif sl >= 0.98:
                service_index = 2
            elif sl >= 0.95:
                service_index = 1
            else:
                service_index = 0
        self.service_level_combo.setCurrentIndex(service_index)
        
        if config.demand_std_dev:
            self.std_dev_spin.setValue(float(config.demand_std_dev))
        
        if config.order_cost:
            self.order_cost_spin.setValue(float(config.order_cost))
        
        if config.holding_cost_percentage:
            self.holding_cost_spin.setValue(float(config.holding_cost_percentage))
        
        if config.unit_cost:
            self.unit_cost_spin.setValue(float(config.unit_cost))
        
        # تحديث الحسابات
        self.calculate_values()
    
    def save_configuration(self):
        """حفظ التكوين"""
        product_id = self.product_combo.currentData()
        if not product_id:
            QMessageBox.warning(self, "تحذير", "الرجاء اختيار منتج")
            return
        
        avg_demand = Decimal(str(self.avg_demand_spin.value()))
        if avg_demand <= 0:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال متوسط الطلب اليومي")
            return
        
        try:
            # إنشاء التكوين
            config_data = {
                'product_id': product_id,
                'average_daily_demand': avg_demand,
                'lead_time_days': self.lead_time_spin.value(),
                'service_level': Decimal(str(self.service_level_combo.currentData())),
                'demand_std_dev': Decimal(str(self.std_dev_spin.value())),
                'order_cost': Decimal(str(self.order_cost_spin.value())),
                'holding_cost_percentage': Decimal(str(self.holding_cost_spin.value())),
                'unit_cost': Decimal(str(self.unit_cost_spin.value()))
            }
            
            if self.config:
                # تحديث
                config_data['id'] = self.config.id
                self.service.update_safety_stock_config(**config_data)
                QMessageBox.information(self, "نجح", "تم تحديث التكوين بنجاح")
            else:
                # إنشاء جديد
                self.service.create_safety_stock_config(**config_data)
                QMessageBox.information(self, "نجح", "تم إنشاء التكوين بنجاح")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ التكوين:\n{str(e)}")
