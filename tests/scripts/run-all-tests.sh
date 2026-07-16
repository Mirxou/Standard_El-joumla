#!/bin/bash
# Run All Tests Script
# تشغيل جميع الاختبارات

set -e

echo "🧪 تشغيل جميع الاختبارات..."
echo "════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_PASSED=0
TOTAL_FAILED=0

# 1. Services Tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1️⃣ اختبار الخدمات (Services Tests)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if bash scripts/test-services.sh; then
    ((TOTAL_PASSED++))
else
    ((TOTAL_FAILED++))
fi

echo ""
echo ""

# 2. Docker Tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2️⃣ اختبار Docker Setup${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if bash scripts/test-docker.sh; then
    ((TOTAL_PASSED++))
else
    ((TOTAL_FAILED++))
fi

echo ""
echo ""

# 3. API Tests (if API is running)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3️⃣ اختبار REST API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if curl -s http://localhost:8000/health &> /dev/null; then
    if bash scripts/test-api.sh; then
        ((TOTAL_PASSED++))
    else
        ((TOTAL_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️ API غير يعمل حالياً. تخطي اختبارات API.${NC}"
    echo "   لتشغيل API: docker-compose up api"
fi

echo ""
echo ""

# Final Summary
echo "════════════════════════════════════════"
echo -e "${BLUE}📊 الملخص النهائي:${NC}"
echo "════════════════════════════════════════"
echo "   ✅ نجحت: $TOTAL_PASSED"
echo "   ❌ فشلت: $TOTAL_FAILED"
echo "════════════════════════════════════════"

if [ $TOTAL_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 جميع الاختبارات نجحت! النظام جاهز!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.${NC}"
    exit 1
fi

