#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern Action Delegate - Icon-Based Actions with Precise Click Detection
Delegate حديث لأيقونات الإجراءات مع كشف دقيق للنقرات
"""

from PySide6.QtWidgets import QStyledItemDelegate, QApplication, QStyle, QStyleOptionViewItem
from PySide6.QtCore import Qt, Signal, QRect, QSize, QPoint, QModelIndex, QEvent
from PySide6.QtGui import QIcon, QPainter, QColor, QCursor, QPen, QBrush
from pathlib import Path
from typing import Optional


class ModernActionDelegate(QStyledItemDelegate):
    """
    🔥 Modern Action Delegate - أيقونات حديثة مع كشف دقيق للنقرات
    
    Features:
    - SVG Icons (Edit & Delete)
    - Precise Click Detection
    - Hover Effects
    - Product ID Emission (not just row index)
    """
    
    # إشارات ترسل Product ID (وليس row index فقط)
    edit_clicked = Signal(int)  # product_id
    delete_clicked = Signal(int)  # product_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # أحجام الأيقونات
        self.icon_size = QSize(22, 22)
        self.spacing = 20  # مسافة بين الأيقونتين
        self.padding = 8  # padding من الحواف
        
        # تحميل الأيقونات
        self._load_icons()
    
    def _load_icons(self):
        """تحميل الأيقونات من ملفات SVG"""
        try:
            # البحث عن الأيقونات في مجلد assets
            project_root = Path(__file__).parent.parent.parent.parent
            edit_path = project_root / "assets" / "icons" / "edit.svg"
            delete_path = project_root / "assets" / "icons" / "trash.svg"
            
            # تحميل الأيقونات
            if edit_path.exists():
                self.edit_icon = QIcon(str(edit_path))
            else:
                # Fallback: استخدام أيقونة Qt القياسية
                style = QApplication.instance().style() if QApplication.instance() else None
                if style:
                    self.edit_icon = style.standardIcon(QStyle.SP_FileDialogDetailedView)
                else:
                    self.edit_icon = QIcon()
            
            if delete_path.exists():
                self.delete_icon = QIcon(str(delete_path))
            else:
                # Fallback: استخدام أيقونة Qt القياسية
                style = QApplication.instance().style() if QApplication.instance() else None
                if style:
                    self.delete_icon = style.standardIcon(QStyle.SP_TrashIcon)
                else:
                    self.delete_icon = QIcon()
                    
        except Exception:
            # Fallback: أيقونات فارغة
            self.edit_icon = QIcon()
            self.delete_icon = QIcon()
    
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """حجم الخلية المطلوب"""
        # عرض: أيقونتان + مسافات + padding
        width = (self.icon_size.width() * 2) + self.spacing + (self.padding * 2)
        height = self.icon_size.height() + (self.padding * 2)
        return QSize(width, max(height, option.rect.height()))
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """
        رسم الأيقونات في الخلية
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        try:
            # خلفية الخلية
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            elif option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, option.palette.alternateBase())
            
            # حساب مواقع الأيقونات
            edit_rect, delete_rect = self._get_icon_rects(option)
            
            # الحصول على موضع الماوس للتحقق من Hover
            widget = option.widget
            if widget:
                mouse_pos = widget.mapFromGlobal(QCursor.pos())
                # تحويل الإحداثيات إلى إحداثيات الخلية
                cell_mouse_pos = mouse_pos - option.rect.topLeft()
                
                # التحقق من Hover
                edit_hovered = edit_rect.contains(cell_mouse_pos)
                delete_hovered = delete_rect.contains(cell_mouse_pos)
                
                # تغيير المؤشر عند Hover
                if edit_hovered or delete_hovered:
                    widget.setCursor(Qt.PointingHandCursor)
            else:
                edit_hovered = False
                delete_hovered = False
            
            # رسم أيقونة التعديل (أزرق)
            self._draw_icon(painter, edit_rect, self.edit_icon, "#3b82f6", edit_hovered)
            
            # رسم أيقونة الحذف (أحمر)
            self._draw_icon(painter, delete_rect, self.delete_icon, "#ef4444", delete_hovered)
            
        except Exception as e:
            # في حالة أي خطأ، لا نريد أن يتوقف الرسم
            import traceback
            print(f"خطأ في رسم الأيقونات: {e}\n{traceback.format_exc()}")
        finally:
            painter.restore()
    
    def _draw_icon(self, painter: QPainter, rect: QRect, icon: QIcon, 
                   color: str, is_hovered: bool = False):
        """رسم أيقونة واحدة مع تأثير Hover"""
        if icon and not icon.isNull():
            # رسم الأيقونة
            icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal)
        else:
            # Fallback: رسم دائرة بسيطة
            icon_color = QColor(color)
            if is_hovered:
                icon_color = icon_color.darker(120)  # أغمق عند hover
            
            painter.setPen(QPen(icon_color, 2))
            painter.setBrush(QBrush(icon_color))
            center = rect.center()
            radius = min(rect.width(), rect.height()) // 3
            painter.drawEllipse(center, radius, radius)
    
    def _get_icon_rects(self, option: QStyleOptionViewItem):
        """
        حساب أماكن الأيقونات بدقة لتكون في المنتصف
        """
        cell_rect = option.rect
        
        # محاذاة عمودية (في المنتصف)
        icon_y = cell_rect.top() + (cell_rect.height() - self.icon_size.height()) // 2
        
        # محاذاة أفقية: توزيع متساوي في منتصف الخلية
        total_width = (self.icon_size.width() * 2) + self.spacing
        start_x = cell_rect.left() + (cell_rect.width() - total_width) // 2
        
        # موقع أيقونة التعديل (Edit)
        edit_x = start_x
        edit_rect = QRect(edit_x, icon_y, self.icon_size.width(), self.icon_size.height())
        
        # موقع أيقونة الحذف (Delete)
        delete_x = edit_x + self.icon_size.width() + self.spacing
        delete_rect = QRect(delete_x, icon_y, self.icon_size.width(), self.icon_size.height())
        
        return edit_rect, delete_rect
    
    def editorEvent(self, event: QEvent, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """
        🔥 CRITICAL FIX: معالجة نقرات الماوس بدقة
        
        المشكلة السابقة: كان يستخدم MouseButtonPress بدلاً من MouseButtonRelease
        الحل: استخدام MouseButtonRelease + حساب دقيق للمناطق
        """
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                # حساب مواقع الأيقونات
                edit_rect, delete_rect = self._get_icon_rects(option)
                
                # موضع الضغطة (بالنسبة للخلية)
                # 🔥 CRITICAL FIX: تحويل الإحداثيات بشكل صحيح
                if hasattr(event, 'position'):
                    click_pos = event.position().toPoint()
                elif hasattr(event, 'pos'):
                    click_pos = event.pos()
                else:
                    click_pos = QPoint(event.x(), event.y())
                
                # تحويل الإحداثيات إلى إحداثيات الخلية
                click_pos = click_pos - option.rect.topLeft()
                
                # 🔥 CRITICAL: الحصول على Product ID من Model
                # العمود 0 يحتوي على product_id
                product_id = None
                try:
                    if model:
                        product_id_index = model.index(index.row(), 0)
                        # محاولة الحصول على product_id من UserRole أولاً
                        product_id = model.data(product_id_index, Qt.UserRole)
                        if not product_id:
                            # Fallback: الحصول من DisplayRole
                            product_id_str = model.data(product_id_index, Qt.DisplayRole)
                            if product_id_str:
                                try:
                                    product_id = int(product_id_str)
                                except (ValueError, TypeError):
                                    pass
                except Exception:
                    pass
                
                # التحقق من أي أيقونة تم الضغط عليها
                if edit_rect.contains(click_pos):
                    if product_id:
                        self.edit_clicked.emit(int(product_id))
                    else:
                        # Fallback: إرسال row index
                        self.edit_clicked.emit(index.row())
                    return True
                
                elif delete_rect.contains(click_pos):
                    if product_id:
                        self.delete_clicked.emit(int(product_id))
                    else:
                        # Fallback: إرسال row index
                        self.delete_clicked.emit(index.row())
                    return True
        
        return super().editorEvent(event, model, option, index)
    
    def createEditor(self, parent, option: QStyleOptionViewItem, index: QModelIndex):
        """لا نريد محرر - الأيقونات فقط"""
        return None

