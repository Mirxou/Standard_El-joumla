#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Updater
نظام التحديث التلقائي مع Changelog و App Version Lock
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from src.api.api_client import APIClient
from src.utils.logger import setup_logger


class AutoUpdater:
    """نظام التحديث التلقائي"""
    
    def __init__(self, api_client: APIClient, current_version: str = "5.3.0"):
        self.api_client = api_client
        self.current_version = current_version
        self.logger = setup_logger(__name__)
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        التحقق من وجود تحديثات
        
        Returns:
            معلومات التحديث أو None
        """
        try:
            response = self.api_client.get("/api/v1/version")
            if not response:
                return None
            
            latest_version = response.get('version')
            min_required = response.get('min_required_version')
            
            # App Version Lock - التحقق من الحد الأدنى المطلوب
            if min_required and self._compare_versions(self.current_version, min_required) < 0:
                return {
                    'update_available': True,
                    'critical': True,
                    'mandatory': True,
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'min_required_version': min_required,
                    'download_url': response.get('download_url'),
                    'release_notes': response.get('release_notes', ''),
                    'changelog': response.get('changelog', []),
                    'message': f'يجب تحديث التطبيق إلى الإصدار {min_required} على الأقل'
                }
            
            # التحقق من وجود تحديث جديد
            if latest_version and self._compare_versions(self.current_version, latest_version) < 0:
                return {
                    'update_available': True,
                    'critical': response.get('critical', False),
                    'mandatory': False,
                    'current_version': self.current_version,
                    'latest_version': latest_version,
                    'download_url': response.get('download_url'),
                    'release_notes': response.get('release_notes', ''),
                    'changelog': response.get('changelog', [])
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ فشل التحقق من التحديثات: {str(e)}")
            return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        مقارنة إصدارين
        
        Args:
            v1: الإصدار الأول
            v2: الإصدار الثاني
            
        Returns:
            -1 إذا كان v1 < v2, 0 إذا كان v1 == v2, 1 إذا كان v1 > v2
        """
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        try:
            v1_tuple = version_tuple(v1)
            v2_tuple = version_tuple(v2)
            
            if v1_tuple < v2_tuple:
                return -1
            elif v1_tuple > v2_tuple:
                return 1
            else:
                return 0
        except Exception:
            return 0
    
    def download_update(self, download_url: str, save_path: Path) -> bool:
        """
        تنزيل التحديث
        
        Args:
            download_url: رابط التحديث
            save_path: مسار الحفظ
            
        Returns:
            True إذا نجح التنزيل
        """
        try:
            self.logger.info(f"🔄 بدء تنزيل التحديث: {download_url}")
            
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # يمكن إرسال إشارة للتقدم هنا
            
            self.logger.info(f"✅ تم تنزيل التحديث: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل تنزيل التحديث: {str(e)}")
            return False
