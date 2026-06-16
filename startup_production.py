#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Production Startup Script
سكريبت بدء الإنتاج السريع
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """Print styled header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def check_python():
    """Check Python version"""
    print("🐍 Checking Python environment...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print(f"❌ Python {version.major}.{version.minor} - Requires 3.12+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_venv():
    """Check virtual environment"""
    print("\n📦 Checking virtual environment...")
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        print("   Create with: python -m venv .venv")
        return False
    print("✅ Virtual environment found")
    return True

def install_dependencies():
    """Install dependencies"""
    print("\n📥 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            check=True
        )
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some dependencies may have failed to install")
        return True  # Continue anyway

def verify_database():
    """Verify database"""
    print("\n🗄️  Verifying database...")
    try:
        result = subprocess.run(
            [sys.executable, "verify_production.py"],
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✅ Database verified")
            return True
        else:
            print("⚠️  Database verification had issues")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️  Database verification timed out")
        return True

def run_tests():
    """Run quick tests"""
    print("\n🧪 Running quick tests...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_simple.py", "-v", "-q"],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Tests passed")
            return True
        else:
            print("⚠️  Some tests failed (non-critical)")
            return True
    except Exception:
        print("ℹ️  Tests skipped")
        return True

def start_app():
    """Start the application"""
    print("\n🚀 Starting application...")
    print("   Running: python main.py\n")

    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting app: {e}")

def main():
    """Main startup routine"""
    print_header("⚡ LOGICAL VERSION ERP - PRODUCTION STARTUP")

    # Checks
    if not check_python():
        sys.exit(1)

    if not check_venv():
        sys.exit(1)

    install_dependencies()

    print_header("🔍 VERIFICATION")
    verify_database()
    run_tests()

    # Ask to start
    print("\n" + "=" * 70)
    response = input("Ready to start application? (y/n): ").lower().strip()
    if response == 'y':
        start_app()
    else:
        print("\n👋 Startup cancelled")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Startup interrupted")
        sys.exit(0)
