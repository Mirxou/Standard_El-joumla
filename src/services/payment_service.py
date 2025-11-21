"""
خدمة إدارة المدفوعات والذمم المدينة والدائنة
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from ..models.payment import (
    Payment, PaymentManager, PaymentType, PaymentMethod, PaymentStatus,
    AccountType, AccountBalance, PaymentSchedule
)
from ..models.customer import CustomerManager
from ..models.supplier import SupplierManager
from ..models.sale import SaleManager
from ..models.purchase import PurchaseManager


class PaymentService:
    """خدمة إدارة المدفوعات"""
    
    def __init__(self, db_manager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)
        
        # إنشاء مديري النماذج
        self.payment_manager = PaymentManager(db_manager, logger)
        self.customer_manager = CustomerManager(db_manager, logger)
        self.supplier_manager = SupplierManager(db_manager, logger)
        
        # إنشاء الجداول إذا لم تكن موجودة
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول المدفوعات"""
        try:
            # جدول المدفوعات الرئيسي
            payments_table = """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_number TEXT UNIQUE NOT NULL,
                payment_type TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'معلق',
                
                amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                currency TEXT NOT NULL DEFAULT 'DZD',
                exchange_rate DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
                amount_in_base_currency DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                
                payment_date DATE NOT NULL,
                due_date DATE,
                
                customer_id INTEGER,
                supplier_id INTEGER,
                user_id INTEGER,
                sale_id INTEGER,
                purchase_id INTEGER,
                
                reference_number TEXT,
                bank_name TEXT,
                account_number TEXT,
                notes TEXT,
                account_code TEXT,
                cost_center TEXT,
                
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (purchase_id) REFERENCES purchases(id)
            )
            """
            
            # جدول جدولة المدفوعات (الأقساط)
            payment_schedules_table = """
            CREATE TABLE IF NOT EXISTS payment_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                installment_number INTEGER NOT NULL,
                due_date DATE NOT NULL,
                amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                paid_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                remaining_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                status TEXT NOT NULL DEFAULT 'معلق',
                notes TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
            """
            
            # جدول مرفقات المدفوعات
            payment_attachments_table = """
            CREATE TABLE IF NOT EXISTS payment_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                uploaded_at DATETIME NOT NULL,
                
                FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE
            )
            """
            
            # تنفيذ إنشاء الجداول
            self.db_manager.execute_query(payments_table)
            self.db_manager.execute_query(payment_schedules_table)
            self.db_manager.execute_query(payment_attachments_table)
            
            # إنشاء الفهارس
            self._create_indexes()
            
            if self.logger:
                self.logger.info("تم إنشاء جداول المدفوعات بنجاح")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء جداول المدفوعات: {str(e)}")
    
    def _create_indexes(self):
        """إنشاء الفهارس"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_payments_entity ON payments(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
                "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
                "CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(payment_type)",
                "CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method)",
                "CREATE INDEX IF NOT EXISTS idx_account_balances_entity ON account_balances(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_account_balances_type ON account_balances(account_type)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_entity ON payment_schedules(entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_due_date ON payment_schedules(due_date)",
                "CREATE INDEX IF NOT EXISTS idx_payment_schedules_status ON payment_schedules(status)"
            ]
            
            for index in indexes:
                self.db_manager.execute_query(index)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء فهارس المدفوعات: {str(e)}")
    
    # ===== إدارة المدفوعات =====
    
    def create_customer_payment(self, customer_id: int, amount: Decimal, 
                              payment_method: str = PaymentMethod.CASH.value,
                              payment_date: date = None, reference_number: str = None,
                              notes: str = None, user_id: int = None) -> Optional[Payment]:
        """إنشاء دفعة من العميل"""
        try:
            payment = Payment(
                payment_type=PaymentType.CUSTOMER_PAYMENT.value,
                payment_method=payment_method,
                amount=amount,
                payment_date=payment_date or date.today(),
                customer_id=customer_id,
                user_id=user_id,
                reference_number=reference_number,
                notes=notes,
                status=PaymentStatus.COMPLETED.value
            )
            
            payment_id = self.payment_manager.create_payment(payment)
            if payment_id:
                return self.payment_manager.get_payment_by_id(payment_id)
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء دفعة العميل: {str(e)}")
            return None
    
    def create_supplier_payment(self, supplier_id: int, amount: Decimal,
                              payment_method: str = PaymentMethod.CASH.value,
                              payment_date: date = None, reference_number: str = None,
                              notes: str = None, user_id: int = None) -> Optional[Payment]:
        """إنشاء دفعة للمورد"""
        try:
            payment = Payment(
                payment_type=PaymentType.SUPPLIER_PAYMENT.value,
                payment_method=payment_method,
                amount=amount,
                payment_date=payment_date or date.today(),
                supplier_id=supplier_id,
                user_id=user_id,
                reference_number=reference_number,
                notes=notes,
                status=PaymentStatus.COMPLETED.value
            )
            
            payment_id = self.payment_manager.create_payment(payment)
            if payment_id:
                return self.payment_manager.get_payment_by_id(payment_id)
            
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء دفعة المورد: {str(e)}")
            return None
    
    def get_payments_by_date_range(self, start_date: date, end_date: date,
                                 payment_type: str = None) -> List[Payment]:
        """الحصول على المدفوعات في فترة زمنية"""
        try:
            query = """
            SELECT * FROM payments 
            WHERE payment_date BETWEEN ? AND ?
            """
            params = [start_date.isoformat(), end_date.isoformat()]
            
            if payment_type:
                query += " AND payment_type = ?"
                params.append(payment_type)
            
            query += " ORDER BY payment_date DESC, created_at DESC"
            
            results = self.db_manager.fetch_all(query, params)
            return [self.payment_manager._row_to_payment(row) for row in results]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المدفوعات: {str(e)}")
            return []
    
    # ===== إدارة الذمم المدينة =====
    
    def get_accounts_receivable(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم المدينة (العملاء)"""
        try:
            query = """
            SELECT 
                c.id,
                c.name,
                c.phone,
                c.current_balance,
                c.credit_limit,
                (c.credit_limit - c.current_balance) as available_credit,
                (SELECT COUNT(*) FROM payments WHERE entity_id = c.id AND payment_type = 'customer_payment') as payments_count,
            (SELECT MAX(payment_date) FROM payments WHERE entity_id = c.id AND payment_type = 'customer_payment') as last_payment_date,
            (SELECT COUNT(*) FROM payment_schedules 
             WHERE entity_id = c.id AND due_date < ? AND status != ?) as overdue_payments
            FROM customers c
            WHERE c.current_balance > 0 AND c.is_active = 1
            ORDER BY c.current_balance DESC
            """
            
            today = date.today().isoformat()
            results = self.db_manager.fetch_all(query, (today, PaymentStatus.COMPLETED.value))
            
            receivables = []
            for row in results:
                receivables.append({
                    'customer_id': row[0],
                    'customer_name': row[1],
                    'phone': row[2],
                    'balance': Decimal(str(row[3])),
                    'credit_limit': Decimal(str(row[4])),
                    'available_credit': Decimal(str(row[5])),
                    'payments_count': row[6],
                    'last_payment_date': date.fromisoformat(row[7]) if row[7] else None,
                    'overdue_payments': row[8]
                })
            
            return receivables
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم المدينة: {str(e)}")
            return []
    
    def get_accounts_payable(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم الدائنة (الموردين)"""
        try:
            query = """
            SELECT 
                s.id,
                s.name,
                s.phone,
                s.current_balance,
                s.credit_limit,
                (s.credit_limit - s.current_balance) as available_credit,
                (SELECT COUNT(*) FROM payments WHERE entity_id = s.id AND payment_type = 'supplier_payment') as payments_count,
            (SELECT MAX(payment_date) FROM payments WHERE entity_id = s.id AND payment_type = 'supplier_payment') as last_payment_date,
            (SELECT COUNT(*) FROM payment_schedules 
             WHERE entity_id = s.id AND due_date < ? AND status != ?) as overdue_payments
            FROM suppliers s
            WHERE s.current_balance > 0 AND s.is_active = 1
            ORDER BY s.current_balance DESC
            """
            
            today = date.today().isoformat()
            results = self.db_manager.fetch_all(query, (today, PaymentStatus.COMPLETED.value))
            
            payables = []
            for row in results:
                payables.append({
                    'supplier_id': row[0],
                    'supplier_name': row[1],
                    'phone': row[2],
                    'balance': Decimal(str(row[3])),
                    'credit_limit': Decimal(str(row[4])),
                    'available_credit': Decimal(str(row[5])),
                    'payments_count': row[6],
                    'last_payment_date': date.fromisoformat(row[7]) if row[7] else None,
                    'overdue_payments': row[8]
                })
            
            return payables
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم الدائنة: {str(e)}")
            return []
    
    def get_overdue_receivables(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم المدينة المتأخرة"""
        try:
            overdue_payments = self.payment_manager.get_overdue_payments()
            receivables = []
            
            for payment in overdue_payments:
                if payment.customer_id and payment.payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    customer = self.customer_manager.get_customer_by_id(payment.customer_id)
                    if customer:
                        days_overdue = (date.today() - payment.due_date).days
                        receivables.append({
                            'payment_id': payment.id,
                            'customer_id': customer.id,
                            'customer_name': customer.name,
                            'amount': payment.amount,
                            'due_date': payment.due_date,
                            'days_overdue': days_overdue,
                            'payment_method': payment.payment_method,
                            'reference_number': payment.reference_number
                        })
            
            return sorted(receivables, key=lambda x: x['days_overdue'], reverse=True)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم المدينة المتأخرة: {str(e)}")
            return []
    
    def get_overdue_payables(self) -> List[Dict[str, Any]]:
        """الحصول على الذمم الدائنة المتأخرة"""
        try:
            overdue_payments = self.payment_manager.get_overdue_payments()
            payables = []
            
            for payment in overdue_payments:
                if payment.supplier_id and payment.payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    supplier = self.supplier_manager.get_supplier_by_id(payment.supplier_id)
                    if supplier:
                        days_overdue = (date.today() - payment.due_date).days
                        payables.append({
                            'payment_id': payment.id,
                            'supplier_id': supplier.id,
                            'supplier_name': supplier.name,
                            'amount': payment.amount,
                            'due_date': payment.due_date,
                            'days_overdue': days_overdue,
                            'payment_method': payment.payment_method,
                            'reference_number': payment.reference_number
                        })
            
            return sorted(payables, key=lambda x: x['days_overdue'], reverse=True)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على الذمم الدائنة المتأخرة: {str(e)}")
            return []
    
    # ===== التقارير المالية =====
    
    def get_payment_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """ملخص المدفوعات"""
        try:
            query = """
            SELECT 
                payment_type,
                payment_method,
                COUNT(*) as count,
                SUM(amount_in_base_currency) as total_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY payment_type, payment_method
            ORDER BY total_amount DESC
            """
            
            results = self.db_manager.fetch_all(query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentStatus.COMPLETED.value
            ))
            
            summary = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'by_type_and_method': [],
                'totals': {
                    'customer_payments': Decimal('0.00'),
                    'supplier_payments': Decimal('0.00'),
                    'total_payments': Decimal('0.00'),
                    'net_cash_flow': Decimal('0.00')
                }
            }
            
            for row in results:
                payment_type = row[0]
                payment_method = row[1]
                count = row[2]
                amount = Decimal(str(row[3]))
                
                summary['by_type_and_method'].append({
                    'payment_type': payment_type,
                    'payment_method': payment_method,
                    'count': count,
                    'amount': amount
                })
                
                # تجميع الإجماليات
                if payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    summary['totals']['customer_payments'] += amount
                elif payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    summary['totals']['supplier_payments'] += amount
                
                summary['totals']['total_payments'] += amount
            
            # حساب صافي التدفق النقدي
            summary['totals']['net_cash_flow'] = (
                summary['totals']['customer_payments'] - 
                summary['totals']['supplier_payments']
            )
            
            return summary
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في ملخص المدفوعات: {str(e)}")
            return {}
    
    def get_aging_report(self, account_type: str) -> List[Dict[str, Any]]:
        """تقرير أعمار الذمم"""
        try:
            if account_type == AccountType.RECEIVABLE.value:
                # تقرير أعمار الذمم المدينة
                query = """
                SELECT 
                    c.id,
                    c.name,
                    c.current_balance,
                    SUM(CASE WHEN p.due_date >= ? THEN p.amount_in_base_currency ELSE 0 END) as current_amount,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_1_30,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_31_60,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_61_90,
                    SUM(CASE WHEN p.due_date < ? THEN p.amount_in_base_currency ELSE 0 END) as over_90_days
                FROM customers c
                LEFT JOIN payments p ON c.id = p.customer_id 
                    AND p.payment_type = ? AND p.status != ?
                WHERE c.current_balance > 0 AND c.is_active = 1
                GROUP BY c.id, c.name, c.current_balance
                ORDER BY c.current_balance DESC
                """
                
                today = date.today()
                days_30_ago = today - timedelta(days=30)
                days_60_ago = today - timedelta(days=60)
                days_90_ago = today - timedelta(days=90)
                
                results = self.db_manager.fetch_all(query, (
                    today.isoformat(),
                    days_30_ago.isoformat(), today.isoformat(),
                    days_60_ago.isoformat(), days_30_ago.isoformat(),
                    days_90_ago.isoformat(), days_60_ago.isoformat(),
                    days_90_ago.isoformat(),
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentStatus.COMPLETED.value
                ))
                
            elif account_type == AccountType.PAYABLE.value:
                # تقرير أعمار الذمم الدائنة
                query = """
                SELECT 
                    s.id,
                    s.name,
                    s.current_balance,
                    SUM(CASE WHEN p.due_date >= ? THEN p.amount_in_base_currency ELSE 0 END) as current_amount,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_1_30,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_31_60,
                    SUM(CASE WHEN p.due_date BETWEEN ? AND ? THEN p.amount_in_base_currency ELSE 0 END) as days_61_90,
                    SUM(CASE WHEN p.due_date < ? THEN p.amount_in_base_currency ELSE 0 END) as over_90_days
                FROM suppliers s
                LEFT JOIN payments p ON s.id = p.supplier_id 
                    AND p.payment_type = ? AND p.status != ?
                WHERE s.current_balance > 0 AND s.is_active = 1
                GROUP BY s.id, s.name, s.current_balance
                ORDER BY s.current_balance DESC
                """
                
                today = date.today()
                days_30_ago = today - timedelta(days=30)
                days_60_ago = today - timedelta(days=60)
                days_90_ago = today - timedelta(days=90)
                
                results = self.db_manager.fetch_all(query, (
                    today.isoformat(),
                    days_30_ago.isoformat(), today.isoformat(),
                    days_60_ago.isoformat(), days_30_ago.isoformat(),
                    days_90_ago.isoformat(), days_60_ago.isoformat(),
                    days_90_ago.isoformat(),
                    PaymentType.SUPPLIER_PAYMENT.value,
                    PaymentStatus.COMPLETED.value
                ))
            
            else:
                return []
            
            aging_data = []
            for row in results:
                aging_data.append({
                    'account_id': row[0],
                    'account_name': row[1],
                    'total_balance': Decimal(str(row[2])),
                    'current': Decimal(str(row[3] or 0)),
                    'days_1_30': Decimal(str(row[4] or 0)),
                    'days_31_60': Decimal(str(row[5] or 0)),
                    'days_61_90': Decimal(str(row[6] or 0)),
                    'over_90_days': Decimal(str(row[7] or 0))
                })
            
            return aging_data
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تقرير أعمار الذمم: {str(e)}")
            return []
    
    def get_cash_flow_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """تقرير التدفق النقدي"""
        try:
            query = """
            SELECT 
                DATE(payment_date) as payment_date,
                payment_type,
                SUM(amount_in_base_currency) as daily_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY DATE(payment_date), payment_type
            ORDER BY payment_date ASC
            """
            
            results = self.db_manager.fetch_all(query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentStatus.COMPLETED.value
            ))
            
            cash_flow = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'daily_flow': {},
                'summary': {
                    'total_inflow': Decimal('0.00'),
                    'total_outflow': Decimal('0.00'),
                    'net_flow': Decimal('0.00')
                }
            }
            
            for row in results:
                payment_date = row[0]
                payment_type = row[1]
                amount = Decimal(str(row[2]))
                
                if payment_date not in cash_flow['daily_flow']:
                    cash_flow['daily_flow'][payment_date] = {
                        'inflow': Decimal('0.00'),
                        'outflow': Decimal('0.00'),
                        'net': Decimal('0.00')
                    }
                
                if payment_type == PaymentType.CUSTOMER_PAYMENT.value:
                    cash_flow['daily_flow'][payment_date]['inflow'] += amount
                    cash_flow['summary']['total_inflow'] += amount
                elif payment_type == PaymentType.SUPPLIER_PAYMENT.value:
                    cash_flow['daily_flow'][payment_date]['outflow'] += amount
                    cash_flow['summary']['total_outflow'] += amount
                
                # حساب الصافي اليومي
                cash_flow['daily_flow'][payment_date]['net'] = (
                    cash_flow['daily_flow'][payment_date]['inflow'] -
                    cash_flow['daily_flow'][payment_date]['outflow']
                )
            
            # حساب الصافي الإجمالي
            cash_flow['summary']['net_flow'] = (
                cash_flow['summary']['total_inflow'] -
                cash_flow['summary']['total_outflow']
            )
            
            return cash_flow
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تقرير التدفق النقدي: {str(e)}")
            return {}
    
    def get_payment_trends_analysis(self, start_date: date, end_date: date, period_type: str = 'monthly') -> Dict[str, Any]:
        """تحليل اتجاهات المدفوعات"""
        try:
            # تحديد تجميع البيانات حسب نوع الفترة
            if period_type == 'daily':
                date_format = "DATE(payment_date)"
                date_group = "DATE(payment_date)"
            elif period_type == 'weekly':
                date_format = "strftime('%Y-W%W', payment_date)"
                date_group = "strftime('%Y-W%W', payment_date)"
            elif period_type == 'monthly':
                date_format = "strftime('%Y-%m', payment_date)"
                date_group = "strftime('%Y-%m', payment_date)"
            else:  # yearly
                date_format = "strftime('%Y', payment_date)"
                date_group = "strftime('%Y', payment_date)"
            
            query = f"""
            SELECT 
                {date_format} as period,
                payment_type,
                COUNT(*) as transaction_count,
                SUM(amount_in_base_currency) as total_amount,
                AVG(amount_in_base_currency) as avg_amount,
                MIN(amount_in_base_currency) as min_amount,
                MAX(amount_in_base_currency) as max_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY {date_group}, payment_type
            ORDER BY period ASC, payment_type
            """
            
            results = self.db_manager.fetch_all(query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentStatus.COMPLETED.value
            ))
            
            trends = {
                'period_type': period_type,
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'trends_data': {},
                'summary': {
                    'total_periods': 0,
                    'growth_rate': {},
                    'volatility': {}
                }
            }
            
            # تنظيم البيانات
            for row in results:
                period = row[0]
                payment_type = row[1]
                
                if period not in trends['trends_data']:
                    trends['trends_data'][period] = {}
                
                trends['trends_data'][period][payment_type] = {
                    'transaction_count': row[2],
                    'total_amount': Decimal(str(row[3])),
                    'avg_amount': Decimal(str(row[4])),
                    'min_amount': Decimal(str(row[5])),
                    'max_amount': Decimal(str(row[6]))
                }
            
            # حساب معدلات النمو والتقلبات
            periods = sorted(trends['trends_data'].keys())
            trends['summary']['total_periods'] = len(periods)
            
            if len(periods) >= 2:
                for payment_type in [PaymentType.CUSTOMER_PAYMENT.value, PaymentType.SUPPLIER_PAYMENT.value]:
                    amounts = []
                    for period in periods:
                        if payment_type in trends['trends_data'][period]:
                            amounts.append(float(trends['trends_data'][period][payment_type]['total_amount']))
                        else:
                            amounts.append(0.0)
                    
                    if len(amounts) >= 2 and amounts[0] > 0:
                        # معدل النمو
                        growth_rate = ((amounts[-1] - amounts[0]) / amounts[0]) * 100
                        trends['summary']['growth_rate'][payment_type] = round(growth_rate, 2)
                        
                        # التقلبات (الانحراف المعياري)
                        if len(amounts) > 1:
                            mean_amount = sum(amounts) / len(amounts)
                            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
                            volatility = (variance ** 0.5) / mean_amount * 100 if mean_amount > 0 else 0
                            trends['summary']['volatility'][payment_type] = round(volatility, 2)
            
            return trends
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحليل اتجاهات المدفوعات: {str(e)}")
            return {}
    
    def get_payment_forecast(self, historical_months: int = 12, forecast_months: int = 3) -> Dict[str, Any]:
        """توقع المدفوعات المستقبلية"""
        try:
            # الحصول على البيانات التاريخية
            end_date = date.today()
            start_date = end_date - timedelta(days=historical_months * 30)
            
            query = """
            SELECT 
                strftime('%Y-%m', payment_date) as month,
                payment_type,
                SUM(amount_in_base_currency) as monthly_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY strftime('%Y-%m', payment_date), payment_type
            ORDER BY month ASC
            """
            
            results = self.db_manager.fetch_all(query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentStatus.COMPLETED.value
            ))
            
            # تنظيم البيانات التاريخية
            historical_data = {}
            for row in results:
                month = row[0]
                payment_type = row[1]
                amount = Decimal(str(row[2]))
                
                if payment_type not in historical_data:
                    historical_data[payment_type] = []
                
                historical_data[payment_type].append({
                    'month': month,
                    'amount': amount
                })
            
            # حساب التوقعات باستخدام المتوسط المتحرك البسيط
            forecast = {
                'historical_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'months': historical_months
                },
                'forecast_period': {
                    'months': forecast_months
                },
                'predictions': {},
                'confidence_level': 'متوسط'  # يمكن تحسينه لاحقاً
            }
            
            for payment_type, data in historical_data.items():
                if len(data) >= 3:  # نحتاج على الأقل 3 نقاط بيانات
                    # حساب المتوسط المتحرك للأشهر الثلاثة الأخيرة
                    recent_amounts = [float(item['amount']) for item in data[-3:]]
                    avg_amount = sum(recent_amounts) / len(recent_amounts)
                    
                    # حساب الاتجاه
                    if len(data) >= 6:
                        first_half = sum(float(item['amount']) for item in data[:len(data)//2]) / (len(data)//2)
                        second_half = sum(float(item['amount']) for item in data[len(data)//2:]) / (len(data) - len(data)//2)
                        trend_factor = (second_half - first_half) / first_half if first_half > 0 else 0
                    else:
                        trend_factor = 0
                    
                    # توليد التوقعات
                    predictions = []
                    for i in range(forecast_months):
                        # تطبيق الاتجاه تدريجياً
                        predicted_amount = avg_amount * (1 + trend_factor * (i + 1) * 0.1)
                        
                        # إضافة الشهر المتوقع
                        forecast_date = end_date + timedelta(days=(i + 1) * 30)
                        forecast_month = forecast_date.strftime('%Y-%m')
                        
                        predictions.append({
                            'month': forecast_month,
                            'predicted_amount': round(Decimal(str(predicted_amount)), 2),
                            'confidence': 'متوسط'
                        })
                    
                    forecast['predictions'][payment_type] = predictions
            
            return forecast
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في توقع المدفوعات: {str(e)}")
            return {}
    
    def get_period_comparison_analysis(self, current_start: date, current_end: date, 
                                     previous_start: date, previous_end: date) -> Dict[str, Any]:
        """مقارنة فترات المدفوعات"""
        try:
            def get_period_data(start_date: date, end_date: date) -> Dict[str, Any]:
                query = """
                SELECT 
                    payment_type,
                    COUNT(*) as transaction_count,
                    SUM(amount_in_base_currency) as total_amount,
                    AVG(amount_in_base_currency) as avg_amount,
                    payment_method,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN customer_id END) as unique_customers,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN supplier_id END) as unique_suppliers
                FROM payments
                WHERE payment_date BETWEEN ? AND ? AND status = ?
                GROUP BY payment_type, payment_method
                """
                
                results = self.db_manager.fetch_all(query, (
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentType.SUPPLIER_PAYMENT.value,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value
                ))
                
                period_data = {
                    'total_transactions': 0,
                    'total_amount': Decimal('0.00'),
                    'by_type': {},
                    'by_method': {},
                    'unique_customers': 0,
                    'unique_suppliers': 0
                }
                
                for row in results:
                    payment_type = row[0]
                    transaction_count = row[1]
                    total_amount = Decimal(str(row[2]))
                    avg_amount = Decimal(str(row[3]))
                    payment_method = row[4]
                    
                    period_data['total_transactions'] += transaction_count
                    period_data['total_amount'] += total_amount
                    
                    if payment_type not in period_data['by_type']:
                        period_data['by_type'][payment_type] = {
                            'count': 0,
                            'amount': Decimal('0.00'),
                            'avg_amount': Decimal('0.00')
                        }
                    
                    period_data['by_type'][payment_type]['count'] += transaction_count
                    period_data['by_type'][payment_type]['amount'] += total_amount
                    period_data['by_type'][payment_type]['avg_amount'] = avg_amount
                    
                    if payment_method not in period_data['by_method']:
                        period_data['by_method'][payment_method] = {
                            'count': 0,
                            'amount': Decimal('0.00')
                        }
                    
                    period_data['by_method'][payment_method]['count'] += transaction_count
                    period_data['by_method'][payment_method]['amount'] += total_amount
                
                # الحصول على عدد العملاء والموردين الفريدين
                unique_query = """
                SELECT 
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN customer_id END) as unique_customers,
                    COUNT(DISTINCT CASE WHEN payment_type = ? THEN supplier_id END) as unique_suppliers
                FROM payments
                WHERE payment_date BETWEEN ? AND ? AND status = ?
                """
                
                unique_result = self.db_manager.fetch_one(unique_query, (
                    PaymentType.CUSTOMER_PAYMENT.value,
                    PaymentType.SUPPLIER_PAYMENT.value,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    PaymentStatus.COMPLETED.value
                ))
                
                if unique_result:
                    period_data['unique_customers'] = unique_result[0] or 0
                    period_data['unique_suppliers'] = unique_result[1] or 0
                
                return period_data
            
            # الحصول على بيانات الفترتين
            current_data = get_period_data(current_start, current_end)
            previous_data = get_period_data(previous_start, previous_end)
            
            # حساب المقارنات والنسب
            comparison = {
                'current_period': {
                    'start_date': current_start,
                    'end_date': current_end,
                    'data': current_data
                },
                'previous_period': {
                    'start_date': previous_start,
                    'end_date': previous_end,
                    'data': previous_data
                },
                'comparison': {
                    'transaction_growth': 0.0,
                    'amount_growth': 0.0,
                    'avg_transaction_growth': 0.0,
                    'customer_growth': 0.0,
                    'supplier_growth': 0.0,
                    'by_type': {},
                    'by_method': {}
                }
            }
            
            # حساب نسب النمو
            if previous_data['total_transactions'] > 0:
                comparison['comparison']['transaction_growth'] = (
                    (current_data['total_transactions'] - previous_data['total_transactions']) /
                    previous_data['total_transactions'] * 100
                )
            
            if previous_data['total_amount'] > 0:
                comparison['comparison']['amount_growth'] = float(
                    (current_data['total_amount'] - previous_data['total_amount']) /
                    previous_data['total_amount'] * 100
                )
            
            if previous_data['unique_customers'] > 0:
                comparison['comparison']['customer_growth'] = (
                    (current_data['unique_customers'] - previous_data['unique_customers']) /
                    previous_data['unique_customers'] * 100
                )
            
            if previous_data['unique_suppliers'] > 0:
                comparison['comparison']['supplier_growth'] = (
                    (current_data['unique_suppliers'] - previous_data['unique_suppliers']) /
                    previous_data['unique_suppliers'] * 100
                )
            
            # مقارنة حسب النوع
            for payment_type in current_data['by_type']:
                if payment_type in previous_data['by_type']:
                    prev_amount = previous_data['by_type'][payment_type]['amount']
                    curr_amount = current_data['by_type'][payment_type]['amount']
                    
                    if prev_amount > 0:
                        growth = float((curr_amount - prev_amount) / prev_amount * 100)
                        comparison['comparison']['by_type'][payment_type] = {
                            'amount_growth': growth
                        }
            
            # مقارنة حسب طريقة الدفع
            for payment_method in current_data['by_method']:
                if payment_method in previous_data['by_method']:
                    prev_amount = previous_data['by_method'][payment_method]['amount']
                    curr_amount = current_data['by_method'][payment_method]['amount']
                    
                    if prev_amount > 0:
                        growth = float((curr_amount - prev_amount) / prev_amount * 100)
                        comparison['comparison']['by_method'][payment_method] = {
                            'amount_growth': growth
                        }
            
            return comparison
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في مقارنة فترات المدفوعات: {str(e)}")
            return {}
    
    def get_payment_performance_kpis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """مؤشرات الأداء الرئيسية للمدفوعات"""
        try:
            # الاستعلامات الأساسية
            summary_query = """
            SELECT 
                payment_type,
                COUNT(*) as transaction_count,
                SUM(amount_in_base_currency) as total_amount,
                AVG(amount_in_base_currency) as avg_amount,
                MIN(amount_in_base_currency) as min_amount,
                MAX(amount_in_base_currency) as max_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND status = ?
            GROUP BY payment_type
            """
            
            # معدل التحصيل
            collection_query = """
            SELECT 
                COUNT(CASE WHEN status = ? THEN 1 END) as completed_payments,
                COUNT(*) as total_payments,
                SUM(CASE WHEN status = ? THEN amount_in_base_currency ELSE 0 END) as collected_amount,
                SUM(amount_in_base_currency) as total_amount
            FROM payments
            WHERE payment_date BETWEEN ? AND ? AND payment_type = ?
            """
            
            # متوسط وقت التحصيل
            collection_time_query = """
            SELECT 
                AVG(julianday(payment_date) - julianday(due_date)) as avg_collection_days
            FROM payments
            WHERE payment_date BETWEEN ? AND ? 
                AND payment_type = ? 
                AND status = ?
                AND due_date IS NOT NULL
            """
            
            results = self.db_manager.fetch_all(summary_query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentStatus.COMPLETED.value
            ))
            
            collection_results = self.db_manager.fetch_one(collection_query, (
                PaymentStatus.COMPLETED.value,
                PaymentStatus.COMPLETED.value,
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentType.CUSTOMER_PAYMENT.value
            ))
            
            collection_time_result = self.db_manager.fetch_one(collection_time_query, (
                start_date.isoformat(),
                end_date.isoformat(),
                PaymentType.CUSTOMER_PAYMENT.value,
                PaymentStatus.COMPLETED.value
            ))
            
            kpis = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_transactions': 0,
                    'total_amount': Decimal('0.00'),
                    'avg_transaction_value': Decimal('0.00')
                },
                'by_type': {},
                'collection_metrics': {
                    'collection_rate': 0.0,
                    'collection_amount_rate': 0.0,
                    'avg_collection_days': 0.0
                },
                'efficiency_metrics': {
                    'transactions_per_day': 0.0,
                    'amount_per_day': Decimal('0.00'),
                    'payment_velocity': 0.0
                }
            }
            
            # معالجة النتائج الأساسية
            for row in results:
                payment_type = row[0]
                transaction_count = row[1]
                total_amount = Decimal(str(row[2]))
                avg_amount = Decimal(str(row[3]))
                min_amount = Decimal(str(row[4]))
                max_amount = Decimal(str(row[5]))
                
                kpis['summary']['total_transactions'] += transaction_count
                kpis['summary']['total_amount'] += total_amount
                
                kpis['by_type'][payment_type] = {
                    'transaction_count': transaction_count,
                    'total_amount': total_amount,
                    'avg_amount': avg_amount,
                    'min_amount': min_amount,
                    'max_amount': max_amount
                }
            
            # حساب متوسط قيمة المعاملة الإجمالي
            if kpis['summary']['total_transactions'] > 0:
                kpis['summary']['avg_transaction_value'] = (
                    kpis['summary']['total_amount'] / kpis['summary']['total_transactions']
                )
            
            # معالجة مقاييس التحصيل
            if collection_results:
                completed_payments = collection_results[0] or 0
                total_payments = collection_results[1] or 0
                collected_amount = Decimal(str(collection_results[2] or 0))
                total_amount = Decimal(str(collection_results[3] or 0))
                
                if total_payments > 0:
                    kpis['collection_metrics']['collection_rate'] = (completed_payments / total_payments) * 100
                
                if total_amount > 0:
                    kpis['collection_metrics']['collection_amount_rate'] = float(
                        (collected_amount / total_amount) * 100
                    )
            
            # متوسط وقت التحصيل
            if collection_time_result and collection_time_result[0]:
                kpis['collection_metrics']['avg_collection_days'] = round(collection_time_result[0], 1)
            
            # مقاييس الكفاءة
            period_days = (end_date - start_date).days + 1
            if period_days > 0:
                kpis['efficiency_metrics']['transactions_per_day'] = (
                    kpis['summary']['total_transactions'] / period_days
                )
                kpis['efficiency_metrics']['amount_per_day'] = (
                    kpis['summary']['total_amount'] / period_days
                )
                
                # سرعة المدفوعات (معاملات في اليوم)
                kpis['efficiency_metrics']['payment_velocity'] = (
                    kpis['summary']['total_transactions'] / period_days
                )
            
            return kpis
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في مؤشرات الأداء الرئيسية: {str(e)}")
            return {}