import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Service
خدمة إدارة الجلسات المشتركة بين Desktop و Web
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.api.api_client import APIClient
from src.core.keyring_manager import KeyringManager
from src.utils.logger import setup_logger


class SessionService:
    """خدمة إدارة الجلسات المشتركة"""

    def __init__(self, api_client: APIClient, keyring_manager: Optional[KeyringManager] = None):
        self.api_client = api_client
        self.keyring_manager = keyring_manager or KeyringManager()
        self.logger = setup_logger(__name__)

        self.current_session: Optional[Dict[str, Any]] = None
        self.device_id = self.keyring_manager.get_device_id()

    def login(self, username: str, password: str) -> bool:
        """
        تسجيل الدخول وإنشاء جلسة مشتركة

        Args:
            username: اسم المستخدم
            password: كلمة المرور

        Returns:
            True إذا نجح تسجيل الدخول
        """
        try:
            # تسجيل الدخول عبر API
            response = self.api_client.post(
                "/api/v1/auth/login",
                {
                    "username": username,
                    "password": password,
                    "device_id": self.device_id,
                },
            )

            if response and "access_token" in response:
                token = response["access_token"]
                self.api_client.token = token

                # حفظ Token في Keyring
                self.keyring_manager.set_password(f"session_token_{self.device_id}", token)

                # الحصول على معلومات الجلسة
                self.current_session = {
                    "token": token,
                    "user_id": response.get("user_id"),
                    "username": response.get("username"),
                    "device_id": self.device_id,
                    "created_at": datetime.now().isoformat(),
                }

                self.logger.info(f"✅ تم تسجيل الدخول: {username} (Device: {self.device_id[:8]}...)")
                return True
            else:
                self.logger.error("❌ فشل تسجيل الدخول: استجابة غير صحيحة")
                return False

        except Exception as e:
            self.logger.error(f"❌ فشل تسجيل الدخول: {str(e)}")
            return False

    def logout(self, from_all_devices: bool = False) -> bool:
        """
        تسجيل الخروج

        Args:
            from_all_devices: تسجيل الخروج من جميع الأجهزة

        Returns:
            True إذا نجح تسجيل الخروج
        """
        try:
            if from_all_devices:
                # تسجيل الخروج من جميع الأجهزة
                self.api_client.post("/api/v1/auth/logout-all", {})
            else:
                # تسجيل الخروج من الجهاز الحالي فقط
                self.api_client.post("/api/v1/auth/logout", {"device_id": self.device_id})

            # حذف Token من Keyring
            self.keyring_manager.delete_password(f"session_token_{self.device_id}")

            self.api_client.token = None
            self.current_session = None

            self.logger.info("✅ تم تسجيل الخروج")
            return True

        except Exception as e:
            self.logger.error(f"❌ فشل تسجيل الخروج: {str(e)}")
            return False

    def restore_session(self) -> bool:
        """
        استعادة الجلسة من Keyring

        Returns:
            True إذا نجحت الاستعادة
        """
        try:
            token = self.keyring_manager.get_password(f"session_token_{self.device_id}")
            if not token:
                return False

            # التحقق من صحة Token
            self.api_client.token = token
            user_info = self.api_client.get("/api/v1/auth/me")

            if user_info:
                self.current_session = {
                    "token": token,
                    "user_id": user_info.get("user_id"),
                    "username": user_info.get("username"),
                    "device_id": self.device_id,
                    "created_at": datetime.now().isoformat(),
                }
                self.logger.info("✅ تم استعادة الجلسة")
                return True
            else:
                # Token غير صالح - حذفه
                self.keyring_manager.delete_password(f"session_token_{self.device_id}")
                return False

        except Exception as e:
            self.logger.error(f"❌ فشل استعادة الجلسة: {str(e)}")
            return False

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        الحصول على قائمة الجلسات النشطة

        Returns:
            قائمة بالجلسات النشطة
        """
        try:
            response = self.api_client.get("/api/v1/auth/sessions")
            if response and "sessions" in response:
                return response["sessions"]
            return []
        except Exception as e:
            self.logger.error(f"❌ فشل الحصول على الجلسات: {str(e)}")
            return []

    def is_session_valid(self) -> bool:
        """
        التحقق من صحة الجلسة الحالية

        Returns:
            True إذا كانت الجلسة صالحة
        """
        if not self.current_session or not self.api_client.token:
            return False

        try:
            user_info = self.api_client.get("/api/v1/auth/me")
            return user_info is not None
        except Exception:
            return False
