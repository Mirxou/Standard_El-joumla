import pytest
from unittest.mock import MagicMock, patch, ANY
from decimal import Decimal
from datetime import date
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.accounting_service import AccountingService
from src.models.account import Account, ChartOfAccounts
from src.models.journal_entry import JournalEntry, JournalLine

@pytest.fixture
def mock_db_manager():
    """Mock لمدير قاعدة البيانات"""
    return MagicMock()

@pytest.fixture
def service(mock_db_manager):
    """إنشاء خدمة المحاسبة مع mock للتبعيات"""
    # منع الإنشاء الفعلي للحسابات الافتراضية
    with patch.object(AccountingService, '_create_default_chart_of_accounts'):
        # محاكاة عدم وجود حسابات في البداية
        mock_db_manager.fetch_all.return_value = []
        service = AccountingService(mock_db_manager)
        return service

class TestAccountingService:
    """اختبارات وحدة لخدمة المحاسبة"""

    def test_create_journal_entry_balanced(self, service, mock_db_manager):
        """اختبار إنشاء قيد يومي متوازن"""
        entry = JournalEntry(
            entry_date=date.today(),
            description="Test Entry",
            reference_type="test"
        )
        entry.add_line(JournalLine(account_id=1, debit_amount=Decimal("100.00")))
        entry.add_line(JournalLine(account_id=2, credit_amount=Decimal("100.00")))

        # محاكاة أن القيد غير موجود مسبقاً
        mock_db_manager.fetch_one.return_value = (0,)
        # محاكاة نجاح إدراج القيد
        mock_db_manager.execute.return_value.lastrowid = 1

        journal_id = service.create_journal_entry(entry)

        assert journal_id == 1
        # التحقق من أنه تم استدعاء دالة الإدراج ثلاث مرات (للقيد الرئيسي وسطرين)
        assert mock_db_manager.execute.call_count >= 3

    def test_create_journal_entry_unbalanced(self, service):
        """اختبار منع إنشاء قيد يومي غير متوازن"""
        entry = JournalEntry(
            entry_date=date.today(),
            description="Unbalanced Test"
        )
        entry.add_line(JournalLine(account_id=1, debit_amount=Decimal("100.00")))
        entry.add_line(JournalLine(account_id=2, credit_amount=Decimal("99.00")))

        with pytest.raises(ValueError, match="القيد غير متوازن"):
            service.create_journal_entry(entry)

    @patch.object(AccountingService, '_update_account_balances')
    def test_post_journal_entry_success(self, mock_update_balances, service, mock_db_manager):
        """اختبار ترحيل قيد يومي بنجاح"""
        journal_id = 1
        mock_entry = JournalEntry(id=journal_id, is_posted=False)
        mock_entry.add_line(JournalLine(debit_amount=100))
        mock_entry.add_line(JournalLine(credit_amount=100))

        # محاكاة أن القيد موجود وغير مرحل
        with patch.object(service, 'get_journal_entry', return_value=mock_entry):
            success = service.post_journal_entry(journal_id, "test_user")

            assert success is True
            # التحقق من تحديث حالة القيد في قاعدة البيانات
            # التحقق من أن execute تم استدعاؤه مع query يحتوي على UPDATE
            execute_calls = [call for call in mock_db_manager.execute.call_args_list 
                           if call and len(call[0]) > 0 and "UPDATE" in str(call[0][0]) and "is_posted" in str(call[0][0])]
            assert len(execute_calls) > 0, "لم يتم استدعاء UPDATE للترحيل"
            # التحقق من استدعاء دالة تحديث الأرصدة
            mock_update_balances.assert_called_once_with(journal_id)

    def test_get_trial_balance(self, service):
        """اختبار حساب ميزان المراجعة"""
        # إعداد حسابات وهمية
        account1 = Account(id=1, account_code="1001", account_name="Cash", 
                          account_type="Asset", normal_side="DEBIT")
        account2 = Account(id=2, account_code="3001", account_name="Capital", 
                          account_type="Equity", normal_side="CREDIT")
        
        # محاكاة أن هذه الحسابات موجودة في دليل الحسابات
        service.coa.accounts = {1: account1, 2: account2}
        
        # محاكاة أرصدة الحسابات
        with patch.object(service, 'get_account_balance') as mock_get_balance:
            mock_get_balance.side_effect = [Decimal("1000.00"), Decimal("1000.00")]
            
            trial_balance = service.get_trial_balance()
            
            assert trial_balance["is_balanced"] is True
            assert trial_balance["total_debits"] == 1000.00
            assert trial_balance["total_credits"] == 1000.00
            assert len(trial_balance["accounts"]) == 2
            assert trial_balance["accounts"][0]["debit"] == 1000.00
            assert trial_balance["accounts"][1]["credit"] == 1000.00




