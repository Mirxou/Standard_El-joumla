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
        print(f"خطأ في تحميل ملف الأنماط {file_path}: {e}")
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
    style_sheet = load_main_style(theme)
    if style_sheet:
        app.setStyleSheet(style_sheet)
        return True
    return False


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

