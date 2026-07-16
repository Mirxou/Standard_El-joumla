#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح main_window.py لاستخدام Repository pattern
"""

from pathlib import Path

def fix_main_window():
    """إصلاح main_window.py"""
    main_window_path = Path(__file__).parent / "src" / "ui" / "windows" / "main_window.py"

    if not main_window_path.exists():
        print("❌ main_window.py غير موجود")
        return

    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # إضافة imports الجديدة
        import_section = """
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.core.local_database_manager import LocalDatabaseManager
"""

        # إدراج imports بعد config_manager
        if "from src.core.config_manager import ConfigManager" in content:
            content = content.replace(
                "from src.core.config_manager import ConfigManager",
                "from src.core.config_manager import ConfigManager\n" + import_section
            )
            print("✅ تم إضافة imports")

        # إضافة تهيئة repositories في __init__
        init_marker = "self.config_manager = ConfigManager()"
        repo_init = """
        # تهيئة مدير قاعدة البيانات والـ repositories
        self.db_manager = LocalDatabaseManager()
        self.product_repo = ProductRepository(self.db_manager)
        self.sale_repo = SaleRepository(self.db_manager)
"""

        if init_marker in content:
            content = content.replace(init_marker, init_marker + repo_init)
            print("✅ تم إضافة تهيئة repositories")

        # حفظ الملف
        with open(main_window_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ تم إصلاح main_window.py بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إصلاح main_window.py: {e}")

if __name__ == "__main__":
    fix_main_window()