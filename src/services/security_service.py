#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الأمان والصلاحيات (Security Service)
توفر إدارة الأدوار، التحقق من الأذونات، وسجل التدقيق البسيط
"""
from typing import List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

class SecurityService:
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger

    def create_role(self, name: str, permissions: List[str]) -> Optional[int]:
        try:
            now = datetime.now()
            q = 'INSERT INTO roles (name, permissions, created_at, updated_at) VALUES (?, ?, ?, ?)'
            res = self.db.execute_query(q, (name, ','.join(permissions), now, now))
            if res and hasattr(res, 'lastrowid'):
                return res.lastrowid
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في إنشاء الدور: {e}')
        return None

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        try:
            q = 'INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)'
            self.db.execute_query(q, (user_id, role_id, datetime.now()))
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في تعيين الدور للمستخدم: {e}')
            return False

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        try:
            q = ('SELECT r.permissions FROM roles r '
                 'JOIN user_roles ur ON ur.role_id = r.id '
                 'WHERE ur.user_id = ?')
            rows = self.db.fetch_all(q, (user_id,))
            perms = set()
            for r in rows:
                if r[0]:
                    perms.update([p.strip() for p in r[0].split(',') if p.strip()])
            return permission in perms
        except Exception as e:
            if self.logger:
                self.logger.error(f'خطأ في فحص صلاحية المستخدم {user_id}: {e}')
            return False

    def audit_log(self, actor: str, action: str, details: str = '') -> None:
        try:
            q = 'INSERT INTO audit_logs (actor, action, details, created_at) VALUES (?, ?, ?, ?)'
            self.db.execute_query(q, (actor, action, details, datetime.now()))
        except Exception as e:
            if self.logger:
                self.logger.error(f'فشل تسجيل السجل التدقيقي: {e}')
