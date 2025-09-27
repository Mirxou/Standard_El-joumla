#!/usr/bin/env python3
"""
خدمة المستخدمين - User Service
تدير المستخدمين والمصادقة والصلاحيات
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.database_manager import DatabaseManager
from ..utils.logger import setup_logger, DatabaseLogger
from ..models.user import User, UserManager, UserRole, Permission


class SessionStatus(Enum):
    """حالات الجلسة"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class UserSession:
    """جلسة المستخدم"""
    session_id: str
    user_id: int
    username: str
    role: UserRole
    login_time: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE


@dataclass
class LoginAttempt:
    """محاولة تسجيل الدخول"""
    username: str
    ip_address: Optional[str]
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None


@dataclass
class SecuritySettings:
    """إعدادات الأمان"""
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 480  # 8 ساعات
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = False
    password_expiry_days: int = 90
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_expiry_hours: int = 24


class UserService:
    """خدمة المستخدمين"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = setup_logger(__name__)
        self.db_logger = DatabaseLogger(db_manager)
        self.user_manager = UserManager(db_manager)
        
        # الجلسات النشطة
        self.active_sessions: Dict[str, UserSession] = {}
        
        # إعدادات الأمان
        self.security_settings = SecuritySettings()
        
        # تحميل إعدادات الأمان من قاعدة البيانات
        self._load_security_settings()
        
        # إنشاء جداول إضافية للأمان
        self._create_security_tables()
    
    def _create_security_tables(self):
        """إنشاء جداول الأمان الإضافية"""
        try:
            # جدول محاولات تسجيل الدخول
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    failure_reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول الجلسات النشطة
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # جدول إعدادات الأمان
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS security_settings (
                    id INTEGER PRIMARY KEY,
                    setting_name TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # فهارس للأداء
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_login_attempts_timestamp ON login_attempts(timestamp)")
            self.db.execute_query("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
            
            self.logger.info("تم إنشاء جداول الأمان بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء جداول الأمان: {e}")
            raise
    
    def _load_security_settings(self):
        """تحميل إعدادات الأمان من قاعدة البيانات"""
        try:
            settings = self.db.execute_query("SELECT setting_name, setting_value FROM security_settings")
            
            for setting in settings:
                name = setting['setting_name']
                value = setting['setting_value']
                
                if hasattr(self.security_settings, name):
                    # تحويل القيمة إلى النوع المناسب
                    current_value = getattr(self.security_settings, name)
                    if isinstance(current_value, int):
                        setattr(self.security_settings, name, int(value))
                    elif isinstance(current_value, bool):
                        setattr(self.security_settings, name, value.lower() == 'true')
                    else:
                        setattr(self.security_settings, name, value)
                        
        except Exception as e:
            self.logger.warning(f"تعذر تحميل إعدادات الأمان: {e}")
    
    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[bool, Optional[UserSession], Optional[str]]:
        """مصادقة المستخدم وإنشاء جلسة"""
        try:
            # التحقق من محاولات تسجيل الدخول المتكررة
            if self._is_user_locked(username):
                self._log_login_attempt(username, ip_address, False, "المستخدم مقفل بسبب محاولات فاشلة متكررة")
                return False, None, "المستخدم مقفل مؤقتاً بسبب محاولات تسجيل دخول فاشلة متكررة"
            
            # التحقق من بيانات المستخدم
            user = self.user_manager.authenticate_user(username, password)
            
            if not user:
                self._log_login_attempt(username, ip_address, False, "اسم المستخدم أو كلمة المرور غير صحيحة")
                return False, None, "اسم المستخدم أو كلمة المرور غير صحيحة"
            
            # التحقق من حالة المستخدم
            if not user.is_active:
                self._log_login_attempt(username, ip_address, False, "المستخدم غير نشط")
                return False, None, "المستخدم غير نشط"
            
            if user.is_locked:
                self._log_login_attempt(username, ip_address, False, "المستخدم مقفل")
                return False, None, "المستخدم مقفل"
            
            # التحقق من انتهاء صلاحية كلمة المرور
            if self._is_password_expired(user):
                self._log_login_attempt(username, ip_address, False, "كلمة المرور منتهية الصلاحية")
                return False, None, "كلمة المرور منتهية الصلاحية، يرجى تغييرها"
            
            # إنشاء جلسة جديدة
            session = self._create_session(user, ip_address, user_agent)
            
            # تسجيل محاولة تسجيل دخول ناجحة
            self._log_login_attempt(username, ip_address, True)
            
            # تحديث آخر تسجيل دخول للمستخدم
            self.user_manager._update_last_login(user.id, datetime.now())
            
            # تسجيل في سجل قاعدة البيانات
            self.db_logger.log_login(user.id, ip_address, True)
            
            return True, session, None
            
        except Exception as e:
            self.logger.error(f"خطأ في مصادقة المستخدم: {e}")
            self._log_login_attempt(username, ip_address, False, f"خطأ في النظام: {str(e)}")
            return False, None, "حدث خطأ في النظام"
    
    def _create_session(self, user: User, ip_address: Optional[str], user_agent: Optional[str]) -> UserSession:
        """إنشاء جلسة جديدة للمستخدم"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()
        
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            username=user.username,
            role=user.role,
            login_time=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # حفظ الجلسة في الذاكرة
        self.active_sessions[session_id] = session
        
        # حفظ الجلسة في قاعدة البيانات
        self.db.execute_query("""
            INSERT INTO user_sessions (session_id, user_id, login_time, last_activity, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user.id, now, now, ip_address, user_agent))
        
        return session
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[UserSession]]:
        """التحقق من صحة الجلسة"""
        try:
            session = self.active_sessions.get(session_id)
            
            if not session:
                # محاولة تحميل الجلسة من قاعدة البيانات
                session = self._load_session_from_db(session_id)
                if not session:
                    return False, None
            
            # التحقق من انتهاء صلاحية الجلسة
            if self._is_session_expired(session):
                self._terminate_session(session_id, "انتهت صلاحية الجلسة")
                return False, None
            
            # تحديث آخر نشاط
            session.last_activity = datetime.now()
            self.active_sessions[session_id] = session
            
            # تحديث في قاعدة البيانات
            self.db.execute_query("""
                UPDATE user_sessions 
                SET last_activity = ? 
                WHERE session_id = ?
            """, (session.last_activity, session_id))
            
            return True, session
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من الجلسة: {e}")
            return False, None
    
    def _load_session_from_db(self, session_id: str) -> Optional[UserSession]:
        """تحميل الجلسة من قاعدة البيانات"""
        try:
            result = self.db.execute_query("""
                SELECT s.*, u.username, u.role 
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_id = ? AND s.status = 'active'
            """, (session_id,))
            
            if not result:
                return None
            
            row = result[0]
            
            return UserSession(
                session_id=row['session_id'],
                user_id=row['user_id'],
                username=row['username'],
                role=UserRole(row['role']),
                login_time=datetime.fromisoformat(row['login_time']),
                last_activity=datetime.fromisoformat(row['last_activity']),
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                status=SessionStatus(row['status'])
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل الجلسة من قاعدة البيانات: {e}")
            return None
    
    def logout_user(self, session_id: str) -> bool:
        """تسجيل خروج المستخدم"""
        try:
            session = self.active_sessions.get(session_id)
            if session:
                self.db_logger.log_logout(session.user_id)
            
            return self._terminate_session(session_id, "تسجيل خروج")
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الخروج: {e}")
            return False
    
    def _terminate_session(self, session_id: str, reason: str) -> bool:
        """إنهاء الجلسة"""
        try:
            # إزالة من الذاكرة
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # تحديث في قاعدة البيانات
            self.db.execute_query("""
                UPDATE user_sessions 
                SET status = 'terminated' 
                WHERE session_id = ?
            """, (session_id,))
            
            self.logger.info(f"تم إنهاء الجلسة {session_id}: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في إنهاء الجلسة: {e}")
            return False
    
    def check_permission(self, session_id: str, permission: Permission) -> bool:
        """التحقق من صلاحية المستخدم"""
        try:
            is_valid, session = self.validate_session(session_id)
            
            if not is_valid or not session:
                return False
            
            # الحصول على المستخدم
            user = self.user_manager.get_by_id(session.user_id)
            if not user:
                return False
            
            return permission in user.permissions
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من الصلاحية: {e}")
            return False
    
    def update_session_activity(self, session_id: str) -> bool:
        """تحديث نشاط الجلسة"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            # تحديث في الذاكرة
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            
            # تحديث في قاعدة البيانات
            self.db.execute_query("""
                UPDATE user_sessions 
                SET last_activity = ? 
                WHERE session_id = ?
            """, (session.last_activity, session_id))
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث نشاط الجلسة: {e}")
            return False
    
    def _is_user_locked(self, username: str) -> bool:
        """التحقق من قفل المستخدم بسبب محاولات فاشلة"""
        try:
            # الحصول على محاولات تسجيل الدخول الفاشلة في آخر فترة
            cutoff_time = datetime.now() - timedelta(minutes=self.security_settings.lockout_duration_minutes)
            
            failed_attempts = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM login_attempts
                WHERE username = ? AND success = 0 AND timestamp > ?
            """, (username, cutoff_time))
            
            if failed_attempts and failed_attempts[0]['count'] >= self.security_settings.max_login_attempts:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من قفل المستخدم: {e}")
            return False
    
    def _is_password_expired(self, user: User) -> bool:
        """التحقق من انتهاء صلاحية كلمة المرور"""
        if not user.last_password_change:
            return False
        
        expiry_date = user.last_password_change + timedelta(days=self.security_settings.password_expiry_days)
        return datetime.now() > expiry_date
    
    def _is_session_expired(self, session: UserSession) -> bool:
        """التحقق من انتهاء صلاحية الجلسة"""
        timeout = timedelta(minutes=self.security_settings.session_timeout_minutes)
        return datetime.now() - session.last_activity > timeout
    
    def _log_login_attempt(self, username: str, ip_address: Optional[str], success: bool, failure_reason: Optional[str] = None):
        """تسجيل محاولة تسجيل الدخول"""
        try:
            self.db.execute_query("""
                INSERT INTO login_attempts (username, ip_address, success, failure_reason)
                VALUES (?, ?, ?, ?)
            """, (username, ip_address, success, failure_reason))
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل محاولة تسجيل الدخول: {e}")
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """تغيير كلمة المرور"""
        try:
            # التحقق من كلمة المرور الحالية
            user = self.user_manager.get_by_id(user_id)
            if not user:
                return False, "المستخدم غير موجود"
            
            if not self.user_manager.verify_password(old_password, user.password_hash):
                return False, "كلمة المرور الحالية غير صحيحة"
            
            # التحقق من قوة كلمة المرور الجديدة
            is_valid, message = self._validate_password_strength(new_password)
            if not is_valid:
                return False, message
            
            # تغيير كلمة المرور
            success = self.user_manager.change_password(user_id, new_password)
            
            if success:
                self.db_logger.log_action("password_change", "users", user_id, None, None)
                return True, None
            else:
                return False, "فشل في تغيير كلمة المرور"
                
        except Exception as e:
            self.logger.error(f"خطأ في تغيير كلمة المرور: {e}")
            return False, "حدث خطأ في النظام"
    
    def reset_password(self, username: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """إعادة تعيين كلمة المرور"""
        try:
            user = self.user_manager.get_by_username(username)
            if not user:
                return False, "المستخدم غير موجود", None
            
            # إنشاء كلمة مرور مؤقتة
            temp_password = secrets.token_urlsafe(12)
            
            # تحديث كلمة المرور
            success = self.user_manager.reset_password(user.id, temp_password)
            
            if success:
                self.db_logger.log_action("password_reset", "users", user.id, None, None)
                return True, None, temp_password
            else:
                return False, "فشل في إعادة تعيين كلمة المرور", None
                
        except Exception as e:
            self.logger.error(f"خطأ في إعادة تعيين كلمة المرور: {e}")
            return False, "حدث خطأ في النظام", None
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, Optional[str]]:
        """التحقق من قوة كلمة المرور"""
        if len(password) < self.security_settings.password_min_length:
            return False, f"كلمة المرور يجب أن تكون {self.security_settings.password_min_length} أحرف على الأقل"
        
        if self.security_settings.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل"
        
        if self.security_settings.password_require_lowercase and not any(c.islower() for c in password):
            return False, "كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل"
        
        if self.security_settings.password_require_numbers and not any(c.isdigit() for c in password):
            return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
        
        if self.security_settings.password_require_symbols and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل"
        
        return True, None
    
    def get_active_sessions(self, user_id: Optional[int] = None) -> List[UserSession]:
        """الحصول على الجلسات النشطة"""
        try:
            sessions = []
            
            for session in self.active_sessions.values():
                if user_id is None or session.user_id == user_id:
                    if not self._is_session_expired(session):
                        sessions.append(session)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على الجلسات النشطة: {e}")
            return []
    
    def terminate_all_sessions(self, user_id: int, except_session_id: Optional[str] = None) -> int:
        """إنهاء جميع جلسات المستخدم"""
        try:
            terminated_count = 0
            
            sessions_to_terminate = []
            for session_id, session in self.active_sessions.items():
                if session.user_id == user_id and session_id != except_session_id:
                    sessions_to_terminate.append(session_id)
            
            for session_id in sessions_to_terminate:
                if self._terminate_session(session_id, "إنهاء جميع الجلسات"):
                    terminated_count += 1
            
            return terminated_count
            
        except Exception as e:
            self.logger.error(f"خطأ في إنهاء جميع الجلسات: {e}")
            return 0
    
    def get_login_history(self, username: Optional[str] = None, limit: int = 100) -> List[LoginAttempt]:
        """الحصول على تاريخ تسجيل الدخول"""
        try:
            query = "SELECT * FROM login_attempts"
            params = []
            
            if username:
                query += " WHERE username = ?"
                params.append(username)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            results = self.db.execute_query(query, params)
            
            attempts = []
            for row in results:
                attempts.append(LoginAttempt(
                    username=row['username'],
                    ip_address=row['ip_address'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    success=bool(row['success']),
                    failure_reason=row['failure_reason']
                ))
            
            return attempts
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تاريخ تسجيل الدخول: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """تنظيف الجلسات المنتهية الصلاحية"""
        try:
            cleaned_count = 0
            expired_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if self._is_session_expired(session):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                if self._terminate_session(session_id, "انتهت صلاحية الجلسة"):
                    cleaned_count += 1
            
            # تنظيف قاعدة البيانات أيضاً
            cutoff_time = datetime.now() - timedelta(minutes=self.security_settings.session_timeout_minutes)
            self.db.execute_query("""
                UPDATE user_sessions 
                SET status = 'expired' 
                WHERE last_activity < ? AND status = 'active'
            """, (cutoff_time,))
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الجلسات المنتهية: {e}")
            return 0
    
    def update_security_settings(self, settings: Dict[str, Any]) -> bool:
        """تحديث إعدادات الأمان"""
        try:
            for setting_name, setting_value in settings.items():
                if hasattr(self.security_settings, setting_name):
                    # تحديث في الذاكرة
                    setattr(self.security_settings, setting_name, setting_value)
                    
                    # تحديث في قاعدة البيانات
                    self.db.execute_query("""
                        INSERT OR REPLACE INTO security_settings (setting_name, setting_value, updated_at)
                        VALUES (?, ?, ?)
                    """, (setting_name, str(setting_value), datetime.now()))
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث إعدادات الأمان: {e}")
            return False
    
    def generate_jwt_token(self, user: User) -> str:
        """إنشاء JWT token للمستخدم"""
        try:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'role': user.role.value,
                'exp': datetime.utcnow() + timedelta(hours=self.security_settings.jwt_expiry_hours),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(payload, self.security_settings.jwt_secret_key, algorithm='HS256')
            return token
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء JWT token: {e}")
            raise
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """التحقق من JWT token"""
        try:
            payload = jwt.decode(token, self.security_settings.jwt_secret_key, algorithms=['HS256'])
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            self.logger.error(f"خطأ في التحقق من JWT token: {e}")
            return None