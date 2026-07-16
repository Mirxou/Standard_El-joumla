#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoice Table Model - High-Performance Editable Model for Invoice Items
نموذج جدول الفاتورة عالي الأداء مع خلايا قابلة للتعديل
"""

from decimal import Decimal, InvalidOperation
from typing import List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from ...models.sale import SaleItem

try:
    from ...utils.math_utils import to_decimal
except ImportError:
    # Fallback إذا لم يكن math_utils متوفراً
    def to_decimal(value):
        if value is None or value == "":
            return Decimal("0")
        try:
            if isinstance(value, str):
                cleaned = value.strip().replace("د.ج", "").replace("دج", "").replace(",", "").strip()
                return Decimal(cleaned) if cleaned else Decimal("0")
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")


class InvoiceTableModel(QAbstractTableModel):
    """
    Model عالي الأداء لجدول عناصر الفاتورة
    يدعم التعديل المباشر للكمية والخصم
    """

    def __init__(self, items: Optional[List[SaleItem]] = None, parent=None):
        super().__init__(parent)
        self._items = items if items is not None else []
        self._column_headers = [
            "#",
            "المنتج",
            "السعر",
            "الكمية",
            "الخصم",
            "الإجمالي",
            "حذف",
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        """عدد الصفوف"""
        if parent.isValid():
            return 0
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        """عدد الأعمدة"""
        if parent.isValid():
            return 0
        return len(self._column_headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """رؤوس الأعمدة"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section < len(self._column_headers):
                    return self._column_headers[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """إرجاع البيانات للخلية"""
        if not index.isValid() or index.row() >= len(self._items):
            return None

        row = index.row()
        col = index.column()
        item = self._items[row]

        # DisplayRole - النص المعروض
        if role == Qt.DisplayRole:
            if col == 0:  # #
                return str(row + 1)
            elif col == 1:  # المنتج
                return item.product_name
            elif col == 2:  # السعر
                return f"{item.unit_price:.2f}"
            elif col == 3:  # الكمية (قابل للتعديل)
                return str(item.quantity)
            elif col == 4:  # الخصم (قابل للتعديل)
                return f"{item.discount_amount:.2f}"
            elif col == 5:  # الإجمالي
                return f"{item.total_amount:.2f}"
            elif col == 6:  # حذف
                return "🗑️"  # أيقونة سلة مهملات

        # TextAlignmentRole - محاذاة النص
        elif role == Qt.TextAlignmentRole:
            if col == 0:  # #
                return Qt.AlignCenter
            elif col in (2, 3, 4, 5):  # أرقام
                return Qt.AlignCenter | Qt.AlignVCenter
            elif col == 6:  # حذف
                return Qt.AlignCenter
            else:
                return Qt.AlignVCenter | Qt.AlignRight

        # ForegroundRole - لون النص
        elif role == Qt.ForegroundRole:
            if col == 5:  # الإجمالي
                return QColor("#10b981")  # أخضر زمردي (Tailwind green-500)
            elif col == 6:  # حذف
                return QColor("#ef4444")  # أحمر فاتح (Tailwind red-500)

        # UserRole - إرجاع العنصر الكامل
        elif role == Qt.UserRole:
            return item

        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        """تحديث البيانات (للتعديل المباشر)"""
        if not index.isValid() or index.row() >= len(self._items):
            return False

        if role != Qt.EditRole:
            return False

        row = index.row()
        col = index.column()
        item = self._items[row]

        try:
            if col == 3:  # الكمية
                # قبول int أو string
                if isinstance(value, str):
                    quantity = int(float(value))  # تحويل آمن
                else:
                    quantity = int(value)
                if quantity < 1:
                    return False
                item.quantity = quantity
                # إعادة حساب الإجمالي
                item.total_amount = item.unit_price * item.quantity - item.discount_amount
                # إشعار التغيير للصف بالكامل
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                # إشعار تغيير الإجمالي
                total_index = self.index(row, 5)
                self.dataChanged.emit(total_index, total_index, [Qt.DisplayRole])
                return True

            elif col == 4:  # الخصم
                # تحويل آمن إلى Decimal باستخدام to_decimal
                discount = to_decimal(value)
                if discount < 0:
                    discount = Decimal("0")

                item.discount_amount = discount
                # إعادة حساب الإجمالي
                item.total_amount = item.unit_price * item.quantity - item.discount_amount
                # إشعار التغيير
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                total_index = self.index(row, 5)
                self.dataChanged.emit(total_index, total_index, [Qt.DisplayRole])
                return True

        except (ValueError, TypeError) as e:  # noqa: F841
            # تسجيل الخطأ للتحليل
            import sys

            if hasattr(sys, "stderr"):
                pass  # Error in setData
            return False
        except Exception:
            # معالجة أي خطأ آخر (مثل InvalidOperation من Decimal)
            import sys

            if hasattr(sys, "stderr"):
                pass  # Unexpected error in setData
            return False

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """تحديد الخصائص لكل خلية"""
        if not index.isValid():
            return Qt.NoItemFlags

        col = index.column()

        # الأعمدة القابلة للتعديل
        if col == 3 or col == 4:  # الكمية والخصم
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

        # الأعمدة الأخرى (قراءة فقط)
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def add_item(self, item: SaleItem):
        """إضافة عنصر جديد"""
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()

    def remove_item(self, row: int):
        """حذف عنصر"""
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            # تحديث أرقام الصفوف
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 0), [Qt.DisplayRole])

    def update_item(self, row: int, item: SaleItem):
        """تحديث عنصر موجود"""
        if 0 <= row < len(self._items):
            self._items[row] = item
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.columnCount() - 1),
                [Qt.DisplayRole],
            )

    def get_items(self) -> List[SaleItem]:
        """الحصول على جميع العناصر"""
        return self._items.copy()

    def clear(self):
        """مسح جميع العناصر"""
        if self._items:
            self.beginRemoveRows(QModelIndex(), 0, len(self._items) - 1)
            self._items.clear()
            self.endRemoveRows()

    def refresh(self):
        """تحديث الجدول بالكامل"""
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, self.columnCount() - 1),
                [Qt.DisplayRole],
            )
