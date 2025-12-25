#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Style Loader
محمل الأنماط الرئيسية مع دعم السمات
"""

from pathlib import Path
from typing import Optional
import re


def load_qss_file(file_path: Path) -> Optional[str]:
    """
    تحميل ملف QSS مع معالجة @import
    
    Args:
        file_path: مسار ملف QSS
    
    Returns:
        محتوى الملف مع استبدال @import أو None
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # معالجة @import
        styles_dir = file_path.parent
        import_pattern = r'@import\s+url\(([^)]+)\);'
        
        def replace_import(match):
            import_file = match.group(1).strip()
            import_path = styles_dir / import_file
            imported_content = load_qss_file(import_path)
            return imported_content if imported_content else ''
        
        content = re.sub(import_pattern, replace_import, content)
        return content
        
    except Exception as e:
        # لا نطبع خطأ هنا لأن هذا قد يكون متوقعاً في بعض البيئات
        # فقط نعيد None للإشارة إلى أن التحميل فشل
        return None


def load_main_style(theme: str = 'light') -> Optional[str]:
    """
    تحميل ملف الأنماط الرئيسي (main.qss)
    
    Args:
        theme: السمة ('light' أو 'dark')
    
    Returns:
        محتوى ملف QSS أو None إذا لم يتم العثور عليه
    """
    styles_dir = Path(__file__).parent
    
    # تحديد ملف QSS حسب السمة
    if theme == 'dark':
        qss_file = styles_dir / "main-dark.qss"
        if not qss_file.exists():
            # إذا لم يكن موجوداً، استخدم main.qss
            qss_file = styles_dir / "main.qss"
    else:
        qss_file = styles_dir / "main.qss"
    
    return load_qss_file(qss_file)


def apply_style_to_app(app, theme: str = 'light') -> bool:
    """
    تطبيق الأنماط على التطبيق
    
    Args:
        app: QApplication instance
        theme: السمة ('light' أو 'dark')
    
    Returns:
        True إذا تم التطبيق بنجاح
    """
    try:
        style_sheet = load_main_style(theme)
        if style_sheet:
            # تنظيف الأنماط من الخصائص غير المدعومة في Qt
            style_sheet = _clean_qss(style_sheet)
            # قمع تحذيرات Qt حول الأنماط غير المدعومة
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                app.setStyleSheet(style_sheet)
            return True
    except Exception as e:
        # لا نطبع خطأ هنا لأن هذا قد يكون متوقعاً في بعض البيئات
        # فقط نعيد False للإشارة إلى أن التطبيق فشل
        pass
    return False


def _clean_qss(qss_content: str) -> str:
    """
    تنظيف محتوى QSS من الخصائص غير المدعومة في Qt
    
    Qt لا يدعم بعض خصائص CSS مثل:
    - box-shadow
    - text-shadow
    - transform
    - filter
    - وغيرها
    
    Args:
        qss_content: محتوى QSS الأصلي
    
    Returns:
        محتوى QSS بعد التنظيف
    """
    import re
    
    # قائمة الخصائص غير المدعومة
    unsupported_properties = [
        r'box-shadow\s*:[^;]+;',
        r'text-shadow\s*:[^;]+;',
        r'transform\s*:[^;]+;',
        r'filter\s*:[^;]+;',
        r'backdrop-filter\s*:[^;]+;',
        r'perspective\s*:[^;]+;',
        r'transition\s*:[^;]+;',
        r'animation\s*:[^;]+;',
    ]
    
    cleaned = qss_content
    for pattern in unsupported_properties:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    return cleaned


def get_available_themes() -> list:
    """
    الحصول على قائمة السمات المتاحة
    
    Returns:
        قائمة بأسماء السمات المتاحة
    """
    styles_dir = Path(__file__).parent
    themes = ['light']  # السمة الافتراضية
    
    if (styles_dir / "main-dark.qss").exists():
        themes.append('dark')
    
    return themes

