#!/usr/bin/env python3
"""التحقق من المكتبات المتوفرة"""
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print()

libs = ['pytest', 'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore']
for lib in libs:
    try:
        __import__(lib)
        print(f"✅ {lib}")
    except ImportError as e:
        print(f"❌ {lib}: {e}")

print()
print("sys.path:")
for p in sys.path[:5]:
    print(f"  {p}")
