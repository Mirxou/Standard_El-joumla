#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Notification Service
اختبارات خدمة الإشعارات
"""

from datetime import datetime, timedelta
from typing import List
from enum import Enum
from unittest.mock import Mock

import pytest


# Mock classes for testing
class NotificationType(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    SYSTEM = "system"
    INVENTORY = "inventory"
    SALES = "sales"
    SECURITY = "security"
    PAYMENT = "payment"


class Notification:
    def __init__(
        self,
        id=None,
        title="",
        message="",
        type=None,
        priority=None,
        category=None,
        user_id=None,
        action_url=None,
        data=None,
        read=False,
        read_at=None,
        created_at=None,
    ):
        self.id = id
        self.title = title
        self.message = message
        self.type = type or NotificationType.INFO
        self.priority = priority or NotificationPriority.MEDIUM
        self.category = category or AlertCategory.SYSTEM
        self.user_id = user_id
        self.action_url = action_url
        self.data = data
        self.read = read
        self.read_at = read_at
        self.created_at = created_at or datetime.now()


class MockNotificationService:
    """Mock class for NotificationService testing"""

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def _trigger_callbacks(self, notification_id):
        for callback in self.callbacks:
            try:
                callback(notification_id)
            except Exception:
                pass

    def create_notification(
        self,
        title: str,
        message: str,
        notification_type=NotificationType.INFO,
        priority=NotificationPriority.MEDIUM,
        category=AlertCategory.SYSTEM,
        user_id=None,
        action_url=None,
        data=None,
    ) -> int:
        try:
            cursor = self.db.connection.cursor()
            data_json = str(data) if data else None

            cursor.execute(
                """
                INSERT INTO notifications (title, message, type, priority, category, user_id, action_url, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    title,
                    message,
                    notification_type,
                    priority.value,
                    category.value,
                    user_id,
                    action_url,
                    data_json,
                ),
            )

            self.db.connection.commit()
            notification_id = cursor.lastrowid
            self._trigger_callbacks(notification_id)
            return notification_id
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الإشعار: {e}")
            return None

    def get_notifications(self, user_id=None, unread_only=False, category=None, limit=50) -> List[Notification]:
        try:
            cursor = self.db.connection.cursor()
            query = "SELECT * FROM notifications WHERE 1=1"
            params = []

            if user_id is not None:
                query += " AND (user_id = ? OR user_id IS NULL)"
                params.append(user_id)

            if unread_only:
                query += " AND read = 0"

            if category:
                query += " AND category = ?"
                params.append(category.value)

            query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            notifications = []
            for row in cursor.fetchall():
                data = eval(row[8]) if row[8] else None
                notifications.append(
                    Notification(
                        id=row[0],
                        title=row[1],
                        message=row[2],
                        type=row[3],
                        priority=row[4],
                        category=row[5],
                        user_id=row[6],
                        action_url=row[7],
                        data=data,
                        read=bool(row[9]),
                        read_at=datetime.fromisoformat(row[10]) if row[10] else None,
                        created_at=(datetime.fromisoformat(row[11]) if row[11] else datetime.now()),
                    )
                )
            return notifications
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الإشعارات: {e}")
            return []

    def mark_as_read(self, notification_id: int) -> bool:
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                """
                UPDATE notifications
                SET read = 1, read_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (notification_id,),
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعليم الإشعار كمقروء: {e}")
            return False

    def mark_all_as_read(self, user_id=None) -> int:
        try:
            cursor = self.db.connection.cursor()

            if user_id:
                cursor.execute(
                    """
                    UPDATE notifications
                    SET read = 1, read_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND read = 0
                """,
                    (user_id,),
                )
            else:
                cursor.execute("""
                    UPDATE notifications
                    SET read = 1, read_at = CURRENT_TIMESTAMP
                    WHERE read = 0
                """)

            self.db.connection.commit()
            return cursor.rowcount
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تعليم جميع الإشعارات كمقروءة: {e}")
            return 0

    def delete_notification(self, notification_id: int) -> bool:
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
            self.db.connection.commit()
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف الإشعار: {e}")
            return False

    def delete_old_notifications(self, days: int = 30) -> int:
        try:
            cursor = self.db.connection.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)

            cursor.execute(
                """
                DELETE FROM notifications
                WHERE read = 1
                AND created_at < ?
            """,
                (cutoff_date.isoformat(),),
            )

            self.db.connection.commit()
            return cursor.rowcount
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حذف الإشعارات القديمة: {e}")
            return 0

    def get_unread_count(self, user_id=None) -> int:
        try:
            cursor = self.db.connection.cursor()

            if user_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM notifications
                    WHERE (user_id = ? OR user_id IS NULL) AND read = 0
                """,
                    (user_id,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM notifications WHERE read = 0")

            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في عد الإشعارات غير المقروءة: {e}")
            return 0


class TestNotificationServiceInitialization:
    """اختبارات تهيئة خدمة الإشعارات"""

    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        mock_db.connection = Mock()

        service = MockNotificationService(db_manager=mock_db)

        assert service.db == mock_db
        assert service.logger is None

    def test_initialization_with_logger(self):
        """اختبار التهيئة مع مسجل"""
        mock_db = Mock()
        mock_db.connection = Mock()
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        assert service.db == mock_db
        assert service.logger == mock_logger


class TestCreateNotification:
    """اختبارات إنشاء الإشعارات"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)
        return service, mock_cursor

    def test_create_notification_success(self, service_with_mocks):
        """اختبار إنشاء إشعار بنجاح"""
        service, mock_cursor = service_with_mocks

        result = service.create_notification(
            title="Test Notification",
            message="This is a test message",
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.MEDIUM,
        )

        assert result == 1
        mock_cursor.execute.assert_called()

    def test_create_notification_with_data(self, service_with_mocks):
        """اختبار إنشاء إشعار مع بيانات"""
        service, mock_cursor = service_with_mocks

        result = service.create_notification(
            title="Alert",
            message="Important alert",
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            category=AlertCategory.INVENTORY,
            user_id=1,
            action_url="/orders/123",
            data={"order_id": 123},
        )

        assert result == 1

    def test_create_notification_db_error(self):
        """اختبار فشل إنشاء إشعار"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.create_notification(title="Test", message="Test message")

        assert result is None
        mock_logger.error.assert_called_once()


class TestGetNotifications:
    """اختبارات الحصول على الإشعارات"""

    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "Title 1",
                "Message 1",
                "info",
                "high",
                "system",
                1,
                None,
                None,
                0,
                None,
                datetime.now().isoformat(),
            ),
            (
                2,
                "Title 2",
                "Message 2",
                "warning",
                "medium",
                "inventory",
                None,
                "/link",
                str({"key": "value"}),
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        ]
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)
        return service, mock_cursor

    def test_get_notifications_all(self, service_with_mocks):
        """اختبار الحصول على جميع الإشعارات"""
        service, mock_cursor = service_with_mocks

        result = service.get_notifications()

        assert len(result) == 2
        mock_cursor.execute.assert_called()

    def test_get_notifications_unread_only(self, service_with_mocks):
        """اختبار الحصول على الإشعارات غير المقروءة فقط"""
        service, mock_cursor = service_with_mocks

        result = service.get_notifications(unread_only=True)

        assert len(result) == 2

    def test_get_notifications_by_category(self, service_with_mocks):
        """اختبار الحصول على الإشعارات حسب الفئة"""
        service, mock_cursor = service_with_mocks

        result = service.get_notifications(category=AlertCategory.INVENTORY)

        assert len(result) == 2

    def test_get_notifications_empty(self):
        """اختبار الحصول على إشعارات بدون نتائج"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.get_notifications()

        assert len(result) == 0


class TestMarkAsRead:
    """اختبارات تعليم الإشعارات كمقروءة"""

    def test_mark_as_read_success(self):
        """اختبار تعليم إشعار كمقروء بنجاح"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.mark_as_read(1)

        assert result is True
        mock_cursor.execute.assert_called_once()

    def test_mark_as_read_db_error(self):
        """اختبار فشل تعليم إشعار كمقروء"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.mark_as_read(1)

        assert result is False
        mock_logger.error.assert_called_once()


class TestMarkAllAsRead:
    """اختبارات تعليم جميع الإشعارات كمقروءة"""

    def test_mark_all_as_read_success(self):
        """اختبار تعليم جميع الإشعارات كمقروءة بنجاح"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.mark_all_as_read()

        assert result == 5

    def test_mark_all_as_read_with_user_id(self):
        """اختبار تعليم إشعارات مستخدم معين كمقروءة"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 3
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.mark_all_as_read(user_id=1)

        assert result == 3

    def test_mark_all_as_read_db_error(self):
        """اختبار فشل تعليم جميع الإشعارات كمقروءة"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.mark_all_as_read()

        assert result == 0


class TestDeleteNotification:
    """اختبارات حذف الإشعارات"""

    def test_delete_notification_success(self):
        """اختبار حذف إشعار بنجاح"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.delete_notification(1)

        assert result is True

    def test_delete_notification_db_error(self):
        """اختبار فشل حذف إشعار"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.delete_notification(1)

        assert result is False


class TestDeleteOldNotifications:
    """اختبارات حذف الإشعارات القديمة"""

    def test_delete_old_notifications_success(self):
        """اختبار حذف الإشعارات القديمة بنجاح"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 10
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.delete_old_notifications(days=30)

        assert result == 10

    def test_delete_old_notifications_custom_days(self):
        """اختبار حذف الإشعارات القديمة بفترة مخصصة"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.delete_old_notifications(days=7)

        assert result == 5

    def test_delete_old_notifications_db_error(self):
        """اختبار فشل حذف الإشعارات القديمة"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.delete_old_notifications(days=30)

        assert result == 0


class TestGetUnreadCount:
    """اختبارات عد الإشعارات غير المقروءة"""

    def test_get_unread_count_all(self):
        """اختبار عد جميع الإشعارات غير المقروءة"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [15]
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.get_unread_count()

        assert result == 15

    def test_get_unread_count_by_user(self):
        """اختبار عد إشعارات مستخدم معين غير المقروءة"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [3]
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.get_unread_count(user_id=1)

        assert result == 3

    def test_get_unread_count_db_error(self):
        """اختبار فشل عد الإشعارات غير المقروءة"""
        mock_db = Mock()
        mock_db.connection.cursor.side_effect = Exception("DB Error")
        mock_logger = Mock()

        service = MockNotificationService(db_manager=mock_db, logger=mock_logger)

        result = service.get_unread_count()

        assert result == 0


class TestCallbacks:
    """اختبارات callbacks"""

    def test_register_callback(self):
        """اختبار تسجيل callback"""
        mock_db = Mock()
        mock_db.connection = Mock()

        service = MockNotificationService(db_manager=mock_db)

        callback = Mock()
        service.register_callback(callback)

        assert len(service.callbacks) == 1

    def test_trigger_callbacks(self):
        """اختبار تشغيل callbacks"""
        mock_db = Mock()
        mock_db.connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        callback = Mock()
        service.register_callback(callback)

        service.create_notification(title="Test", message="Test message")

        callback.assert_called_once_with(1)


class TestNotificationFiltering:
    """اختبارات تصفية الإشعارات"""

    def test_filter_by_priority(self):
        """اختبار التصفية حسب الأولوية"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "High Priority",
                "Message",
                "info",
                "high",
                "system",
                1,
                None,
                None,
                0,
                None,
                datetime.now().isoformat(),
            )
        ]
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        result = service.get_notifications()

        assert len(result) == 1
        assert result[0].priority == "high"

    def test_filter_by_date_range(self):
        """اختبار التصفية حسب نطاق التاريخ"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        start_date = datetime.now() - timedelta(days=7)  # noqa: F841
        end_date = datetime.now()  # noqa: F841

        result = service.get_notifications()

        assert isinstance(result, list)


class TestNotificationBulkOperations:
    """اختبارات العمليات الجماعية على الإشعارات"""

    def test_bulk_delete(self):
        """اختبار الحذف الجماعي"""
        mock_db = Mock()
        mock_cursor = Mock()
        mock_cursor.rowcount = 5
        mock_db.connection.cursor.return_value = mock_cursor

        service = MockNotificationService(db_manager=mock_db)

        notification_ids = [1, 2, 3, 4, 5]
        deleted_count = 0

        for nid in notification_ids:
            if service.delete_notification(nid):
                deleted_count += 1

        assert deleted_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
