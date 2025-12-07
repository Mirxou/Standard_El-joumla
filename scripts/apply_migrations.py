"""
سكريبت تطبيق جميع الـ migrations على قاعدة البيانات
"""
import sqlite3
import sys
from pathlib import Path

# إضافة المسار الجذري للمشروع
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def backup_database(db_path: Path):
    """نسخ احتياطي لقاعدة البيانات"""
    backup_path = db_path.parent / f"{db_path.stem}_backup_{Path(db_path).stat().st_mtime:.0f}{db_path.suffix}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ تم إنشاء نسخة احتياطية: {backup_path.name}")
    return backup_path

def apply_migrations(db_path: Path, migrations_dir: Path, force: bool = False):
    """تطبيق جميع migrations على قاعدة البيانات"""
    
    if not db_path.exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    if not migrations_dir.exists():
        print(f"❌ مجلد migrations غير موجود: {migrations_dir}")
        return False
    
    # نسخة احتياطية
    backup_path = backup_database(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # جدول لتتبع الـ migrations المطبقة
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_file TEXT UNIQUE NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # الحصول على الـ migrations المطبقة مسبقاً
        applied = set(row[0] for row in conn.execute("SELECT migration_file FROM schema_migrations").fetchall())
        
        # قراءة وتطبيق الـ migrations
        migration_files = sorted(migrations_dir.glob("*.sql"))
        print(f"\n📁 وُجد {len(migration_files)} ملف migration\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for migration_file in migration_files:
            migration_name = migration_file.name
            
            if migration_name in applied and not force:
                print(f"⏭️  {migration_name} - مُطبّق مسبقاً (تخطي)")
                skip_count += 1
                continue
            
            print(f"▶️  تطبيق: {migration_name}...", end=" ")
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # تقسيم الاستعلامات
                queries = [q.strip() for q in sql_content.split(';') if q.strip()]
                
                # تنفيذ كل استعلام
                for query in queries:
                    if query.strip():
                        try:
                            conn.execute(query)
                        except sqlite3.OperationalError as e:
                            error_msg = str(e).lower()
                            # تجاهل الأخطاء المتعلقة بالأعمدة الموجودة مسبقاً
                            if "duplicate column" in error_msg or "already exists" in error_msg:
                                print(f"   ⚠️  تخطي: {query[:50]}... (موجود مسبقاً)")
                                continue
                            # تجاهل الأخطاء المتعلقة بالفهارس الموجودة مسبقاً
                            elif "index" in error_msg and "already exists" in error_msg:
                                print(f"   ⚠️  تخطي: {query[:50]}... (موجود مسبقاً)")
                                continue
                            else:
                                raise
                
                # تسجيل Migration كمطبّق
                conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations (migration_file) VALUES (?)",
                    (migration_name,)
                )
                conn.commit()
                
                print("✅")
                success_count += 1
                
            except Exception as e:
                conn.rollback()
                print(f"❌ خطأ: {e}")
                error_count += 1
                
                # في حالة خطأ، نتوقف أو نستمر حسب الخيار
                if not force:
                    print("\n⚠️  توقف التطبيق بسبب خطأ. استخدم --force للمتابعة رغم الأخطاء.")
                    break
        
        conn.close()
        
        # النتيجة النهائية
        print(f"\n{'='*60}")
        print(f"✅ نجح: {success_count}")
        print(f"⏭️  تم تخطيه: {skip_count}")
        print(f"❌ فشل: {error_count}")
        print(f"{'='*60}\n")
        
        if error_count > 0:
            print(f"⚠️  يمكنك استرجاع النسخة الاحتياطية من: {backup_path}")
        
        return error_count == 0
        
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        print(f"⚠️  استرجع النسخة الاحتياطية من: {backup_path}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="تطبيق migrations على قاعدة البيانات")
    parser.add_argument("--db", default="data/inventory.db", help="مسار قاعدة البيانات")
    parser.add_argument("--migrations", default="migrations", help="مسار مجلد migrations")
    parser.add_argument("--force", action="store_true", help="إعادة تطبيق جميع migrations حتى لو طُبّقت مسبقاً")
    
    args = parser.parse_args()
    
    db_path = project_root / args.db
    migrations_dir = project_root / args.migrations
    
    print("="*60)
    print("تطبيق Database Migrations")
    print("="*60)
    print(f"قاعدة البيانات: {db_path}")
    print(f"مجلد Migrations: {migrations_dir}")
    print(f"وضع Force: {args.force}")
    print("="*60 + "\n")
    
    success = apply_migrations(db_path, migrations_dir, args.force)
    
    if success:
        print("✅ تم تطبيق جميع migrations بنجاح!")
        sys.exit(0)
    else:
        print("❌ فشل تطبيق بعض migrations")
        sys.exit(1)
