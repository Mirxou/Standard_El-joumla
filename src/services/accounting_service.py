#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة المحاسبة
Accounting Service

توفر خدمات المحاسبة مثل إنشاء القيود وتحديث الأرصدة والقوائم المالية
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import logging

from ..models.account import Account, ChartOfAccounts
from ..models.journal_entry import JournalEntry, JournalLine


class AccountingService:
    """خدمة إدارة المحاسبة"""
    
    def __init__(self, db_manager):
        """
        تهيئة خدمة المحاسبة
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        self.coa = ChartOfAccounts()  # دليل الحسابات
        self._initialize_chart_of_accounts()
    
    def _initialize_chart_of_accounts(self) -> None:
        """تهيئة دليل الحسابات من قاعدة البيانات"""
        try:
            accounts = self.db.fetch_all("""
                SELECT id, account_code, account_name, account_type, sub_type,
                       description, normal_side, is_header, parent_account_id,
                       is_active, is_locked, opening_balance, current_balance,
                       created_at, updated_at
                FROM chart_of_accounts
                ORDER BY account_code
            """)
            
            for row in accounts:
                account = Account(
                    id=row[0],
                    account_code=row[1],
                    account_name=row[2],
                    account_type=row[3],
                    sub_type=row[4],
                    description=row[5],
                    normal_side=row[6],
                    is_header=row[7],
                    parent_account_id=row[8],
                    is_active=row[9],
                    is_locked=row[10],
                    opening_balance=Decimal(str(row[11])) if row[11] else Decimal("0"),
                    current_balance=Decimal(str(row[12])) if row[12] else Decimal("0"),
                    created_at=datetime.fromisoformat(row[13]) if row[13] else None,
                    updated_at=datetime.fromisoformat(row[14]) if row[14] else None
                )
                self.coa.add_account(account)
                self.logger.info(f"تم تحميل الحساب: {account.account_code} - {account.account_name}")
        
        except Exception as e:
            self.logger.error(f"خطأ في تحميل دليل الحسابات: {e}")
            self._create_default_chart_of_accounts()
    
    def _create_default_chart_of_accounts(self) -> None:
        """إنشاء دليل حسابات افتراضي"""
        default_accounts = [
            # رؤوس الحسابات (Headers)
            Account(account_code="1000", account_name="الأصول الحالية", account_type="Asset", 
                   sub_type="Current Asset", normal_side="DEBIT", is_header=True, is_active=True),
            Account(account_code="1500", account_name="الأصول الثابتة", account_type="Asset",
                   sub_type="Fixed Asset", normal_side="DEBIT", is_header=True, is_active=True),
            Account(account_code="2000", account_name="الالتزامات الحالية", account_type="Liability",
                   sub_type="Current Liability", normal_side="CREDIT", is_header=True, is_active=True),
            Account(account_code="3000", account_name="حقوق الملكية", account_type="Equity",
                   normal_side="CREDIT", is_header=True, is_active=True),
            Account(account_code="4000", account_name="الإيرادات", account_type="Revenue",
                   normal_side="CREDIT", is_header=True, is_active=True),
            Account(account_code="5000", account_name="المصروفات", account_type="Expense",
                   normal_side="DEBIT", is_header=True, is_active=True),
            
            # الأصول الحالية
            Account(account_code="1001", account_name="النقد بالصندوق", account_type="Asset",
                   sub_type="Current Asset", normal_side="DEBIT", parent_account_id=1001),
            Account(account_code="1002", account_name="النقد بالبنك", account_type="Asset",
                   sub_type="Current Asset", normal_side="DEBIT", parent_account_id=1001),
            Account(account_code="1010", account_name="حسابات العملاء", account_type="Asset",
                   sub_type="Current Asset", normal_side="DEBIT", parent_account_id=1001),
            Account(account_code="1020", account_name="المخزون", account_type="Asset",
                   sub_type="Current Asset", normal_side="DEBIT", parent_account_id=1001),
            
            # الالتزامات الحالية
            Account(account_code="2001", account_name="حسابات الموردين", account_type="Liability",
                   sub_type="Current Liability", normal_side="CREDIT", parent_account_id=2001),
            Account(account_code="2010", account_name="الضرائب المستحقة", account_type="Liability",
                   sub_type="Current Liability", normal_side="CREDIT", parent_account_id=2001),
            
            # حقوق الملكية
            Account(account_code="3001", account_name="رأس المال", account_type="Equity",
                   normal_side="CREDIT", parent_account_id=3001),
            Account(account_code="3010", account_name="الأرباح المحتفظ بها", account_type="Equity",
                   normal_side="CREDIT", parent_account_id=3001),
            
            # الإيرادات
            Account(account_code="4001", account_name="إيرادات المبيعات", account_type="Revenue",
                   normal_side="CREDIT", parent_account_id=4001),
            Account(account_code="4010", account_name="عمولات", account_type="Revenue",
                   normal_side="CREDIT", parent_account_id=4001),
            
            # المصروفات
            Account(account_code="5001", account_name="تكلفة البضاعة المباعة", account_type="Expense",
                   normal_side="DEBIT", parent_account_id=5001),
            Account(account_code="5010", account_name="رواتب الموظفين", account_type="Expense",
                   normal_side="DEBIT", parent_account_id=5001),
            Account(account_code="5020", account_name="مصروفات الإيجار", account_type="Expense",
                   normal_side="DEBIT", parent_account_id=5001),
            Account(account_code="5030", account_name="مصروفات النقل", account_type="Expense",
                   normal_side="DEBIT", parent_account_id=5001),
        ]
        
        for account in default_accounts:
            self.create_account(account)
    
    def create_account(self, account: Account) -> int:
        """إنشاء حساب جديد"""
        try:
            cursor = self.db.execute("""
                INSERT INTO chart_of_accounts (
                    account_code, account_name, account_type, sub_type, description,
                    normal_side, is_header, parent_account_id, is_active, is_locked,
                    opening_balance, current_balance, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                datetime.now().isoformat()
            ))
            
            account_id = cursor.lastrowid
            account.id = account_id
            self.coa.add_account(account)
            
            self.logger.info(f"تم إنشاء حساب جديد: {account.account_code} - {account.account_name}")
            return account_id
        
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الحساب: {e}")
            return 0
    
    def get_account(self, account_id: int) -> Optional[Account]:
        """احصل على حساب"""
        return self.coa.get_account_by_id(account_id)
    
    def get_account_by_code(self, code: str) -> Optional[Account]:
        """احصل على حساب بالرمز"""
        return self.coa.get_account_by_code(code)
    
    def create_journal_entry(self, entry: JournalEntry) -> int:
        """إنشاء قيد يومي جديد"""
        if not entry.is_balanced():
            raise ValueError("القيد غير متوازن")
        
        try:
            # توليد رقم القيد
            entry_number = self._generate_entry_number(entry.reference_type)
            
            cursor = self.db.execute("""
                INSERT INTO general_journal (
                    entry_number, entry_date, reference_type, reference_id,
                    description, notes, is_posted, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_number,
                entry.entry_date.isoformat(),
                entry.reference_type,
                entry.reference_id,
                entry.description,
                entry.notes,
                entry.is_posted,
                datetime.now().isoformat(),
                entry.created_by or "system"
            ))
            
            journal_id = cursor.lastrowid
            entry.id = journal_id
            
            # إدراج أسطر القيد
            for line in entry.lines:
                self._insert_journal_line(journal_id, line)
            
            self.logger.info(f"تم إنشاء قيد يومي: {entry_number}")
            return journal_id
        
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء القيد: {e}")
            return 0
    
    def _insert_journal_line(self, journal_id: int, line: JournalLine) -> int:
        """إدراج سطر من القيد"""
        cursor = self.db.execute("""
            INSERT INTO journal_lines (
                journal_id, account_id, account_code, account_name,
                debit_amount, credit_amount, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            journal_id,
            line.account_id,
            line.account_code,
            line.account_name,
            float(line.debit_amount),
            float(line.credit_amount),
            line.description,
            datetime.now().isoformat()
        ))
        
        return cursor.lastrowid
    
    def _generate_entry_number(self, reference_type: str) -> str:
        """توليد رقم القيد"""
        try:
            result = self.db.fetch_one("""
                SELECT COUNT(*) FROM general_journal WHERE reference_type = ?
            """, (reference_type,))
            
            count = result[0] + 1 if result else 1
            date = datetime.now()
            return f"JE-{reference_type[:3].upper()}-{count:04d}-{date.strftime('%Y%m')}"
        
        except:
            return f"JE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def post_journal_entry(self, journal_id: int, posted_by: str) -> bool:
        """ترحيل قيد يومي"""
        try:
            entry = self.get_journal_entry(journal_id)
            if not entry:
                return False
            
            if not entry.can_post():
                raise ValueError("لا يمكن ترحيل هذا القيد")
            
            # تحديث حالة القيد
            self.db.execute("""
                UPDATE general_journal 
                SET is_posted = 1, posted_date = ?, posted_by = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), posted_by, journal_id))
            
            # تحديث أرصدة الحسابات
            self._update_account_balances(journal_id)
            
            self.logger.info(f"تم ترحيل القيد رقم {journal_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"خطأ في ترحيل القيد: {e}")
            return False
    
    def _update_account_balances(self, journal_id: int) -> None:
        """تحديث أرصدة الحسابات من قيد"""
        try:
            lines = self.db.fetch_all("""
                SELECT account_id, debit_amount, credit_amount
                FROM journal_lines
                WHERE journal_id = ?
            """, (journal_id,))
            
            for line in lines:
                account_id, debit, credit = line
                
                # حساب الفرق
                difference = (Decimal(str(debit)) if debit else Decimal("0")) - \
                           (Decimal(str(credit)) if credit else Decimal("0"))
                
                # تحديث الرصيد
                self.db.execute("""
                    UPDATE chart_of_accounts
                    SET current_balance = current_balance + ?
                    WHERE id = ?
                """, (float(difference), account_id))
        
        except Exception as e:
            self.logger.error(f"خطأ في تحديث أرصدة الحسابات: {e}")
    
    def get_journal_entry(self, journal_id: int) -> Optional[JournalEntry]:
        """احصل على قيد يومي"""
        try:
            entry_row = self.db.fetch_one("""
                SELECT id, entry_number, entry_date, reference_type, reference_id,
                       description, notes, is_posted, posted_date, posted_by,
                       created_at, created_by
                FROM general_journal
                WHERE id = ?
            """, (journal_id,))
            
            if not entry_row:
                return None
            
            entry = JournalEntry(
                id=entry_row[0],
                entry_number=entry_row[1],
                entry_date=datetime.fromisoformat(entry_row[2]) if entry_row[2] else None,
                reference_type=entry_row[3],
                reference_id=entry_row[4],
                description=entry_row[5],
                notes=entry_row[6],
                is_posted=entry_row[7],
                posted_date=datetime.fromisoformat(entry_row[8]) if entry_row[8] else None,
                posted_by=entry_row[9],
                created_at=datetime.fromisoformat(entry_row[10]) if entry_row[10] else None,
                created_by=entry_row[11]
            )
            
            # تحميل الأسطر
            lines = self.db.fetch_all("""
                SELECT id, account_id, account_code, account_name,
                       debit_amount, credit_amount, description, created_at
                FROM journal_lines
                WHERE journal_id = ?
            """, (journal_id,))
            
            for line in lines:
                entry.add_line(JournalLine(
                    id=line[0],
                    account_id=line[1],
                    account_code=line[2],
                    account_name=line[3],
                    debit_amount=Decimal(str(line[4])) if line[4] else Decimal("0"),
                    credit_amount=Decimal(str(line[5])) if line[5] else Decimal("0"),
                    description=line[6],
                    created_at=datetime.fromisoformat(line[7]) if line[7] else None
                ))
            
            return entry
        
        except Exception as e:
            self.logger.error(f"خطأ في جلب القيد: {e}")
            return None
    
    def get_account_balance(self, account_id: int) -> Decimal:
        """احصل على رصيد الحساب"""
        try:
            account = self.get_account(account_id)
            return account.current_balance if account else Decimal("0")
        except:
            return Decimal("0")
    
    def get_trial_balance(self) -> Dict[str, any]:
        """احصل على ميزان المراجعة"""
        try:
            accounts = self.coa.get_active_accounts()
            
            total_debits = Decimal("0")
            total_credits = Decimal("0")
            
            trial_balance = []
            
            for account in accounts:
                balance = self.get_account_balance(account.id)
                
                if account.is_debit_account():
                    debit = balance if balance > 0 else Decimal("0")
                    credit = -balance if balance < 0 else Decimal("0")
                else:
                    debit = -balance if balance < 0 else Decimal("0")
                    credit = balance if balance > 0 else Decimal("0")
                
                total_debits += debit
                total_credits += credit
                
                trial_balance.append({
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "debit": float(debit),
                    "credit": float(credit)
                })
            
            return {
                "date": datetime.now().isoformat(),
                "accounts": trial_balance,
                "total_debits": float(total_debits),
                "total_credits": float(total_credits),
                "is_balanced": abs(total_debits - total_credits) < Decimal("0.01")
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في حساب ميزان المراجعة: {e}")
            return {"error": str(e)}
    
    def get_financial_position(self) -> Dict[str, any]:
        """احصل على الحالة المالية (الميزانية العمومية)"""
        try:
            assets = self._get_account_group_balance("Asset")
            liabilities = self._get_account_group_balance("Liability")
            equity = self._get_account_group_balance("Equity")
            
            return {
                "date": datetime.now().isoformat(),
                "assets": float(assets),
                "liabilities": float(liabilities),
                "equity": float(equity),
                "total_liabilities_and_equity": float(liabilities + equity),
                "is_balanced": abs(assets - (liabilities + equity)) < Decimal("0.01")
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في حساب الحالة المالية: {e}")
            return {"error": str(e)}
    
    def _get_account_group_balance(self, account_type: str) -> Decimal:
        """احصل على رصيد مجموعة حسابات"""
        accounts = self.coa.get_accounts_by_type(account_type)
        total = Decimal("0")
        
        for account in accounts:
            total += self.get_account_balance(account.id)
        
        return total
    
    def get_income_statement(self, start_date: datetime, end_date: datetime) -> Dict[str, any]:
        """احصل على قائمة الدخل لفترة معينة"""
        try:
            # الإيرادات
            revenues = self._get_account_group_period_total("Revenue", start_date, end_date)
            
            # المصروفات
            expenses = self._get_account_group_period_total("Expense", start_date, end_date)
            
            net_income = revenues - expenses
            
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_revenues": float(revenues),
                "total_expenses": float(expenses),
                "net_income": float(net_income)
            }
        
        except Exception as e:
            self.logger.error(f"خطأ في حساب قائمة الدخل: {e}")
            return {"error": str(e)}
    
    def _get_account_group_period_total(self, account_type: str, start_date: datetime, end_date: datetime) -> Decimal:
        """احصل على إجمالي مجموعة حسابات خلال فترة معينة"""
        try:
            result = self.db.fetch_one("""
                SELECT COALESCE(SUM(jl.debit_amount + jl.credit_amount), 0)
                FROM journal_lines jl
                JOIN general_journal gj ON jl.journal_id = gj.id
                JOIN chart_of_accounts coa ON jl.account_id = coa.id
                WHERE coa.account_type = ? 
                  AND gj.is_posted = 1
                  AND gj.entry_date BETWEEN ? AND ?
            """, (account_type, start_date.isoformat(), end_date.isoformat()))
            
            return Decimal(str(result[0])) if result and result[0] else Decimal("0")
        
        except Exception as e:
            self.logger.error(f"خطأ في حساب إجمالي المجموعة: {e}")
            return Decimal("0")
