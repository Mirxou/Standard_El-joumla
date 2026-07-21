"""
حوار تفاصيل الجرد
Count Details Dialog
"""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager


class CountDetailsDialog(BaseDialog):
    """حوار تفاصيل الجرد"""

    def __init__(self, db_manager, count_id=None, parent=None):
        super().__init__(title="", parent=parent)
        self.db = db_manager
        self.count_id = count_id
        self.count_data = None
        self.count_items = []

        # self.setWindowTitle("تفاصيل الجرد")
        # self.setGeometry(100, 100, 900, 600)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.resize(950, 650)

        self.title_text = "تفاصيل الجرد"

        self.setup_ui()

        if count_id:
            self.load_count_data()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = self.content_layout

        # معلومات الجرد
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("رقم الجرد:"))
        self.count_number_label = QLabel(str(self.count_id or "جديد"))
        info_layout.addWidget(self.count_number_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # جدول المنتجات
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(
            [
                "المنتج",
                "الرمز",
                "الكمية في النظام",
                "الكمية المحسوبة",
                "الفرق",
                "ملاحظات",
            ]
        )
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.products_table.horizontalHeader().setMinimumSectionSize(120)
        self.products_table.horizontalHeader().setDefaultSectionSize(150)
        self.products_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.products_table)

        # أزرار
        buttons_layout = QHBoxLayout()

        load_btn = QPushButton("تحميل المنتجات")
        load_btn.clicked.connect(self.load_products)
        buttons_layout.addWidget(load_btn)

        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save_count)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def load_count_data(self):
        """تحميل بيانات الجرد"""
        try:
            rows = self.db.fetch_all(
                "SELECT id, count_number, count_date, location_id, notes, status FROM physical_counts WHERE id = ?",
                (self.count_id,),
            )
            if rows:
                row = rows[0]
                self.count_data = {
                    "id": row["id"],
                    "number": row["count_number"],
                    "date": row["count_date"],
                    "location": row["location_id"],
                    "notes": row["notes"],
                    "status": row["status"],
                }
                self.count_number_label.setText(str(row["count_number"]))
                self.load_products()
        except Exception as e:
            self.notify.show_error("خطأ", f"خطأ في تحميل بيانات الجرد: {str(e)}")

    def load_products(self):
        """تحميل المنتجات المرتبطة بالجرد"""
        try:
            self.products_table.setRowCount(0)
            self.count_items = []

            if self.count_id:
                # تحميل المنتجات المسجلة
                rows = self.db.fetch_all(
                    """
                    SELECT cp.id, p.name, p.code, p.current_stock, cp.counted_quantity, cp.notes
                    FROM count_products cp
                    JOIN products p ON cp.product_id = p.id
                    WHERE cp.count_id = ?
                """,
                    (self.count_id,),
                )
            else:
                # تحميل جميع المنتجات
                rows = self.db.fetch_all("SELECT id, name, code, current_stock, 0 as counted_quantity, '' as notes FROM products LIMIT 50")

            self.products_table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                # المنتج
                self.products_table.setItem(row_idx, 0, QTableWidgetItem(str(row["name"])))
                # الرمز
                self.products_table.setItem(row_idx, 1, QTableWidgetItem(str(row["code"])))
                # الكمية في النظام
                system_qty = row["current_stock"] or 0
                self.products_table.setItem(row_idx, 2, QTableWidgetItem(str(system_qty)))
                # الكمية المحسوبة
                spinbox = QSpinBox()
                spinbox.setValue(row["counted_quantity"] or 0)
                self.products_table.setCellWidget(row_idx, 3, spinbox)
                # الفرق
                difference = (row["counted_quantity"] or 0) - system_qty
                diff_item = QTableWidgetItem(str(difference))
                if difference != 0:
                    diff_item.setBackground(QColor(255, 200, 200))
                self.products_table.setItem(row_idx, 4, diff_item)
                # الملاحظات
                self.products_table.setItem(row_idx, 5, QTableWidgetItem(str(row.get("notes") or "")))

                self.count_items.append(row["id"])
        except Exception as e:
            self.notify.show_warning("تحذير", f"خطأ في تحميل المنتجات: {str(e)}")

    def save_count(self):
        """حفظ بيانات الجرد"""
        try:
            for row_idx in range(self.products_table.rowCount()):
                # الحصول على الكمية المحسوبة من SpinBox
                spinbox = self.products_table.cellWidget(row_idx, 3)
                if spinbox:
                    counted_qty = spinbox.value()
                    notes_item = self.products_table.item(row_idx, 5)
                    notes = notes_item.text() if notes_item else ""

                    if self.count_id and row_idx < len(self.count_items):
                        # تحديث منتج موجود
                        self.db.execute_query(
                            "UPDATE count_products SET counted_quantity = ?, notes = ? WHERE id = ?",
                            (counted_qty, notes, self.count_items[row_idx]),
                        )

            self.db.execute_query("COMMIT")
            self.notify.show_success("نجاح", "تم حفظ بيانات الجرد بنجاح")
            self.accept()
        except Exception as e:
            self.notify.show_error("خطأ", f"خطأ في حفظ البيانات: {str(e)}")
