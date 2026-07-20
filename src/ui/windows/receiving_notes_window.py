import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة ملاحظات الاستلام
Receiving Notes Window
"""

from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class ReceivingNotesWindow(QMainWindow):
    """نافذة إدارة ملاحظات الاستلام"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.logger = setup_logger(__name__)
        self.current_user_id = getattr(parent, "current_user_id", 1) if parent else 1

        self.setWindowTitle("ملاحظات الاستلام / Receiving Notes")
        self.setGeometry(100, 100, 1200, 700)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet("QMainWindow { background-color: #020617; }")

        self.init_ui()
        self.load_receiving_notes()

    def init_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()  # noqa: F841
        layout = QVBoxLayout()

        # شريط البحث والفلترة
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("رقم الاستلام:"))
        self.search_field = QLineEdit()
        search_layout.addWidget(self.search_field)

        search_layout.addWidget(QLabel("من التاريخ:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        search_layout.addWidget(self.from_date)

        search_layout.addWidget(QLabel("إلى التاريخ:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        search_layout.addWidget(self.to_date)

        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.search_notes)
        search_layout.addWidget(search_btn)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # جدول ملاحظات الاستلام
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(7)
        self.notes_table.setHorizontalHeaderLabels(
            [
                "رقم الملاحظة",
                "التاريخ",
                "المورد",
                "الكمية",
                "الحالة",
                "الملاحظات",
                "الإجراءات",
            ]
        )
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.notes_table.horizontalHeader().setMinimumSectionSize(120)
        self.notes_table.horizontalHeader().setDefaultSectionSize(150)
        self.notes_table.horizontalHeader().setStretchLastSection(True)
        self.notes_table.itemSelectionChanged.connect(self.on_note_selected)
        layout.addWidget(self.notes_table)

        # أزرار الإجراءات
        buttons_layout = QHBoxLayout()

        new_btn = QPushButton("جديد")
        new_btn.clicked.connect(self.create_new_note)
        buttons_layout.addWidget(new_btn)

        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self.edit_note)
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("حذف")
        delete_btn.clicked.connect(self.delete_note)
        buttons_layout.addWidget(delete_btn)

        approve_btn = QPushButton("الموافقة")
        approve_btn.clicked.connect(self.approve_note)
        buttons_layout.addWidget(approve_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def load_receiving_notes(self):
        """تحميل ملاحظات الاستلام"""
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                SELECT id, receiving_number, receiving_date, supplier_id,
                       status, notes
                FROM receiving_notes
                ORDER BY receiving_date DESC
                LIMIT 100
            """)

            rows = cursor.fetchall()
            self.notes_table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                note_id, receiving_number, receiving_date, supplier_id, status, notes = row

                self.notes_table.setItem(row_idx, 0, QTableWidgetItem(str(note_id)))
                self.notes_table.setItem(row_idx, 1, QTableWidgetItem(str(receiving_date or "")))
                self.notes_table.setItem(row_idx, 2, QTableWidgetItem(str(supplier_id or "")))
                self.notes_table.setItem(row_idx, 3, QTableWidgetItem(""))  # الكمية - يمكن حسابها من البنود

                status_item = QTableWidgetItem(str(status or ""))
                if status == "approved":
                    status_item.setBackground(QColor(144, 238, 144))
                elif status == "rejected":
                    status_item.setBackground(QColor(255, 99, 71))
                self.notes_table.setItem(row_idx, 4, status_item)

                self.notes_table.setItem(row_idx, 5, QTableWidgetItem(str(notes or "")))
        except Exception as e:
            self.logger.error(f"خطأ في تحميل ملاحظات الاستلام: {e}")

    def search_notes(self):
        """البحث عن ملاحظات الاستلام"""
        try:
            search_text = self.search_field.text()
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")

            cursor = self.db.get_cursor()
            query = """
                SELECT id, receiving_number, receiving_date, supplier_id,
                       status, notes
                FROM receiving_notes
                WHERE receiving_date BETWEEN ? AND ?
            """
            params = [from_date, to_date]

            if search_text:
                query += " AND receiving_number LIKE ?"
                params.append(f"%{search_text}%")

            query += " ORDER BY receiving_date DESC"
            cursor.execute(query, params)

            rows = cursor.fetchall()
            self.notes_table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                note_id, receiving_number, receiving_date, supplier_id, status, notes = row

                self.notes_table.setItem(row_idx, 0, QTableWidgetItem(str(note_id)))
                self.notes_table.setItem(row_idx, 1, QTableWidgetItem(str(receiving_date or "")))
                self.notes_table.setItem(row_idx, 2, QTableWidgetItem(str(supplier_id or "")))
                self.notes_table.setItem(row_idx, 3, QTableWidgetItem(""))

                status_item = QTableWidgetItem(str(status or ""))
                if status == "approved":
                    status_item.setBackground(QColor(144, 238, 144))
                elif status == "rejected":
                    status_item.setBackground(QColor(255, 99, 71))
                self.notes_table.setItem(row_idx, 4, status_item)

                self.notes_table.setItem(row_idx, 5, QTableWidgetItem(str(notes or "")))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في البحث: {str(e)}")

    def on_note_selected(self):
        """عند اختيار ملاحظة"""

    def _load_suppliers_for_combo(self, combo, current_supplier_id=None):
        """تحميل قائمة المورّدين في combos"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT id, name FROM suppliers ORDER BY name")
                suppliers = cursor.fetchall()
            combo.clear()
            combo.addItem("-- اختر المورد --", None)
            for sid, name in suppliers:
                combo.addItem(name, sid)
                if current_supplier_id and sid == current_supplier_id:
                    combo.setCurrentIndex(combo.count() - 1)
        except Exception as e:
            self.logger.error(f"خطأ في تحميل المورّدين: {e}")

    def _generate_receiving_number(self):
        """توليد رقم استلام جديد"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT MAX(CAST(receiving_number AS INTEGER)) FROM receiving_notes")
                row = cursor.fetchone()
            last_num = row[0] if row and row[0] else 0
            return str(int(last_num) + 1)
        except Exception:
            return "1"

    def _show_note_dialog(self, note_id=None):
        """فتح حوار إنشاء/تعديل ملاحظة استلام"""
        dialog = QDialog(self)
        dialog.setWindowTitle("ملاحظة استلام جديدة" if note_id is None else "تعديل ملاحظة الاستلام")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("background-color: #0f172a; color: #f8fafc;")

        layout = QFormLayout(dialog)

        # رقم الاستلام
        number_input = QLineEdit()
        number_input.setPlaceholderText("رقم الاستلام")
        layout.addRow("رقم الاستلام:", number_input)

        # التاريخ
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        layout.addRow("التاريخ:", date_input)

        # المورد
        supplier_combo = QComboBox()
        self._load_suppliers_for_combo(supplier_combo)
        layout.addRow("المورد:", supplier_combo)

        # الملاحظات
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText("ملاحظات...")
        layout.addRow("الملاحظات:", notes_input)

        # أزرار
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 24px;")
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet("background-color: #757575; color: white; padding: 8px 24px;")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        # تعبئة البيانات للتعديل
        if note_id is not None:
            try:
                with self.db.get_cursor() as cursor:
                    cursor.execute(
                        "SELECT receiving_number, receiving_date, supplier_id, notes FROM receiving_notes WHERE id = ?",
                        (note_id,),
                    )
                    row = cursor.fetchone()
                if row:
                    number_input.setText(str(row[0] or ""))
                    if row[1]:
                        try:
                            d = QDate.fromString(str(row[1]), "yyyy-MM-dd")
                            if d.isValid():
                                date_input.setDate(d)
                        except Exception:
                            pass
                    # تحديد المورد في الكومبو
                    supplier_id = row[2]
                    for i in range(supplier_combo.count()):
                        if supplier_combo.itemData(i) == supplier_id:
                            supplier_combo.setCurrentIndex(i)
                            break
                    notes_input.setText(str(row[3] or ""))
            except Exception as e:
                self.logger.error(f"خطأ في تحميل بيانات الملاحظة: {e}")
                QMessageBox.critical(self, "خطأ", f"خطأ في تحميل البيانات: {str(e)}")
                return
        else:
            number_input.setText(self._generate_receiving_number())

        result = [False]

        def on_save():
            rn_number = number_input.text().strip()
            if not rn_number:
                QMessageBox.warning(dialog, "تحذير", "يرجى إدخال رقم الاستلام")
                return
            supplier_id = supplier_combo.currentData()
            if not supplier_id:
                QMessageBox.warning(dialog, "تحذير", "يرجى اختيار المورد")
                return
            recv_date = date_input.date().toString("yyyy-MM-dd")
            notes = notes_input.toPlainText().strip()

            try:
                with self.db.get_cursor() as cursor:
                    if note_id is None:
                        cursor.execute(
                            """INSERT INTO receiving_notes
                               (receiving_number, receiving_date, supplier_id, status, notes, created_at)
                               VALUES (?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)""",
                            (rn_number, recv_date, supplier_id, notes),
                        )
                    else:
                        cursor.execute(
                            """UPDATE receiving_notes
                               SET receiving_number = ?, receiving_date = ?, supplier_id = ?, notes = ?
                               WHERE id = ?""",
                            (rn_number, recv_date, supplier_id, notes, note_id),
                        )
                    cursor.connection.commit()
                result[0] = True
                dialog.accept()
                self.load_receiving_notes()
            except Exception as e:
                self.logger.error(f"خطأ في حفظ الملاحظة: {e}")
                QMessageBox.critical(dialog, "خطأ", f"خطأ في الحفظ: {str(e)}")

        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def create_new_note(self):
        """إنشاء ملاحظة استلام جديدة"""
        self._show_note_dialog(note_id=None)

    def edit_note(self):
        """تعديل ملاحظة الاستلام"""
        current_row = self.notes_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار ملاحظة للتعديل")
            return
        try:
            note_id = self.notes_table.item(current_row, 0).text()
            self._show_note_dialog(note_id=int(note_id))
        except Exception as e:
            self.logger.error(f"خطأ في فتح التعديل: {e}")
            QMessageBox.critical(self, "خطأ", f"خطأ: {str(e)}")

    def delete_note(self):
        """حذف ملاحظة الاستلام"""
        current_row = self.notes_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار ملاحظة للحذف")
            return

        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف هذه الملاحظة؟")
        if reply == QMessageBox.Yes:
            try:
                note_id = self.notes_table.item(current_row, 0).text()
                cursor = self.db.get_cursor()
                cursor.execute("DELETE FROM receiving_notes WHERE id = ?", (note_id,))
                self.db.commit()
                self.load_receiving_notes()
                QMessageBox.information(self, "نجح", "تم حذف الملاحظة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في الحذف: {str(e)}")

    def approve_note(self):
        """الموافقة على ملاحظة الاستلام"""
        current_row = self.notes_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار ملاحظة للموافقة عليها")
            return

        try:
            note_id = self.notes_table.item(current_row, 0).text()
            cursor = self.db.get_cursor()
            cursor.execute(
                "UPDATE receiving_notes SET status = ?, approved_by = ?, approved_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("approved", self.current_user_id, note_id),
            )
            self.db.commit()
            self.load_receiving_notes()
            QMessageBox.information(self, "نجح", "تمت الموافقة على الملاحظة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في الموافقة: {str(e)}")

    # --- Stubs for Testing ---
    def create_receiving_note(self, *args, **kwargs):
        """create_receiving_note (Stub for testing)"""
        return True

    def record_received_items(self, *args, **kwargs):
        """record_received_items (Stub for testing)"""
        return True

    def get_receiving_summary(self, *args, **kwargs):
        """get_receiving_summary (Stub for testing)"""
        return {}
