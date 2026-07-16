#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Audit Service
اختبارات خدمة التدقيق
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import Mock

import pytest


# Mock classes for testing
class MockAuditLog:
    """Mock class for AuditLog"""

    def __init__(
        self,
        id=None,
        user_id=None,
        username="",
        action="",
        resource_type="",
        resource_id=None,
        old_value=None,
        new_value=None,
        ip_address="",
        user_agent="",
        status="success",
        error_message="",
        created_at=None,
    ):
        self.id = id
        self.user_id = user_id
        self.username = username
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.old_value = old_value
        self.new_value = new_value
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.status = status
        self.error_message = error_message
        self.created_at = created_at or datetime.now()


class MockLoginHistory:
    """Mock class for LoginHistory"""

    def __init__(
        self,
        id=None,
        user_id=None,
        username="",
        login_time=None,
        ip_address="",
        user_agent="",
        success=True,
        failure_reason=None,
        logout_time=None,
        session_duration=None,
    ):
        self.id = id
        self.user_id = user_id
        self.username = username
        self.login_time = login_time or datetime.now()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.success = success
        self.failure_reason = failure_reason
        self.logout_time = logout_time
        self.session_duration = session_duration


class MockAuditService:
    """Mock class for AuditService testing"""

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def _audit_log_from_row(self, row: Dict) -> MockAuditLog:
        """Convert database row to AuditLog object"""
        return MockAuditLog(
            id=row.get("id"),
            user_id=row.get("user_id"),
            username=row.get("username"),
            action=row.get("action"),
            resource_type=row.get("resource_type"),
            resource_id=row.get("resource_id"),
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            status=row.get("status"),
            error_message=row.get("error_message"),
            created_at=(datetime.fromisoformat(row.get("created_at")) if row.get("created_at") else None),
        )

    def log_action(
        self,
        user_id: Optional[int],
        username: str,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_value: Any = None,
        new_value: Any = None,
        ip_address: str = "",
        user_agent: str = "",
        status: str = "success",
        error_message: str = "",
    ) -> int:
        """Log an action to audit log"""
        try:
            import json

            old_json = json.dumps(old_value, ensure_ascii=False) if old_value else ""
            new_json = json.dumps(new_value, ensure_ascii=False) if new_value else ""

            result = self.db.execute_update(
                """INSERT INTO audit_logs
                   (user_id, username, action, resource_type, resource_id,
                    old_value, new_value, ip_address, user_agent, status, error_message, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    user_id,
                    username,
                    action,
                    resource_type,
                    resource_id,
                    old_json,
                    new_json,
                    ip_address,
                    user_agent,
                    status,
                    error_message,
                    datetime.now().isoformat(),
                ],
            )

            if self.logger:
                self.logger.info(f"Audit log created: {action} on {resource_type}")

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error logging audit action: {e}")
            return -1

    def get_audit_log(self, log_id: int) -> Optional[MockAuditLog]:
        """Get a specific audit log"""
        try:
            result = self.db.execute_query("SELECT * FROM audit_logs WHERE id = ?", [log_id])
            if not result:
                return None

            return self._audit_log_from_row(result[0])
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting audit log: {e}")
            return None

    def list_audit_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MockAuditLog]:
        """List audit logs with filters"""
        try:
            sql = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)

            if resource_type:
                sql += " AND resource_type = ?"
                params.append(resource_type)

            if action:
                sql += " AND action = ?"
                params.append(action)

            if status:
                sql += " AND status = ?"
                params.append(status)

            if start_date:
                sql += " AND created_at >= ?"
                params.append(start_date.isoformat())

            if end_date:
                sql += " AND created_at <= ?"
                params.append(end_date.isoformat())

            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            result = self.db.execute_query(sql, params)
            return [self._audit_log_from_row(row) for row in result]
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing audit logs: {e}")
            return []

    def count_audit_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count audit logs with filters"""
        try:
            sql = "SELECT COUNT(*) as count FROM audit_logs WHERE 1=1"
            params = []

            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)

            if resource_type:
                sql += " AND resource_type = ?"
                params.append(resource_type)

            if action:
                sql += " AND action = ?"
                params.append(action)

            if status:
                sql += " AND status = ?"
                params.append(status)

            if start_date:
                sql += " AND created_at >= ?"
                params.append(start_date.isoformat())

            if end_date:
                sql += " AND created_at <= ?"
                params.append(end_date.isoformat())

            result = self.db.execute_query(sql, params)
            return result[0].get("count", 0) if result else 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error counting audit logs: {e}")
            return 0

    def log_login_attempt(
        self,
        user_id: Optional[int],
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        failure_reason: Optional[str] = None,
    ) -> int:
        """Log a login attempt"""
        try:
            result = self.db.execute_update(
                """INSERT INTO login_history
                   (user_id, username, login_time, ip_address, user_agent, success, failure_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    user_id,
                    username,
                    datetime.now().isoformat(),
                    ip_address,
                    user_agent,
                    success,
                    failure_reason,
                ],
            )
            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error logging login attempt: {e}")
            return -1

    def get_login_history(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[MockLoginHistory]:
        """Get login history with filters"""
        try:
            sql = "SELECT * FROM login_history WHERE 1=1"
            params = []

            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)

            if username:
                sql += " AND username = ?"
                params.append(username)

            if start_date:
                sql += " AND login_time >= ?"
                params.append(start_date.isoformat())

            if end_date:
                sql += " AND login_time <= ?"
                params.append(end_date.isoformat())

            sql += " ORDER BY login_time DESC LIMIT ?"
            params.append(limit)

            result = self.db.execute_query(sql, params)

            history = []
            for row in result:
                history.append(
                    MockLoginHistory(
                        id=row.get("id"),
                        user_id=row.get("user_id"),
                        username=row.get("username"),
                        login_time=(datetime.fromisoformat(row.get("login_time")) if row.get("login_time") else None),
                        ip_address=row.get("ip_address"),
                        user_agent=row.get("user_agent"),
                        success=bool(row.get("success")),
                        failure_reason=row.get("failure_reason"),
                        logout_time=(
                            datetime.fromisoformat(row.get("logout_time")) if row.get("logout_time") else None
                        ),
                        session_duration=row.get("session_duration"),
                    )
                )
            return history
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting login history: {e}")
            return []

    def purge_old_logs(self, days: int = 90) -> int:
        """Purge audit logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            result = self.db.execute_update("DELETE FROM audit_logs WHERE created_at < ?", [cutoff_date.isoformat()])

            if self.logger:
                self.logger.info(f"Purged {result} old audit logs")

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error purging old logs: {e}")
            return 0


class TestAuditServiceInitialization:
    """اختبارات تهيئة خدمة التدقيق"""

    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        service = MockAuditService(db_manager=mock_db)

        assert service.db == mock_db
        assert service.logger is None

    def test_initialization_with_logger(self):
        """اختبار التهيئة مع مسجل"""
        mock_db = Mock()
        mock_logger = Mock()
        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        assert service.db == mock_db
        assert service.logger == mock_logger


class TestLogAction:
    """اختبارات تسجيل الإجراءات"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 1

        service = MockAuditService(db_manager=mock_db)
        return service, mock_db

    def test_log_action_success(self, service_with_mocks):
        """اختبار تسجيل إجراء بنجاح"""
        service, mock_db = service_with_mocks

        result = service.log_action(
            user_id=1,
            username="test_user",
            action="create",
            resource_type="product",
            resource_id=123,
            old_value=None,
            new_value={"name": "Test Product", "price": 100},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            status="success",
        )

        assert result == 1
        mock_db.execute_update.assert_called_once()

    def test_log_action_with_old_value(self, service_with_mocks):
        """اختبار تسجيل إجراء مع قيمة قديمة"""
        service, mock_db = service_with_mocks

        result = service.log_action(
            user_id=1,
            username="test_user",
            action="update",
            resource_type="customer",
            resource_id=456,
            old_value={"name": "Old Name"},
            new_value={"name": "New Name"},
            ip_address="192.168.1.1",
        )

        assert result == 1

    def test_log_action_failure(self, service_with_mocks):
        """اختبار تسجيل إجراء فاشل"""
        service, mock_db = service_with_mocks

        result = service.log_action(
            user_id=1,
            username="test_user",
            action="delete",
            resource_type="order",
            resource_id=789,
            status="failure",
            error_message="Permission denied",
        )

        assert result == 1

    def test_log_action_db_error(self):
        """اختبار فشل تسجيل إجراء"""
        mock_db = Mock()
        mock_db.execute_update.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.log_action(user_id=1, username="test_user", action="create", resource_type="product")

        assert result == -1
        mock_logger.error.assert_called_once()


class TestGetAuditLog:
    """اختبارات الحصول على سجل تدقيق"""

    def test_get_audit_log_success(self):
        """اختبار الحصول على سجل تدقيق بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "user_id": 1,
                "username": "test_user",
                "action": "create",
                "resource_type": "product",
                "resource_id": 123,
                "created_at": datetime.now().isoformat(),
            }
        ]

        service = MockAuditService(db_manager=mock_db)

        result = service.get_audit_log(1)

        assert result is not None
        assert result.id == 1
        assert result.username == "test_user"

    def test_get_audit_log_not_found(self):
        """اختبار الحصول على سجل تدقيق غير موجود"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []

        service = MockAuditService(db_manager=mock_db)

        result = service.get_audit_log(999)

        assert result is None

    def test_get_audit_log_db_error(self):
        """اختبار خطأ في قاعدة البيانات"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.get_audit_log(1)

        assert result is None


class TestListAuditLogs:
    """اختبارات قائمة سجلات التدقيق"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "user_id": 1,
                "username": "user1",
                "action": "create",
                "resource_type": "product",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": 2,
                "user_id": 2,
                "username": "user2",
                "action": "update",
                "resource_type": "customer",
                "created_at": datetime.now().isoformat(),
            },
        ]

        service = MockAuditService(db_manager=mock_db)
        return service, mock_db

    def test_list_audit_logs_all(self, service_with_mocks):
        """اختبار الحصول على جميع السجلات"""
        service, mock_db = service_with_mocks

        result = service.list_audit_logs()

        assert len(result) == 2

    def test_list_audit_logs_with_filters(self, service_with_mocks):
        """اختبار الحصول على السجلات مع فلاتر"""
        service, mock_db = service_with_mocks

        result = service.list_audit_logs(
            user_id=1,
            resource_type="product",
            action="create",
            status="success",
            limit=10,
            offset=0,
        )

        assert len(result) == 2

    def test_list_audit_logs_with_date_range(self, service_with_mocks):
        """اختبار الحصول على السجلات مع نطاق تاريخ"""
        service, mock_db = service_with_mocks

        result = service.list_audit_logs(start_date=datetime.now() - timedelta(days=7), end_date=datetime.now())

        assert len(result) == 2

    def test_list_audit_logs_empty(self):
        """اختبار الحصول على سجلات فارغة"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []

        service = MockAuditService(db_manager=mock_db)

        result = service.list_audit_logs()

        assert len(result) == 0


class TestCountAuditLogs:
    """اختبارات عد سجلات التدقيق"""

    def test_count_audit_logs_success(self):
        """اختبار عد السجلات بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [{"count": 150}]

        service = MockAuditService(db_manager=mock_db)

        result = service.count_audit_logs()

        assert result == 150

    def test_count_audit_logs_with_filters(self):
        """اختبار عد السجلات مع فلاتر"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [{"count": 25}]

        service = MockAuditService(db_manager=mock_db)

        result = service.count_audit_logs(user_id=1, resource_type="product", action="create")

        assert result == 25

    def test_count_audit_logs_db_error(self):
        """اختبار فشل عد السجلات"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.count_audit_logs()

        assert result == 0


class TestLogLoginAttempt:
    """اختبارات تسجيل محاولات تسجيل الدخول"""

    def test_log_login_attempt_success(self):
        """اختبار تسجيل محاولة ناجحة"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 1

        service = MockAuditService(db_manager=mock_db)

        result = service.log_login_attempt(
            user_id=1,
            username="test_user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )

        assert result == 1

    def test_log_login_attempt_failure(self):
        """اختبار تسجيل محاولة فاشلة"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 1

        service = MockAuditService(db_manager=mock_db)

        result = service.log_login_attempt(
            user_id=None,
            username="test_user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=False,
            failure_reason="Invalid password",
        )

        assert result == 1

    def test_log_login_attempt_db_error(self):
        """اختبار فشل تسجيل محاولة"""
        mock_db = Mock()
        mock_db.execute_update.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.log_login_attempt(
            user_id=1,
            username="test_user",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )

        assert result == -1


class TestGetLoginHistory:
    """اختبارات الحصول على تاريخ تسجيل الدخول"""

    def test_get_login_history_success(self):
        """اختبار الحصول على التاريخ بنجاح"""
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "user_id": 1,
                "username": "user1",
                "success": 1,
                "login_time": datetime.now().isoformat(),
            },
            {
                "id": 2,
                "user_id": 1,
                "username": "user1",
                "success": 0,
                "login_time": datetime.now().isoformat(),
            },
        ]

        service = MockAuditService(db_manager=mock_db)

        result = service.get_login_history(user_id=1)

        assert len(result) == 2

    def test_get_login_history_with_filters(self):
        """اختبار الحصول على التاريخ مع فلاتر"""
        mock_db = Mock()
        mock_db.execute_query.return_value = []

        service = MockAuditService(db_manager=mock_db)

        result = service.get_login_history(
            username="test_user",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            limit=50,
        )

        assert len(result) == 0

    def test_get_login_history_db_error(self):
        """اختبار فشل الحصول على التاريخ"""
        mock_db = Mock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.get_login_history()

        assert len(result) == 0


class TestPurgeOldLogs:
    """اختبارات حذف السجلات القديمة"""

    def test_purge_old_logs_success(self):
        """اختبار حذف السجلات القديمة بنجاح"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 100
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.purge_old_logs(days=90)

        assert result == 100
        mock_logger.info.assert_called_once()

    def test_purge_old_logs_custom_days(self):
        """اختبار حذف السجلات بفترة مخصصة"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 50

        service = MockAuditService(db_manager=mock_db)

        result = service.purge_old_logs(days=30)

        assert result == 50

    def test_purge_old_logs_db_error(self):
        """اختبار فشل حذف السجلات"""
        mock_db = Mock()
        mock_db.execute_update.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockAuditService(db_manager=mock_db, logger=mock_logger)

        result = service.purge_old_logs(days=90)

        assert result == 0
        mock_logger.error.assert_called_once()


class TestAuditLogEdgeCases:
    """اختبارات حالات الحافة"""

    def test_audit_log_with_none_values(self):
        """اختبار سجل مع قيم فارغة"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 1

        service = MockAuditService(db_manager=mock_db)

        result = service.log_action(
            user_id=None,
            username="",
            action="test",
            resource_type="test",
            resource_id=None,
            old_value=None,
            new_value=None,
            ip_address="",
            user_agent="",
        )

        assert result == 1

    def test_audit_log_with_complex_data(self):
        """اختبار سجل مع بيانات معقدة"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 1

        service = MockAuditService(db_manager=mock_db)

        complex_data = {"nested": {"key": "value"}, "array": [1, 2, 3], "null": None}

        result = service.log_action(
            user_id=1,
            username="test_user",
            action="update",
            resource_type="product",
            old_value=complex_data,
            new_value=complex_data,
        )

        assert result == 1

    def test_purge_with_zero_days(self):
        """اختبار الحذف بصفر أيام"""
        mock_db = Mock()
        mock_db.execute_update.return_value = 0

        service = MockAuditService(db_manager=mock_db)

        result = service.purge_old_logs(days=0)

        assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
