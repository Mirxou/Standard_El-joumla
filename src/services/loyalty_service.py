"""
نظام نقاط الولاء والمكافآت
Loyalty Points & Rewards System

Features:
- نقاط الولاء التلقائية على المشتريات
- برامج المكافآت
- العروض الخاصة للعملاء المميزين
- تتبع النقاط والاسترداد
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class LoyaltyTier:
    """مستوى الولاء"""
    name: str
    min_points: int
    benefits: List[str]
    discount_percentage: float


@dataclass
class LoyaltyTransaction:
    """معاملة نقاط الولاء"""
    customer_id: int
    points: int
    transaction_type: str  # 'earn' or 'redeem'
    order_id: Optional[int]
    notes: str
    timestamp: datetime


class LoyaltySystem:
    """نظام إدارة نقاط الولاء"""
    
    # مستويات الولاء
    TIERS = [
        LoyaltyTier("برونزي", 0, ["خصم 5%"], 5.0),
        LoyaltyTier("فضي", 500, ["خصم 10%", "شحن مجاني"], 10.0),
        LoyaltyTier("ذهبي", 1500, ["خصم 15%", "شحن مجاني", "عروض حصرية"], 15.0),
        LoyaltyTier("بلاتيني", 5000, ["خصم 20%", "شحن مجاني", "عروض حصرية", "أولوية الدعم"], 20.0)
    ]
    
    # نقاط لكل ريال/دولار
    POINTS_PER_CURRENCY = 1
    
    # ريال لكل نقطة عند الاسترداد
    REDEMPTION_RATE = 0.10
    
    def __init__(self, db_manager):
        """
        تهيئة نظام الولاء
        
        Args:
            db_manager: مدير قاعدة البيانات
        """
        self.db = db_manager
        self._create_tables()
    
    def _create_tables(self):
        """إنشاء جداول نقاط الولاء"""
        # جدول رصيد النقاط
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS loyalty_balance (
                customer_id INTEGER PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                lifetime_points INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'برونزي',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # جدول معاملات النقاط
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS loyalty_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                order_id INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # جدول العروض الخاصة
        self.db.execute_query('''
            CREATE TABLE IF NOT EXISTS loyalty_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                tier_required TEXT,
                discount_percentage REAL,
                points_required INTEGER,
                valid_from TEXT,
                valid_to TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.db.connection.commit()
    
    def earn_points(
        self, 
        customer_id: int, 
        purchase_amount: float,
        order_id: Optional[int] = None
    ) -> Dict:
        """
        كسب نقاط من عملية شراء
        
        Args:
            customer_id: معرف العميل
            purchase_amount: قيمة الشراء
            order_id: معرف الطلب
            
        Returns:
            معلومات النقاط المكتسبة
        """
        points = int(purchase_amount * self.POINTS_PER_CURRENCY)
        
        # تحديث الرصيد
        self.db.execute_query('''
            INSERT INTO loyalty_balance (customer_id, total_points, lifetime_points)
            VALUES (?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                total_points = total_points + ?,
                lifetime_points = lifetime_points + ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (customer_id, points, points, points, points))
        
        # تسجيل المعاملة
        self.db.execute_query('''
            INSERT INTO loyalty_transactions 
            (customer_id, points, transaction_type, order_id, notes)
            VALUES (?, ?, 'earn', ?, ?)
        ''', (customer_id, points, order_id, f"كسب {points} نقطة من شراء بقيمة {purchase_amount}"))
        
        # تحديث المستوى
        new_tier = self._update_tier(customer_id)
        
        self.db.connection.commit()
        
        return {
            "points_earned": points,
            "new_tier": new_tier,
            "message": f"تم إضافة {points} نقطة إلى حسابك!"
        }
    
    def redeem_points(
        self, 
        customer_id: int, 
        points: int,
        order_id: Optional[int] = None
    ) -> Dict:
        """
        استرداد النقاط للحصول على خصم
        
        Args:
            customer_id: معرف العميل
            points: عدد النقاط للاسترداد
            order_id: معرف الطلب
            
        Returns:
            معلومات الاسترداد
        """
        balance = self.get_balance(customer_id)
        
        if balance['total_points'] < points:
            raise ValueError(f"رصيد غير كافي. الرصيد الحالي: {balance['total_points']} نقطة")
        
        discount_amount = points * self.REDEMPTION_RATE
        
        # خصم النقاط
        self.db.execute_query('''
            UPDATE loyalty_balance
            SET total_points = total_points - ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = ?
        ''', (points, customer_id))
        
        # تسجيل المعاملة
        self.db.execute_query('''
            INSERT INTO loyalty_transactions 
            (customer_id, points, transaction_type, order_id, notes)
            VALUES (?, ?, 'redeem', ?, ?)
        ''', (customer_id, -points, order_id, f"استرداد {points} نقطة مقابل خصم {discount_amount}"))
        
        self.db.connection.commit()
        
        return {
            "points_redeemed": points,
            "discount_amount": discount_amount,
            "remaining_points": balance['total_points'] - points,
            "message": f"تم استرداد {points} نقطة مقابل خصم {discount_amount}"
        }
    
    def get_balance(self, customer_id: int) -> Dict:
        """الحصول على رصيد النقاط"""
        result = self.db.execute_query('''
            SELECT total_points, lifetime_points, tier, updated_at
            FROM loyalty_balance
            WHERE customer_id = ?
        ''', (customer_id,))
        
        if not result:
            return {
                "total_points": 0,
                "lifetime_points": 0,
                "tier": "برونزي",
                "tier_benefits": self.TIERS[0].benefits
            }
        
        row = result[0]
        tier_info = next((t for t in self.TIERS if t.name == row['tier']), self.TIERS[0])
        
        return {
            "total_points": row['total_points'],
            "lifetime_points": row['lifetime_points'],
            "tier": row['tier'],
            "tier_benefits": tier_info.benefits,
            "discount_percentage": tier_info.discount_percentage,
            "updated_at": row['updated_at']
        }
    
    def get_transactions(
        self, 
        customer_id: int, 
        limit: int = 20
    ) -> List[Dict]:
        """الحصول على سجل المعاملات"""
        result = self.db.execute_query('''
            SELECT id, points, transaction_type, order_id, notes, created_at
            FROM loyalty_transactions
            WHERE customer_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (customer_id, limit))
        
        transactions = []
        for row in result:
            transactions.append({
                "id": row['id'],
                "points": row['points'],
                "type": row['transaction_type'],
                "order_id": row['order_id'],
                "notes": row['notes'],
                "date": row['created_at']
            })
        
        return transactions
    
    def _update_tier(self, customer_id: int) -> str:
        """تحديث مستوى العميل بناءً على النقاط"""
        balance = self.get_balance(customer_id)
        lifetime_points = balance['lifetime_points']
        
        # تحديد المستوى المناسب
        new_tier = self.TIERS[0]
        for tier in reversed(self.TIERS):
            if lifetime_points >= tier.min_points:
                new_tier = tier
                break
        
        # تحديث في قاعدة البيانات
        result = self.db.execute_query('''
            UPDATE loyalty_balance
            SET tier = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE customer_id = ?
        ''', (new_tier.name, customer_id))
        
        self.db.connection.commit()
        
        return new_tier.name
    
    def create_special_offer(
        self,
        title: str,
        description: str,
        tier_required: str,
        discount_percentage: float = 0,
        points_required: int = 0,
        valid_days: int = 30
    ) -> int:
        """إنشاء عرض خاص"""
        valid_from = datetime.now().strftime('%Y-%m-%d')
        valid_to = (datetime.now() + timedelta(days=valid_days)).strftime('%Y-%m-%d')
        
        self.db.execute_query('''
            INSERT INTO loyalty_offers 
            (title, description, tier_required, discount_percentage, points_required, valid_from, valid_to)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, tier_required, discount_percentage, points_required, valid_from, valid_to))
        
        return 1  # Success
    
    def get_active_offers(self, tier: str) -> List[Dict]:
        """الحصول على العروض النشطة للمستوى المحدد"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = self.db.execute_query('''
            SELECT id, title, description, discount_percentage, points_required, valid_from, valid_to
            FROM loyalty_offers
            WHERE is_active = 1
                AND tier_required <= ?
                AND valid_from <= ?
                AND valid_to >= ?
            ORDER BY created_at DESC
        ''', (tier, today, today))
        
        offers = []
        for row in result:
            offers.append({
                "id": row['id'],
                "title": row['title'],
                "description": row['description'],
                "discount_percentage": row['discount_percentage'],
                "points_required": row['points_required'],
                "valid_from": row['valid_from'],
                "valid_to": row['valid_to']
            })
        
        return offers


if __name__ == "__main__":
    print("🎁 Loyalty System Test")
    print("=" * 50)
    print("✅ Module loaded successfully!")
    print("\nLoyalty Tiers:")
    for tier in LoyaltySystem.TIERS:
        print(f"  {tier.name}: {tier.min_points}+ points, {tier.discount_percentage}% discount")

