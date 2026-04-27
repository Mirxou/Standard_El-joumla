#!/usr/bin/env python3
import sys
sys.path.insert(0, 'c:/Users/aboun/Desktop/Logical Version trae')

try:
    from tests.unit import test_abc_analysis_window
    print("✅ test_abc_analysis_window.py: OK")
except Exception as e:
    print(f"❌ test_abc_analysis_window.py: {e}")
