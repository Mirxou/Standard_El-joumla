import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.user_service import UserService, SecuritySettings
from src.models.user import User, UserRole, Permission

@pytest.fixture
def mock_db_manager():
    """Mock لمدير قاعدة البيانات"""
    return MagicMock()

@pytest.fixture
def mock_user_manager():
    """Mock لمدير المستخدمين"""
    return MagicMock()

@pytest.fixture
def service(mock_db_manager, mock_user_manager):
    """إنشاء خدمة المستخدمين مع mock للتبعيات"""
    with patch('src.services.user_service.UserManager', return_value=mock_user_manager):
        with patch('src.services.user_service.DatabaseLogger'):
            # تعطيل تحميل الإعدادات من قاعدة البيانات للاختبار
            with patch.object(UserService, '_load_security_settings'):
                service = UserService(mock_db_manager)
                # استخدام إعدادات أمان افتراضية يمكن التنبؤ بها
                service.security_settings = SecuritySettings(max_login_attempts=3)
                return service

class TestUserService:
    """اختبارات وحدة لخدمة المستخدمين"""

    def test_authenticate_user_success(self, service, mock_user_manager):
        """اختبار مصادقة مستخدم بنجاح"""
        mock_user = User(id=1, username="testuser", role=UserRole.ADMIN, is_active=True, is_locked=False)
        mock_user_manager.authenticate_user.return_value = mock_user
        
        # محاكاة عدم وجود محاولات فاشلة
        service.db.execute_query.return_value = [{'count': 0}]
        
        success, session, message = service.authenticate_user("testuser", "password")
        
        assert success is True
        assert session is not None
        assert message is None
        assert session.username == "testuser"
        mock_user_manager.authenticate_user.assert_called_once_with("testuser", "password")

    def test_authenticate_user_failure_wrong_password(self, service, mock_user_manager):
        """اختبار فشل المصادقة بسبب كلمة مرور خاطئة"""
        mock_user_manager.authenticate_user.return_value = None
        service.db.execute_query.return_value = [{'count': 0}]

        success, session, message = service.authenticate_user("testuser", "wrongpassword")

        assert success is False
        assert session is None
        assert "غير صحيحة" in message

    def test_user_lockout_after_failed_attempts(self, service, mock_user_manager):
        """اختبار قفل المستخدم بعد 3 محاولات فاشلة"""
        # محاكاة أن المستخدم مقفل
        service.db.execute_query.return_value = [{'count': 3}]

        success, session, message = service.authenticate_user("lockeduser", "password")

        assert success is False
        assert session is None
        assert "مقفل مؤقتاً" in message
        # التأكد من عدم محاولة المصادقة إذا كان المستخدم مقفلاً
        mock_user_manager.authenticate_user.assert_not_called()

    def test_change_password_success(self, service, mock_user_manager):
        """اختبار تغيير كلمة المرور بنجاح"""
        user_id = 1
        mock_user = User(id=user_id, password_hash="old_hash")
        mock_user_manager.get_by_id.return_value = mock_user
        mock_user_manager.verify_password.return_value = True
        mock_user_manager.change_password.return_value = True
        
        # محاكاة أن كلمة المرور الجديدة قوية
        with patch.object(service, '_validate_password_strength', return_value=(True, None)):
            success, message = service.change_password(user_id, "old_password", "NewPassword123")

        assert success is True
        assert message is None
        mock_user_manager.change_password.assert_called_once_with(user_id, "NewPassword123")

    def test_change_password_wrong_old_password(self, service, mock_user_manager):
        """اختبار فشل تغيير كلمة المرور بسبب كلمة مرور قديمة خاطئة"""
        user_id = 1
        mock_user = User(id=user_id, password_hash="old_hash")
        mock_user_manager.get_by_id.return_value = mock_user
        mock_user_manager.verify_password.return_value = False # كلمة المرور القديمة خاطئة

        success, message = service.change_password(user_id, "wrong_old_password", "NewPassword123")

        assert success is False
        assert "غير صحيحة" in message
        mock_user_manager.change_password.assert_not_called()

    def test_check_permission_success(self, service, mock_user_manager):
        """اختبار التحقق من صلاحية موجودة لدى المستخدم"""
        mock_user = User(id=1, username="testuser", role=UserRole.ADMIN)
        # محاكاة أن المدير لديه جميع الصلاحيات
        mock_user.permissions = {p for p in Permission}
        mock_user_manager.get_by_id.return_value = mock_user
        
        # محاكاة جلسة صالحة
        with patch.object(service, 'validate_session') as mock_validate:
            mock_session = MagicMock(user_id=1)
            mock_validate.return_value = (True, mock_session)
            
            has_permission = service.check_permission("valid_session_id", Permission.USERS_MANAGE)
            
            assert has_permission is True
    
    def test_validate_session_success(self, service):
        """اختبار التحقق من جلسة صالحة"""
        session = service._create_session(User(id=1, username="testuser", role=UserRole.ADMIN), "127.0.0.1", "pytest-agent")
        session_id = session.session_id
        
        valid, returned_session = service.validate_session(session_id)
        
        assert valid is True
        assert returned_session is not None
        assert returned_session.session_id == session_id
    
    def test_validate_session_expired(self, service):
        """اختبار التحقق من جلسة منتهية الصلاحية"""
        # إنشاء جلسة منتهية الصلاحية
        with patch.object(service, 'security_settings') as mock_settings:
            mock_settings.jwt_expiry_hours = -1  # انتهت الصلاحية
            session = service._create_session(User(id=1, username="testuser", role=UserRole.ADMIN), "127.0.0.1", "pytest-agent")
        
        # محاولة التحقق من جلسة منتهية
        valid, returned_session = service.validate_session("invalid_session")
        
        assert valid is False
    
    def test_logout_user(self, service):
        """اختبار تسجيل خروج المستخدم"""
        session = service._create_session(User(id=1, username="testuser", role=UserRole.CASHIER), "127.0.0.1", "pytest-agent")
        session_id = session.session_id
        
        result = service.logout_user(session_id)
        
        assert result is True
        assert session_id not in service.active_sessions
    
    def test_change_password_weak_password(self, service, mock_user_manager):
        """اختبار فشل تغيير كلمة المرور بسبب كلمة مرور ضعيفة"""
        user_id = 1
        mock_user = User(id=user_id, password_hash="old_hash")
        mock_user_manager.get_by_id.return_value = mock_user
        mock_user_manager.verify_password.return_value = True
        
        # محاكاة أن كلمة المرور الجديدة ضعيفة
        with patch.object(service, '_validate_password_strength', return_value=(False, "كلمة المرور ضعيفة")):
            success, message = service.change_password(user_id, "old_password", "weak")
        
        assert success is False
        assert "ضعيفة" in message
        mock_user_manager.change_password.assert_not_called()




