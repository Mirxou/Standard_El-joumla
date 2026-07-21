#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
Sales Table Model - High-Performance Model for QTableView
نموذج جدول المبيعات عالي الأداء
"""

from typing import Optional

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class SalesTableModel(QAbstractTableModel):
    """
    Model عالي الأداء لجدول المبيعات
    يستخدم Pandas DataFrame كمصدر بيانات للسرعة القصوى
    """

    def __init__(self, data: Optional[pd.DataFrame] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else pd.DataFrame()
        self._column_headers = [
            "رقم الفاتورة",
            "العميل",
            "التاريخ",
            "المبلغ الإجمالي",
            "المبلغ المدفوع",
            "المبلغ المتبقي",
            "الحالة",
            "طريقة الدفع",
            "إجراءات",
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        """عدد الصفوف"""
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        """عدد الأعمدة"""
        if parent.isValid():
            return 0
        return len(self._column_headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """
        إرجاع البيانات للخلية
        يدعم: DisplayRole, TextAlignmentRole, ForegroundRole, UserRole
        """
        if not index.isValid() or index.row() >= len(self._data):
            return None

        row = index.row()
        col = index.column()

        # DisplayRole - النص المعروض
        if role == Qt.DisplayRole:
            try:
                # Mapping الأعمدة من DataFrame إلى العناوين
                column_mapping = {
                    0: "invoice_number",  # رقم الفاتورة
                    1: "customer_name",  # العميل
                    2: "sale_date",  # التاريخ
                    3: "total_amount",  # المبلغ الإجمالي
                    4: "paid_amount",  # المبلغ المدفوع
                    5: "remaining_amount",  # المبلغ المتبقي
                    6: "status",  # الحالة
                    7: "payment_method",  # طريقة الدفع
                    8: "actions",  # إجراءات
                }

                col_name = column_mapping.get(col)
                if col_name and col_name in self._data.columns:
                    value = self._data.iloc[row][col_name]

                    # تنسيق الأرقام المالية
                    if col in (3, 4, 5):  # المبالغ المالية
                        try:
                            return f"{float(value):,.2f}" if pd.notna(value) and str(value).strip() else "0.00"
                        except (ValueError, TypeError):
                            return "0.00"
                    # تنسيق التاريخ
                    elif col == 2:  # التاريخ
                        if pd.notna(value):
                            return str(value)[:10] if len(str(value)) > 10 else str(value)
                        return "-"
                    # عمود الإجراءات (فارغ، سيتم ملؤه بـ Delegate)
                    elif col == 8:
                        return ""
                    else:
                        return str(value) if pd.notna(value) else "-"
                else:
                    return "-"
            except (IndexError, KeyError, ValueError, TypeError):
                return "-"

        # TextAlignmentRole - محاذاة النص
        elif role == Qt.TextAlignmentRole:
            if col in (0, 2, 3, 4, 5, 6, 7, 8):  # أعمدة مركزية
                return Qt.AlignCenter
            else:
                return Qt.AlignVCenter | Qt.AlignRight

        # ForegroundRole - لون النص (حسب الحالة)
        elif role == Qt.ForegroundRole:
            if col == 6:  # عمود الحالة
                try:
                    status = str(self._data.iloc[row]["status"]).lower() if "status" in self._data.columns else ""
                    if "ملغية" in status or "cancelled" in status:
                        return QColor("#e74c3c")  # أحمر - ملغاة
                    elif "مدفوعة" in status or "paid" in status:
                        return QColor("#27ae60")  # أخضر - مدفوعة
                    elif "مؤكدة" in status or "confirmed" in status:
                        return QColor("#3498db")  # أزرق - مؤكدة
                    else:
                        return QColor("#94a3b8")  # رمادي - أخرى
                except (IndexError, KeyError, ValueError, TypeError):
                    return QColor("#94a3b8")
            elif col == 5:  # المبلغ المتبقي
                try:
                    remaining = (
                        float(self._data.iloc[row]["remaining_amount"])
                        if "remaining_amount" in self._data.columns
                        and pd.notna(self._data.iloc[row]["remaining_amount"])
                        else 0
                    )
                    if remaining > 0:
                        return QColor("#e74c3c")  # أحمر - دين
                    else:
                        return QColor("#27ae60")  # أخضر - مدفوع بالكامل
                except (IndexError, ValueError, TypeError):
                    return QColor("#94a3b8")

        # UserRole - بيانات إضافية (sale_id)
        elif role == Qt.UserRole:
            if col == 0:  # في عمود رقم الفاتورة نخزن sale_id
                try:
                    return (
                        int(self._data.iloc[row]["id"])
                        if "id" in self._data.columns and pd.notna(self._data.iloc[row]["id"])
                        else None
                    )
                except (ValueError, TypeError, KeyError):
                    return None

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """إرجاع بيانات الرأس"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._column_headers):
                return self._column_headers[section]
        return None

    def setData(self, data: pd.DataFrame):
        """تحديث البيانات"""
        self.beginResetModel()
        self._data = data if data is not None else pd.DataFrame()
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """ترتيب البيانات"""
        if self._data.empty:
            return

        self.layoutAboutToBeChanged.emit()

        try:
            # Mapping الأعمدة
            column_mapping = {
                0: "invoice_number",
                1: "customer_name",
                2: "sale_date",
                3: "total_amount",
                4: "paid_amount",
                5: "remaining_amount",
                6: "status",
                7: "payment_method",
            }

            col_name = column_mapping.get(column)
            if col_name and col_name in self._data.columns:
                ascending = order == Qt.AscendingOrder
                self._data = self._data.sort_values(by=col_name, ascending=ascending).reset_index(drop=True)
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in sales_table_model.py")

        self.layoutChanged.emit()
