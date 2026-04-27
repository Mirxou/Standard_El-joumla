#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تشغيل Backend API للشبكة المحلية
Script to start Backend API for local network access
"""

import sys
import uvicorn
from pathlib import Path

# إضافة مسار المشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import app
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

if __name__ == "__main__":
    logger.info("火箭 بدء تشغيل REST API Server للشبكة المحلية...")
    logger.info("📍 الوصول متاح من: http://127.0.0.1:8001")
    logger.info("📚 API Documentation: http://127.0.0.1:8001/docs")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",  # للوصول من الشبكة المحلية
            port=8001,
            reload=False,  # تعطيل reload للإنتاج
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف الخادم بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل الخادم: {e}")
        sys.exit(1)

