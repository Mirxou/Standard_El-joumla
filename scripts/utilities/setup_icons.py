#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Icon Downloader - Feather Icons
سكريبت تحميل الأيقونات تلقائياً من Feather Icons
"""

import urllib.request
from pathlib import Path

# إعدادات المجلدات
ICON_DIR = Path("assets") / "icons"
ICON_DIR.mkdir(parents=True, exist_ok=True)

# روابط الأيقونات (Feather Icons - High Quality SVGs)
ICONS = {
    "edit.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/edit-2.svg",
    "trash.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/trash-2.svg",
    "save.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/save.svg",
    "search.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/search.svg",
    "plus.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/plus.svg",
    "x.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/x.svg",        # للإغلاق
    "check.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/check.svg", # للتأكيد
    "filter.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/filter.svg", # للفلترة
    "refresh-cw.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/refresh-cw.svg", # للتحديث
    "download.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/download.svg", # للتحميل
    "settings.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/settings.svg", # للإعدادات
    "close.svg": "https://raw.githubusercontent.com/feathericons/feather/master/icons/x-circle.svg", # للإغلاق (بديل لـ x.svg)
}

print(f"🚀 Starting download to: {ICON_DIR}...")
print()

success_count = 0
error_count = 0

for name, url in ICONS.items():
    file_path = ICON_DIR / name
    try:
        print(f"   ⬇️  Downloading {name}...", end=" ")
        urllib.request.urlretrieve(url, str(file_path))
        print("✅ Done.")
        success_count += 1
    except Exception as e:
        print(f"❌ Error: {e}")
        error_count += 1

print()
print("=" * 50)
print(f"✨ Download Complete!")
print(f"   ✅ Success: {success_count}")
if error_count > 0:
    print(f"   ❌ Errors: {error_count}")
print()
print("🎉 All icons are ready! You can run the app now.")
print("=" * 50)

