#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت فحص الـ Imports غير المستخدمة
يستكشف مجلد src ويقترح الـ imports التي يمكن حذفها
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class ImportChecker:
    def __init__(self, root_dir: str = "src"):
        self.root_dir = Path(root_dir)
        self.unused_imports: Dict[str, List[str]] = {}
        self.errors: List[Tuple[str, str]] = []
    
    def check_file(self, file_path: Path) -> List[str]:
        """فحص ملف واحد وإرجاع قائمة الـ imports غير المستخدمة"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # جمع جميع الـ imports
            imports = set()
            import_froms = defaultdict(set)
            
            # جمع جميع الأسماء المستخدمة
            used_names = set()
            
            for node in ast.walk(tree):
                # جمع الـ imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    module = node.module.split('.')[0] if node.module else None
                    if module:
                        import_froms[module].update(
                            alias.name.split('.')[0] for alias in node.names
                        )
                
                # جمع الأسماء المستخدمة
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # التحقق من الـ imports غير المستخدمة
            unused = []
            
            # فحص الـ imports البسيطة
            for imp in imports:
                if imp not in used_names and imp not in ['sys', 'os', 'typing', 'pathlib']:
                    unused.append(imp)
            
            # فحص الـ import from
            for module, names in import_froms.items():
                if module not in used_names:
                    # التحقق من الأسماء المستوردة
                    for name in names:
                        if name not in used_names:
                            unused.append(f"{module}.{name}")
            
            return unused
            
        except SyntaxError as e:
            self.errors.append((str(file_path), f"Syntax Error: {e}"))
            return []
        except Exception as e:
            self.errors.append((str(file_path), f"Error: {e}"))
            return []
    
    def scan_directory(self):
        """فحص جميع ملفات Python في المجلد"""
        python_files = list(self.root_dir.rglob("*.py"))
        
        print(f"🔍 فحص {len(python_files)} ملف Python...\n")
        
        for file_path in python_files:
            # تخطي ملفات __pycache__ و .venv
            if '__pycache__' in str(file_path) or '.venv' in str(file_path):
                continue
            
            unused = self.check_file(file_path)
            if unused:
                rel_path = file_path.relative_to(self.root_dir)
                self.unused_imports[str(rel_path)] = unused
        
        # طباعة النتائج
        self.print_results()
    
    def print_results(self):
        """طباعة النتائج"""
        if self.unused_imports:
            print("⚠️  وجدت imports غير مستخدمة:\n")
            for file_path, imports in sorted(self.unused_imports.items()):
                print(f"📄 {file_path}:")
                for imp in imports:
                    print(f"   - {imp}")
                print()
        else:
            print("✅ لم يتم العثور على imports غير مستخدمة!")
        
        if self.errors:
            print("\n❌ أخطاء أثناء الفحص:\n")
            for file_path, error in self.errors:
                print(f"📄 {file_path}: {error}")

if __name__ == "__main__":
    checker = ImportChecker()
    checker.scan_directory()

