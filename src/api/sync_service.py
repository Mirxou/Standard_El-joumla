#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Service
خدمة المزامنة ثنائية الاتجاه مع Ultimate Sync Flow
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.core.local_database_manager import LocalDatabaseManager
from src.api.api_client import APIClient
from src.api.delta_sync import DeltaSyncService
from src.api.circuit_breaker import CircuitBreaker
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.customer_repository import CustomerRepository
from src.utils.logger import setup_logger


class SyncService:
    """خدمة المزامنة ثنائية الاتجاه"""
    
    def __init__(
        self,
        local_db: LocalDatabaseManager,
        api_client: APIClient,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.local_db = local_db
        self.api_client = api_client
        self.delta_sync = DeltaSyncService(local_db)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.logger = setup_logger(__name__)
        
        # Repositories
        self.product_repo = ProductRepository(local_db)
        self.sale_repo = SaleRepository(local_db)
        self.customer_repo = CustomerRepository(local_db)
    
    def sync_ultimate_flow(self) -> Dict[str, Any]:
        """
        Ultimate Sync Flow:
        Local Commit → Handshake → Pull → Conflict Check → Push → Ack
        
        Returns:
            نتيجة المزامنة
        """
        result = {
            'success': False,
            'pulled_count': 0,
            'pushed_count': 0,
            'conflicts': [],
            'errors': []
        }
        
        try:
            # 1. Handshake - الحصول على آخر timestamp
            last_synced = self.local_db.get_last_synced_at()
            if last_synced is None:
                last_synced = datetime.fromtimestamp(0)
            
            handshake_result = self._handshake(last_synced)
            if not handshake_result['success']:
                result['errors'].append("فشل Handshake")
                return result
            
            # 2. Pull - سحب التعديلات من السيرفر
            pull_result = self._pull_delta(last_synced)
            result['pulled_count'] = pull_result['count']
            result['conflicts'].extend(pull_result['conflicts'])
            
            # 3. Push - رفع التعديلات المحلية
            push_result = self._push_pending()
            result['pushed_count'] = push_result['count']
            result['errors'].extend(push_result['errors'])
            
            # 4. Ack - تحديث last_synced_at مع Server Time
            server_time = self.api_client.get_server_time()
            if server_time:
                self.local_db.set_last_synced_at(server_time)
            else:
                # Fallback إلى Client Time
                self.local_db.set_last_synced_at(datetime.now())
            
            result['success'] = True
            self.logger.info(f"✅ تمت المزامنة: {result['pulled_count']} سجل مسحوب، {result['pushed_count']} سجل مرسل")
            
        except Exception as e:
            self.logger.error(f"❌ فشل المزامنة: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    def _handshake(self, last_synced: datetime) -> Dict[str, Any]:
        """
        Handshake - التحقق من حالة المزامنة
        
        Args:
            last_synced: آخر وقت مزامنة
            
        Returns:
            نتيجة Handshake
        """
        try:
            response = self.circuit_breaker.call(
                lambda: self.api_client.get(
                    "/api/v1/sync/handshake",
                    params={"last_synced": last_synced.isoformat()}
                )
            )
            
            if response:
                return {'success': True, 'data': response}
            else:
                return {'success': False, 'error': 'فشل Handshake'}
                
        except Exception as e:
            self.logger.error(f"❌ فشل Handshake: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _pull_delta(self, since: datetime) -> Dict[str, Any]:
        """
        Pull - سحب التعديلات من السيرفر
        
        Args:
            since: التاريخ للبدء منه
            
        Returns:
            نتيجة Pull
        """
        result = {
            'count': 0,
            'conflicts': []
        }
        
        try:
            # الحصول على التعديلات من السيرفر
            response = self.circuit_breaker.call(
                lambda: self.api_client.get(
                    "/api/v1/sync/delta",
                    params={"last_synced": since.isoformat()}
                )
            )
            
            if not response or 'items' not in response:
                return result
            
            # معالجة كل عنصر
            for item in response['items']:
                table_name = item.get('table_name')
                record_data = item.get('data', {})
                
                if not table_name or not record_data:
                    continue
                
                # Conflict Check
                conflict = self._check_conflict(table_name, record_data)
                if conflict:
                    result['conflicts'].append(conflict)
                    continue
                
                # تطبيق التعديل
                if self._apply_remote_change(table_name, record_data):
                    result['count'] += 1
                    
        except Exception as e:
            self.logger.error(f"❌ فشل Pull: {str(e)}")
        
        return result
    
    def _push_pending(self) -> Dict[str, Any]:
        """
        Push - رفع التعديلات المحلية المعلقة
        
        Returns:
            نتيجة Push
        """
        result = {
            'count': 0,
            'errors': []
        }
        
        try:
            # الحصول على العناصر المعلقة
            pending_items = self.local_db.get_pending_items(include_deleted=True)
            
            if not pending_items:
                return result
            
            # تجميع حسب الجدول
            items_by_table = {}
            for item in pending_items:
                table_name = item.get('source_table') or item.get('table_name')
                if not table_name:
                    continue
                
                if table_name not in items_by_table:
                    items_by_table[table_name] = []
                
                # إزالة source_table من البيانات
                item_data = {k: v for k, v in item.items() if k != 'source_table'}
                items_by_table[table_name].append(item_data)
            
            # إرسال كل جدول
            for table_name, items in items_by_table.items():
                try:
                    response = self.circuit_breaker.call(
                        lambda: self.api_client.post(
                            f"/api/v1/sync/push",
                            data={
                                'table_name': table_name,
                                'items': items
                            }
                        )
                    )
                    
                    if response and 'acknowledged_ids' in response:
                        # تعليم السجلات كمتزامنة
                        for ack_id in response['acknowledged_ids']:
                            self.local_db.mark_as_synced(table_name, ack_id)
                            result['count'] += 1
                            
                except Exception as e:
                    result['errors'].append(f"فشل Push لـ {table_name}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"❌ فشل Push: {str(e)}")
            result['errors'].append(str(e))
        
        return result
    
    def _check_conflict(self, table_name: str, remote_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        التحقق من وجود تعارض
        
        Args:
            table_name: اسم الجدول
            remote_data: البيانات من السيرفر
            
        Returns:
            معلومات التعارض أو None
        """
        record_id = remote_data.get('id')
        if not record_id:
            return None
        
        # الحصول على السجل المحلي
        if table_name == 'products':
            local_record = self.product_repo.find_by_id(record_id, include_deleted=True)
        elif table_name == 'sales':
            local_record = self.sale_repo.find_by_id(record_id, include_deleted=True)
        elif table_name == 'customers':
            local_record = self.customer_repo.find_by_id(record_id, include_deleted=True)
        else:
            local_record = None
        
        # إذا لم يكن هناك سجل محلي، لا يوجد تعارض
        if not local_record:
            return None
        
        # التحقق من التعارض (مثلاً: إذا كان السجل المحلي محدث بعد السجل البعيد)
        local_updated = local_record.get('updated_at')
        remote_updated = remote_data.get('updated_at')
        
        if local_updated and remote_updated:
            try:
                local_dt = datetime.fromisoformat(local_updated) if isinstance(local_updated, str) else local_updated
                remote_dt = datetime.fromisoformat(remote_updated) if isinstance(remote_updated, str) else remote_updated
                
                # إذا كان السجل المحلي محدث بعد السجل البعيد، يوجد تعارض
                if local_dt > remote_dt and local_record.get('is_synced') == 0:
                    return {
                        'table_name': table_name,
                        'record_id': record_id,
                        'local_data': local_record,
                        'remote_data': remote_data,
                        'reason': 'local_newer'
                    }
            except Exception:
                pass
        
        return None
    
    def _apply_remote_change(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        تطبيق تغيير من السيرفر
        
        Args:
            table_name: اسم الجدول
            data: البيانات
            
        Returns:
            True إذا نجح التطبيق
        """
        try:
            raw_record_id = data.get('id')
            if raw_record_id is None:
                return False
            try:
                record_id: int = int(raw_record_id)
            except (TypeError, ValueError):
                return False
            
            if table_name == 'products':
                repo = self.product_repo
            elif table_name == 'sales':
                repo = self.sale_repo
            elif table_name == 'customers':
                repo = self.customer_repo
            else:
                return False
            
            # التحقق من وجود السجل
            existing = repo.find_by_id(record_id, include_deleted=True)
            
            if existing:
                # تحديث
                # إزالة id من البيانات
                update_data = {k: v for k, v in data.items() if k != 'id'}
                return repo.update(record_id, update_data)
            else:
                # إنشاء جديد
                return repo.create(data) is not None
                
        except Exception as e:
            self.logger.error(f"❌ فشل تطبيق التغيير: {str(e)}")
            return False
    
    def sync_now(self) -> Dict[str, Any]:
        """
        مزامنة فورية (يدوية)
        
        Returns:
            نتيجة المزامنة
        """
        return self.sync_ultimate_flow()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        الحصول على حالة المزامنة
        
        Returns:
            حالة المزامنة
        """
        summary = self.delta_sync.get_sync_summary()
        circuit_state = self.circuit_breaker.get_state()
        
        return {
            **summary,
            'circuit_breaker': circuit_state,
            'is_online': self.api_client.is_online()
        }
