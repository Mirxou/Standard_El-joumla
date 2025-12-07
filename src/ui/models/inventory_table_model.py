#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inventory Table Model - High-Performance Model for QTableView
نماذج جدول المخزون عالية الأداء
"""

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor
from typing import Optional, List, Dict, Any
import pandas as pd


class InventoryTableModel(QAbstractTableModel):
    """
    Model عالي الأداء لجدول المخزون
    يستخدم Pandas DataFrame كمصدر بيانات للسرعة القصوى
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else pd.DataFrame()
        self._column_headers = [
            "المعرف", "الباركود", "اسم المنتج", "الفئة",
            "الوحدة", "الكمية الحالية", "الحد الأدنى",
            "سعر البيع", "حالة المخزون", "إجراءات"
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
                value = self._data.iloc[row, col]
                # تنسيق الأرقام
                if col == 7:  # سعر البيع
                    try:
                        return f"{float(value):,.2f}" if pd.notna(value) and str(value).strip() else "0.00"
                    except (ValueError, TypeError):
                        return "0.00"
                elif col in (5, 6):  # الكمية الحالية والحد الأدنى
                    try:
                        # معالجة آمنة للتحويل: تحقق من أن القيمة ليست string فارغ
                        if pd.notna(value) and str(value).strip():
                            return str(int(float(value)))  # تحويل إلى float أولاً ثم int
                        else:
                            return "0"
                    except (ValueError, TypeError):
                        return "0"
                else:
                    return str(value) if pd.notna(value) else "-"
            except (IndexError, KeyError, ValueError, TypeError):
                return "-"
        
        # TextAlignmentRole - محاذاة النص
        elif role == Qt.TextAlignmentRole:
            if col in (0, 5, 6, 7):  # أعمدة مركزية
                return Qt.AlignCenter
            else:
                return Qt.AlignVCenter | Qt.AlignRight
        
        # ForegroundRole - لون النص (حسب حالة المخزون)
        elif role == Qt.ForegroundRole:
            if col == 8:  # عمود حالة المخزون
                try:
                    current_stock = float(self._data.iloc[row, 5]) if pd.notna(self._data.iloc[row, 5]) else 0
                    min_stock = float(self._data.iloc[row, 6]) if pd.notna(self._data.iloc[row, 6]) else 0
                    
                    if current_stock == 0:
                        return QColor("#e74c3c")  # أحمر - نفد
                    elif current_stock <= min_stock:
                        return QColor("#f39c12")  # برتقالي - منخفض
                    else:
                        return QColor("#27ae60")  # أخضر - جيد
                except (IndexError, ValueError, TypeError):
                    return QColor("#2c3e50")  # رمادي افتراضي
        
        # UserRole - بيانات إضافية (مثل product_id)
        elif role == Qt.UserRole:
            if col == 0:  # العمود الأول يحتوي على product_id
                try:
                    return int(self._data.iloc[row, 0]) if pd.notna(self._data.iloc[row, 0]) else None
                except (IndexError, ValueError, TypeError):
                    return None
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """رؤوس الأعمدة"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if 0 <= section < len(self._column_headers):
                    return self._column_headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
    def setData(self, data: pd.DataFrame):
        """
        تحديث البيانات (High-Performance)
        يستخدم beginResetModel/endResetModel للسرعة القصوى
        ⚠️ تحذير: هذه الدالة تستبدل البيانات بالكامل!
        """
        self.beginResetModel()
        self._data = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame()
        self.endResetModel()
    
    def appendData(self, new_data: pd.DataFrame):
        """
        🔥 CRITICAL: إضافة بيانات جديدة إلى نهاية الجدول (بدون استبدال)
        يستخدم beginInsertRows/endInsertRows للحفاظ على موضع التمرير
        """
        if new_data is None or new_data.empty:
            return
        
        # التأكد من أن الأعمدة متطابقة
        if not self._data.empty:
            # التحقق من تطابق الأعمدة
            if list(new_data.columns) != list(self._data.columns):
                # محاولة إعادة ترتيب الأعمدة لتطابق البيانات الموجودة
                try:
                    new_data = new_data.reindex(columns=self._data.columns, fill_value="")
                except Exception:
                    # إذا فشل، نستخدم الأعمدة من new_data
                    pass
        
        # حساب عدد الصفوف الحالية والجديدة
        current_row_count = len(self._data)
        new_row_count = len(new_data)
        
        if new_row_count == 0:
            return
        
        # 🔥 استخدام beginInsertRows/endInsertRows لإضافة الصفوف الجديدة
        # هذا يحافظ على موضع التمرير ولا يسبب إعادة رسم كاملة
        self.beginInsertRows(QModelIndex(), current_row_count, current_row_count + new_row_count - 1)
        
        # دمج البيانات باستخدام pd.concat (بدلاً من الاستبدال)
        if self._data.empty:
            self._data = new_data.copy()
        else:
            # استخدام concat لإضافة الصفوف الجديدة
            self._data = pd.concat([self._data, new_data], ignore_index=True)
        
        self.endInsertRows()
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Sorting فوري باستخدام Pandas (أسرع من Python loops)
        """
        if self._data.empty or column >= len(self._column_headers):
            return
        
        try:
            self.layoutAboutToBeChanged.emit()
            
            # Pandas sorting - أسرع بكثير من Python loops
            ascending = (order == Qt.AscendingOrder)
            self._data = self._data.sort_values(
                by=self._data.columns[column],
                ascending=ascending,
                na_position='last'
            ).reset_index(drop=True)
            
            self.layoutChanged.emit()
        except Exception:
            # في حالة الخطأ، لا نغير البيانات
            pass
    
    def flags(self, index: QModelIndex):
        """خصائص الخلية"""
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def get_product_id(self, row: int) -> Optional[int]:
        """الحصول على product_id من صف معين"""
        try:
            if 0 <= row < len(self._data):
                return int(self._data.iloc[row, 0]) if pd.notna(self._data.iloc[row, 0]) else None
        except (IndexError, ValueError, TypeError):
            pass
        return None
    
    def get_row_data(self, row: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات صف كامل كـ dict"""
        try:
            if 0 <= row < len(self._data):
                return self._data.iloc[row].to_dict()
        except (IndexError, ValueError):
            pass
        return None

