#!/usr/bin/env python3
"""
API Client للتطبيق - يدعم الوضع المحلي والسحابي
Hybrid Mode: يعمل محليًا أو عبر API حسب توفر الاتصال
"""
import requests
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import time
import logging

from src.utils.logger import setup_logger

class APIClient:
    """
    عميل API هجين يدعم:
    - الوضع المحلي (Offline): الوصول المباشر لقاعدة البيانات
    - الوضع السحابي (Online): الاتصال بـ API
    - Retry Logic مع Exponential Backoff
    - Request/Response Logging
    """
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: int = 5,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        retry_status_codes: Optional[List[int]] = None,
        enable_logging: bool = True
    ):
        """
        تهيئة عميل API
        
        Args:
            base_url: عنوان الـ API (افتراضي: localhost)
            timeout: وقت انتظار الاتصال بالثواني
            max_retries: عدد محاولات إعادة المحاولة (افتراضي: 3)
            retry_backoff_factor: عامل الانتظار الأسي (افتراضي: 0.5)
                الانتظار = retry_backoff_factor * (2 ** attempt_number)
            retry_status_codes: قائمة أكواد الحالة التي تستدعي إعادة المحاولة
                (افتراضي: [500, 502, 503, 504])
            enable_logging: تفعيل تسجيل الطلبات (افتراضي: True)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.retry_status_codes = retry_status_codes or [500, 502, 503, 504]
        self.enable_logging = enable_logging
        
        self.token: Optional[str] = None
        self._is_online: Optional[bool] = None
        self._last_check: Optional[datetime] = None
        
        # Logger
        self.logger = setup_logger(__name__) if enable_logging else logging.getLogger(__name__)
    
    def is_online(self, force_check: bool = False) -> bool:
        """
        التحقق من توفر الاتصال بالـ API
        
        Args:
            force_check: إجبار الفحص حتى لو تم مؤخرًا
            
        Returns:
            True إذا كان API متاحًا
        """
        # فحص مخزن مؤقت (لا تفحص أكثر من مرة كل 10 ثوانٍ)
        if not force_check and self._last_check:
            elapsed = (datetime.now() - self._last_check).total_seconds()
            if elapsed < 10 and self._is_online is not None:
                return self._is_online
        
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            self._is_online = response.status_code == 200
        except Exception:
            self._is_online = False
        
        self._last_check = datetime.now()
        return self._is_online
    
    def login(self, username: str, password: str) -> bool:
        """
        تسجيل الدخول والحصول على JWT Token مع Retry Logic
        
        Args:
            username: اسم المستخدم
            password: كلمة المرور
            
        Returns:
            True في حالة النجاح
        """
        if not self.is_online():
            return False
        
        # تسجيل الدخول لا يحتاج retry (أخطاء المصادقة لا يجب إعادة المحاولة)
        response = self._make_request(
            "POST",
            "/api/v1/auth/login",
            json_data={"username": username, "password": password}
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access_token")
                if self.enable_logging:
                    self.logger.info(f"تم تسجيل الدخول بنجاح للمستخدم: {username}")
                return True
            except ValueError:
                if self.enable_logging:
                    self.logger.warning("فشل تحويل استجابة تسجيل الدخول إلى JSON")
                return False
        
        if self.enable_logging:
            self.logger.warning(f"فشل تسجيل الدخول للمستخدم: {username}")
        
        return False
    
    def _should_retry(self, status_code: int, exception: Optional[Exception] = None) -> bool:
        """
        تحديد ما إذا كان يجب إعادة المحاولة
        
        Args:
            status_code: كود حالة HTTP
            exception: استثناء (إن وجد)
            
        Returns:
            True إذا كان يجب إعادة المحاولة
        """
        # إعادة المحاولة في حالة أخطاء الشبكة
        if exception:
            return isinstance(exception, (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException
            ))
        
        # إعادة المحاولة في حالة أكواد الحالة المحددة
        return status_code in self.retry_status_codes
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        حساب وقت الانتظار باستخدام Exponential Backoff
        
        Args:
            attempt: رقم المحاولة (0-based)
            
        Returns:
            وقت الانتظار بالثواني
        """
        return self.retry_backoff_factor * (2 ** attempt)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Optional[requests.Response]:
        """
        تنفيذ طلب HTTP مع Retry Logic و Exponential Backoff
        
        Args:
            method: طريقة HTTP (GET, POST, PUT, DELETE)
            endpoint: مسار الـ endpoint
            params: معاملات الاستعلام (لـ GET)
            data: البيانات (لـ POST/PUT)
            json_data: بيانات JSON (لـ POST/PUT)
            
        Returns:
            Response object أو None في حالة الفشل
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # تسجيل المحاولة
                if self.enable_logging and attempt > 0:
                    self.logger.debug(
                        f"إعادة محاولة {attempt}/{self.max_retries} للطلب: {method} {url}"
                    )
                
                # تنفيذ الطلب
                if method.upper() == "GET":
                    response = requests.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = requests.post(
                        url,
                        json=json_data or data,
                        headers=headers,
                        timeout=self.timeout
                    )
                elif method.upper() == "PUT":
                    response = requests.put(
                        url,
                        json=json_data or data,
                        headers=headers,
                        timeout=self.timeout
                    )
                elif method.upper() == "DELETE":
                    response = requests.delete(
                        url,
                        headers=headers,
                        timeout=self.timeout
                    )
                else:
                    raise ValueError(f"طريقة HTTP غير مدعومة: {method}")
                
                # تسجيل الاستجابة
                if self.enable_logging:
                    self.logger.debug(
                        f"API Request: {method} {url} - "
                        f"Status: {response.status_code} - "
                        f"Attempt: {attempt + 1}/{self.max_retries + 1}"
                    )
                
                # التحقق من الحاجة لإعادة المحاولة
                if self._should_retry(response.status_code):
                    if attempt < self.max_retries:
                        backoff_time = self._calculate_backoff(attempt)
                        if self.enable_logging:
                            self.logger.warning(
                                f"طلب فاشل (Status: {response.status_code}) - "
                                f"إعادة المحاولة بعد {backoff_time:.2f} ثانية"
                            )
                        time.sleep(backoff_time)
                        continue
                    else:
                        if self.enable_logging:
                            self.logger.error(
                                f"فشل الطلب بعد {self.max_retries + 1} محاولات: "
                                f"{method} {url} - Status: {response.status_code}"
                            )
                        return None
                
                # نجح الطلب
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                # التحقق من الحاجة لإعادة المحاولة
                if self._should_retry(0, e) and attempt < self.max_retries:
                    backoff_time = self._calculate_backoff(attempt)
                    if self.enable_logging:
                        self.logger.warning(
                            f"خطأ في الاتصال: {str(e)} - "
                            f"إعادة المحاولة بعد {backoff_time:.2f} ثانية"
                        )
                    time.sleep(backoff_time)
                    continue
                else:
                    if self.enable_logging:
                        self.logger.error(
                            f"فشل الطلب بعد {attempt + 1} محاولات: {method} {url} - {str(e)}"
                        )
                    return None
            
            except Exception as e:
                # أخطاء غير متوقعة - لا إعادة محاولة
                if self.enable_logging:
                    self.logger.error(f"خطأ غير متوقع في الطلب: {method} {url} - {str(e)}")
                return None
        
        # فشل جميع المحاولات
        if self.enable_logging and last_exception:
            self.logger.error(
                f"فشل الطلب نهائياً بعد {self.max_retries + 1} محاولات: "
                f"{method} {url} - {str(last_exception)}"
            )
        
        return None
    
    def _get_headers(self) -> Dict[str, str]:
        """الحصول على Headers مع Token"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        طلب GET من API مع Retry Logic
        
        Args:
            endpoint: مسار الـ endpoint (بدون base_url)
            params: معاملات الاستعلام
            
        Returns:
            البيانات المسترجعة أو None
        """
        if not self.is_online():
            return None
        
        response = self._make_request("GET", endpoint, params=params)
        
        if response and response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                if self.enable_logging:
                    self.logger.warning(f"فشل تحويل الاستجابة إلى JSON: {endpoint}")
                return None
        
        return None
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        طلب POST إلى API مع Retry Logic
        
        Args:
            endpoint: مسار الـ endpoint
            data: البيانات المراد إرسالها
            
        Returns:
            الاستجابة أو None
        """
        if not self.is_online():
            return None
        
        response = self._make_request("POST", endpoint, json_data=data)
        
        if response and response.status_code in [200, 201]:
            try:
                return response.json()
            except ValueError:
                if self.enable_logging:
                    self.logger.warning(f"فشل تحويل الاستجابة إلى JSON: {endpoint}")
                return None
        
        return None
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        طلب PUT إلى API مع Retry Logic
        
        Args:
            endpoint: مسار الـ endpoint
            data: البيانات المراد إرسالها
            
        Returns:
            الاستجابة أو None
        """
        if not self.is_online():
            return None
        
        response = self._make_request("PUT", endpoint, json_data=data)
        
        if response and response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                if self.enable_logging:
                    self.logger.warning(f"فشل تحويل الاستجابة إلى JSON: {endpoint}")
                return None
        
        return None
    
    def delete(self, endpoint: str) -> bool:
        """
        طلب DELETE إلى API مع Retry Logic
        
        Args:
            endpoint: مسار الـ endpoint
            
        Returns:
            True إذا نجح الحذف
        """
        if not self.is_online():
            return False
        
        response = self._make_request("DELETE", endpoint)
        
        return response is not None and response.status_code in [200, 204]


class HybridDataService:
    """
    خدمة بيانات هجينة تدعم الوضع المحلي والسحابي
    """
    
    def __init__(self, db_manager, api_client: APIClient):
        """
        تهيئة الخدمة الهجينة
        
        Args:
            db_manager: مدير قاعدة البيانات المحلية
            api_client: عميل API
        """
        self.db = db_manager
        self.api = api_client
    
    def get_products(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """
        الحصول على المنتجات (هجين)
        
        يحاول من API أولاً، ثم يعود للقاعدة المحلية
        """
        # محاولة API أولاً
        if self.api.is_online():
            result = self.api.get("products", {"page": page, "page_size": page_size})
            if result:
                return result.get("items", [])
        
        # العودة للقاعدة المحلية
        offset = (page - 1) * page_size
        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT id, name, barcode, unit, selling_price, current_stock "
                "FROM products ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return [dict(zip(columns, row)) for row in rows]
    
    def create_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """
        إنشاء منتج جديد (هجين)
        """
        # محاولة API أولاً
        if self.api.is_online():
            result = self.api.post("products", product_data)
            if result:
                # مزامنة مع القاعدة المحلية
                self._sync_product_to_local(result)
                return result.get("id")
        
        # إنشاء محليًا
        with self.db.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO products(name, barcode, unit, cost_price, selling_price,
                                   current_stock, created_at, updated_at)
                VALUES(?,?,?,?,?,?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (
                    product_data.get("name"),
                    product_data.get("barcode"),
                    product_data.get("unit", "قطعة"),
                    product_data.get("cost_price", 0),
                    product_data.get("selling_price", 0),
                    product_data.get("current_stock", 0)
                )
            )
            product_id = cur.lastrowid
            cur.connection.commit()
            
            # إضافة لقائمة المزامنة
            self._mark_for_sync("product", product_id, "create")
            
            return product_id
    
    def _sync_product_to_local(self, product: Dict[str, Any]):
        """
        مزامنة منتج من API إلى القاعدة المحلية
        
        Args:
            product: بيانات المنتج من API
        """
        try:
            product_id = product.get('id')
            if not product_id:
                return
            
            with self.db.get_cursor() as cur:
                # التحقق من وجود المنتج
                cur.execute("SELECT id FROM products WHERE id = ?", (product_id,))
                exists = cur.fetchone()
                
                if exists:
                    # تحديث المنتج الموجود
                    cur.execute("""
                        UPDATE products SET
                            name = ?,
                            barcode = ?,
                            unit = ?,
                            cost_price = ?,
                            selling_price = ?,
                            current_stock = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        product.get('name'),
                        product.get('barcode'),
                        product.get('unit', 'قطعة'),
                        product.get('cost_price', 0),
                        product.get('selling_price', 0),
                        product.get('current_stock', 0),
                        product_id
                    ))
                else:
                    # إدراج منتج جديد
                    cur.execute("""
                        INSERT INTO products (
                            id, name, barcode, unit, cost_price, selling_price,
                            current_stock, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        product_id,
                        product.get('name'),
                        product.get('barcode'),
                        product.get('unit', 'قطعة'),
                        product.get('cost_price', 0),
                        product.get('selling_price', 0),
                        product.get('current_stock', 0)
                    ))
                
                cur.connection.commit()
        except Exception:
            # في حالة فشل، نتجاهل (لا نريد إيقاف العملية)
            pass
    
    def _mark_for_sync(self, entity_type: str, entity_id: int, operation: str):
        """
        تعليم عملية للمزامنة لاحقًا عند توفر الاتصال
        
        Args:
            entity_type: نوع الكيان (product, customer, sale...)
            entity_id: معرف الكيان
            operation: نوع العملية (create, update, delete)
        """
        with self.db.get_cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0
                )
                """
            )
            
            cur.execute(
                "INSERT INTO sync_queue(entity_type, entity_id, operation) VALUES(?,?,?)",
                (entity_type, entity_id, operation)
            )
            cur.connection.commit()
    
    def sync_pending_changes(self) -> Dict[str, int]:
        """
        مزامنة التغييرات المعلقة مع API
        
        Returns:
            إحصائيات المزامنة
        """
        if not self.api.is_online():
            return {"synced": 0, "failed": 0, "pending": 0}
        
        synced = 0
        failed = 0
        
        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT id, entity_type, entity_id, operation FROM sync_queue WHERE synced = 0"
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            pending_items = [dict(zip(columns, row)) for row in rows]
            
            for item in pending_items:
                try:
                    item_id = item.get('id') if isinstance(item, dict) else item[0]
                    entity_type = item.get('entity_type') if isinstance(item, dict) else item[1]
                    entity_id = item.get('entity_id') if isinstance(item, dict) else item[2]
                    operation = item.get('operation') if isinstance(item, dict) else item[3]
                    
                    # تنفيذ المزامنة حسب نوع الكيان والعملية
                    success = False
                    
                    if entity_type == "product":
                        if operation == "create":
                            # الحصول على المنتج من قاعدة البيانات المحلية
                            product = self.db.execute_query(
                                "SELECT * FROM products WHERE id = ?",
                                (entity_id,)
                            )
                            if product:
                                # إرسال إلى API
                                result = self.api.post("products", product[0] if isinstance(product, list) else product)
                                success = result is not None
                        elif operation == "update":
                            product = self.db.execute_query(
                                "SELECT * FROM products WHERE id = ?",
                                (entity_id,)
                            )
                            if product:
                                result = self.api.put(f"products/{entity_id}", product[0] if isinstance(product, list) else product)
                                success = result is not None
                        elif operation == "delete":
                            success = self.api.delete(f"products/{entity_id}")
                    
                    elif entity_type == "sale":
                        if operation == "create":
                            sale = self.db.execute_query(
                                "SELECT * FROM sales WHERE id = ?",
                                (entity_id,)
                            )
                            if sale:
                                result = self.api.post("sales", sale[0] if isinstance(sale, list) else sale)
                                success = result is not None
                        elif operation == "update":
                            sale = self.db.execute_query(
                                "SELECT * FROM sales WHERE id = ?",
                                (entity_id,)
                            )
                            if sale:
                                result = self.api.put(f"sales/{entity_id}", sale[0] if isinstance(sale, list) else sale)
                                success = result is not None
                        elif operation == "delete":
                            success = self.api.delete(f"sales/{entity_id}")
                    
                    # تعليم كمزامنة إذا نجحت
                    if success:
                        cur.execute("UPDATE sync_queue SET synced = 1 WHERE id = ?", (item_id,))
                        synced += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
            
            cur.connection.commit()
        
        return {
            "synced": synced,
            "failed": failed,
            "pending": len(pending_items) - synced - failed
        }
