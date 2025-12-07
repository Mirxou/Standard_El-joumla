#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الجهاز العصبي المركزي للتطبيق - Global Signals System
Central Nervous System for Application-wide Communication

هذا الملف يحتوي على جميع الإشارات (Signals) التي تربط الوحدات المختلفة ببعضها.
عندما يحدث تغيير في جزء من النظام، يتم إطلاق إشارة تلقائياً لتحديث الأجزاء الأخرى.

مثال:
- عند حفظ فاتورة مبيعات → يطلق sales_updated و inventory_updated
- صفحة المخزون تستمع لـ inventory_updated → تحديث تلقائي
- صفحة الداشبورد تستمع لـ sales_updated → تحديث الإحصائيات تلقائياً
"""

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    """
    الجهاز العصبي المركزي للتطبيق.
    
    يحتوي على جميع الإشارات التي تربط الوحدات المختلفة ببعضها.
    يستخدم Singleton Pattern لضمان وجود نسخة واحدة فقط في التطبيق.
    
    الاستخدام:
        from src.core.signals import signals
        
        # إطلاق إشارة
        signals.sales_updated.emit()
        
        # الاستماع لإشارة
        signals.sales_updated.connect(self.refresh_sales_data)
    """
    
    # ==================== إشارات البيانات (Data Signals) ====================
    
    # إشارات المخزون
    inventory_updated = Signal()          # تطلق عند أي تغيير في الكميات (بيع/شراء/تعديل/تسوية)
    inventory_item_added = Signal(int)    # تطلق عند إضافة منتج جديد (product_id)
    inventory_item_updated = Signal(int)  # تطلق عند تعديل منتج (product_id)
    inventory_item_deleted = Signal(int)  # تطلق عند حذف منتج (product_id)
    stock_adjusted = Signal(int)          # تطلق عند تسوية المخزون (product_id)
    stock_transferred = Signal()          # تطلق عند نقل المخزون بين المواقع
    
    # إشارات المبيعات
    sales_updated = Signal()              # تطلق عند إنشاء/تعديل/حذف فاتورة مبيعات
    sale_created = Signal(int)             # تطلق عند إنشاء فاتورة جديدة (sale_id)
    sale_updated = Signal(int)            # تطلق عند تعديل فاتورة (sale_id)
    sale_deleted = Signal(int)            # تطلق عند حذف فاتورة (sale_id)
    sale_paid = Signal(int)               # تطلق عند تسجيل دفعة لفاتورة (sale_id)
    
    # إشارات المشتريات
    purchases_updated = Signal()           # تطلق عند إنشاء/تعديل/حذف أمر شراء
    purchase_created = Signal(int)        # تطلق عند إنشاء أمر شراء جديد (purchase_id)
    purchase_received = Signal(int)        # تطلق عند استلام شحنة (purchase_id)
    purchase_paid = Signal(int)           # تطلق عند تسجيل دفعة لأمر شراء (purchase_id)
    
    # إشارات المدفوعات
    payments_updated = Signal()           # تطلق عند تسجيل/تعديل/حذف دفعة
    payment_recorded = Signal(int)        # تطلق عند تسجيل دفعة جديدة (payment_id)
    
    # إشارات العملاء والموردين
    customer_updated = Signal(int)        # تطلق عند إضافة/تعديل/حذف عميل (customer_id)
    supplier_updated = Signal(int)        # تطلق عند إضافة/تعديل/حذف مورد (supplier_id)
    
    # إشارات الفئات
    category_updated = Signal()           # تطلق عند إضافة/تعديل/حذف فئة
    
    # ==================== إشارات الإعدادات (Settings Signals) ====================
    
    settings_changed = Signal()           # تطلق عند تغيير أي إعداد (العملة، الثيم، اللغة، إلخ)
    theme_changed = Signal(str)           # تطلق عند تغيير الثيم (theme_name)
    currency_changed = Signal(str)         # تطلق عند تغيير العملة (currency_code)
    language_changed = Signal(str)         # تطلق عند تغيير اللغة (language_code)
    
    # ==================== إشارات المستخدم (User Signals) ====================
    
    user_logged_in = Signal(int)          # تطلق عند تسجيل دخول مستخدم (user_id)
    user_logged_out = Signal(int)         # تطلق عند تسجيل خروج مستخدم (user_id)
    user_permissions_changed = Signal(int) # تطلق عند تغيير صلاحيات مستخدم (user_id)
    
    # ==================== إشارات النظام (System Signals) ====================
    
    database_updated = Signal()           # تطلق عند تحديث قاعدة البيانات (نسخ احتياطي/استعادة)
    backup_created = Signal(str)          # تطلق عند إنشاء نسخة احتياطية (backup_path)
    backup_restored = Signal(str)          # تطلق عند استعادة نسخة احتياطية (backup_path)
    
    # ==================== إشارات التقارير (Reports Signals) ====================
    
    report_generated = Signal(str)        # تطلق عند توليد تقرير (report_type)
    
    # ==================== إشارات الإشعارات (Notifications Signals) ====================
    
    notification_created = Signal(str)     # تطلق عند إنشاء إشعار جديد (notification_type)
    low_stock_alert = Signal(int)          # تطلق عند انخفاض المخزون (product_id)
    payment_due_alert = Signal(int)       # تطلق عند استحقاق دفعة (payment_id)


# إنشاء نسخة وحيدة (Singleton) يتم استدعاؤها في كل مكان
# هذا يضمن أن جميع الأجزاء تستخدم نفس الإشارات
signals = AppSignals()

