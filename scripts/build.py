#!/usr/bin/env python3
"""
سكريبت البناء - Build Script
يبني تطبيق El-Joumla ERP كملف تنفيذي Windows باستخدام Nuitka
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# معلومات التطبيق
APP_NAME = "ElJoumla"
APP_VERSION = "6.0.0"
APP_COMPANY = "Standard El-Joumla"
APP_DESCRIPTION = "نظام إدارة المبيعات والمجوز بالجملة"
APP_ICON = PROJECT_ROOT / "assets" / "icons" / "app_icon.ico"

# المجلدات المطلوبة
DATA_DIRS = [
    "assets",
    "locales",
    "config",
    "data",
]


def check_nuitka():
    """التحقق من تثبيت Nuitka"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✓ Nuitka مثبّت: {result.stdout.strip()}")
            return True
    except Exception:
        pass

    print("✗ Nuitka غير مثبّت. جاري التثبيت...")
    subprocess.run([sys.executable, "-m", "pip", "install", "nuitka"], check=True)
    print("✓ Nuitka تم تثبيته")
    return True


def build_onefile():
    """بناء كملف واحد (Onefile)"""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--enable-qt=pyside6",
        "--windows-disable-console",
        f"--windows-icon-from-ico={APP_ICON}",
        f"--windows-company-name={APP_COMPANY}",
        f"--windows-product-name={APP_NAME} ERP",
        f"--windows-file-version={APP_VERSION}",
        f"--windows-product-version={APP_VERSION}",
        f"--output-filename={APP_NAME}.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "--python-flag=no_site",
    ]

    # إضافة مجلدات البيانات
    for data_dir in DATA_DIRS:
        dir_path = PROJECT_ROOT / data_dir
        if dir_path.exists():
            cmd.append(f"--include-data-dir={data_dir}={data_dir}")

    # ملف الإدخال
    cmd.append(str(PROJECT_ROOT / "main.py"))

    print(f"\nبناء {APP_NAME} v{APP_VERSION} كملف واحد...")
    print(f"الأمر: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        exe_path = PROJECT_ROOT / f"{APP_NAME}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✓ البناء ناجح: {exe_path} ({size_mb:.1f} MB)")
            return True

    print("\n✗ فشل البناء")
    return False


def build_standalone():
    """بناء كمجلد مستقل (Standalone)"""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--enable-qt=pyside6",
        "--windows-disable-console",
        f"--windows-icon-from-ico={APP_ICON}",
        f"--windows-company-name={APP_COMPANY}",
        f"--windows-product-name={APP_NAME} ERP",
        f"--windows-file-version={APP_VERSION}",
        f"--windows-product-version={APP_VERSION}",
        f"--output-dir={PROJECT_ROOT / 'dist'}",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "--python-flag=no_site",
    ]

    for data_dir in DATA_DIRS:
        dir_path = PROJECT_ROOT / data_dir
        if dir_path.exists():
            cmd.append(f"--include-data-dir={data_dir}={data_dir}")

    cmd.append(str(PROJECT_ROOT / "main.py"))

    print(f"\nبناء {APP_NAME} v{APP_VERSION} كمجلد مستقل...")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode == 0:
        dist_dir = PROJECT_ROOT / "dist" / "main.dist"
        if dist_dir.exists():
            print(f"\n✓ البناء ناجح: {dist_dir}")
            return True

    print("\n✗ فشل البناء")
    return False


def create_inno_setup():
    """إنشاء مثبت InnoSetup"""
    iss_content = f"""; InnoSetup Script for {APP_NAME} ERP
#define MyAppName "{APP_NAME}"
#define MyAppVersion "{APP_VERSION}"
#define MyAppPublisher "{APP_COMPANY}"
#define MyAppExeName "{APP_NAME}.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
OutputDir=installer_output
OutputBaseFilename={APP_NAME}_Setup_{{#MyAppVersion}}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "dist\\main.dist\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{app}}\\unins000.exe"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#MyAppName}}}}"; Flags: nowait postinstall skipifsilent
"""

    iss_path = PROJECT_ROOT / "installer.iss"
    with open(iss_path, 'w', encoding='utf-8') as f:
        f.write(iss_content)

    print(f"✓ ملف InnoSetup أُنشئ: {iss_path}")
    print("  لإنشاء المثبت، شغّل: iscc installer.iss")


def main():
    parser = argparse.ArgumentParser(description=f"بناء {APP_NAME} ERP")
    parser.add_argument("--mode", choices=["onefile", "standalone", "both"], default="onefile")
    parser.add_argument("--installer", action="store_true", help="إنشاء مثبت InnoSetup")
    parser.add_argument("--clean", action="store_true", help="تنظيف قبل البناء")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"بناء {APP_NAME} ERP v{APP_VERSION}")
    print(f"{'='*60}")

    if args.clean:
        print("\nتنظيف...")
        for d in ["build", "dist", f"{APP_NAME}.build"]:
            p = PROJECT_ROOT / d
            if p.exists():
                shutil.rmtree(p)
                print(f"  ✓ حُذف: {d}")

    check_nuitka()

    success = False
    if args.mode in ("onefile", "both"):
        success = build_onefile()

    if args.mode in ("standalone", "both"):
        success = build_standalone()

    if args.installer:
        create_inno_setup()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
