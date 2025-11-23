#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة النسخ الاحتياطي التدريجي
Incremental Backup Service
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import sqlite3
import json
import hashlib
import shutil


class IncrementalBackupService:
    """خدمة النسخ الاحتياطي التدريجي (Delta Backups)"""
    
    def __init__(self, database_path: str, backup_dir: str):
        self.database_path = database_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # جدول لتتبع التغييرات
        self.changes_db_path = self.backup_dir / "backup_changes.db"
        self._init_changes_tracking()
    
    def _init_changes_tracking(self):
        """تهيئة قاعدة بيانات تتبع التغييرات"""
        conn = sqlite3.connect(str(self.changes_db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_name TEXT NOT NULL UNIQUE,
                backup_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tables_hash TEXT,
                base_snapshot_id INTEGER,
                FOREIGN KEY (base_snapshot_id) REFERENCES backup_snapshots(id)
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS table_checksums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                row_count INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES backup_snapshots(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_full_backup(self, snapshot_name: Optional[str] = None) -> Dict[str, Any]:
        """إنشاء نسخة احتياطية كاملة"""
        try:
            if snapshot_name is None:
                snapshot_name = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_file = self.backup_dir / f"{snapshot_name}.db"
            
            # نسخ قاعدة البيانات الكاملة
            shutil.copy2(self.database_path, backup_file)
            
            # حساب checksums لجميع الجداول
            table_checksums = self._calculate_table_checksums()
            
            # تسجيل snapshot
            conn = sqlite3.connect(str(self.changes_db_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO backup_snapshots (snapshot_name, backup_type, tables_hash) VALUES (?, ?, ?)",
                (snapshot_name, 'full', json.dumps(table_checksums))
            )
            snapshot_id = cursor.lastrowid
            
            # تسجيل checksums للجداول
            for table_name, checksum_data in table_checksums.items():
                cursor.execute(
                    "INSERT INTO table_checksums (snapshot_id, table_name, checksum, row_count) VALUES (?, ?, ?, ?)",
                    (snapshot_id, table_name, checksum_data['checksum'], checksum_data['row_count'])
                )
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'snapshot_name': snapshot_name,
                'snapshot_id': snapshot_id,
                'backup_file': str(backup_file),
                'backup_type': 'full',
                'tables_count': len(table_checksums),
                'created_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_incremental_backup(self, base_snapshot_name: Optional[str] = None) -> Dict[str, Any]:
        """إنشاء نسخة احتياطية تدريجية (فقط التغييرات)"""
        try:
            # الحصول على آخر snapshot كقاعدة
            conn = sqlite3.connect(str(self.changes_db_path))
            cursor = conn.cursor()
            
            if base_snapshot_name:
                cursor.execute(
                    "SELECT * FROM backup_snapshots WHERE snapshot_name = ?",
                    (base_snapshot_name,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM backup_snapshots ORDER BY created_at DESC LIMIT 1"
                )
            
            base_snapshot = cursor.fetchone()
            
            if not base_snapshot:
                conn.close()
                return {
                    'success': False,
                    'error': 'لا توجد نسخة احتياطية أساسية. يجب إنشاء نسخة كاملة أولاً.'
                }
            
            base_snapshot_id = base_snapshot[0]
            base_snapshot_name = base_snapshot[1]
            
            # حساب checksums الحالية
            current_checksums = self._calculate_table_checksums()
            
            # الحصول على checksums القاعدة
            cursor.execute(
                "SELECT table_name, checksum, row_count FROM table_checksums WHERE snapshot_id = ?",
                (base_snapshot_id,)
            )
            base_checksums = {row[0]: {'checksum': row[1], 'row_count': row[2]} for row in cursor.fetchall()}
            
            # تحديد الجداول المتغيرة
            changed_tables = []
            for table_name, current_data in current_checksums.items():
                base_data = base_checksums.get(table_name)
                if not base_data or base_data['checksum'] != current_data['checksum']:
                    changed_tables.append(table_name)
            
            if not changed_tables:
                conn.close()
                return {
                    'success': True,
                    'snapshot_name': None,
                    'message': 'لا توجد تغييرات منذ آخر نسخة احتياطية',
                    'changed_tables': []
                }
            
            # إنشاء اسم للنسخة التدريجية
            snapshot_name = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # تصدير الجداول المتغيرة فقط
            delta_file = self.backup_dir / f"{snapshot_name}.sql"
            self._export_tables_to_sql(changed_tables, delta_file)
            
            # تسجيل النسخة التدريجية
            cursor.execute(
                "INSERT INTO backup_snapshots (snapshot_name, backup_type, tables_hash, base_snapshot_id) VALUES (?, ?, ?, ?)",
                (snapshot_name, 'incremental', json.dumps(current_checksums), base_snapshot_id)
            )
            snapshot_id = cursor.lastrowid
            
            # تسجيل checksums للجداول
            for table_name, checksum_data in current_checksums.items():
                cursor.execute(
                    "INSERT INTO table_checksums (snapshot_id, table_name, checksum, row_count) VALUES (?, ?, ?, ?)",
                    (snapshot_id, table_name, checksum_data['checksum'], checksum_data['row_count'])
                )
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'snapshot_name': snapshot_name,
                'snapshot_id': snapshot_id,
                'backup_file': str(delta_file),
                'backup_type': 'incremental',
                'base_snapshot': base_snapshot_name,
                'changed_tables': changed_tables,
                'tables_count': len(changed_tables),
                'created_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_table_checksums(self) -> Dict[str, Dict[str, Any]]:
        """حساب checksums لجميع الجداول"""
        checksums = {}
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # الحصول على قائمة الجداول
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                # حساب checksum بناءً على محتوى الجدول
                cursor.execute(f"SELECT * FROM {table} ORDER BY rowid")
                rows = cursor.fetchall()
                
                # تحويل البيانات إلى نص وحساب hash
                table_data = json.dumps(rows, sort_keys=True, default=str)
                checksum = hashlib.sha256(table_data.encode()).hexdigest()
                
                checksums[table] = {
                    'checksum': checksum,
                    'row_count': len(rows)
                }
            except Exception:
                # تخطي الجداول التي لا يمكن قراءتها
                pass
        
        conn.close()
        return checksums
    
    def _export_tables_to_sql(self, tables: List[str], output_file: Path):
        """تصدير جداول محددة إلى ملف SQL"""
        conn = sqlite3.connect(self.database_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- Incremental Backup SQL Dump\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Tables: {', '.join(tables)}\n\n")
            
            for table in tables:
                try:
                    # حذف الجدول إذا كان موجوداً
                    f.write(f"-- Table: {table}\n")
                    f.write(f"DELETE FROM {table};\n")
                    
                    # تصدير البيانات
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    # الحصول على أسماء الأعمدة
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    if rows:
                        for row in rows:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")
                                else:
                                    values.append(str(val))
                            
                            f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                    
                    f.write("\n")
                
                except Exception as e:
                    f.write(f"-- Error exporting table {table}: {str(e)}\n\n")
        
        conn.close()
    
    def restore_from_incremental(self, snapshot_name: str) -> Dict[str, Any]:
        """استعادة من نسخة تدريجية (يتطلب تطبيق جميع التغييرات من القاعدة)"""
        try:
            conn = sqlite3.connect(str(self.changes_db_path))
            cursor = conn.cursor()
            
            # الحصول على معلومات النسخة
            cursor.execute(
                "SELECT * FROM backup_snapshots WHERE snapshot_name = ?",
                (snapshot_name,)
            )
            snapshot = cursor.fetchone()
            
            if not snapshot:
                conn.close()
                return {
                    'success': False,
                    'error': f'النسخة الاحتياطية {snapshot_name} غير موجودة'
                }
            
            snapshot_type = snapshot[2]
            
            if snapshot_type == 'full':
                # استعادة من نسخة كاملة
                backup_file = self.backup_dir / f"{snapshot_name}.db"
                if backup_file.exists():
                    shutil.copy2(backup_file, self.database_path)
                    conn.close()
                    return {
                        'success': True,
                        'message': 'تمت الاستعادة من النسخة الكاملة',
                        'snapshot_name': snapshot_name
                    }
                else:
                    conn.close()
                    return {
                        'success': False,
                        'error': 'ملف النسخة الاحتياطية غير موجود'
                    }
            
            else:
                # استعادة من نسخة تدريجية - يتطلب تطبيق chain
                conn.close()
                return {
                    'success': False,
                    'error': 'استعادة النسخ التدريجية تتطلب تطبيق سلسلة التغييرات - لم يتم تطبيقها بعد'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """قائمة جميع النسخ الاحتياطية"""
        try:
            conn = sqlite3.connect(str(self.changes_db_path))
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT snapshot_name, backup_type, created_at, base_snapshot_id FROM backup_snapshots ORDER BY created_at DESC"
            )
            
            backups = []
            for row in cursor.fetchall():
                backups.append({
                    'snapshot_name': row[0],
                    'backup_type': row[1],
                    'created_at': row[2],
                    'base_snapshot_id': row[3]
                })
            
            conn.close()
            return backups
        
        except Exception:
            return []
    
    def get_backup_chain(self, snapshot_name: str) -> List[str]:
        """الحصول على سلسلة النسخ المطلوبة للاستعادة"""
        try:
            conn = sqlite3.connect(str(self.changes_db_path))
            cursor = conn.cursor()
            
            chain = []
            current_name = snapshot_name
            
            while current_name:
                cursor.execute(
                    "SELECT snapshot_name, backup_type, base_snapshot_id FROM backup_snapshots WHERE snapshot_name = ?",
                    (current_name,)
                )
                snapshot = cursor.fetchone()
                
                if not snapshot:
                    break
                
                chain.insert(0, snapshot[0])
                
                # إذا وصلنا لنسخة كاملة، نتوقف
                if snapshot[1] == 'full':
                    break
                
                # الانتقال للنسخة الأساسية
                base_id = snapshot[2]
                if base_id:
                    cursor.execute(
                        "SELECT snapshot_name FROM backup_snapshots WHERE id = ?",
                        (base_id,)
                    )
                    base_row = cursor.fetchone()
                    current_name = base_row[0] if base_row else None
                else:
                    break
            
            conn.close()
            return chain
        
        except Exception:
            return []
