# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),  # Include source code if needed for dynamic imports or reflection
        ('README.md', '.'),
        ('LICENSE.txt', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'sqlite3',
        'src.services.backup_service',
        'src.services.performance_service',
        'src.services.inventory_service',
        'src.services.sales_service',
        'src.services.reports_service',
        'src.services.user_service',
        'src.services.email_service',
        'src.services.reminder_service',
        'src.services.scheduler_service',
        'src.ui.notifications_manager',
        'src.core.database_manager',
        'src.core.config_manager',
        'src.utils.logger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LogicalVersionERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LogicalVersionERP',
)
