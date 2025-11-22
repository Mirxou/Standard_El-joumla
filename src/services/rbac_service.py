"""
RBAC Service - Role-Based Access Control
نظام التحكم بالوصول القائم على الأدوار
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

class RBACService:
    """خدمة إدارة الصلاحيات والأدوار"""
    
    def __init__(self, db_manager, logger=None):
        self.db = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self._permission_cache = {}  # Cache for user permissions
        self._roles_cols = self._detect_roles_schema()

    def _detect_roles_schema(self) -> dict:
        """Detect roles table schema and return column name mapping.
        Maps to a canonical interface: role_id, role_name, display_name, description, is_active, is_system, created_at, updated_at
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("PRAGMA table_info(roles)")
            cols = {row[1] for row in cursor.fetchall()}
        except Exception:
            cols = set()

        mapping = {}
        # ID
        mapping['id'] = 'role_id' if 'role_id' in cols else ('id' if 'id' in cols else None)
        # Name
        mapping['name'] = 'role_name' if 'role_name' in cols else ('name' if 'name' in cols else None)
        # Display name
        if 'display_name' in cols:
            mapping['display'] = 'display_name'
        else:
            # Fallback to name
            mapping['display'] = mapping['name']
        # Description
        mapping['desc'] = 'description' if 'description' in cols else None
        # Active/System
        mapping['active'] = 'is_active' if 'is_active' in cols else None
        mapping['system'] = 'is_system' if 'is_system' in cols else None
        # Timestamps
        mapping['created'] = 'created_at' if 'created_at' in cols else None
        mapping['updated'] = 'updated_at' if 'updated_at' in cols else None
        return mapping
    
    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================
    
    def create_role(self, role_name: str, display_name: str, 
                   description: str = None, created_by: int = None) -> int:
        """إنشاء دور جديد"""
        try:
            cursor = self.db.conn.cursor()
            # Build dynamic insert based on available columns
            cols = []
            vals = []
            if self._roles_cols['name']:
                cols.append(self._roles_cols['name'])
                vals.append(role_name)
            if self._roles_cols['display']:
                cols.append(self._roles_cols['display'])
                vals.append(display_name)
            if self._roles_cols['desc']:
                cols.append(self._roles_cols['desc'])
                vals.append(description)
            placeholders = ', '.join(['?'] * len(vals))
            sql = f"INSERT INTO roles ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(vals))
            
            role_id = cursor.lastrowid
            self.db.conn.commit()
            
            self.logger.info(f"Created role: {role_name} (ID: {role_id})")
            return role_id
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error creating role: {e}")
            raise
    
    def get_role(self, role_id: int) -> Optional[Dict]:
        """الحصول على دور بالمعرف"""
        cursor = self.db.conn.cursor()
        id_col = self._roles_cols['id']
        name_col = self._roles_cols['name']
        disp_col = self._roles_cols['display']
        desc_col = self._roles_cols['desc'] or "''"
        act_col = self._roles_cols['active'] or '1'
        sys_col = self._roles_cols['system'] or '0'
        crt_col = self._roles_cols['created'] or 'CURRENT_TIMESTAMP'
        upd_col = self._roles_cols['updated'] or 'CURRENT_TIMESTAMP'
        cursor.execute(f'''
            SELECT {id_col}, {name_col}, {disp_col}, {desc_col},
                   {act_col}, {sys_col}, {crt_col}, {upd_col}
            FROM roles
            WHERE {id_col} = ?
        ''', (role_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'role_id': row[0],
                'role_name': row[1],
                'display_name': row[2],
                'description': row[3],
                'is_active': bool(row[4]) if isinstance(row[4], (int, bool)) else True,
                'is_system': bool(row[5]) if isinstance(row[5], (int, bool)) else False,
                'created_at': row[6],
                'updated_at': row[7]
            }
        return None
    
    def list_roles(self, include_inactive: bool = False) -> List[Dict]:
        """قائمة جميع الأدوار"""
        cursor = self.db.conn.cursor()
        id_col = self._roles_cols['id']
        name_col = self._roles_cols['name']
        disp_col = self._roles_cols['display']
        desc_col = self._roles_cols['desc'] or "''"
        act_col = self._roles_cols['active'] or '1'
        sys_col = self._roles_cols['system'] or '0'
        crt_col = self._roles_cols['created'] or 'CURRENT_TIMESTAMP'

        base = f"SELECT {id_col}, {name_col}, {disp_col}, {desc_col}, {act_col}, {sys_col}, {crt_col} FROM roles"
        if not include_inactive and self._roles_cols['active']:
            base += f" WHERE {act_col} = 1"
        base += f" ORDER BY {disp_col}"
        cursor.execute(base)
        roles = []
        
        for row in cursor.fetchall():
            roles.append({
                'role_id': row[0],
                'role_name': row[1],
                'display_name': row[2],
                'description': row[3],
                'is_active': bool(row[4]) if isinstance(row[4], (int, bool)) else True,
                'is_system': bool(row[5]) if isinstance(row[5], (int, bool)) else False,
                'created_at': row[6]
            })
        
        return roles
    
    def update_role(self, role_id: int, **kwargs) -> bool:
        """تحديث دور"""
        try:
            allowed_fields = ['display_name', 'description', 'is_active']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not updates:
                return False
            
            # Check if system role
            role = self.get_role(role_id)
            if role and role['is_system'] and 'is_active' in updates:
                raise ValueError("Cannot deactivate system role")
            
            # Map keys to actual columns
            col_map = {
                'display_name': self._roles_cols['display'],
                'description': self._roles_cols['desc'],
                'is_active': self._roles_cols['active']
            }
            set_parts = []
            values = []
            for k, v in updates.items():
                if col_map[k]:
                    set_parts.append(f"{col_map[k]} = ?")
                    values.append(v)
            if not set_parts:
                return False
            set_clause = ', '.join(set_parts)
            values = list(updates.values()) + [role_id]
            
            cursor = self.db.conn.cursor()
            id_col = self._roles_cols['id']
            cursor.execute(f'''UPDATE roles SET {set_clause} WHERE {id_col} = ?''', values)
            
            self.db.conn.commit()
            self.logger.info(f"Updated role {role_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error updating role: {e}")
            raise
    
    def delete_role(self, role_id: int) -> bool:
        """حذف دور (غير نظامي فقط)"""
        try:
            role = self.get_role(role_id)
            if not role:
                return False
            
            if role['is_system']:
                raise ValueError("Cannot delete system role")
            
            cursor = self.db.conn.cursor()
            id_col = self._roles_cols['id']
            cursor.execute(f'DELETE FROM roles WHERE {id_col} = ?', (role_id,))
            self.db.conn.commit()
            
            self.logger.info(f"Deleted role {role_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error deleting role: {e}")
            raise
    
    # ========================================================================
    # PERMISSION MANAGEMENT
    # ========================================================================
    
    def create_permission(self, permission_name: str, module: str,
                         action: str, description: str = None) -> int:
        """إنشاء صلاحية جديدة"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO permissions (permission_name, module, action, description)
                VALUES (?, ?, ?, ?)
            ''', (permission_name, module, action, description))
            
            permission_id = cursor.lastrowid
            self.db.conn.commit()
            
            self.logger.info(f"Created permission: {permission_name}")
            return permission_id
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error creating permission: {e}")
            raise
    
    def list_permissions(self, module: str = None) -> List[Dict]:
        """قائمة الصلاحيات"""
        cursor = self.db.conn.cursor()
        
        if module:
            cursor.execute('''
                SELECT permission_id, permission_name, module, action, description
                FROM permissions
                WHERE module = ?
                ORDER BY module, action
            ''', (module,))
        else:
            cursor.execute('''
                SELECT permission_id, permission_name, module, action, description
                FROM permissions
                ORDER BY module, action
            ''')
        
        permissions = []
        for row in cursor.fetchall():
            permissions.append({
                'permission_id': row[0],
                'permission_name': row[1],
                'module': row[2],
                'action': row[3],
                'description': row[4]
            })
        
        return permissions
    
    def get_role_permissions(self, role_id: int) -> List[Dict]:
        """الحصول على صلاحيات دور"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT p.permission_id, p.permission_name, p.module, p.action, p.description
            FROM permissions p
            INNER JOIN role_permissions rp ON p.permission_id = rp.permission_id
            WHERE rp.role_id = ?
            ORDER BY p.module, p.action
        ''', (role_id,))
        
        permissions = []
        for row in cursor.fetchall():
            permissions.append({
                'permission_id': row[0],
                'permission_name': row[1],
                'module': row[2],
                'action': row[3],
                'description': row[4]
            })
        
        return permissions
    
    def assign_permission_to_role(self, role_id: int, permission_id: int,
                                  granted_by: int = None) -> bool:
        """إسناد صلاحية لدور"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_by)
                VALUES (?, ?, ?)
            ''', (role_id, permission_id, granted_by))
            
            self.db.conn.commit()
            self.logger.info(f"Assigned permission {permission_id} to role {role_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error assigning permission: {e}")
            raise
    
    def revoke_permission_from_role(self, role_id: int, permission_id: int) -> bool:
        """إلغاء صلاحية من دور"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                DELETE FROM role_permissions
                WHERE role_id = ? AND permission_id = ?
            ''', (role_id, permission_id))
            
            self.db.conn.commit()
            self._clear_permission_cache()
            self.logger.info(f"Revoked permission {permission_id} from role {role_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error revoking permission: {e}")
            raise
    
    # ========================================================================
    # USER-ROLE MANAGEMENT
    # ========================================================================
    
    def assign_role_to_user(self, user_id: int, role_id: int,
                           assigned_by: int = None, 
                           expires_at: datetime = None) -> bool:
        """إسناد دور لمستخدم"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_roles 
                (user_id, role_id, assigned_by, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, role_id, assigned_by, expires_at))
            
            self.db.conn.commit()
            self._clear_permission_cache(user_id)
            self.logger.info(f"Assigned role {role_id} to user {user_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error assigning role: {e}")
            raise
    
    def revoke_role_from_user(self, user_id: int, role_id: int) -> bool:
        """إلغاء دور من مستخدم"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                DELETE FROM user_roles
                WHERE user_id = ? AND role_id = ?
            ''', (user_id, role_id))
            
            self.db.conn.commit()
            self._clear_permission_cache(user_id)
            self.logger.info(f"Revoked role {role_id} from user {user_id}")
            return True
            
        except Exception as e:
            self.db.conn.rollback()
            self.logger.error(f"Error revoking role: {e}")
            raise
    
    def get_user_roles(self, user_id: int) -> List[Dict]:
        """الحصول على أدوار المستخدم"""
        cursor = self.db.conn.cursor()
        rid = self._roles_cols['id']
        rname = self._roles_cols['name']
        rdisp = self._roles_cols['display']
        rdesc = self._roles_cols['desc'] or "''"
        ractive = self._roles_cols['active'] or '1'
        cursor.execute(f'''
            SELECT r.{rid}, r.{rname}, r.{rdisp}, {rdesc},
                   ur.assigned_at, ur.expires_at
            FROM roles r
            INNER JOIN user_roles ur ON r.{rid} = ur.role_id
            WHERE ur.user_id = ?
            AND {ractive} = 1
            AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        ''', (user_id,))
        
        roles = []
        for row in cursor.fetchall():
            roles.append({
                'role_id': row[0],
                'role_name': row[1],
                'display_name': row[2],
                'description': row[3],
                'assigned_at': row[4],
                'expires_at': row[5]
            })
        
        return roles
    
    # ========================================================================
    # PERMISSION CHECKING
    # ========================================================================
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """الحصول على جميع صلاحيات المستخدم"""
        # Check cache first
        if user_id in self._permission_cache:
            cached_time, permissions = self._permission_cache[user_id]
            if (datetime.now() - cached_time).seconds < 300:  # 5 minutes
                return permissions
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT p.permission_name
            FROM v_user_permissions
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        permissions = [row[0] for row in cursor.fetchall()]
        
        # Cache the result
        self._permission_cache[user_id] = (datetime.now(), permissions)
        
        return permissions
    
    def has_permission(self, user_id: int, permission_name: str) -> bool:
        """التحقق من صلاحية محددة"""
        permissions = self.get_user_permissions(user_id)
        return permission_name in permissions
    
    def has_any_permission(self, user_id: int, permission_names: List[str]) -> bool:
        """التحقق من أي صلاحية من القائمة"""
        permissions = self.get_user_permissions(user_id)
        return any(perm in permissions for perm in permission_names)
    
    def has_all_permissions(self, user_id: int, permission_names: List[str]) -> bool:
        """التحقق من جميع الصلاحيات"""
        permissions = self.get_user_permissions(user_id)
        return all(perm in permissions for perm in permission_names)
    
    def can(self, user_id: int, module: str, action: str) -> bool:
        """التحقق من صلاحية بالوحدة والإجراء"""
        permission_name = f"{module}.{action}"
        return self.has_permission(user_id, permission_name)
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _clear_permission_cache(self, user_id: int = None):
        """مسح ذاكرة التخزين المؤقت للصلاحيات"""
        if user_id:
            self._permission_cache.pop(user_id, None)
        else:
            self._permission_cache.clear()
    
    def get_permission_matrix(self, role_id: int = None) -> Dict:
        """الحصول على مصفوفة الصلاحيات"""
        cursor = self.db.conn.cursor()
        
        if role_id:
            cursor.execute('''
                SELECT p.module, p.action, 
                       CASE WHEN rp.permission_id IS NOT NULL THEN 1 ELSE 0 END AS has_permission
                FROM permissions p
                LEFT JOIN role_permissions rp 
                    ON p.permission_id = rp.permission_id AND rp.role_id = ?
                ORDER BY p.module, p.action
            ''', (role_id,))
        else:
            cursor.execute('''
                SELECT module, action, 1 AS has_permission
                FROM permissions
                ORDER BY module, action
            ''')
        
        matrix = {}
        for row in cursor.fetchall():
            module, action, has_perm = row
            if module not in matrix:
                matrix[module] = {}
            matrix[module][action] = bool(has_perm)
        
        return matrix
    
    def get_statistics(self) -> Dict:
        """إحصائيات النظام"""
        cursor = self.db.conn.cursor()
        
        stats = {}
        
        # Total roles
        cursor.execute('SELECT COUNT(*) FROM roles WHERE is_active = 1')
        stats['total_roles'] = cursor.fetchone()[0]
        
        # Total permissions
        cursor.execute('SELECT COUNT(*) FROM permissions')
        stats['total_permissions'] = cursor.fetchone()[0]
        
        # Users with roles
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_roles')
        stats['users_with_roles'] = cursor.fetchone()[0]
        
        # Most assigned role
        cursor.execute('''
            SELECT r.display_name, COUNT(*) AS count
            FROM user_roles ur
            INNER JOIN roles r ON ur.role_id = r.role_id
            GROUP BY ur.role_id
            ORDER BY count DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        stats['most_assigned_role'] = {
            'name': row[0] if row else None,
            'count': row[1] if row else 0
        }
        
        return stats
