#!/usr/bin/env python3
"""
نظام السجلات المحسّن - Enhanced Logging System
سجلات دوارة مع فصل حسب النوع وتسجيل الاستعلامات البطيئة
"""

import os
import logging
import json
import time
import glob
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any, List


class StructuredFormatter(logging.Formatter):
    """منسق السجلات المنظم"""
    
    def __init__(self, include_user: bool = True):
        super().__init__()
        self.include_user = include_user
        self._current_user = "system"
    
    def set_user(self, username: str):
        self._current_user = username
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname.ljust(8)
        module = record.name
        
        parts = [f"[{timestamp}]", f"[{level}]", f"[{module}]"]
        
        if self.include_user:
            parts.append(f"[user:{self._current_user}]")
        
        message = record.getMessage()
        parts.append(message)
        
        # استثناء
        if record.exc_info and record.exc_info[0]:
            parts.append('\n' + self.formatException(record.exc_info))
        
        return ' '.join(parts)


class JSONFormatter(logging.Formatter):
    """منسق JSON للتحليل الآلي"""
    
    def __init__(self, app_name: str = "ElJoumla", app_version: str = "6.0.0"):
        super().__init__()
        self.app_name = app_name
        self.app_version = app_version
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "app": self.app_name,
            "version": self.app_version,
            "line": record.lineno,
            "func": record.funcName,
        }
        
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class EnhancedLoggingSystem:
    """نظام السجلات المحسّن"""
    
    DEFAULT_LOG_DIR = "logs"
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    MAX_LOG_AGE_DAYS = 30
    
    def __init__(self, log_dir: str = "logs", app_name: str = "ElJoumla",
                 app_version: str = "6.0.0", json_format: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.app_name = app_name
        self.app_version = app_version
        self.json_format = json_format
        
        self._handlers: Dict[str, logging.Handler] = {}
        self._formatters: Dict[str, logging.Formatter] = {}
        self._structured_formatter: Optional[StructuredFormatter] = None
        
        self._setup()
    
    def _setup(self):
        """إعداد السجلات"""
        # المنسقات
        self._structured_formatter = StructuredFormatter()
        json_formatter = JSONFormatter(self.app_name, self.app_version)
        
        # ملفات السجل
        log_files = {
            'app': 'eljoumla.log',
            'slow_queries': 'slow_queries.log',
            'security': 'security.log',
            'crash': 'crash.log',
        }
        
        for name, filename in log_files.items():
            filepath = self.log_dir / filename
            
            handler = RotatingFileHandler(
                str(filepath),
                maxBytes=self.MAX_BYTES,
                backupCount=self.BACKUP_COUNT,
                encoding='utf-8',
            )
            
            if self.json_format:
                handler.setFormatter(json_formatter)
            else:
                handler.setFormatter(self._structured_formatter)
            
            self._handlers[name] = handler
        
        # المعالج الرئيسي
        app_logger = logging.getLogger()
        app_logger.addHandler(self._handlers['app'])
        app_logger.setLevel(logging.INFO)
        
        # سجل الأمن
        security_logger = logging.getLogger('security')
        security_logger.addHandler(self._handlers['security'])
        security_logger.setLevel(logging.WARNING)
        
        # سجل الاستعلامات البطيئة
        slow_query_logger = logging.getLogger('slow_query')
        slow_query_logger.addHandler(self._handlers['slow_queries'])
        slow_query_logger.setLevel(logging.WARNING)
    
    def set_user(self, username: str):
        """تعيين المستخدم الحالي للسجلات"""
        if self._structured_formatter:
            self._structured_formatter.set_user(username)
    
    def log_slow_query(self, query: str, duration_ms: float, 
                       threshold_ms: float = 500.0, params: str = ""):
        """تسجيل استعلام بطيء"""
        if duration_ms >= threshold_ms:
            logger = logging.getLogger('slow_query')
            logger.warning(
                f"استعلام بطيء: {duration_ms:.0f}ms >= {threshold_ms:.0f}ms | "
                f"SQL: {query[:200]}{'...' if len(query) > 200 else ''} | "
                f"Params: {params[:100]}"
            )
    
    def log_security_event(self, event_type: str, details: str, 
                           level: str = "WARNING"):
        """تسجيل حدث أمني"""
        logger = logging.getLogger('security')
        message = f"[{event_type}] {details}"
        
        if level == "CRITICAL":
            logger.critical(message)
        elif level == "ERROR":
            logger.error(message)
        else:
            logger.warning(message)
    
    def cleanup_old_logs(self):
        """حذف السجلات القديمة"""
        cutoff = datetime.now() - timedelta(days=self.MAX_LOG_AGE_DAYS)
        deleted = 0
        
        for log_file in glob.glob(str(self.log_dir / "*.log*")):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if mtime < cutoff:
                    os.remove(log_file)
                    deleted += 1
            except Exception:
                pass
        
        if deleted > 0:
            logging.getLogger(__name__).info(f"تم حذف {deleted} ملف سجل قديم")
    
    def get_recent_logs(self, log_name: str = 'app', lines: int = 100) -> List[str]:
        """قراءة آخر N سطر من سجل"""
        filename_map = {
            'app': 'eljoumla.log',
            'slow_queries': 'slow_queries.log',
            'security': 'security.log',
            'crash': 'crash.log',
        }
        
        filename = filename_map.get(log_name, 'eljoumla.log')
        filepath = self.log_dir / filename
        
        if not filepath.exists():
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception:
            return []
    
    def get_log_stats(self) -> Dict[str, Any]:
        """إحصائيات السجلات"""
        stats = {}
        for name, handler in self._handlers.items():
            if isinstance(handler, RotatingFileHandler):
                filepath = Path(handler.baseFilename)
                size = filepath.stat().st_size if filepath.exists() else 0
                stats[name] = {
                    'file': str(filepath),
                    'size_mb': round(size / (1024 * 1024), 2),
                    'backups': len(list(filepath.parent.glob(f"{filepath.name}.*"))) if filepath.exists() else 0,
                }
        return stats
