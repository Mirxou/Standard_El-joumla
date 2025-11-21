"""
Mobile API Endpoints
نقاط نهاية API خاصة بتطبيق الموبايل
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..auth import get_current_user, require_role

router = APIRouter(prefix="/mobile", tags=["mobile"])


# ==========================================
# Pydantic Models
# ==========================================

class DashboardResponse(BaseModel):
    """Dashboard data for mobile app"""
    today_sales: float
    pending_orders: int
    low_stock_count: int
    new_customers_today: int
    sales_trend: List[dict]
    top_products: List[dict]


class QuickSaleRequest(BaseModel):
    """Quick sale creation from mobile"""
    customer_id: int
    items: List[dict]
    payment_method: str
    location: Optional[dict] = None  # GPS coordinates
    signature: Optional[str] = None  # Base64 encoded signature


class SyncRequest(BaseModel):
    """Offline data sync request"""
    pending_sales: List[dict]
    pending_customers: List[dict]
    inventory_counts: List[dict]
    last_sync_timestamp: datetime


# ==========================================
# Dashboard Endpoints
# ==========================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_mobile_dashboard(
    user: dict = Depends(get_current_user)
):
    """
    Get dashboard data optimized for mobile
    
    Returns:
    - Today's sales total
    - Pending orders count
    - Low stock alerts
    - New customers today
    - Sales trend (last 7 days)
    - Top 5 products
    """
    from ...core.database_manager import DatabaseManager
    from datetime import date
    
    db = DatabaseManager()
    today = date.today()
    
    # Today's sales
    today_sales = db.execute_query(
        """
        SELECT COALESCE(SUM(total_amount), 0) as total
        FROM sales
        WHERE DATE(date) = ?
        """,
        (today,)
    )
    
    # Pending orders
    pending = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM sales
        WHERE status IN ('pending', 'processing')
        """
    )
    
    # Low stock products
    low_stock = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM products
        WHERE stock <= min_stock
        """
    )
    
    # New customers today
    new_customers = db.execute_query(
        """
        SELECT COUNT(*) as count
        FROM customers
        WHERE DATE(created_at) = ?
        """,
        (today,)
    )
    
    # Sales trend (last 7 days)
    sales_trend_data = db.execute_query(
        """
        SELECT DATE(date) as day, SUM(total_amount) as total
        FROM sales
        WHERE date >= DATE('now', '-7 days')
        GROUP BY DATE(date)
        ORDER BY day
        """
    )
    
    sales_trend = [
        {"date": row[0], "amount": row[1]}
        for row in sales_trend_data
    ]
    
    # Top 5 products
    top_products_data = db.execute_query(
        """
        SELECT 
            p.id,
            p.name,
            SUM(si.quantity) as total_sold,
            SUM(si.quantity * si.unit_price) as revenue
        FROM products p
        JOIN sale_items si ON p.id = si.product_id
        JOIN sales s ON si.sale_id = s.id
        WHERE s.date >= DATE('now', '-30 days')
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
        """
    )
    
    top_products = [
        {
            "id": row[0],
            "name": row[1],
            "quantity_sold": row[2],
            "revenue": row[3]
        }
        for row in top_products_data
    ]
    
    return DashboardResponse(
        today_sales=today_sales[0][0] if today_sales else 0,
        pending_orders=pending[0][0] if pending else 0,
        low_stock_count=low_stock[0][0] if low_stock else 0,
        new_customers_today=new_customers[0][0] if new_customers else 0,
        sales_trend=sales_trend,
        top_products=top_products
    )


# ==========================================
# Quick Sale (Field Sales)
# ==========================================

@router.post("/quick-sale")
async def create_quick_sale(
    sale_data: QuickSaleRequest,
    user: dict = Depends(get_current_user)
):
    """
    Create a sale quickly from mobile (field sales)
    
    Features:
    - Minimal required fields
    - GPS location tracking
    - Digital signature support
    - Offline sync friendly
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    try:
        # Calculate total
        total = sum(
            item['quantity'] * item['unit_price']
            for item in sale_data.items
        )
        
        # Create sale
        sale_id = db.execute_query(
            """
            INSERT INTO sales (
                customer_id, user_id, total_amount,
                payment_method, status, date,
                gps_location, customer_signature
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sale_data.customer_id,
                user['user_id'],
                total,
                sale_data.payment_method,
                'completed',
                datetime.now(),
                str(sale_data.location) if sale_data.location else None,
                sale_data.signature
            ),
            commit=True
        )
        
        # Add sale items
        for item in sale_data.items:
            db.execute_query(
                """
                INSERT INTO sale_items (
                    sale_id, product_id, quantity, unit_price
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    sale_id,
                    item['product_id'],
                    item['quantity'],
                    item['unit_price']
                ),
                commit=True
            )
            
            # Update stock
            db.execute_query(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                """,
                (item['quantity'], item['product_id']),
                commit=True
            )
        
        return {
            "success": True,
            "sale_id": sale_id,
            "total_amount": total,
            "message": "Sale created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create sale: {str(e)}"
        )


# ==========================================
# Barcode Scanner
# ==========================================

@router.get("/barcode/{barcode}")
async def scan_barcode(
    barcode: str,
    user: dict = Depends(get_current_user)
):
    """
    Lookup product by barcode
    
    Returns product details and stock availability
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    product = db.execute_query(
        """
        SELECT 
            id, name, sku, price, cost, stock,
            min_stock, category, description
        FROM products
        WHERE barcode = ? OR sku = ?
        """,
        (barcode, barcode)
    )
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    
    p = product[0]
    
    return {
        "id": p[0],
        "name": p[1],
        "sku": p[2],
        "price": p[3],
        "cost": p[4],
        "stock": p[5],
        "min_stock": p[6],
        "category": p[7],
        "description": p[8],
        "in_stock": p[5] > 0,
        "low_stock": p[5] <= p[6]
    }


# ==========================================
# Offline Sync
# ==========================================

@router.post("/sync/upload")
async def upload_offline_data(
    sync_data: SyncRequest,
    user: dict = Depends(get_current_user)
):
    """
    Upload offline data from mobile
    
    Handles:
    - Pending sales created offline
    - New customers added offline
    - Inventory counts performed offline
    
    Returns conflict resolution if needed
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    results = {
        "sales_synced": 0,
        "customers_synced": 0,
        "inventory_synced": 0,
        "conflicts": []
    }
    
    try:
        # Sync pending sales
        for sale in sync_data.pending_sales:
            try:
                # Check for duplicates by temp_id
                existing = db.execute_query(
                    "SELECT id FROM sales WHERE temp_id = ?",
                    (sale.get('temp_id'),)
                )
                
                if existing:
                    results['conflicts'].append({
                        "type": "sale",
                        "temp_id": sale.get('temp_id'),
                        "status": "duplicate"
                    })
                    continue
                
                # Create sale
                sale_id = db.execute_query(
                    """
                    INSERT INTO sales (
                        customer_id, user_id, total_amount,
                        payment_method, status, date, temp_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sale['customer_id'],
                        user['user_id'],
                        sale['total_amount'],
                        sale['payment_method'],
                        'completed',
                        sale['date'],
                        sale.get('temp_id')
                    ),
                    commit=True
                )
                
                results['sales_synced'] += 1
                
            except Exception as e:
                results['conflicts'].append({
                    "type": "sale",
                    "temp_id": sale.get('temp_id'),
                    "error": str(e)
                })
        
        # Sync new customers
        for customer in sync_data.pending_customers:
            try:
                # Check for duplicates by phone
                existing = db.execute_query(
                    "SELECT id FROM customers WHERE phone = ?",
                    (customer['phone'],)
                )
                
                if existing:
                    results['conflicts'].append({
                        "type": "customer",
                        "phone": customer['phone'],
                        "status": "duplicate"
                    })
                    continue
                
                # Create customer
                db.execute_query(
                    """
                    INSERT INTO customers (
                        name, phone, email, address
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        customer['name'],
                        customer['phone'],
                        customer.get('email'),
                        customer.get('address')
                    ),
                    commit=True
                )
                
                results['customers_synced'] += 1
                
            except Exception as e:
                results['conflicts'].append({
                    "type": "customer",
                    "phone": customer.get('phone'),
                    "error": str(e)
                })
        
        # Sync inventory counts
        for count in sync_data.inventory_counts:
            try:
                # Update stock
                db.execute_query(
                    """
                    UPDATE products
                    SET stock = ?
                    WHERE id = ?
                    """,
                    (count['counted_quantity'], count['product_id']),
                    commit=True
                )
                
                results['inventory_synced'] += 1
                
            except Exception as e:
                results['conflicts'].append({
                    "type": "inventory",
                    "product_id": count.get('product_id'),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results,
            "sync_timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/sync/download")
async def download_sync_data(
    since: datetime = Query(..., description="Last sync timestamp"),
    user: dict = Depends(get_current_user)
):
    """
    Download updated data for offline use
    
    Returns:
    - Products updated since last sync
    - Customers updated since last sync
    - Price changes
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    # Updated products
    products = db.execute_query(
        """
        SELECT id, name, sku, price, stock, barcode, category
        FROM products
        WHERE updated_at > ?
        """,
        (since,)
    )
    
    # Updated customers
    customers = db.execute_query(
        """
        SELECT id, name, phone, email, address
        FROM customers
        WHERE updated_at > ?
        """,
        (since,)
    )
    
    return {
        "products": [
            {
                "id": p[0],
                "name": p[1],
                "sku": p[2],
                "price": p[3],
                "stock": p[4],
                "barcode": p[5],
                "category": p[6]
            }
            for p in products
        ],
        "customers": [
            {
                "id": c[0],
                "name": c[1],
                "phone": c[2],
                "email": c[3],
                "address": c[4]
            }
            for c in customers
        ],
        "sync_timestamp": datetime.now()
    }


# ==========================================
# Notifications
# ==========================================

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """
    Get user notifications for mobile app
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    query = """
        SELECT 
            id, title, message, type, is_read,
            created_at, action_url
        FROM notifications
        WHERE user_id = ?
    """
    
    if unread_only:
        query += " AND is_read = 0"
    
    query += " ORDER BY created_at DESC LIMIT ?"
    
    notifications = db.execute_query(
        query,
        (user['user_id'], limit)
    )
    
    return [
        {
            "id": n[0],
            "title": n[1],
            "message": n[2],
            "type": n[3],
            "is_read": bool(n[4]),
            "created_at": n[5],
            "action_url": n[6]
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: int,
    user: dict = Depends(get_current_user)
):
    """Mark notification as read"""
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    db.execute_query(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE id = ? AND user_id = ?
        """,
        (notification_id, user['user_id']),
        commit=True
    )
    
    return {"success": True}


# ==========================================
# Location Tracking
# ==========================================

@router.post("/location/track")
async def track_location(
    latitude: float,
    longitude: float,
    accuracy: Optional[float] = None,
    user: dict = Depends(get_current_user)
):
    """
    Track user location (for field sales)
    
    Records GPS coordinates with timestamp
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    db.execute_query(
        """
        INSERT INTO user_locations (
            user_id, latitude, longitude,
            accuracy, recorded_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user['user_id'],
            latitude,
            longitude,
            accuracy,
            datetime.now()
        ),
        commit=True
    )
    
    return {
        "success": True,
        "message": "Location recorded"
    }


@router.get("/location/nearby-customers")
async def get_nearby_customers(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    user: dict = Depends(get_current_user)
):
    """
    Find customers within radius
    
    Uses Haversine formula for distance calculation
    """
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    # Simple distance calculation (for SQLite)
    # Note: In production, use PostGIS or similar for accurate geo queries
    customers = db.execute_query(
        """
        SELECT 
            id, name, phone, address,
            gps_latitude, gps_longitude,
            (
                6371 * acos(
                    cos(radians(?)) * cos(radians(gps_latitude)) *
                    cos(radians(gps_longitude) - radians(?)) +
                    sin(radians(?)) * sin(radians(gps_latitude))
                )
            ) AS distance_km
        FROM customers
        WHERE gps_latitude IS NOT NULL
        HAVING distance_km <= ?
        ORDER BY distance_km
        LIMIT 20
        """,
        (latitude, longitude, latitude, radius_km)
    )
    
    return [
        {
            "id": c[0],
            "name": c[1],
            "phone": c[2],
            "address": c[3],
            "latitude": c[4],
            "longitude": c[5],
            "distance_km": round(c[6], 2)
        }
        for c in customers
    ]
