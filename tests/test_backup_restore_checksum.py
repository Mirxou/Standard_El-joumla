from pathlib import Path
from src.services.backup_service import BackupService


class DummyDB2:
    def __init__(self, path: str):
        self.db_path = path
        self.connection = None
    def initialize(self):
        pass
    def execute_query(self, *args, **kwargs):
        return []
    def execute_update(self, *args, **kwargs):
        return 0


def test_backup_restore_and_verify(tmp_path):
    db_file = tmp_path / 'main.db'
    db_file.write_bytes(b'content-data-123')
    backups_dir = tmp_path / 'bks'
    svc = BackupService(DummyDB2(str(db_file)), str(backups_dir))
    svc.set_encryption_password('VeryStrong#Pass99')
    created = svc.create_backup(description='chk', compress=True, encrypt=True)
    assert created['success'] is True
    backup_name = created['backup_name']
    verify = svc.verify_backup(backup_name, password='VeryStrong#Pass99')
    assert verify['success'] is True and verify['match'] is True
    restored = svc.restore_backup(backup_name, password='VeryStrong#Pass99')
    assert restored['success'] is True and restored['checksum_verified'] is True
