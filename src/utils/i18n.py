"""
نظام اللغات المتعددة
Internationalization (i18n) System
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from enum import Enum


class Language(Enum):
    """اللغات المدعومة"""
    ARABIC = "ar"
    ENGLISH = "en"


class TranslationManager:
    """
    مدير الترجمة للتطبيق
    يدعم اللغة العربية والإنجليزية مع تبديل فوري
    """
    
    def __init__(self, default_language: Language = Language.ARABIC):
        """
        تهيئة مدير الترجمة
        
        Args:
            default_language: اللغة الافتراضية
        """
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.translations_dir = Path("data/translations")
        self.translations_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_translations()
    
    def _load_translations(self):
        """تحميل ملفات الترجمة"""
        for lang in Language:
            translation_file = self.translations_dir / f"{lang.value}.json"
            
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[lang.value] = json.load(f)
            else:
                # إنشاء ملف الترجمة الافتراضي
                self.translations[lang.value] = self._get_default_translations(lang)
                self._save_translation_file(lang)
    
    def _save_translation_file(self, language: Language):
        """حفظ ملف الترجمة"""
        translation_file = self.translations_dir / f"{language.value}.json"
        with open(translation_file, 'w', encoding='utf-8') as f:
            json.dump(
                self.translations[language.value],
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def _get_default_translations(self, language: Language) -> Dict[str, str]:
        """الحصول على الترجمات الافتراضية"""
        if language == Language.ARABIC:
            return self._get_arabic_translations()
        else:
            return self._get_english_translations()
    
    def _get_arabic_translations(self) -> Dict[str, str]:
        """الترجمات العربية"""
        return {
            # General
            "app_name": "نظام إدارة المخزون والمبيعات",
            "app_description": "نظام شامل لإدارة المخزون والمبيعات والمحاسبة",
            "version": "الإصدار",
            "welcome": "مرحباً",
            "loading": "جاري التحميل...",
            "saving": "جاري الحفظ...",
            "success": "نجح",
            "error": "خطأ",
            "warning": "تحذير",
            "info": "معلومات",
            "confirm": "تأكيد",
            "cancel": "إلغاء",
            "close": "إغلاق",
            "save": "حفظ",
            "delete": "حذف",
            "edit": "تعديل",
            "add": "إضافة",
            "search": "بحث",
            "filter": "تصفية",
            "refresh": "تحديث",
            "export": "تصدير",
            "import": "استيراد",
            "print": "طباعة",
            "yes": "نعم",
            "no": "لا",
            "ok": "موافق",
            "apply": "تطبيق",
            "reset": "إعادة تعيين",
            "clear": "مسح",
            
            # Menu Items
            "menu_file": "ملف",
            "menu_edit": "تحرير",
            "menu_view": "عرض",
            "menu_tools": "أدوات",
            "menu_help": "مساعدة",
            "menu_settings": "إعدادات",
            "menu_logout": "تسجيل خروج",
            "menu_exit": "خروج",
            
            # Main Modules
            "dashboard": "لوحة المعلومات",
            "sales": "المبيعات",
            "purchases": "المشتريات",
            "inventory": "المخزون",
            "accounting": "المحاسبة",
            "customers": "العملاء",
            "suppliers": "الموردون",
            "products": "المنتجات",
            "reports": "التقارير",
            "settings": "الإعدادات",
            "users": "المستخدمون",
            "permissions": "الصلاحيات",
            
            # Sales
            "invoice": "فاتورة",
            "invoices": "الفواتير",
            "quote": "عرض سعر",
            "quotes": "عروض الأسعار",
            "sales_return": "مرتجع مبيعات",
            "sales_returns": "مرتجعات المبيعات",
            "customer": "عميل",
            "payment": "دفعة",
            "payments": "المدفوعات",
            "payment_plan": "خطة تقسيط",
            "payment_plans": "خطط التقسيط",
            
            # Purchases
            "purchase_invoice": "فاتورة شراء",
            "purchase_invoices": "فواتير الشراء",
            "purchase_order": "أمر شراء",
            "purchase_orders": "أوامر الشراء",
            "purchase_return": "مرتجع مشتريات",
            "purchase_returns": "مرتجعات المشتريات",
            "supplier": "مورد",
            "receive": "استلام",
            
            # Inventory
            "product": "منتج",
            "category": "فئة",
            "categories": "الفئات",
            "stock": "مخزون",
            "warehouse": "مستودع",
            "warehouses": "المستودعات",
            "movement": "حركة",
            "movements": "الحركات",
            "count": "جرد",
            "counts": "الجرد",
            "adjustment": "تعديل",
            "adjustments": "التعديلات",
            
            # Accounting
            "account": "حساب",
            "accounts": "الحسابات",
            "journal_entry": "قيد يومية",
            "journal_entries": "قيود اليومية",
            "trial_balance": "ميزان المراجعة",
            "income_statement": "قائمة الدخل",
            "balance_sheet": "الميزانية العمومية",
            "credit": "دائن",
            "debit": "مدين",
            
            # Reports
            "report": "تقرير",
            "daily_report": "تقرير يومي",
            "monthly_report": "تقرير شهري",
            "annual_report": "تقرير سنوي",
            "sales_report": "تقرير المبيعات",
            "purchase_report": "تقرير المشتريات",
            "inventory_report": "تقرير المخزون",
            "financial_report": "تقرير مالي",
            "profit_loss": "الأرباح والخسائر",
            
            # Common Fields
            "date": "التاريخ",
            "from_date": "من تاريخ",
            "to_date": "إلى تاريخ",
            "code": "الرمز",
            "name": "الاسم",
            "description": "الوصف",
            "notes": "ملاحظات",
            "amount": "المبلغ",
            "quantity": "الكمية",
            "price": "السعر",
            "total": "الإجمالي",
            "subtotal": "المجموع الفرعي",
            "tax": "الضريبة",
            "discount": "الخصم",
            "status": "الحالة",
            "type": "النوع",
            "created_at": "تاريخ الإنشاء",
            "updated_at": "تاريخ التحديث",
            "created_by": "أنشئ بواسطة",
            "phone": "الهاتف",
            "email": "البريد الإلكتروني",
            "address": "العنوان",
            "city": "المدينة",
            "country": "الدولة",
            
            # Status Values
            "active": "نشط",
            "inactive": "غير نشط",
            "pending": "معلق",
            "approved": "معتمد",
            "rejected": "مرفوض",
            "completed": "مكتمل",
            "cancelled": "ملغي",
            "draft": "مسودة",
            
            # Messages
            "msg_save_success": "تم الحفظ بنجاح",
            "msg_delete_success": "تم الحذف بنجاح",
            "msg_update_success": "تم التحديث بنجاح",
            "msg_confirm_delete": "هل أنت متأكد من الحذف؟",
            "msg_no_data": "لا توجد بيانات",
            "msg_loading_data": "جاري تحميل البيانات...",
            "msg_operation_failed": "فشلت العملية",
            "msg_invalid_input": "بيانات غير صحيحة",
            "msg_required_field": "هذا الحقل مطلوب",
            
            # Login
            "login": "تسجيل دخول",
            "logout": "تسجيل خروج",
            "username": "اسم المستخدم",
            "password": "كلمة المرور",
            "remember_me": "تذكرني",
            "forgot_password": "نسيت كلمة المرور؟",
            
            # System Management
            "backup": "نسخة احتياطية",
            "backups": "النسخ الاحتياطية",
            "restore": "استعادة",
            "performance": "الأداء",
            "maintenance": "الصيانة",
            "optimize": "تحسين",
            "system_settings": "إعدادات النظام",
            
            # Notifications
            "notification": "إشعار",
            "notifications": "الإشعارات",
            "alert": "تنبيه",
            "alerts": "التنبيهات",
            "reminder": "تذكير",
            "reminders": "التذكيرات",
            
            # Language
            "language": "اللغة",
            "arabic": "العربية",
            "english": "الإنجليزية",
            "change_language": "تغيير اللغة",
        }
    
    def _get_english_translations(self) -> Dict[str, str]:
        """الترجمات الإنجليزية"""
        return {
            # General
            "app_name": "Inventory & Sales Management System",
            "app_description": "Comprehensive system for inventory, sales, and accounting management",
            "version": "Version",
            "welcome": "Welcome",
            "loading": "Loading...",
            "saving": "Saving...",
            "success": "Success",
            "error": "Error",
            "warning": "Warning",
            "info": "Information",
            "confirm": "Confirm",
            "cancel": "Cancel",
            "close": "Close",
            "save": "Save",
            "delete": "Delete",
            "edit": "Edit",
            "add": "Add",
            "search": "Search",
            "filter": "Filter",
            "refresh": "Refresh",
            "export": "Export",
            "import": "Import",
            "print": "Print",
            "yes": "Yes",
            "no": "No",
            "ok": "OK",
            "apply": "Apply",
            "reset": "Reset",
            "clear": "Clear",
            
            # Menu Items
            "menu_file": "File",
            "menu_edit": "Edit",
            "menu_view": "View",
            "menu_tools": "Tools",
            "menu_help": "Help",
            "menu_settings": "Settings",
            "menu_logout": "Logout",
            "menu_exit": "Exit",
            
            # Main Modules
            "dashboard": "Dashboard",
            "sales": "Sales",
            "purchases": "Purchases",
            "inventory": "Inventory",
            "accounting": "Accounting",
            "customers": "Customers",
            "suppliers": "Suppliers",
            "products": "Products",
            "reports": "Reports",
            "settings": "Settings",
            "users": "Users",
            "permissions": "Permissions",
            
            # Sales
            "invoice": "Invoice",
            "invoices": "Invoices",
            "quote": "Quote",
            "quotes": "Quotes",
            "sales_return": "Sales Return",
            "sales_returns": "Sales Returns",
            "customer": "Customer",
            "payment": "Payment",
            "payments": "Payments",
            "payment_plan": "Payment Plan",
            "payment_plans": "Payment Plans",
            
            # Purchases
            "purchase_invoice": "Purchase Invoice",
            "purchase_invoices": "Purchase Invoices",
            "purchase_order": "Purchase Order",
            "purchase_orders": "Purchase Orders",
            "purchase_return": "Purchase Return",
            "purchase_returns": "Purchase Returns",
            "supplier": "Supplier",
            "receive": "Receive",
            
            # Inventory
            "product": "Product",
            "category": "Category",
            "categories": "Categories",
            "stock": "Stock",
            "warehouse": "Warehouse",
            "warehouses": "Warehouses",
            "movement": "Movement",
            "movements": "Movements",
            "count": "Count",
            "counts": "Counts",
            "adjustment": "Adjustment",
            "adjustments": "Adjustments",
            
            # Accounting
            "account": "Account",
            "accounts": "Accounts",
            "journal_entry": "Journal Entry",
            "journal_entries": "Journal Entries",
            "trial_balance": "Trial Balance",
            "income_statement": "Income Statement",
            "balance_sheet": "Balance Sheet",
            "credit": "Credit",
            "debit": "Debit",
            
            # Reports
            "report": "Report",
            "daily_report": "Daily Report",
            "monthly_report": "Monthly Report",
            "annual_report": "Annual Report",
            "sales_report": "Sales Report",
            "purchase_report": "Purchase Report",
            "inventory_report": "Inventory Report",
            "financial_report": "Financial Report",
            "profit_loss": "Profit & Loss",
            
            # Common Fields
            "date": "Date",
            "from_date": "From Date",
            "to_date": "To Date",
            "code": "Code",
            "name": "Name",
            "description": "Description",
            "notes": "Notes",
            "amount": "Amount",
            "quantity": "Quantity",
            "price": "Price",
            "total": "Total",
            "subtotal": "Subtotal",
            "tax": "Tax",
            "discount": "Discount",
            "status": "Status",
            "type": "Type",
            "created_at": "Created At",
            "updated_at": "Updated At",
            "created_by": "Created By",
            "phone": "Phone",
            "email": "Email",
            "address": "Address",
            "city": "City",
            "country": "Country",
            
            # Status Values
            "active": "Active",
            "inactive": "Inactive",
            "pending": "Pending",
            "approved": "Approved",
            "rejected": "Rejected",
            "completed": "Completed",
            "cancelled": "Cancelled",
            "draft": "Draft",
            
            # Messages
            "msg_save_success": "Saved successfully",
            "msg_delete_success": "Deleted successfully",
            "msg_update_success": "Updated successfully",
            "msg_confirm_delete": "Are you sure you want to delete?",
            "msg_no_data": "No data available",
            "msg_loading_data": "Loading data...",
            "msg_operation_failed": "Operation failed",
            "msg_invalid_input": "Invalid input",
            "msg_required_field": "This field is required",
            
            # Login
            "login": "Login",
            "logout": "Logout",
            "username": "Username",
            "password": "Password",
            "remember_me": "Remember me",
            "forgot_password": "Forgot password?",
            
            # System Management
            "backup": "Backup",
            "backups": "Backups",
            "restore": "Restore",
            "performance": "Performance",
            "maintenance": "Maintenance",
            "optimize": "Optimize",
            "system_settings": "System Settings",
            
            # Notifications
            "notification": "Notification",
            "notifications": "Notifications",
            "alert": "Alert",
            "alerts": "Alerts",
            "reminder": "Reminder",
            "reminders": "Reminders",
            
            # Language
            "language": "Language",
            "arabic": "Arabic",
            "english": "English",
            "change_language": "Change Language",
        }
    
    def t(self, key: str, **kwargs) -> str:
        """
        ترجمة نص
        
        Args:
            key: مفتاح الترجمة
            **kwargs: متغيرات للاستبدال في النص
            
        Returns:
            النص المترجم
        """
        translation = self.translations.get(
            self.current_language.value, {}
        ).get(key, key)
        
        # استبدال المتغيرات
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError:
                pass
        
        return translation
    
    def set_language(self, language: Language):
        """
        تغيير اللغة الحالية
        
        Args:
            language: اللغة الجديدة
        """
        self.current_language = language
    
    def get_language(self) -> Language:
        """الحصول على اللغة الحالية"""
        return self.current_language
    
    def is_rtl(self) -> bool:
        """
        هل اللغة الحالية من اليمين إلى اليسار؟
        
        Returns:
            True إذا كانت RTL
        """
        return self.current_language == Language.ARABIC
    
    def add_translation(self, key: str, ar_value: str, en_value: str):
        """
        إضافة ترجمة جديدة
        
        Args:
            key: المفتاح
            ar_value: القيمة بالعربية
            en_value: القيمة بالإنجليزية
        """
        self.translations[Language.ARABIC.value][key] = ar_value
        self.translations[Language.ENGLISH.value][key] = en_value
        
        # حفظ الملفات
        self._save_translation_file(Language.ARABIC)
        self._save_translation_file(Language.ENGLISH)


# Instance واحدة للتطبيق بأكمله
_translation_manager = None


def get_translation_manager() -> TranslationManager:
    """الحصول على instance مدير الترجمة"""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def t(key: str, **kwargs) -> str:
    """
    دالة مختصرة للترجمة
    
    Args:
        key: مفتاح الترجمة
        **kwargs: متغيرات للاستبدال
        
    Returns:
        النص المترجم
    """
    return get_translation_manager().t(key, **kwargs)
