import pytest
from unittest.mock import MagicMock, patch, mock_open
from decimal import Decimal
import pandas as pd
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.report_exporter import ReportExporter

@pytest.fixture
def mock_db_manager():
    """Mock لمدير قاعدة البيانات"""
    return MagicMock()

@pytest.fixture
def exporter(mock_db_manager):
    """إنشاء خدمة تصدير التقارير"""
    return ReportExporter(mock_db_manager)

@pytest.fixture
def sample_data():
    """بيانات تقرير وهمية"""
    return [
        {'id': 1, 'name': 'منتج 1', 'price': Decimal('100.50'), 'quantity': 10},
        {'id': 2, 'name': 'منتج 2', 'price': Decimal('250.00'), 'quantity': 5},
    ]

class TestReportExporter:
    """اختبارات وحدة لخدمة تصدير التقارير"""

    @patch('src.services.report_exporter.HTML')
    def test_export_to_pdf(self, mock_html, exporter, sample_data, tmp_path):
        """اختبار التصدير إلى PDF"""
        output_path = tmp_path / "report.pdf"
        
        exporter.export_to_pdf(sample_data, "تقرير وهمي", str(output_path))
        
        # التحقق من أن WeasyPrint تم استدعاؤه
        mock_html.assert_called_once()
        
        # التحقق من أن محتوى HTML يحتوي على البيانات
        html_content = mock_html.call_args[0][0]
        assert "<h1>تقرير وهمي</h1>" in html_content
        assert "<td>منتج 1</td>" in html_content
        assert "<td>100.5</td>" in html_content
        
        # التحقق من أن دالة كتابة الملف تم استدعاؤها
        mock_html.return_value.write_pdf.assert_called_once_with(str(output_path))

    @patch('pandas.DataFrame.to_excel')
    def test_export_to_excel(self, mock_to_excel, exporter, sample_data, tmp_path):
        """اختبار التصدير إلى Excel"""
        output_path = tmp_path / "report.xlsx"
        
        exporter.export_to_excel(sample_data, str(output_path))
        
        # التحقق من أن to_excel تم استدعاؤها
        mock_to_excel.assert_called_once()
        
        # التحقق من المسار الصحيح
        assert mock_to_excel.call_args[0][0] == str(output_path)
        
        # التحقق من أن index=False (لعدم كتابة فهرس pandas في الملف)
        assert mock_to_excel.call_args[1]['index'] is False

    def test_export_to_csv(self, exporter, sample_data, tmp_path):
        """اختبار التصدير إلى CSV"""
        output_path = tmp_path / "report.csv"
        
        # استخدام mock_open لعزل نظام الملفات
        m = mock_open()
        with patch("builtins.open", m):
            exporter.export_to_csv(sample_data, str(output_path))
            
            # التحقق من أن الملف تم فتحه للكتابة
            m.assert_called_once_with(str(output_path), 'w', newline='', encoding='utf-8-sig')
            
            # التحقق من أن البيانات تم كتابتها
            handle = m()
            # التحقق من كتابة الرؤوس
            handle.write.assert_any_call('id,name,price,quantity\n')
            # التحقق من كتابة الصف الأول
            handle.write.assert_any_call('1,منتج 1,100.50,10\n')

    @patch.object(ReportExporter, 'export_to_pdf')
    @patch.object(ReportExporter, 'export_to_excel')
    @patch.object(ReportExporter, 'export_to_csv')
    def test_export_report_dispatcher(self, mock_csv, mock_excel, mock_pdf, exporter, sample_data):
        """اختبار أن دالة export_report تستدعي الدالة الصحيحة حسب الصيغة"""
        
        # اختبار PDF
        exporter.export_report(sample_data, "Test", "test.pdf", "pdf")
        mock_pdf.assert_called_once()
        mock_excel.assert_not_called()
        mock_csv.assert_not_called()
        
        # إعادة تعيين mocks
        mock_pdf.reset_mock()
        
        # اختبار Excel
        exporter.export_report(sample_data, "Test", "test.xlsx", "excel")
        mock_pdf.assert_not_called()
        mock_excel.assert_called_once()
        mock_csv.assert_not_called()
        
        # إعادة تعيين mocks
        mock_excel.reset_mock()
        
        # اختبار CSV
        exporter.export_report(sample_data, "Test", "test.csv", "csv")
        mock_pdf.assert_not_called()
        mock_excel.assert_not_called()
        mock_csv.assert_called_once()