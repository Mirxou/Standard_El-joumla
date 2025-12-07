# -*- coding: utf-8 -*-

"""
⚠️ DEPRECATED - هذا الملف مهمل وغير مستخدم في التطبيق الحالي

The Ultimate Wholesale Invoice Interface
Designed by the Lead Product Designer for a World-Class SaaS ERP.

This interface implements the "Three-Zone Enterprise Layout" for high-volume B2B trading,
focusing on speed, information density, and data visibility.

- Zone 1: The Intelligent Header (Customer Context)
- Zone 2: The Power Grid (Product Table)
- Zone 3: The Footer & Logistics (Bottom Panel)

⚠️ تحذير: لا تستخدم هذا الملف في الكود الإنتاجي!
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QTableWidget, QHeaderView, QPushButton,
    QTableWidgetItem, QSpacerItem, QSizePolicy, QComboBox, QTextEdit,
    QMessageBox
)
from PySide6.QtGui import QIcon, Qt, QCursor
from PySide6.QtCore import QSize, Signal

class InsightCard(QFrame):
    """A small card for displaying live customer insights in the header."""
    def __init__(self, title, value, icon_path=None):
        super().__init__()
        self.setObjectName("InsightCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icon (Optional)
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(18, 18)))
            layout.addWidget(icon_label)

        title_label = QLabel(f"{title}:")
        title_label.setObjectName("InsightTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("InsightValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value, style_class=""):
        self.value_label.setText(value)
        self.value_label.setProperty("class", style_class)
        # Re-polish to apply new style property
        self.style().unpolish(self.value_label)
        self.style().polish(self.value_label)

class WholesaleInvoiceWindow(QDialog):
    """
    ⚠️ DEPRECATED - هذا الكلاس مهمل وغير مستخدم
    
    واجهة فاتورة الجملة
    
    ⚠️ ملاحظة: تم استبدال هذا الكلاس بـ `SalesDialog` في `src/ui/dialogs/sales_dialog.py`
    `SalesDialog` يستخدم نفس التصميم (3-Zone Enterprise Layout) مع تحسينات.
    لا تستخدم هذا الكلاس في الكود الإنتاجي!
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wholesale Invoice - B2B Trading")
        self.setMinimumSize(1400, 900)

        self.admin_mode = True # To show/hide margin column

        self._setup_ui()
        self._setup_styles()
        self._populate_dummy_data()

    def _setup_ui(self):
        """Builds the main 3-zone layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === ZONE 1: The Intelligent Header ===
        header_frame = self._create_zone1_header()
        main_layout.addWidget(header_frame)

        # === ZONE 2: The Power Grid ===
        grid_frame = self._create_zone2_power_grid()
        main_layout.addWidget(grid_frame, 1) # Make the grid stretch

        # === ZONE 3: The Footer & Logistics ===
        footer_frame = self._create_zone3_footer()
        main_layout.addWidget(footer_frame)

    def _create_zone1_header(self):
        """Creates the top bar with customer context."""
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(15)

        # Top row: Customer Selection
        customer_selection_layout = QHBoxLayout()
        customer_label = QLabel("Customer:")
        customer_label.setStyleSheet("font-weight: 600; color: #1E293B; font-size: 14px; min-width: 80px;")
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setPlaceholderText("Select or search for a customer...")
        self.customer_combo.addItems(["Global Imports Inc.", "MegaCorp Logistics", "Retail Kings LLC"])
        self.customer_combo.setMinimumHeight(45)
        customer_selection_layout.addWidget(customer_label)
        customer_selection_layout.addWidget(self.customer_combo, 1)

        # Bottom row: Live Insight Cards
        insights_layout = QHBoxLayout()
        insights_layout.setSpacing(12)
        self.card_credit = InsightCard("💳 Credit Limit", "$5,000 / $20,000")
        self.card_balance = InsightCard("💰 Current Balance", "$1,250.75")
        self.card_tier = InsightCard("🏷️ Price Tier", "Wholesale Level 2")
        
        shipping_label = QLabel("📍 Shipping To:")
        shipping_label.setStyleSheet("font-weight: 500; color: #64748B; font-size: 13px;")
        self.shipping_address_combo = QComboBox()
        self.shipping_address_combo.addItems(["Main Warehouse, 123 Industrial Ave", "Downtown Branch, 456 Market St"])
        self.shipping_address_combo.setFixedWidth(350)
        self.shipping_address_combo.setMinimumHeight(40)

        insights_layout.addWidget(self.card_credit)
        insights_layout.addWidget(self.card_balance)
        insights_layout.addWidget(self.card_tier)
        insights_layout.addStretch()
        insights_layout.addWidget(shipping_label)
        insights_layout.addWidget(self.shipping_address_combo)

        header_layout.addLayout(customer_selection_layout)
        header_layout.addLayout(insights_layout)
        return header_frame

    def _create_zone2_power_grid(self):
        """Creates the main product table."""
        grid_container = QFrame()
        grid_container.setObjectName("GridContainer")
        layout = QVBoxLayout(grid_container)
        layout.setContentsMargins(20, 20, 20, 20)

        self.product_table = QTableWidget()
        self.product_table.setObjectName("PowerGrid")
        
        columns = ["#", "Product Info", "Stock", "Unit", "Quantity", "Unit Price", "Discount %", "Net Price", "Margin %", "Total", ""]
        self.product_table.setColumnCount(len(columns))
        self.product_table.setHorizontalHeaderLabels(columns)

        # Column sizing strategy for high-density
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.product_table.setColumnWidth(0, 40)
        self.product_table.setColumnWidth(2, 80)
        self.product_table.setColumnWidth(3, 120)
        self.product_table.setColumnWidth(4, 80)
        self.product_table.setColumnHidden(8, not self.admin_mode) # Hide Margin for non-admins
        self.product_table.setColumnWidth(10, 40)

        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.product_table)
        return grid_container

    def _create_zone3_footer(self):
        """Creates the bottom panel with logistics and financials."""
        footer_frame = QFrame()
        footer_frame.setObjectName("FooterFrame")
        layout = QHBoxLayout(footer_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left Side: Logistics
        logistics_frame = QFrame()
        logistics_layout = QVBoxLayout(logistics_frame)
        logistics_layout.setContentsMargins(0,0,0,0)
        logistics_layout.setSpacing(10)

        logistics_title = QLabel("Logistics & Shipping")
        logistics_title.setStyleSheet("font-weight: 600; color: #1E293B; font-size: 14px; margin-bottom: 5px;")
        logistics_layout.addWidget(logistics_title)

        logistics_fields_layout = QHBoxLayout()
        logistics_fields_layout.setSpacing(10)
        self.po_number_input = QLineEdit()
        self.po_number_input.setPlaceholderText("PO Number")
        self.driver_name_input = QLineEdit()
        self.driver_name_input.setPlaceholderText("Driver Name")
        logistics_fields_layout.addWidget(self.po_number_input)
        logistics_fields_layout.addWidget(self.driver_name_input)

        self.shipping_method_combo = QComboBox()
        self.shipping_method_combo.addItems(["Internal Fleet", "FedEx Ground", "Customer Pickup"])

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Internal notes for logistics team...")
        self.notes_input.setFixedHeight(80)

        logistics_layout.addLayout(logistics_fields_layout)
        logistics_layout.addWidget(self.shipping_method_combo)
        logistics_layout.addWidget(self.notes_input)

        # Right Side: Financials
        financials_frame = QFrame()
        financials_frame.setObjectName("FinancialsFrame")
        financials_layout = QVBoxLayout(financials_frame)
        financials_layout.setContentsMargins(20,20,20,20)
        financials_layout.setSpacing(15)

        financials_layout.addWidget(self._create_summary_row("Subtotal", "145,800.00"))
        financials_layout.addWidget(self._create_summary_row("Bulk Discount (5%)", "-7,290.00", "discount"))
        financials_layout.addWidget(self._create_summary_row("VAT (19%)", "26,316.90"))
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("Divider")
        financials_layout.addWidget(line)

        final_total_layout = QHBoxLayout()
        final_total_title = QLabel("FINAL TOTAL")
        final_total_title.setObjectName("FinalTotalTitle")
        final_total_value = QLabel("164,826.90")
        final_total_value.setObjectName("FinalTotalValue")
        final_total_layout.addWidget(final_total_title)
        final_total_layout.addStretch()
        final_total_layout.addWidget(final_total_value)
        financials_layout.addLayout(final_total_layout)

        self.payment_terms_combo = QComboBox()
        self.payment_terms_combo.addItems(["Payment Terms: Net 30", "Payment Terms: Net 15", "Cash on Delivery"])
        financials_layout.addWidget(self.payment_terms_combo)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setSpacing(10)
        self.btn_print = QPushButton("Save & Print")
        self.btn_print.setObjectName("PrimaryButton")
        self.btn_print.setMinimumHeight(50)
        self.btn_save = QPushButton("Save as Draft")
        self.btn_save.setObjectName("SecondaryButton")
        self.btn_save.setMinimumHeight(50)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_save)
        action_buttons_layout.addWidget(self.btn_print)
        
        layout.addWidget(logistics_frame, 1)
        layout.addWidget(financials_frame)
        layout.addLayout(action_buttons_layout)

        return footer_frame

    def _create_summary_row(self, title, value, style_class=""):
        """Helper to create a row in the financial summary."""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0,0,0,0)
        title_label = QLabel(title)
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        value_label.setProperty("class", style_class)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return row

    def _add_product_row(self, data):
        """Adds a product row to the power grid."""
        row_idx = self.product_table.rowCount()
        self.product_table.insertRow(row_idx)

        # Column 0: #
        self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))

        # Column 1: Product Info (Name + SKU)
        product_info_widget = QWidget()
        product_layout = QVBoxLayout(product_info_widget)
        product_layout.setContentsMargins(5,5,5,5)
        product_layout.addWidget(QLabel(data['name']))
        sku_label = QLabel(f"SKU: {data['sku']}")
        sku_label.setObjectName("SkuLabel")
        product_layout.addWidget(sku_label)
        self.product_table.setCellWidget(row_idx, 1, product_info_widget)

        # Column 2: Stock
        self.product_table.setItem(row_idx, 2, QTableWidgetItem(str(data['stock'])))

        # Column 3: Unit (Dropdown)
        unit_combo = QComboBox()
        unit_combo.addItems(["Pcs", "Box (12 Pcs)", "Carton (48 Pcs)"])
        self.product_table.setCellWidget(row_idx, 3, unit_combo)

        # Column 4: Quantity
        self.product_table.setItem(row_idx, 4, QTableWidgetItem(str(data['qty'])))

        # Column 5: Unit Price
        self.product_table.setItem(row_idx, 5, QTableWidgetItem(f"{data['unit_price']:.2f}"))

        # Column 6: Discount %
        self.product_table.setItem(row_idx, 6, QTableWidgetItem(str(data['discount'])))

        # Column 7: Net Price
        self.product_table.setItem(row_idx, 7, QTableWidgetItem(f"{data['net_price']:.2f}"))

        # Column 8: Margin %
        margin_item = QTableWidgetItem(f"{data['margin']:.1f}%")
        margin_item.setForeground(Qt.GlobalColor.darkGreen if data['margin'] > 15 else Qt.GlobalColor.darkRed)
        self.product_table.setItem(row_idx, 8, margin_item)

        # Column 9: Total
        total_item = QTableWidgetItem(f"{data['total']:.2f}")
        total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.product_table.setItem(row_idx, 9, total_item)

        # Column 10: Actions (Delete Button)
        delete_button = QPushButton("🗑️")
        delete_button.setObjectName("DeleteButton")
        delete_button.setToolTip("Delete this item")
        delete_button.setFixedSize(30, 30)
        delete_button.clicked.connect(lambda checked, r=row_idx: self._delete_product_row(r))
        self.product_table.setCellWidget(row_idx, 10, delete_button)

        self.product_table.resizeRowToContents(row_idx)

    def _populate_dummy_data(self):
        """Fills the UI with sample wholesale data."""
        # Set insight card values
        self.card_credit.set_value("$5,000 / $20,000", "ok")
        self.card_balance.set_value("$1,250.75", "warn")

        # Populate product grid
        products = [
            {'name': 'Industrial Grade Server Rack (24U)', 'sku': 'SR-24U-IND', 'stock': 15, 'unit': 'Pcs', 'qty': 2, 'unit_price': 45000.00, 'discount': 10, 'net_price': 40500.00, 'margin': 22.5, 'total': 81000.00},
            {'name': 'Bulk Ethernet Cable CAT6 (305m)', 'sku': 'ETH-C6-305M', 'stock': 250, 'unit': 'Box', 'qty': 10, 'unit_price': 6000.00, 'discount': 0, 'net_price': 6000.00, 'margin': 35.0, 'total': 60000.00},
            {'name': 'Power Distribution Unit (PDU)', 'sku': 'PDU-16A-C13', 'stock': 88, 'unit': 'Pcs', 'qty': 5, 'unit_price': 960.00, 'discount': 0, 'net_price': 960.00, 'margin': 12.0, 'total': 4800.00},
        ]
        for p in products:
            self._add_product_row(p)
    
    def _delete_product_row(self, row_idx):
        """Delete a product row from the table."""
        if 0 <= row_idx < self.product_table.rowCount():
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                "Are you sure you want to remove this item?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.product_table.removeRow(row_idx)
                # Recalculate totals here if needed

    def _setup_styles(self):
        """Applies the enterprise QSS stylesheet."""
        self.setStyleSheet("""
            WholesaleInvoiceWindow {
                background-color: #F8FAFC;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
            /* --- Zone 1: Header --- */
            #HeaderFrame {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
            QComboBox {
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 15px;
                background-color: #FFFFFF;
                font-size: 14px;
                color: #1E293B;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
            QComboBox:editable {
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748B;
                width: 0;
                height: 0;
            }
            #InsightCard {
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                background-color: #FFFFFF;
                min-width: 180px;
            }
            #InsightTitle { 
                font-weight: 500; 
                color: #64748B; 
                font-size: 12px;
            }
            #InsightValue { 
                font-weight: 700; 
                color: #1E293B; 
                font-size: 14px;
            }
            #InsightValue[class="ok"] { color: #10b981; }
            #InsightValue[class="warn"] { color: #f59e0b; }
            #InsightValue[class="danger"] { color: #ef4444; }

            /* --- Zone 2: Power Grid --- */
            #GridContainer {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E2E8F0;
            }
            #PowerGrid {
                border: none;
                gridline-color: transparent;
                font-size: 14px;
                background-color: #FFFFFF;
                selection-background-color: #EFF6FF;
                selection-color: #1E293B;
            }
            #PowerGrid::item { 
                padding: 10px 8px; 
                border-bottom: 1px solid #F1F5F9;
            }
            #PowerGrid::item:selected {
                background-color: #EFF6FF;
            }
            #PowerGrid::item:alternate {
                background-color: #F8FAFC;
            }
            #PowerGrid QHeaderView::section {
                background-color: #F8FAFC;
                padding: 14px 10px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: 600;
                color: #475569;
                font-size: 13px;
            }
            #SkuLabel { 
                color: #94A3B8; 
                font-size: 11px; 
                font-weight: 400;
            }

            /* --- Zone 3: Footer --- */
            #FooterFrame {
                background-color: #F8FAFC;
                padding: 0;
            }
            #FinancialsFrame {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                font-size: 14px;
            }
            #Divider { background-color: #E2E8F0; }
            #FinalTotalTitle {
                font-size: 16px;
                font-weight: 600;
                color: #475569;
            }
            #FinalTotalValue {
                font-size: 32px;
                font-weight: 800;
                color: #10b981;
                letter-spacing: -0.5px;
            }
            QLabel[class="discount"] { color: #ef4444; }

            /* --- Buttons --- */
            QPushButton {
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 16px;
            }
            #PrimaryButton {
                background-color: #3b82f6; /* Royal Blue */
                color: white;
                border: none;
            }
            #PrimaryButton:hover { background-color: #2563eb; }
            #SecondaryButton {
                background-color: white;
                color: #334155;
                border: 1px solid #CBD5E1;
            }
            #SecondaryButton:hover { background-color: #F8FAFC; }
            #DeleteButton {
                background-color: transparent;
                border: none;
                padding: 0;
            }
            #DeleteButton:hover {
                background-color: #FEF2F2; /* Light Red */
            }
""")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WholesaleInvoiceWindow()
    window.show()
    sys.exit(app.exec())
