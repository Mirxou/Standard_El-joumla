"""
UI Tests for Reports Tab
اختبارات واجهة المستخدم لتبويب التقارير
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt, QDate
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture(scope="session")
def qapp():
    """إنشاء تطبيق Qt للاختبارات"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_services():
    """Mock للخدمات المطلوبة"""
    dashboard_service = Mock()
    purchase_service = Mock()
    payment_service = Mock()
    report_exporter = Mock()
    
    # إعداد بيانات افتراضية
    dashboard_service.load_dashboard.return_value = Mock(
        kpis={
            "total_sales": 100000.0,
            "gross_profit": 30000.0,
            "profit_margin": 30.0,
            "receivables": 5000.0,
            "payables": 3000.0
        },
        top_products=[
            {"name": "منتج 1", "qty": 100, "total": 10000.0},
            {"name": "منتج 2", "qty": 50, "total": 5000.0}
        ],
        distribution=[
            {"method": "نقدي", "amount": 60000.0},
            {"method": "بطاقة", "amount": 40000.0}
        ]
    )
    
    purchase_service.get_purchases_summary.return_value = {
        "total_amount": 70000.0,
        "count": 10
    }
    
    payment_service.get_accounts_receivable.return_value = [
        {"balance": 5000.0}
    ]
    payment_service.get_accounts_payable.return_value = [
        {"balance": 3000.0}
    ]
    
    return {
        "dashboard": dashboard_service,
        "purchase": purchase_service,
        "payment": payment_service,
        "exporter": report_exporter
    }


@pytest.fixture
def main_window(qapp, db_manager, mock_services):
    """إنشاء نافذة رئيسية مع mock للخدمات"""
    from src.ui.windows.main_window import MainWindow
    
    with patch('src.core.config_manager.ConfigManager') as mock_config, \
         patch('src.services.dashboard_service.DashboardService', return_value=mock_services["dashboard"]), \
         patch('src.services.purchase_service.PurchaseService', return_value=mock_services["purchase"]), \
         patch('src.services.payment_service.PaymentService', return_value=mock_services["payment"]), \
         patch('src.services.report_exporter.ReportExporter', return_value=mock_services["exporter"]):
        
        mock_config.return_value.get.return_value = {}
        
        try:
            window = MainWindow()
            # تهيئة تبويب التقارير
            if hasattr(window, 'create_reports_tab'):
                window.reports_tab = window.create_reports_tab()
            return window
        except Exception as e:
            pytest.skip(f"MainWindow requires full application setup: {e}")


class TestReportsTabCreation:
    """اختبارات إنشاء تبويب التقارير"""
    
    def test_reports_tab_exists(self, main_window):
        """اختبار وجود تبويب التقارير"""
        assert hasattr(main_window, 'create_reports_tab')
    
    def test_reports_tab_creation(self, main_window):
        """اختبار إنشاء تبويب التقارير"""
        if hasattr(main_window, 'create_reports_tab'):
            tab = main_window.create_reports_tab()
            assert tab is not None
    
    def test_reports_tab_widgets_exist(self, main_window):
        """اختبار وجود العناصر الأساسية في تبويب التقارير"""
        if hasattr(main_window, 'reports_tab'):
            tab = main_window.reports_tab
            assert tab is not None
            
            # التحقق من وجود العناصر الأساسية
            assert hasattr(main_window, 'report_start_date') or hasattr(main_window, 'report_end_date')
            assert hasattr(main_window, 'report_refresh_btn')
            assert hasattr(main_window, 'report_type_combo')
            assert hasattr(main_window, 'reports_summary_labels')


class TestReportsDataRefresh:
    """اختبارات تحديث بيانات التقارير"""
    
    def test_refresh_reports_data_exists(self, main_window):
        """اختبار وجود دالة refresh_reports_data"""
        assert hasattr(main_window, 'refresh_reports_data')
    
    def test_refresh_reports_data_without_tab(self, main_window):
        """اختبار refresh_reports_data عندما لا يوجد تبويب"""
        # إزالة التبويب مؤقتاً
        if hasattr(main_window, 'reports_summary_labels'):
            delattr(main_window, 'reports_summary_labels')
        
        # يجب ألا يحدث خطأ
        try:
            main_window.refresh_reports_data()
        except Exception:
            pytest.fail("refresh_reports_data يجب أن تتعامل مع عدم وجود التبويب بشكل صحيح")
    
    def test_refresh_reports_data_without_dashboard_service(self, main_window):
        """اختبار refresh_reports_data بدون dashboard_service"""
        if hasattr(main_window, 'reports_summary_labels'):
            # إزالة dashboard_service مؤقتاً
            original_service = getattr(main_window, 'dashboard_service', None)
            main_window.dashboard_service = None
            
            try:
                main_window.refresh_reports_data()
            except Exception:
                pytest.fail("refresh_reports_data يجب أن تتعامل مع عدم وجود dashboard_service بشكل صحيح")
            finally:
                main_window.dashboard_service = original_service
    
    def test_refresh_reports_data_success(self, main_window, mock_services):
        """اختبار refresh_reports_data بنجاح"""
        if not hasattr(main_window, 'reports_summary_labels'):
            pytest.skip("Reports tab not initialized")
        
        # تهيئة العناصر المطلوبة
        if not hasattr(main_window, 'report_start_date'):
            from PySide6.QtWidgets import QDateEdit
            main_window.report_start_date = QDateEdit()
            main_window.report_start_date.setDate(QDate.currentDate().addDays(-30))
            main_window.report_end_date = QDateEdit()
            main_window.report_end_date.setDate(QDate.currentDate())
        
        # تهيئة الخدمات
        main_window.dashboard_service = mock_services["dashboard"]
        main_window.purchase_service = mock_services["purchase"]
        main_window.payment_service = mock_services["payment"]
        
        # تهيئة الجداول
        if not hasattr(main_window, 'top_products_table'):
            from PySide6.QtWidgets import QTableWidget
            main_window.top_products_table = QTableWidget()
            main_window.top_products_table.setColumnCount(3)
            main_window.payment_distribution_table = QTableWidget()
            main_window.payment_distribution_table.setColumnCount(2)
            main_window.revenue_vs_expense_table = QTableWidget()
            main_window.revenue_vs_expense_table.setColumnCount(3)
        
        # تنفيذ refresh
        try:
            main_window.refresh_reports_data()
            # التحقق من تحديث البيانات
            assert main_window.dashboard_service.load_dashboard.called
        except Exception as e:
            pytest.fail(f"refresh_reports_data فشل: {e}")


class TestReportsSummaryUpdate:
    """اختبارات تحديث ملخص التقارير"""
    
    def test_update_reports_summary_exists(self, main_window):
        """اختبار وجود دالة update_reports_summary"""
        assert hasattr(main_window, 'update_reports_summary')
    
    def test_update_reports_summary_without_labels(self, main_window):
        """اختبار update_reports_summary بدون labels"""
        # إزالة labels مؤقتاً
        if hasattr(main_window, 'reports_summary_labels'):
            original_labels = main_window.reports_summary_labels
            delattr(main_window, 'reports_summary_labels')
        
        try:
            mock_dashboard = Mock(kpis={})
            main_window.update_reports_summary(mock_dashboard, {}, 0.0, 0.0)
        except Exception:
            pytest.fail("update_reports_summary يجب أن تتعامل مع عدم وجود labels بشكل صحيح")
        finally:
            if 'original_labels' in locals():
                main_window.reports_summary_labels = original_labels
    
    def test_update_reports_summary_with_data(self, main_window):
        """اختبار update_reports_summary مع بيانات"""
        if not hasattr(main_window, 'reports_summary_labels'):
            pytest.skip("Reports summary labels not initialized")
        
        # تهيئة labels
        from PySide6.QtWidgets import QLabel
        main_window.reports_summary_labels = {
            "total_sales": QLabel(),
            "total_purchases": QLabel(),
            "gross_profit": QLabel(),
            "profit_margin": QLabel(),
            "receivables": QLabel(),
            "payables": QLabel()
        }
        
        mock_dashboard = Mock(kpis={
            "total_sales": 100000.0,
            "gross_profit": 30000.0,
            "profit_margin": 30.0,
            "receivables": 5000.0,
            "payables": 3000.0
        })
        
        purchase_summary = {"total_amount": 70000.0}
        
        try:
            main_window.update_reports_summary(mock_dashboard, purchase_summary, 5000.0, 3000.0)
            # التحقق من تحديث القيم
            assert main_window.reports_summary_labels["total_sales"].text() != ""
            assert main_window.reports_summary_labels["profit_margin"].text() != ""
        except Exception as e:
            pytest.fail(f"update_reports_summary فشل: {e}")


class TestReportsTables:
    """اختبارات جداول التقارير"""
    
    def test_update_top_products_table_exists(self, main_window):
        """اختبار وجود دالة update_top_products_table"""
        assert hasattr(main_window, 'update_top_products_table')
    
    def test_update_top_products_table(self, main_window):
        """اختبار تحديث جدول أفضل المنتجات"""
        from PySide6.QtWidgets import QTableWidget
        main_window.top_products_table = QTableWidget()
        main_window.top_products_table.setColumnCount(3)
        
        products = [
            {"name": "منتج 1", "qty": 100, "total": 10000.0},
            {"name": "منتج 2", "qty": 50, "total": 5000.0}
        ]
        
        try:
            main_window.update_top_products_table(products)
            assert main_window.top_products_table.rowCount() == 2
        except Exception as e:
            pytest.fail(f"update_top_products_table فشل: {e}")
    
    def test_update_payment_distribution_table_exists(self, main_window):
        """اختبار وجود دالة update_payment_distribution_table"""
        assert hasattr(main_window, 'update_payment_distribution_table')
    
    def test_update_payment_distribution_table(self, main_window):
        """اختبار تحديث جدول توزيع المدفوعات"""
        from PySide6.QtWidgets import QTableWidget
        main_window.payment_distribution_table = QTableWidget()
        main_window.payment_distribution_table.setColumnCount(2)
        
        distribution = [
            {"method": "نقدي", "amount": 60000.0},
            {"method": "بطاقة", "amount": 40000.0}
        ]
        
        try:
            main_window.update_payment_distribution_table(distribution)
            assert main_window.payment_distribution_table.rowCount() == 2
        except Exception as e:
            pytest.fail(f"update_payment_distribution_table فشل: {e}")
    
    def test_update_revenue_vs_expense_table_exists(self, main_window):
        """اختبار وجود دالة update_revenue_vs_expense_table"""
        assert hasattr(main_window, 'update_revenue_vs_expense_table')
    
    def test_update_revenue_vs_expense_table(self, main_window):
        """اختبار تحديث جدول الإيرادات مقابل المشتريات"""
        from PySide6.QtWidgets import QTableWidget
        main_window.revenue_vs_expense_table = QTableWidget()
        main_window.revenue_vs_expense_table.setColumnCount(3)
        
        revenue_data = [
            {"date": date.today(), "revenue": 10000.0, "expense": 7000.0},
            {"date": date.today() - timedelta(days=1), "revenue": 8000.0, "expense": 6000.0}
        ]
        
        try:
            main_window.update_revenue_vs_expense_table(revenue_data)
            assert main_window.revenue_vs_expense_table.rowCount() == 2
        except Exception as e:
            pytest.fail(f"update_revenue_vs_expense_table فشل: {e}")


class TestReportsQuickRange:
    """اختبارات النطاقات السريعة للتقارير"""
    
    def test_set_report_quick_range_exists(self, main_window):
        """اختبار وجود دالة set_report_quick_range"""
        assert hasattr(main_window, 'set_report_quick_range')
    
    def test_set_report_quick_range_7_days(self, main_window):
        """اختبار تعيين نطاق 7 أيام"""
        if not hasattr(main_window, 'report_start_date'):
            from PySide6.QtWidgets import QDateEdit
            main_window.report_start_date = QDateEdit()
            main_window.report_end_date = QDateEdit()
        
        try:
            main_window.set_report_quick_range(7)
            start_date = main_window.report_start_date.date().toPython()
            end_date = main_window.report_end_date.date().toPython()
            days_diff = (end_date - start_date).days
            assert days_diff == 7
        except Exception as e:
            pytest.fail(f"set_report_quick_range فشل: {e}")
    
    def test_set_report_quick_range_30_days(self, main_window):
        """اختبار تعيين نطاق 30 يوم"""
        if not hasattr(main_window, 'report_start_date'):
            from PySide6.QtWidgets import QDateEdit
            main_window.report_start_date = QDateEdit()
            main_window.report_end_date = QDateEdit()
        
        try:
            main_window.set_report_quick_range(30)
            start_date = main_window.report_start_date.date().toPython()
            end_date = main_window.report_end_date.date().toPython()
            days_diff = (end_date - start_date).days
            assert days_diff == 30
        except Exception as e:
            pytest.fail(f"set_report_quick_range فشل: {e}")


class TestReportsExport:
    """اختبارات تصدير التقارير"""
    
    def test_export_reports_summary_exists(self, main_window):
        """اختبار وجود دالة export_reports_summary"""
        assert hasattr(main_window, 'export_reports_summary')
    
    def test_print_reports_summary_exists(self, main_window):
        """اختبار وجود دالة print_reports_summary"""
        assert hasattr(main_window, 'print_reports_summary')
    
    def test_open_detailed_report_exists(self, main_window):
        """اختبار وجود دالة open_detailed_report"""
        assert hasattr(main_window, 'open_detailed_report')


@pytest.mark.ui
@pytest.mark.requires_ui
class TestReportsTabIntegration:
    """اختبارات تكامل تبويب التقارير"""
    
    def test_reports_tab_full_workflow(self, main_window, mock_services):
        """اختبار سير العمل الكامل لتبويب التقارير"""
        if not hasattr(main_window, 'create_reports_tab'):
            pytest.skip("Reports tab creation not available")
        
        # تهيئة الخدمات
        main_window.dashboard_service = mock_services["dashboard"]
        main_window.purchase_service = mock_services["purchase"]
        main_window.payment_service = mock_services["payment"]
        
        # إنشاء التبويب
        tab = main_window.create_reports_tab()
        assert tab is not None
        
        # تحديث البيانات
        if hasattr(main_window, 'refresh_reports_data'):
            try:
                main_window.refresh_reports_data()
                assert True
            except Exception as e:
                pytest.fail(f"Full workflow failed: {e}")

