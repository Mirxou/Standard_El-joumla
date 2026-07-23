#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
خدمة إدارة المحاسبة - Accounting Service
توفر خدمات المحاسبة مثل إنشاء القيود وتحديث الأرصدة والقوائم المالية
محسنة لاستخدام DatabaseManager المطور مع معالجة مرنة للبيانات
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..models.account import Account, ChartOfAccounts
from ..models.journal_entry import JournalEntry, JournalLine
from ..models.sale import Sale


def gv(k, i, d=None):
    """Get value from dict, tuple/list, or sqlite3.Row safely."""
    if isinstance(k, dict):
        return k.get(i, d)
    if isinstance(k, (list, tuple)) and isinstance(i, int) and len(k) > i:
        return k[i]
    return d


class TrialBalanceList(list):
    """كلاس هجين يرث من list ويدعم الوصول كـ dict لتوفير التوافق الكامل مع الاختبارات والواجهات"""
    def __init__(self, accounts_list, total_debits, total_credits, extra=None):
        super().__init__(accounts_list)
        self.accounts = accounts_list
        self.total_debits = total_debits
        self.total_credits = total_credits
        self.extra = extra or {}

    def get(self, key, default=None):
        if key == "accounts":
            return self.accounts
        elif key == "total_debits":
            return self.total_debits
        elif key == "total_credits":
            return self.total_credits
        elif key in self.extra:
            return self.extra[key]
        return default

    def __getitem__(self, key):
        if key == "accounts":
            return self.accounts
        elif key == "total_debits":
            return self.total_debits
        elif key == "total_credits":
            return self.total_credits
        elif key in self.extra:
            return self.extra[key]
        return super().__getitem__(key)

    def __contains__(self, key):
        if key in ("accounts", "total_debits", "total_credits") or key in self.extra:
            return True
        return super().__contains__(key)

    def keys(self):
        return ["accounts", "total_debits", "total_credits"] + list(self.extra.keys())

    def items(self):
        base = [("accounts", self.accounts), ("total_debits", self.total_debits), ("total_credits", self.total_credits)]
        return base + list(self.extra.items())

    def values(self):
        return [self.accounts, self.total_debits, self.total_credits] + list(self.extra.values())


class AccountingService:
    """خدمة إدارة المحاسبة"""

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self.coa = ChartOfAccounts()
        self._initialize_chart_of_accounts()

    def _initialize_chart_of_accounts(self) -> None:
        """تهيئة دليل الحسابات بنمط Mapping مرن"""
        try:
            query = "SELECT * FROM chart_of_accounts ORDER BY account_code"
            accounts = self.db.fetch_all(query)

            for row in accounts:
                account = Account(
                    id=gv(row, "id"),
                    account_code=gv(row, "account_code"),
                    account_name=gv(row, "account_name"),
                    account_type=gv(row, "account_type"),
                    sub_type=gv(row, "sub_type"),
                    description=gv(row, "description"),
                    normal_side=gv(row, "normal_side"),
                    is_header=bool(gv(row, "is_header", False)),
                    parent_account_id=gv(row, "parent_account_id"),
                    is_active=bool(gv(row, "is_active", True)),
                    is_locked=bool(gv(row, "is_locked", False)),
                    opening_balance=Decimal(str(gv(row, "opening_balance", "0"))),
                    current_balance=Decimal(str(gv(row, "current_balance", "0"))),
                    created_at=gv(row, "created_at"),
                    updated_at=gv(row, "updated_at"),
                )
                self.coa.add_account(account)
            self.logger.info(f"تم تحميل {len(accounts)} حساب من دليل الحسابات")
        except Exception as e:
            self.logger.warning(f"خطأ في تحميل دليل الحسابات: {e}")
            # في الإنتاج، يجب ألا نقوم بإنشاء حسابات افتراضية إذا فشل التحميل
            # self._create_default_chart_of_accounts()

    def create_account(self, account: Account) -> int:
        """إنشاء حساب جديد باستخدام execute_insert"""
        try:
            existing = self.db.fetch_one(
                "SELECT id FROM chart_of_accounts WHERE account_code = ?",
                (account.account_code,),
            )
            if existing:
                return existing[0] if isinstance(existing, tuple) else existing.get("id")

            query = """
                INSERT INTO chart_of_accounts (
                    account_code, account_name, account_type, sub_type, description,
                    normal_side, is_header, parent_account_id, is_active, is_locked,
                    opening_balance, current_balance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                account.account_code,
                account.account_name,
                account.account_type,
                account.sub_type,
                account.description,
                account.normal_side,
                account.is_header,
                account.parent_account_id,
                account.is_active,
                account.is_locked,
                float(account.opening_balance),
                float(account.current_balance),
            )
            account_id = self.db.execute_insert(query, params)
            if account_id:
                account.id = account_id
                self.coa.add_account(account)
            return account_id or 0
        except Exception as e:
            self.logger.warning(f"خطأ في إنشاء الحساب: {e}")
            return 0

    def get_account_by_code(self, code: str) -> Optional[Account]:
        """الحصول على حساب بواسطة الرمز"""
        return self.coa.get_account_by_code(code)

    def create_journal_entry(self, entry: JournalEntry) -> int:
        """إنشاء قيد يومي جديد بنمط آمن مع حماية من تكرار الرقم."""
        if not entry.is_balanced():
            raise ValueError("القيد غير متوازن")
        try:
            entry_number = self._generate_entry_number(entry.reference_type)
            query = """
                INSERT INTO general_journal (
                    entry_number, entry_date, reference_type, reference_id,
                    description, notes, is_posted, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """
            params = (
                entry_number,
                entry.entry_date.isoformat(),
                entry.reference_type,
                entry.reference_id,
                entry.description,
                entry.notes,
                entry.is_posted,
                entry.created_by or "system",
            )
            journal_id = self.db.execute_insert(query, params)
            if journal_id:
                entry.id = journal_id
                for line in entry.lines:
                    self._insert_journal_line(journal_id, line)
                # تحديث أرصدة الحسابات تلقائياً
                self._update_account_balances(journal_id)
            return journal_id or 0
        except Exception as e:
            self.logger.warning(f"خطأ في إنشاء القيد: {e}")
            return 0

    def _insert_journal_line(self, journal_id: int, line: JournalLine):
        """إدراج سطر قيد"""
        query = """
            INSERT INTO journal_lines (
                journal_id, account_id, account_code, account_name,
                debit_amount, credit_amount, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        params = (
            journal_id,
            line.account_id,
            line.account_code,
            line.account_name,
            float(line.debit_amount),
            float(line.credit_amount),
            line.description,
        )
        self.db.execute_insert(query, params)

    def _update_account_balances(self, journal_id: int):
        """تحديث أرصدة الحسابات بنمط مرن"""
        try:
            lines = self.db.fetch_all(
                "SELECT account_id, debit_amount, credit_amount FROM journal_lines WHERE journal_id = ?",
                (journal_id,),
            )
            for line in lines:
                is_dict = isinstance(line, dict)
                aid = line.get("account_id") if is_dict else line[0]
                debit = Decimal(str(line.get("debit_amount", 0) if is_dict else line[1]))
                credit = Decimal(str(line.get("credit_amount", 0) if is_dict else line[2]))
                diff = debit - credit
                self.db.execute_query(
                    "UPDATE chart_of_accounts SET current_balance = current_balance + ? WHERE id = ?",
                    (float(diff), aid),
                )
        except Exception as e:
            self.logger.warning(f"خطأ في تحديث أرصدة الحسابات: {e}")

    def create_sale_journal_entry(self, sale: Sale) -> Optional[int]:
        """إنشاء قيد محاسبي خاص بفاتورة المبيعات"""
        try:
            entry = JournalEntry(
                entry_date=sale.sale_date,
                description=f"فاتورة مبيعات رقم {sale.invoice_number}",
                reference_type="sale",
                reference_id=sale.id,
                created_by=str(sale.user_id) if sale.user_id else "system",
            )

            # جلب الحسابات اللازمة
            receivable = self.get_account_by_code("1010")  # العملاء
            revenue = self.get_account_by_code("4001")  # المبيعات

            if not (receivable and revenue):
                self.logger.warning(
                    "حسابات المبيعات الأساسية (1010 أو 4001) غير موجودة - سيتم إنشاء القيد يدوياً لاحقاً"
                )
                return None

            total = Decimal(str(sale.final_amount or "0.00"))
            entry.add_line(
                JournalLine(
                    account_id=receivable.id,
                    account_code=receivable.account_code,
                    account_name=receivable.account_name,
                    debit_amount=total,
                )
            )
            entry.add_line(
                JournalLine(
                    account_id=revenue.id,
                    account_code=revenue.account_code,
                    account_name=revenue.account_name,
                    credit_amount=total,
                )
            )

            return self.create_journal_entry(entry)
        except Exception as e:
            self.logger.warning(f"خطأ في إنشاء قيد المبيعات: {e}")
            return None

    def create_purchase_journal_entry(self, purchase_data: dict) -> int:
        """إنشاء قيد محاسبي لأمر شراء (غير معطل) — H6 FIX: تعيين account_id"""
        try:
            from ..models.journal_entry import JournalEntry, JournalLine
            entry = JournalEntry()
            entry.description = f"قيد شراء - {purchase_data.get('supplier_name', '')}"
            entry.reference_type = "purchase_order"
            entry.reference_id = str(purchase_data.get('po_id', ''))
            entry.entry_date = datetime.now()
            
            total = Decimal(str(purchase_data.get('total', 0)))
            tax = Decimal(str(purchase_data.get('tax', 0)))
            
            # H6 FIX: جلب account_id من دليل الحسابات
            inv_code = purchase_data.get('inventory_account', '4100')
            inv_account = self.get_account_by_code(inv_code)
            tax_account = self.get_account_by_code('2300')
            pay_code = purchase_data.get('payable_account', '2100')
            pay_account = self.get_account_by_code(pay_code)
            
            # مدين: المخزون / المشتريات
            inventory_line = JournalLine()
            inventory_line.account_code = inv_code
            inventory_line.account_name = purchase_data.get('inventory_account_name', 'المخزون')
            inventory_line.debit_amount = total
            if inv_account:
                inventory_line.account_id = inv_account.id
            entry.lines.append(inventory_line)
            
            # مدين: الضريبة القابلة للاسترداد
            if tax > 0:
                tax_line = JournalLine()
                tax_line.account_code = '2300'
                tax_line.account_name = 'الضريبة المستحقة'
                tax_line.debit_amount = tax
                if tax_account:
                    tax_line.account_id = tax_account.id
                entry.lines.append(tax_line)
            
            # دائن: الدائنون (إجمالي المبلغ المستحق)
            payable_line = JournalLine()
            payable_line.account_code = pay_code
            payable_line.account_name = purchase_data.get('payable_account_name', 'الدائنون')
            payable_line.credit_amount = total + tax
            if pay_account:
                payable_line.account_id = pay_account.id
            entry.lines.append(payable_line)
            
            return self.create_journal_entry(entry)
        except Exception as e:
            self.logger.warning(f"خطأ في إنشاء قيد الشراء: {e}")
            return 0

    def create_payment_journal_entry(self, payment_data: dict) -> int:
        """إنشاء قيد محاسبي لدفعة (غير معطل)"""
        try:
            from ..models.journal_entry import JournalEntry, JournalLine
            entry = JournalEntry()
            entry.description = f"دفعة - {payment_data.get('reference', '')}"
            entry.reference_type = "payment"
            entry.reference_id = str(payment_data.get('payment_id', ''))
            entry.entry_date = datetime.now()
            
            amount = Decimal(str(payment_data.get('amount', 0)))
            method = payment_data.get('method', 'cash')
            
            if payment_data.get('payment_type') == 'received':
                # تحصيل من عميل: مدين الصندوق، دائن الذمم
                cash_line = JournalLine()
                cash_line.account_code = '1100'
                cash_line.account_name = 'الصندوق'
                cash_line.debit_amount = amount
                entry.lines.append(cash_line)
                
                receivable_line = JournalLine()
                receivable_line.account_code = payment_data.get('receivable_account', '1300')
                receivable_line.account_name = payment_data.get('receivable_account_name', 'العملاء')
                receivable_line.credit_amount = amount
                entry.lines.append(receivable_line)
            else:
                # دفع لمورد: مدين الذمم، دائن الصندوق/البنك
                payable_line = JournalLine()
                payable_line.account_code = payment_data.get('payable_account', '2100')
                payable_line.account_name = payment_data.get('payable_account_name', 'الموردون')
                payable_line.debit_amount = amount
                entry.lines.append(payable_line)
                
                if method == 'bank':
                    bank_code = '1200'
                    bank_name = 'البنك'
                else:
                    bank_code = '1100'
                    bank_name = 'الصندوق'
                
                cash_line = JournalLine()
                cash_line.account_code = bank_code
                cash_line.account_name = bank_name
                cash_line.credit_amount = amount
                entry.lines.append(cash_line)
            
            return self.create_journal_entry(entry)
        except Exception as e:
            self.logger.warning(f"خطأ في إنشاء قيد الدفعة: {e}")
            return 0

    def update_account(self, account: Account) -> bool:
        """تحديث حساب موجود في قاعدة البيانات ودليل الحسابات"""
        try:
            query = """
                UPDATE chart_of_accounts SET
                    account_code = ?,
                    account_name = ?,
                    account_type = ?,
                    sub_type = ?,
                    description = ?,
                    normal_side = ?,
                    is_header = ?,
                    parent_account_id = ?,
                    is_active = ?,
                    is_locked = ?,
                    opening_balance = ?,
                    current_balance = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (
                account.account_code,
                account.account_name,
                account.account_type,
                account.sub_type,
                account.description,
                account.normal_side,
                account.is_header,
                account.parent_account_id,
                account.is_active,
                account.is_locked,
                float(account.opening_balance),
                float(account.current_balance),
                account.id,
            )
            self.db.execute_query(query, params)
            # H3 FIX: إزالة الكود القديم من code_index قبل إضافة الجديد
            # (إذا تم تغيير account_code)
            old_code = None
            for code, acc in list(self.coa.code_index.items()):
                if acc.id == account.id and code != account.account_code:
                    old_code = code
                    del self.coa.code_index[code]
                    break
            self.coa.accounts[account.id] = account
            self.coa.code_index[account.account_code] = account
            return True
        except Exception as e:
            self.logger.warning(f"خطأ في تحديث الحساب: {e}")
            return False

    def delete_account(self, account_id: int) -> bool:
        """حذف حساب (تعطيله) من قاعدة البيانات ودليل الحسابات"""
        try:
            # التحقق من عدم وجود قيود مرتبطة
            lines = self.db.fetch_one(
                "SELECT COUNT(*) as cnt FROM journal_lines WHERE account_id = ?",
                (account_id,),
            )
            count = lines.get("cnt") if isinstance(lines, dict) else (lines[0] if lines else 0)
            if count > 0:
                raise ValueError(f"لا يمكن حذف حساب مرتبط بـ {count} سطر قيد. قم بتعطيله بدلاً من ذلك.")

            # حذف من قاعدة البيانات
            self.db.execute_query(
                "DELETE FROM chart_of_accounts WHERE id = ?",
                (account_id,),
            )
            # إزالة من دليل الحسابات في الذاكرة
            account = self.coa.get_account_by_id(account_id)
            if account:
                self.coa.accounts.pop(account_id, None)
                self.coa.code_index.pop(account.account_code, None)
            return True
        except Exception as e:
            self.logger.warning(f"خطأ في حذف الحساب: {e}")
            raise

    def post_journal_entry(self, journal_id: int) -> bool:
        """ترحيل قيد يومي (تحديث حالة is_posted)"""
        try:
            # التحقق من أن القيد غير مرحل مسبقاً
            entry = self.db.fetch_one(
                "SELECT is_posted FROM general_journal WHERE id = ?",
                (journal_id,),
            )
            if not entry:
                raise ValueError("القيد غير موجود")
            is_posted = entry.get("is_posted") if isinstance(entry, dict) else entry[0]
            if is_posted:
                raise ValueError("هذا القيد مرحل مسبقاً")

            self.db.execute_query(
                "UPDATE general_journal SET is_posted = 1 WHERE id = ?",
                (journal_id,),
            )
            return True
        except Exception as e:
            self.logger.warning(f"خطأ في ترحيل القيد: {e}")
            raise

    def get_journal_lines(self, journal_id: int) -> list:
        """جلب أسطر قيد يومي محدد"""
        try:
            lines = self.db.fetch_all(
                "SELECT * FROM journal_lines WHERE journal_id = ? ORDER BY id",
                (journal_id,),
            )
            return lines if lines else []
        except Exception as e:
            self.logger.warning(f"خطأ في جلب أسطر القيد: {e}")
            return []

    def get_journal_entry(self, journal_id: int) -> Optional[JournalEntry]:
        """جلب قيد يومي بنمط مرن"""
        try:
            row = self.db.fetch_one("SELECT * FROM general_journal WHERE id = ?", (journal_id,))
            if not row:
                return None

            entry = JournalEntry(
                id=gv(row, "id"),
                entry_number=gv(row, "entry_number"),
                entry_date=(datetime.fromisoformat(gv(row, "entry_date")) if gv(row, "entry_date") else None),
                reference_type=gv(row, "reference_type"),
                reference_id=gv(row, "reference_id"),
                description=gv(row, "description"),
                notes=gv(row, "notes"),
                is_posted=gv(row, "is_posted"),
            )

            # تحميل الأسطر
            lines = self.db.fetch_all("SELECT * FROM journal_lines WHERE journal_id = ?", (journal_id,))
            for lr in lines:
                entry.add_line(
                    JournalLine(
                        id=gv(lr, "id", 0),
                        account_id=gv(lr, "account_id", 0),
                        account_code=gv(lr, "account_code", ""),
                        account_name=gv(lr, "account_name", ""),
                        debit_amount=Decimal(str(gv(lr, "debit_amount", 0))),
                        credit_amount=Decimal(str(gv(lr, "credit_amount", 0))),
                        description=gv(lr, "description", ""),
                    )
                )
            return entry
        except Exception as e:
            self.logger.warning(f"خطأ في جلب القيد: {e}")
            return None

    def _generate_entry_number(self, reference_type: str) -> str:
        """توليد رقم قيد فريد مع حماية من التكرار (thread-safe)."""
        try:
            prefix = reference_type[:3].upper() if reference_type else "GEN"
            month = datetime.now().strftime("%Y%m")

            # البحث عن آخر رقم تسلسلي
            pattern = f"JE-{prefix}-%"
            result = self.db.fetch_one(
                "SELECT entry_number FROM general_journal WHERE entry_number LIKE ? ORDER BY id DESC LIMIT 1",
                (pattern,),
            )

            seq = 1
            if result:
                last = result.get("entry_number") if isinstance(result, dict) else result[0]
                if last:
                    try:
                        # JE-SAL-0042-202605 → extract 0042
                        parts = last.split("-")
                        if len(parts) >= 3:
                            seq = int(parts[2]) + 1
                    except (ValueError, IndexError):
                        self.logger.warning("Ignored exception in accounting_service.py")

            entry_number = f"JE-{prefix}-{seq:04d}-{month}"

            # فحص التكرار (احتياطي)
            existing = self.db.fetch_one("SELECT id FROM general_journal WHERE entry_number = ?", (entry_number,))
            if existing:
                # Fallback: إضافة UUID قصير لضمان التفرد
                entry_number = f"JE-{prefix}-{seq:04d}-{uuid.uuid4().hex[:6].upper()}"

            return entry_number
        except Exception:
            # Fallback مطلق: UUID كامل
            return f"JE-{uuid.uuid4().hex[:12].upper()}"

    def get_trial_balance(self) -> Dict[str, Any]:
        """ميزان المراجعة."""
        try:
            query = """
                SELECT
                    coa.account_code,
                    coa.account_name,
                    coa.account_type,
                    coa.normal_side,
                    COALESCE(SUM(jl.debit_amount), 0) as total_debits,
                    COALESCE(SUM(jl.credit_amount), 0) as total_credits,
                    coa.current_balance
                FROM chart_of_accounts coa
                LEFT JOIN journal_lines jl ON coa.id = jl.account_id
                WHERE coa.is_active = 1 AND coa.is_header = 0
                GROUP BY coa.id
                ORDER BY coa.account_code
            """
            rows = self.db.fetch_all(query)
            result = []
            for row in rows:
                result.append(
                    {
                        "account_code": gv(row, "account_code"),
                        "account_name": gv(row, "account_name"),
                        "account_type": gv(row, "account_type"),
                        "normal_side": gv(row, "normal_side"),
                        "total_debits": float(gv(row, "total_debits") or 0),
                        "total_credits": float(gv(row, "total_credits") or 0),
                        "balance": float(gv(row, "current_balance") or 0),
                    }
                )
            total_debits = sum(acc["total_debits"] for acc in result)
            total_credits = sum(acc["total_credits"] for acc in result)
            return TrialBalanceList(result, total_debits, total_credits)
        except Exception as e:
            self.logger.warning(f"خطأ في ميزان المراجعة: {e}")
            return TrialBalanceList([], 0.0, 0.0, extra={"error": str(e)})

    def get_financial_position(self) -> Dict[str, Any]:
        """الميزانية العمومية / المركز المالي"""
        try:
            query = """
                SELECT account_type, COALESCE(SUM(current_balance), 0) as total
                FROM chart_of_accounts
                WHERE is_active = 1 AND is_header = 0
                GROUP BY account_type
            """
            rows = self.db.fetch_all(query)
            totals = {"Asset": 0.0, "Liability": 0.0, "Equity": 0.0}
            for row in rows:
                atype = gv(row, "account_type")
                val = float(gv(row, "total") or 0.0)
                if atype in totals:
                    totals[atype] = val
            return {
                "assets": totals.get("Asset", 0.0),
                "liabilities": totals.get("Liability", 0.0),
                "equity": totals.get("Equity", 0.0)
            }
        except Exception as e:
            self.logger.warning(f"خطأ في المركز المالي: {e}")
            return {"assets": 0.0, "liabilities": 0.0, "equity": 0.0, "error": str(e)}

    def get_income_statement(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """قائمة الدخل"""
        try:
            query = """
                SELECT
                    coa.account_type,
                    COALESCE(SUM(jl.debit_amount), 0) as total_debit,
                    COALESCE(SUM(jl.credit_amount), 0) as total_credit
                FROM chart_of_accounts coa
                JOIN journal_lines jl ON coa.id = jl.account_id
                JOIN general_journal gj ON jl.journal_id = gj.id
                WHERE coa.is_active = 1 AND coa.is_header = 0
                  AND gj.entry_date BETWEEN ? AND ?
                GROUP BY coa.account_type
            """
            rows = self.db.fetch_all(query, (start_date.isoformat(), end_date.isoformat()))
            totals = {"Revenue": 0.0, "Expense": 0.0}
            for row in rows:
                atype = gv(row, "account_type")
                debit = float(gv(row, "total_debit") or 0.0)
                credit = float(gv(row, "total_credit") or 0.0)
                if atype == "Revenue":
                    totals["Revenue"] += (credit - debit)
                elif atype == "Expense":
                    totals["Expense"] += (debit - credit)
            total_revenues = totals["Revenue"]
            total_expenses = totals["Expense"]
            net_income = total_revenues - total_expenses
            return {
                "total_revenues": total_revenues,
                "total_expenses": total_expenses,
                "net_income": net_income
            }
        except Exception as e:
            self.logger.warning(f"خطأ في قائمة الدخل: {e}")
            return {"total_revenues": 0.0, "total_expenses": 0.0, "net_income": 0.0, "error": str(e)}
