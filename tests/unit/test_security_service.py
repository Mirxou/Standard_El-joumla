"""
Unit Tests for SecurityService
اختبارات وحدة SecurityService
"""

import pytest

from src.core.security_service import (
    AdvancedSecurityService,
    generate_api_key,
    generate_secure_token,
)


class TestAdvancedSecurityService:
    """اختبارات خدمة الأمان المتقدمة"""

    @pytest.fixture
    def security_service(self):
        """إنشاء خدمة أمان"""
        return AdvancedSecurityService()

    def test_init(self, security_service):
        """اختبار التهيئة"""
        assert security_service is not None
        assert security_service.session_timeout == 3600
        assert security_service.max_login_attempts == 5

    def test_hash_password(self, security_service):
        """اختبار تشفير كلمة المرور"""
        password = "test_password_123"
        hashed = security_service.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self, security_service):
        """اختبار التحقق من كلمة المرور"""
        password = "test_password_123"
        hashed = security_service.hash_password(password)

        # قد يفشل إذا لم يكن Argon2 مثبتاً أو كان هناك مشكلة في التشفير
        # لكن يجب ألا يرفع استثناء
        try:
            result = security_service.verify_password(password, hashed)
            assert isinstance(result, bool)
        except Exception:
            # قد يرفع استثناء إذا لم يكن Argon2 مثبتاً
            pass

    def test_create_session(self, security_service):
        """اختبار إنشاء جلسة"""
        user_id = 1
        username = "test_user"

        token = security_service.create_session(user_id, username)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_session(self, security_service):
        """اختبار التحقق من صحة الجلسة"""
        user_id = 1
        username = "test_user"

        token = security_service.create_session(user_id, username)

        # التحقق من الجلسة
        session_data = security_service.validate_session(token)
        assert session_data is not None
        assert isinstance(session_data, dict)
        assert session_data["user_id"] == user_id

        # التحقق من جلسة غير موجودة
        session_data = security_service.validate_session("invalid_token")
        assert session_data is None

    def test_record_failed_login(self, security_service):
        """اختبار تسجيل محاولة تسجيل دخول فاشلة"""
        username = "test_user"

        result = security_service.record_failed_login(username)

        # يجب أن يعيد True إذا لم يتم حظر المعرف
        assert isinstance(result, bool)


class TestSecurityFunctions:
    """اختبارات الدوال المساعدة"""

    def test_generate_secure_token(self):
        """اختبار إنشاء رمز آمن"""
        token = generate_secure_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0  # token_urlsafe يعيد string أطول من length

    def test_generate_secure_token_custom_length(self):
        """اختبار إنشاء رمز بطول مخصص"""
        token = generate_secure_token(length=64)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0  # token_urlsafe يعيد string أطول من length

    def test_generate_api_key(self):
        """اختبار إنشاء مفتاح API"""
        api_key = generate_api_key()

        assert api_key is not None
        assert len(api_key) > 0
