#!/usr/bin/env python3
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

mods = [
    'src.ui.windows.abc_analysis_window',
    'src.ui.windows.safety_stock_window',
    'src.ui.windows.batch_tracking_window',
    'src.ui.windows.reorder_recommendations_window',
    'src.ui.dialogs.safety_stock_dialog',
    'src.ui.dialogs.batch_dialog',
]

failed = []
for m in mods:
    try:
        __import__(m)
        print(f'Imported: {m}')
    except Exception as e:
        print(f'FAILED: {m}: {e}')
        traceback.print_exc()
        failed.append(m)

if failed:
    sys.exit(1)
print('OK')
