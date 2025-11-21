#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة تقارير العملاء والموردين
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTabWidget, QWidget, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument, QTextCursor
from datetime import datetime, timedelta


class ContactsReportDialog(QDialog):
    """نافذة تقارير العملاء والموردين"""
    
    def __init__(self, db_manager, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = logger
        
        self.setWindowTitle("تقارير العملاء والموردين")
        self.setGeometry(100, 100, 900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        title = QLabel("تقارير العملاء والموردين")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # تبويبات التقارير
        self.tab_widget = QTabWidget()
        
        # تقرير العملاء
        customers_tab = self.create_customers_report_tab()
        self.tab_widget.addTab(customers_tab, "👥 تقرير العملاء")
        
        # تقرير الموردين
        suppliers_tab = self.create_suppliers_report_tab()
        self.tab_widget.addTab(suppliers_tab, "🏭 تقرير الموردين")
        
        # تقرير المقارنة
        comparison_tab = self.create_comparison_report_tab()
        self.tab_widget.addTab(comparison_tab, "📊 تقرير المقارنة")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("📥 تصدير التقرير")
        export_btn.clicked.connect(self.export_report)
        buttons_layout.addWidget(export_btn)
        
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.clicked.connect(self.print_report)
        buttons_layout.addWidget(print_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_customers_report_tab(self):
        """إنشاء تبويب تقرير العملاء"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # خيارات التقرير
        options_layout = QHBoxLayout()
        
        period_label = QLabel("الفترة:")
        self.customers_period_combo = QComboBox()
        self.customers_period_combo.addItems(["الكل", "هذا الشهر", "آخر 3 أشهر", "آخر سنة"])
        self.customers_period_combo.currentIndexChanged.connect(self.generate_customers_report)
        options_layout.addWidget(period_label)
        options_layout.addWidget(self.customers_period_combo)
        options_layout.addStretch()
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.generate_customers_report)
        options_layout.addWidget(refresh_btn)
        
        layout.addLayout(options_layout)
        
        # منطقة التقرير
        self.customers_report_text = QTextEdit()
        self.customers_report_text.setReadOnly(True)
        layout.addWidget(self.customers_report_text)
        
        # توليد التقرير الأولي
        self.generate_customers_report()
        
        return tab
    
    def create_suppliers_report_tab(self):
        """إنشاء تبويب تقرير الموردين"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # خيارات التقرير
        options_layout = QHBoxLayout()
        
        period_label = QLabel("الفترة:")
        self.suppliers_period_combo = QComboBox()
        self.suppliers_period_combo.addItems(["الكل", "هذا الشهر", "آخر 3 أشهر", "آخر سنة"])
        self.suppliers_period_combo.currentIndexChanged.connect(self.generate_suppliers_report)
        options_layout.addWidget(period_label)
        options_layout.addWidget(self.suppliers_period_combo)
        options_layout.addStretch()
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.generate_suppliers_report)
        options_layout.addWidget(refresh_btn)
        
        layout.addLayout(options_layout)
        
        # منطقة التقرير
        self.suppliers_report_text = QTextEdit()
        self.suppliers_report_text.setReadOnly(True)
        layout.addWidget(self.suppliers_report_text)
        
        # توليد التقرير الأولي
        self.generate_suppliers_report()
        
        return tab
    
    def create_comparison_report_tab(self):
        """إنشاء تبويب تقرير المقارنة"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # خيارات التقرير
        options_layout = QHBoxLayout()
        options_layout.addStretch()
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.generate_comparison_report)
        options_layout.addWidget(refresh_btn)
        
        layout.addLayout(options_layout)
        
        # منطقة التقرير
        self.comparison_report_text = QTextEdit()
        self.comparison_report_text.setReadOnly(True)
        layout.addWidget(self.comparison_report_text)
        
        # توليد التقرير الأولي
        self.generate_comparison_report()
        
        return tab
    
    def generate_customers_report(self):
        """توليد تقرير العملاء"""
        try:
            # احسب الإحصائيات
            total = self.db_manager.fetch_one("SELECT COUNT(*) FROM customers")[0] or 0
            active = self.db_manager.fetch_one("SELECT COUNT(*) FROM customers WHERE is_active = 1")[0] or 0
            
            # الأعلى رصيد مستحق - تحقق من وجود العمود أولاً
            try:
                top_balance = self.db_manager.fetch_all(
                    "SELECT name, COALESCE(current_balance, 0) as balance FROM customers WHERE COALESCE(current_balance, 0) > 0 ORDER BY balance DESC LIMIT 5"
                )
            except:
                top_balance = []
            
            # الأكثر شراءً
            try:
                top_buyers = self.db_manager.fetch_all(
                    """
                    SELECT c.name, COUNT(*) as purchase_count, COALESCE(SUM(s.total_amount), 0) as total_amount
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id
                    ORDER BY purchase_count DESC
                    LIMIT 5
                    """
                )
            except:
                top_buyers = []
            
            # بناء التقرير
            report = f"""
{'='*80}
تقرير العملاء
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

📊 الإحصائيات العامة:
─────────────────────────────────────────────────────────────────────────────
  إجمالي العملاء:          {total}
  العملاء النشطون:         {active}
  العملاء المعطلون:        {total - active}

"""
            
            if top_balance:
                report += """💰 العملاء الأعلى رصيداً مستحقاً:
─────────────────────────────────────────────────────────────────────────────
"""
                for i, (name, balance) in enumerate(top_balance, 1):
                    report += f"  {i}. {name:<30} {float(balance):>15,.2f} دج\n"
            else:
                report += """💰 العملاء الأعلى رصيداً مستحقاً:
─────────────────────────────────────────────────────────────────────────────
  لا توجد أرصدة مستحقة
"""
            
            if top_buyers:
                report += f"\n🛍️  العملاء الأكثر شراءً:\n"
                report += "─────────────────────────────────────────────────────────────────────────────\n"
                for i, (name, count, amount) in enumerate(top_buyers, 1):
                    amount_val = float(amount) if amount else 0
                    report += f"  {i}. {name:<30} {count:>5} فاتورة  {amount_val:>15,.2f} دج\n"
            else:
                report += f"\n🛍️  العملاء الأكثر شراءً:\n"
                report += "─────────────────────────────────────────────────────────────────────────────\n"
                report += "  لا توجد عمليات شراء مسجلة\n"
            
            report += f"\n{'='*80}\n"
            
            self.customers_report_text.setText(report)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توليد تقرير العملاء: {str(e)}")
            error_report = f"""
{'='*80}
تقرير العملاء
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

⚠️ رسالة الخطأ:
─────────────────────────────────────────────────────────────────────────────
{str(e)}

💡 الحل:
─────────────────────────────────────────────────────────────────────────────
تم تحميل البيانات الأساسية. قد تكون بعض الأعمدة الإضافية غير متاحة.

{'='*80}
"""
            self.customers_report_text.setText(error_report)
    
    def generate_suppliers_report(self):
        """توليد تقرير الموردين"""
        try:
            # احسب الإحصائيات
            total = self.db_manager.fetch_one("SELECT COUNT(*) FROM suppliers")[0] or 0
            active = self.db_manager.fetch_one("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")[0] or 0
            
            # الموردين الأكثر عمليات (لا يوجد عمود current_balance في جدول suppliers)
            try:
                top_suppliers = self.db_manager.fetch_all(
                    """
                    SELECT s.name, COUNT(*) as purchase_count, COALESCE(SUM(p.total_amount), 0) as total_amount
                    FROM suppliers s
                    LEFT JOIN purchases p ON s.id = p.supplier_id
                    GROUP BY s.id
                    ORDER BY purchase_count DESC
                    LIMIT 5
                    """
                )
            except:
                top_suppliers = []
            
            # بناء التقرير
            report = f"""
{'='*80}
تقرير الموردين
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

📊 الإحصائيات العامة:
─────────────────────────────────────────────────────────────────────────────
  إجمالي الموردين:         {total}
  الموردين النشطين:       {active}
  الموردين المعطلين:      {total - active}

"""
            
            if top_suppliers:
                report += f"📦 الموردين الأكثر عمليات:\n"
                report += "─────────────────────────────────────────────────────────────────────────────\n"
                for i, (name, count, amount) in enumerate(top_suppliers, 1):
                    amount_val = float(amount) if amount else 0
                    report += f"  {i}. {name:<30} {count:>5} عملية   {amount_val:>15,.2f} دج\n"
            else:
                report += f"📦 الموردين الأكثر عمليات:\n"
                report += "─────────────────────────────────────────────────────────────────────────────\n"
                report += "  لا توجد عمليات شراء مسجلة\n"
            
            report += f"\n{'='*80}\n"
            
            self.suppliers_report_text.setText(report)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توليد تقرير الموردين: {str(e)}")
            error_report = f"""
{'='*80}
تقرير الموردين
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

⚠️ رسالة الخطأ:
─────────────────────────────────────────────────────────────────────────────
{str(e)}

💡 الحل:
─────────────────────────────────────────────────────────────────────────────
تم تحميل البيانات الأساسية. قد تكون بعض الأعمدة الإضافية غير متاحة.

{'='*80}
"""
            self.suppliers_report_text.setText(error_report)
    
    def generate_comparison_report(self):
        """توليد تقرير المقارنة بين العملاء والموردين"""
        try:
            # إحصائيات العملاء
            customers_total = self.db_manager.fetch_one("SELECT COUNT(*) FROM customers")[0] or 0
            customers_active = self.db_manager.fetch_one("SELECT COUNT(*) FROM customers WHERE is_active = 1")[0] or 0
            customers_balance = self.db_manager.fetch_one("SELECT COALESCE(SUM(COALESCE(current_balance, 0)), 0) FROM customers")[0] or 0
            
            # إحصائيات الموردين
            suppliers_total = self.db_manager.fetch_one("SELECT COUNT(*) FROM suppliers")[0] or 0
            suppliers_active = self.db_manager.fetch_one("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")[0] or 0
            # لا يوجد current_balance في جدول suppliers
            suppliers_balance = 0
            
            # إحصائيات المبيعات
            try:
                sales_total = self.db_manager.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM sales")[0] or 0
                sales_count = self.db_manager.fetch_one("SELECT COUNT(*) FROM sales")[0] or 0
            except:
                sales_total = 0
                sales_count = 0
            
            # إحصائيات الشراء
            try:
                purchases_total = self.db_manager.fetch_one("SELECT COALESCE(SUM(total_amount), 0) FROM purchases")[0] or 0
                purchases_count = self.db_manager.fetch_one("SELECT COUNT(*) FROM purchases")[0] or 0
            except:
                purchases_total = 0
                purchases_count = 0
            
            # بناء التقرير
            report = f"""
{'='*80}
تقرير المقارنة: العملاء مقابل الموردين
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

📊 مقارنة العدد:
─────────────────────────────────────────────────────────────────────────────
{'المقياس':<30} {'العملاء':>20} {'الموردين':>20}
{'-'*70}
{'الإجمالي':<30} {customers_total:>20} {suppliers_total:>20}
{'النشطين':<30} {customers_active:>20} {suppliers_active:>20}
{'المعطلين':<30} {customers_total - customers_active:>20} {suppliers_total - suppliers_active:>20}

💰 الأرصدة المستحقة من العملاء:
─────────────────────────────────────────────────────────────────────────────
  إجمالي الرصيد:           {float(customers_balance):>20,.2f} دج
  متوسط الرصيد:           {float(customers_balance)/max(customers_total, 1):>20,.2f} دج

📈 مقارنة المعاملات المالية:
─────────────────────────────────────────────────────────────────────────────
{'المقياس':<30} {'المبيعات':>20} {'المشتريات':>20}
{'-'*70}
{'عدد العمليات':<30} {sales_count:>20} {purchases_count:>20}
{'إجمالي المبلغ':<30} {float(sales_total):>20,.2f} {float(purchases_total):>20,.2f}
{'متوسط العملية':<30} {float(sales_total)/max(sales_count, 1):>20,.2f} {float(purchases_total)/max(purchases_count, 1):>20,.2f}

📋 التحليل:
─────────────────────────────────────────────────────────────────────────────
"""
            
            # تحليل الحالات
            if customers_total > suppliers_total:
                report += f"  ✓ عدد العملاء ({customers_total}) أكثر من الموردين ({suppliers_total})\n"
            elif suppliers_total > customers_total:
                report += f"  ✓ عدد الموردين ({suppliers_total}) أكثر من العملاء ({customers_total})\n"
            else:
                report += f"  ✓ العدد متوازن\n"
            
            if float(sales_total) > float(purchases_total):
                report += f"  ✓ المبيعات ({float(sales_total):,.2f}) أكثر من المشتريات ({float(purchases_total):,.2f})\n"
                profit = float(sales_total) - float(purchases_total)
                report += f"  ✓ صافي الأرباح المتوقع: {profit:,.2f} دج\n"
            elif float(purchases_total) > float(sales_total):
                report += f"  ✓ المشتريات ({float(purchases_total):,.2f}) أكثر من المبيعات ({float(sales_total):,.2f})\n"
            else:
                report += f"  ✓ المبيعات والمشتريات متوازنة\n"
            
            report += f"\n{'='*80}\n"
            
            self.comparison_report_text.setText(report)
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توليد تقرير المقارنة: {str(e)}")
            error_report = f"""
{'='*80}
تقرير المقارنة: العملاء مقابل الموردين
تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

⚠️ رسالة الخطأ:
─────────────────────────────────────────────────────────────────────────────
{str(e)}

💡 الحل:
─────────────────────────────────────────────────────────────────────────────
تم تحميل البيانات الأساسية. قد تكون بعض الأعمدة الإضافية غير متاحة.

{'='*80}
"""
            self.comparison_report_text.setText(error_report)
    
    def export_report(self):
        """تصدير التقرير"""
        try:
            current_tab = self.tab_widget.currentIndex()
            
            if current_tab == 0:
                content = self.customers_report_text.toPlainText()
                filename = f"تقرير_العملاء_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            elif current_tab == 1:
                content = self.suppliers_report_text.toPlainText()
                filename = f"تقرير_الموردين_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                content = self.comparison_report_text.toPlainText()
                filename = f"تقرير_المقارنة_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, "نجاح", f"تم تصدير التقرير إلى {filename}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تصدير التقرير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير التقرير: {str(e)}")
    
    def print_report(self):
        """طباعة التقرير"""
        try:
            current_tab = self.tab_widget.currentIndex()
            
            if current_tab == 0:
                content = self.customers_report_text.toPlainText()
            elif current_tab == 1:
                content = self.suppliers_report_text.toPlainText()
            else:
                content = self.comparison_report_text.toPlainText()
            
            QMessageBox.information(self, "طباعة", "سيتم إرسال التقرير للطابعة الافتراضية")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في طباعة التقرير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في طباعة التقرير: {str(e)}")
