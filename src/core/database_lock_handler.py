#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Lock Handler - معالج قفل قاعدة البيانات
معالجة أخطاء القفل وإعادة المحاولة
"""

import sqlite3
import time
from typing import Callable, Any, Optional
from functools import wraps
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# SQLite lock error codes
SQLITE_BUSY = 5
SQLITE_LOCKED = 6
SQLITE_IOERR = 10
SQLITE_PROTOCOL = 15

# Maximum retry attempts
MAX_RETRIES = 5
# Initial delay in seconds
INITIAL_DELAY = 0.1
# Maximum delay in seconds
MAX_DELAY = 2.0
# Backoff multiplier
BACKOFF_MULTIPLIER = 2.0


def is_lock_error(error: Exception) -> bool:
    """
    التحقق من أن الخطأ هو خطأ قفل قاعدة البيانات
    
    Args:
        error: الاستثناء المراد فحصه
        
    Returns:
        True إذا كان خطأ قفل
    """
    if isinstance(error, sqlite3.OperationalError):
        error_msg = str(error).lower()
        return any(keyword in error_msg for keyword in [
            'database is locked',
            'database locked',
            'unable to open database',
            'disk i/o error',
            'disk i/o',
            'io error'
        ])
    
    if isinstance(error, sqlite3.DatabaseError):
        error_code = getattr(error, 'sqlite_errorcode', None)
        if error_code in [SQLITE_BUSY, SQLITE_LOCKED, SQLITE_IOERR, SQLITE_PROTOCOL]:
            return True
    
    return False


def calculate_retry_delay(attempt: int) -> float:
    """
    حساب وقت الانتظار قبل إعادة المحاولة (exponential backoff)
    
    Args:
        attempt: رقم المحاولة (يبدأ من 1)
        
    Returns:
        وقت الانتظار بالثواني
    """
    delay = INITIAL_DELAY * (BACKOFF_MULTIPLIER ** (attempt - 1))
    return min(delay, MAX_DELAY)


def retry_on_lock_error(
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_DELAY,
    max_delay: float = MAX_DELAY,
    backoff_multiplier: float = BACKOFF_MULTIPLIER
):
    """
    Decorator لإعادة المحاولة عند أخطاء قفل قاعدة البيانات
    
    Args:
        max_retries: الحد الأقصى لعدد المحاولات
        initial_delay: التأخير الأولي بالثواني
        max_delay: الحد الأقصى للتأخير بالثواني
        backoff_multiplier: مضاعف التأخير
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    if is_lock_error(e):
                        last_error = e
                        
                        if attempt < max_retries:
                            delay = calculate_retry_delay(attempt)
                            logger.warning(
                                f"خطأ قفل قاعدة البيانات في {func.__name__} (المحاولة {attempt}/{max_retries}). "
                                f"إعادة المحاولة بعد {delay:.2f} ثانية..."
                            )
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"فشل {func.__name__} بعد {max_retries} محاولات. "
                                f"الخطأ الأخير: {e}"
                            )
                    else:
                        # خطأ آخر غير قفل - إعادة رفعه مباشرة
                        raise
            
            # إذا وصلنا هنا، فشلت جميع المحاولات
            if last_error:
                raise last_error
            else:
                raise RuntimeError(f"فشل {func.__name__} بدون خطأ محدد")
        
        return wrapper
    return decorator


class DatabaseLockHandler:
    """
    معالج قفل قاعدة البيانات
    يوفر وظائف لإعادة المحاولة عند أخطاء القفل
    """
    
    def __init__(
        self,
        max_retries: int = MAX_RETRIES,
        initial_delay: float = INITIAL_DELAY,
        max_delay: float = MAX_DELAY,
        backoff_multiplier: float = BACKOFF_MULTIPLIER
    ):
        """
        تهيئة معالج القفل
        
        Args:
            max_retries: الحد الأقصى لعدد المحاولات
            initial_delay: التأخير الأولي بالثواني
            max_delay: الحد الأقصى للتأخير بالثواني
            backoff_multiplier: مضاعف التأخير
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.logger = setup_logger(__name__)
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        تنفيذ دالة مع إعادة المحاولة عند أخطاء القفل
        
        Args:
            func: الدالة المراد تنفيذها
            *args: المعاملات الموضعية
            **kwargs: المعاملات المسماة
            
        Returns:
            نتيجة تنفيذ الدالة
            
        Raises:
            sqlite3.OperationalError: إذا فشلت جميع المحاولات
        """
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                if is_lock_error(e):
                    last_error = e
                    
                    if attempt < self.max_retries:
                        delay = calculate_retry_delay(attempt)
                        self.logger.warning(
                            f"خطأ قفل قاعدة البيانات (المحاولة {attempt}/{self.max_retries}). "
                            f"إعادة المحاولة بعد {delay:.2f} ثانية..."
                        )
                        time.sleep(delay)
                    else:
                        self.logger.error(
                            f"فشل بعد {self.max_retries} محاولات. الخطأ الأخير: {e}"
                        )
                else:
                    # خطأ آخر غير قفل - إعادة رفعه مباشرة
                    raise
        
        # إذا وصلنا هنا، فشلت جميع المحاولات
        if last_error:
            raise last_error
        else:
            raise RuntimeError("فشل بدون خطأ محدد")
    
    def check_database_health(self, connection: sqlite3.Connection) -> bool:
        """
        فحص صحة قاعدة البيانات والاتصال
        
        Args:
            connection: اتصال قاعدة البيانات
            
        Returns:
            True إذا كانت قاعدة البيانات صحية
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            self.logger.error(f"خطأ في فحص صحة قاعدة البيانات: {e}")
            return False

