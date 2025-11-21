#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من سلامة النسخة الاحتياطية
Verify encrypted backup integrity
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.encrypted_backup_service import EncryptedBackupService

def verify_backup(backup_file: str):
    """التحقق من سلامة نسخة احتياطية مشفرة"""
    print("=" * 70)
    print("🔍 التحقق من سلامة النسخة الاحتياطية")
    print("=" * 70)
    
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"\n❌ الملف غير موجود: {backup_file}")
        return False
    
    print(f"\n📁 الملف: {backup_path.name}")
    print(f"📏 الحجم: {backup_path.stat().st_size / 1024:.2f} KB")
    
    try:
        # Initialize service
        service = EncryptedBackupService(
            database_path="data/logical_release.db",
            backup_dir=str(backup_path.parent)
        )
        
        print("\n🔐 جاري التحقق...")
        
        # Read and verify
        with open(backup_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Try to decrypt and verify checksum
        try:
            # Decrypt
            decrypted_data = service._decrypt_data(encrypted_data)
            print("   ✅ التشفير سليم")
            
            # Decompress
            import gzip
            decompressed_data = gzip.decompress(decrypted_data)
            print("   ✅ الضغط سليم")
            
            # Verify it's a valid SQLite database
            if decompressed_data[:16] == b'SQLite format 3\x00':
                print("   ✅ قاعدة البيانات سليمة")
            else:
                print("   ⚠️  تحذير: البيانات قد لا تكون قاعدة بيانات صحيحة")
            
            # Check metadata if exists
            metadata_path = backup_path.with_suffix('.metadata.json')
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as mf:
                    metadata = json.load(mf)
                
                print("\n📋 البيانات الوصفية:")
                print(f"   التاريخ: {metadata.get('timestamp', 'غير متوفر')}")
                print(f"   الحجم الأصلي: {metadata.get('original_size', 0) / 1024:.2f} KB")
                print(f"   الحجم المضغوط: {metadata.get('compressed_size', 0) / 1024:.2f} KB")
                
                # Verify checksum if available
                if 'checksum' in metadata:
                    import hashlib
                    actual_checksum = hashlib.sha256(decompressed_data).hexdigest()
                    expected_checksum = metadata['checksum']
                    
                    if actual_checksum == expected_checksum:
                        print("   ✅ التحقق من Checksum نجح")
                    else:
                        print("   ❌ فشل التحقق من Checksum")
                        return False
            
            print("\n" + "=" * 70)
            print("✅ النسخة الاحتياطية صالحة للاستخدام")
            print("=" * 70)
            
            return True
            
        except Exception as decrypt_error:
            print(f"   ❌ فشل فك التشفير: {str(decrypt_error)}")
            return False
        
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("الاستخدام: python verify_backup.py <backup_file.encrypted>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    success = verify_backup(backup_file)
    sys.exit(0 if success else 1)
