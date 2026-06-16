#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icon Loader - Modern SVG Icon System
نظام تحميل الأيقونات الحديثة (SVG)
"""

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


class IconLoader:
    """
    محمل الأيقونات الحديثة
    يدعم SVG مع إمكانية إعادة التلوين الديناميكية
    """

    # أسماء الأيقونات القياسية
    ICON_EDIT = "edit"
    ICON_DELETE = "trash"
    ICON_SAVE = "save"
    ICON_SEARCH = "search"
    ICON_PLUS = "plus"
    ICON_REFRESH = "refresh-cw"  # تم التصحيح ليطابق اسم الملف
    ICON_SETTINGS = "settings"
    ICON_CLOSE = "close"
    ICON_CHECK = "check"
    ICON_FILTER = "filter"
    ICON_DOWNLOAD = "download"
    ICON_X = "x"  # للإغلاق (بديل لـ close)

    def __init__(self, icons_dir: Optional[str] = None):
        """
        تهيئة محمل الأيقونات

        Args:
            icons_dir: مسار مجلد الأيقونات (افتراضي: assets/icons)
        """
        # تحديد مسار الأيقونات
        if icons_dir:
            self.icons_dir = Path(icons_dir)
        else:
            # البحث عن assets/icons من جذر المشروع
            project_root = Path(__file__).parent.parent.parent.parent
            self.icons_dir = project_root / "assets" / "icons"

        # إنشاء المجلد إذا لم يكن موجوداً
        self.icons_dir.mkdir(parents=True, exist_ok=True)

        # Cache للأيقونات المحملة
        self._icon_cache = {}

    def get_icon(self, icon_name: str, color: str = "#f8fafc", size: int = 20) -> QIcon:
        """
        تحميل أيقونة SVG مع إعادة التلوين

        Args:
            icon_name: اسم الأيقونة (بدون .svg)
            color: لون الأيقونة (hex code)
            size: حجم الأيقونة بالبكسل

        Returns:
            QIcon: الأيقونة المحملة
        """
        cache_key = f"{icon_name}_{color}_{size}"

        # التحقق من الـ Cache
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        # مسار الملف
        icon_path = self.icons_dir / f"{icon_name}.svg"

        # إذا لم يكن الملف موجوداً، استخدم أيقونة Qt القياسية كبديل
        if not icon_path.exists():
            icon = self._get_fallback_icon(icon_name, size)
            self._icon_cache[cache_key] = icon
            return icon

        # تحميل SVG وإعادة التلوين
        try:
            icon = self._load_svg_icon(icon_path, color, size)
            self._icon_cache[cache_key] = icon
            return icon
        except Exception:
            # في حالة الخطأ، استخدم البديل
            icon = self._get_fallback_icon(icon_name, size)
            self._icon_cache[cache_key] = icon
            return icon

    def _load_svg_icon(self, icon_path: Path, color: str, size: int) -> QIcon:
        """تحميل أيقونة SVG وإعادة تلوينها"""
        # قراءة محتوى SVG
        with open(icon_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        # استبدال الألوان في SVG
        # البحث عن fill="#..." أو stroke="#..." واستبدالها
        import re

        # استبدال fill
        svg_content = re.sub(r'fill="[^"]*"', f'fill="{color}"', svg_content)
        # استبدال stroke
        svg_content = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', svg_content)
        # إذا لم يكن هناك fill أو stroke، أضفه
        if "fill=" not in svg_content and "<path" in svg_content:
            svg_content = svg_content.replace("<path", f'<path fill="{color}"')

        # إنشاء QIcon من SVG
        renderer = QSvgRenderer(svg_content.encode("utf-8"))
        pixmap = QPixmap(size, size)
        pixmap.fill("transparent")

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        icon = QIcon(pixmap)
        return icon

    def _get_fallback_icon(self, icon_name: str, size: int) -> QIcon:
        """الحصول على أيقونة بديلة من Qt"""
        from PySide6.QtWidgets import QStyle

        app = QApplication.instance()
        if not app:
            return QIcon()

        style = app.style()
        if not style:
            return QIcon()

        # خريطة الأيقونات
        icon_map = {
            self.ICON_EDIT: QStyle.SP_FileDialogDetailedView,
            self.ICON_DELETE: QStyle.SP_TrashIcon,
            self.ICON_SAVE: QStyle.SP_DialogSaveButton,
            self.ICON_SEARCH: QStyle.SP_FileDialogContentsView,
            self.ICON_PLUS: QStyle.SP_FileDialogNewFolder,
            self.ICON_REFRESH: QStyle.SP_BrowserReload,
            self.ICON_SETTINGS: QStyle.SP_FileDialogInfoView,
            self.ICON_CLOSE: QStyle.SP_DialogCloseButton,
            self.ICON_X: QStyle.SP_DialogCloseButton,
            self.ICON_CHECK: QStyle.SP_DialogApplyButton,
            self.ICON_FILTER: QStyle.SP_FileDialogListView,
            self.ICON_DOWNLOAD: QStyle.SP_ArrowDown,
        }

        standard_icon = icon_map.get(icon_name, QStyle.SP_FileIcon)
        return style.standardIcon(standard_icon)

    def clear_cache(self):
        """مسح الـ Cache"""
        self._icon_cache.clear()


# Instance عام للاستخدام السريع
_icon_loader_instance = None


def get_icon_loader() -> IconLoader:
    """الحصول على Instance عام من IconLoader"""
    global _icon_loader_instance
    if _icon_loader_instance is None:
        _icon_loader_instance = IconLoader()
    return _icon_loader_instance
