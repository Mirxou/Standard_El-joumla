// web/lib/db/client.ts

// إعداد رابط الـ API (يقرأ من .env.local أو يستخدم الافتراضي)
// ملاحظة: هذا الملف للتوافقية مع الكود القديم فقط
// يُنصح باستخدام apiClient من @/lib/api/client بدلاً من هذا الملف
import { API_CONFIG } from '@/lib/config/api'
import { logger } from '@/lib/utils/logger'

const API_BASE_URL = API_CONFIG.BASE_URL;

/**
 * دالة موحدة لجلب وإرسال البيانات من Python API
 * @param endpoint المسار (مثال: '/products')
 * @param options خيارات إضافية (المنهج، الجسم، إلخ)
 */
export async function fetchFromAPI(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE',
    body?: any
  } = {}
) {
  const { method = 'GET', body = null } = options;

  try {
    // إضافة بادئة /api/v1 إذا لم تكن موجودة
    let path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    if (!path.startsWith('/api/v1')) {
      path = `/api/v1${path}`;
    }
    const url = `${API_BASE_URL}${path}`;

    logger.debug(`${method}: ${url}`);

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const companyId = typeof window !== 'undefined' ? localStorage.getItem('company_id') : null;

    const requestOptions: RequestInit = {
      method,
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(companyId ? { 'X-Company-ID': companyId } : {}),
      },
    };

    if (body && method !== 'GET') {
      requestOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url, requestOptions);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(`API Error ${response.status}: ${errorData.detail || response.statusText}`);
      return method === 'GET' ? [] : { error: errorData.detail || response.statusText };
    }

    // لعمليات الحذف أو الاستجابات الفارغة
    if (response.status === 204) return { success: true };

    return await response.json();
  } catch (error: any) {
    console.error(`❌ Failed to ${method} from API:`, error);
    return method === 'GET' ? [] : { error: error.message || "فشل الاتصال بالخادم" };
  }
}

// --- توافقية مع الكود القديم (Mocking) ---
// هذه الدوال موجودة فقط لمنع انهيار الصفحات التي لا تزال تستخدم SQL القديم
// سنقوم باستبدالها تدريجياً
export const sql = async (strings: TemplateStringsArray | string, ...values: any[]) => {
  console.warn("⚠️ Warning: Old SQL method called. Please use fetchFromAPI instead.");
  return [];
};

export const db = {
  select: () => ({ from: () => [] }),
};