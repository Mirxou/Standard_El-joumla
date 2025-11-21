#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة خطط الدفع والتقسيط
Payment Plan Service
"""

import sqlite3
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.payment_plan import (
    PaymentPlan, PaymentInstallment, PaymentPlanStatus,
    InstallmentStatus, PaymentFrequency, LateFeeType
)
from core.database_manager import DatabaseManager


class PaymentPlanService:
    """خدمة إدارة خطط الدفع"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # ===================== إنشاء وإدارة الخطط =====================
    
    def generate_plan_number(self) -> str:
        """توليد رقم خطة دفع"""
        today = date.today()
        prefix = f"PP-{today.year}{today.month:02d}"
        
        query = """
        SELECT plan_number FROM payment_plans 
        WHERE plan_number LIKE ? 
        ORDER BY plan_number DESC LIMIT 1
        """
        
        result = self.db.execute_query(query, (f"{prefix}%",))
        
        if result and result[0][0]:
            last_number = result[0][0]
            sequence = int(last_number.split('-')[-1]) + 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    def create_payment_plan(self, plan: PaymentPlan) -> int:
        """إنشاء خطة دفع جديدة"""
        if not plan.plan_number:
            plan.plan_number = self.generate_plan_number()
        
        if not plan.start_date:
            plan.start_date = date.today()
        
        # حساب المبلغ المقسط
        plan.financed_amount = plan.total_amount - plan.down_payment
        
        # توليد الأقساط
        if not plan.installments:
            plan.generate_installments()
        
        plan.created_at = datetime.now()
        plan.updated_at = datetime.now()
        
        # حفظ الخطة
        query = """
        INSERT INTO payment_plans (
            plan_number, invoice_id, invoice_number, customer_id, customer_name,
            plan_name, description, start_date, end_date,
            total_amount, down_payment, financed_amount,
            number_of_installments, installment_amount, frequency,
            interest_rate, total_interest,
            late_fee_type, late_fee_value, grace_period_days,
            status, total_paid, total_remaining, total_late_fees,
            notes, terms_conditions, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            plan.plan_number, plan.invoice_id, plan.invoice_number,
            plan.customer_id, plan.customer_name,
            plan.plan_name, plan.description,
            plan.start_date.isoformat() if plan.start_date else None,
            plan.end_date.isoformat() if plan.end_date else None,
            float(plan.total_amount), float(plan.down_payment), float(plan.financed_amount),
            plan.number_of_installments, float(plan.installment_amount),
            plan.frequency.name if isinstance(plan.frequency, PaymentFrequency) else plan.frequency,
            float(plan.interest_rate), float(plan.total_interest),
            plan.late_fee_type.name if isinstance(plan.late_fee_type, LateFeeType) else plan.late_fee_type,
            float(plan.late_fee_value), plan.grace_period_days,
            plan.status.name if isinstance(plan.status, PaymentPlanStatus) else plan.status,
            float(plan.total_paid), float(plan.total_remaining), float(plan.total_late_fees),
            plan.notes, plan.terms_conditions, plan.created_by,
            plan.created_at.isoformat() if plan.created_at else None,
            plan.updated_at.isoformat() if plan.updated_at else None
        )
        
        plan_id = self.db.execute_update(query, params)
        
        # حفظ الأقساط
        for installment in plan.installments:
            self._save_installment(plan_id, installment)
        
        return plan_id
    
    def _save_installment(self, plan_id: int, installment: PaymentInstallment) -> int:
        """حفظ قسط"""
        query = """
        INSERT INTO payment_installments (
            payment_plan_id, installment_number, due_date,
            principal_amount, interest_amount, late_fee, total_amount,
            amount_paid, remaining_amount, status,
            payment_date, payment_method, payment_reference,
            notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            plan_id, installment.installment_number,
            installment.due_date.isoformat() if installment.due_date else None,
            float(installment.principal_amount), float(installment.interest_amount),
            float(installment.late_fee), float(installment.total_amount),
            float(installment.amount_paid), float(installment.remaining_amount),
            installment.status.name if isinstance(installment.status, InstallmentStatus) else installment.status,
            installment.payment_date.isoformat() if installment.payment_date else None,
            installment.payment_method, installment.payment_reference,
            installment.notes,
            installment.created_at.isoformat() if installment.created_at else None,
            installment.updated_at.isoformat() if installment.updated_at else None
        )
        
        return self.db.execute_update(query, params)
    
    def get_payment_plan(self, plan_id: int) -> Optional[PaymentPlan]:
        """الحصول على خطة دفع"""
        query = """
        SELECT * FROM payment_plans WHERE id = ?
        """
        
        result = self.db.execute_query(query, (plan_id,))
        if not result:
            return None
        
        plan_data = self._row_to_dict(result[0])
        plan = PaymentPlan.from_dict(plan_data)
        
        # تحميل الأقساط
        installments_query = """
        SELECT * FROM payment_installments WHERE payment_plan_id = ?
        ORDER BY installment_number
        """
        installments_result = self.db.execute_query(installments_query, (plan_id,))
        
        for inst_row in installments_result:
            inst_data = self._row_to_dict(inst_row)
            plan.installments.append(PaymentInstallment.from_dict(inst_data))
        
        return plan
    
    def update_payment_plan(self, plan: PaymentPlan) -> bool:
        """تحديث خطة دفع"""
        plan.updated_at = datetime.now()
        
        query = """
        UPDATE payment_plans SET
            invoice_id = ?, invoice_number = ?, customer_id = ?, customer_name = ?,
            plan_name = ?, description = ?, start_date = ?, end_date = ?,
            total_amount = ?, down_payment = ?, financed_amount = ?,
            number_of_installments = ?, installment_amount = ?, frequency = ?,
            interest_rate = ?, total_interest = ?,
            late_fee_type = ?, late_fee_value = ?, grace_period_days = ?,
            status = ?, total_paid = ?, total_remaining = ?, total_late_fees = ?,
            notes = ?, terms_conditions = ?, updated_at = ?
        WHERE id = ?
        """
        
        params = (
            plan.invoice_id, plan.invoice_number, plan.customer_id, plan.customer_name,
            plan.plan_name, plan.description,
            plan.start_date.isoformat() if plan.start_date else None,
            plan.end_date.isoformat() if plan.end_date else None,
            float(plan.total_amount), float(plan.down_payment), float(plan.financed_amount),
            plan.number_of_installments, float(plan.installment_amount),
            plan.frequency.name if isinstance(plan.frequency, PaymentFrequency) else plan.frequency,
            float(plan.interest_rate), float(plan.total_interest),
            plan.late_fee_type.name if isinstance(plan.late_fee_type, LateFeeType) else plan.late_fee_type,
            float(plan.late_fee_value), plan.grace_period_days,
            plan.status.name if isinstance(plan.status, PaymentPlanStatus) else plan.status,
            float(plan.total_paid), float(plan.total_remaining), float(plan.total_late_fees),
            plan.notes, plan.terms_conditions,
            plan.updated_at.isoformat(),
            plan.id
        )
        
        self.db.execute_update(query, params)
        
        # تحديث الأقساط
        for installment in plan.installments:
            if installment.id:
                self._update_installment(installment)
            else:
                self._save_installment(plan.id, installment)
        
        return True
    
    def _update_installment(self, installment: PaymentInstallment) -> bool:
        """تحديث قسط"""
        installment.updated_at = datetime.now()
        
        query = """
        UPDATE payment_installments SET
            due_date = ?, principal_amount = ?, interest_amount = ?,
            late_fee = ?, total_amount = ?, amount_paid = ?, remaining_amount = ?,
            status = ?, payment_date = ?, payment_method = ?, payment_reference = ?,
            notes = ?, updated_at = ?
        WHERE id = ?
        """
        
        params = (
            installment.due_date.isoformat() if installment.due_date else None,
            float(installment.principal_amount), float(installment.interest_amount),
            float(installment.late_fee), float(installment.total_amount),
            float(installment.amount_paid), float(installment.remaining_amount),
            installment.status.name if isinstance(installment.status, InstallmentStatus) else installment.status,
            installment.payment_date.isoformat() if installment.payment_date else None,
            installment.payment_method, installment.payment_reference,
            installment.notes,
            installment.updated_at.isoformat(),
            installment.id
        )
        
        self.db.execute_update(query, params)
        return True
    
    # ===================== البحث والتصفية =====================
    
    def get_all_payment_plans(
        self,
        customer_id: Optional[int] = None,
        status: Optional[PaymentPlanStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PaymentPlan]:
        """الحصول على قائمة خطط الدفع"""
        query = "SELECT * FROM payment_plans WHERE 1=1"
        params = []
        
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        
        if status:
            query += " AND status = ?"
            params.append(status.name if isinstance(status, PaymentPlanStatus) else status)
        
        if from_date:
            query += " AND start_date >= ?"
            params.append(from_date.isoformat())
        
        if to_date:
            query += " AND start_date <= ?"
            params.append(to_date.isoformat())
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.db.execute_query(query, tuple(params))
        
        plans = []
        for row in results:
            plan_data = self._row_to_dict(row)
            plan = PaymentPlan.from_dict(plan_data)
            
            # تحميل الأقساط
            inst_query = "SELECT * FROM payment_installments WHERE payment_plan_id = ? ORDER BY installment_number"
            inst_results = self.db.execute_query(inst_query, (plan.id,))
            for inst_row in inst_results:
                inst_data = self._row_to_dict(inst_row)
                plan.installments.append(PaymentInstallment.from_dict(inst_data))
            
            plans.append(plan)
        
        return plans
    
    def get_overdue_installments(self) -> List[Tuple[PaymentPlan, PaymentInstallment]]:
        """الحصول على الأقساط المتأخرة"""
        query = """
        SELECT pp.*, pi.* 
        FROM payment_plans pp
        JOIN payment_installments pi ON pp.id = pi.payment_plan_id
        WHERE pi.status IN (?, ?)
        AND pi.due_date < date('now')
        ORDER BY pi.due_date
        """
        
        params = (InstallmentStatus.PENDING.name, InstallmentStatus.PARTIALLY_PAID.name)
        results = self.db.execute_query(query, params)
        
        overdue = []
        for row in results:
            # استخراج بيانات الخطة والقسط من الصف
            plan_data = self._extract_plan_data(row)
            inst_data = self._extract_installment_data(row)
            
            plan = PaymentPlan.from_dict(plan_data)
            installment = PaymentInstallment.from_dict(inst_data)
            
            overdue.append((plan, installment))
        
        return overdue
    
    # ===================== الدفع =====================
    
    def make_payment(
        self,
        plan_id: int,
        installment_id: int,
        amount: Decimal,
        payment_date: Optional[date] = None,
        payment_method: Optional[str] = None,
        reference: Optional[str] = None
    ) -> bool:
        """تسجيل دفعة"""
        plan = self.get_payment_plan(plan_id)
        if not plan:
            return False
        
        # العثور على القسط
        installment = next((inst for inst in plan.installments if inst.id == installment_id), None)
        if not installment:
            return False
        
        # تسجيل الدفعة
        if not installment.make_payment(amount, payment_date, payment_method, reference):
            return False
        
        # تحديث القسط
        self._update_installment(installment)
        
        # تحديث الملخص المالي للخطة
        plan.update_financial_summary()
        self.update_payment_plan(plan)
        
        return True
    
    def apply_late_fees_to_plan(self, plan_id: int) -> bool:
        """تطبيق غرامات التأخير على خطة"""
        plan = self.get_payment_plan(plan_id)
        if not plan:
            return False
        
        plan.apply_late_fees()
        
        # تحديث الأقساط
        for installment in plan.installments:
            if installment.id:
                self._update_installment(installment)
        
        # تحديث الملخص
        plan.update_financial_summary()
        self.update_payment_plan(plan)
        
        return True
    
    def apply_late_fees_to_all(self) -> int:
        """تطبيق غرامات التأخير على جميع الخطط النشطة"""
        query = "SELECT id FROM payment_plans WHERE status = ?"
        results = self.db.execute_query(query, (PaymentPlanStatus.ACTIVE.name,))
        
        count = 0
        for row in results:
            plan_id = row[0]
            if self.apply_late_fees_to_plan(plan_id):
                count += 1
        
        return count
    
    # ===================== الإحصائيات =====================
    
    def get_customer_payment_summary(self, customer_id: int) -> Dict[str, Any]:
        """ملخص دفعات العميل"""
        query = """
        SELECT 
            COUNT(*) as total_plans,
            SUM(total_amount) as total_financed,
            SUM(total_paid) as total_paid,
            SUM(total_remaining) as total_remaining,
            SUM(total_late_fees) as total_late_fees
        FROM payment_plans
        WHERE customer_id = ?
        """
        
        result = self.db.execute_query(query, (customer_id,))
        if not result:
            return {}
        
        row = result[0]
        return {
            'total_plans': row[0] or 0,
            'total_financed': float(row[1]) if row[1] else 0.0,
            'total_paid': float(row[2]) if row[2] else 0.0,
            'total_remaining': float(row[3]) if row[3] else 0.0,
            'total_late_fees': float(row[4]) if row[4] else 0.0,
        }
    
    def get_payment_plan_statistics(self) -> Dict[str, Any]:
        """إحصائيات خطط الدفع"""
        # حسب الحالة
        status_query = """
        SELECT status, COUNT(*), SUM(total_amount), SUM(total_remaining)
        FROM payment_plans
        GROUP BY status
        """
        
        status_results = self.db.execute_query(status_query)
        by_status = {}
        for row in status_results:
            by_status[row[0]] = {
                'count': row[1],
                'total_amount': float(row[2]) if row[2] else 0.0,
                'total_remaining': float(row[3]) if row[3] else 0.0,
            }
        
        # الأقساط المتأخرة
        overdue_query = """
        SELECT COUNT(*)
        FROM payment_installments
        WHERE status IN (?, ?)
        AND due_date < date('now')
        """
        overdue_result = self.db.execute_query(
            overdue_query,
            (InstallmentStatus.PENDING.name, InstallmentStatus.PARTIALLY_PAID.name)
        )
        overdue_count = overdue_result[0][0] if overdue_result else 0
        
        return {
            'by_status': by_status,
            'overdue_installments': overdue_count,
        }
    
    # ===================== وظائف مساعدة =====================
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """تحويل صف إلى قاموس"""
        if not row:
            return {}
        
        cursor = self.db.conn.cursor()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        return dict(zip(columns, row))
    
    def _extract_plan_data(self, row) -> Dict[str, Any]:
        """استخراج بيانات الخطة من صف مدمج"""
        # افتراض أن أعمدة الخطة تأتي أولاً
        plan_columns = ['id', 'plan_number', 'invoice_id', 'invoice_number', 
                       'customer_id', 'customer_name', 'plan_name', 'description',
                       'start_date', 'end_date', 'total_amount', 'down_payment',
                       'financed_amount', 'number_of_installments', 'installment_amount',
                       'frequency', 'interest_rate', 'total_interest', 'late_fee_type',
                       'late_fee_value', 'grace_period_days', 'status', 'total_paid',
                       'total_remaining', 'total_late_fees', 'notes', 'terms_conditions',
                       'created_by', 'created_at', 'updated_at', 'completed_at']
        return dict(zip(plan_columns, row[:len(plan_columns)]))
    
    def _extract_installment_data(self, row) -> Dict[str, Any]:
        """استخراج بيانات القسط من صف مدمج"""
        plan_cols_count = 31  # عدد أعمدة الخطة
        inst_columns = ['id', 'payment_plan_id', 'installment_number', 'due_date',
                       'principal_amount', 'interest_amount', 'late_fee', 'total_amount',
                       'amount_paid', 'remaining_amount', 'status', 'payment_date',
                       'payment_method', 'payment_reference', 'notes', 'created_at', 'updated_at']
        return dict(zip(inst_columns, row[plan_cols_count:]))
