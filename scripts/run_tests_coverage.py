#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مُشغل سريع للاختبارات مع التغطية و خيارات مبسطة.
Usage:
  python scripts/run_tests_coverage.py              # كل الاختبارات + تغطية نصية
  python scripts/run_tests_coverage.py --html       # إضافة تقرير HTML
  python scripts/run_tests_coverage.py --files tests/test_cache_service.py tests/test_password_strength.py
"""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run pytest with coverage helpers")
    parser.add_argument('--html', action='store_true', help='Include HTML coverage report')
    parser.add_argument('--files', nargs='*', help='Specific test files to run')
    args = parser.parse_args()

    base_cmd = [sys.executable, '-m', 'pytest', '--cov=src', '--cov-report=term-missing']
    if args.html:
        base_cmd.append('--cov-report=html')
    if args.files:
        base_cmd.extend(args.files)
    else:
        base_cmd.append('-q')

    print('Running:', ' '.join(base_cmd))
    result = subprocess.run(base_cmd)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
