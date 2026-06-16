#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تهيئة البيانات الافتراضية
Populate default categories and reset admin password
"""

import sys
from pathlib import Path

# إضافة مسار src للمشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager
from src.models.user import UserManager
from src.models.category import CategoryManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    logger.info("🚀 بدء تهيئة البيانات الافتراضية...")
    
    try:
        # تهيئة Config و Database
        config = ConfigManager()
        db_path = config.get_database_path()
        logger.info(f"📍 استخدام قاعدة البيانات في: {db_path}")
        
        db_manager = LocalDatabaseManager(db_path=db_path)
        if not db_manager.initialize():
            logger.error("❌ فشل تهيئة قاعدة البيانات")
            return
        
        # 1. تحديث/إنشاء كلمة مرور Admin
        logger.info("🔐 تحديث كلمة مرور المدير...")
        user_manager = UserManager(db_manager, logger)
        admin = user_manager.get_user_by_username("admin")
        
        if admin:
            # إذا كان موجوداً، إعادة تعيين كلمة المرور
            if user_manager.reset_password(admin.id, "123"):
                logger.info("✅ تم إعادة تعيين كلمة مرور admin إلى: 123")
            else:
                logger.error("❌ فشل إعادة تعيين كلمة المرور")
        else:
            # إذا لم يكن موجوداً، إنشاؤه
            if user_manager.create_default_admin():
                logger.info("✅ تم إنشاء مستخدم admin بكلمة مرور: 123")
            else:
                logger.error("❌ فشل إنشاء مستخدم admin")
        
        # 2. إضافة الفئات الافتراضية
        logger.info("📁 إضافة فئات افتراضية...")
        category_manager = CategoryManager(db_manager, logger)
        if category_manager.create_default_categories():
            logger.info("✅ تم معالجة الفئات الافتراضية")
        else:
            logger.error("❌ فشل معالجة الفئات الافتراضية")
            
        logger.info("✨ اكتملت العملية بنجاح!")
        
    except Exception as e:
        logger.error(f"❌ حدث خطأ غير متوقع: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
