#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Service
خدمة تحميل الصور بشكل كسول (Lazy Loading) - لا BLOB في قاعدة البيانات
"""

import os
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QThread, Signal, QObject
from src.utils.logger import setup_logger
from src.api.thread_pool_manager import ThreadPoolManager, BaseRunnable


class ImageDownloadSignals(QObject):
    """إشارات تحميل الصور"""
    image_loaded = Signal(str, QPixmap)  # url, pixmap
    download_failed = Signal(str, str)  # url, error


class ImageDownloadRunnable(BaseRunnable):
    """Runnable لتحميل الصور في الخلفية"""
    
    def __init__(self, url: str, cache_path: Path, signals: Optional[ImageDownloadSignals] = None):
        super().__init__()
        self.url = url
        self.cache_path = cache_path
        self.signals = signals or ImageDownloadSignals()
    
    def run(self):
        """تحميل الصورة"""
        try:
            # حساب hash للـ URL
            url_hash = hashlib.md5(self.url.encode()).hexdigest()
            local_path = self.cache_path / f"{url_hash}.jpg"  # يمكن تحديد الامتداد من URL
            
            # تحميل الصورة
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            
            # حفظ الصورة
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # تحميل QPixmap
            pixmap = QPixmap(str(local_path))
            if not pixmap.isNull():
                self.signals.image_loaded.emit(self.url, pixmap)
            else:
                self.signals.download_failed.emit(self.url, "فشل تحميل الصورة")
                
        except Exception as e:
            self.signals.download_failed.emit(self.url, str(e))


class ImageService:
    """خدمة إدارة الصور (Lazy Loading)"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        تهيئة خدمة الصور
        
        Args:
            cache_dir: مجلد التخزين المؤقت (اختياري - سيتم تحديده تلقائياً)
        """
        self.logger = setup_logger(__name__)
        
        # تحديد مجلد التخزين المؤقت
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.cache_dir = project_root / "cache" / "images"
        else:
            self.cache_dir = cache_dir
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread Pool Manager
        self.thread_pool = ThreadPoolManager.get_instance()
        
        # Cache للصور المحملة
        self._pixmap_cache: Dict[str, QPixmap] = {}
    
    def get_image(self, url: str, placeholder: Optional[QPixmap] = None) -> QPixmap:
        """
        الحصول على صورة (Lazy Loading)
        
        Args:
            url: رابط الصورة
            placeholder: صورة بديلة أثناء التحميل
            
        Returns:
            QPixmap للصورة (أو placeholder)
        """
        if not url:
            return placeholder or QPixmap()
        
        # التحقق من Cache
        if url in self._pixmap_cache:
            return self._pixmap_cache[url]
        
        # حساب hash للـ URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        local_path = self.cache_dir / f"{url_hash}.jpg"
        
        # التحقق من وجود الصورة محلياً
        if local_path.exists():
            try:
                pixmap = QPixmap(str(local_path))
                if not pixmap.isNull():
                    self._pixmap_cache[url] = pixmap
                    return pixmap
            except Exception as e:
                self.logger.warning(f"⚠️ فشل تحميل الصورة من Cache: {str(e)}")
        
        # تحميل الصورة في الخلفية
        self._download_image_async(url, local_path)
        
        # إرجاع placeholder
        return placeholder or QPixmap()
    
    def _download_image_async(self, url: str, local_path: Path):
        """
        تحميل الصورة بشكل غير متزامن
        
        Args:
            url: رابط الصورة
            local_path: مسار الحفظ المحلي
        """
        signals = ImageDownloadSignals()
        signals.image_loaded.connect(lambda u, p: self._on_image_loaded(u, p))
        
        runnable = ImageDownloadRunnable(url, self.cache_dir, signals)
        self.thread_pool.start(runnable)
    
    def _on_image_loaded(self, url: str, pixmap: QPixmap):
        """معالجة تحميل الصورة"""
        self._pixmap_cache[url] = pixmap
        self.logger.debug(f"✅ تم تحميل الصورة: {url}")
    
    def clear_cache(self, older_than_days: int = 30):
        """
        تنظيف Cache (حذف الصور القديمة)
        
        Args:
            older_than_days: حذف الصور الأقدم من هذا العدد من الأيام
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0
        
        for file_path in self.cache_dir.glob("*.jpg"):
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                self.logger.warning(f"⚠️ فشل حذف ملف: {file_path} - {str(e)}")
        
        self.logger.info(f"✅ تم تنظيف Cache: {deleted_count} ملف محذوف")
    
    def get_cache_size(self) -> int:
        """
        الحصول على حجم Cache بالبايت
        
        Returns:
            حجم Cache
        """
        total_size = 0
        for file_path in self.cache_dir.glob("*.jpg"):
            try:
                total_size += file_path.stat().st_size
            except Exception:
                pass
        return total_size
