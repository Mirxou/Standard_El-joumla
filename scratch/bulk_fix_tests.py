import os
import re
from pathlib import Path

def fix_all_unit_tests():
    tests_dir = Path("tests/unit")
    fixed_files = []
    
    for test_file in tests_dir.glob("test_*.py"):
        content = test_file.read_text(encoding="utf-8")
        
        # Check if it uses db_manager=Mock()
        if "db_manager=Mock()" in content or "db_manager = Mock()" in content:
            # Replace with MagicMock and setup return values
            # Also ensure MagicMock is imported
            if "from unittest.mock import" in content:
                if "MagicMock" not in content:
                    content = content.replace("from unittest.mock import", "from unittest.mock import MagicMock,")
            
            # Create a more robust mock setup
            # We want to replace db_manager=Mock() with something like:
            # mock_db = MagicMock(); mock_db.fetch_all.return_value = []; return Class(mock_db)
            
            # Pattern 1: return Class(db_manager=Mock())
            content = re.sub(
                r"return ([a-zA-Z0-9_]+)\(db_manager=Mock\(\)\)",
                r"mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return \1(db_manager=mock_db)",
                content
            )
            
            # Pattern 2: return Class(Mock())
            content = re.sub(
                r"return ([a-zA-Z0-9_]+)\(Mock\(\)\)",
                r"mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return \1(mock_db)",
                content
            )
            
            test_file.write_text(content, encoding="utf-8")
            fixed_files.append(test_file)
            
    return fixed_files

if __name__ == "__main__":
    fixed = fix_all_unit_tests()
    print(f"Fixed {len(fixed)} files.")
