#!/usr/bin/env python3
"""
حماية النسخة الواحدة - Single Instance Protection
يضمن تشغيل نسخة واحدة فقط من التطبيق في أي وقت
"""

import os
import sys
import logging
from typing import Optional


class SingleInstance:
    """يضمن تشغيل نسخة واحدة فقط من التطبيق"""

    def __init__(self, app_name: str = "ElJoumlaERP"):
        self.app_name = app_name
        self.logger = logging.getLogger(__name__)
        self._lockfile: Optional[object] = None
        self._lockpath: Optional[str] = None
        self._mutex: Optional[object] = None

    def try_lock(self) -> bool:
        """محاولة الحصول على القفل. يعيد True إذا نجح (لا نسخة أخرى تعمل)"""
        if sys.platform == 'win32':
            return self._try_lock_windows()
        else:
            return self._try_lock_unix()

    def _try_lock_windows(self) -> bool:
        """قفل على Windows باستخدام Named Mutex"""
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32

            # إنشاء Named Mutex
            mutex_name = f"Global\\{self.app_name}_SingleInstance"
            self._mutex = kernel32.CreateMutexW(None, False, mutex_name)

            # ERROR_ALREADY_EXISTS = 183
            if kernel32.GetLastError() == 183:
                self.logger.warning(f"نسخة أخرى من {self.app_name} تعمل بالفعل")
                return False

            self.logger.info("تم الحصول على قفل النسخة الواحدة (Windows Mutex)")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء Mutex: {e}")
            # في حالة الفشل، نسمح بالتشغيل (تراجع آمن)
            return True

    def _try_lock_unix(self) -> bool:
        """قفل على Unix باستخدام lock file"""
        try:
            # مسار ملف القفل
            if sys.platform == 'darwin':
                base_dir = os.path.expanduser("~/Library/Caches")
            else:
                base_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')

            lock_dir = os.path.join(base_dir, self.app_name)
            os.makedirs(lock_dir, exist_ok=True)

            self._lockpath = os.path.join(lock_dir, f"{self.app_name}.lock")

            # فتح ملف القفل
            self._lockfile = open(self._lockpath, 'w')

            # محاولة القفل الحصري (non-blocking)
            import fcntl
            try:
                fcntl.flock(self._lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # كتابة PID
                self._lockfile.write(str(os.getpid()))
                self._lockfile.flush()
                self.logger.info("تم الحصول على قفل النسخة الواحدة (Unix lock file)")
                return True
            except IOError:
                self._lockfile.close()
                self._lockfile = None
                self.logger.warning(f"نسخة أخرى من {self.app_name} تعمل بالفعل")
                return False

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء lock file: {e}")
            return True  # تراجع آمن

    def release(self):
        """تحرير القفل عند إغلاق التطبيق"""
        try:
            if sys.platform == 'win32' and self._mutex:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.CloseHandle(self._mutex)
                self._mutex = None
                self.logger.info("تم تحرير قفل Windows Mutex")

            elif self._lockfile:
                import fcntl
                fcntl.flock(self._lockfile.fileno(), fcntl.LOCK_UN)
                self._lockfile.close()
                self._lockfile = None

                if self._lockpath and os.path.exists(self._lockpath):
                    os.remove(self._lockpath)

                self.logger.info("تم تحرير قفل Unix lock file")

        except Exception as e:
            self.logger.error(f"خطأ في تحرير القفل: {e}")

    def __enter__(self):
        if not self.try_lock():
            raise RuntimeError(f"نسخة أخرى من {self.app_name} تعمل بالفعل")
        return self

    def __exit__(self, *args):
        self.release()
