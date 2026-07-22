#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critical test for create_purchase_journal_entry in AccountingService.

Verifies that purchase journal entries are correctly balanced:
  - Without tax: debit (inventory) == credit (payable)
  - With tax: debit (inventory + tax) == credit (payable)
  - Tax appears as a separate debit line only when tax > 0
"""

from decimal import Decimal
from unittest.mock import patch

import pytest


class TestPurchaseJournalEntry:
    """Tests for AccountingService.create_purchase_journal_entry."""

    def _make_service(self, db_manager):
        """Create an AccountingService, patching _initialize_chart_of_accounts
        to avoid querying a non-existent chart_of_accounts table."""
        from src.services.accounting_service import AccountingService
        svc = AccountingService.__new__(AccountingService)
        svc.db = db_manager
        svc.coa = type('obj', (object,), {
            'add_account': lambda self, a: None,
            'get_account_by_code': lambda self, c: None,
        })()
        svc.logger = type('obj', (object,), {
            'info': lambda *a: None,
            'warning': lambda *a: None,
            'error': lambda *a: None,
        })()
        return svc

    def test_journal_without_tax_is_balanced(self, db_manager_with_data):
        """With zero tax, debit == credit and no tax line is added."""
        svc = self._make_service(db_manager_with_data)
        purchase_data = {
            "supplier_name": "مور test",
            "po_id": "PO-1",
            "total": 1000,
            "tax": 0,
        }

        captured_entry = None

        def fake_create_entry(entry):
            nonlocal captured_entry
            captured_entry = entry
            return 99  # pretend success

        with patch.object(svc, 'create_journal_entry', side_effect=fake_create_entry):
            result = svc.create_purchase_journal_entry(purchase_data)

        assert result == 99
        assert captured_entry is not None

        # Should have exactly 2 lines: inventory debit + payable credit
        lines = captured_entry.lines
        assert len(lines) == 2

        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)

        assert total_debits == Decimal("1000")
        assert total_credits == Decimal("1000")
        assert captured_entry.is_balanced()

        # Verify line roles
        assert lines[0].account_code == "4100"
        assert lines[0].debit_amount == Decimal("1000")
        assert lines[0].credit_amount == Decimal("0")

        assert lines[1].account_code == "2100"
        assert lines[1].credit_amount == Decimal("1000")
        assert lines[1].debit_amount == Decimal("0")

    def test_journal_with_tax_is_balanced(self, db_manager_with_data):
        """With tax, inventory debit + tax debit == payable credit."""
        svc = self._make_service(db_manager_with_data)
        purchase_data = {
            "supplier_name": "مور test",
            "po_id": "PO-2",
            "total": 5000,
            "tax": 150,
        }

        captured_entry = None

        def fake_create_entry(entry):
            nonlocal captured_entry
            captured_entry = entry
            return 100

        with patch.object(svc, 'create_journal_entry', side_effect=fake_create_entry):
            result = svc.create_purchase_journal_entry(purchase_data)

        assert result == 100
        assert captured_entry is not None

        # Should have 3 lines: inventory debit, tax debit, payable credit
        lines = captured_entry.lines
        assert len(lines) == 3

        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)

        # Debits: 5000 (inventory) + 150 (tax) = 5150
        assert total_debits == Decimal("5150")
        # Credits: 5000 + 150 = 5150
        assert total_credits == Decimal("5150")
        assert captured_entry.is_balanced()

        # Tax line should be separate
        tax_line = lines[1]
        assert tax_line.account_code == "2300"
        assert tax_line.account_name == "الضريبة المستحقة"
        assert tax_line.debit_amount == Decimal("150")

        # Payable line should be total + tax
        payable_line = lines[2]
        assert payable_line.account_code == "2100"
        assert payable_line.credit_amount == Decimal("5150")

    def test_journal_balance_precision(self, db_manager_with_data):
        """Test with Decimal amounts to ensure no floating-point drift."""
        svc = self._make_service(db_manager_with_data)
        purchase_data = {
            "supplier_name": "مور",
            "po_id": "PO-3",
            "total": "3333.33",
            "tax": "666.67",
        }

        captured_entry = None

        def fake_create_entry(entry):
            nonlocal captured_entry
            captured_entry = entry
            return 1

        with patch.object(svc, 'create_journal_entry', side_effect=fake_create_entry):
            svc.create_purchase_journal_entry(purchase_data)

        lines = captured_entry.lines
        total_debits = sum(line.debit_amount for line in lines)
        total_credits = sum(line.credit_amount for line in lines)

        assert total_debits == Decimal("4000.00")
        assert total_credits == Decimal("4000.00")
        assert captured_entry.is_balanced()

    def test_journal_entry_reference_fields(self, db_manager_with_data):
        """Verify reference_type and reference_id are set correctly."""
        svc = self._make_service(db_manager_with_data)
        purchase_data = {
            "supplier_name": "مؤسسة التقنية",
            "po_id": 42,
            "total": 2000,
            "tax": 0,
        }

        captured_entry = None

        def fake_create_entry(entry):
            nonlocal captured_entry
            captured_entry = entry
            return 1

        with patch.object(svc, 'create_journal_entry', side_effect=fake_create_entry):
            svc.create_purchase_journal_entry(purchase_data)

        assert captured_entry.reference_type == "purchase_order"
        assert captured_entry.reference_id == "42"
        assert "مؤسسة التقنية" in captured_entry.description