#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate Limiter للـ REST API
Rate Limiting for REST API
"""

from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import hashlib

from src.utils.logger import setup_logger


class APIRateLimiter:
    """Rate Limiter للـ API"""
    
    def __init__(
        self,
        default_max_requests: int = 100,
        default_window_seconds: int = 60,
        per_endpoint_limits: Optional[Dict[str, Dict[str, int]]] = None
    ):
        """
        تهيئة Rate Limiter
        
        Args:
            default_max_requests: الحد الافتراضي للطلبات في النافذة الزمنية
            default_window_seconds: النافذة الزمنية الافتراضية بالثواني
            per_endpoint_limits: حدود مخصصة لكل endpoint
                مثال: {
                    "/api/auth/login": {"max_requests": 5, "window_seconds": 60},
                    "/api/products": {"max_requests": 200, "window_seconds": 60}
                }
        """
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds
        self.per_endpoint_limits = per_endpoint_limits or {}
        
        # تتبع الطلبات: {identifier: [(timestamp, endpoint), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        
        self.logger = setup_logger(__name__)
    
    def _get_identifier(self, ip_address: str, user_id: Optional[int] = None) -> str:
        """
        الحصول على معرف فريد للمستخدم/IP
        
        Args:
            ip_address: عنوان IP
            user_id: معرف المستخدم (اختياري)
            
        Returns:
            معرف فريد
        """
        if user_id:
            # استخدام user_id إذا كان متاحاً (أكثر دقة)
            return f"user_{user_id}"
        else:
            # استخدام IP address
            return f"ip_{ip_address}"
    
    def _get_limit(self, endpoint: str) -> Tuple[int, int]:
        """
        الحصول على الحد المخصص لـ endpoint
        
        Args:
            endpoint: مسار الـ endpoint
            
        Returns:
            (max_requests, window_seconds)
        """
        # البحث عن حد مخصص
        for path, limits in self.per_endpoint_limits.items():
            if endpoint.startswith(path):
                return limits.get("max_requests", self.default_max_requests), \
                       limits.get("window_seconds", self.default_window_seconds)
        
        return self.default_max_requests, self.default_window_seconds
    
    def is_allowed(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None
    ) -> Tuple[bool, int, Optional[int]]:
        """
        التحقق من السماح بالطلب
        
        Args:
            ip_address: عنوان IP
            endpoint: مسار الـ endpoint
            user_id: معرف المستخدم (اختياري)
            
        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        identifier = self._get_identifier(ip_address, user_id)
        max_requests, window_seconds = self._get_limit(endpoint)
        
        with self._lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # تنظيف الطلبات القديمة
            key = f"{identifier}:{endpoint}"
            self._requests[key] = [
                req_time for req_time in self._requests[key]
                if req_time > cutoff
            ]
            
            # التحقق من الحد
            current_count = len(self._requests[key])
            
            if current_count >= max_requests:
                # حساب الوقت المتبقي حتى يمكن إرسال طلب جديد
                if self._requests[key]:
                    oldest_request = min(self._requests[key])
                    retry_after = int((oldest_request + timedelta(seconds=window_seconds) - now).total_seconds())
                    retry_after = max(0, retry_after)
                else:
                    retry_after = window_seconds
                
                self.logger.warning(
                    f"Rate limit exceeded: {identifier} on {endpoint} "
                    f"({current_count}/{max_requests} requests)"
                )
                return False, 0, retry_after
            
            # إضافة الطلب الحالي
            self._requests[key].append(now)
            
            remaining = max_requests - current_count - 1
            
            return True, remaining, None
    
    def reset(self, ip_address: str, endpoint: Optional[str] = None, user_id: Optional[int] = None):
        """
        إعادة تعيين عداد الطلبات
        
        Args:
            ip_address: عنوان IP
            endpoint: مسار الـ endpoint (اختياري - إذا لم يتم تحديده، يتم إعادة تعيين جميع الـ endpoints)
            user_id: معرف المستخدم (اختياري)
        """
        identifier = self._get_identifier(ip_address, user_id)
        
        with self._lock:
            if endpoint:
                key = f"{identifier}:{endpoint}"
                if key in self._requests:
                    del self._requests[key]
            else:
                # حذف جميع الطلبات لهذا المعرف
                keys_to_delete = [k for k in self._requests.keys() if k.startswith(f"{identifier}:")]
                for key in keys_to_delete:
                    del self._requests[key]
    
    def get_stats(self, ip_address: str, endpoint: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        الحصول على إحصائيات Rate Limiting
        
        Args:
            ip_address: عنوان IP
            endpoint: مسار الـ endpoint (اختياري)
            user_id: معرف المستخدم (اختياري)
            
        Returns:
            إحصائيات Rate Limiting
        """
        identifier = self._get_identifier(ip_address, user_id)
        max_requests, window_seconds = self._get_limit(endpoint or "")
        
        with self._lock:
            if endpoint:
                key = f"{identifier}:{endpoint}"
                current_count = len(self._requests.get(key, []))
            else:
                # عدد الطلبات لجميع الـ endpoints
                current_count = sum(
                    len(requests) for key, requests in self._requests.items()
                    if key.startswith(f"{identifier}:")
                )
            
            return {
                "identifier": identifier,
                "endpoint": endpoint or "all",
                "current_requests": current_count,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "remaining_requests": max(0, max_requests - current_count)
            }
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """
        تنظيف الإدخالات القديمة
        
        Args:
            max_age_hours: الحد الأقصى لعمر الإدخالات بالساعات
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._lock:
            for key in list(self._requests.keys()):
                self._requests[key] = [
                    req_time for req_time in self._requests[key]
                    if req_time > cutoff
                ]
                
                # حذف المفاتيح الفارغة
                if not self._requests[key]:
                    del self._requests[key]
        
        self.logger.debug(f"تم تنظيف إدخالات Rate Limiter الأقدم من {max_age_hours} ساعة")

