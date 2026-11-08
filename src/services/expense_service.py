#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة المصاريف - Expense Service
إدارة المصاريف التشغيلية: تصنيفات، مصاريف، مصاريف متكررة، قيود محاسبية.

Features:
- تصنيفات المصاريف (Expense Categories) مرتبطة بحسابات دليل الحسابات
- CRUD كامل للمصاريف مع حالات (معلق/موافق عليه/مرفوض)
- قيد محاسبي تلقائي عند الموافقة: مدين المصروف / دائن الصندوق
- مصاريف متكررة (Recurring): يومي/أسبوعي/شهري/سنوي + توليد المستحق
- إحصاءات: إجمالي حسب الفئة/الشهر
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ExpenseStatus:
    """حالات المصروف"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseService:
    """خدمة إدارة المصاريف"""

    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or setup_logger(__name__)
        self._ensure_tables()

    # ────────────────────────── Schema ──────────────────────────

    def _ensure_tables(self) -> None:
        """إنشاء جداول المصاريف + التصنيفات الافتراضية"""
        try:
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS expense_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    account_code TEXT DEFAULT '5000',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_number TEXT UNIQUE,
                    category_id INTEGER,
                    description TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    expense_date DATE NOT NULL,
                    payment_method TEXT DEFAULT 'cash',
                    vendor TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    recurring_id INTEGER,
                    notes TEXT,
                    created_by INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    journal_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES expense_categories(id),
                    FOREIGN KEY (recurring_id) REFERENCES recurring_expenses(id)
                )
            """)
            self.db.execute_non_query("""
                CREATE TABLE IF NOT EXISTS recurring_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category_id INTEGER,
                    description TEXT,
                    amount DECIMAL(15,2) NOT NULL,
                    frequency TEXT NOT NULL DEFAULT 'monthly',
                    next_due_date DATE NOT NULL,
                    last_generated_date DATE,
                    is_active BOOLEAN DEFAULT 1,
                    auto_approve BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES expense_categories(id)
                )
            """)
            # فهارس
            try:
                self.db.execute_non_query(
                    "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)"
                )
                self.db.execute_non_query(
                    "CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status)"
                )
                self.db.execute_non_query(
                    "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category_id)"
                )
            except Exception:
                pass

            self._seed_default_categories()
            self.logger.info("تم تهيئة جداول المصاريف بنجاح")
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة جداول المصاريف: {e}")

    def _seed_default_categories(self) -> None:
        """تصنيفات افتراضية للمصاريف التشغيلية"""
        defaults = [
            ("إيجار", "إيجار المحل أو المستودع", "5010"),
            ("رواتب وأجور", "رواتب الموظفين والأجور", "5020"),
            ("كهرباء وماء", "فواتير الخدمات", "5030"),
            ("نقل ومواصلات", "مصاريف النقل والتوصيل", "5040"),
            ("صيانة", "صيانة المعدات والمعدات", "5050"),
            ("تسويق وإعلان", "مصاريف التسويق والإعلانات", "5060"),
            ("مصاريف عامة", "مصاريف تشغيلية متنوعة", "5000"),
        ]
        try:
            for name, desc, code in defaults:
                existing = self.db.fetch_one(
                    "SELECT id FROM expense_categories WHERE name = ?", (name,)
                )
                if not existing:
                    self.db.execute_insert(
                        """
                        INSERT INTO expense_categories (name, description, account_code)
                        VALUES (?, ?, ?)
                        """,
                        (name, desc, code),
                    )
        except Exception as e:
            self.logger.warning(f"تخطي تهيئة التصنيفات الافتراضية: {e}")

    # ────────────────────────── الحسابات المحاسبية ──────────────────────────

    def _get_or_create_account(self, account_code: str, account_name: str,
                               account_type: str, normal_side: str = "DEBIT"):
        """جلب حساب من دليل الحسابات أو إنشاؤه إن لم يوجد"""
        try:
            from src.services.accounting_service import AccountingService
            from src.models.account import Account

            accounting = AccountingService(self.db, self.logger)
            account = accounting.get_account_by_code(account_code)
            if account:
                return account
            accounting.create_account(Account(
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                normal_side=normal_side,
                description=f"حساب تلقائي من خدمة المصاريف",
            ))
            return accounting.get_account_by_code(account_code)
        except Exception as e:
            self.logger.warning(f"تعذر تجهيز الحساب {account_code}: {e}")
            return None

    @staticmethod
    def _to_datetime(value) -> datetime:
        """تحويل قيمة تاريخ (date/str/datetime) إلى datetime للقيد المحاسبي"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now()

    def _create_expense_journal_entry(self, expense_id: int, description: str,
                                      amount: Decimal, account_code: str,
                                      payment_method: str, expense_date) -> Optional[int]:
        """قيد المصروف: مدين حساب المصروف / دائن الصندوق أو البنك"""
        try:
            from src.services.accounting_service import AccountingService
            from src.models.journal_entry import JournalEntry, JournalLine

            amount = Decimal(str(amount or 0))
            if amount <= 0:
                return None

            expense_account = self._get_or_create_account(
                account_code, f"مصروف - {description[:30]}", "Expense", "DEBIT"
            )
            # الصندوق (نقداً) أو البنك (تحويل)
            if str(payment_method) in ("bank", "bank_transfer", "cheque", "تحويل بنكي", "شيك"):
                cash_account = self._get_or_create_account("1020", "البنك", "Asset", "DEBIT")
            else:
                cash_account = self._get_or_create_account("1000", "الصندوق", "Asset", "DEBIT")

            if not (expense_account and cash_account):
                self.logger.warning(
                    "حسابات المصروف/الصندوق غير متوفرة — قيد المصروف %d مؤجل", expense_id
                )
                return None

            entry = JournalEntry(
                entry_date=self._to_datetime(expense_date),
                description=f"مصروف: {description}",
                reference_type="expense",
                reference_id=expense_id,
                created_by="expense_service",
            )
            entry.add_line(JournalLine(
                account_id=expense_account.id,
                account_code=expense_account.account_code,
                account_name=expense_account.account_name,
                debit_amount=amount,
            ))
            entry.add_line(JournalLine(
                account_id=cash_account.id,
                account_code=cash_account.account_code,
                account_name=cash_account.account_name,
                credit_amount=amount,
            ))
            if not entry.is_balanced():
                self.logger.warning("قيد المصروف %d غير متوازن — تم الإلغاء", expense_id)
                return None
            return AccountingService(self.db, self.logger).create_journal_entry(entry)
        except Exception as e:
            self.logger.warning(f"فشل قيد المصروف {expense_id}: {e}")
            return None

    # ────────────────────────── التصنيفات ──────────────────────────

    def create_category(self, name: str, description: str = "",
                        account_code: str = "5000") -> Optional[int]:
        """إنشاء تصنيف مصاريف"""
        try:
            existing = self.db.fetch_one(
                "SELECT id FROM expense_categories WHERE name = ?", (name,)
            )
            if existing:
                self.logger.warning(f"التصنيف '{name}' موجود مسبقاً")
                row = dict(existing) if not isinstance(existing, int) else {"id": existing}
                return row.get("id")
            return self.db.execute_insert(
                """
                INSERT INTO expense_categories (name, description, account_code)
                VALUES (?, ?, ?)
                """,
                (name, description, account_code),
            )
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء التصنيف: {e}")
            return None

    def get_categories(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """جلب تصنيفات المصاريف"""
        try:
            query = "SELECT * FROM expense_categories"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY name"
            rows = self.db.fetch_all(query)
            return [dict(r) for r in rows] if rows else []
        except Exception as e:
            self.logger.error(f"خطأ في جلب التصنيفات: {e}")
            return []

    # ────────────────────────── المصاريف ──────────────────────────

    def _generate_expense_number(self) -> str:
        """توليد رقم مصروف فريد EXP-YYYYMMDD-XXXX"""
        try:
            today = date.today().isoformat().replace("-", "")
            prefix = f"EXP-{today}-"
            row = self.db.fetch_one(
                "SELECT expense_number FROM expenses WHERE expense_number LIKE ? "
                "ORDER BY id DESC LIMIT 1",
                (f"{prefix}%",),
            )
            seq = 1
            if row:
                try:
                    seq = int(str(row.get("expense_number")).split("-")[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            return f"{prefix}{seq:04d}"
        except Exception:
            return f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def create_expense(
        self,
        description: str,
        amount: Decimal,
        expense_date: Optional[date] = None,
        category_id: Optional[int] = None,
        payment_method: str = "cash",
        vendor: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[int] = None,
        recurring_id: Optional[int] = None,
    ) -> Optional[int]:
        """إنشاء مصروف جديد (حالة أولية: معلق بانتظار الموافقة)"""
        try:
            amount = Decimal(str(amount or 0))
            if amount <= 0:
                self.logger.warning("تم رفض المصروف: المبلغ غير صحيح")
                return None
            if not description or not str(description).strip():
                self.logger.warning("تم رفض المصروف: الوصف مطلوب")
                return None

            expense_date = expense_date or date.today()
            expense_number = self._generate_expense_number()

            expense_id = self.db.execute_insert(
                """
                INSERT INTO expenses (
                    expense_number, category_id, description, amount, expense_date,
                    payment_method, vendor, status, recurring_id, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    expense_number, category_id, str(description).strip(), float(amount),
                    expense_date.isoformat(), payment_method, vendor,
                    recurring_id, notes, created_by,
                ),
            )
            self.logger.info(f"تم إنشاء المصروف {expense_number} بمبلغ {amount}")
            return expense_id
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء المصروف: {e}")
            return None

    def approve_expense(self, expense_id: int, approved_by: Optional[int] = None) -> bool:
        """الموافقة على مصروف + إنشاء قيد محاسبي تلقائي (مدين مصروف / دائن صندوق)"""
        try:
            row = self.db.fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            if not row:
                self.logger.warning(f"المصروف {expense_id} غير موجود")
                return False
            expense = dict(row)
            if expense.get("status") == ExpenseStatus.APPROVED:
                self.logger.warning(f"المصروف {expense_id} موافق عليه مسبقاً")
                return False
            if expense.get("status") == ExpenseStatus.REJECTED:
                self.logger.warning(f"المصروف {expense_id} مرفوض — لا يمكن الموافقة")
                return False

            # حساب المصروف من التصنيف
            account_code = "5000"
            if expense.get("category_id"):
                cat = self.db.fetch_one(
                    "SELECT account_code FROM expense_categories WHERE id = ?",
                    (expense["category_id"],),
                )
                if cat and cat.get("account_code"):
                    account_code = str(cat["account_code"])

            journal_id = self._create_expense_journal_entry(
                expense_id=expense_id,
                description=str(expense.get("description", "")),
                amount=Decimal(str(expense.get("amount", 0))),
                account_code=account_code,
                payment_method=str(expense.get("payment_method", "cash")),
                expense_date=expense.get("expense_date"),
            )

            self.db.execute_non_query(
                """
                UPDATE expenses
                SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP,
                    journal_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (approved_by, journal_id, expense_id),
            )
            self.logger.info(
                f"تمت الموافقة على المصروف {expense_id} — القيد: {journal_id}"
            )
            return True
        except Exception as e:
            self.logger.error(f"خطأ في الموافقة على المصروف {expense_id}: {e}")
            return False

    def reject_expense(self, expense_id: int, approved_by: Optional[int] = None) -> bool:
        """رفض مصروف معلق"""
        try:
            row = self.db.fetch_one(
                "SELECT status FROM expenses WHERE id = ?", (expense_id,)
            )
            if not row or row.get("status") != ExpenseStatus.PENDING:
                self.logger.warning(f"المصروف {expense_id} ليس معلقاً — لا يمكن الرفض")
                return False
            self.db.execute_non_query(
                "UPDATE expenses SET status = 'rejected', approved_by = ?, "
                "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (approved_by, expense_id),
            )
            return True
        except Exception as e:
            self.logger.error(f"خطأ في رفض المصروف {expense_id}: {e}")
            return False

    def delete_expense(self, expense_id: int) -> bool:
        """حذف مصروف معلق فقط (الموافق عليه محاسبياً — لا يُحذف)"""
        try:
            row = self.db.fetch_one(
                "SELECT status FROM expenses WHERE id = ?", (expense_id,)
            )
            if not row:
                return False
            if row.get("status") == ExpenseStatus.APPROVED:
                self.logger.warning(
                    f"المصروف {expense_id} موافق عليه — الحذف ممنوع (قيد محاسبي)"
                )
                return False
            self.db.execute_non_query("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return True
        except Exception as e:
            self.logger.error(f"خطأ في حذف المصروف {expense_id}: {e}")
            return False

    def get_expense(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """جلب مصروف واحد مع التصنيف"""
        try:
            row = self.db.fetch_one(
                """
                SELECT e.*, c.name AS category_name, c.account_code
                FROM expenses e
                LEFT JOIN expense_categories c ON c.id = e.category_id
                WHERE e.id = ?
                """,
                (expense_id,),
            )
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"خطأ في جلب المصروف {expense_id}: {e}")
            return None

    def get_expenses(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """جلب المصاريف بفلاتر (تاريخ/تصنيف/حالة)"""
        try:
            query = """
                SELECT e.*, c.name AS category_name
                FROM expenses e
                LEFT JOIN expense_categories c ON c.id = e.category_id
                WHERE 1=1
            """
            params: List[Any] = []
            if start_date:
                query += " AND e.expense_date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                query += " AND e.expense_date <= ?"
                params.append(end_date.isoformat())
            if category_id:
                query += " AND e.category_id = ?"
                params.append(category_id)
            if status:
                query += " AND e.status = ?"
                params.append(status)
            query += " ORDER BY e.expense_date DESC, e.id DESC LIMIT ?"
            params.append(int(limit))
            rows = self.db.fetch_all(query, tuple(params))
            return [dict(r) for r in rows] if rows else []
        except Exception as e:
            self.logger.error(f"خطأ في جلب المصاريف: {e}")
            return []

    def get_expense_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """إحصاءات المصاريف: الإجمالي، حسب التصنيف، حسب الشهر"""
        try:
            where = "WHERE e.status = 'approved'"
            params: List[Any] = []
            if start_date:
                where += " AND e.expense_date >= ?"
                params.append(start_date.isoformat())
            if end_date:
                where += " AND e.expense_date <= ?"
                params.append(end_date.isoformat())

            total_row = self.db.fetch_one(
                f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
                f"FROM expenses e {where}",
                tuple(params),
            )

            by_category = self.db.fetch_all(
                f"""
                SELECT COALESCE(c.name, 'غير مصنف') AS category,
                       COALESCE(SUM(e.amount), 0) AS total
                FROM expenses e
                LEFT JOIN expense_categories c ON c.id = e.category_id
                {where}
                GROUP BY c.name ORDER BY total DESC
                """,
                tuple(params),
            )

            by_month = self.db.fetch_all(
                f"""
                SELECT strftime('%Y-%m', e.expense_date) AS month,
                       COALESCE(SUM(e.amount), 0) AS total
                FROM expenses e
                {where}
                GROUP BY month ORDER BY month DESC LIMIT 12
                """,
                tuple(params),
            )

            return {
                "total": float((total_row or {}).get("total", 0) or 0),
                "count": int((total_row or {}).get("cnt", 0) or 0),
                "by_category": [dict(r) for r in (by_category or [])],
                "by_month": [dict(r) for r in (by_month or [])],
            }
        except Exception as e:
            self.logger.error(f"خطأ في إحصاءات المصاريف: {e}")
            return {"total": 0, "count": 0, "by_category": [], "by_month": []}

    # ────────────────────────── المصاريف المتكررة ──────────────────────────

    def create_recurring(
        self,
        name: str,
        amount: Decimal,
        frequency: str = "monthly",
        next_due_date: Optional[date] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        auto_approve: bool = False,
    ) -> Optional[int]:
        """إنشاء مصروف متكرر (يومي/أسبوعي/شهري/سنوي)"""
        try:
            amount = Decimal(str(amount or 0))
            if amount <= 0:
                self.logger.warning("تم رفض المصروف المتكرر: المبلغ غير صحيح")
                return None
            if frequency not in ("daily", "weekly", "monthly", "yearly"):
                self.logger.warning(f"تكرار غير صحيح: {frequency}")
                return None

            next_due_date = next_due_date or date.today()
            return self.db.execute_insert(
                """
                INSERT INTO recurring_expenses (
                    name, category_id, description, amount, frequency,
                    next_due_date, auto_approve
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name, category_id, description, float(amount), frequency,
                    next_due_date.isoformat(), int(auto_approve),
                ),
            )
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء المصروف المتكرر: {e}")
            return None

    def get_recurring(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """جلب المصاريف المتكررة"""
        try:
            query = "SELECT * FROM recurring_expenses"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY next_due_date"
            rows = self.db.fetch_all(query)
            return [dict(r) for r in rows] if rows else []
        except Exception as e:
            self.logger.error(f"خطأ في جلب المصاريف المتكررة: {e}")
            return []

    def _advance_due_date(self, due: date, frequency: str) -> date:
        """تقديم تاريخ الاستحقاق حسب التكرار"""
        if frequency == "daily":
            return due + timedelta(days=1)
        if frequency == "weekly":
            return due + timedelta(weeks=1)
        if frequency == "yearly":
            try:
                return due.replace(year=due.year + 1)
            except ValueError:  # 29 Feb
                return due.replace(year=due.year + 1, day=28)
        # monthly
        month = due.month + 1
        year = due.year
        if month > 12:
            month = 1
            year += 1
        try:
            return due.replace(year=year, month=month)
        except ValueError:  # 31 → 30
            return due.replace(year=year, month=month, day=28)

    def generate_due_expenses(self, as_of: Optional[date] = None) -> List[Dict[str, Any]]:
        """توليد المصاريف المستحقة من القوالب المتكررة (حتى تاريخ معين).

        لكل قالب نشط استحقاقه <= as_of:
        - إنشاء مصروف بحالة معلقة (أو موافق عليه إذا auto_approve مع قيد)
        - تقديم next_due_date للدورة التالية
        - يدعم حلقات متعددة إذا تأخر التوليد (catch-up)
        """
        generated: List[Dict[str, Any]] = []
        as_of = as_of or date.today()
        try:
            templates = self.db.fetch_all(
                "SELECT * FROM recurring_expenses WHERE is_active = 1 AND next_due_date <= ?",
                (as_of.isoformat(),),
            )
            for tpl in templates or []:
                t = dict(tpl)
                due = date.fromisoformat(str(t["next_due_date"]))
                frequency = str(t["frequency"])
                iterations = 0
                while due <= as_of and iterations < 24:  # حد أمان
                    expense_id = self.create_expense(
                        description=str(t.get("description") or t.get("name", "")),
                        amount=Decimal(str(t.get("amount", 0))),
                        expense_date=due,
                        category_id=t.get("category_id"),
                        payment_method="cash",
                        notes=f"متكرر: {t.get('name')} ({frequency})",
                        recurring_id=t.get("id"),
                    )
                    if expense_id and t.get("auto_approve"):
                        self.approve_expense(expense_id)
                    generated.append({
                        "recurring_id": t.get("id"),
                        "expense_id": expense_id,
                        "due_date": due.isoformat(),
                    })
                    due = self._advance_due_date(due, frequency)
                    iterations += 1

                if iterations > 0:
                    self.db.execute_non_query(
                        "UPDATE recurring_expenses SET next_due_date = ?, "
                        "last_generated_date = ? WHERE id = ?",
                        (due.isoformat(), as_of.isoformat(), t["id"]),
                    )
            if generated:
                self.logger.info(f"تم توليد {len(generated)} مصروف من القوالب المتكررة")
        except Exception as e:
            self.logger.error(f"خطأ في توليد المصاريف المتكررة: {e}")
        return generated
