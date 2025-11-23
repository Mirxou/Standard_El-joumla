#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار تفعيل وتعطيل النسخ الاحتياطي التلقائي"""
import time
import pytest
from pathlib import Path
from src.core.database_manager import DatabaseManager
from src.services.backup_service import BackupService

@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / 'auto_backup.db'
    manager = DatabaseManager(str(db_path))
    manager.initialize()
    return manager

@pytest.fixture
def backup_service(db, tmp_path):
    bdir = tmp_path / 'backups'
    svc = BackupService(db, backup_dir=str(bdir))
    return svc

def test_enable_auto_backup_creates_backup(backup_service):
    assert backup_service.enable_auto_backup(interval_hours=24, keep_count=5) is True
    # النسخة الفورية يجب أن تُنشأ
    files = list(Path(backup_service.backup_dir).glob('backup_*.zip'))
    assert len(files) >= 1

def test_disable_auto_backup(backup_service):
    backup_service.enable_auto_backup(interval_hours=24)
    assert backup_service.disable_auto_backup() is True
    assert backup_service._auto_backup_enabled is False

