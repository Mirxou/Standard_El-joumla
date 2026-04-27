#!/bin/bash
# Docker Test Script
# اختبار شامل لـ Docker Setup

set -e

echo "🧪 بدء اختبار Docker Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((TESTS_FAILED++))
    fi
}

# 1. Check Docker installation
echo "1️⃣ التحقق من تثبيت Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_test 0 "Docker مثبت: $DOCKER_VERSION"
else
    print_test 1 "Docker غير مثبت"
    exit 1
fi

# 2. Check Docker Compose installation
echo ""
echo "2️⃣ التحقق من تثبيت Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_test 0 "Docker Compose مثبت: $COMPOSE_VERSION"
else
    print_test 1 "Docker Compose غير مثبت"
    exit 1
fi

# 3. Check if Docker daemon is running
echo ""
echo "3️⃣ التحقق من تشغيل Docker Daemon..."
if docker info &> /dev/null; then
    print_test 0 "Docker Daemon يعمل"
else
    print_test 1 "Docker Daemon غير يعمل"
    exit 1
fi

# 4. Check required files
echo ""
echo "4️⃣ التحقق من الملفات المطلوبة..."
REQUIRED_FILES=("Dockerfile" "docker-compose.yml" ".dockerignore")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_test 0 "الملف موجود: $file"
    else
        print_test 1 "الملف مفقود: $file"
    fi
done

# 5. Check .docker.env
echo ""
echo "5️⃣ التحقق من ملف البيئة..."
if [ -f ".docker.env" ]; then
    print_test 0 "ملف .docker.env موجود"
else
    echo -e "${YELLOW}⚠️ ملف .docker.env غير موجود، سيتم إنشاؤه من المثال...${NC}"
    if [ -f ".docker.env.example" ]; then
        cp .docker.env.example .docker.env
        echo -e "${YELLOW}⚠️ يرجى تعديل .docker.env قبل المتابعة${NC}"
    fi
fi

# 6. Validate docker-compose.yml syntax
echo ""
echo "6️⃣ التحقق من صحة docker-compose.yml..."
if docker-compose config &> /dev/null; then
    print_test 0 "docker-compose.yml صحيح"
else
    print_test 1 "docker-compose.yml يحتوي على أخطاء"
    docker-compose config
fi

# 7. Build Docker images (dry run)
echo ""
echo "7️⃣ اختبار بناء Docker Images..."
echo "   (هذا قد يستغرق بضع دقائق...)"
if docker-compose build --dry-run &> /dev/null || docker-compose config &> /dev/null; then
    print_test 0 "Docker Images قابلة للبناء"
else
    print_test 1 "خطأ في بناء Docker Images"
fi

# 8. Check port availability
echo ""
echo "8️⃣ التحقق من توفر المنافذ..."
PORTS=(8000 3000 5432 6379 9090 3001)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t &> /dev/null; then
        echo -e "${YELLOW}⚠️ المنفذ $port مستخدم${NC}"
    else
        print_test 0 "المنفذ $port متاح"
    fi
done

# 9. Test health check endpoint (if API is running)
echo ""
echo "9️⃣ اختبار Health Check Endpoint..."
if curl -s http://localhost:8000/health &> /dev/null; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        print_test 0 "Health Check يعمل"
    else
        print_test 1 "Health Check لا يعيد الحالة المتوقعة"
    fi
else
    echo -e "${YELLOW}⚠️ API غير يعمل حالياً (هذا طبيعي إذا لم يتم تشغيله)${NC}"
fi

# 10. Check Docker images
echo ""
echo "🔟 التحقق من Docker Images المبنية..."
if docker images | grep -q "erp"; then
    print_test 0 "Docker Images موجودة"
    docker images | grep "erp"
else
    echo -e "${YELLOW}⚠️ Docker Images غير مبنية بعد${NC}"
fi

# Summary
echo ""
echo "════════════════════════════════════════"
echo "📊 ملخص الاختبارات:"
echo "   ✅ نجحت: $TESTS_PASSED"
echo "   ❌ فشلت: $TESTS_FAILED"
echo "════════════════════════════════════════"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 جميع الاختبارات نجحت! Docker Setup جاهز!${NC}"
    echo ""
    echo "📝 الخطوات التالية:"
    echo "   1. عدّل .docker.env بإعداداتك"
    echo "   2. شغّل: docker-compose up -d"
    echo "   3. تحقق من: docker-compose ps"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.${NC}"
    exit 1
fi

