"""
اختبارات شاملة لنموذج JournalEntry
Comprehensive tests for JournalEntry model
"""

import unittest
from datetime import datetime
from decimal import Decimal

from src.models.journal_entry import JournalEntry, JournalLine


class TestJournalLine(unittest.TestCase):
    """اختبارات سطر القيد"""

    def test_journal_line_debit(self):
        """سطر قيد مدين"""
        line = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            debit_amount=Decimal("1000.00"),
        )
        self.assertEqual(line.debit_amount, Decimal("1000.00"))
        self.assertEqual(line.credit_amount, Decimal("0.00"))
        self.assertTrue(line.is_debit())

    def test_journal_line_credit(self):
        """سطر قيد دائن"""
        line = JournalLine(
            account_id=2,
            account_code="2001",
            account_name="رأس المال",
            credit_amount=Decimal("1000.00"),
        )
        self.assertEqual(line.credit_amount, Decimal("1000.00"))
        self.assertEqual(line.debit_amount, Decimal("0.00"))
        self.assertFalse(line.is_debit())

    def test_journal_line_both_amounts_error(self):
        """خطأ عند تحديد مبلغ مدين ودائن"""
        with self.assertRaises(ValueError):
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("500.00"),
                credit_amount=Decimal("500.00"),
            )

    def test_journal_line_no_amount_error(self):
        """خطأ عند عدم تحديد مبلغ"""
        with self.assertRaises(ValueError):
            JournalLine(account_id=1, account_code="1001", account_name="النقد")

    def test_journal_line_with_description(self):
        """سطر قيد مع وصف"""
        line = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            debit_amount=Decimal("500.00"),
            description="إيداع نقدي",
        )
        self.assertEqual(line.description, "إيداع نقدي")

    def test_journal_line_with_timestamp(self):
        """سطر قيد مع طابع زمني"""
        now = datetime.now()
        line = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            debit_amount=Decimal("1000.00"),
            created_at=now,
        )
        self.assertEqual(line.created_at, now)

    def test_journal_line_is_credit(self):
        """اختبار دالة is_credit"""
        line = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            credit_amount=Decimal("500.00"),
        )
        self.assertTrue(line.is_credit())

    def test_journal_line_get_amount(self):
        """احصل على المبلغ"""
        line = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            debit_amount=Decimal("1000.00"),
        )
        self.assertEqual(line.get_amount(), Decimal("1000.00"))

    def test_journal_line_get_side(self):
        """احصل على الجانب"""
        line_debit = JournalLine(
            account_id=1,
            account_code="1001",
            account_name="النقد",
            debit_amount=Decimal("1000.00"),
        )
        self.assertEqual(line_debit.get_side(), "DEBIT")

        line_credit = JournalLine(
            account_id=2,
            account_code="2001",
            account_name="رأس المال",
            credit_amount=Decimal("1000.00"),
        )
        self.assertEqual(line_credit.get_side(), "CREDIT")


class TestJournalEntry(unittest.TestCase):
    """اختبارات القيد اليومي"""

    def test_journal_entry_creation(self):
        """إنشاء قيد يومي"""
        entry = JournalEntry(
            entry_number="JE001",
            reference_type="Sales",
            reference_id=1,
            entry_date=datetime.now(),
        )
        self.assertEqual(entry.entry_number, "JE001")
        self.assertEqual(entry.reference_type, "Sales")
        self.assertEqual(entry.reference_id, 1)

    def test_journal_entry_with_lines(self):
        """قيد يومي مع أسطر"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("1000.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="3001",
                account_name="رأس المال",
                credit_amount=Decimal("1000.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)
        self.assertEqual(len(entry.lines), 2)

    def test_journal_entry_debit_credit_balance(self):
        """التحقق من توازن المدين والدائن"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("500.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="1002",
                account_name="أوراق القبض",
                debit_amount=Decimal("500.00"),
            ),
            JournalLine(
                account_id=3,
                account_code="2001",
                account_name="الدائنون",
                credit_amount=Decimal("1000.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertEqual(entry.get_total_debits(), Decimal("1000.00"))
        self.assertEqual(entry.get_total_credits(), Decimal("1000.00"))

    def test_journal_entry_is_balanced(self):
        """فحص توازن القيد"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("1000.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="3001",
                account_name="رأس المال",
                credit_amount=Decimal("1000.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertTrue(entry.is_balanced())

    def test_journal_entry_unbalanced(self):
        """فحص عدم توازن القيد"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("1000.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="3001",
                account_name="رأس المال",
                credit_amount=Decimal("500.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertFalse(entry.is_balanced())

    def test_journal_entry_posted(self):
        """قيد مسجل"""
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, is_posted=True)
        self.assertTrue(entry.is_posted)

    def test_journal_entry_draft(self):
        """قيد مسودة"""
        entry = JournalEntry(
            entry_number="JE001",
            reference_type="Sales",
            reference_id=1,
            is_posted=False,
        )
        self.assertFalse(entry.is_posted)

    def test_journal_entry_with_notes(self):
        """قيد مع ملاحظات"""
        entry = JournalEntry(
            entry_number="JE001",
            reference_type="Sales",
            reference_id=1,
            notes="قيد تصحيح",
        )
        self.assertEqual(entry.notes, "قيد تصحيح")

    def test_journal_entry_description(self):
        """قيد مع وصف"""
        entry = JournalEntry(
            entry_number="JE001",
            reference_type="Sales",
            reference_id=1,
            description="قيد المبيعات",
        )
        self.assertEqual(entry.description, "قيد المبيعات")

    def test_journal_entry_total_amount(self):
        """حساب إجمالي المبلغ"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("2500.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="1002",
                account_name="أوراق",
                debit_amount=Decimal("2500.00"),
            ),
            JournalLine(
                account_id=3,
                account_code="2001",
                account_name="دائنون",
                credit_amount=Decimal("5000.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertEqual(entry.get_total_debits(), Decimal("5000.00"))
        self.assertEqual(entry.get_total_credits(), Decimal("5000.00"))
        self.assertTrue(entry.is_balanced())


class TestJournalEntryValidation(unittest.TestCase):
    """اختبارات التحقق من صحة القيد"""

    def test_valid_journal_entry(self):
        """قيد صحيح"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("1000.00"),
            ),
            JournalLine(
                account_id=2,
                account_code="3001",
                account_name="رأس المال",
                credit_amount=Decimal("1000.00"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertTrue(entry.is_balanced())
        self.assertEqual(len(entry.lines), 2)

    def test_single_line_entry(self):
        """قيد بسطر واحد (خطأ - لابد من سطرين على الأقل)"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("1000.00"),
            )
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertFalse(entry.is_balanced())


class TestJournalEntryEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_large_entry(self):
        """قيد كبير برصيد عالي"""
        lines = [
            JournalLine(
                account_id=1,
                account_code="1001",
                account_name="النقد",
                debit_amount=Decimal("999999999.99"),
            ),
            JournalLine(
                account_id=2,
                account_code="3001",
                account_name="رأس المال",
                credit_amount=Decimal("999999999.99"),
            ),
        ]
        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertTrue(entry.is_balanced())

    def test_many_lines_entry(self):
        """قيد برصيد عدد كبير من الأسطر"""
        lines = []
        for i in range(50):
            lines.append(
                JournalLine(
                    account_id=i,
                    account_code=f"100{i}",
                    account_name=f"حساب {i}",
                    debit_amount=Decimal("100.00"),
                )
            )
        lines.append(
            JournalLine(
                account_id=100,
                account_code="5000",
                account_name="الإجمالي",
                credit_amount=Decimal("5000.00"),
            )
        )

        entry = JournalEntry(entry_number="JE001", reference_type="Sales", reference_id=1, lines=lines)

        self.assertTrue(entry.is_balanced())


if __name__ == "__main__":
    unittest.main()
