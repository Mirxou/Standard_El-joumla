#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action Delegate - High-Performance Icon Rendering
رسم الأيقونات والأزرار بدون استخدام Widgets
"""

from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem
from PySide6.QtCore import Qt, QRect, QSize, Signal, QModelIndex, QPoint
from PySide6.QtGui import QPainter, QIcon, QColor, QPen, QBrush
from typing import Optional

# Phase 4: استخدام IconLoader الحديث
try:
    from src.ui.styles.icon_loader import get_icon_loader
    ICON_LOADER_AVAILABLE = True
except ImportError:
    ICON_LOADER_AVAILABLE = False
    get_icon_loader = None


class ActionDelegate(QStyledItemDelegate):
    """
    Delegate عالي الأداء لرسم أزرار الإجراءات (Edit/Delete)
    يستخدم QPainter للرسم مباشرة (بدون Widgets) للحفاظ على 60 FPS
    """
    
    # إشارات للإجراءات
    edit_clicked = Signal(QModelIndex)
    delete_clicked = Signal(QModelIndex)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered_icon = None  # أيقونة عند hover
        self._icon_size = QSize(20, 20)  # حجم الأيقونة
        self._spacing = 12  # المسافة بين الأيقونات (زيادة للوضوح)
        self._padding = 4  # المسافة من الحواف
        
        # ألوان الأيقونات (محسّنة للتباين العالي)
        self._edit_color = "#3b82f6"  # Royal Blue - تباين ممتاز
        self._delete_color = "#ef4444"  # Red - تباين ممتاز
        self._edit_hover_color = "#2563eb"  # أزرق داكن عند hover
        self._delete_hover_color = "#dc2626"  # أحمر داكن عند hover
        
        # ألوان للخلفيات الداكنة (إذا لزم الأمر)
        self._edit_color_dark = "#60a5fa"  # أزرق فاتح للخلفيات الداكنة
        self._delete_color_dark = "#f87171"  # أحمر فاتح للخلفيات الداكنة
        
        # Phase 4: استخدام IconLoader الحديث
        self._icon_loader = None
        if ICON_LOADER_AVAILABLE:
            try:
                self._icon_loader = get_icon_loader()
            except Exception:
                pass
        
        # تحميل الأيقونات
        self._load_icons()
    
    def _load_icons(self):
        """تحميل الأيقونات (Phase 4: SVG Icons)"""
        if self._icon_loader:
            # استخدام أيقونات SVG الحديثة
            self._edit_icon = self._icon_loader.get_icon("edit", self._edit_color, self._icon_size.width())
            self._delete_icon = self._icon_loader.get_icon("trash", self._delete_color, self._icon_size.width())
        else:
            # Fallback: استخدام أيقونات Qt القياسية
            try:
                style = self.parent().style() if self.parent() else None
                if style:
                    self._edit_icon = style.standardIcon(QStyle.SP_FileDialogDetailedView)
                    self._delete_icon = style.standardIcon(QStyle.SP_TrashIcon)
                else:
                    self._edit_icon = None
                    self._delete_icon = None
            except Exception:
                self._edit_icon = None
                self._delete_icon = None
    
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """حجم الخلية المطلوب"""
        # عرض: أيقونتان + مسافات + padding
        width = (self._icon_size.width() * 2) + (self._spacing * 2) + (self._padding * 2)
        height = self._icon_size.height() + (self._padding * 2)
        return QSize(width, max(height, option.rect.height()))
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """
        رسم الأيقونات في الخلية
        يتم استدعاؤها فقط للخلايا المرئية (Virtual Rendering)
        
        ⚠️ CRITICAL: لا تقم بأي تحديثات للواجهة هنا (مثل update() أو repaint())
        هذا سيسبب Recursive Repaint!
        """
        # إعداد الرسم
        painter.save()
        
        try:
            # خلفية الخلية
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            elif option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, option.palette.alternateBase())
            else:
                painter.fillRect(option.rect, option.palette.base())
            
            # حساب مواقع الأيقونات (محاذاة محسّنة)
            cell_rect = option.rect
            
            # محاذاة عمودية مثالية (في المنتصف تماماً)
            icon_y = cell_rect.top() + (cell_rect.height() - self._icon_size.height()) // 2
            
            # محاذاة أفقية: توزيع متساوي في منتصف الخلية
            total_width = (self._icon_size.width() * 2) + self._spacing
            start_x = cell_rect.left() + (cell_rect.width() - total_width) // 2
            
            # موقع أيقونة التعديل (Edit) - في المنتصف تماماً
            edit_x = start_x
            edit_rect = QRect(edit_x, icon_y, self._icon_size.width(), self._icon_size.height())
            
            # موقع أيقونة الحذف (Delete) - بجانب التعديل
            delete_x = edit_x + self._icon_size.width() + self._spacing
            delete_rect = QRect(delete_x, icon_y, self._icon_size.width(), self._icon_size.height())
            
            # التحقق من Hover
            mouse_pos = option.widget.mapFromGlobal(QPoint()) if option.widget else QPoint()
            # Note: للحصول على موضع الماوس الفعلي، نحتاج إلى تمريره من View
            
            # رسم أيقونة التعديل
            self._draw_icon(
                painter, edit_rect, 
                self._edit_icon, 
                self._edit_color,
                option.state & QStyle.State_MouseOver and self._is_point_in_rect(mouse_pos, edit_rect)
            )
            
            # رسم أيقونة الحذف
            self._draw_icon(
                painter, delete_rect,
                self._delete_icon,
                self._delete_color,
                option.state & QStyle.State_MouseOver and self._is_point_in_rect(mouse_pos, delete_rect)
            )
        except Exception:
            # في حالة أي خطأ، لا نريد أن يتوقف الرسم
            pass
        finally:
            painter.restore()
    
    def _draw_icon(self, painter: QPainter, rect: QRect, icon: Optional[QIcon], 
                   color: str, is_hovered: bool = False):
        """
        رسم أيقونة واحدة (Phase 4: مع دعم Hover وتحسين التباين والمحاذاة المثالية)
        """
        painter.setRenderHint(QPainter.Antialiasing)  # تحسين الحواف
        painter.setRenderHint(QPainter.SmoothPixmapTransform)  # تحسين جودة الأيقونات
        
        if icon and not icon.isNull():
            # Phase 4: إذا كان IconLoader متاحاً، أعد تحميل الأيقونة بلون مختلف عند hover
            if self._icon_loader and is_hovered:
                # تحديد نوع الأيقونة (edit أو delete) من اللون
                if color in (self._edit_color, self._edit_color_dark):
                    hover_color = self._edit_hover_color
                    icon_name = "edit"
                elif color in (self._delete_color, self._delete_color_dark):
                    hover_color = self._delete_hover_color
                    icon_name = "trash"
                else:
                    hover_icon = icon
                    icon_name = None
                
                if icon_name:
                    hover_icon = self._icon_loader.get_icon(icon_name, hover_color, self._icon_size.width())
                else:
                    hover_icon = icon
                
                # رسم الأيقونة في المنتصف تماماً (محاذاة مثالية)
                hover_icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal)
            else:
                # استخدام الأيقونة العادية - محاذاة مثالية في المنتصف
                icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal)
        else:
            # Fallback: رسم دائرة بسيطة كبديل (مع تحسين التباين)
            # لون الأيقونة (أغمق عند hover لتحسين التباين)
            hover_color = self._edit_hover_color if is_hovered else color
            icon_color = QColor(hover_color)
            
            # تحسين التباين: استخدام stroke أكثر سماكة
            painter.setPen(QPen(icon_color, 2.5))
            painter.setBrush(QBrush(icon_color))
            
            # رسم دائرة في المنتصف تماماً (محاذاة مثالية)
            center = rect.center()
            radius = min(rect.width(), rect.height()) // 3
            painter.drawEllipse(center, radius, radius)
    
    def _is_point_in_rect(self, point: QPoint, rect: QRect) -> bool:
        """التحقق من وجود نقطة داخل مستطيل"""
        return rect.contains(point)
    
    def editorEvent(self, event, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """
        معالجة أحداث الماوس (Clicks)
        يتم استدعاؤها عند الضغط على الخلية
        
        ⚠️ CRITICAL: لا تقم بأي تحديثات للواجهة هنا (مثل update() أو repaint())
        استخدم Signals فقط لإرسال الأحداث إلى MainWindow
        """
        if event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # حساب مواقع الأيقونات
                cell_rect = option.rect
                icon_y = cell_rect.top() + (cell_rect.height() - self._icon_size.height()) // 2
                
                edit_x = cell_rect.left() + self._padding
                edit_rect = QRect(edit_x, icon_y, self._icon_size.width(), self._icon_size.height())
                
                delete_x = edit_x + self._icon_size.width() + self._spacing
                delete_rect = QRect(delete_x, icon_y, self._icon_size.width(), self._icon_size.height())
                
                # موضع الضغطة
                click_pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                
                # التحقق من أي أيقونة تم الضغط عليها
                if edit_rect.contains(click_pos):
                    self.edit_clicked.emit(index)
                    return True
                elif delete_rect.contains(click_pos):
                    self.delete_clicked.emit(index)
                    return True
        
        return super().editorEvent(event, model, option, index)
    
    def createEditor(self, parent, option: QStyleOptionViewItem, index: QModelIndex):
        """لا نريد محرر - الأيقونات فقط"""
        return None

