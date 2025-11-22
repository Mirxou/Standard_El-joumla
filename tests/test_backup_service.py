import os
from pathlib import Path
from src.services.backup_service import BackupService

class DummyDB:
    def __init__(self, path: str):
        self.db_path = path
        self.connection = None
    def initialize(self):
        pass
    def execute_query(self, *args, **kwargs):
        return []
    def execute_update(self, *args, **kwargs):
        return 0


def test_backup_create(tmp_path):
    db_file = tmp_path / "test.db"
    db_file.write_bytes(b"dummy")
    bkdir = tmp_path / "backups"
    svc = BackupService(DummyDB(str(db_file)), str(bkdir))
    res = svc.create_backup(description="t", compress=True, encrypt=False)
    assert res["success"] is True
    assert Path(res["path"]).exists()


def test_backup_create_encrypted(tmp_path):
    db_file = tmp_path / "test.db"
    db_file.write_bytes(b"dummy")
    bkdir = tmp_path / "backups"
    svc = BackupService(DummyDB(str(db_file)), str(bkdir))
    svc.set_encryption_password("Strong#Passw0rd!")
    res = svc.create_backup(description="enc", compress=True, encrypt=True)
    assert res["success"] is True
    p = Path(res["path"]) 
    assert p.suffix.endswith(".enc") or p.name.endswith(".enc")
