#!/bin/bash
# API Test Script
# اختبار شامل لـ REST API

set -e

API_URL=${1:-"http://localhost:8000"}
echo "🧪 اختبار REST API على: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((TESTS_FAILED++))
    fi
}

# 1. Health Check
echo "1️⃣ اختبار Health Check..."
HEALTH_RESPONSE=$(curl -s "$API_URL/health" || echo "ERROR")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_test 0 "Health Check"
    echo "   Response: $HEALTH_RESPONSE"
else
    print_test 1 "Health Check فشل"
fi

# 2. API Health Check
echo ""
echo "2️⃣ اختبار API Health Check..."
API_HEALTH=$(curl -s "$API_URL/api/v1/health" || echo "ERROR")
if echo "$API_HEALTH" | grep -q "healthy"; then
    print_test 0 "API Health Check"
    echo "   Response: $API_HEALTH"
else
    print_test 1 "API Health Check فشل"
fi

# 3. OpenAPI Documentation
echo ""
echo "3️⃣ اختبار OpenAPI Documentation..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$DOCS_RESPONSE" == "200" ]; then
    print_test 0 "Swagger UI متاح"
else
    print_test 1 "Swagger UI غير متاح (HTTP $DOCS_RESPONSE)"
fi

# 4. OpenAPI JSON
echo ""
echo "4️⃣ اختبار OpenAPI JSON..."
OPENAPI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/openapi.json")
if [ "$OPENAPI_RESPONSE" == "200" ]; then
    print_test 0 "OpenAPI JSON متاح"
else
    print_test 1 "OpenAPI JSON غير متاح (HTTP $OPENAPI_RESPONSE)"
fi

# 5. Login Endpoint (without credentials - should fail gracefully)
echo ""
echo "5️⃣ اختبار Login Endpoint..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' || echo "ERROR")
if echo "$LOGIN_RESPONSE" | grep -q "error\|detail\|401\|422"; then
    print_test 0 "Login Endpoint يستجيب (فشل متوقع)"
else
    print_test 1 "Login Endpoint لا يستجيب بشكل صحيح"
fi

# 6. Rate Limiting Test
echo ""
echo "6️⃣ اختبار Rate Limiting..."
RATE_LIMIT_TEST=0
for i in {1..10}; do
    RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/auth/login" \
        -X POST -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}')
    if [ "$RESPONSE_CODE" == "429" ]; then
        RATE_LIMIT_TEST=1
        break
    fi
    sleep 0.1
done
if [ $RATE_LIMIT_TEST -eq 1 ]; then
    print_test 0 "Rate Limiting يعمل"
else
    echo -e "${YELLOW}⚠️ Rate Limiting لم يتم تفعيله بعد${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════"
echo "📊 ملخص اختبارات API:"
echo "   ✅ نجحت: $TESTS_PASSED"
echo "   ❌ فشلت: $TESTS_FAILED"
echo "════════════════════════════════════════"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 جميع اختبارات API نجحت!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ بعض الاختبارات فشلت.${NC}"
    exit 1
fi

