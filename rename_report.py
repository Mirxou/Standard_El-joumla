import os
from pathlib import Path

def main():
    base_dir = Path(r"c:\Users\pc\Desktop\الإصدار المنطقي trae\src\services")
    src = base_dir / "report_service.py"
    dst = base_dir / "report_generator.py"
    
    print(f"Attempting to rename: {src} -> {dst}")
    
    if not src.exists():
        print(f"❌ Source file does not exist: {src}")
        # Try listing dir to see what's there
        print("Files in directory:")
        for f in base_dir.glob("*.py"):
            print(f.name)
        return

    try:
        os.rename(src, dst)
        print("✅ Rename successful.")
    except Exception as e:
        print(f"❌ Rename failed: {e}")

if __name__ == "__main__":
    main()
