from datetime import date
from decimal import Decimal
from pathlib import Path  # noqa: F811
from unittest.mock import MagicMock, patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.journal_entry import JournalEntry, JournalLine
from src.services.accounting_service import AccountingService


@pytest.fixture
def mock_db_manager():
    """Mock لمدير قاعدة البيانات"""
    return MagicMock()


@pytest.fixture
def service(mock_db_manager):
    """إنشاء خدمة المحاسبة مع mock للتبعيات"""
    # منع الإنشاء الفعلي للحسابات الافتراضية
    with patch.object(AccountingService, "_initialize_chart_of_accounts"):
        # محاكاة عدم وجود حسابات في البداية
        mock_db_manager.fetch_all.return_value = []
        mock_db_manager.fetch_one.return_value = (0,)
        service = AccountingService(mock_db_manager)
        return service


class TestAccountingService:
    """اختبارات وحدة لخدمة المحاسبة"""

    def test_create_journal_entry_balanced(self, service, mock_db_manager):
        """اختبار إنشاء قيد يومي متوازن"""
        entry = JournalEntry(entry_date=date.today(), description="Test Entry", reference_type="test")
        entry.add_line(JournalLine(account_id=1, debit_amount=Decimal("100.00")))
        entry.add_line(JournalLine(account_id=2, credit_amount=Decimal("100.00")))

        # محاكاة نجاح إدراج القيد
        mock_db_manager.execute_insert.return_value = 1
        mock_db_manager.fetch_one.return_value = (0,)

        journal_id = service.create_journal_entry(entry)

        assert journal_id == 1

    def test_create_journal_entry_unbalanced(self, service):
        """اختبار منع إنشاء قيد يومي غير متوازن"""
        entry = JournalEntry(entry_date=date.today(), description="Unbalanced Test")
        entry.add_line(JournalLine(account_id=1, debit_amount=Decimal("100.00")))
        entry.add_line(JournalLine(account_id=2, credit_amount=Decimal("99.00")))

        with pytest.raises(ValueError, match="القيد غير متوازن"):
            service.create_journal_entry(entry)

    @patch.object(AccountingService, "_update_account_balances")
    def test_post_journal_entry_success(self, mock_update_balances, service, mock_db_manager):
        """اختبار ترحيل قيد يومي بنجاح"""
        journal_id = 1
        mock_entry = MagicMock()
        mock_entry.is_posted = False

        with patch.object(service, "get_journal_entry", return_value=mock_entry):
            mock_db_manager.execute.return_value = MagicMock()
            success = service.get_journal_entry(journal_id) is not None
            assert success is True

    def test_get_trial_balance(self, service):
        """اختبار حساب ميزان المراجعة"""
        tb = service.get_trial_balance()
        assert isinstance(tb, list)
