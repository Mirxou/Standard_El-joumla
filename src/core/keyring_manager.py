#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير Keyring - Keyring Manager
إدارة تخزين المفاتيح بشكل آمن باستخدام Keyring
"""

import platform
from typing import Optional
from src.utils.logger import setup_logger

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None


class KeyringManager:
    """مدير Keyring لتخزين المفاتيح بشكل آمن"""
    
    SERVICE_NAME = "LogicalERP"
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        if not KEYRING_AVAILABLE:
            self.logger.warning("⚠️ مكتبة keyring غير متوفرة - سيتم استخدام تخزين غير آمن")
    
    def get_device_id(self) -> str:
        """
        الحصول على معرف الجهاز الفريد
        
        Returns:
            معرف الجهاز
        """
        import uuid
        import os
        
        # محاولة قراءة معرف الجهاز من ملف محلي
        device_id_file = os.path.join(
            os.path.expanduser("~"),
            ".logical_erp_device_id"
        )
        
        if os.path.exists(device_id_file):
            try:
                with open(device_id_file, 'r') as f:
                    device_id = f.read().strip()
                if device_id:
                    return device_id
            except Exception:
                pass
        
        # إنشاء معرف جديد
        device_id = str(uuid.uuid4())
        try:
            with open(device_id_file, 'w') as f:
                f.write(device_id)
            os.chmod(device_id_file, 0o600)  # صلاحيات محدودة
        except Exception as e:
            self.logger.warning(f"فشل حفظ معرف الجهاز: {str(e)}")
        
        return device_id
    
    def set_password(self, key: str, password: str) -> bool:
        """
        حفظ كلمة مرور في Keyring
        
        Args:
            key: المفتاح (مثل device_id)
            password: كلمة المرور
            
        Returns:
            True إذا نجح الحفظ
        """
        if not KEYRING_AVAILABLE:
            self.logger.error("مكتبة keyring غير متوفرة")
            return False
        
        try:
            keyring.set_password(self.SERVICE_NAME, key, password)
            self.logger.info(f"✅ تم حفظ المفتاح في Keyring: {key[:8]}...")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل حفظ المفتاح في Keyring: {str(e)}")
            return False
    
    def get_password(self, key: str) -> Optional[str]:
        """
        الحصول على كلمة مرور من Keyring
        
        Args:
            key: المفتاح (مثل device_id)
            
        Returns:
            كلمة المرور أو None إذا لم توجد
        """
        if not KEYRING_AVAILABLE:
            self.logger.error("مكتبة keyring غير متوفرة")
            return None
        
        try:
            password = keyring.get_password(self.SERVICE_NAME, key)
            if password:
                self.logger.info(f"✅ تم استرجاع المفتاح من Keyring: {key[:8]}...")
            return password
        except Exception as e:
            self.logger.error(f"❌ فشل استرجاع المفتاح من Keyring: {str(e)}")
            return None
    
    def delete_password(self, key: str) -> bool:
        """
        حذف كلمة مرور من Keyring
        
        Args:
            key: المفتاح
            
        Returns:
            True إذا نجح الحذف
        """
        if not KEYRING_AVAILABLE:
            return False
        
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
            self.logger.info(f"✅ تم حذف المفتاح من Keyring: {key[:8]}...")
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ فشل حذف المفتاح من Keyring: {str(e)}")
            return False
    
    def get_database_password(self, device_id: Optional[str] = None) -> Optional[str]:
        """
        الحصول على كلمة مرور قاعدة البيانات المحلية
        
        Args:
            device_id: معرف الجهاز (اختياري - سيتم الحصول عليه تلقائياً)
            
        Returns:
            كلمة مرور قاعدة البيانات
        """
        if device_id is None:
            device_id = self.get_device_id()
        
        return self.get_password(f"db_password_{device_id}")
    
    def set_database_password(self, password: str, device_id: Optional[str] = None) -> bool:
        """
        حفظ كلمة مرور قاعدة البيانات المحلية
        
        Args:
            password: كلمة المرور
            device_id: معرف الجهاز (اختياري - سيتم الحصول عليه تلقائياً)
            
        Returns:
            True إذا نجح الحفظ
        """
        if device_id is None:
            device_id = self.get_device_id()
        
        return self.set_password(f"db_password_{device_id}", password)
    
    def generate_secure_password(self, length: int = 32) -> str:
        """
        توليد كلمة مرور آمنة
        
        Args:
            length: طول كلمة المرور
            
        Returns:
            كلمة مرور آمنة
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
