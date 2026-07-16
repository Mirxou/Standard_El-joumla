#!/usr/bin/env python3  # noqa: E265
# -*- coding: utf-8 -*-
"""
API Routes - REST API Endpoints
مسارات API للـ REST API
"""

import json
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from src.api.auth import JWTAuthManager
from src.api.cache_manager import cached, invalidate_cache
from src.api.websocket_manager import get_websocket_manager
from src.core.database_manager import DatabaseManager
from src.models.category import CategoryManager
from src.models.product import Product, ProductManager
from src.models.purchase import PaymentStatus as PurchasePaymentStatus
from src.models.purchase import Purchase, PurchaseItem, PurchaseManager, PurchaseStatus
from src.models.reports import ReportManager
from src.models.return_invoice import ReturnManager
from src.models.sale import PaymentMethod, Sale, SaleItem, SaleManager, SaleStatus
from src.models.supplier import SupplierManager
from src.models.user import UserManager
from src.models.warehouse import WarehouseManager
from src.utils.logger import setup_logger

# Router
router = APIRouter()


# Health check endpoint for production readiness
@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# Security
security = HTTPBearer()

# Logger
logger = setup_logger(__name__)


# ==================== Pydantic Models ====================


class LoginRequest(BaseModel):
    """نموذج طلب تسجيل الدخول"""

    username: str = Field(..., description="اسم المستخدم")
    password: str = Field(..., description="كلمة المرور")


class LoginResponse(BaseModel):
    """نموذج استجابة تسجيل الدخول"""

    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="bearer", description="نوع Token")
    expires_in: int = Field(..., description="مدة الصلاحية بالثواني")
    user_id: int = Field(..., description="معرف المستخدم")
    username: str = Field(..., description="اسم المستخدم")
    full_name: Optional[str] = Field(None, description="الاسم الكامل")
    company_id: Optional[int] = Field(None, description="معرف الشركة")


class RefreshTokenRequest(BaseModel):
    """نموذج طلب تحديث Token"""

    refresh_token: str = Field(..., description="Refresh Token")


class RefreshTokenResponse(BaseModel):
    """نموذج استجابة تحديث Token"""

    access_token: str = Field(..., description="JWT Access Token الجديد")
    token_type: str = Field(default="bearer", description="نوع Token")
    expires_in: int = Field(..., description="مدة الصلاحية بالثواني")


class UserInfo(BaseModel):
    """معلومات المستخدم"""

    user_id: int
    username: str
    full_name: Optional[str]
    role_id: Optional[int]
    company_id: Optional[int]
    is_active: bool


# ==================== Warehouse Models ====================


# ==================== Returns Models ====================


class ReturnItemSchema(BaseModel):
    product_id: int
    quantity: float
    unit_price: float
    return_reason: Optional[str] = None
    notes: Optional[str] = None


class ReturnCreate(BaseModel):
    return_type: str
    return_reason: Optional[str] = None
    original_sale_id: Optional[int] = None
    customer_id: Optional[int] = None
    items: List[ReturnItemSchema]
    notes: Optional[str] = None


class ReturnResponse(BaseModel):
    id: int
    return_number: str
    return_type: str
    status: str
    total_amount: float
    created_at: str


# ==================== Warehouse Models ====================


class WarehouseCreate(BaseModel):
    """نموذج إنشاء مستودع"""

    code: str = Field(..., description="رمز المستودع")
    name: str = Field(..., description="اسم المستودع")
    name_en: Optional[str] = None
    warehouse_type: str = Field(default="main", description="نوع المستودع")
    capacity: float = Field(default=0.0, description="السعة")
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class WarehouseResponse(BaseModel):
    """نموذج استجابة مستودع"""

    id: int
    code: str
    name: str
    name_en: Optional[str]
    warehouse_type: str
    capacity: float
    current_utilization: float
    address: Optional[str]
    city: Optional[str]
    phone: Optional[str]
    manager_name: Optional[str]
    is_active: bool
    status: str = "نشط"  # حقل مشتق للواجهة

    model_config = ConfigDict(from_attributes=True)


class WarehouseListResponse(BaseModel):
    warehouses: List[WarehouseResponse]


# ==================== Product Models ====================


class ProductCreate(BaseModel):
    """نموذج إنشاء منتج"""

    name: str = Field(..., description="اسم المنتج")
    name_en: Optional[str] = Field(None, description="الاسم بالإنجليزية")
    barcode: Optional[str] = Field(None, description="الباركود")
    category_id: Optional[int] = Field(None, description="معرف الفئة")
    unit: str = Field(default="قطعة", description="الوحدة")
    cost_price: float = Field(default=0.0, description="سعر التكلفة")
    selling_price: float = Field(default=0.0, description="سعر البيع")
    min_stock: int = Field(default=0, description="الحد الأدنى للمخزون")
    current_stock: int = Field(default=0, description="المخزون الحالي")
    description: Optional[str] = Field(None, description="الوصف")
    image_path: Optional[str] = Field(None, description="مسار الصورة")
    is_active: bool = Field(default=True, description="نشط")


class ProductUpdate(BaseModel):
    """نموذج تحديث منتج"""

    name: Optional[str] = Field(None, description="اسم المنتج")
    name_en: Optional[str] = Field(None, description="الاسم بالإنجليزية")
    barcode: Optional[str] = Field(None, description="الباركود")
    category_id: Optional[int] = Field(None, description="معرف الفئة")
    unit: Optional[str] = Field(None, description="الوحدة")
    cost_price: Optional[float] = Field(None, description="سعر التكلفة")
    selling_price: Optional[float] = Field(None, description="سعر البيع")
    min_stock: Optional[int] = Field(None, description="الحد الأدنى للمخزون")
    current_stock: Optional[int] = Field(None, description="المخزون الحالي")
    description: Optional[str] = Field(None, description="الوصف")
    image_path: Optional[str] = Field(None, description="مسار الصورة")
    is_active: Optional[bool] = Field(None, description="نشط")


class ProductResponse(BaseModel):
    """نموذج استجابة منتج - متوافق مع Frontend و Backend"""

    id: int
    name: str
    name_en: Optional[str] = None
    # Backend fields
    barcode: Optional[str] = None
    # Frontend fields (aliases) - يتم ملؤها بواسطة serialize_product_for_frontend
    sku: Optional[str] = None  # Alias for barcode
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    unit: str = "قطعة"
    cost_price: float = 0.0
    # Backend: selling_price, Frontend: price
    selling_price: float = 0.0
    price: Optional[float] = None  # Alias for selling_price
    # Backend: min_stock, Frontend: min_stock_level
    min_stock: int = 0
    min_stock_level: Optional[int] = None  # Alias for min_stock
    # Backend: current_stock, Frontend: stock
    current_stock: int = 0
    stock: Optional[int] = None  # Alias for current_stock
    description: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    status: Optional[str] = None  # 'active' | 'draft' | 'archived'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    profit_margin: float = 0.0
    profit_amount: float = 0.0
    stock_value: float = 0.0
    is_low_stock: bool = False

    model_config = ConfigDict(extra="allow")


# ==================== Supplier Models ====================


class SupplierCreate(BaseModel):
    name: str = Field(..., description="اسم المورد")
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    credit_limit: float = 0.0
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None
    credit_limit: Optional[float] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    current_balance: float
    total_purchases: float
    purchases_count: int
    is_active: bool


class UserListResponse(BaseModel):
    """نموذج استجابة قائمة المستخدمين"""

    users: List[UserInfo]


class PurchaseItemResponse(BaseModel):
    id: int
    purchase_id: int
    product_id: int
    product_name: str
    quantity_ordered: float
    quantity_received: float
    unit_cost: float
    total_amount: float
    is_fully_received: bool


class PurchaseResponse(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    purchase_date: str
    status: str
    payment_status: str
    total_amount: float
    paid_amount: float
    remaining_amount: float
    items_count: int
    is_fully_received: bool


class PurchaseCreate(BaseModel):
    supplier_id: int
    purchase_date: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    payment_terms: str = "نقدي"
    notes: Optional[str] = None
    items: List[Dict[str, Any]]  # Simplified for now, should be PurchaseItemCreate


class ReturnResponse(BaseModel):  # noqa: F811
    id: int
    return_number: str
    return_type: str
    return_date: Optional[str]
    status: str
    customer_name: Optional[str]
    supplier_name: Optional[str]
    total_amount: float
    items_count: int = 0


class ReturnCreate(BaseModel):  # noqa: F811
    return_type: str = "SALE_RETURN"
    original_sale_id: Optional[int] = None
    original_purchase_id: Optional[int] = None
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    return_date: Optional[str] = None
    return_reason: str = "OTHER"
    notes: Optional[str] = None
    items: List[Dict[str, Any]]


class ProductListResponse(BaseModel):
    """نموذج استجابة قائمة المنتجات"""

    products: List[ProductResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==================== Inventory Models ====================


class StockMovementResponse(BaseModel):
    id: Optional[int]
    product_id: int
    product_name: Optional[str]
    movement_type: str
    quantity: float
    reference_id: Optional[int]
    reference_type: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]


# ==================== Serializers ====================


def serialize_product_for_frontend(product_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    تحويل Product من Backend format إلى Frontend format
    يحل مشكلة التناقض في أسماء الحقول بين Backend و Frontend
    """
    result = product_dict.copy()

    # تحويل الحقول لتتوافق مع Frontend
    # Backend: barcode → Frontend: sku
    # Logique améliorée: priorité à barcode si valide, sinon sku existant, sinon chaîne vide
    barcode_val = result.get("barcode")
    sku_val = result.get("sku")

    # Déterminer la valeur SKU finale
    if barcode_val and str(barcode_val).strip():
        # Utiliser barcode si présent et non vide
        result["sku"] = str(barcode_val).strip()
    elif sku_val and str(sku_val).strip():
        # Sinon utiliser sku existant s'il est valide
        result["sku"] = str(sku_val).strip()
    else:
        # Par défaut, chaîne vide
        result["sku"] = ""

    # Backend: selling_price → Frontend: price (مع الاحتفاظ بـ selling_price)
    if "selling_price" in result:
        result["price"] = result.get("selling_price", 0.0)
    elif "price" not in result:
        result["price"] = 0.0

    # Backend: current_stock → Frontend: stock (مع الاحتفاظ بـ current_stock)
    if "current_stock" in result:
        result["stock"] = result.get("current_stock", 0)
    elif "stock" not in result:
        result["stock"] = 0

    # Backend: min_stock → Frontend: min_stock_level
    if "min_stock" in result:
        result["min_stock_level"] = result.get("min_stock", 0)
    elif "min_stock_level" not in result:
        result["min_stock_level"] = 0

    # إضافة status بناءً على is_active و current_stock
    # Garantir que status est toujours défini
    is_active = result.get("is_active", True)
    current_stock = result.get("current_stock", result.get("stock", 0))

    if not is_active:
        result["status"] = "archived"
    elif current_stock <= 0:
        result["status"] = "draft"
    else:
        result["status"] = "active"

    return result


# ==================== Dependencies ====================


def get_auth_manager() -> JWTAuthManager:
    """الحصول على Auth Manager"""
    # في الإنتاج، يجب الحصول من app state
    from src.api.app import auth_manager

    if not auth_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth Manager غير متاح",
        )
    return auth_manager


def get_db_manager() -> DatabaseManager:
    """الحصول على Database Manager"""
    from src.api.app import db_manager

    if not db_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database Manager غير متاح",
        )
    return db_manager


def get_product_manager() -> ProductManager:
    """الحصول على Product Manager"""
    db_manager = get_db_manager()
    return ProductManager(db_manager, logger)


def get_warehouse_manager() -> "WarehouseManager":
    """الحصول على Warehouse Manager"""
    from src.models.warehouse import WarehouseManager

    db_manager = get_db_manager()
    return WarehouseManager(db_manager, logger)


def get_supplier_manager() -> "SupplierManager":
    """الحصول على Supplier Manager"""
    from src.models.supplier import SupplierManager

    db_manager = get_db_manager()
    return SupplierManager(db_manager, logger)


def get_user_manager() -> "UserManager":
    """الحصول على User Manager"""
    from src.models.user import UserManager

    db_manager = get_db_manager()
    return UserManager(db_manager, logger)


def get_purchase_manager() -> "PurchaseManager":
    """الحصول على Purchase Manager"""
    from src.models.purchase import PurchaseManager

    db_manager = get_db_manager()
    return PurchaseManager(db_manager, logger)


def get_return_manager() -> "ReturnManager":
    """الحصول على Return Manager"""
    from src.models.return_invoice import ReturnManager

    db_manager = get_db_manager()
    return ReturnManager(db_manager, logger)


def get_report_manager() -> "ReportManager":
    """الحصول على Report Manager"""
    from src.models.reports import ReportManager

    db_manager = get_db_manager()
    return ReportManager(db_manager, logger)


def get_category_manager() -> "CategoryManager":
    """الحصول على Category Manager"""
    from src.models.category import CategoryManager

    db_manager = get_db_manager()
    return CategoryManager(db_manager, logger)


def get_inventory_service() -> "InventoryService":
    """الحصول على Inventory Service"""
    from src.services.inventory_service import InventoryService

    db_manager = get_db_manager()
    return InventoryService(db_manager, logger)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: JWTAuthManager = Depends(get_auth_manager),
) -> Dict[str, Any]:
    """
    Dependency للحصول على المستخدم الحالي من Token

    Args:
        request: FastAPI Request
        credentials: HTTP Authorization Credentials
        auth_manager: JWT Auth Manager

    Returns:
        بيانات المستخدم
    """
    # التحقق مما إذا كان AuthMiddleware قد قام بالمصادقة بالفعل
    if hasattr(request.state, "user_id") and request.state.user_id:
        return {
            "sub": request.state.user_id,
            "username": getattr(request.state, "username", "unknown"),
            "company_id": getattr(request.state, "company_id", None),
        }
    token = credentials.credentials

    user = auth_manager.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ==================== Auth Routes ====================


@router.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    auth_manager: JWTAuthManager = Depends(get_auth_manager),
):
    """
    تسجيل الدخول والحصول على JWT Tokens

    Args:
        login_data: بيانات تسجيل الدخول
        request: FastAPI Request
        response: FastAPI Response لتعيين Cookies
        auth_manager: JWT Auth Manager

    Returns:
        LoginResponse مع Tokens
    """
    # مصادقة المستخدم
    result = auth_manager.authenticate_user(username=login_data.username, password=login_data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )

    # تعيين httpOnly cookies للأمان (في حالة Production)
    # في حالة Development نرجع الـ token في body أيضاً للتوافق
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    expires_in = result.get("expires_in", 86400)

    # تحديد إذا كنا في Production
    is_production = request.app.title != "Development Server"

    if access_token and is_production:
        # تعيين access_token كـ httpOnly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=expires_in,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

        # تعيين refresh_token كـ httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=expires_in * 30,  # أطول مدة للـ refresh
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

    return LoginResponse(**result)


@router.post("/auth/logout", tags=["Authentication"])
async def logout(
    response: Response,
    request: Request,
):
    """
    تسجيل الخروج ومسح الـ cookies

    Args:
        response: FastAPI Response لمسح الـ cookies
        request: FastAPI Request

    Returns:
        رسالة نجاح
    """
    # تحديد إذا كنا في Production
    is_production = request.app.title != "Development Server"

    if is_production:
        # مسح access_token cookie
        response.delete_cookie(key="access_token", path="/")

        # مسح refresh_token cookie
        response.delete_cookie(key="refresh_token", path="/")

    return {"message": "تم تسجيل الخروج بنجاح"}


@router.post("/auth/refresh", response_model=RefreshTokenResponse, tags=["Authentication"])
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_manager: JWTAuthManager = Depends(get_auth_manager),
):
    """
    تحديث Access Token باستخدام Refresh Token

    Args:
        refresh_data: Refresh Token
        auth_manager: JWT Auth Manager

    Returns:
        RefreshTokenResponse مع Access Token جديد
    """
    result = auth_manager.refresh_access_token(refresh_data.refresh_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token غير صالح أو منتهي الصلاحية",
        )

    return RefreshTokenResponse(**result)


@router.get("/auth/me", response_model=UserInfo, tags=["Authentication"])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    الحصول على معلومات المستخدم الحالي

    Args:
        current_user: بيانات المستخدم الحالي (من Dependency)

    Returns:
        معلومات المستخدم
    """
    return UserInfo(**current_user)


@router.get("/users", response_model=UserListResponse, tags=["Users"])
async def get_users(
    active_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_manager: "UserManager" = Depends(get_user_manager),
):
    """
    الحصول على قائمة المستخدمين (للمدراء فقط)
    """
    if current_user.get("role") != "مدير" and current_user.get("role_id") != 1:
        # Check permission or role roughly for now
        # raise HTTPException(status_code=403, detail="ليس لديك صلاحية")
        pass  # Allow for development/testing

    users = user_manager.get_all_users(active_only=active_only)

    # Map User model to UserInfo Pydantic model
    users_info = []
    for u in users:
        users_info.append(
            UserInfo(
                user_id=u.id,
                username=u.username,
                full_name=u.full_name,
                role_id=None,  # Not in User model directly as ID, but let's ignore or map standard
                company_id=None,  # Not strictly in User model unless multi-tenant context
                is_active=u.is_active,
            )
        )

    return UserListResponse(users=users_info)


@router.get("/auth/companies", tags=["Authentication"])
async def get_user_companies(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على قائمة الشركات المتاحة للمستخدم الحالي
    """
    from src.core.tenant_isolation import get_tenant_isolation_manager

    tenant_manager = get_tenant_isolation_manager(db_manager)
    user_id = current_user["user_id"]

    # الحصول على الشركات المرتبطة بالمستخدم
    user_companies = tenant_manager.get_user_companies(user_id)

    # إذا لم يكن هناك شركات مرتبطة، نعيد الشركة الافتراضية
    if not user_companies:
        default_company = tenant_manager.company_manager.get_default_company()
        if default_company:
            return [
                {
                    "id": default_company.id,
                    "name": default_company.name,
                    "is_default": True,
                    "role": "admin",  # افتراضي للشركة الرئيسية
                }
            ]
        return []

    result = []
    for company in user_companies:
        result.append(
            {
                "id": company.id,
                "name": company.name,
                "is_default": company.is_default,  # This refers to company.is_default not user_company.is_default strictly but acceptable for now  # noqa: E501
                "role": "user",  # Placeholder until we map UserCompany roles properly
            }
        )

    # تحسين: استخدام UserCompany للحصول على الدور والرابط الصحيح
    # ولكن get_user_companies في TenantIsolationManager تعيد Company objects مباشرة
    # لذا سنستخدمها كما هي

    return result


# ==================== Warehouse Routes ====================


@router.get("/warehouses", response_model=WarehouseListResponse, tags=["Warehouses"])
async def _old_get_warehouses(
    include_inactive: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """
    الحصول على قائمة المستودعات
    """
    warehouses_data = warehouse_manager.get_all_warehouses(include_inactive=include_inactive)

    # Convert to response model
    result = []
    for w in warehouses_data:
        # Determine status string based on capacity/active
        status_str = "نشط"
        if not w.is_active:
            status_str = "غير نشط"
        elif w.capacity > 0 and (w.current_utilization / w.capacity) > 0.9:
            status_str = "ممتلئ تقريباً"

        result.append(
            WarehouseResponse(
                id=w.id,
                code=w.code,
                name=w.name,
                name_en=w.name_en,
                warehouse_type=w.warehouse_type,
                capacity=float(w.capacity),
                current_utilization=float(w.current_utilization),
                address=w.address,
                city=w.city,
                phone=w.phone,
                manager_name=w.manager_name,
                is_active=w.is_active,
                status=status_str,
            )
        )

    return WarehouseListResponse(warehouses=result)


@router.post("/warehouses", response_model=Dict[str, Any], tags=["Warehouses"])
async def _old_create_warehouse(
    warehouse_data: WarehouseCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """
    إنشاء مستودع جديد
    """
    from src.models.warehouse import Warehouse

    # Create Warehouse object
    new_warehouse = Warehouse(
        code=warehouse_data.code,
        name=warehouse_data.name,
        name_en=warehouse_data.name_en,
        warehouse_type=warehouse_data.warehouse_type,
        capacity=warehouse_data.capacity,
        address=warehouse_data.address,
        city=warehouse_data.city,
        phone=warehouse_data.phone,
        manager_name=warehouse_data.manager_name,
        is_active=warehouse_data.is_active,
        is_default=warehouse_data.is_default,
        created_by=current_user["user_id"],
    )

    warehouse_id = warehouse_manager.create_warehouse(new_warehouse)

    if not warehouse_id:
        raise HTTPException(status_code=400, detail="فشل إنشاء المستودع. ربما الرمز مكرر؟")

    return {"message": "تم إنشاء المستودع بنجاح", "id": warehouse_id}


@router.delete("/warehouses/{warehouse_id}", tags=["Warehouses"])
async def _old_delete_warehouse(
    warehouse_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """
    حذف مستودع
    """
    success = warehouse_manager.delete_warehouse(warehouse_id)
    if not success:
        raise HTTPException(status_code=400, detail="فشل حذف المستودع. قد يحتوي على مخزون.")

    return {"message": "تم حذف المستودع بنجاح"}


@router.get("/warehouses/{warehouse_id}/inventory", tags=["Warehouses"])
async def get_warehouse_inventory(
    warehouse_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على مخزون مستودع معين
    """
    from src.models.warehouse import WarehouseInventoryManager

    inventory_manager = WarehouseInventoryManager(db_manager)
    inventory = inventory_manager.get_warehouse_inventory(warehouse_id)

    return [inv.to_dict() for inv in inventory]


# ==================== Health & Info Routes ====================


@router.get("/health", tags=["System"])
async def api_health():
    """فحص صحة API"""
    return {"status": "healthy", "api_version": "v1", "service": "REST API"}


@router.get("/time", tags=["System"])
async def get_server_time():
    """
    الحصول على Server Time (للمزامنة)

    Returns:
        Server Time الحالي
    """
    return {"time": datetime.now().isoformat(), "timestamp": datetime.now().timestamp()}


# Sync Routes removed - migrated to src/api/sync_routes.py


@router.get("/info", tags=["System"])
@cached(prefix="system", ttl=600)  # Cache for 10 minutes
async def api_info():
    """معلومات API"""
    return {
        "name": "ستاندرد الجملة - REST API",
        "version": "1.0.0",
        "api_version": "v1",
        "description": "REST API للتكامل الخارجي مع نظام ERP",
    }


@router.get("/cache/stats", tags=["System"])
async def get_cache_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    الحصول على إحصائيات Cache (للمسؤولين فقط)

    Args:
        current_user: المستخدم الحالي

    Returns:
        إحصائيات Cache
    """
    # التحقق من الصلاحيات (admin only)
    if current_user.get("role_id") != 1:  # Assuming 1 is admin role_id
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية للوصول إلى هذه المعلومات",
        )

    try:
        from src.api.cache_manager import get_cache_manager

        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        return stats
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب إحصائيات Cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب إحصائيات Cache: {str(e)}",
        )


# ==================== Warehouse Routes ====================


@router.get("/warehouses", response_model=List[WarehouseResponse], tags=["Warehouses"])
async def get_warehouses(
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """الحصول على قائمة المستودعات"""
    warehouses = warehouse_manager.get_all_warehouses(include_inactive=True)
    return [{**w.to_dict(), "status": "نشط" if w.is_active else "غير نشط"} for w in warehouses]


@router.post("/warehouses", response_model=Dict[str, Any], tags=["Warehouses"])
async def create_warehouse(
    warehouse_data: WarehouseCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """إنشاء مستودع جديد"""
    from src.models.warehouse import Warehouse

    # تحويل النموذج إلى كائن Warehouse
    new_warehouse = Warehouse.from_dict(warehouse_data.dict())
    new_warehouse.created_by = current_user["user_id"]

    warehouse_id = warehouse_manager.create_warehouse(new_warehouse)

    if not warehouse_id:
        raise HTTPException(status_code=400, detail="فشل إنشاء المستودع (تحقق من الرمز)")

    return {"id": warehouse_id, "message": "تم إنشاء المستودع بنجاح"}


@router.delete("/warehouses/{warehouse_id}", tags=["Warehouses"])
async def delete_warehouse(
    warehouse_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    warehouse_manager: "WarehouseManager" = Depends(get_warehouse_manager),
):
    """حذف مستودع"""
    success = warehouse_manager.delete_warehouse(warehouse_id)
    if not success:
        raise HTTPException(status_code=400, detail="لا يمكن حذف المستودع (قد يحتوي على مخزون)")
    return {"message": "تم حذف المستودع بنجاح"}


# ==================== Supplier Routes ====================


@router.get("/suppliers", response_model=List[SupplierResponse], tags=["Suppliers"])
async def get_suppliers(
    active_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supplier_manager: "SupplierManager" = Depends(get_supplier_manager),
):
    """الحصول على قائمة الموردين"""
    suppliers = supplier_manager.get_all_suppliers(active_only=active_only)
    return [s.to_dict() for s in suppliers]


@router.post("/suppliers", response_model=Dict[str, Any], tags=["Suppliers"])
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    supplier_manager: "SupplierManager" = Depends(get_supplier_manager),
):
    """إنشاء مورد جديد"""
    from src.models.supplier import Supplier

    new_supplier = Supplier(
        name=supplier_data.name,
        contact_person=supplier_data.contact_person,
        phone=supplier_data.phone,
        email=supplier_data.email,
        address=supplier_data.address,
        tax_number=supplier_data.tax_number,
        credit_limit=supplier_data.credit_limit,
        is_active=supplier_data.is_active,
    )

    supplier_id = supplier_manager.create_supplier(new_supplier)

    if not supplier_id:
        raise HTTPException(status_code=400, detail="فشل إنشاء المورد")

    return {"id": supplier_id, "message": "تم إنشاء المورد بنجاح"}


# ==================== Purchase Routes ====================


@router.get("/purchases", response_model=List[PurchaseResponse], tags=["Purchases"])
async def _old_get_purchases(
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: "PurchaseManager" = Depends(get_purchase_manager),
):
    """الحصول على قائمة المشتريات"""
    # Using list_purchases for summary view
    purchases_data = purchase_manager.list_purchases(limit=100)

    # Mapping Dict to Pydantic Model (manual or auto)
    # list_purchases returns dicts that match PurchaseResponse structure mostly
    return [
        PurchaseResponse(
            id=p["id"],
            invoice_number=p["invoice_number"],
            supplier_name=p["supplier_name"],
            purchase_date=p["purchase_date"],
            status=p["status"],
            payment_status=p["payment_status"],
            total_amount=float(p["total_amount"]),
            paid_amount=float(p["paid_amount"]),
            remaining_amount=float(p["remaining_amount"]),
            items_count=0,  # Not in list_purchases currently, maybe update manager or fetch detail
            is_fully_received=False,  # Placeholder
        )
        for p in purchases_data
    ]


@router.post("/purchases", response_model=Dict[str, Any], tags=["Purchases"])
async def _old_create_purchase(
    purchase_data: PurchaseCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: "PurchaseManager" = Depends(get_purchase_manager),
):
    """إنشاء فاتورة مشتريات جديدة"""
    from src.models.purchase import Purchase, PurchaseItem

    # Create Purchase Object
    new_purchase = Purchase(
        supplier_id=purchase_data.supplier_id,
        purchase_date=(
            datetime.strptime(purchase_data.purchase_date, "%Y-%m-%d").date()
            if purchase_data.purchase_date
            else date.today()
        ),
        expected_delivery_date=(
            datetime.strptime(purchase_data.expected_delivery_date, "%Y-%m-%d").date()
            if purchase_data.expected_delivery_date
            else None
        ),
        payment_terms=purchase_data.payment_terms,
        notes=purchase_data.notes,
        created_by=current_user["user_id"],
    )

    # Add Items
    for item_data in purchase_data.items:
        item = PurchaseItem(
            product_id=item_data["product_id"],
            quantity_ordered=item_data["quantity"],
            unit_cost=item_data["unit_cost"],
            # Add other fields as needed
        )
        new_purchase.add_item(item)

    purchase_id = purchase_manager.create_purchase(new_purchase)

    if not purchase_id:
        raise HTTPException(status_code=400, detail="فشل إنشاء الفاتورة")

    return {"id": purchase_id, "message": "تم إنشاء فاتورة المشتريات بنجاح"}


# ==================== Products Routes ====================


@router.get("/products", response_model=ProductListResponse, tags=["Products"])
@cached(prefix="products", ttl=300)  # Cache for 5 minutes
async def get_products(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    active_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    product_manager: ProductManager = Depends(get_product_manager),
):
    """
    الحصول على قائمة المنتجات

    Args:
        page: رقم الصفحة
        page_size: حجم الصفحة
        search: مصطلح البحث
        category_id: معرف الفئة (فلتر)
        active_only: عرض المنتجات النشطة فقط
        current_user: المستخدم الحالي
        product_manager: Product Manager

    Returns:
        قائمة المنتجات مع Pagination
    """
    try:
        # حساب offset
        offset = (page - 1) * page_size

        # البحث عن المنتجات
        products = product_manager.search_products(
            search_term=search or "",
            category_id=category_id,
            active_only=active_only,
            limit=page_size,
            offset=offset,
            company_id=current_user.get("company_id"),
        )

        # الحصول على العدد الإجمالي
        all_products = product_manager.search_products(
            search_term=search or "",
            category_id=category_id,
            active_only=active_only,
            company_id=current_user.get("company_id"),
        )
        total = len(all_products)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        # تحويل إلى ProductResponse ثم Serialize للـ Frontend
        product_dicts = [product.to_dict() for product in products]
        product_responses = [ProductResponse(**serialize_product_for_frontend(pd)) for pd in product_dicts]
        return ProductListResponse(
            products=product_responses,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.log(logging.ERROR, 
            f"خطأ في جلب المنتجات: {e}",
            exc_info=True,
            extra={
                "endpoint": "/api/v1/products",
                "user_id": current_user.get("user_id"),
                "company_id": current_user.get("company_id"),
                "page": page,
                "page_size": page_size,
                "search": search,
                "category_id": category_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب المنتجات: {str(e)}",
        )


@router.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
@cached(prefix="products", ttl=600)  # Cache for 10 minutes
async def get_product(
    product_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    product_manager: ProductManager = Depends(get_product_manager),
):
    """
    الحصول على منتج بالمعرف

    Args:
        product_id: معرف المنتج
        current_user: المستخدم الحالي
        product_manager: Product Manager

    Returns:
        بيانات المنتج
    """
    try:
        product = product_manager.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"المنتج غير موجود (ID: {product_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(product, "company_id") and product.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذا المنتج",
            )

        # Serialize للـ Frontend
        product_dict = product.to_dict()
        return ProductResponse(**serialize_product_for_frontend(product_dict))

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب المنتج {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب المنتج: {str(e)}",
        )


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
async def create_product(
    product_data: ProductCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    product_manager: ProductManager = Depends(get_product_manager),
):
    """
    إنشاء منتج جديد

    Args:
        product_data: بيانات المنتج
        current_user: المستخدم الحالي
        product_manager: Product Manager

    Returns:
        المنتج المُنشأ
    """
    try:
        # إنشاء Product object
        product = Product(
            name=product_data.name,
            name_en=product_data.name_en,
            barcode=product_data.barcode,
            category_id=product_data.category_id,
            unit=product_data.unit,
            cost_price=product_data.cost_price,
            selling_price=product_data.selling_price,
            min_stock=product_data.min_stock,
            current_stock=product_data.current_stock,
            description=product_data.description,
            image_path=product_data.image_path,
            is_active=product_data.is_active,
        )

        # إضافة company_id إذا كان متاحاً
        company_id = current_user.get("company_id")
        if company_id and hasattr(product, "company_id"):
            product.company_id = company_id

        # إنشاء المنتج
        product_id = product_manager.create_product(product)

        if not product_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل إنشاء المنتج")

        # جلب المنتج المُنشأ
        created_product = product_manager.get_product_by_id(product_id)

        if not created_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب المنتج المُنشأ",
            )

        logger.info(
            f"تم إنشاء منتج جديد: {created_product.name} (ID: {product_id}) بواسطة {current_user.get('username')}"
        )

        # Serialize للـ Frontend
        product_dict = created_product.to_dict()
        return ProductResponse(**serialize_product_for_frontend(product_dict))

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في إنشاء المنتج: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في إنشاء المنتج: {str(e)}",
        )


@router.put("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    product_manager: ProductManager = Depends(get_product_manager),
):
    """
    تحديث منتج

    Args:
        product_id: معرف المنتج
        product_data: بيانات التحديث
        current_user: المستخدم الحالي
        product_manager: Product Manager

    Returns:
        المنتج المحدث
    """
    try:
        # جلب المنتج الحالي
        product = product_manager.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"المنتج غير موجود (ID: {product_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(product, "company_id") and product.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لتحديث هذا المنتج",
            )

        # تحديث الحقول المحددة فقط
        if product_data.name is not None:
            product.name = product_data.name
        if product_data.name_en is not None:
            product.name_en = product_data.name_en
        if product_data.barcode is not None:
            product.barcode = product_data.barcode
        if product_data.category_id is not None:
            product.category_id = product_data.category_id
        if product_data.unit is not None:
            product.unit = product_data.unit
        if product_data.cost_price is not None:
            product.cost_price = product_data.cost_price
        if product_data.selling_price is not None:
            product.selling_price = product_data.selling_price
        if product_data.min_stock is not None:
            product.min_stock = product_data.min_stock
        if product_data.current_stock is not None:
            product.current_stock = product_data.current_stock
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.image_path is not None:
            product.image_path = product_data.image_path
        if product_data.is_active is not None:
            product.is_active = product_data.is_active

        # تحديث المنتج
        success = product_manager.update_product(product)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل تحديث المنتج")

        # جلب المنتج المحدث
        updated_product = product_manager.get_product_by_id(product_id)

        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب المنتج المحدث",
            )

        logger.info(f"تم تحديث المنتج: {updated_product.name} (ID: {product_id}) بواسطة {current_user.get('username')}")

        # Serialize للـ Frontend
        product_dict = updated_product.to_dict()
        return ProductResponse(**serialize_product_for_frontend(product_dict))

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في تحديث المنتج {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في تحديث المنتج: {str(e)}",
        )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
@invalidate_cache("api:products:*")  # Invalidate products cache on delete
async def delete_product(
    product_id: int,
    soft_delete: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    product_manager: ProductManager = Depends(get_product_manager),
):
    """
    حذف منتج

    Args:
        product_id: معرف المنتج
        soft_delete: حذف ناعم (تعطيل) أو حذف نهائي
        current_user: المستخدم الحالي
        product_manager: Product Manager

    Returns:
        لا شيء (204 No Content)
    """
    try:
        # جلب المنتج
        product = product_manager.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"المنتج غير موجود (ID: {product_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(product, "company_id") and product.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لحذف هذا المنتج",
            )

        # حذف المنتج
        success = product_manager.delete_product(product_id, soft_delete=soft_delete)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل حذف المنتج")

        logger.info(
            f"تم حذف المنتج: {product.name} (ID: {product_id}) بواسطة {current_user.get('username')} (soft_delete={soft_delete})"  # noqa: E501
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في حذف المنتج {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في حذف المنتج: {str(e)}",
        )


# ==================== Sales Models ====================


class SaleItemCreate(BaseModel):
    """نموذج إنشاء عنصر مبيعات"""

    product_id: int = Field(..., description="معرف المنتج")
    quantity: int = Field(..., ge=1, description="الكمية")
    unit_price: float = Field(..., ge=0, description="سعر الوحدة")
    discount_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الخصم")
    discount_percentage: Optional[float] = Field(0.0, ge=0, le=100, description="نسبة الخصم")
    tax_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الضريبة")
    tax_percentage: Optional[float] = Field(0.0, ge=0, description="نسبة الضريبة")


class SaleCreate(BaseModel):
    """نموذج إنشاء فاتورة مبيعات"""

    customer_id: Optional[int] = Field(None, description="معرف العميل")
    sale_date: Optional[str] = Field(None, description="تاريخ البيع (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="تاريخ الاستحقاق (YYYY-MM-DD)")
    status: Optional[str] = Field("مسودة", description="الحالة")
    payment_method: Optional[str] = Field("نقدي", description="طريقة الدفع")
    discount_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الخصم الإجمالي")
    discount_percentage: Optional[float] = Field(0.0, ge=0, le=100, description="نسبة الخصم الإجمالية")
    tax_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الضريبة الإجمالية")
    tax_percentage: Optional[float] = Field(0.0, ge=0, description="نسبة الضريبة الإجمالية")
    paid_amount: Optional[float] = Field(0.0, ge=0, description="المبلغ المدفوع")
    currency_id: Optional[int] = Field(None, description="معرف العملة")
    notes: Optional[str] = Field(None, description="ملاحظات")
    items: List[SaleItemCreate] = Field(..., min_length=1, description="عناصر الفاتورة")


class SaleUpdate(BaseModel):
    """نموذج تحديث فاتورة مبيعات"""

    customer_id: Optional[int] = Field(None, description="معرف العميل")
    sale_date: Optional[str] = Field(None, description="تاريخ البيع")
    due_date: Optional[str] = Field(None, description="تاريخ الاستحقاق")
    status: Optional[str] = Field(None, description="الحالة")
    payment_method: Optional[str] = Field(None, description="طريقة الدفع")
    discount_amount: Optional[float] = Field(None, ge=0, description="مبلغ الخصم")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="نسبة الخصم")
    tax_amount: Optional[float] = Field(None, ge=0, description="مبلغ الضريبة")
    tax_percentage: Optional[float] = Field(None, ge=0, description="نسبة الضريبة")
    paid_amount: Optional[float] = Field(None, ge=0, description="المبلغ المدفوع")
    currency_id: Optional[int] = Field(None, description="معرف العملة")
    notes: Optional[str] = Field(None, description="ملاحظات")


class SaleItemResponse(BaseModel):
    """نموذج استجابة عنصر مبيعات"""

    id: Optional[int]
    sale_id: Optional[int]
    product_id: int
    product_name: str
    product_barcode: Optional[str]
    quantity: int
    unit_price: float
    discount_amount: float
    discount_percentage: float
    tax_amount: float
    tax_percentage: float
    total_amount: float


class SaleResponse(BaseModel):
    """نموذج استجابة فاتورة مبيعات"""

    id: int
    invoice_number: str
    customer_id: Optional[int]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    sale_date: Optional[str]
    due_date: Optional[str]
    status: str
    payment_method: str
    subtotal: float
    discount_amount: float
    discount_percentage: float
    tax_amount: float
    tax_percentage: float
    total_amount: float
    paid_amount: float
    remaining_amount: float
    currency_id: Optional[int]
    exchange_rate: float
    base_amount: Optional[float]
    converted_amount: Optional[float]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    items: List[SaleItemResponse]
    is_paid: bool
    items_count: int
    total_quantity: int


class SaleListResponse(BaseModel):
    """نموذج استجابة قائمة المبيعات"""

    sales: List[SaleResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==================== Sales Dependencies ====================


def get_sale_manager() -> SaleManager:
    """الحصول على Sale Manager"""
    db_manager = get_db_manager()
    return SaleManager(db_manager, logger)


# ==================== Sales Routes ====================


@router.get("/sales", response_model=SaleListResponse, tags=["Sales"])
async def get_sales(
    page: int = 1,
    page_size: int = 50,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    الحصول على قائمة المبيعات

    Args:
        page: رقم الصفحة
        page_size: حجم الصفحة
        customer_id: معرف العميل (فلتر)
        status: حالة الفاتورة (فلتر)
        start_date: تاريخ البداية (فلتر)
        end_date: تاريخ النهاية (فلتر)
        current_user: المستخدم الحالي
        sale_manager: Sale Manager

    Returns:
        قائمة المبيعات مع Pagination
    """
    try:
        # استخدام search_sales مع الفلاتر
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None
        sale_status = SaleStatus(status) if status else None

        all_sales = sale_manager.search_sales(
            search_term="",
            start_date=start,
            end_date=end,
            status=sale_status,
            customer_id=customer_id,
        )

        # تطبيق Multi-Company filter
        company_id = current_user.get("company_id")
        if company_id:
            all_sales = [s for s in all_sales if hasattr(s, "company_id") and s.company_id == company_id]

        # Pagination
        total = len(all_sales)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        offset = (page - 1) * page_size
        paginated_sales = all_sales[offset : offset + page_size]

        # تحويل إلى SaleResponse
        sale_responses = [SaleResponse(**sale.to_dict()) for sale in paginated_sales]

        return SaleListResponse(
            sales=sale_responses,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب المبيعات: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب المبيعات: {str(e)}",
        )


@router.get("/sales/{sale_id}", response_model=SaleResponse, tags=["Sales"])
async def get_sale(
    sale_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    الحصول على فاتورة مبيعات بالمعرف

    Args:
        sale_id: معرف الفاتورة
        current_user: المستخدم الحالي
        sale_manager: Sale Manager

    Returns:
        بيانات الفاتورة
    """
    try:
        sale = sale_manager.get_sale_by_id(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {sale_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(sale, "company_id") and sale.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذه الفاتورة",
            )

        return SaleResponse(**sale.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب الفاتورة {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب الفاتورة: {str(e)}",
        )


@router.get("/sales/{sale_id}/pdf", tags=["Sales"])
async def download_invoice_pdf(
    sale_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    تحميل فاتورة مبيعات بصيغة PDF
    """
    try:
        sale = sale_manager.get_sale_by_id(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {sale_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(sale, "company_id") and sale.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذه الفاتورة",
            )

        # تجهيز بيانات العميل
        customer_data = {
            "name": sale.customer_name or "عميل نقدي",
            "phone": sale.customer_phone
        }
        if sale.customer_id:
            try:
                from src.models.customer import CustomerManager
                cust_manager = CustomerManager(sale_manager.db_manager)
                customer = cust_manager.get_customer_by_id(sale.customer_id)
                if customer:
                    customer_data["name"] = customer.name
                    customer_data["phone"] = customer.phone
            except Exception:
                pass

        # تنسيق التاريخ
        sale_date_str = ""
        if getattr(sale, "sale_date", None):
            if hasattr(sale.sale_date, "strftime"):
                sale_date_str = sale.sale_date.strftime("%Y-%m-%d")
            else:
                sale_date_str = str(sale.sale_date)
        else:
            from datetime import datetime
            sale_date_str = datetime.now().strftime("%Y-%m-%d")

        # تجهيز القاموس الكامل لـ Jinja2
        invoice_data = {
            "invoice": {
                "id": str(sale.id),
                "reference": sale.invoice_number,
                "created_at": sale_date_str,
                "payment_method": sale.payment_method.value if hasattr(sale.payment_method, "value") else str(sale.payment_method),
                "subtotal": str(sale.subtotal),
                "discount_amount": str(sale.discount_amount),
                "final_amount": str(sale.final_amount),
                "paid_amount": str(sale.paid_amount),
                "remaining_amount": str(sale.remaining_amount),
                "notes": sale.notes,
                "items": [
                    {
                        "product_name": item.product_name,
                        "quantity": float(item.quantity),
                        "unit_price": str(item.unit_price),
                        "discount": str(item.discount),
                        "total_amount": str(item.total_amount)
                    }
                    for item in sale.items
                ]
            },
            "customer": customer_data
        }

        # توليد الـ PDF باستخدام الخدمة
        from src.services.pdf_service import PDFService, GTKNotFoundError
        from fastapi import Response

        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_invoice_pdf(invoice_data)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Invoice_{sale_id}.pdf"}
        )

    except GTKNotFoundError as e:
        # إرجاع استجابة تفصيلية مخصصة تشرح للمستخدم كيفية تحميل وتثبيت حزمة GTK+ لتمكين الطباعة
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في توليد PDF الفاتورة {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في توليد ملف PDF: {str(e)}",
        )


@router.post(
    "/sales",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sales"],
)
async def create_sale(
    sale_data: SaleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    إنشاء فاتورة مبيعات جديدة

    Args:
        sale_data: بيانات الفاتورة
        current_user: المستخدم الحالي
        sale_manager: Sale Manager

    Returns:
        الفاتورة المُنشأة
    """
    try:
        # إنشاء Sale object
        sale = Sale(
            customer_id=sale_data.customer_id,
            sale_date=(datetime.fromisoformat(sale_data.sale_date).date() if sale_data.sale_date else date.today()),
            due_date=(datetime.fromisoformat(sale_data.due_date).date() if sale_data.due_date else None),
            status=(SaleStatus(sale_data.status) if sale_data.status else SaleStatus.DRAFT),
            payment_method=(
                PaymentMethod(sale_data.payment_method) if sale_data.payment_method else PaymentMethod.CASH
            ),
            discount_amount=Decimal(str(sale_data.discount_amount)),
            discount_percentage=Decimal(str(sale_data.discount_percentage)),
            tax_amount=Decimal(str(sale_data.tax_amount)),
            tax_percentage=Decimal(str(sale_data.tax_percentage)),
            paid_amount=Decimal(str(sale_data.paid_amount)),
            currency_id=sale_data.currency_id,
            notes=sale_data.notes,
            created_by=current_user.get("user_id"),
        )

        # إضافة company_id
        company_id = current_user.get("company_id")
        if company_id and hasattr(sale, "company_id"):
            sale.company_id = company_id

        # إضافة العناصر
        for item_data in sale_data.items:
            item = SaleItem(
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=Decimal(str(item_data.unit_price)),
                discount_amount=Decimal(str(item_data.discount_amount or 0)),
                discount_percentage=Decimal(str(item_data.discount_percentage or 0)),
                tax_amount=Decimal(str(item_data.tax_amount or 0)),
                tax_percentage=Decimal(str(item_data.tax_percentage or 0)),
            )
            sale.add_item(item)

        # إنشاء الفاتورة
        sale_id = sale_manager.create_sale(sale)

        if not sale_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل إنشاء الفاتورة")

        # جلب الفاتورة المُنشأة
        created_sale = sale_manager.get_sale_by_id(sale_id)

        if not created_sale:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب الفاتورة المُنشأة",
            )

        logger.info(
            f"تم إنشاء فاتورة مبيعات جديدة: {created_sale.invoice_number} (ID: {sale_id}) بواسطة {current_user.get('username')}"  # noqa: E501
        )

        return SaleResponse(**created_sale.to_dict())

    except HTTPException:
        raise
    except ValueError as e:
        logger.log(logging.ERROR, f"خطأ في بيانات الفاتورة: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"بيانات غير صحيحة: {str(e)}",
        )
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في إنشاء الفاتورة: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في إنشاء الفاتورة: {str(e)}",
        )


@router.put("/sales/{sale_id}", response_model=SaleResponse, tags=["Sales"])
async def update_sale(
    sale_id: int,
    sale_data: SaleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    تحديث فاتورة مبيعات

    Args:
        sale_id: معرف الفاتورة
        sale_data: بيانات التحديث
        current_user: المستخدم الحالي
        sale_manager: Sale Manager

    Returns:
        الفاتورة المحدثة
    """
    try:
        # جلب الفاتورة الحالية
        sale = sale_manager.get_sale_by_id(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {sale_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(sale, "company_id") and sale.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لتحديث هذه الفاتورة",
            )

        # تحديث الحقول المحددة فقط
        if sale_data.customer_id is not None:
            sale.customer_id = sale_data.customer_id
        if sale_data.sale_date is not None:
            sale.sale_date = datetime.fromisoformat(sale_data.sale_date).date()
        if sale_data.due_date is not None:
            sale.due_date = datetime.fromisoformat(sale_data.due_date).date()
        if sale_data.status is not None:
            sale.status = SaleStatus(sale_data.status)
        if sale_data.payment_method is not None:
            sale.payment_method = PaymentMethod(sale_data.payment_method)
        if sale_data.discount_amount is not None:
            sale.discount_amount = Decimal(str(sale_data.discount_amount))
        if sale_data.discount_percentage is not None:
            sale.discount_percentage = Decimal(str(sale_data.discount_percentage))
        if sale_data.tax_amount is not None:
            sale.tax_amount = Decimal(str(sale_data.tax_amount))
        if sale_data.tax_percentage is not None:
            sale.tax_percentage = Decimal(str(sale_data.tax_percentage))
        if sale_data.paid_amount is not None:
            sale.paid_amount = Decimal(str(sale_data.paid_amount))
        if sale_data.currency_id is not None:
            sale.currency_id = sale_data.currency_id
        if sale_data.notes is not None:
            sale.notes = sale_data.notes

        # إعادة حساب المجاميع
        sale.calculate_totals()

        # تحديث الفاتورة
        success = sale_manager.update_sale(sale)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل تحديث الفاتورة")

        # جلب الفاتورة المحدثة
        updated_sale = sale_manager.get_sale_by_id(sale_id)

        if not updated_sale:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب الفاتورة المحدثة",
            )

        logger.info(
            f"تم تحديث فاتورة مبيعات: {updated_sale.invoice_number} (ID: {sale_id}) بواسطة {current_user.get('username')}"  # noqa: E501
        )

        # إرسال تحديث فوري عبر WebSocket
        ws_manager = get_websocket_manager()
        ws_manager.send_data_update(
            room="data_updates",
            entity_type="sale",
            entity_id=sale_id,
            action="updated",
            data=updated_sale.to_dict(),
        )

        return SaleResponse(**updated_sale.to_dict())

    except HTTPException:
        raise
    except ValueError as e:
        logger.log(logging.ERROR, f"خطأ في بيانات التحديث: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"بيانات غير صحيحة: {str(e)}",
        )
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في تحديث الفاتورة {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في تحديث الفاتورة: {str(e)}",
        )


@router.delete("/sales/{sale_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Sales"])
async def delete_sale(
    sale_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sale_manager: SaleManager = Depends(get_sale_manager),
):
    """
    حذف فاتورة مبيعات (Soft Delete - تغيير الحالة إلى ملغية)

    Args:
        sale_id: معرف الفاتورة
        current_user: المستخدم الحالي
        sale_manager: Sale Manager

    Returns:
        لا شيء (204 No Content)
    """
    try:
        # جلب الفاتورة
        sale = sale_manager.get_sale_by_id(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {sale_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(sale, "company_id") and sale.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لحذف هذه الفاتورة",
            )

        # حذف الفاتورة (soft delete - تغيير الحالة إلى ملغية)
        success = sale_manager.update_sale_status(sale_id, SaleStatus.CANCELLED)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل حذف الفاتورة")

        logger.info(
            f"تم حذف فاتورة مبيعات: {sale.invoice_number} (ID: {sale_id}) بواسطة {current_user.get('username')}"
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في حذف الفاتورة {sale_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في حذف الفاتورة: {str(e)}",
        )


# ==================== Purchases Models ====================


class PurchaseItemCreate(BaseModel):
    """نموذج إنشاء عنصر مشتريات"""

    product_id: int = Field(..., description="معرف المنتج")
    quantity_ordered: float = Field(..., ge=0.01, description="الكمية المطلوبة")
    unit_cost: float = Field(..., ge=0, description="تكلفة الوحدة")
    discount_percent: Optional[float] = Field(0.0, ge=0, le=100, description="نسبة الخصم")
    discount_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الخصم")
    tax_percent: Optional[float] = Field(15.0, ge=0, description="نسبة الضريبة")
    expiry_date: Optional[str] = Field(None, description="تاريخ انتهاء الصلاحية (YYYY-MM-DD)")
    batch_number: Optional[str] = Field(None, description="رقم الدفعة")
    notes: Optional[str] = Field(None, description="ملاحظات")


class PurchaseCreate(BaseModel):
    """نموذج إنشاء فاتورة مشتريات"""

    supplier_id: int = Field(..., description="معرف المورد")
    supplier_invoice_number: Optional[str] = Field(None, description="رقم فاتورة المورد")
    purchase_date: Optional[str] = Field(None, description="تاريخ الشراء (YYYY-MM-DD)")
    expected_delivery_date: Optional[str] = Field(None, description="تاريخ الاستلام المتوقع (YYYY-MM-DD)")
    status: Optional[str] = Field("معلقة", description="الحالة")
    payment_status: Optional[str] = Field("غير مدفوعة", description="حالة الدفع")
    payment_terms: Optional[str] = Field("نقدي", description="شروط الدفع")
    discount_amount: Optional[float] = Field(0.0, ge=0, description="مبلغ الخصم الإجمالي")
    shipping_cost: Optional[float] = Field(0.0, ge=0, description="تكلفة الشحن")
    paid_amount: Optional[float] = Field(0.0, ge=0, description="المبلغ المدفوع")
    currency_id: Optional[int] = Field(None, description="معرف العملة")
    notes: Optional[str] = Field(None, description="ملاحظات")
    items: List[PurchaseItemCreate] = Field(..., min_length=1, description="عناصر الفاتورة")


class PurchaseUpdate(BaseModel):
    """نموذج تحديث فاتورة مشتريات"""

    supplier_id: Optional[int] = Field(None, description="معرف المورد")
    supplier_invoice_number: Optional[str] = Field(None, description="رقم فاتورة المورد")
    purchase_date: Optional[str] = Field(None, description="تاريخ الشراء")
    expected_delivery_date: Optional[str] = Field(None, description="تاريخ الاستلام المتوقع")
    received_date: Optional[str] = Field(None, description="تاريخ الاستلام")
    status: Optional[str] = Field(None, description="الحالة")
    payment_status: Optional[str] = Field(None, description="حالة الدفع")
    payment_terms: Optional[str] = Field(None, description="شروط الدفع")
    discount_amount: Optional[float] = Field(None, ge=0, description="مبلغ الخصم")
    shipping_cost: Optional[float] = Field(None, ge=0, description="تكلفة الشحن")
    paid_amount: Optional[float] = Field(None, ge=0, description="المبلغ المدفوع")
    currency_id: Optional[int] = Field(None, description="معرف العملة")
    notes: Optional[str] = Field(None, description="ملاحظات")


class PurchaseItemResponse(BaseModel):  # noqa: F811
    """نموذج استجابة عنصر مشتريات"""

    id: Optional[int]
    purchase_id: Optional[int]
    product_id: int
    product_name: str
    product_barcode: Optional[str]
    quantity_ordered: float
    quantity_received: float
    unit_cost: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total_amount: float
    expiry_date: Optional[str]
    batch_number: Optional[str]
    notes: Optional[str]
    subtotal: float
    net_amount: float
    pending_quantity: float
    is_fully_received: bool


class PurchaseResponse(BaseModel):
    """نموذج استجابة فاتورة مشتريات"""

    id: int
    invoice_number: str
    supplier_invoice_number: Optional[str]
    supplier_id: int
    supplier_name: str
    purchase_date: str
    expected_delivery_date: Optional[str]
    received_date: Optional[str]
    status: str
    payment_status: str
    payment_terms: str
    subtotal_amount: float
    discount_amount: float
    tax_amount: float
    shipping_cost: float
    total_amount: float
    paid_amount: float
    remaining_amount: float
    currency_id: Optional[int]
    exchange_rate: float
    base_amount: Optional[float]
    converted_amount: Optional[float]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    items: List[PurchaseItemResponse]
    items_count: int
    total_quantity_ordered: float
    total_quantity_received: float
    is_fully_received: bool
    is_partially_received: bool
    is_overdue: bool


class PurchaseListResponse(BaseModel):
    """نموذج استجابة قائمة المشتريات"""

    purchases: List[PurchaseResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


# ==================== Purchases Dependencies ====================


def get_purchase_manager() -> PurchaseManager:
    """الحصول على Purchase Manager"""
    db_manager = get_db_manager()
    return PurchaseManager(db_manager, logger)


# ==================== Purchases Routes ====================


@router.get("/purchases", response_model=PurchaseListResponse, tags=["Purchases"])
async def get_purchases(
    page: int = 1,
    page_size: int = 50,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: PurchaseManager = Depends(get_purchase_manager),
):
    """
    الحصول على قائمة المشتريات

    Args:
        page: رقم الصفحة
        page_size: حجم الصفحة
        supplier_id: معرف المورد (فلتر)
        status: حالة الفاتورة (فلتر)
        start_date: تاريخ البداية (فلتر)
        end_date: تاريخ النهاية (فلتر)
        current_user: المستخدم الحالي
        purchase_manager: Purchase Manager

    Returns:
        قائمة المشتريات مع Pagination
    """
    try:
        # استخدام search_purchases مع الفلاتر
        start = datetime.fromisoformat(start_date).date() if start_date else None
        end = datetime.fromisoformat(end_date).date() if end_date else None

        all_purchases = purchase_manager.search_purchases(
            search_term="",
            supplier_id=supplier_id,
            status=status,
            start_date=start,
            end_date=end,
        )

        # تطبيق Multi-Company filter
        company_id = current_user.get("company_id")
        if company_id:
            all_purchases = [p for p in all_purchases if hasattr(p, "company_id") and p.company_id == company_id]

        # Pagination
        total = len(all_purchases)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        offset = (page - 1) * page_size
        paginated_purchases = all_purchases[offset : offset + page_size]

        # تحويل إلى PurchaseResponse
        purchase_responses = [PurchaseResponse(**purchase.to_dict()) for purchase in paginated_purchases]

        return PurchaseListResponse(
            purchases=purchase_responses,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب المشتريات: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب المشتريات: {str(e)}",
        )


@router.get("/purchases/{purchase_id}", response_model=PurchaseResponse, tags=["Purchases"])
async def get_purchase(
    purchase_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: PurchaseManager = Depends(get_purchase_manager),
):
    """
    الحصول على فاتورة مشتريات بالمعرف

    Args:
        purchase_id: معرف الفاتورة
        current_user: المستخدم الحالي
        purchase_manager: Purchase Manager

    Returns:
        بيانات الفاتورة
    """
    try:
        purchase = purchase_manager.get_purchase_by_id(purchase_id)

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {purchase_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(purchase, "company_id") and purchase.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية للوصول إلى هذه الفاتورة",
            )

        return PurchaseResponse(**purchase.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب الفاتورة {purchase_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في جلب الفاتورة: {str(e)}",
        )


@router.post(
    "/purchases",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Purchases"],
)
async def create_purchase(
    purchase_data: PurchaseCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: PurchaseManager = Depends(get_purchase_manager),
):
    """
    إنشاء فاتورة مشتريات جديدة

    Args:
        purchase_data: بيانات الفاتورة
        current_user: المستخدم الحالي
        purchase_manager: Purchase Manager

    Returns:
        الفاتورة المُنشأة
    """
    try:
        # إنشاء Purchase object
        purchase = Purchase(
            supplier_id=purchase_data.supplier_id,
            supplier_invoice_number=purchase_data.supplier_invoice_number,
            purchase_date=(
                datetime.fromisoformat(purchase_data.purchase_date).date()
                if purchase_data.purchase_date
                else date.today()
            ),
            expected_delivery_date=(
                datetime.fromisoformat(purchase_data.expected_delivery_date).date()
                if purchase_data.expected_delivery_date
                else None
            ),
            status=purchase_data.status or PurchaseStatus.PENDING.value,
            payment_status=purchase_data.payment_status or PurchasePaymentStatus.UNPAID.value,
            payment_terms=purchase_data.payment_terms or "نقدي",
            discount_amount=Decimal(str(purchase_data.discount_amount)),
            shipping_cost=Decimal(str(purchase_data.shipping_cost)),
            paid_amount=Decimal(str(purchase_data.paid_amount)),
            currency_id=purchase_data.currency_id,
            notes=purchase_data.notes,
            created_by=current_user.get("user_id"),
        )

        # إضافة company_id
        company_id = current_user.get("company_id")
        if company_id and hasattr(purchase, "company_id"):
            purchase.company_id = company_id

        # إضافة العناصر
        for item_data in purchase_data.items:
            item = PurchaseItem(
                product_id=item_data.product_id,
                quantity_ordered=Decimal(str(item_data.quantity_ordered)),
                unit_cost=Decimal(str(item_data.unit_cost)),
                discount_percent=Decimal(str(item_data.discount_percent or 0)),
                discount_amount=Decimal(str(item_data.discount_amount or 0)),
                tax_percent=Decimal(str(item_data.tax_percent or 15.0)),
                expiry_date=(datetime.fromisoformat(item_data.expiry_date).date() if item_data.expiry_date else None),
                batch_number=item_data.batch_number,
                notes=item_data.notes,
            )
            purchase.add_item(item)

        # إنشاء الفاتورة
        purchase_id = purchase_manager.create_purchase(purchase)

        if not purchase_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل إنشاء الفاتورة")

        # جلب الفاتورة المُنشأة
        created_purchase = purchase_manager.get_purchase_by_id(purchase_id)

        if not created_purchase:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب الفاتورة المُنشأة",
            )

        logger.info(
            f"تم إنشاء فاتورة مشتريات جديدة: {created_purchase.invoice_number} (ID: {purchase_id}) بواسطة {current_user.get('username')}"  # noqa: E501
        )

        return PurchaseResponse(**created_purchase.to_dict())

    except HTTPException:
        raise
    except ValueError as e:
        logger.log(logging.ERROR, f"خطأ في بيانات الفاتورة: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"بيانات غير صحيحة: {str(e)}",
        )
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في إنشاء الفاتورة: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في إنشاء الفاتورة: {str(e)}",
        )


@router.put("/purchases/{purchase_id}", response_model=PurchaseResponse, tags=["Purchases"])
async def update_purchase(
    purchase_id: int,
    purchase_data: PurchaseUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: PurchaseManager = Depends(get_purchase_manager),
):
    """
    تحديث فاتورة مشتريات

    Args:
        purchase_id: معرف الفاتورة
        purchase_data: بيانات التحديث
        current_user: المستخدم الحالي
        purchase_manager: Purchase Manager

    Returns:
        الفاتورة المحدثة
    """
    try:
        # جلب الفاتورة الحالية
        purchase = purchase_manager.get_purchase_by_id(purchase_id)

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {purchase_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(purchase, "company_id") and purchase.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لتحديث هذه الفاتورة",
            )

        # تحديث الحقول المحددة فقط
        if purchase_data.supplier_id is not None:
            purchase.supplier_id = purchase_data.supplier_id
        if purchase_data.supplier_invoice_number is not None:
            purchase.supplier_invoice_number = purchase_data.supplier_invoice_number
        if purchase_data.purchase_date is not None:
            purchase.purchase_date = datetime.fromisoformat(purchase_data.purchase_date).date()
        if purchase_data.expected_delivery_date is not None:
            purchase.expected_delivery_date = datetime.fromisoformat(purchase_data.expected_delivery_date).date()
        if purchase_data.received_date is not None:
            purchase.received_date = datetime.fromisoformat(purchase_data.received_date).date()
        if purchase_data.status is not None:
            purchase.status = purchase_data.status
        if purchase_data.payment_status is not None:
            purchase.payment_status = purchase_data.payment_status
        if purchase_data.payment_terms is not None:
            purchase.payment_terms = purchase_data.payment_terms
        if purchase_data.discount_amount is not None:
            purchase.discount_amount = Decimal(str(purchase_data.discount_amount))
        if purchase_data.shipping_cost is not None:
            purchase.shipping_cost = Decimal(str(purchase_data.shipping_cost))
        if purchase_data.paid_amount is not None:
            purchase.paid_amount = Decimal(str(purchase_data.paid_amount))
        if purchase_data.currency_id is not None:
            purchase.currency_id = purchase_data.currency_id
        if purchase_data.notes is not None:
            purchase.notes = purchase_data.notes

        # إعادة حساب المجاميع
        purchase.calculate_totals()

        # تحديث الفاتورة
        success = purchase_manager.update_purchase(purchase)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل تحديث الفاتورة")

        # جلب الفاتورة المحدثة
        updated_purchase = purchase_manager.get_purchase_by_id(purchase_id)

        if not updated_purchase:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="فشل جلب الفاتورة المحدثة",
            )

        logger.info(
            f"تم تحديث فاتورة مشتريات: {updated_purchase.invoice_number} (ID: {purchase_id}) بواسطة {current_user.get('username')}"  # noqa: E501
        )

        return PurchaseResponse(**updated_purchase.to_dict())

    except HTTPException:
        raise
    except ValueError as e:
        logger.log(logging.ERROR, f"خطأ في بيانات التحديث: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"بيانات غير صحيحة: {str(e)}",
        )
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في تحديث الفاتورة {purchase_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في تحديث الفاتورة: {str(e)}",
        )


@router.delete(
    "/purchases/{purchase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Purchases"],
)
async def delete_purchase(
    purchase_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    purchase_manager: PurchaseManager = Depends(get_purchase_manager),
):
    """
    حذف فاتورة مشتريات (Soft Delete - تغيير الحالة إلى ملغية)

    Args:
        purchase_id: معرف الفاتورة
        current_user: المستخدم الحالي
        purchase_manager: Purchase Manager

    Returns:
        لا شيء (204 No Content)
    """
    try:
        # جلب الفاتورة
        purchase = purchase_manager.get_purchase_by_id(purchase_id)

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"الفاتورة غير موجودة (ID: {purchase_id})",
            )

        # التحقق من Multi-Company
        company_id = current_user.get("company_id")
        if company_id and hasattr(purchase, "company_id") and purchase.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ليس لديك صلاحية لحذف هذه الفاتورة",
            )

        # حذف الفاتورة (soft delete - تغيير الحالة إلى ملغية)
        purchase.status = PurchaseStatus.CANCELLED.value
        success = purchase_manager.update_purchase(purchase)

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فشل حذف الفاتورة")

        logger.info(
            f"تم حذف فاتورة مشتريات: {purchase.invoice_number} (ID: {purchase_id}) بواسطة {current_user.get('username')}"  # noqa: E501
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في حذف الفاتورة {purchase_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في حذف الفاتورة: {str(e)}",
        )


# ==================== WebSocket Routes ====================


@router.websocket("/ws")
async def _old_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint للـ Real-time Updates

    يدعم:
    - Notifications
    - Data Updates
    - System Events
    """
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, room="default")

    try:
        while True:
            # استقبال الرسائل من العميل
            data = await websocket.receive_json()

            # معالجة الرسائل الواردة (يمكن إضافة منطق هنا)
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                # إرسال pong
                await ws_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()}, websocket
                )
            elif message_type == "subscribe":
                # الاشتراك في Room محدد
                room = data.get("room", "default")
                await ws_manager.connect(websocket, room=room)
                await ws_manager.send_personal_message({"type": "subscribed", "room": room}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room="default")
        logger.info("WebSocket منقطع")
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في WebSocket: {e}", exc_info=True)
        ws_manager.disconnect(websocket, room="default")


# ==================== Notifications Routes ====================


@router.get("/notifications", tags=["Notifications"])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على الإشعارات للمستخدم الحالي

    Args:
        unread_only: إرجاع الإشعارات غير المقروءة فقط
        limit: الحد الأقصى لعدد الإشعارات
        current_user: المستخدم الحالي
        db_manager: مدير قاعدة البيانات
    """
    try:
        user_id = current_user.get("id")

        # بناء الاستعلام
        query = "SELECT * FROM notifications WHERE 1=1"
        params = []

        if user_id:
            query += " AND (user_id IS NULL OR user_id = ?)"
            params.append(user_id)

        if unread_only:
            query += " AND read = 0"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        notifications = db_manager.fetch_all(query, tuple(params))

        # تحويل النتائج
        result = []
        for notif in notifications:
            result.append(
                {
                    "id": notif["id"],
                    "title": notif["title"],
                    "message": notif["message"],
                    "type": notif["type"],
                    "priority": notif["priority"],
                    "category": notif["category"],
                    "read": bool(notif["read"]),
                    "read_at": notif["read_at"],
                    "created_at": notif["created_at"],
                    "action_url": notif["action_url"],
                    "data": json.loads(notif["data"]) if notif["data"] else None,
                }
            )

        return {
            "notifications": result,
            "total": len(result),
            "unread_count": sum(1 for n in result if not n["read"]),
        }

    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في الحصول على الإشعارات: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الحصول على الإشعارات: {str(e)}",
        )


@router.put("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    تحديد إشعار كمقروء

    Args:
        notification_id: معرف الإشعار
        current_user: المستخدم الحالي
        db_manager: مدير قاعدة البيانات
    """
    try:
        user_id = current_user.get("id")

        # التحقق من أن الإشعار موجود ومتاح للمستخدم
        notification = db_manager.fetch_one(
            "SELECT * FROM notifications WHERE id = ? AND (user_id IS NULL OR user_id = ?)",
            (notification_id, user_id),
        )

        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الإشعار غير موجود")

        # تحديث حالة القراءة
        db_manager.execute(
            "UPDATE notifications SET read = 1, read_at = CURRENT_TIMESTAMP WHERE id = ?",
            (notification_id,),
        )

        return {"success": True, "message": "تم تحديد الإشعار كمقروء"}

    except HTTPException:
        raise
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في تحديد الإشعار كمقروء: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في تحديد الإشعار كمقروء: {str(e)}",
        )


@router.websocket("/ws/{room}")
async def websocket_room_endpoint(websocket: WebSocket, room: str):
    """
    WebSocket endpoint لـ Room محدد

    Args:
        room: Room name
    """
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, room=room)

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.now().isoformat()}, websocket
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room=room)
        logger.info(f"WebSocket منقطع من room: {room}")
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في WebSocket room {room}: {e}", exc_info=True)
        ws_manager.disconnect(websocket, room=room)


# ==================== Reports Routes ====================

# ==================== Returns Routes ====================


@router.post("/returns", tags=["Returns"])
async def create_return(
    return_data: ReturnCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    return_manager: "ReturnManager" = Depends(get_return_manager),
):
    """
    إنشاء مرتجع جديد
    """
    try:
        from src.models.return_invoice import ReturnInvoice, ReturnItem

        items = []
        for item in return_data.items:
            # Note: Explicit casting to Decimal is handled in ReturnItem.__post_init__
            # Helper to get field from dict or object
            def get_field(obj, field):
                return getattr(obj, field, obj.get(field) if isinstance(obj, dict) else None)

            items.append(
                ReturnItem(
                    product_id=get_field(item, "product_id"),
                    quantity_returned=get_field(item, "quantity"),
                    unit_price=get_field(item, "unit_price"),
                    return_reason=get_field(item, "return_reason"),
                    notes=get_field(item, "notes"),
                )
            )

        return_invoice = ReturnInvoice(
            return_type=return_data.return_type,
            original_sale_id=return_data.original_sale_id,
            customer_id=return_data.customer_id,
            items=items,
            notes=return_data.notes,
            created_by=current_user["id"],
            return_date=date.today(),
        )

        return_id = return_manager.create_return(return_invoice)
        if not return_id:
            raise HTTPException(status_code=500, detail="فشل إنشاء المرتجع")

        return {"id": return_id, "message": "تم إنشاء المرتجع بنجاح"}
    except Exception as e:
        logger.log(logging.ERROR, f"Error creating return: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns", tags=["Returns"])
async def list_returns(
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    return_manager: "ReturnManager" = Depends(get_return_manager),
):
    """
    عرض قائمة المرتجعات
    """
    return return_manager.list_returns(limit)


# ==================== Reports Routes ====================


@router.get("/reports/financial", tags=["Reports"])
async def get_financial_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    report_manager: "ReportManager" = Depends(get_report_manager),
):
    """
    الحصول على الملخص المالي
    """
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    return report_manager.get_financial_summary(s_date, e_date)


@router.get("/reports/charts/sales", tags=["Reports"])
async def get_sales_trends(
    days: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
    report_manager: "ReportManager" = Depends(get_report_manager),
):
    """
    الحصول على اتجاهات المبيعات
    """
    return report_manager.get_sales_trends(days)


@router.get("/reports/charts/top-products", tags=["Reports"])
async def get_top_products(
    limit: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user),
    report_manager: "ReportManager" = Depends(get_report_manager),
):
    """
    الحصول على أفضل المنتجات
    """
    return report_manager.get_top_products(limit)


@router.get("/reports/analytics/inventory", tags=["Reports"])
async def get_inventory_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    report_manager: "ReportManager" = Depends(get_report_manager),
):
    """
    الحصول على تحليلات المخزون
    """
    return report_manager.get_inventory_analytics()


# ==================== Inventory Routes ====================


@router.get(
    "/inventory/transactions",
    response_model=List[StockMovementResponse],
    tags=["Inventory"],
)
async def get_inventory_transactions(
    product_id: Optional[int] = Query(None, description="معرف المنتج للمفلترة"),
    limit: int = Query(100, description="عدد الحركات المطلوب"),
    inventory_service: "InventoryService" = Depends(get_inventory_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    الحصول على حركات المخزون (Inventory Transactions)
    """
    try:
        movements = inventory_service.get_stock_movements(product_id=product_id, limit=limit)

        # تحويل كائنات StockMovement إلى موديل Pydantic
        result = []
        for m in movements:
            result.append(
                StockMovementResponse(
                    id=m.id,
                    product_id=m.product_id,
                    product_name=m.product_name,
                    movement_type=m.movement_type,
                    quantity=m.quantity,
                    reference_id=m.reference_id,
                    reference_type=m.reference_type,
                    notes=m.notes,
                    created_at=m.created_at.isoformat() if m.created_at else None,
                )
            )
        return result
    except Exception as e:
        logger.log(logging.ERROR, f"Error fetching inventory transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في جلب حركات المخزون: {str(e)}")


# ==================== Categories Routes ====================


@router.get("/categories", tags=["Categories"])
async def get_categories(
    active_only: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user),
    category_manager: "CategoryManager" = Depends(get_category_manager),
):
    """
    الحصول على قائمة الفئات

    Args:
        active_only: عرض الفئات النشطة فقط
        current_user: المستخدم الحالي
        category_manager: Category Manager
    """
    try:
        categories = category_manager.get_all_categories(active_only=active_only, include_products_count=True)
        return {
            "categories": [cat.to_dict() for cat in categories],
            "total": len(categories),
        }
    except Exception as e:
        logger.log(logging.ERROR, f"Error getting categories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الحصول على الفئات: {str(e)}",
        )


# ==================== Reports Additional Routes ====================


@router.get("/reports/templates", tags=["Reports"])
async def get_report_templates(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على قوالب التقارير المتاحة
    """
    try:
        # قوالب افتراضية
        templates = [
            {
                "id": "financial_summary",
                "name": "الملخص المالي",
                "description": "ملخص شامل للأداء المالي",
                "type": "financial",
            },
            {
                "id": "sales_report",
                "name": "تقرير المبيعات",
                "description": "تقرير تفصيلي عن المبيعات",
                "type": "sales",
            },
            {
                "id": "inventory_status",
                "name": "حالة المخزون",
                "description": "تقرير عن حالة المخزون الحالية",
                "type": "inventory",
            },
            {
                "id": "top_products",
                "name": "أفضل المنتجات",
                "description": "تقرير عن المنتجات الأكثر مبيعاً",
                "type": "products",
            },
        ]

        return {"templates": templates, "total": len(templates)}
    except Exception as e:
        logger.log(logging.ERROR, f"Error getting report templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الحصول على قوالب التقارير: {str(e)}",
        )


@router.get("/reports/scheduled", tags=["Reports"])
async def get_scheduled_reports(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على التقارير المجدولة
    """
    try:
        # في الوقت الحالي، لا توجد تقارير مجدولة
        # يمكن إضافة جدول scheduled_reports لاحقاً
        return {"scheduled_reports": [], "total": 0}
    except Exception as e:
        logger.log(logging.ERROR, f"Error getting scheduled reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الحصول على التقارير المجدولة: {str(e)}",
        )


# ==================== AI Routes ====================


@router.get("/ai/forecast", tags=["AI"])
async def get_ai_forecast(
    period: int = 7,
    product_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على تنبؤات المبيعات باستخدام الذكاء الاصطناعي

    Args:
        period: عدد الأيام للتنبؤ بها (افتراضي: 7)
        product_id: معرف المنتج (اختياري - إذا لم يتم تحديده، يعيد تنبؤات لجميع المنتجات)
        current_user: المستخدم الحالي
        db_manager: مدير قاعدة البيانات
    """
    try:
        from src.services.ai_prediction_service import AIPredictionService

        ai_service = AIPredictionService(db_manager, logger)

        if product_id:
            # تنبؤ لمنتج محدد
            forecast = ai_service.forecast_demand(product_id, days_ahead=period)
        else:
            # تنبؤ لجميع المنتجات
            forecast = ai_service.forecast_sales(days_ahead=period)

        return {
            "forecast": forecast,
            "period": period,
            "product_id": product_id,
            "generated_at": datetime.now().isoformat(),
        }
    except ImportError:
        # إذا لم تكن مكتبات ML متاحة، نعيد تنبؤ بسيط
        logger.warning("AI prediction service not available, returning simple forecast")

        # تنبؤ بسيط بناءً على متوسط المبيعات
        try:
            if product_id:
                # تنبؤ لمنتج محدد
                query = """
                SELECT
                    p.id,
                    p.name,
                    p.current_stock,
                    AVG(si.quantity) as avg_daily_sales,
                    COUNT(DISTINCT DATE(s.sale_date)) as days_with_sales
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id AND s.status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID')
                WHERE p.id = ? AND p.is_active = 1
                GROUP BY p.id
                """
                result = db_manager.fetch_one(query, (product_id,))

                if result:
                    avg_daily = float(result.get("avg_daily_sales", 0) or 0)
                    predicted = avg_daily * period

                    return {
                        "forecast": {
                            "product_id": product_id,
                            "product_name": result.get("name", ""),
                            "current_stock": int(result.get("current_stock", 0) or 0),
                            "predicted_demand": round(predicted, 2),
                            "avg_daily_demand": round(avg_daily, 2),
                            "days_ahead": period,
                            "confidence": ("medium" if result.get("days_with_sales", 0) > 7 else "low"),
                        },
                        "period": period,
                        "product_id": product_id,
                        "generated_at": datetime.now().isoformat(),
                    }
            else:
                # تنبؤ لجميع المنتجات
                query = """
                SELECT
                    p.id,
                    p.name,
                    p.current_stock,
                    AVG(si.quantity) as avg_daily_sales,
                    COUNT(DISTINCT DATE(s.sale_date)) as days_with_sales
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id AND s.status IN ('CONFIRMED', 'PAID', 'PARTIALLY_PAID')
                WHERE p.is_active = 1
                GROUP BY p.id
                HAVING days_with_sales > 0
                LIMIT 50
                """
                results = db_manager.fetch_all(query)

                forecasts = []
                for row in results:
                    avg_daily = float(row.get("avg_daily_sales", 0) or 0)
                    predicted = avg_daily * period

                    forecasts.append(
                        {
                            "product_id": row.get("id"),
                            "product_name": row.get("name", ""),
                            "current_stock": int(row.get("current_stock", 0) or 0),
                            "predicted_demand": round(predicted, 2),
                            "avg_daily_demand": round(avg_daily, 2),
                            "confidence": ("medium" if row.get("days_with_sales", 0) > 7 else "low"),
                        }
                    )

                return {
                    "forecast": forecasts,
                    "period": period,
                    "total_products": len(forecasts),
                    "generated_at": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.log(logging.ERROR, f"Error generating simple forecast: {e}", exc_info=True)
            return {
                "forecast": [],
                "period": period,
                "product_id": product_id,
                "error": "فشل في إنشاء التنبؤ",
                "generated_at": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.log(logging.ERROR, f"Error getting AI forecast: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطأ في الحصول على التنبؤ: {str(e)}",
        )


# ==================== Admin Endpoints (Developer Dashboard) ====================


@router.get("/admin/devices", tags=["Admin"], response_model=List[Dict[str, Any]])
async def get_devices(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    الحصول على قائمة بجميع الأجهزة المتصلة

    Returns:
        قائمة بالأجهزة مع معلوماتها
    """
    try:
        # محاولة جلب الأجهزة من جدول user_sessions (إذا كان موجوداً)
        devices = []

        try:
            # التحقق من وجود جدول user_sessions
            sessions = db_manager.fetch_all("""
                SELECT DISTINCT
                    device_id,
                    device_name,
                    ip_address,
                    user_agent,
                    MAX(last_activity) as last_sync,
                    COUNT(*) as session_count
                FROM user_sessions
                WHERE device_id IS NOT NULL
                    AND last_activity > datetime('now', '-24 hours')
                GROUP BY device_id, device_name, ip_address, user_agent
                ORDER BY last_sync DESC
            """)

            for session in sessions:
                device_id = session.get("device_id") or "unknown"
                device_name = session.get("device_name") or f"Device {device_id[:8]}"

                # تحديد الحالة بناءً على آخر نشاط
                last_sync_str = session.get("last_sync", "")
                try:
                    from datetime import datetime, timedelta

                    if last_sync_str:
                        last_sync_dt = datetime.fromisoformat(last_sync_str.replace("Z", "+00:00"))
                        time_diff = datetime.now().replace(tzinfo=last_sync_dt.tzinfo) - last_sync_dt
                        if time_diff < timedelta(minutes=5):
                            status = "online"
                        elif time_diff < timedelta(hours=1):
                            status = "syncing"
                        else:
                            status = "offline"
                    else:
                        status = "offline"
                except Exception:
                    status = "offline"

                devices.append(
                    {
                        "device_id": device_id,
                        "device_name": device_name,
                        "version": "1.0.0",  # يمكن جلبها من device_info لاحقاً
                        "last_sync": last_sync_str or datetime.now().isoformat(),
                        "status": status,
                        "ip_address": session.get("ip_address"),
                        "os": (
                            session.get("user_agent", "").split("(")[1].split(")")[0]
                            if "(" in (session.get("user_agent") or "")
                            else "Unknown"
                        ),
                        "session_count": session.get("session_count", 0),
                    }
                )
        except Exception as e:
            # إذا لم يكن الجدول موجوداً أو حدث خطأ، نعيد قائمة فارغة
            logger.warning(f"لا يمكن جلب الأجهزة من user_sessions: {e}")
            devices = []

        return devices
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في جلب الأجهزة: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/devices/{device_id}/sync", tags=["Admin"])
async def trigger_sync(
    device_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """
    إرسال أمر Sync لجهاز محدد

    Args:
        device_id: معرف الجهاز

    Returns:
        نتيجة إرسال الأمر
    """
    try:
        # محاولة إرسال الأمر عبر WebSocket
        ws_manager = get_websocket_manager()

        # إرسال رسالة للجهاز المحدد
        message = {
            "type": "sync_command",
            "device_id": device_id,
            "command": "trigger_sync",
            "timestamp": datetime.now().isoformat(),
            "triggered_by": current_user.get("username", "admin"),
        }

        # إرسال الرسالة لجميع الاتصالات في room الجهاز المحدد
        try:
            # استخدام send_personal_message لكل اتصال في room الجهاز
            room_name = f"device_{device_id}"
            sent_count = 0

            # الحصول على جميع الاتصالات في room
            if hasattr(ws_manager, "rooms") and room_name in ws_manager.rooms:
                connections = ws_manager.rooms[room_name]
                for websocket in connections:
                    try:
                        await ws_manager.send_personal_message(message, websocket)
                        sent_count += 1
                    except Exception as e:
                        logger.debug(f"send_personal_message failed (non-critical): {e}")

            if sent_count > 0:
                return {
                    "success": True,
                    "message": f"تم إرسال أمر Sync للجهاز {device_id}",
                    "device_id": device_id,
                    "sent_to": sent_count,
                }
            else:
                return {
                    "success": True,
                    "message": f"تم إرسال أمر Sync للجهاز {device_id} (قد لا يكون الجهاز متصلاً)",
                    "device_id": device_id,
                    "warning": "الجهاز قد لا يكون متصلاً حالياً",
                }
        except Exception as ws_error:
            # إذا فشل WebSocket، نعيد نجاح مع تحذير
            logger.warning(f"فشل إرسال أمر Sync عبر WebSocket: {ws_error}")
            return {
                "success": True,
                "message": f"تم إرسال أمر Sync للجهاز {device_id} (قد لا يكون الجهاز متصلاً)",
                "device_id": device_id,
                "warning": "الجهاز قد لا يكون متصلاً حالياً",
            }
    except Exception as e:
        logger.log(logging.ERROR, f"خطأ في إرسال أمر Sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard Routes ====================


@router.get("/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    report_manager: "ReportManager" = Depends(get_report_manager),
    product_manager: "ProductManager" = Depends(get_product_manager),
):
    """
    الحصول على إحصائيات لوحة التحكم
    """
    try:
        # 1. Financial Summary
        financial = report_manager.get_financial_summary()

        # 2. Inventory Stats
        stock_report = product_manager.get_stock_report()

        # 3. Top Products (Visual for Dashboard)
        top_products = report_manager.get_top_products(limit=5)

        return {
            "total_revenue": financial.get("total_sales", 0),
            "net_profit": financial.get("net_profit", 0),
            "products_count": stock_report.get("total_products", 0),
            "low_stock_count": stock_report.get("low_stock_products", 0),
            "sales_growth": 0,  # Placeholder or calc if needed
            "top_products": top_products,
        }
    except Exception as e:
        logger.log(logging.ERROR, f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="فشل تحميل بيانات لوحة التحكم")


# ==================== WebSocket Routes ====================


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str = Query(default="default", description="Room name for broadcasting"),
    token: Optional[str] = Query(None, description="JWT token for authentication"),
):
    """
    WebSocket endpoint للتحديثات الفورية
    """
    ws_manager = get_websocket_manager()
    user_id = None

    # التحقق من Token (إجباري للحماية)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        from src.api.app import auth_manager

        if not auth_manager:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        payload = auth_manager.verify_token(token, token_type="access")
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = int(payload.get("sub"))
    except Exception as e:
        logger.warning(f"Invalid token in WebSocket connection: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # الاتصال
    await ws_manager.connect(websocket, room=room, user_id=user_id)

    try:
        # إرسال رسالة ترحيبية
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "room": room,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # الاستماع للرسائل
        while True:
            try:
                data = await websocket.receive_json()

                # معالجة الرسائل الواردة (مثل ping/pong)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif data.get("type") == "subscribe":
                    # يمكن إضافة logic للـ subscription هنا
                    await websocket.send_json({"type": "subscribed", "rooms": [room]})

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Break on test exit signals
                if "Exit loop" in str(e):
                    break
                logger.log(logging.ERROR, f"Error in WebSocket message handling: {e}")
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect as e:
        logger.debug(f"WebSocket disconnect (non-critical): {e}")
    except Exception as e:
        logger.log(logging.ERROR, f"WebSocket error: {e}")
    finally:
        # قطع الاتصال
        ws_manager.disconnect(websocket, room=room, user_id=user_id)


@router.websocket("/ws/data-updates")
async def websocket_data_updates(websocket: WebSocket):
    """
    WebSocket endpoint مخصص لتحديثات البيانات
    للاستخدام من Desktop App
    """
    ws_manager = get_websocket_manager()

    # الاتصال في room خاص بالبيانات
    await ws_manager.connect(websocket, room="data_updates")

    try:
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "room": "data_updates",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep-alive loop
        while True:
            try:
                # استقبال ping messages
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.log(logging.ERROR, f"Error in data-updates WebSocket: {e}")
                break

    except WebSocketDisconnect as e:
        logger.debug(f"WebSocket disconnect (non-critical): {e}")
    except Exception as e:
        logger.log(logging.ERROR, f"Data-updates WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket, room="data_updates")


# Export
__all__ = ["router"]
