#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة العملاء (CRM) المحسّنة
أدوات لإنشاء/تعديل/البحث عن العملاء وإدارة الفرص والعملاء المحتملين
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class LeadStatus(Enum):
    """حالات العملاء المحتملين"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class OpportunityStage(Enum):
    """مراحل الفرص البيعية"""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    WON = "won"
    LOST = "lost"


@dataclass
class Lead:
    """عميل محتمل"""
    lead_id: Optional[int] = None
    name: str = ""
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None  # المصدر: website, referral, cold_call, etc
    status: LeadStatus = LeadStatus.NEW
    assigned_to: Optional[int] = None
    expected_value: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Opportunity:
    """فرصة بيعية"""
    opportunity_id: Optional[int] = None
    name: str = ""
    customer_id: Optional[int] = None
    lead_id: Optional[int] = None
    stage: OpportunityStage = OpportunityStage.PROSPECTING
    expected_value: float = 0.0
    probability: float = 0.0  # احتمالية النجاح (0-100)
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CRMService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger
        self._init_crm_tables()

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        try:
            now = datetime.now()
            q = ('INSERT INTO customers (name, phone, email, address, credit_limit, current_balance, created_at, updated_at) '
                 'VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
            params = (
                customer_data.get('name'), customer_data.get('phone'), customer_data.get('email'), customer_data.get('address'),
                float(customer_data.get('credit_limit', 0)), float(customer_data.get('current_balance', 0)), now, now
            )
            res = self.db.execute_query(q, params)
            if res and hasattr(res, 'lastrowid'):
                return res.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء عميل: {e}')
        return None

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.db.fetch_one('SELECT * FROM customers WHERE id = ?', (customer_id,))
            return row
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في جلب بيانات العميل {customer_id}: {e}')
            return None

    def search_customers(self, term: str) -> List[Dict[str, Any]]:
        try:
            like = f'%{term}%'
            rows = self.db.fetch_all('SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?', (like, like, like))
            return rows
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في البحث عن العملاء: {e}')
            return []
    
    def _init_crm_tables(self):
        """إنشاء جداول CRM المحسّنة"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # جدول العملاء المحتملين (Leads)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    company TEXT,
                    phone TEXT,
                    email TEXT,
                    source TEXT,
                    status TEXT DEFAULT 'new',
                    assigned_to INTEGER,
                    expected_value REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
                )
            """)
            
            # جدول الفرص البيعية (Opportunities)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    customer_id INTEGER,
                    lead_id INTEGER,
                    stage TEXT DEFAULT 'prospecting',
                    expected_value REAL DEFAULT 0,
                    probability REAL DEFAULT 0,
                    expected_close_date DATE,
                    assigned_to INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id),
                    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
                )
            """)
            
            # جدول تفاعلات العملاء
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_interactions (
                    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    lead_id INTEGER,
                    interaction_type TEXT NOT NULL,
                    subject TEXT,
                    notes TEXT,
                    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                    FOREIGN KEY (lead_id) REFERENCES leads(lead_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            conn.commit()
            if self.logger:
                self.logger.info("✅ تم إنشاء جداول CRM المحسّنة")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء جداول CRM: {e}")
    
    # ==================== إدارة العملاء المحتملين ====================
    
    def create_lead(self, lead: Lead) -> Optional[int]:
        """إنشاء عميل محتمل جديد"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO leads (
                    name, company, phone, email, source,
                    status, assigned_to, expected_value, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.name, lead.company, lead.phone, lead.email, lead.source,
                lead.status.value, lead.assigned_to, lead.expected_value, lead.notes
            ))
            
            conn.commit()
            lead_id = cursor.lastrowid
            
            if self.logger:
                self.logger.info(f"✅ تم إنشاء عميل محتمل: {lead.name} (ID: {lead_id})")
            
            return lead_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء العميل المحتمل: {e}")
            return None
    
    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """الحصول على عميل محتمل"""
        try:
            row = self.db.fetch_one('SELECT * FROM leads WHERE lead_id = ?', (lead_id,))
            if row:
                return Lead(
                    lead_id=row['lead_id'],
                    name=row['name'],
                    company=row['company'],
                    phone=row['phone'],
                    email=row['email'],
                    source=row['source'],
                    status=LeadStatus(row['status']),
                    assigned_to=row['assigned_to'],
                    expected_value=row['expected_value'],
                    notes=row['notes'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على العميل المحتمل: {e}")
        return None
    
    def update_lead_status(self, lead_id: int, status: LeadStatus) -> bool:
        """تحديث حالة العميل المحتمل"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE leads
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE lead_id = ?
            """, (status.value, lead_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث حالة العميل المحتمل: {e}")
            return False
    
    def convert_lead_to_customer(self, lead_id: int) -> Optional[int]:
        """تحويل عميل محتمل إلى عميل"""
        lead = self.get_lead(lead_id)
        if not lead:
            return None
        
        try:
            # إنشاء عميل جديد
            customer_data = {
                'name': lead.name,
                'phone': lead.phone,
                'email': lead.email,
                'address': lead.company or "",
                'credit_limit': 0,
                'current_balance': 0
            }
            
            customer_id = self.create_customer(customer_data)
            
            if customer_id:
                # تحديث حالة العميل المحتمل
                self.update_lead_status(lead_id, LeadStatus.WON)
                
                if self.logger:
                    self.logger.info(f"✅ تم تحويل العميل المحتمل {lead_id} إلى عميل {customer_id}")
                
                return customer_id
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحويل العميل المحتمل: {e}")
        
        return None
    
    def list_leads(self, status: Optional[LeadStatus] = None) -> List[Lead]:
        """قائمة العملاء المحتملين"""
        try:
            if status:
                rows = self.db.fetch_all(
                    'SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC',
                    (status.value,)
                )
            else:
                rows = self.db.fetch_all('SELECT * FROM leads ORDER BY created_at DESC')
            
            leads = []
            for row in rows:
                leads.append(Lead(
                    lead_id=row['lead_id'],
                    name=row['name'],
                    company=row['company'],
                    phone=row['phone'],
                    email=row['email'],
                    source=row['source'],
                    status=LeadStatus(row['status']),
                    assigned_to=row['assigned_to'],
                    expected_value=row['expected_value'],
                    notes=row['notes']
                ))
            
            return leads
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في قائمة العملاء المحتملين: {e}")
            return []
    
    # ==================== إدارة الفرص ====================
    
    def create_opportunity(self, opportunity: Opportunity) -> Optional[int]:
        """إنشاء فرصة بيعية"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO opportunities (
                    name, customer_id, lead_id, stage, expected_value,
                    probability, expected_close_date, assigned_to, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity.name, opportunity.customer_id, opportunity.lead_id,
                opportunity.stage.value, opportunity.expected_value,
                opportunity.probability, opportunity.expected_close_date,
                opportunity.assigned_to, opportunity.description
            ))
            
            conn.commit()
            opportunity_id = cursor.lastrowid
            
            if self.logger:
                self.logger.info(f"✅ تم إنشاء فرصة بيعية: {opportunity.name}")
            
            return opportunity_id
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إنشاء الفرصة: {e}")
            return None
    
    def update_opportunity_stage(self, opportunity_id: int, stage: OpportunityStage) -> bool:
        """تحديث مرحلة الفرصة"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE opportunities
                SET stage = ?, updated_at = CURRENT_TIMESTAMP
                WHERE opportunity_id = ?
            """, (stage.value, opportunity_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحديث مرحلة الفرصة: {e}")
            return False
    
    def get_sales_pipeline(self) -> Dict[str, Any]:
        """الحصول على مسار المبيعات"""
        try:
            pipeline = {}
            
            for stage in OpportunityStage:
                rows = self.db.fetch_all("""
                    SELECT COUNT(*) as count, SUM(expected_value) as total_value
                    FROM opportunities
                    WHERE stage = ?
                """, (stage.value,))
                
                if rows and rows[0]:
                    pipeline[stage.value] = {
                        'count': rows[0]['count'] or 0,
                        'total_value': rows[0]['total_value'] or 0
                    }
            
            return pipeline
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على مسار المبيعات: {e}")
            return {}
    
    # ==================== التفاعلات ====================
    
    def add_interaction(self, customer_id: Optional[int], lead_id: Optional[int],
                       interaction_type: str, subject: str, notes: str, user_id: int) -> Optional[int]:
        """إضافة تفاعل مع عميل أو عميل محتمل"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO customer_interactions (
                    customer_id, lead_id, interaction_type, subject, notes, user_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (customer_id, lead_id, interaction_type, subject, notes, user_id))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة التفاعل: {e}")
            return None
    
    def get_customer_interactions(self, customer_id: int) -> List[Dict[str, Any]]:
        """الحصول على تفاعلات العميل"""
        try:
            rows = self.db.fetch_all("""
                SELECT * FROM customer_interactions
                WHERE customer_id = ?
                ORDER BY interaction_date DESC
            """, (customer_id,))
            return rows or []
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على تفاعلات العميل: {e}")
            return []
