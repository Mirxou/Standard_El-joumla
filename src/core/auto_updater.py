#!/usr/bin/env python3
"""
نظام التحديث التلقائي - Auto-Updater
يتحقص من التحديثات ويحملها ويثبتها بأمان
"""

import os
import sys
import json
import hashlib
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from PySide6.QtCore import QObject, QThread, Signal, QProcess
from PySide6.QtWidgets import QMessageBox, QProgressDialog


class VersionInfo:
    """معلومات الإصدار"""
    def __init__(self, major: int, minor: int, patch: int, pre: str = ""):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = pre

    @classmethod
    def parse(cls, version_str: str) -> 'VersionInfo':
        """تحليل سلسلة الإصدار: '6.0.0' أو '6.1.0-beta'"""
        version_str = version_str.lstrip('v')
        parts = version_str.split('-', 1)
        pre = parts[1] if len(parts) > 1 else ""
        nums = parts[0].split('.')
        return cls(
            major=int(nums[0]) if len(nums) > 0 else 0,
            minor=int(nums[1]) if len(nums) > 1 else 0,
            patch=int(nums[2]) if len(nums) > 2 else 0,
            pre=pre
        )

    def __gt__(self, other: 'VersionInfo') -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
        if self.pre and not other.pre:
            return False  # pre-release < release
        if not self.pre and other.pre:
            return True
        return self.pre > other.pre

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += f"-{self.pre}"
        return s


class UpdateCheckWorker(QThread):
    """عامل فحص التحديثات في الخلفية"""
    update_found = Signal(dict)    # معلومات التحديث
    no_update = Signal()
    check_error = Signal(str)

    def __init__(self, current_version: str, update_url: str, channel: str = "stable"):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url
        self.channel = channel
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            import urllib.request
            import urllib.error

            headers = {
                'User-Agent': f'ElJoumla-ERP/{self.current_version}',
                'Accept': 'application/json'
            }
            req = urllib.request.Request(self.update_url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            # تحليل أحدث إصدار
            if isinstance(data, list) and len(data) > 0:
                # GitHub releases format
                latest = data[0]
                latest_version = latest.get('tag_name', '0.0.0')
                changelog = latest.get('body', '')

                # إيجاد رابط التحميل
                assets = latest.get('assets', [])
                download_url = None
                for asset in assets:
                    name = asset.get('name', '').lower()
                    if name.endswith('.exe') or name.endswith('.zip'):
                        download_url = asset.get('browser_download_url')
                        break

                if not download_url:
                    self.check_error.emit("لم يتم إيجاد ملف التحديث")
                    return

                update_info = {
                    'version': latest_version,
                    'changelog': changelog,
                    'download_url': download_url,
                    'published_at': latest.get('published_at', ''),
                }

            elif isinstance(data, dict):
                # API مخصص
                latest_version = data.get('version', '0.0.0')
                update_info = {
                    'version': latest_version,
                    'changelog': data.get('changelog', ''),
                    'download_url': data.get('download_url', ''),
                    'sha256': data.get('sha256', ''),
                    'signature': data.get('signature', ''),
                    'published_at': data.get('published_at', ''),
                }
            else:
                self.check_error.emit("صيغة الاستجابة غير معروفة")
                return

            # مقارنة الإصدارات
            current = VersionInfo.parse(self.current_version)
            latest_v = VersionInfo.parse(latest_version)

            if latest_v > current:
                self.logger.info(f"تحديث متاح: {latest_v} > {current}")
                self.update_found.emit(update_info)
            else:
                self.logger.info(f"لا تحديث متاح: {latest_v} <= {current}")
                self.no_update.emit()

        except Exception as e:
            self.logger.error(f"خطأ في فحص التحديثات: {e}")
            self.check_error.emit(str(e))


class UpdateDownloadWorker(QThread):
    """عامل تحميل التحديث في الخلفية"""
    download_progress = Signal(int)       # نسبة مئوية
    download_completed = Signal(str)      # مسار الملف المحمّل
    download_error = Signal(str)
    hash_mismatch = Signal()

    def __init__(self, download_url: str, expected_sha256: str = "",
                 save_dir: str = ""):
        super().__init__()
        self.download_url = download_url
        self.expected_sha256 = expected_sha256
        self.save_dir = save_dir or tempfile.gettempdir()
        self.logger = logging.getLogger(__name__)
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            import urllib.request

            # تحديد اسم الملف
            filename = self.download_url.split('/')[-1]
            save_path = os.path.join(self.save_dir, f"eljoumla_update_{filename}")

            # تحميل مع تتبع التقدم
            req = urllib.request.Request(self.download_url)
            with urllib.request.urlopen(req, timeout=60) as response:
                total = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192

                hasher = hashlib.sha256()

                with open(save_path, 'wb') as f:
                    while not self._cancelled:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        hasher.update(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(downloaded * 100 / total)
                            self.download_progress.emit(pct)

                if self._cancelled:
                    os.remove(save_path)
                    return

                # التحقق من SHA256
                if self.expected_sha256:
                    actual_hash = hasher.hexdigest()
                    if actual_hash != self.expected_sha256:
                        self.logger.error(f"SHA256 لا يتطابق: متوقع={self.expected_sha256}, فعلي={actual_hash}")
                        os.remove(save_path)
                        self.hash_mismatch.emit()
                        return

                self.logger.info(f"تم تحميل التحديث: {save_path}")
                self.download_completed.emit(save_path)

        except Exception as e:
            self.logger.error(f"خطأ في تحميل التحديث: {e}")
            self.download_error.emit(str(e))


class AutoUpdater(QObject):
    """نظام التحديث التلقائي"""

    # إشارات
    update_available = Signal(dict)     # معلومات التحديث
    update_downloaded = Signal(str)     # مسار الملف
    update_installed = Signal()         # تم التثبيت
    update_error = Signal(str)          # خطأ

    # الإعدادات الافتراضية
    DEFAULT_UPDATE_URL = "https://api.github.com/repos/Mirxou/Standard_El-joumla/releases"

    def __init__(self, parent=None,
                 current_version: str = "6.0.0",
                 update_url: str = "",
                 channel: str = "stable"):
        super().__init__(parent)

        self.current_version = current_version
        self.update_url = update_url or self.DEFAULT_UPDATE_URL
        self.channel = channel
        self.logger = logging.getLogger(__name__)

        self._check_worker: Optional[UpdateCheckWorker] = None
        self._download_worker: Optional[UpdateDownloadWorker] = None
        self._pending_update: Optional[Dict] = None
        self._downloaded_file: Optional[str] = None

    def check_for_updates(self, silent: bool = True) -> bool:
        """فحص التحديثات"""
        if self._check_worker and self._check_worker.isRunning():
            return False

        self._check_worker = UpdateCheckWorker(
            self.current_version, self.update_url, self.channel
        )
        self._check_worker.update_found.connect(self._on_update_found)
        self._check_worker.no_update.connect(self._on_no_update if not silent else lambda: None)
        self._check_worker.check_error.connect(self._on_check_error if not silent else lambda e: None)
        self._check_worker.start()

        return True

    def _on_update_found(self, update_info: dict):
        """عند إيجاد تحديث"""
        self._pending_update = update_info
        self.update_available.emit(update_info)
        self.logger.info(f"تحديث متاح: v{update_info.get('version', '?')}")

    def _on_no_update(self):
        """لا تحديث متاح"""
        QMessageBox.information(
            None, "التحقق من التحديثات",
            "أنت تستخدم أحدث إصدار ✅"
        )

    def _on_check_error(self, error: str):
        """خطأ في الفحص"""
        QMessageBox.warning(
            None, "خطأ في التحديث",
            f"تعذر فحص التحديثات:\n{error}"
        )

    def download_and_install(self, update_info: Optional[Dict] = None):
        """تحميل وتثبيت التحديث"""
        info = update_info or self._pending_update
        if not info:
            self.update_error.emit("لا معلومات تحديث متاحة")
            return

        # تأكيد المستخدم
        version = info.get('version', '؟')
        changelog = info.get('changelog', 'لا تفاصيل متاحة')

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("تحديث متاح")
        msg.setText(f"الإصدار {version} متاح للتثبيت.\n\nهل تريد تحميله الآن؟")
        msg.setDetailedText(changelog)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)

        if msg.exec() != QMessageBox.Yes:
            return

        # بدء التحميل
        download_url = info.get('download_url', '')
        sha256 = info.get('sha256', '')

        self._download_worker = UpdateDownloadWorker(download_url, sha256)
        self._download_worker.download_progress.connect(self._on_download_progress)
        self._download_worker.download_completed.connect(self._on_download_completed)
        self._download_worker.download_error.connect(self._on_download_error)
        self._download_worker.hash_mismatch.connect(self._on_hash_mismatch)
        self._download_worker.start()

    def _on_download_progress(self, pct: int):
        """تقدم التحميل"""
        self.logger.info(f"تقدم تحميل التحديث: {pct}%")

    def _on_download_completed(self, filepath: str):
        """اكتمال التحميل"""
        self._downloaded_file = filepath
        self.update_downloaded.emit(filepath)
        self.logger.info(f"تم تحميل التحديث: {filepath}")

        # اقتراح التثبيت
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("التحديث جاهز")
        msg.setText("تم تحميل التحديث بنجاح.\n\nسيتم التثبيت بعد إعادة التشغيل.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

        self._prepare_install(filepath)

    def _on_download_error(self, error: str):
        self.update_error.emit(error)
        QMessageBox.critical(None, "خطأ في التحميل", f"فشل تحميل التحديث:\n{error}")

    def _on_hash_mismatch(self):
        self.update_error.emit("SHA256 لا يتطابق — الملف تالف")
        QMessageBox.critical(None, "خطأ في التحميل",
            "الملف المحمّل تالف (SHA256 لا يتطابق).\nالتحميل مُلغى لحماية النظام.")

    def _prepare_install(self, update_file: str):
        """إعداد التثبيت — إنشاء script لاستبدال EXE بعد الإغلاق"""
        try:
            if not getattr(sys, 'frozen', False):
                self.logger.info("وضع التطوير — لا تثبيت تلقائي")
                return

            current_exe = sys.executable
            backup_exe = current_exe + ".backup"

            # إنشاء batch script للاستبدال
            bat_content = f"""@echo off
echo Updating El-Joumla ERP...
timeout /t 2 /nobreak >nul

REM Backup current version
if exist "{current_exe}" (
    copy /y "{current_exe}" "{backup_exe}"
)

REM Replace with new version
copy /y "{update_file}" "{current_exe}"

REM Restart application
start "" "{current_exe}"

REM Cleanup
del "{update_file}"
del "%~f0"
"""
            bat_path = os.path.join(tempfile.gettempdir(), "eljoumla_update.bat")
            with open(bat_path, 'w') as f:
                f.write(bat_content)

            # تشغيل batch script عند إغلاق التطبيق
            QProcess.startDetached('cmd.exe', ['/c', bat_path])

            self.logger.info(f"script التثبيت جاهز: {bat_path}")

        except Exception as e:
            self.logger.error(f"خطأ في إعداد التثبيت: {e}")
            self.update_error.emit(str(e))
