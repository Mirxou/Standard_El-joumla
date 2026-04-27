#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script
سكربت بناء التطبيق باستخدام PyInstaller
"""

import subprocess
import sys
from pathlib import Path

def build_app():
    """بناء التطبيق"""
    project_root = Path(__file__).parent.parent
    
    print("🔨 بدء بناء التطبيق...")
    
    try:
        # تشغيل PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            "build.spec"
        ]
        
        result = subprocess.run(cmd, cwd=project_root, check=True)
        
        print("✅ تم بناء التطبيق بنجاح!")
        print(f"📦 الملف: {project_root / 'dist' / 'LogicalERP.exe'}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل بناء التطبيق: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_app()
