#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Telemetry - فحص بيانات Telemetry
Quick script to check telemetry data
"""

import json
from pathlib import Path
from src.core.telemetry_hook import WindowTelemetry


def check_telemetry():
    """فحص بيانات Telemetry"""
    print("=" * 60)
    print("Window Telemetry Report")
    print("=" * 60)
    print()
    
    # إنشاء telemetry instance
    telemetry = WindowTelemetry()
    
    # عرض التقرير
    report = telemetry.generate_report()
    print(report)
    
    # عرض البيانات من ملف JSON
    telemetry_file = Path("logs/window_telemetry.json")
    if telemetry_file.exists():
        print()
        print("=" * 60)
        print("JSON Data:")
        print("=" * 60)
        with open(telemetry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print()
        print("⚠️  ملف Telemetry غير موجود بعد")
        print("   شغّل التطبيق وافتح بعض النوافذ أولاً")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    check_telemetry()

