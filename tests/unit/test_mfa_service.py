"""
Unit Tests for MFAService
اختبارات وحدة MFAService
"""

import pytest
from src.security.mfa_service import MFAService, MFAMethod, MFAConfig


class TestMFAService:
    """اختبارات خدمة MFA"""
    
    @pytest.fixture
    def mfa_service(self, db_manager):
        """إنشاء خدمة MFA"""
        return MFAService(db_manager)
    
    def test_init(self, mfa_service):
        """اختبار التهيئة"""
        assert mfa_service is not None
        assert mfa_service.OTP_LENGTH == 6
        assert mfa_service.OTP_VALIDITY_MINUTES == 5
    
    def test_hash_code(self, mfa_service):
        """اختبار تشفير الكود"""
        code = "123456"
        hashed = mfa_service._hash_code(code)
        
        assert hashed is not None
        assert hashed != code
        assert len(hashed) > 0
    
    def test_enable_mfa_with_user(self, mfa_service, db_manager):
        """اختبار تفعيل MFA مع إنشاء مستخدم"""
        # إنشاء مستخدم أولاً
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, full_name, salt, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("test_user", "hash", "test@example.com", "Test User", "salt123", "user", 1))
            cursor.connection.commit()
            user_id = cursor.lastrowid
        
        methods = [MFAMethod.SMS, MFAMethod.EMAIL]
        phone = "1234567890"
        email = "test@example.com"
        
        result = mfa_service.enable_mfa(
            user_id=user_id,
            methods=methods,
            phone_number=phone,
            email=email
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert result.get('mfa_enabled') is True
    
    def test_get_mfa_config_with_user(self, mfa_service, db_manager):
        """اختبار الحصول على إعدادات MFA مع مستخدم"""
        # إنشاء مستخدم أولاً
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, full_name, salt, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("test_user2", "hash", "test2@example.com", "Test User 2", "salt123", "user", 1))
            cursor.connection.commit()
            user_id = cursor.lastrowid
        
        # تفعيل MFA أولاً
        mfa_service.enable_mfa(
            user_id=user_id,
            methods=[MFAMethod.SMS],
            phone_number="1234567890"
        )
        
        config = mfa_service.get_mfa_config(user_id)
        
        assert config is not None
        assert config.user_id == user_id
    
    def test_disable_mfa_with_user(self, mfa_service, db_manager):
        """اختبار تعطيل MFA مع مستخدم"""
        # إنشاء مستخدم أولاً
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, full_name, salt, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("test_user3", "hash", "test3@example.com", "Test User 3", "salt123", "user", 1))
            cursor.connection.commit()
            user_id = cursor.lastrowid
        
        # تفعيل MFA أولاً
        mfa_service.enable_mfa(
            user_id=user_id,
            methods=[MFAMethod.SMS],
            phone_number="1234567890"
        )
        
        # تعطيل MFA
        result = mfa_service.disable_mfa(user_id)
        assert result is True

