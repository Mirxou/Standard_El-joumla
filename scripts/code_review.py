#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  Code Review Automation Script — Standard El-Joumla ERP      ║
# ║  Aurora Noir v4.0 — Pre-commit & Pre-PR Quality Gates        ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# الاستخدام:
#   python scripts/code_review.py                    # فحص كامل
#   python scripts/code_review.py --staged           # فحص الملفات المعدلة فقط
#   python scripts/code_review.py --fix              # إصلاح تلقائي
#   python scripts/code_review.py --security         # فحص أمني فقط
#

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# ── Colors ──────────────────────────────────────────────────────────

class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# ── Issue Model ─────────────────────────────────────────────────────

@dataclass
class Issue:
    file: str
    line: int
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # syntax, style, security, design, logic
    message: str
    auto_fixable: bool = False


# ── Review Checks ──────────────────────────────────────────────────

class CodeReviewer:
    def __init__(self, root: str = "src"):
        self.root = Path(root)
        self.issues: List[Issue] = []

    def get_files(self, staged_only: bool = False) -> List[Path]:
        """Get Python files to review."""
        if staged_only:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached", "--diff-filter=ACM"],
                capture_output=True, text=True
            )
            files = [
                Path(f) for f in result.stdout.strip().split("\n")
                if f.endswith(".py") and Path(f).exists()
            ]
        else:
            files = list(self.root.rglob("*.py"))
            # Exclude legacy/tests
            files = [f for f in files if "legacy" not in str(f) and "__pycache__" not in str(f)]
        return sorted(files)

    def check_syntax(self, files: List[Path]):
        """1️⃣ Syntax validation."""
        print(f"\n{C.BOLD}{C.CYAN}1️⃣  Syntax Validation{C.END}")
        for f in files:
            try:
                compile(f.read_text(encoding="utf-8"), str(f), "exec")
            except SyntaxError as e:
                self.issues.append(Issue(
                    file=str(f), line=e.lineno or 0,
                    severity="CRITICAL", category="syntax",
                    message=f"SyntaxError: {e.msg}"
                ))
        if not any(i.severity == "CRITICAL" and i.category == "syntax" for i in self.issues):
            print(f"   {C.GREEN}✅ All {len(files)} files compile successfully{C.END}")

    def check_hardcoded_colors(self, files: List[Path]):
        """2️⃣ Design token compliance."""
        print(f"\n{C.BOLD}{C.CYAN}2️⃣  Design Token Compliance{C.END}")
        TOKEN_FILE = "design_tokens.py"
        HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{6}")
        EXEMPT_COLORS = {"#C8A54E", "#E8C96A", "#A88A3E"}  # design token defs

        total_hardcoded = 0
        for f in files:
            if TOKEN_FILE in str(f):
                continue
            content = f.read_text(encoding="utf-8", errors="ignore")
            matches = HEX_PATTERN.findall(content)
            non_exempt = [m for m in matches if m.upper() not in EXEMPT_COLORS]
            if non_exempt:
                total_hardcoded += len(non_exempt)
                rel = str(f.relative_to(self.root))
                print(f"   {C.YELLOW}⚠️  {rel}: {len(non_exempt)} hardcoded colors{C.END}")
        if total_hardcoded == 0:
            print(f"   {C.GREEN}✅ No hardcoded colors found{C.END}")
        else:
            print(f"   {C.YELLOW}📊 Total: {total_hardcoded} hardcoded colors across UI files{C.END}")

    def check_shebang(self, files: List[Path]):
        """3️⃣ Shebang ordering."""
        print(f"\n{C.BOLD}{C.CYAN}3️⃣  Shebang Ordering{C.END}")
        count = 0
        for f in files:
            lines = f.read_text(encoding="utf-8", errors="ignore").split("\n")[:3]
            if len(lines) >= 2:
                if "import" in lines[0] and "#!/usr/bin/env" in lines[1]:
                    self.issues.append(Issue(
                        file=str(f), line=1, severity="LOW", category="style",
                        message="Shebang on line 2 (should be line 1)", auto_fixable=True
                    ))
                    count += 1
        if count == 0:
            print(f"   {C.GREEN}✅ All shebangs correctly ordered{C.END}")
        else:
            print(f"   {C.YELLOW}⚠️  {count} files with wrong shebang order{C.END}")

    def check_sql_injection(self, files: List[Path]):
        """4️⃣ SQL injection patterns."""
        print(f"\n{C.BOLD}{C.CYAN}4️⃣  SQL Injection Check{C.END}")
        DANGEROUS_PATTERNS = [
            (r'f["\'].*SELECT.*\{.*\}.*FROM', "f-string in SELECT"),
            (r'f["\'].*WHERE.*\{.*\}', "f-string in WHERE"),
            (r'\.format\(.+\).*(?:SELECT|WHERE|INSERT|UPDATE|DELETE)', ".format() in SQL"),
        ]
        count = 0
        for f in files:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in DANGEROUS_PATTERNS:
                for m in re.finditer(pattern, content, re.IGNORECASE):
                    line_no = content[:m.start()].count("\n") + 1
                    self.issues.append(Issue(
                        file=str(f), line=line_no,
                        severity="HIGH", category="security",
                        message=f"Potential SQL injection: {desc}"
                    ))
                    count += 1
        if count == 0:
            print(f"   {C.GREEN}✅ No SQL injection patterns found{C.END}")
        else:
            print(f"   {C.RED}🚨 {count} potential SQL injection(s) found!{C.END}")

    def check_bare_logging(self, files: List[Path]):
        """5️⃣ Bare logging (bypasses instance logger)."""
        print(f"\n{C.BOLD}{C.CYAN}5️⃣  Bare Logging Check{C.END}")
        count = 0
        for f in files:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r'logging\.getLogger\(__name__\)\.\w+\(', content):
                line_no = content[:m.start()].count("\n") + 1
                count += 1
                self.issues.append(Issue(
                    file=str(f), line=line_no, severity="MEDIUM", category="style",
                    message="Bare logging.getLogger() — use self.logger instead"
                ))
        if count == 0:
            print(f"   {C.GREEN}✅ No bare logging calls{C.END}")
        else:
            print(f"   {C.YELLOW}⚠️  {count} bare logging calls found{C.END}")

    def check_none_safety(self, files: List[Path]):
        """6️⃣ None safety — accessing attributes/methods on potentially None objects."""
        print(f"\n{C.BOLD}{C.CYAN}6️⃣  None Safety Check{C.END}")
        count = 0
        for f in files:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # Find patterns like: result = self.db.fetch_one(...) ... result["key"] without if result:
            # This is a simplified heuristic
            lines = content.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()
                if re.match(r'\w+\s*=\s*self\.db\.fetch_one\(', stripped):
                    # Check if next non-empty line accesses the result without a None check
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_stripped = lines[j].strip()
                        if not next_stripped or next_stripped.startswith("#"):
                            continue
                        if next_stripped.startswith("if ") and "is not None" in next_stripped:
                            break  # Has check, OK
                        if next_stripped.startswith("if ") and "else" in next_stripped:
                            break
                        if "[" in next_stripped and "(" not in next_stripped.split("[")[0]:
                            count += 1
                        break
        if count == 0:
            print(f"   {C.GREEN}✅ No obvious None safety issues{C.END}")
        else:
            print(f"   {C.YELLOW}⚠️  {count} potential None safety issues{C.END}")

    def run_review(self, staged_only: bool = False):
        """Run all review checks."""
        files = self.get_files(staged_only)
        print(f"\n{C.BOLD}╔══════════════════════════════════════════════════════════════╗{C.END}")
        print(f"{C.BOLD}║  🏢 Code Review — Standard El-Joumla ERP v4.0             ║{C.END}")
        print(f"{C.BOLD}║  📁 Files: {len(files):<48}║{C.END}")
        print(f"{C.BOLD}╚══════════════════════════════════════════════════════════════╝{C.END}")

        self.check_syntax(files)
        self.check_hardcoded_colors(files)
        self.check_shebang(files)
        self.check_sql_injection(files)
        self.check_bare_logging(files)
        self.check_none_safety(files)

        # ── Summary ─────────────────────────────────────────────────
        print(f"\n{C.BOLD}📊 Review Summary{C.END}")
        critical = len([i for i in self.issues if i.severity == "CRITICAL"])
        high = len([i for i in self.issues if i.severity == "HIGH"])
        medium = len([i for i in self.issues if i.severity == "MEDIUM"])
        low = len([i for i in self.issues if i.severity == "LOW"])

        print(f"   🔴 Critical: {critical}")
        print(f"   🟠 High:     {high}")
        print(f"   🟡 Medium:   {medium}")
        print(f"   ⚪ Low:      {low}")
        print(f"   ─────────────────────")
        print(f"   Total:     {len(self.issues)}")

        if critical > 0 or high > 0:
            print(f"\n   {C.RED}🚨 BLOCKED: {critical} critical + {high} high issues must be fixed{C.END}")
            return False
        print(f"\n   {C.GREEN}✅ Quality gate passed!{C.END}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Code Review — Standard El-Joumla ERP")
    parser.add_argument("--staged", action="store_true", help="Review only staged files")
    parser.add_argument("--fix", action="store_true", help="Auto-fix what's possible")
    parser.add_argument("--security", action="store_true", help="Security scan only")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    reviewer = CodeReviewer()
    passed = reviewer.run_review(staged_only=args.staged)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()