#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مسح Cache التطبيق"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = DatabaseManager(config.get_database_path())
db.initialize()

print("=== مسح Cache ===")

try:
    # حذف جميع مفاتيح الـ cache المتعلقة بالمنتجات والمخزون
    cache_patterns = [
        'ui:inventory:%',
        'ui:products:%',
        'ui:dashboard:%',
        'products:%',
        'inventory:%'
    ]
    
    for pattern in cache_patterns:
        result = db.execute_non_query(
            "DELETE FROM cache WHERE key LIKE ?",
            (pattern,)
        )
        print(f"✓ حذف {result} عنصر من pattern: {pattern}")
    
    # مسح Cache القديم (أكبر من ساعة)
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(hours=1)
    old_cache = db.execute_non_query(
        "DELETE FROM cache WHERE updated_at < ?",
        (cutoff,)
    )
    print(f"✓ حذف {old_cache} عنصر cache قديم")
    
    print("\n✅ تم مسح الـ Cache بنجاح!")
    print("\n💡 الآن يمكنك تشغيل التطبيق: python main.py")
    
except Exception as e:
    print(f"✗ خطأ في مسح Cache: {e}")
