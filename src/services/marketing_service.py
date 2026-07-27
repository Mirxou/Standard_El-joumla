import logging
#!/usr/bin/env python3
"""
خدمة التسويق - Marketing Service
إدارة الحملات التسويقية وتقسيم العملاء والتواصل الجماعي
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..core.database_manager import DatabaseManager
from ..utils.db_helpers import get_value
from ..utils.logger import setup_logger


def get_val(key, index, default=None):
    return (
        key[index]
        if isinstance(key, (list, tuple)) and len(key) > index
        else (key.get(index, default) if isinstance(key, dict) else default)
    )


class CampaignType(Enum):
    """أنواع الحملات التسويقية"""

    EMAIL = "email"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    PROMOTIONAL = "promotional"
    SEASONAL = "seasonal"
    LOYALTY = "loyalty"


class CampaignStatus(Enum):
    """حالات الحملة"""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CustomerSegmentType(Enum):
    """أنواع تقسيم العملاء"""

    ALL = "all"
    NEW_CUSTOMERS = "new_customers"
    REPEAT_CUSTOMERS = "repeat_customers"
    HIGH_VALUE = "high_value"
    INACTIVE = "inactive"
    CUSTOM = "custom"


@dataclass
class MarketingCampaign:
    """حملة تسويقية"""

    campaign_id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    campaign_type: CampaignType = CampaignType.EMAIL
    status: CampaignStatus = CampaignStatus.DRAFT

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    target_segment: CustomerSegmentType = CustomerSegmentType.ALL
    target_customer_ids: Optional[List[int]] = None

    message_subject: Optional[str] = None
    message_content: Optional[str] = None

    budget: float = 0.0
    estimated_reach: int = 0
    actual_reach: int = 0

    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_converted: int = 0

    revenue_generated: float = 0.0
    roi: float = 0.0

    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CustomerSegment:
    """شريحة عملاء"""

    segment_id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    segment_type: CustomerSegmentType = CustomerSegmentType.CUSTOM

    filters: Optional[Dict[str, Any]] = None
    customer_count: int = 0

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CampaignMetrics:
    """مقاييس الحملة"""

    campaign_id: int
    campaign_name: str

    # معدلات التفاعل
    delivery_rate: float = 0.0  # نسبة التوصيل
    open_rate: float = 0.0  # نسبة الفتح
    click_rate: float = 0.0  # نسبة النقر
    conversion_rate: float = 0.0  # نسبة التحويل

    # المالية
    total_budget: float = 0.0
    total_revenue: float = 0.0
    roi: float = 0.0
    cost_per_acquisition: float = 0.0

    # الوقت
    duration_days: int = 0
    status: CampaignStatus = CampaignStatus.DRAFT


class MarketingService:
    """خدمة التسويق"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = setup_logger(__name__)
        self._init_tables()

    def _init_tables(self):
        """إنشاء جداول التسويق"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # جدول الحملات التسويقية
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketing_campaigns (
                    campaign_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    campaign_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',

                    start_date TIMESTAMP,
                    end_date TIMESTAMP,

                    target_segment TEXT,
                    target_customer_ids TEXT,

                    message_subject TEXT,
                    message_content TEXT,

                    budget REAL DEFAULT 0,
                    estimated_reach INTEGER DEFAULT 0,
                    actual_reach INTEGER DEFAULT 0,

                    total_sent INTEGER DEFAULT 0,
                    total_delivered INTEGER DEFAULT 0,
                    total_opened INTEGER DEFAULT 0,
                    total_clicked INTEGER DEFAULT 0,
                    total_converted INTEGER DEFAULT 0,

                    revenue_generated REAL DEFAULT 0,
                    roi REAL DEFAULT 0,

                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """)

            # جدول شرائح العملاء
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_segments (
                    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    segment_type TEXT NOT NULL,
                    filters TEXT,
                    customer_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # جدول سجل الحملات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaign_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP,
                    converted_at TIMESTAMP,
                    conversion_value REAL DEFAULT 0,

                    FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(campaign_id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            """)

            conn.commit()
            self.logger.info("✅ تم إنشاء جداول التسويق بنجاح")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"خطأ في إنشاء جداول التسويق: {e}")
            raise

    # ==================== إدارة الحملات ====================

    def create_campaign(self, campaign: MarketingCampaign) -> int:
        """إنشاء حملة تسويقية جديدة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO marketing_campaigns (
                    name, description, campaign_type, status,
                    start_date, end_date,
                    target_segment, message_subject, message_content,
                    budget, estimated_reach, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    campaign.name,
                    campaign.description,
                    campaign.campaign_type.value,
                    campaign.status.value,
                    campaign.start_date,
                    campaign.end_date,
                    campaign.target_segment.value if campaign.target_segment else None,
                    campaign.message_subject,
                    campaign.message_content,
                    campaign.budget,
                    campaign.estimated_reach,
                    campaign.created_by,
                ),
            )

            conn.commit()
            campaign_id = cursor.lastrowid

            self.logger.info(f"✅ تم إنشاء حملة تسويقية: {campaign.name} (ID: {campaign_id})")
            return campaign_id

        except Exception as e:
            conn.rollback()
            self.logger.error(f"خطأ في إنشاء الحملة: {e}")
            raise

    def get_campaign(self, campaign_id: int) -> Optional[MarketingCampaign]:
        """الحصول على حملة محددة"""
        try:
            query = "SELECT * FROM marketing_campaigns WHERE campaign_id = ?"
            result = self.db.execute_query(query, (campaign_id,))

            if not result or len(result) == 0:
                return None

            row = result[0]
            isinstance(row, dict)

            def to_dt(val):
                if not val:
                    return None
                if isinstance(val, datetime):
                    return val
                try:
                    return datetime.fromisoformat(str(val).replace(" ", "T"))
                except Exception:
                    return None

            return MarketingCampaign(
                campaign_id=get_val("campaign_id", 0),
                name=get_val("name", 1, ""),
                description=get_val("description", 2),
                campaign_type=CampaignType(get_val("campaign_type", 3, "email")),
                status=CampaignStatus(get_val("status", 4, "draft")),
                start_date=to_dt(get_val("start_date", 5)),
                end_date=to_dt(get_val("end_date", 6)),
                target_segment=(
                    CustomerSegmentType(get_val("target_segment", 7))
                    if get_val("target_segment", 7)
                    else CustomerSegmentType.ALL
                ),
                message_subject=get_val("message_subject", 9),
                message_content=get_val("message_content", 10),
                budget=float(get_val("budget", 11, 0)),
                estimated_reach=get_val("estimated_reach", 12, 0),
                actual_reach=get_val("actual_reach", 13, 0),
                total_sent=get_val("total_sent", 14, 0),
                total_delivered=get_val("total_delivered", 15, 0),
                total_opened=get_val("total_opened", 16, 0),
                total_clicked=get_val("total_clicked", 17, 0),
                total_converted=get_val("total_converted", 18, 0),
                revenue_generated=float(get_val("revenue_generated", 19, 0)),
                roi=float(get_val("roi", 20, 0)),
                created_by=get_val("created_by", 21),
                created_at=to_dt(get_val("created_at", 22)),
                updated_at=to_dt(get_val("updated_at", 23)),
            )
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الحملة: {e}")
            return None

    def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None,
    ) -> List[MarketingCampaign]:
        """قائمة الحملات"""
        try:
            query = "SELECT * FROM marketing_campaigns WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if campaign_type:
                query += " AND campaign_type = ?"
                params.append(campaign_type.value)

            query += " ORDER BY created_at DESC"

            result = self.db.execute_query(query, tuple(params))
            campaigns = []

            for row in result:
                isinstance(row, dict)
                campaigns.append(
                    MarketingCampaign(
                        campaign_id=get_val("campaign_id", 0),
                        name=get_val("name", 1, ""),
                        description=get_val("description", 2),
                        campaign_type=CampaignType(get_val("campaign_type", 3, "email")),
                        status=CampaignStatus(get_val("status", 4, "draft")),
                        budget=float(get_val("budget", 11, 0)),
                        total_sent=get_val("total_sent", 14, 0),
                        revenue_generated=float(get_val("revenue_generated", 19, 0)),
                        roi=float(get_val("roi", 20, 0)),
                    )
                )

            return campaigns
        except Exception as e:
            self.logger.error(f"خطأ في سرد الحملات: {e}")
            return []

    def update_campaign_status(self, campaign_id: int, status: CampaignStatus):
        """تحديث حالة الحملة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE marketing_campaigns
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE campaign_id = ?
            """,
                (status.value, campaign_id),
            )

            conn.commit()
            self.logger.info(f"✅ تم تحديث حالة الحملة {campaign_id} إلى {status.value}")

        except Exception as e:
            conn.rollback()
            self.logger.error(f"خطأ في تحديث حالة الحملة: {e}")
            raise

    # ==================== تقسيم العملاء ====================

    def create_segment(self, segment: CustomerSegment) -> int:
        """إنشاء شريحة عملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            import json

            cursor.execute(
                """
                INSERT INTO customer_segments (
                    name, description, segment_type, filters
                ) VALUES (?, ?, ?, ?)
            """,
                (
                    segment.name,
                    segment.description,
                    segment.segment_type.value,
                    json.dumps(segment.filters) if segment.filters else None,
                ),
            )

            conn.commit()
            segment_id = cursor.lastrowid

            self.logger.info(f"✅ تم إنشاء شريحة عملاء: {segment.name}")
            return segment_id

        except Exception as e:
            conn.rollback()
            self.logger.error(f"خطأ في إنشاء شريحة العملاء: {e}")
            raise

    def get_segment_customers(self, segment_type: CustomerSegmentType) -> List[int]:
        """الحصول على معرفات العملاء في شريحة معينة"""
        cursor = self.db.get_cursor()

        if segment_type == CustomerSegmentType.ALL:
            cursor.execute("SELECT customer_id FROM customers WHERE is_active = 1")
            return [get_value(row, 'customer_id') for row in cursor.fetchall()]

        elif segment_type == CustomerSegmentType.NEW_CUSTOMERS:
            # العملاء الجدد خلال آخر 30 يوم
            cursor.execute("""
                SELECT customer_id FROM customers
                WHERE created_at >= datetime('now', '-30 days')
                AND is_active = 1
            """)
            return [get_value(row, 'customer_id') for row in cursor.fetchall()]

        elif segment_type == CustomerSegmentType.HIGH_VALUE:
            # العملاء ذوي القيمة العالية (أكثر من 10000)
            cursor.execute("""
                SELECT customer_id FROM customers
                WHERE total_purchases > 10000
                AND is_active = 1
                ORDER BY total_purchases DESC
            """)
            return [get_value(row, 'customer_id') for row in cursor.fetchall()]

        elif segment_type == CustomerSegmentType.INACTIVE:
            # العملاء غير النشطين (لم يشتروا منذ 90 يوم)
            cursor.execute("""
                SELECT c.customer_id FROM customers c
                WHERE NOT EXISTS (
                    SELECT 1 FROM invoices i
                    WHERE i.customer_id = c.customer_id
                    AND i.invoice_date >= datetime('now', '-90 days')
                )
                AND c.is_active = 1
            """)
            return [get_value(row, 'customer_id') for row in cursor.fetchall()]

        return []

    # ==================== التحليلات والمقاييس ====================

    def get_campaign_metrics(self, campaign_id: int) -> CampaignMetrics:
        """الحصول على مقاييس الحملة"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"الحملة {campaign_id} غير موجودة")

        # حساب المعدلات
        delivery_rate = (campaign.total_delivered / campaign.total_sent * 100) if campaign.total_sent > 0 else 0
        open_rate = (campaign.total_opened / campaign.total_delivered * 100) if campaign.total_delivered > 0 else 0
        click_rate = (campaign.total_clicked / campaign.total_opened * 100) if campaign.total_opened > 0 else 0
        conversion_rate = (campaign.total_converted / campaign.total_clicked * 100) if campaign.total_clicked > 0 else 0

        # حساب ROI
        roi = ((campaign.revenue_generated - campaign.budget) / campaign.budget * 100) if campaign.budget > 0 else 0

        # حساب تكلفة الاكتساب
        cost_per_acquisition = (campaign.budget / campaign.total_converted) if campaign.total_converted > 0 else 0

        # حساب المدة
        duration_days = 0
        if campaign.start_date and campaign.end_date:
            duration_days = (campaign.end_date - campaign.start_date).days

        return CampaignMetrics(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            delivery_rate=round(delivery_rate, 2),
            open_rate=round(open_rate, 2),
            click_rate=round(click_rate, 2),
            conversion_rate=round(conversion_rate, 2),
            total_budget=campaign.budget,
            total_revenue=campaign.revenue_generated,
            roi=round(roi, 2),
            cost_per_acquisition=round(cost_per_acquisition, 2),
            duration_days=duration_days,
            status=campaign.status,
        )

    def get_all_campaigns_summary(self) -> Dict[str, Any]:
        """ملخص جميع الحملات"""
        cursor = self.db.get_cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_campaigns,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_campaigns,
                SUM(budget) as total_budget,
                SUM(revenue_generated) as total_revenue,
                SUM(total_sent) as total_sent,
                SUM(total_converted) as total_conversions
            FROM marketing_campaigns
        """)

        row = cursor.fetchone()

        total_budget = get_value(row, 'total_budget', 0) or 0
        total_revenue = get_value(row, 'total_revenue', 0) or 0
        overall_roi = ((total_revenue - total_budget) / total_budget * 100) if total_budget > 0 else 0
        total_sent = get_value(row, 'total_sent', 0) or 0
        total_conversions = get_value(row, 'total_conversions', 0) or 0

        return {
            "total_campaigns": get_value(row, 'total_campaigns', 0) or 0,
            "active_campaigns": get_value(row, 'active_campaigns', 0) or 0,
            "total_budget": total_budget,
            "total_revenue": total_revenue,
            "overall_roi": round(overall_roi, 2),
            "total_sent": total_sent,
            "total_conversions": total_conversions,
            "average_conversion_rate": round((total_conversions / total_sent * 100) if total_sent > 0 else 0, 2),
        }

    # ==================== التواصل ====================

    def send_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """إرسال الحملة (محاكاة)"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"الحملة {campaign_id} غير موجودة")

        if campaign.status != CampaignStatus.SCHEDULED:
            raise ValueError("يجب أن تكون الحملة في حالة 'مجدولة' للإرسال")

        # الحصول على العملاء المستهدفين
        if campaign.target_customer_ids:
            customer_ids = campaign.target_customer_ids
        else:
            customer_ids = self.get_segment_customers(campaign.target_segment)

        # محاكاة الإرسال
        total_sent = len(customer_ids)
        total_delivered = int(total_sent * 0.95)  # 95% معدل توصيل
        total_opened = int(total_delivered * 0.25)  # 25% معدل فتح
        total_clicked = int(total_opened * 0.15)  # 15% معدل نقر
        total_converted = int(total_clicked * 0.05)  # 5% معدل تحويل

        # تحديث الحملة
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE marketing_campaigns
                SET status = 'active',
                    actual_reach = ?,
                    total_sent = ?,
                    total_delivered = ?,
                    total_opened = ?,
                    total_clicked = ?,
                    total_converted = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE campaign_id = ?
            """,
                (
                    total_sent,
                    total_sent,
                    total_delivered,
                    total_opened,
                    total_clicked,
                    total_converted,
                    campaign_id,
                ),
            )

            conn.commit()

            self.logger.info(f"✅ تم إرسال الحملة {campaign.name}: {total_sent} رسالة")

            return {
                "success": True,
                "campaign_id": campaign_id,
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "delivery_rate": round(total_delivered / total_sent * 100, 2),
            }

        except Exception as e:
            conn.rollback()
            self.logger.error(f"خطأ في إرسال الحملة: {e}")
            raise
