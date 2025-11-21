#!/usr/bin/env python3
"""
FastAPI application layer providing secure REST endpoints.
Integrates with existing UserService (JWT) and DatabaseManager.
Security v2.0: Rate limiting, refresh tokens, i18n support
"""
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
import json
import hashlib

from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from ..core.database_manager import DatabaseManager
from ..services.user_service import UserService
from ..services.vendor_rating_service import VendorRatingService, SupplierEvaluation

try:
    from ..services.vendor_service import VendorService
except ImportError:
    VendorService = None

try:
    from ..services.sales_service_enhanced import SalesService
except ImportError:
    SalesService = None

try:
    from ..services.inventory_service_enhanced import InventoryService, StockMovement, MovementType
except ImportError:
    InventoryService = None
    StockMovement = None
    MovementType = None

try:
    from ..services.reports_service import ReportsService, ReportFilter, ExportFormat, ReportType
except ImportError:
    ReportsService = None
    ReportFilter = None
    ExportFormat = None
    ReportType = None

try:
    from ..services.purchase_order_service import PurchaseOrderService
except ImportError:
    PurchaseOrderService = None

try:
    from ..security.rate_limiter import login_rate_limiter, api_rate_limiter
except ImportError:
    login_rate_limiter = None
    api_rate_limiter = None

try:
    from ..utils.i18n_api import I18n
    i18n = I18n()
except ImportError:
    i18n = None

try:
    from ..ai.chatbot import chatbot
    from ..ai.predictive_analytics import PredictiveEngine
except ImportError:
    chatbot = None
    PredictiveEngine = None

try:
    from ..services.loyalty_service import LoyaltySystem
except ImportError:
    LoyaltySystem = None

try:
    from ..services.einvoice_service import EInvoiceGenerator, EInvoiceConfig, RecurringInvoiceManager
except ImportError:
    EInvoiceGenerator = None
    EInvoiceConfig = None
    RecurringInvoiceManager = None

try:
    from ..services.vendor_portal import VendorPortal
except ImportError:
    VendorPortal = None

try:
    from ..services.marketing_service import MarketingService
except ImportError:
    MarketingService = None

try:
    from ..security.mfa_service import MFAService, MFAMethod
except ImportError:
    MFAService = None
    MFAMethod = None


app = FastAPI(title="Logical Version API", version="3.5.2")

# Register mobile API routes
try:
    from .routes import mobile_router
    app.include_router(mobile_router)
except ImportError:
    pass

db_manager: Optional[DatabaseManager] = None
user_service: Optional[UserService] = None
vendor_rating_service: Optional[VendorRatingService] = None
vendor_crud_service: Optional['VendorService'] = None
sales_service: Optional[SalesService] = None
inventory_service: Optional['InventoryService'] = None
reports_service: Optional['ReportsService'] = None
purchase_order_service: Optional['PurchaseOrderService'] = None
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int


class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    has_next: bool


# --------------------------- Products Schemas ---------------------------
class ProductCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    unit: str = Field(default="قطعة")
    cost_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    min_stock: Optional[int] = Field(default=0, ge=0)
    current_stock: Optional[int] = Field(default=0, ge=0)
    description: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True


class VariantCreate(BaseModel):
    sku: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    barcode: Optional[str] = None
    cost_price: Optional[float] = Field(default=None, ge=0)
    selling_price: Optional[float] = Field(default=None, ge=0)
    current_stock: Optional[int] = Field(default=0, ge=0)
    is_active: bool = True


# --------------------------- Bundles/Pricing/Tags Schemas ---------------------------
class BundleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class BundleItemCreate(BaseModel):
    item_type: Literal['product', 'variant']
    item_product_id: Optional[int] = None
    item_variant_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1)


class PriceCreate(BaseModel):
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    price_type: Literal['retail','wholesale','customer_group'] = Field(default='retail')
    customer_group: Optional[str] = None
    min_qty: int = Field(default=1, ge=1)
    price: float = Field(gt=0)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class TagRequest(BaseModel):
    tag: str


# --------------------------- Sales & Customer Schemas ---------------------------
class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[float] = Field(default=0, ge=0)
    is_active: bool = True


class SaleItemCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    discount: Optional[float] = Field(default=0, ge=0)



class SaleOrderCreate(BaseModel):
    customer_id: int
    items: List[SaleItemCreate]
    notes: Optional[str] = None
    payment_method: str = Field(default="نقدي")

class QuoteCreate(BaseModel):
    customer_id: int
    items: List[SaleItemCreate]
    valid_until: Optional[str] = None
    notes: Optional[str] = None

# ================= Purchase Order Schemas (v1.8.0) =================
class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    product_name: Optional[str] = None
    quantity_ordered: float = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_percent: Optional[float] = Field(default=0, ge=0)
    tax_percent: Optional[float] = Field(default=0, ge=0)
    required_date: Optional[str] = None

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    required_date: Optional[str] = None
    currency: str = Field(default="DZD")
    notes: Optional[str] = None
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderStatusUpdate(BaseModel):
    po_id: int
    new_status: str

class ReceivingItemCreate(BaseModel):
    po_item_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity_received: float = Field(gt=0)
    quantity_accepted: float = Field(gt=0)
    quantity_rejected: Optional[float] = Field(default=0, ge=0)
    warehouse_location: Optional[str] = None
    notes: Optional[str] = None

class ReceiveShipmentRequest(BaseModel):
    po_id: int
    items: List[ReceivingItemCreate]
    notes: Optional[str] = None



# --------------------------- Inventory Schemas ---------------------------
class StockTransferRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    from_location: str
    to_location: str
    notes: Optional[str] = None


class StockReservationRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    reference_id: Optional[int] = None
    reference_type: str = Field(default="order")


class InventoryCountCreate(BaseModel):
    location: str
    notes: Optional[str] = None


class InventoryCountItemCreate(BaseModel):
    product_id: int
    counted_quantity: int = Field(ge=0)


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    movement_type: str
    quantity: int
    reference_id: Optional[int]
    reference_type: Optional[str]
    notes: Optional[str]


# --------------------------- Vendor Management Schemas ---------------------------
class VendorCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms: str = "نقدي"
    credit_limit: float = Field(default=0.0, ge=0)


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = Field(default=None, ge=0)


class VendorEvaluationCreate(BaseModel):
    supplier_id: int
    evaluation_period_start: Optional[str] = None
    evaluation_period_end: Optional[str] = None
    quality_score: float = Field(ge=0, le=5)
    delivery_score: float = Field(ge=0, le=5)
    pricing_score: float = Field(ge=0, le=5)
    communication_score: float = Field(ge=0, le=5)
    reliability_score: float = Field(ge=0, le=5)
    total_orders: int = Field(default=0, ge=0)
    completed_orders: int = Field(default=0, ge=0)
    on_time_deliveries: int = Field(default=0, ge=0)
    late_deliveries: int = Field(default=0, ge=0)
    rejected_shipments: int = Field(default=0, ge=0)
    total_value: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    is_approved: bool = True
    is_preferred: bool = False
    from_location: Optional[str]
    to_location: Optional[str]
    created_at: str


def get_services():
    global db_manager, user_service, vendor_rating_service, vendor_crud_service, sales_service, inventory_service, reports_service, purchase_order_service
    if db_manager is None:
        db = DatabaseManager()
        db.initialize()
        us = UserService(db)
        vr_s = VendorRatingService(db)
        vc_s = VendorService(db) if VendorService else None
        ss = SalesService(db) if SalesService else None
        inv_s = InventoryService(db) if InventoryService else None
        rp_s = ReportsService(db) if ReportsService else None
        po_s = PurchaseOrderService(db) if PurchaseOrderService else None
        return db, us, vr_s, vc_s, ss, inv_s, rp_s, po_s
    return db_manager, user_service, vendor_rating_service, vendor_crud_service, sales_service, inventory_service, reports_service, purchase_order_service


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Dict[str, Any]:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    _, us, _, _, _, _, _, _ = get_services()
    payload = us.verify_jwt_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


@app.on_event("startup")
async def startup_event():
    global db_manager, user_service, vendor_rating_service, vendor_crud_service, sales_service, inventory_service, reports_service
    if db_manager is None:
        db_manager, user_service, vendor_rating_service, vendor_crud_service, sales_service, inventory_service, reports_service, purchase_order_service = get_services()


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, accept_language: Optional[str] = Header(None)):
    # Rate limiting for login attempts
    if login_rate_limiter:
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining = login_rate_limiter.is_allowed(client_ip)
        if not allowed:
            detail = "Rate limit exceeded. Please try again later."
            if i18n:
                locale = i18n.negotiate_locale(accept_language)
                detail = i18n.get_message("rate_limit_exceeded", locale)
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
    
    db, us, _, _, _, _, _, _ = get_services()
    ok, session, msg = us.authenticate_user(req.username, req.password)
    if not ok or not session:
        detail = msg or "Authentication failed"
        if i18n:
            locale = i18n.negotiate_locale(accept_language)
            detail = i18n.get_message("authentication_failed", locale)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
    # Issue JWT
    user = us.user_manager.get_user_by_username(req.username)
    token = us.generate_jwt_token(user)
    return TokenResponse(access_token=token, expires_in_hours=us.security_settings.jwt_expiry_hours)


@app.get("/customers", response_model=PaginatedResponse)
def list_customers(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM customers")
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT id, name, phone, email, current_balance, created_at FROM customers ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        rows = cur.fetchall()
        items = [dict(row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)


@app.get("/products", response_model=PaginatedResponse)
def list_products(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), tag: Optional[str] = Query(default=None), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    with db.get_cursor() as cur:
        if tag:
            cur.execute(
                "SELECT COUNT(*) FROM products p JOIN product_tags t ON p.id = t.product_id WHERE t.tag = ?",
                (tag,)
            )
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT p.id, p.name, p.barcode, p.unit, p.selling_price AS sale_price, p.current_stock AS stock_quantity "
                "FROM products p JOIN product_tags t ON p.id = t.product_id WHERE t.tag = ? "
                "ORDER BY p.id DESC LIMIT ? OFFSET ?",
                (tag, page_size, offset)
            )
        else:
            cur.execute("SELECT COUNT(*) FROM products")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT id, name, barcode, unit, selling_price AS sale_price, current_stock AS stock_quantity FROM products ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            )
        rows = cur.fetchall()
        items = [dict(row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)


@app.post("/products", status_code=201)
def create_product(req: ProductCreate, user=Depends(get_current_user)):
    # RBAC: only admin can create products
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to create product")

    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO products(name, name_en, barcode, category_id, unit, cost_price, selling_price,
                                 min_stock, current_stock, description, image_path, is_active, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                req.name, req.name_en, req.barcode, req.category_id, req.unit,
                req.cost_price, req.selling_price, req.min_stock, req.current_stock,
                req.description, req.image_path, 1 if req.is_active else 0
            )
        )
        new_id = cur.lastrowid
        if req.barcode:
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO product_barcodes(product_id, barcode, is_primary) VALUES(?,?,1)",
                    (new_id, req.barcode)
                )
            except Exception:
                pass
        # commit
        cur.connection.commit()
    return {"id": new_id}


@app.get("/products/{product_id}")
def get_product_detail(product_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT id, name, name_en, barcode, unit, cost_price, selling_price, min_stock, current_stock, description, image_path, is_active, created_at, updated_at FROM products WHERE id=?",
            (product_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        product = {
            "id": row[0],
            "name": row[1],
            "name_en": row[2],
            "barcode": row[3],
            "unit": row[4],
            "cost_price": row[5],
            "selling_price": row[6],
            "min_stock": row[7],
            "current_stock": row[8],
            "description": row[9],
            "image_path": row[10],
            "is_active": bool(row[11]),
            "created_at": row[12],
            "updated_at": row[13]
        }
        # variants
        cur.execute(
            "SELECT id, sku, attributes, barcode, cost_price, selling_price, current_stock, is_active FROM product_variants WHERE product_id=? ORDER BY id DESC",
            (product_id,)
        )
        vars_rows = cur.fetchall()
        variants: List[Dict[str, Any]] = []
        for vr in vars_rows:
            attrs: Optional[Dict[str, Any]] = None
            try:
                attrs = json.loads(vr[2]) if vr[2] else None
            except Exception:
                attrs = None
            variants.append({
                "id": vr[0], "sku": vr[1], "attributes": attrs, "barcode": vr[3],
                "cost_price": vr[4], "selling_price": vr[5], "current_stock": vr[6], "is_active": bool(vr[7])
            })
        # barcodes
        cur.execute(
            "SELECT barcode, barcode_type, is_primary FROM product_barcodes WHERE product_id=? ORDER BY is_primary DESC, id ASC",
            (product_id,)
        )
        codes = [
            {"barcode": r[0], "type": r[1], "is_primary": bool(r[2])}
            for r in cur.fetchall()
        ]
    product["variants"] = variants
    product["barcodes"] = codes
    return product


@app.post("/products/{product_id}/variants", status_code=201)
def create_product_variant(product_id: int, req: VariantCreate, user=Depends(get_current_user)):
    # RBAC: only admin can create variants
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to create variant")

    db, _, _, _, _, _, _, _ = get_services()
    # ensure product exists
    with db.get_cursor() as cur:
        cur.execute("SELECT id FROM products WHERE id=?", (product_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")
        attrs_json = json.dumps(req.attributes, ensure_ascii=False) if req.attributes else None
        cur.execute(
            """
            INSERT INTO product_variants(product_id, sku, attributes, barcode, cost_price, selling_price, current_stock, is_active,
                                         created_at, updated_at)
            VALUES(?,?,?,?,?,?,?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                product_id, req.sku, attrs_json, req.barcode, req.cost_price, req.selling_price,
                req.current_stock or 0, 1 if req.is_active else 0
            )
        )
        new_id = cur.lastrowid
        if req.barcode:
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO product_barcodes(variant_id, barcode, is_primary) VALUES(?,?,0)",
                    (new_id, req.barcode)
                )
            except Exception:
                pass
        cur.connection.commit()
    return {"id": new_id, "product_id": product_id}


# --------------------------- Bundles API ---------------------------
@app.post("/products/{product_id}/bundles", status_code=201)
def create_bundle(product_id: int, req: BundleCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to create bundle")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        # ensure product exists
        cur.execute("SELECT id FROM products WHERE id=?", (product_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")
        cur.execute(
            """
            INSERT INTO product_bundles(product_id, name, description, is_active, created_at, updated_at)
            VALUES(?,?,?,?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (product_id, req.name, req.description, 1 if req.is_active else 0)
        )
        bundle_id = cur.lastrowid
        cur.connection.commit()
    return {"id": bundle_id, "product_id": product_id}


@app.post("/bundles/{bundle_id}/items", status_code=201)
def add_bundle_item(bundle_id: int, req: BundleItemCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to modify bundle")
    if req.item_type == 'product' and not req.item_product_id:
        raise HTTPException(status_code=400, detail="item_product_id is required for product type")
    if req.item_type == 'variant' and not req.item_variant_id:
        raise HTTPException(status_code=400, detail="item_variant_id is required for variant type")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        # ensure bundle exists
        cur.execute("SELECT id FROM product_bundles WHERE id=?", (bundle_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Bundle not found")
        cur.execute(
            """
            INSERT INTO product_bundle_items(bundle_id, item_type, item_product_id, item_variant_id, quantity, created_at)
            VALUES(?,?,?,?,?, CURRENT_TIMESTAMP)
            """,
            (bundle_id, req.item_type, req.item_product_id, req.item_variant_id, req.quantity)
        )
        item_id = cur.lastrowid
        cur.connection.commit()
    return {"id": item_id, "bundle_id": bundle_id}


@app.get("/bundles", response_model=PaginatedResponse)
def list_bundles(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product_bundles")
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT id, product_id, name, description, is_active, created_at FROM product_bundles ORDER BY id DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        rows = cur.fetchall()
        items = [dict(row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)


@app.get("/bundles/{bundle_id}")
def get_bundle_detail(bundle_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("SELECT id, product_id, name, description, is_active, created_at, updated_at FROM product_bundles WHERE id=?", (bundle_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Bundle not found")
        bundle = {
            "id": row[0],
            "product_id": row[1],
            "name": row[2],
            "description": row[3],
            "is_active": bool(row[4]),
            "created_at": row[5],
            "updated_at": row[6]
        }
        cur.execute(
            "SELECT id, item_type, item_product_id, item_variant_id, quantity FROM product_bundle_items WHERE bundle_id=? ORDER BY id ASC",
            (bundle_id,)
        )
        bundle["items"] = [
            {"id": r[0], "item_type": r[1], "item_product_id": r[2], "item_variant_id": r[3], "quantity": r[4]}
            for r in cur.fetchall()
        ]
    return bundle


@app.delete("/bundles/{bundle_id}/items/{item_id}", status_code=204)
def delete_bundle_item(bundle_id: int, item_id: int, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("DELETE FROM product_bundle_items WHERE id=? AND bundle_id=?", (item_id, bundle_id))
        cur.connection.commit()
    return None


# --------------------------- Pricing API ---------------------------
@app.post("/prices", status_code=201)
def create_price(req: PriceCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to create price tier")
    if not req.product_id and not req.variant_id:
        raise HTTPException(status_code=400, detail="product_id or variant_id is required")
    if req.price_type == 'customer_group' and not req.customer_group:
        raise HTTPException(status_code=400, detail="customer_group is required for price_type=customer_group")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO product_prices(product_id, variant_id, price_type, customer_group, min_qty, price, valid_from, valid_to, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (req.product_id, req.variant_id, req.price_type, req.customer_group, req.min_qty, req.price, req.valid_from, req.valid_to)
        )
        price_id = cur.lastrowid
        cur.connection.commit()
    return {"id": price_id}


@app.get("/products/{product_id}/prices")
def list_product_prices(product_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT id, price_type, customer_group, min_qty, price, valid_from, valid_to FROM product_prices WHERE product_id=? ORDER BY min_qty ASC, id ASC",
            (product_id,)
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.get("/variants/{variant_id}/prices")
def list_variant_prices(variant_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT id, price_type, customer_group, min_qty, price, valid_from, valid_to FROM product_prices WHERE variant_id=? ORDER BY min_qty ASC, id ASC",
            (variant_id,)
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]


@app.delete("/prices/{price_id}", status_code=204)
def delete_price(price_id: int, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("DELETE FROM product_prices WHERE id=?", (price_id,))
        cur.connection.commit()
    return None


# --------------------------- Tags API ---------------------------
@app.post("/products/{product_id}/tags", status_code=201)
def add_product_tag(product_id: int, req: TagRequest, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("SELECT id FROM products WHERE id=?", (product_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")
        cur.execute(
            "INSERT OR IGNORE INTO product_tags(product_id, tag, created_at) VALUES(?,?, CURRENT_TIMESTAMP)",
            (product_id, req.tag)
        )
        cur.connection.commit()
    return {"product_id": product_id, "tag": req.tag}


@app.get("/products/{product_id}/tags")
def list_product_tags(product_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("SELECT tag FROM product_tags WHERE product_id=? ORDER BY tag ASC", (product_id,))
        tags = [r[0] for r in cur.fetchall()]
    return {"product_id": product_id, "tags": tags}


@app.delete("/products/{product_id}/tags/{tag}", status_code=204)
def delete_product_tag(product_id: int, tag: str, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute("DELETE FROM product_tags WHERE product_id=? AND tag=?", (product_id, tag))
        cur.connection.commit()
    return None


@app.get("/invoices", response_model=PaginatedResponse)
def list_invoices(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM invoices")
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT id, invoice_number, customer_id, total_amount, status, invoice_date FROM invoices ORDER BY invoice_date DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        rows = cur.fetchall()
        items = [dict(row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)


# --------------------------- Supplier Ratings API ---------------------------
class SupplierEvalRequest(BaseModel):
    quality_score: float
    delivery_score: float
    pricing_score: float
    communication_score: float
    reliability_score: float
    evaluation_period_start: Optional[str] = None
    evaluation_period_end: Optional[str] = None
    total_orders: int = 0
    completed_orders: int = 0
    on_time_deliveries: int = 0
    late_deliveries: int = 0
    rejected_shipments: int = 0
    total_value: float = 0.0
    on_time_delivery_rate: float = 0.0
    quality_acceptance_rate: float = 0.0
    average_lead_time_days: float = 0.0
    notes: Optional[str] = None
    recommendations: Optional[str] = None
    evaluation_date: Optional[str] = None


@app.get("/suppliers/{supplier_id}/rating")
def get_supplier_rating(supplier_id: int, user=Depends(get_current_user)):
    _, _, vr_s, _, _, _, _, _ = get_services()
    res = vr_s.get_supplier_score(supplier_id)
    if not res:
        raise HTTPException(status_code=404, detail="No evaluation found")
    return res


@app.post("/suppliers/{supplier_id}/evaluations", status_code=201)
def create_supplier_evaluation(supplier_id: int, req: SupplierEvalRequest, user=Depends(get_current_user)):
    # RBAC: allow only admin users to create evaluations
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges to create supplier evaluation")

    db, _, vr_s, _, _, _, _, _ = get_services()
    # Fetch supplier name if available
    with db.get_cursor() as cur:
        cur.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
        row = cur.fetchone()
        supplier_name = row[0] if row else None

    ev = SupplierEvaluation(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        evaluation_period_start=req.evaluation_period_start,
        evaluation_period_end=req.evaluation_period_end,
        quality_score=req.quality_score,
        delivery_score=req.delivery_score,
        pricing_score=req.pricing_score,
        communication_score=req.communication_score,
        reliability_score=req.reliability_score,
        total_orders=req.total_orders,
        completed_orders=req.completed_orders,
        on_time_deliveries=req.on_time_deliveries,
        late_deliveries=req.late_deliveries,
        rejected_shipments=req.rejected_shipments,
        total_value=req.total_value,
        on_time_delivery_rate=req.on_time_delivery_rate,
        quality_acceptance_rate=req.quality_acceptance_rate,
        average_lead_time_days=req.average_lead_time_days,
        notes=req.notes,
        recommendations=req.recommendations,
        evaluated_by=user.get("user_id"),
        evaluation_date=req.evaluation_date,
    )
    new_id = vr_s.create_evaluation(ev)
    return {"id": new_id, "supplier_id": supplier_id}


# --------------------------- Customers API ---------------------------
@app.post("/customers", status_code=201)
def create_customer(req: CustomerCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO customers(name, phone, email, address, credit_limit, current_balance, is_active, created_at, updated_at)
            VALUES(?,?,?,?,?, 0, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (req.name, req.phone, req.email, req.address, req.credit_limit, 1 if req.is_active else 0)
        )
        new_id = cur.lastrowid
        cur.connection.commit()
    return {"id": new_id}


@app.get("/customers/{customer_id}")
def get_customer_detail(customer_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT id, name, phone, email, address, credit_limit, current_balance, is_active FROM customers WHERE id=?",
            (customer_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        return dict(row)


# --------------------------- Sales Orders API ---------------------------
@app.post("/sales/orders", status_code=201)
def create_sales_order(req: SaleOrderCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير", "CASHIER", "أمين_صندوق"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    db, _, _, _, _, _, _, _ = get_services()
    
    try:
        # Direct DB insert for reliable ID tracking
        now = datetime.now()
        invoice_no = f"ORD-{int(now.timestamp())}"
        total = sum(it.quantity * it.unit_price * (1 - (it.discount or 0)/100) for it in req.items)
        
        with db.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO sales(invoice_number, customer_id, total_amount, final_amount, payment_method, notes, sale_date, created_at, updated_at)
                VALUES(?,?,?,?,?,?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (invoice_no, req.customer_id, total, total, req.payment_method, req.notes, now.date())
            )
            order_id = cur.lastrowid
            
            for it in req.items:
                item_total = it.quantity * it.unit_price * (1 - (it.discount or 0)/100)
                # batch_id is required (NOT NULL), use variant_id if provided, else default to 1
                batch_id = it.variant_id if it.variant_id else 1
                cur.execute(
                    """
                    INSERT INTO sale_items(sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit, created_at)
                    VALUES(?,?,?,?,?,?,0,0, CURRENT_TIMESTAMP)
                    """,
                    (order_id, it.product_id, batch_id, it.quantity, it.unit_price, item_total)
                )
            
            cur.connection.commit()
        
        return {"id": order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@app.get("/sales/orders", response_model=PaginatedResponse)
def list_sales_orders(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    
    with db.get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sales")
        total = cur.fetchone()[0]
        
        cur.execute(
            """
            SELECT s.id, s.invoice_number, s.customer_id, c.name as customer_name, 
                   s.total_amount, s.final_amount, s.payment_method, s.sale_date, s.created_at
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset)
        )
        rows = cur.fetchall()
        items = [dict(row) for row in rows]
    
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)


@app.get("/sales/orders/{order_id}")
def get_sales_order_detail(order_id: int, user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    
    with db.get_cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.invoice_number, s.customer_id, c.name as customer_name,
                   s.total_amount, s.final_amount, s.payment_method, s.notes, s.sale_date, s.created_at
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.id = ?
            """,
            (order_id,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = dict(row)
        
        # Get items
        cur.execute(
            """
            SELECT si.id, si.product_id, p.name as product_name, si.batch_id, 
                   si.quantity, si.unit_price, si.total_price
            FROM sale_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = ?
            ORDER BY si.id
            """,
            (order_id,)
        )
        order["items"] = [dict(r) for r in cur.fetchall()]
    
    return order

# ---------------- Sales Orders Lifecycle Enhancements (v1.7.0) ----------------

class OrderStatusUpdateRequest(BaseModel):
    order_id: int
    new_status: str

class RefundCreateRequest(BaseModel):
    order_id: int
    amount: float
    reason: Optional[str] = None

class ReturnCreateRequest(BaseModel):
    order_id: int
    items: List[Dict[str, Any]]
    reason: Optional[str] = None

class PaymentTrackingRequest(BaseModel):
    order_id: int

@app.post("/sales/orders/update-status", status_code=200)
def update_order_status(req: OrderStatusUpdateRequest, user=Depends(get_current_user)):
    _, _, _, _, ss, _, _, _ = get_services()
    if not ss:
        raise HTTPException(status_code=501, detail="Sales service not available")
    user_id = user.get("id")
    ok = ss.update_order_status(req.order_id, req.new_status, user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to update order status")
    return {"message": f"Order {req.order_id} status updated to {req.new_status}"}

@app.post("/sales/orders/create-refund", status_code=200)
def create_order_refund(req: RefundCreateRequest, user=Depends(get_current_user)):
    _, _, _, _, ss, _, _, _ = get_services()
    if not ss:
        raise HTTPException(status_code=501, detail="Sales service not available")
    ok = ss.create_refund(req.order_id, req.amount, req.reason or "")
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to create refund")
    return {"message": f"Refund created for order {req.order_id} (amount: {req.amount})"}

@app.post("/sales/orders/create-return", status_code=200)
def create_order_return(req: ReturnCreateRequest, user=Depends(get_current_user)):
    _, _, _, _, ss, _, _, _ = get_services()
    if not ss:
        raise HTTPException(status_code=501, detail="Sales service not available")
    ok = ss.create_return(req.order_id, req.items, req.reason or "")
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to create return")
    return {"message": f"Return created for order {req.order_id}"}

@app.post("/sales/orders/track-payment", status_code=200)
def track_order_payment(req: PaymentTrackingRequest, user=Depends(get_current_user)):
    _, _, _, _, ss, _, _, _ = get_services()
    if not ss:
        raise HTTPException(status_code=501, detail="Sales service not available")
    result = ss.track_payment(req.order_id)
    return result

# ================= Purchase Orders API (v1.8.0) =================

@app.post("/purchase/orders", status_code=201)
def create_purchase_order(req: PurchaseOrderCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    _, _, _, _, _, inv_s, _, po_s = get_services()
    if not po_s:
        raise HTTPException(status_code=501, detail="Purchase order service not available")
    from ..models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatus
    po = PurchaseOrder(
        supplier_id=req.supplier_id,
        supplier_name=req.supplier_name,
        supplier_contact=req.supplier_contact,
        required_date=datetime.strptime(req.required_date, "%Y-%m-%d").date() if req.required_date else None,
        currency=req.currency,
        notes=req.notes,
        status=POStatus.DRAFT,
        items=[]
    )
    subtotal = 0.0
    for it in req.items:
        item_sub = it.quantity_ordered * it.unit_price
        discount_amt = item_sub * (it.discount_percent or 0)/100
        tax_amt = (item_sub - discount_amt) * (it.tax_percent or 0)/100
        net_amt = item_sub - discount_amt + tax_amt
        subtotal += net_amt
        poi = PurchaseOrderItem(
            product_id=it.product_id,
            product_name=it.product_name,
            quantity_ordered=it.quantity_ordered,
            unit_price=it.unit_price,
            discount_percent=it.discount_percent or 0,
            tax_percent=it.tax_percent or 0,
            subtotal=item_sub,
            discount_amount=discount_amt,
            tax_amount=tax_amt,
            net_amount=net_amt
        )
        po.items.append(poi)
    po.subtotal = subtotal
    po.total_amount = subtotal
    po_id = po_s.create_purchase_order(po)
    return {"id": po_id, "po_number": po.po_number}

@app.get("/purchase/orders", response_model=PaginatedResponse)
def list_purchase_orders(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    _, _, _, _, _, _, _, po_s = get_services()
    if not po_s:
        raise HTTPException(status_code=501, detail="Purchase order service not available")
    offset = (page - 1) * page_size
    pos = po_s.get_all_purchase_orders(limit=page_size, offset=offset)
    total = len(po_s.get_all_purchase_orders(limit=100000, offset=0))  # simplified count
    items = []
    for po in pos:
        items.append({
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "supplier_name": po.supplier_name,
            "status": getattr(po.status, 'value', po.status),
            "total_amount": po.total_amount,
            "order_date": po.order_date.isoformat() if po.order_date else None,
            "required_date": po.required_date.isoformat() if po.required_date else None,
            "items_count": len(po.items)
        })
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)

@app.get("/purchase/orders/{po_id}")
def get_purchase_order_detail(po_id: int, user=Depends(get_current_user)):
    _, _, _, _, _, _, _, po_s = get_services()
    if not po_s:
        raise HTTPException(status_code=501, detail="Purchase order service not available")
    po = po_s.get_purchase_order(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {
        "id": po.id,
        "po_number": po.po_number,
        "supplier_id": po.supplier_id,
        "supplier_name": po.supplier_name,
        "status": getattr(po.status, 'value', po.status),
        "total_amount": po.total_amount,
        "order_date": po.order_date.isoformat() if po.order_date else None,
        "required_date": po.required_date.isoformat() if po.required_date else None,
        "items": [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product_name,
                "quantity_ordered": it.quantity_ordered,
                "quantity_received": it.quantity_received,
                "quantity_pending": it.quantity_pending,
                "unit_price": it.unit_price,
                "net_amount": it.net_amount
            } for it in po.items
        ]
    }

@app.post("/purchase/orders/update-status", status_code=200)
def update_purchase_order_status(req: PurchaseOrderStatusUpdate, user=Depends(get_current_user)):
    _, _, _, _, _, _, _, po_s = get_services()
    if not po_s:
        raise HTTPException(status_code=501, detail="Purchase order service not available")
    po = po_s.get_purchase_order(req.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = req.new_status
    po_s.update_purchase_order(po)
    return {"message": f"Purchase order {po.po_number} status updated to {req.new_status}"}

@app.post("/purchase/orders/receive", status_code=200)
def receive_purchase_order(req: ReceiveShipmentRequest, user=Depends(get_current_user)):
    _, _, _, _, _, inv_s, _, po_s = get_services()
    if not po_s or not inv_s:
        raise HTTPException(status_code=501, detail="Required services not available")
    po = po_s.get_purchase_order(req.po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    # Basic quantity update and stock movement
    updated_items = 0
    for ritem in req.items:
        for it in po.items:
            if it.id == ritem.po_item_id:
                it.quantity_received += ritem.quantity_accepted
                it.quantity_pending = max(0, it.quantity_ordered - it.quantity_received)
                # Record stock movement
                from ..services.inventory_service_enhanced import StockMovement, MovementType
                movement = StockMovement(
                    product_id=ritem.product_id,
                    movement_type=MovementType.PURCHASE.value,
                    quantity=int(ritem.quantity_accepted),
                    reference_id=po.id,
                    reference_type="purchase_order",
                    notes=f"Receipt for PO {po.po_number}"
                )
                inv_s.record_stock_movement(movement)
                updated_items += 1
                break
    po_s.update_purchase_order(po)
    return {"message": f"Received items for PO {po.po_number}", "items_updated": updated_items}


# --------------------------- Quotes API ---------------------------
@app.post("/sales/quotes", status_code=201)
def create_quote(req: QuoteCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "مدير", "CASHIER", "أمين_صندوق"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    db, _, _, _, _, _, _, _ = get_services()
    now = datetime.now()
    quote_no = f"QT-{int(now.timestamp())}"
    total = sum(it.quantity * it.unit_price * (1 - (it.discount or 0)/100) for it in req.items)
    
    # Check if quotes table exists, create minimal quote record
    with db.get_cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO quotes(quote_number, customer_id, total_amount, valid_until, notes, created_at, updated_at)
                VALUES(?,?,?,?,?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (quote_no, req.customer_id, total, req.valid_until, req.notes)
            )
            quote_id = cur.lastrowid
            
            for it in req.items:
                item_total = it.quantity * it.unit_price * (1 - (it.discount or 0)/100)
                cur.execute(
                    """
                    INSERT INTO quote_items(quote_id, product_id, variant_id, quantity, unit_price, total, created_at)
                    VALUES(?,?,?,?,?,?, CURRENT_TIMESTAMP)
                    """,
                    (quote_id, it.product_id, it.variant_id, it.quantity, it.unit_price, item_total)
                )
            
            cur.connection.commit()
            return {"id": quote_id, "quote_number": quote_no}
            
        except Exception as e:
            # Quotes table may not exist; return error or create in sales with quote flag
            raise HTTPException(status_code=501, detail=f"Quotes feature requires quotes table: {str(e)}")


@app.get("/sales/quotes", response_model=PaginatedResponse)
def list_quotes(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), user=Depends(get_current_user)):
    db, _, _, _, _, _, _, _ = get_services()
    offset = (page - 1) * page_size
    
    with db.get_cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM quotes")
            total = cur.fetchone()[0]
            
            cur.execute(
                """
                SELECT q.id, q.quote_number, q.customer_id, c.name as customer_name,
                       q.total_amount, q.valid_until, q.created_at
                FROM quotes q
                LEFT JOIN customers c ON q.customer_id = c.id
                ORDER BY q.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset)
            )
            rows = cur.fetchall()
            items = [dict(row) for row in rows]
            
            return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, has_next=offset + page_size < total)
        except Exception:
            # Quotes table doesn't exist
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size, has_next=False)



# ===========================Inventory Management API ===========================

### Transfer Stock
@app.post("/inventory/transfer", status_code=201)
def transfer_stock(req: StockTransferRequest, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????", "WAREHOUSE", "?????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    _, _, _, _, _, inv_s, _, _ = get_services()
    if not inv_s:
        raise HTTPException(status_code=501, detail="Inventory service not available")
    
    success = inv_s.transfer_stock(
        product_id=req.product_id,
        quantity=req.quantity,
        from_location=req.from_location,
        to_location=req.to_location,
        notes=req.notes
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to transfer stock")
    
    return {"message": "Stock transferred successfully"}


### Reserve Stock
@app.post("/inventory/reserve", status_code=201)
def reserve_stock(req: StockReservationRequest, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????", "CASHIER", "????_?????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    _, _, _, _, _, inv_s, _, _ = get_services()
    if not inv_s:
        raise HTTPException(status_code=501, detail="Inventory service not available")
    
    success = inv_s.reserve_stock(
        product_id=req.product_id,
        quantity=req.quantity,
        reference_id=req.reference_id,
        reference_type=req.reference_type
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reserve stock")
    
    return {"message": "Stock reserved successfully"}


### Release Reserved Stock
@app.post("/inventory/release/{product_id}", status_code=200)
def release_stock(product_id: int, quantity: int = Query(ge=1), reference_id: Optional[int] = None, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????", "CASHIER", "????_?????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    _, _, _, _, _, inv_s, _, _ = get_services()
    if not inv_s:
        raise HTTPException(status_code=501, detail="Inventory service not available")
    
    success = inv_s.release_reserved_stock(product_id, quantity, reference_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to release stock")
    
    return {"message": "Stock released successfully"}


### Get Stock Movements
@app.get("/inventory/movements")
def list_stock_movements(
    product_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000),
    user=Depends(get_current_user)
):
    _, _, _, _, _, inv_s, _, _ = get_services()
    if not inv_s:
        raise HTTPException(status_code=501, detail="Inventory service not available")
    
    movements = inv_s.get_stock_movements(product_id=product_id, limit=limit)
    return {"items": movements, "total": len(movements)}


### ABC Analysis
@app.get("/inventory/abc-analysis")
def get_abc_analysis(user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????", "MANAGER", "????_?????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    _, _, _, _, _, inv_s, _, _ = get_services()
    if not inv_s:
        raise HTTPException(status_code=501, detail="Inventory service not available")
    
    analysis = inv_s.perform_abc_analysis()
    return analysis


# ===========================Vendor Management API (v1.5.0)===========================

### Create Vendor
@app.post("/vendors", status_code=201)
def create_vendor(vendor: VendorCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges - Admin only")
    
    _, _, _, vc_s, _, _, _ = get_services()
    if not vc_s:
        raise HTTPException(status_code=501, detail="Vendor service not available")
    
    vendor_data = vendor.dict()
    vendor_id = vc_s.create_vendor(vendor_data)
    
    if not vendor_id:
        raise HTTPException(status_code=500, detail="Failed to create vendor")
    
    return {"id": vendor_id, "message": "Vendor created successfully"}


### Get Vendor Details
@app.get("/vendors/{vendor_id}")
def get_vendor(vendor_id: int, user=Depends(get_current_user)):
    _, _, _, vc_s, _, _, _ = get_services()
    if not vc_s:
        raise HTTPException(status_code=501, detail="Vendor service not available")
    
    vendor = vc_s.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return vendor


### Search Vendors
@app.get("/vendors")
def search_vendors(term: str = Query("", min_length=0), user=Depends(get_current_user)):
    _, _, _, vc_s, _, _, _ = get_services()
    if not vc_s:
        raise HTTPException(status_code=501, detail="Vendor service not available")
    
    if not term:
        # Return empty or all vendors - for now return empty
        return {"items": [], "total": 0}
    
    vendors = vc_s.search_vendors(term)
    return {"items": vendors, "total": len(vendors)}


### Create Vendor Evaluation/Rating
@app.post("/vendors/{vendor_id}/evaluations", status_code=201)
def create_vendor_evaluation(vendor_id: int, evaluation: VendorEvaluationCreate, user=Depends(get_current_user)):
    role = user.get("role")
    if role not in {"admin", "ADMIN", "????", "MANAGER", "????_?????"}:
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    
    _, _, vr_s, _, _, _, _ = get_services()
    if not vr_s:
        raise HTTPException(status_code=501, detail="Vendor rating service not available")
    
    # Create SupplierEvaluation from request
    eval_data = evaluation.dict()
    eval_data["supplier_id"] = vendor_id
    eval_data["evaluated_by"] = user.get("id")
    eval_data["evaluation_date"] = datetime.now().isoformat()
    
    # Calculate rates
    if eval_data["total_orders"] > 0:
        eval_data["on_time_delivery_rate"] = eval_data["on_time_deliveries"] / eval_data["total_orders"]
        eval_data["quality_acceptance_rate"] = 1 - (eval_data["rejected_shipments"] / eval_data["total_orders"])
    else:
        eval_data["on_time_delivery_rate"] = 0.0
        eval_data["quality_acceptance_rate"] = 0.0
    
    eval_data["average_lead_time_days"] = 0.0  # Could calculate from purchase history
    
    supplier_eval = SupplierEvaluation(**eval_data)
    eval_id = vr_s.create_evaluation(supplier_eval)
    
    return {"id": eval_id, "message": "Vendor evaluation created successfully"}


### Get Vendor Latest Evaluation
@app.get("/vendors/{vendor_id}/evaluation")
def get_vendor_evaluation(vendor_id: int, user=Depends(get_current_user)):
    _, _, vr_s, _, _, _, _ = get_services()
    if not vr_s:
        raise HTTPException(status_code=501, detail="Vendor rating service not available")
    
    evaluation = vr_s.get_latest_evaluation(vendor_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="No evaluation found for this vendor")
    
    return evaluation


### Get Vendor Score/Grade
@app.get("/vendors/{vendor_id}/score")
def get_vendor_score(vendor_id: int, user=Depends(get_current_user)):
    _, _, vr_s, _, _, _, _ = get_services()
    if not vr_s:
        raise HTTPException(status_code=501, detail="Vendor rating service not available")
    
    score = vr_s.get_supplier_score(vendor_id)
    if not score:
        raise HTTPException(status_code=404, detail="No score available for this vendor")
    
    return score


### Get Vendor Performance Metrics
@app.get("/vendors/{vendor_id}/performance")
def get_vendor_performance(vendor_id: int, user=Depends(get_current_user)):
    _, _, _, vc_s, _, _ = get_services()
    if not vc_s:
        raise HTTPException(status_code=501, detail="Vendor service not available")
    
    performance = vc_s.vendor_performance(vendor_id)
    if not performance:
        raise HTTPException(status_code=404, detail="No performance data available")
    
    return performance


# ============= Pydantic Schemas for Reports (v1.6.0) =============

class ReportFilterSchema(BaseModel):
    start_date: Optional[str] = None  # Format: YYYY-MM-DD
    end_date: Optional[str] = None
    category_id: Optional[int] = None
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    product_id: Optional[int] = None
    user_id: Optional[int] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    payment_type: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None


# ============= Reports & Analytics API (v1.6.0) =============

### Generate Sales Summary Report
@app.post("/reports/sales-summary")
def generate_sales_report(
    filters: ReportFilterSchema,
    format: str = Query("json", regex="^(json|xlsx|pdf|csv)$"),
    user=Depends(get_current_user)
):
    """
    Generate comprehensive sales summary report
    Includes: total sales, revenue, payment methods breakdown, top customers
    """
    _, _, _, _, _, _, rp_s, _ = get_services()
    if not rp_s or not ReportFilter:
        raise HTTPException(status_code=501, detail="Reports service not available")
    
    # Convert string dates to datetime
    filter_dict = filters.dict(exclude_none=True)
    if "start_date" in filter_dict:
        filter_dict["start_date"] = datetime.strptime(filter_dict["start_date"], "%Y-%m-%d")
    if "end_date" in filter_dict:
        filter_dict["end_date"] = datetime.strptime(filter_dict["end_date"], "%Y-%m-%d")
    
    report_filter = ReportFilter(**filter_dict)
    report_data = rp_s.generate_sales_summary_report(report_filter)
    
    # Export if requested
    if format != "json":
        export_format = ExportFormat(format)
        filename = rp_s.export_report(report_data, export_format)
        return {"message": "Report generated successfully", "filename": filename, "format": format}
    
    # Return JSON data
    return {
        "title": report_data.title,
        "subtitle": report_data.subtitle,
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "data": report_data.data,
        "charts_data": report_data.charts_data
    }


### Generate Inventory Status Report
@app.post("/reports/inventory-status")
def generate_inventory_report(
    filters: ReportFilterSchema,
    format: str = Query("json", regex="^(json|xlsx|pdf|csv)$"),
    user=Depends(get_current_user)
):
    """
    Generate inventory status report
    Includes: stock levels, low stock alerts, stock valuation
    """
    _, _, _, _, _, _, rp_s, _ = get_services()
    if not rp_s or not ReportFilter:
        raise HTTPException(status_code=501, detail="Reports service not available")
    
    filter_dict = filters.dict(exclude_none=True)
    report_filter = ReportFilter(**filter_dict)
    report_data = rp_s.generate_inventory_status_report(report_filter)
    
    if format != "json":
        export_format = ExportFormat(format)
        filename = rp_s.export_report(report_data, export_format)
        return {"message": "Report generated successfully", "filename": filename, "format": format}
    
    return {
        "title": report_data.title,
        "subtitle": report_data.subtitle,
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "data": report_data.data,
        "charts_data": report_data.charts_data
    }


### Generate Financial Summary Report
@app.post("/reports/financial-summary")
def generate_financial_report(
    filters: ReportFilterSchema,
    format: str = Query("json", regex="^(json|xlsx|pdf|csv)$"),
    user=Depends(get_current_user)
):
    """
    Generate financial summary report
    Includes: revenue, expenses, profit/loss, margins
    """
    _, _, _, _, _, _, rp_s, _ = get_services()
    if not rp_s or not ReportFilter:
        raise HTTPException(status_code=501, detail="Reports service not available")
    
    filter_dict = filters.dict(exclude_none=True)
    if "start_date" in filter_dict:
        filter_dict["start_date"] = datetime.strptime(filter_dict["start_date"], "%Y-%m-%d")
    if "end_date" in filter_dict:
        filter_dict["end_date"] = datetime.strptime(filter_dict["end_date"], "%Y-%m-%d")
    
    report_filter = ReportFilter(**filter_dict)
    report_data = rp_s.generate_financial_summary_report(report_filter)
    
    if format != "json":
        export_format = ExportFormat(format)
        filename = rp_s.export_report(report_data, export_format)
        return {"message": "Report generated successfully", "filename": filename, "format": format}
    
    return {
        "title": report_data.title,
        "subtitle": report_data.subtitle,
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "data": report_data.data,
        "charts_data": report_data.charts_data
    }


### Generate Payment Summary Report
@app.post("/reports/payment-summary")
def generate_payment_report(
    filters: ReportFilterSchema,
    format: str = Query("json", regex="^(json|xlsx|pdf|csv)$"),
    user=Depends(get_current_user)
):
    """
    Generate payment summary report
    Includes: payments breakdown, methods analysis, outstanding balances
    """
    _, _, _, _, _, _, rp_s, _ = get_services()
    if not rp_s or not ReportFilter:
        raise HTTPException(status_code=501, detail="Reports service not available")
    
    filter_dict = filters.dict(exclude_none=True)
    if "start_date" in filter_dict:
        filter_dict["start_date"] = datetime.strptime(filter_dict["start_date"], "%Y-%m-%d")
    if "end_date" in filter_dict:
        filter_dict["end_date"] = datetime.strptime(filter_dict["end_date"], "%Y-%m-%d")
    
    report_filter = ReportFilter(**filter_dict)
    report_data = rp_s.generate_payment_summary_report(report_filter)
    
    if format != "json":
        export_format = ExportFormat(format)
        filename = rp_s.export_report(report_data, export_format)
        return {"message": "Report generated successfully", "filename": filename, "format": format}
    
    return {
        "title": report_data.title,
        "subtitle": report_data.subtitle,
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "data": report_data.data,
        "charts_data": report_data.charts_data
    }


### Generate Cash Flow Report
@app.post("/reports/cash-flow")
def generate_cashflow_report(
    filters: ReportFilterSchema,
    format: str = Query("json", regex="^(json|xlsx|pdf|csv)$"),
    user=Depends(get_current_user)
):
    """
    Generate cash flow report
    Includes: cash inflows, outflows, net cash flow trend
    """
    _, _, _, _, _, _, rp_s, _ = get_services()
    if not rp_s or not ReportFilter:
        raise HTTPException(status_code=501, detail="Reports service not available")
    
    filter_dict = filters.dict(exclude_none=True)
    if "start_date" in filter_dict:
        filter_dict["start_date"] = datetime.strptime(filter_dict["start_date"], "%Y-%m-%d")
    if "end_date" in filter_dict:
        filter_dict["end_date"] = datetime.strptime(filter_dict["end_date"], "%Y-%m-%d")
    
    report_filter = ReportFilter(**filter_dict)
    report_data = rp_s.generate_cash_flow_report(report_filter)
    
    if format != "json":
        export_format = ExportFormat(format)
        filename = rp_s.export_report(report_data, export_format)
        return {"message": "Report generated successfully", "filename": filename, "format": format}
    
    return {
        "title": report_data.title,
        "subtitle": report_data.subtitle,
        "generated_at": report_data.generated_at.isoformat(),
        "summary": report_data.summary,
        "data": report_data.data,
        "charts_data": report_data.charts_data
    }


# ============================================================================
# AI & CHATBOT ENDPOINTS
# ============================================================================

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    language: str
    intent: Optional[str]
    confidence: float
    timestamp: str


@app.post("/ai/chat", response_model=ChatResponse)
def chat_with_bot(
    msg: ChatMessage,
    user=Depends(get_current_user)
):
    """
    التحدث مع الـ Chatbot الذكي
    Chat with AI assistant (supports Arabic & English)
    """
    if not chatbot:
        raise HTTPException(status_code=501, detail="Chatbot service not available")
    
    result = chatbot.process_message(
        msg.message, 
        user_id=msg.user_id or str(user.get('id', 'unknown'))
    )
    
    return ChatResponse(**result)


@app.get("/ai/chat/history")
def get_chat_history(
    user_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    user=Depends(get_current_user)
):
    """
    الحصول على سجل المحادثات
    Get chat conversation history
    """
    if not chatbot:
        raise HTTPException(status_code=501, detail="Chatbot service not available")
    
    history = chatbot.get_conversation_history(
        user_id=user_id or str(user.get('id')),
        limit=limit
    )
    
    return {"history": history, "count": len(history)}


@app.delete("/ai/chat/history")
def clear_chat_history(
    user_id: Optional[str] = None,
    user=Depends(get_current_user)
):
    """مسح سجل المحادثات"""
    if not chatbot:
        raise HTTPException(status_code=501, detail="Chatbot service not available")
    
    chatbot.clear_history(user_id=user_id or str(user.get('id')))
    return {"message": "Chat history cleared"}


@app.get("/ai/forecast/sales")
def forecast_sales(
    product_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    user=Depends(get_current_user)
):
    """
    التنبؤ بالمبيعات
    Predict future sales for products
    """
    if not PredictiveEngine:
        raise HTTPException(status_code=501, detail="Predictive analytics not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    predictor = PredictiveEngine(db)
    
    forecasts = predictor.forecast_sales(product_id=product_id, days=days)
    
    return {
        "forecasts": [
            {
                "product_id": f.product_id,
                "product_name": f.product_name,
                "current_stock": f.current_stock,
                "predicted_sales": f.predicted_sales,
                "days_until_stockout": f.days_until_stockout,
                "recommended_reorder": f.recommended_reorder_quantity,
                "confidence": f.confidence
            }
            for f in forecasts
        ],
        "count": len(forecasts)
    }


@app.get("/ai/customer-insights")
def get_customer_insights(
    customer_id: Optional[int] = None,
    user=Depends(get_current_user)
):
    """
    تحليل سلوك العملاء
    Analyze customer behavior and predictions
    """
    if not PredictiveEngine:
        raise HTTPException(status_code=501, detail="Predictive analytics not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    predictor = PredictiveEngine(db)
    
    insights = predictor.analyze_customer_behavior(customer_id=customer_id)
    
    return {
        "insights": [
            {
                "customer_id": i.customer_id,
                "customer_name": i.customer_name,
                "total_purchases": i.total_purchases,
                "average_order_value": i.average_order_value,
                "purchase_frequency": i.purchase_frequency,
                "predicted_next_purchase": i.predicted_next_purchase,
                "customer_segment": i.customer_segment,
                "lifetime_value": i.lifetime_value
            }
            for i in insights
        ],
        "count": len(insights)
    }


@app.get("/ai/recommendations/{customer_id}")
def get_recommendations(
    customer_id: int,
    limit: int = Query(5, ge=1, le=20),
    user=Depends(get_current_user)
):
    """
    الحصول على توصيات المنتجات للعميل
    Get smart product recommendations for customer
    """
    if not PredictiveEngine:
        raise HTTPException(status_code=501, detail="Predictive analytics not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    predictor = PredictiveEngine(db)
    
    recommendations = predictor.get_product_recommendations(
        customer_id=customer_id,
        limit=limit
    )
    
    return {
        "recommendations": recommendations,
        "count": len(recommendations)
    }


@app.get("/ai/anomalies")
def detect_anomalies(
    days: int = Query(7, ge=1, le=30),
    user=Depends(get_current_user)
):
    """
    اكتشاف الشذوذات في المبيعات
    Detect unusual sales patterns
    """
    if not PredictiveEngine:
        raise HTTPException(status_code=501, detail="Predictive analytics not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    predictor = PredictiveEngine(db)
    
    anomalies = predictor.detect_anomalies(days=days)
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies)
    }


# ============================================================================
# MARKETING AUTOMATION ENDPOINTS
# ============================================================================

class SegmentCreate(BaseModel):
    name: str
    description: str
    criteria: Dict[str, Any]


class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    segment_id: Optional[int] = None
    subject: str
    content: str
    scheduled_date: Optional[str] = None
    budget: float = 0


@app.post("/marketing/segments")
def create_customer_segment(
    segment: SegmentCreate,
    user=Depends(get_current_user)
):
    """إنشاء شريحة عملاء"""
    if not MarketingService:
        raise HTTPException(status_code=501, detail="Marketing service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    marketing = MarketingService(db)
    
    segment_id = marketing.create_segment(
        name=segment.name,
        description=segment.description,
        criteria=segment.criteria
    )
    
    return {"segment_id": segment_id, "message": "تم إنشاء الشريحة بنجاح"}


@app.post("/marketing/campaigns")
def create_marketing_campaign(
    campaign: CampaignCreate,
    user=Depends(get_current_user)
):
    """إنشاء حملة تسويقية"""
    if not MarketingService:
        raise HTTPException(status_code=501, detail="Marketing service not available")
    
    from ..services.marketing_service import CampaignType
    
    db, _, _, _, _, _, _, _ = get_services()
    marketing = MarketingService(db)
    
    campaign_id = marketing.create_campaign(
        name=campaign.name,
        campaign_type=CampaignType(campaign.campaign_type),
        segment_id=campaign.segment_id,
        subject=campaign.subject,
        content=campaign.content,
        scheduled_date=campaign.scheduled_date,
        budget=campaign.budget
    )
    
    return {"campaign_id": campaign_id, "message": "تم إنشاء الحملة بنجاح"}


@app.post("/marketing/campaigns/{campaign_id}/send")
def send_marketing_campaign(
    campaign_id: int,
    user=Depends(get_current_user)
):
    """إرسال حملة تسويقية"""
    if not MarketingService:
        raise HTTPException(status_code=501, detail="Marketing service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    marketing = MarketingService(db)
    
    result = marketing.send_campaign(campaign_id)
    return result


@app.get("/marketing/campaigns/{campaign_id}/analytics")
def get_campaign_analytics(
    campaign_id: int,
    user=Depends(get_current_user)
):
    """تحليلات الحملة التسويقية"""
    if not MarketingService:
        raise HTTPException(status_code=501, detail="Marketing service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    marketing = MarketingService(db)
    
    analytics = marketing.get_campaign_analytics(campaign_id)
    return analytics


@app.get("/marketing/leads/hot")
def get_hot_leads(
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user)
):
    """الحصول على العملاء المحتملين الساخنين"""
    if not MarketingService:
        raise HTTPException(status_code=501, detail="Marketing service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    marketing = MarketingService(db)
    
    leads = marketing.get_hot_leads(limit=limit)
    return {"leads": leads, "count": len(leads)}


# ============================================================================
# MFA (Multi-Factor Authentication) ENDPOINTS
# ============================================================================

class MFAEnableRequest(BaseModel):
    methods: List[str]
    phone_number: Optional[str] = None
    email: Optional[str] = None


class MFAVerifyRequest(BaseModel):
    method: str
    code: str


@app.post("/auth/mfa/enable")
def enable_mfa(
    request: MFAEnableRequest,
    user=Depends(get_current_user)
):
    """تفعيل المصادقة متعددة العوامل"""
    if not MFAService or not MFAMethod:
        raise HTTPException(status_code=501, detail="MFA service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    mfa = MFAService(db)
    
    methods = [MFAMethod(m) for m in request.methods]
    
    result = mfa.enable_mfa(
        user_id=user['id'],
        methods=methods,
        phone_number=request.phone_number,
        email=request.email
    )
    
    return result


@app.post("/auth/mfa/disable")
def disable_mfa(user=Depends(get_current_user)):
    """تعطيل المصادقة متعددة العوامل"""
    if not MFAService:
        raise HTTPException(status_code=501, detail="MFA service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    mfa = MFAService(db)
    
    mfa.disable_mfa(user_id=user['id'])
    return {"message": "تم تعطيل MFA بنجاح"}


@app.post("/auth/mfa/send-otp")
def send_mfa_otp(
    method: str,
    user=Depends(get_current_user)
):
    """إرسال OTP"""
    if not MFAService or not MFAMethod:
        raise HTTPException(status_code=501, detail="MFA service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    mfa = MFAService(db)
    
    result = mfa.send_otp(
        user_id=user['id'],
        method=MFAMethod(method)
    )
    
    return result


@app.post("/auth/mfa/verify")
def verify_mfa(
    request: MFAVerifyRequest,
    user=Depends(get_current_user)
):
    """التحقق من MFA"""
    if not MFAService or not MFAMethod:
        raise HTTPException(status_code=501, detail="MFA service not available")
    
    db, _, _, _, _, _, _, _ = get_services()
    mfa = MFAService(db)
    
    method = MFAMethod(request.method)
    
    if method == MFAMethod.TOTP:
        result = mfa.verify_totp(
            user_id=user['id'],
            code=request.code
        )
    elif method == MFAMethod.BACKUP_CODE:
        result = mfa.verify_backup_code(
            user_id=user['id'],
            code=request.code
        )
    else:
        result = mfa.verify_otp(
            user_id=user['id'],
            method=method,
            code=request.code
        )
    
    return result
