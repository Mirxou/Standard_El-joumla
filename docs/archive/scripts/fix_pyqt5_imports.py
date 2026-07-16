#!/usr/bin/env python3
"""إصلاح استيرادات PyQt5 في جميع ملفات الاختبار"""
import os
import re

test_dir = "tests/unit"

# قائمة الملفات التي تحتاج إصلاح
files_to_fix = [
    "test_blur_effect.py", "test_cart_item_widget.py", "test_context_menu.py",
    "test_customer_model.py", "test_data_table.py", "test_detail_view.py",
    "test_drag_drop_list.py", "test_filter_panel.py", "test_info_bubble.py",
    "test_list_view.py", "test_notifications_panel.py", "test_product_list_item.py",
    "test_product_table_model.py", "test_progress_indicator.py", "test_sales_model.py",
    "test_search_box.py", "test_stepper_widget.py", "test_toggle_switch.py",
    "test_tree_view.py"
]

fixed_count = 0

for filename in files_to_fix:
    filepath = os.path.join(test_dir, filename)
    if not os.path.exists(filepath):
        print(f"⚠️ ملف غير موجود: {filename}")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # التحقق مما إذا كان الملف يحتاج إصلاح
    if 'try:' in content and 'HAS_PYQT5' in content:
        print(f"✅ تم إصلاحه مسبقاً: {filename}")
        continue
    
    # إضافة معالجة الأخطاء
    if 'from PyQt5' in content:
        # استبدال الاستيرادات المباشرة باستيرادات محمية
        new_content = re.sub(
            r'(import pytest\nfrom unittest\.mock import Mock, patch, MagicMock\n)',
            r'\1\ntry:\n',
            content
        )
        
        # إضافة except في نهاية الاستيرادات
        lines = new_content.split('\n')
        import_end_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from src.') or line.startswith('import src.'):
                import_end_idx = i
                break
        
        if import_end_idx > 0:
            # إضافة استيرادات في try block
            lines.insert(import_end_idx + 1, '    HAS_PYQT5 = True')
            lines.insert(import_end_idx + 2, 'except ImportError:')
            lines.insert(import_end_idx + 3, '    HAS_PYQT5 = False')
            lines.insert(import_end_idx + 4, '    pytest.skip("PyQt5 not installed", allow_module_level=True)')
            
            new_content = '\n'.join(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            fixed_count += 1
            print(f"✅ تم إصلاح: {filename}")

print(f"\n📊 إجمالي الملفات المُصلحة: {fixed_count}")
