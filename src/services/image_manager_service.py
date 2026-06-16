import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة إدارة صور المنتجات - Product Image Manager Service
تقوم بإدارة صور المنتجات: نسخ، إعادة تسمية، حذف، وإنشاء thumbnails
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from ..utils.logger import setup_logger


class ImageManagerService:
    """خدمة إدارة صور المنتجات"""

    # الصيغ المدعومة
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

    # أحجام الصور
    THUMBNAIL_SIZE = (200, 200)  # حجم الصورة المصغرة
    PREVIEW_SIZE = (400, 400)  # حجم الصورة للمعاينة
    MAX_SIZE = (1200, 1200)  # الحد الأقصى لحجم الصورة

    def __init__(self, base_dir: Optional[str] = None, logger=None):
        """
        تهيئة خدمة إدارة الصور

        Args:
            base_dir: المجلد الأساسي للصور (افتراضي: assets/images)
            logger: كائن السجل
        """
        self.logger = logger or setup_logger(__name__)

        # تحديد المجلد الأساسي
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # البحث عن assets/images من جذر المشروع
            project_root = Path(__file__).parent.parent.parent
            self.base_dir = project_root / "assets" / "images"

        # إنشاء المجلدات المطلوبة
        self.products_dir = self.base_dir / "products"
        self.thumbnails_dir = self.base_dir / "thumbnails"
        self.previews_dir = self.base_dir / "previews"

        # إنشاء المجلدات إذا لم تكن موجودة
        self.products_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"تم تهيئة ImageManagerService - المجلد الأساسي: {self.base_dir}")

    def save_product_image(
        self,
        source_path: str,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
        create_thumbnails: bool = True,
    ) -> Optional[str]:
        """
        حفظ صورة منتج

        Args:
            source_path: مسار الصورة الأصلية
            product_id: معرف المنتج (اختياري)
            product_name: اسم المنتج (اختياري)
            create_thumbnails: إنشاء صور مصغرة (افتراضي: True)

        Returns:
            مسار الصورة المحفوظة أو None في حالة الفشل
        """
        try:
            source = Path(source_path)

            # التحقق من وجود الملف
            if not source.exists():
                self.logger.error(f"الملف غير موجود: {source_path}")
                return None

            # التحقق من صيغة الملف
            if source.suffix.lower() not in self.SUPPORTED_FORMATS:
                self.logger.error(f"صيغة غير مدعومة: {source.suffix}")
                return None

            # إنشاء اسم ملف جديد
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if product_id:
                filename = f"product_{product_id}_{timestamp}{source.suffix}"
            elif product_name:
                # تنظيف اسم المنتج لاستخدامه في اسم الملف
                safe_name = "".join(c for c in product_name if c.isalnum() or c in (" ", "-", "_")).strip()
                safe_name = safe_name.replace(" ", "_")[:30]  # حد أقصى 30 حرف
                filename = f"{safe_name}_{timestamp}{source.suffix}"
            else:
                filename = f"product_{timestamp}{source.suffix}"

            # مسار الوجهة
            dest_path = self.products_dir / filename

            # نسخ الملف
            shutil.copy2(source, dest_path)
            self.logger.info(f"تم نسخ الصورة من {source_path} إلى {dest_path}")

            # معالجة الصورة وإنشاء النسخ المختلفة
            if create_thumbnails:
                self._process_image(dest_path, product_id)

            # إرجاع المسار النسبي
            return str(dest_path.relative_to(self.base_dir.parent))

        except Exception as e:
            self.logger.error(f"خطأ في حفظ صورة المنتج: {str(e)}", exc_info=True)
            return None

    def _process_image(self, image_path: Path, product_id: Optional[int] = None):
        """
        معالجة الصورة وإنشاء النسخ المختلفة

        Args:
            image_path: مسار الصورة
            product_id: معرف المنتج (اختياري)
        """
        if not PIL_AVAILABLE:
            self.logger.warning("Pillow غير متاح، سيتم نسخ الصورة بدون معالجة")
            return

        try:
            # فتح الصورة
            with Image.open(image_path) as img:
                # تحويل إلى RGB إذا كانت الصورة شفافة
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # إنشاء اسم الملف الأساسي
                base_name = image_path.stem

                # إنشاء الصورة المصغرة (Thumbnail)
                thumbnail = img.copy()
                thumbnail.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                thumbnail_path = self.thumbnails_dir / f"{base_name}_thumb.jpg"
                thumbnail.save(thumbnail_path, "JPEG", quality=85, optimize=True)

                # إنشاء صورة المعاينة (Preview)
                preview = img.copy()
                preview.thumbnail(self.PREVIEW_SIZE, Image.Resampling.LANCZOS)
                preview_path = self.previews_dir / f"{base_name}_preview.jpg"
                preview.save(preview_path, "JPEG", quality=90, optimize=True)

                # تقليل حجم الصورة الأصلية إذا كانت كبيرة جداً
                if img.size[0] > self.MAX_SIZE[0] or img.size[1] > self.MAX_SIZE[1]:
                    img.thumbnail(self.MAX_SIZE, Image.Resampling.LANCZOS)
                    img.save(image_path, quality=95, optimize=True)
                    self.logger.info(f"تم تقليل حجم الصورة الأصلية: {image_path}")

                self.logger.debug(f"تم معالجة الصورة: {image_path}")

        except Exception as e:
            self.logger.error(f"خطأ في معالجة الصورة {image_path}: {str(e)}", exc_info=True)

    def get_image_path(self, relative_path: str, size: str = "original") -> Optional[Path]:
        """
        الحصول على مسار الصورة بالحجم المطلوب

        Args:
            relative_path: المسار النسبي للصورة
            size: حجم الصورة ('original', 'preview', 'thumbnail')

        Returns:
            مسار الصورة أو None
        """
        try:
            if size == "original":
                path = self.base_dir.parent / relative_path
            elif size == "preview":
                base_name = Path(relative_path).stem
                path = self.previews_dir / f"{base_name}_preview.jpg"
            elif size == "thumbnail":
                base_name = Path(relative_path).stem
                path = self.thumbnails_dir / f"{base_name}_thumb.jpg"
            else:
                self.logger.warning(f"حجم غير مدعوم: {size}")
                path = self.base_dir.parent / relative_path

            if path.exists():
                return path
            else:
                # إذا لم تكن الصورة المصغرة موجودة، استخدم الأصلية
                if size != "original":
                    original_path = self.base_dir.parent / relative_path
                    if original_path.exists():
                        return original_path
                return None

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على مسار الصورة: {str(e)}")
            return None

    def delete_product_image(self, image_path: str) -> bool:
        """
        حذف صورة منتج

        Args:
            image_path: مسار الصورة (نسبي أو مطلق)

        Returns:
            True إذا تم الحذف بنجاح، False خلاف ذلك
        """
        try:
            # تحديد المسار الكامل
            if Path(image_path).is_absolute():
                full_path = Path(image_path)
            else:
                full_path = self.base_dir.parent / image_path

            # التحقق من أن الصورة في مجلد المنتجات
            if not str(full_path).startswith(str(self.products_dir)):
                self.logger.warning(f"محاولة حذف صورة خارج مجلد المنتجات: {image_path}")
                return False

            # حذف الصورة الأصلية
            if full_path.exists():
                full_path.unlink()
                self.logger.info(f"تم حذف الصورة الأصلية: {full_path}")

            # حذف الصور المصغرة والمعاينة
            base_name = full_path.stem
            thumbnail_path = self.thumbnails_dir / f"{base_name}_thumb.jpg"
            preview_path = self.previews_dir / f"{base_name}_preview.jpg"

            if thumbnail_path.exists():
                thumbnail_path.unlink()
                self.logger.debug(f"تم حذف الصورة المصغرة: {thumbnail_path}")

            if preview_path.exists():
                preview_path.unlink()
                self.logger.debug(f"تم حذف صورة المعاينة: {preview_path}")

            return True

        except Exception as e:
            self.logger.error(f"خطأ في حذف صورة المنتج: {str(e)}", exc_info=True)
            return False

    def update_product_image(
        self,
        old_image_path: Optional[str],
        new_source_path: str,
        product_id: Optional[int] = None,
        product_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        تحديث صورة منتج (حذف القديمة وحفظ الجديدة)

        Args:
            old_image_path: مسار الصورة القديمة
            new_source_path: مسار الصورة الجديدة
            product_id: معرف المنتج
            product_name: اسم المنتج

        Returns:
            مسار الصورة الجديدة أو None
        """
        try:
            # حذف الصورة القديمة إذا كانت موجودة
            if old_image_path:
                self.delete_product_image(old_image_path)

            # حفظ الصورة الجديدة
            return self.save_product_image(
                new_source_path,
                product_id=product_id,
                product_name=product_name,
                create_thumbnails=True,
            )

        except Exception as e:
            self.logger.error(f"خطأ في تحديث صورة المنتج: {str(e)}", exc_info=True)
            return None

    def cleanup_orphaned_images(self) -> int:
        """
        تنظيف الصور اليتيمة (التي لا ترتبط بأي منتج)

        Returns:
            عدد الصور المحذوفة
        """
        try:
            # TODO: تنفيذ منطق البحث عن الصور اليتيمة
            # يحتاج إلى الوصول إلى قاعدة البيانات للتحقق من المنتجات
            self.logger.info("تم استدعاء تنظيف الصور اليتيمة (غير مطبق بعد)")
            return 0

        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الصور اليتيمة: {str(e)}")
            return 0

    def get_image_info(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        الحصول على معلومات الصورة

        Args:
            image_path: مسار الصورة

        Returns:
            معلومات الصورة أو None
        """
        if not PIL_AVAILABLE:
            return None

        try:
            full_path = self.get_image_path(image_path, "original")
            if not full_path or not full_path.exists():
                return None

            with Image.open(full_path) as img:
                return {
                    "path": str(full_path),
                    "size": img.size,
                    "format": img.format,
                    "mode": img.mode,
                    "file_size": full_path.stat().st_size,
                }

        except Exception as e:
            self.logger.error(f"خطأ في الحصول على معلومات الصورة: {str(e)}")
            return None
