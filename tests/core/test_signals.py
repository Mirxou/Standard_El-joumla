"""
اختبارات نظام Signals
Tests for Signals system
"""

import unittest
from PySide6.QtCore import QObject, Signal
from src.core.signals import AppSignals, signals


class TestAppSignalsClass(unittest.TestCase):
    """اختبارات كلاس AppSignals"""

    def test_app_signals_is_qobject(self):
        """AppSignals يرث من QObject"""
        app_signals = AppSignals()
        self.assertIsInstance(app_signals, QObject)

    def test_has_inventory_signals(self):
        """فحص وجود إشارات المخزون"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'inventory_updated'))
        self.assertTrue(hasattr(app_signals, 'inventory_item_added'))
        self.assertTrue(hasattr(app_signals, 'inventory_item_updated'))
        self.assertTrue(hasattr(app_signals, 'inventory_item_deleted'))
        self.assertTrue(hasattr(app_signals, 'stock_adjusted'))
        self.assertTrue(hasattr(app_signals, 'stock_transferred'))

    def test_has_sales_signals(self):
        """فحص وجود إشارات المبيعات"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'sales_updated'))
        self.assertTrue(hasattr(app_signals, 'sale_created'))
        self.assertTrue(hasattr(app_signals, 'sale_updated'))
        self.assertTrue(hasattr(app_signals, 'sale_deleted'))
        self.assertTrue(hasattr(app_signals, 'sale_paid'))

    def test_has_purchases_signals(self):
        """فحص وجود إشارات المشتريات"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'purchases_updated'))
        self.assertTrue(hasattr(app_signals, 'purchase_created'))
        self.assertTrue(hasattr(app_signals, 'purchase_received'))
        self.assertTrue(hasattr(app_signals, 'purchase_paid'))

    def test_has_payment_signals(self):
        """فحص وجود إشارات المدفوعات"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'payments_updated'))
        self.assertTrue(hasattr(app_signals, 'payment_recorded'))

    def test_has_customer_supplier_signals(self):
        """فحص وجود إشارات العملاء والموردين"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'customer_updated'))
        self.assertTrue(hasattr(app_signals, 'supplier_updated'))
        self.assertTrue(hasattr(app_signals, 'category_updated'))

    def test_has_settings_signals(self):
        """فحص وجود إشارات الإعدادات"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'settings_changed'))
        self.assertTrue(hasattr(app_signals, 'theme_changed'))
        self.assertTrue(hasattr(app_signals, 'currency_changed'))
        self.assertTrue(hasattr(app_signals, 'language_changed'))

    def test_has_user_signals(self):
        """فحص وجود إشارات المستخدم"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'user_logged_in'))
        self.assertTrue(hasattr(app_signals, 'user_logged_out'))
        self.assertTrue(hasattr(app_signals, 'user_permissions_changed'))

    def test_has_system_signals(self):
        """فحص وجود إشارات النظام"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'database_updated'))
        self.assertTrue(hasattr(app_signals, 'backup_created'))
        self.assertTrue(hasattr(app_signals, 'backup_restored'))

    def test_has_report_signals(self):
        """فحص وجود إشارات التقارير"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'report_generated'))

    def test_has_notification_signals(self):
        """فحص وجود إشارات الإشعارات"""
        app_signals = AppSignals()
        self.assertTrue(hasattr(app_signals, 'notification_created'))
        self.assertTrue(hasattr(app_signals, 'low_stock_alert'))
        self.assertTrue(hasattr(app_signals, 'payment_due_alert'))


class TestSingletonInstance(unittest.TestCase):
    """اختبارات Singleton instance"""

    def test_signals_singleton_exists(self):
        """فحص وجود singleton instance"""
        self.assertIsNotNone(signals)
        self.assertIsInstance(signals, AppSignals)

    def test_signals_is_qobject(self):
        """singleton instance هو QObject"""
        self.assertIsInstance(signals, QObject)


class TestSignalsEmission(unittest.TestCase):
    """اختبارات إطلاق الإشارات"""

    def setUp(self):
        """إعداد قبل كل اختبار"""
        self.app_signals = AppSignals()
        self.signal_received = False
        self.received_value = None

    def test_emit_inventory_updated(self):
        """إطلاق إشارة inventory_updated"""
        def handler():
            self.signal_received = True
        
        self.app_signals.inventory_updated.connect(handler)
        self.app_signals.inventory_updated.emit()
        self.assertTrue(self.signal_received)

    def test_emit_with_int_parameter(self):
        """إطلاق إشارة مع معامل int"""
        def handler(value):
            self.signal_received = True
            self.received_value = value
        
        self.app_signals.inventory_item_added.connect(handler)
        self.app_signals.inventory_item_added.emit(123)
        
        self.assertTrue(self.signal_received)
        self.assertEqual(self.received_value, 123)

    def test_emit_with_string_parameter(self):
        """إطلاق إشارة مع معامل string"""
        def handler(value):
            self.signal_received = True
            self.received_value = value
        
        self.app_signals.theme_changed.connect(handler)
        self.app_signals.theme_changed.emit("dark")
        
        self.assertTrue(self.signal_received)
        self.assertEqual(self.received_value, "dark")

    def test_multiple_handlers(self):
        """عدة handlers لنفس الإشارة"""
        counter = {'count': 0}
        
        def handler1():
            counter['count'] += 1
        
        def handler2():
            counter['count'] += 10
        
        self.app_signals.sales_updated.connect(handler1)
        self.app_signals.sales_updated.connect(handler2)
        self.app_signals.sales_updated.emit()
        
        self.assertEqual(counter['count'], 11)

    def test_disconnect_handler(self):
        """فصل handler من الإشارة"""
        def handler():
            self.signal_received = True
        
        self.app_signals.category_updated.connect(handler)
        self.app_signals.category_updated.disconnect(handler)
        self.app_signals.category_updated.emit()
        
        self.assertFalse(self.signal_received)


class TestSignalTypes(unittest.TestCase):
    """اختبارات أنواع الإشارات"""

    def test_no_param_signals(self):
        """إشارات بدون معاملات"""
        app_signals = AppSignals()
        
        # Test that these are Signal instances
        self.assertIsInstance(app_signals.inventory_updated, Signal)
        self.assertIsInstance(app_signals.sales_updated, Signal)
        self.assertIsInstance(app_signals.database_updated, Signal)

    def test_int_param_signals(self):
        """إشارات مع معامل int"""
        app_signals = AppSignals()
        
        self.assertIsInstance(app_signals.sale_created, Signal)
        self.assertIsInstance(app_signals.customer_updated, Signal)
        self.assertIsInstance(app_signals.user_logged_in, Signal)

    def test_string_param_signals(self):
        """إشارات مع معامل string"""
        app_signals = AppSignals()
        
        self.assertIsInstance(app_signals.theme_changed, Signal)
        self.assertIsInstance(app_signals.currency_changed, Signal)
        self.assertIsInstance(app_signals.backup_created, Signal)


class TestRealWorldScenarios(unittest.TestCase):
    """اختبارات سيناريوهات واقعية"""

    def setUp(self):
        """إعداد قبل كل اختبار"""
        self.app_signals = AppSignals()
        self.events = []

    def test_sale_creation_workflow(self):
        """سيناريو: إنشاء فاتورة مبيعات"""
        def on_sale_created(sale_id):
            self.events.append(('sale_created', sale_id))
        
        def on_inventory_updated():
            self.events.append(('inventory_updated', None))
        
        def on_sales_updated():
            self.events.append(('sales_updated', None))
        
        self.app_signals.sale_created.connect(on_sale_created)
        self.app_signals.inventory_updated.connect(on_inventory_updated)
        self.app_signals.sales_updated.connect(on_sales_updated)
        
        # محاكاة إنشاء فاتورة
        self.app_signals.sale_created.emit(1001)
        self.app_signals.inventory_updated.emit()
        self.app_signals.sales_updated.emit()
        
        self.assertEqual(len(self.events), 3)
        self.assertEqual(self.events[0], ('sale_created', 1001))
        self.assertEqual(self.events[1], ('inventory_updated', None))

    def test_theme_change_workflow(self):
        """سيناريو: تغيير الثيم"""
        themes_applied = []
        
        def on_theme_changed(theme):
            themes_applied.append(theme)
        
        self.app_signals.theme_changed.connect(on_theme_changed)
        
        self.app_signals.theme_changed.emit("light")
        self.app_signals.theme_changed.emit("dark")
        
        self.assertEqual(themes_applied, ["light", "dark"])


if __name__ == '__main__':
    unittest.main()



