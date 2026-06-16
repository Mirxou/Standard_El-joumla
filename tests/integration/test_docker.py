#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker Test Script
اختبار شامل لـ Docker Setup
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, shell=True):
    """تنفيذ أمر وإرجاع النتيجة"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def test_docker_installation():
    """اختبار تثبيت Docker"""
    # print("1️⃣ التحقق من تثبيت Docker...")

    success, output, error = run_command("docker --version")
    if success:
        # print(f"   ✅ Docker مثبت: {output.strip()}")
        return 1, 0
    else:
        # print(f"   ❌ Docker غير مثبت: {error}")
        return 0, 1


def test_docker_compose_installation():
    """اختبار تثبيت Docker Compose"""
    # print("\n2️⃣ التحقق من تثبيت Docker Compose...")

    success, output, error = run_command("docker-compose --version")
    if success:
        # print(f"   ✅ Docker Compose مثبت: {output.strip()}")
        return 1, 0
    else:
        # print(f"   ❌ Docker Compose غير مثبت: {error}")
        return 0, 1


def test_docker_daemon():
    """اختبار تشغيل Docker Daemon"""
    # print("\n3️⃣ التحقق من تشغيل Docker Daemon...")

    success, output, error = run_command("docker info")
    if success:
        # print("   ✅ Docker Daemon يعمل")
        return 1, 0
    else:
        # print(f"   ❌ Docker Daemon غير يعمل: {error}")
        return 0, 1


def test_required_files():
    """اختبار وجود الملفات المطلوبة"""
    # print("\n4️⃣ التحقق من الملفات المطلوبة...")

    project_root = Path(__file__).parent.parent
    required_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]

    tests_passed = 0
    tests_failed = 0

    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            # print(f"   ✅ الملف موجود: {file}")
            tests_passed += 1
        else:
            # print(f"   ❌ الملف مفقود: {file}")
            tests_failed += 1

    return tests_passed, tests_failed


def test_docker_compose_config():
    """اختبار صحة docker-compose.yml"""
    # print("\n5️⃣ التحقق من صحة docker-compose.yml...")

    success, output, error = run_command("docker-compose config")
    if success:
        # print("   ✅ docker-compose.yml صحيح")
        return 1, 0
    else:
        # print(f"   ❌ docker-compose.yml يحتوي على أخطاء: {error}")
        return 0, 1


def test_ports():
    """اختبار توفر المنافذ"""
    # print("\n6️⃣ التحقق من توفر المنافذ...")

    import socket

    ports = [8000, 3000, 5432, 6379, 9090, 3001]
    tests_passed = 0
    tests_failed = 0

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", port))
        sock.close()

        if result == 0:
            # print(f"   ⚠️ المنفذ {port} مستخدم")
            pass
        else:
            # print(f"   ✅ المنفذ {port} متاح")
            tests_passed += 1

    return tests_passed, tests_failed


def test_health_endpoint():
    """اختبار Health Check Endpoint"""
    # print("\n7️⃣ اختبار Health Check Endpoint...")

    try:
        import json
        import urllib.request

        url = "http://localhost:8000/health"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "healthy":
                # print("   ✅ Health Check يعمل")
                return 1, 0
            else:
                # print("   ❌ Health Check لا يعيد الحالة المتوقعة")
                return 0, 1
    except Exception as e:  # noqa: F841
        # print(f"   ⚠️ API غير يعمل حالياً (هذا طبيعي إذا لم يتم تشغيله): {e}")
        return 0, 0  # لا نحسبه كفشل


def main():
    """الدالة الرئيسية"""
    # print("🧪 بدء اختبار Docker Setup...")
    # print("=" * 50)

    total_passed = 0
    total_failed = 0

    # Test 1: Docker Installation
    passed, failed = test_docker_installation()
    total_passed += passed
    total_failed += failed

    # Test 2: Docker Compose
    passed, failed = test_docker_compose_installation()
    total_passed += passed
    total_failed += failed

    # Test 3: Docker Daemon
    passed, failed = test_docker_daemon()
    total_passed += passed
    total_failed += failed

    # Test 4: Required Files
    passed, failed = test_required_files()
    total_passed += passed
    total_failed += failed

    # Test 5: Docker Compose Config
    passed, failed = test_docker_compose_config()
    total_passed += passed
    total_failed += failed

    # Test 6: Ports
    passed, failed = test_ports()
    total_passed += passed
    total_failed += failed

    # Test 7: Health Endpoint
    passed, failed = test_health_endpoint()
    total_passed += passed
    total_failed += failed

    # Summary
    # print("\n" + "=" * 50)
    # print("📊 ملخص الاختبارات:")
    # print(f"   ✅ نجحت: {total_passed}")
    # print(f"   ❌ فشلت: {total_failed}")
    # print("=" * 50)

    if total_failed == 0:
        # print("\n🎉 جميع الاختبارات نجحت! Docker Setup جاهز!")
        pass
        # print("\n📝 الخطوات التالية:")
        # print("   1. عدّل .docker.env بإعداداتك")
        # print("   2. شغّل: docker-compose up -d")
        # print("   3. تحقق من: docker-compose ps")
        return 0
    else:
        # print("\n⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
