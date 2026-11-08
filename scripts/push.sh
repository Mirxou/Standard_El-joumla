#!/bin/bash
# سكربت الرفع الآمن إلى GitHub — التوكن لا يُحفظ في أي ملف
# Usage: ./scripts/push.sh <GITHUB_PAT>
if [ -z "$1" ]; then
  echo "Usage: $0 <GITHUB_PERSONAL_ACCESS_TOKEN>"
  echo "التوكن يُستخدم مرة واحدة ولا يُحفظ في config أو سجلات."
  exit 1
fi
cd "$(dirname "$0")/.."
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push "https://x-access-token:$1@github.com/Mirxou/Standard_El-joumla.git" "$BRANCH"
RC=$?
if [ $RC -eq 0 ]; then
  echo "✅ تم الرفع بنجاح — الفرع: $BRANCH"
else
  echo "❌ فشل الرفع (كود $RC) — تحقق من صلاحية التوكن (يحتاج repo scope)"
fi
exit $RC
