#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Review Script
سكربت مراجعة الكود التلقائية
"""

import re
import sys
from pathlib import Path
from typing import List, Dict


def review_code(file_path: str) -> List[str]:
    """
    مراجعة ملف كود
    
    Args:
        file_path: مسار الملف
        
    Returns:
        قائمة بالمشاكل المكتشفة
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"فشل قراءة الملف: {str(e)}"]
    
    # Check for SQL Injection
    if re.search(r'f".*SELECT.*\{', content) or re.search(r'f".*INSERT.*\{', content):
        issues.append("⚠️ Potential SQL Injection: String formatting in SQL")
    
    # Check for Hard Delete
    if re.search(r'DELETE FROM\s+\w+\s+WHERE', content, re.IGNORECASE):
        # التحقق من أنه ليس Soft Delete
        if 'is_deleted' not in content:
            issues.append("⚠️ Hard Delete detected: Should use Soft Delete")
    
    # Check for Main Thread blocking (API calls without QThread)
    if 'requests.get' in content or 'requests.post' in content:
        if 'QThread' not in content and 'QRunnable' not in content and 'ThreadPool' not in content:
            issues.append("⚠️ Potential UI blocking: API call without QThread/QRunnable")
    
    # Check for hardcoded passwords/keys
    if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
        issues.append("⚠️ Hardcoded password detected")
    
    if re.search(r'api_key\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
        issues.append("⚠️ Hardcoded API key detected")
    
    # Check for missing error handling
    if 'execute_query' in content or 'execute_non_query' in content:
        if 'try:' not in content or 'except' not in content:
            issues.append("⚠️ Missing error handling in database operations")
    
    return issues


def review_directory(directory: str) -> Dict[str, List[str]]:
    """
    مراجعة مجلد كامل
    
    Args:
        directory: مسار المجلد
        
    Returns:
        قاموس بالملفات ومشاكلها
    """
    results = {}
    dir_path = Path(directory)
    
    for file_path in dir_path.rglob("*.py"):
        if 'test' in str(file_path) or '__pycache__' in str(file_path):
            continue
        
        issues = review_code(str(file_path))
        if issues:
            results[str(file_path)] = issues
    
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "src"
    
    print(f"🔍 مراجعة الكود: {target}")
    results = review_directory(target)
    
    if results:
        print("\n⚠️ المشاكل المكتشفة:\n")
        for file_path, issues in results.items():
            print(f"📄 {file_path}:")
            for issue in issues:
                print(f"  {issue}")
            print()
    else:
        print("✅ لا توجد مشاكل مكتشفة")
