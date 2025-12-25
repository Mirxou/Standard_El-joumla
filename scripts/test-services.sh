#!/bin/bash
# Services Test Script
# اختبار جميع الخدمات

set -e

echo "🧪 اختبار الخدمات..."
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

# Test Python imports
echo "1️⃣ اختبار استيراد الوحدات Python..."
python -c "
import sys
sys.path.insert(0, '.')

# Test core modules
try:
    from src.core.database_manager import DatabaseManager
    print('✅ DatabaseManager')
except Exception as e:
    print(f'❌ DatabaseManager: {e}')
    sys.exit(1)

try:
    from src.services.compliance_service import ComplianceService
    print('✅ ComplianceService')
except Exception as e:
    print(f'❌ ComplianceService: {e}')
    sys.exit(1)

try:
    from src.services.sso_service import SSOService
    print('✅ SSOService')
except Exception as e:
    print(f'❌ SSOService: {e}')
    sys.exit(1)

try:
    from src.core.security_monitor import SecurityMonitor
    print('✅ SecurityMonitor')
except Exception as e:
    print(f'❌ SecurityMonitor: {e}')
    sys.exit(1)

try:
    from src.core.intrusion_detection import IntrusionDetectionSystem
    print('✅ IntrusionDetectionSystem')
except Exception as e:
    print(f'❌ IntrusionDetectionSystem: {e}')
    sys.exit(1)

try:
    from src.services.security_reports_service import SecurityReportsService
    print('✅ SecurityReportsService')
except Exception as e:
    print(f'❌ SecurityReportsService: {e}')
    sys.exit(1)

print('✅ جميع الوحدات قابلة للاستيراد')
" && print_test 0 "Python Modules" || print_test 1 "Python Modules"

# Test database initialization
echo ""
echo "2️⃣ اختبار تهيئة قاعدة البيانات..."
python -c "
import sys
sys.path.insert(0, '.')
from src.core.database_manager import DatabaseManager

db = DatabaseManager(':memory:')
if db.initialize():
    print('✅ Database initialization')
    sys.exit(0)
else:
    print('❌ Database initialization failed')
    sys.exit(1)
" && print_test 0 "Database Initialization" || print_test 1 "Database Initialization"

# Test services initialization
echo ""
echo "3️⃣ اختبار تهيئة الخدمات..."
python -c "
import sys
sys.path.insert(0, '.')
from src.core.database_manager import DatabaseManager

db = DatabaseManager(':memory:')
db.initialize()

# Test ComplianceService
from src.services.compliance_service import ComplianceService
compliance = ComplianceService(db)
print('✅ ComplianceService initialized')

# Test SSOService
from src.services.sso_service import SSOService
sso = SSOService(db)
print('✅ SSOService initialized')

# Test SecurityMonitor
from src.core.security_monitor import SecurityMonitor
monitor = SecurityMonitor(db)
print('✅ SecurityMonitor initialized')

# Test IntrusionDetectionSystem
from src.core.intrusion_detection import IntrusionDetectionSystem
ids = IntrusionDetectionSystem(db)
print('✅ IntrusionDetectionSystem initialized')

print('✅ جميع الخدمات قابلة للتهيئة')
" && print_test 0 "Services Initialization" || print_test 1 "Services Initialization"

# Summary
echo ""
echo "════════════════════════════════════════"
echo "📊 ملخص اختبارات الخدمات:"
echo "   ✅ نجحت: $TESTS_PASSED"
echo "   ❌ فشلت: $TESTS_FAILED"
echo "════════════════════════════════════════"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 جميع اختبارات الخدمات نجحت!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️ بعض الاختبارات فشلت.${NC}"
    exit 1
fi

