#!/usr/bin/env python3
"""
اختبارات Notifications Manager
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from src.ui.notifications_manager import (
    NotificationsManager, Notification, NotificationType, NotificationPriority
)

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestNotificationsManager:
    """اختبارات مدير الإشعارات"""
    
    @pytest.fixture
    def manager(self):
        """إنشاء مدير للاختبارات"""
        parent = QWidget()
        return NotificationsManager(parent)
    
    def test_initialization(self, manager):
        """اختبار تهيئة المدير"""
        assert manager is not None
        assert hasattr(manager, 'notifications')
        assert hasattr(manager, 'max_notifications')
    
    def test_show_notification(self, manager):
        """اختبار عرض إشعار"""
        result = manager.show_notification(
            title="Test",
            message="This is a test notification",
            notification_type=NotificationType.INFO,
            duration=3000
        )
        
        assert result is not None
        assert isinstance(result, Notification) or isinstance(result, str)
    
    def test_show_info_notification(self, manager):
        """اختبار عرض إشعار معلومات"""
        result = manager.show_info("Info Title", "Info message")
        
        assert result is not None
    
    def test_show_warning_notification(self, manager):
        """اختبار عرض إشعار تحذير"""
        result = manager.show_warning("Warning Title", "Warning message")
        
        assert result is not None
    
    def test_show_error_notification(self, manager):
        """اختبار عرض إشعار خطأ"""
        result = manager.show_error("Error Title", "Error message")
        
        assert result is not None
    
    def test_show_success_notification(self, manager):
        """اختبار عرض إشعار نجاح"""
        result = manager.show_success("Success Title", "Success message")
        
        assert result is not None
    
    def test_dismiss_notification(self, manager):
        """اختبار إغلاق إشعار"""
        notification = manager.show_info("Test", "Test message")
        
        if isinstance(notification, Notification):
            result = manager.dismiss_notification(notification.id)
        else:
            result = manager.dismiss_notification(notification)
        
        assert result is True
    
    def test_dismiss_all_notifications(self, manager):
        """اختبار إغلاق جميع الإشعارات"""
        manager.show_info("Test 1", "Message 1")
        manager.show_info("Test 2", "Message 2")
        manager.show_info("Test 3", "Message 3")
        
        result = manager.dismiss_all()
        
        assert result is True
        assert len(manager.notifications) == 0
    
    def test_get_active_notifications(self, manager):
        """اختبار الحصول على الإشعارات النشطة"""
        manager.show_info("Test", "Message")
        
        notifications = manager.get_active_notifications()
        
        assert isinstance(notifications, list)
        assert len(notifications) > 0
    
    def test_set_max_notifications(self, manager):
        """اختبار تعيين الحد الأقصى للإشعارات"""
        result = manager.set_max_notifications(5)
        
        assert result is True
        assert manager.max_notifications == 5
    
    def test_notification_priority(self, manager):
        """اختبار أولوية الإشعارات"""
        result = manager.show_notification(
            title="Urgent",
            message="Urgent message",
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH
        )
        
        assert result is not None
    
    def test_notification_position(self, manager):
        """اختبار موضع الإشعارات"""
        manager.set_position("top-right")
        
        assert manager.position == "top-right"
    
    def test_pause_notifications(self, manager):
        """اختبار إيقاف الإشعارات مؤقتاً"""
        result = manager.pause()
        
        assert result is True
        assert manager.is_paused() is True
    
    def test_resume_notifications(self, manager):
        """اختبار استئناف الإشعارات"""
        manager.pause()
        
        result = manager.resume()
        
        assert result is True
        assert manager.is_paused() is False


class TestNotification:
    """اختبارات الإشعار"""
    
    def test_notification_creation(self):
        """اختبار إنشاء إشعار"""
        notification = Notification(
            id="notif_001",
            title="Test Title",
            message="Test message",
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            created_at=datetime.now(),
            duration=5000
        )
        
        assert notification.id == "notif_001"
        assert notification.title == "Test Title"
        assert notification.message == "Test message"
        assert notification.notification_type == NotificationType.INFO
        assert notification.priority == NotificationPriority.NORMAL
    
    def test_notification_is_expired(self):
        """اختبار انتهاء صلاحية الإشعار"""
        # إشعار انتهت صلاحيته
        expired_notification = Notification(
            id="notif_001",
            title="Expired",
            message="Expired message",
            notification_type=NotificationType.INFO,
            created_at=datetime.now() - timedelta(seconds=10),
            duration=5000  # 5 ثوانٍ
        )
        
        assert expired_notification.is_expired() is True
    
    def test_notification_is_not_expired(self):
        """اختبار عدم انتهاء صلاحية الإشعار"""
        # إشعار لم تنتهِ صلاحيته
        active_notification = Notification(
            id="notif_002",
            title="Active",
            message="Active message",
            notification_type=NotificationType.INFO,
            created_at=datetime.now(),
            duration=5000
        )
        
        assert active_notification.is_expired() is False


class TestNotificationType:
    """اختبارات أنواع الإشعارات"""
    
    def test_notification_types(self):
        """اختبار أنواع الإشعارات المتاحة"""
        assert NotificationType.INFO is not None
        assert NotificationType.WARNING is not None
        assert NotificationType.ERROR is not None
        assert NotificationType.SUCCESS is not None


class TestNotificationPriority:
    """اختبارات أولويات الإشعارات"""
    
    def test_notification_priorities(self):
        """اختبار مستويات الأولوية المتاحة"""
        assert NotificationPriority.LOW is not None
        assert NotificationPriority.NORMAL is not None
        assert NotificationPriority.HIGH is not None
        assert NotificationPriority.URGENT is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



