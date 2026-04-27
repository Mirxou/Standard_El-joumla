/**
 * عميل API مركزي موحد
 * يتعامل مع:
 * - Token management (supports both cookies and localStorage)
 * - Error handling
 * - Retry logic
 * - Request interceptors
 * - Global error toast notifications
 */

import { API_CONFIG, getDefaultHeaders, getFullURL } from '@/lib/config/api';
import { APIError } from '@/lib/types';
import { toast } from 'sonner';

/**
 * Helper function to get a cookie value by name
 */
function getCookie(name: string): string | null {
  if (typeof window === 'undefined') return null;
  
  const matches = document.cookie.match(new RegExp(
    '(?:^|;)\\s*' + name + '=([^;]*)(?:;|$)'
  ));
  
  return matches ? decodeURIComponent(matches[1]) : null;
}

/**
 * Helper function to set a cookie
 */
function setCookie(name: string, value: string, days: number = 1): void {
  if (typeof window === 'undefined') return;
  
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires.toUTCString()};path=/`;
}

/**
 * Helper function to delete a cookie
 */
function deleteCookie(name: string): void {
  if (typeof window === 'undefined') return;
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

export class APIClient {
  private token: string | null = null;
  private companyId: string | null = null;
  private refreshTokenPromise: Promise<string | null> | null = null;
  private useCookies: boolean = false;

  constructor() {
    // Check backend environment to decide token storage method
    this.useCookies = process.env.NODE_ENV === 'production';
    this.loadCredentials();
  }

  /**
   * تحميل بيانات الاعتماد (من cookies أو localStorage)
   */
  private loadCredentials(): void {
    if (typeof window === 'undefined') return;
    
    // Try reading from HTTP-only cookie first in production
    // Note: We can't read HttpOnly cookies from JS, so fall back to localStorage for development
    // In production, the HttpOnly cookie is set by the server, not accessible to JS
    // So we use localStorage as fallback for the token value for API requests
    // The actual HttpOnly cookie is sent automatically by the browser with requests
    
    // Try localStorage first (works in both dev and prod as fallback)
    let token = localStorage.getItem('access_token');
    
    // If not in localStorage and we have a cookie (non-httpOnly), try to read it
    if (!token) {
      token = getCookie('access_token');
    }
    
    this.token = token;
    this.companyId = localStorage.getItem('company_id');
  }

  /**
   * تعيين التوكن (يُستدعى بعد تسجيل الدخول)
   */
  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      // في التطوير، نخزن في localStorage للتوافق
      // في الإنتاج، الـ HttpOnly cookie يُعيَّن من الـ Backend
      localStorage.setItem('access_token', token);
    }
  }

  /**
   * تعيين معرف الشركة الحالية
   */
  setCompanyId(companyId: string): void {
    this.companyId = companyId;
    if (typeof window !== 'undefined') {
      localStorage.setItem('company_id', companyId);
    }
  }

  /**
   * مسح بيانات الاعتماد (تسجيل خروج)
   */
  clearCredentials(): void {
    this.token = null;
    this.companyId = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('company_id');
      // Also clear cookies if they exist
      deleteCookie('access_token');
      deleteCookie('refresh_token');
    }
  }

  /**
   * محاولة تحديث التوكن
   */
  private async refreshToken(): Promise<string | null> {
    // تجنب عمليات refresh متزامنة
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    if (typeof window === 'undefined') {
      return null;
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return null;
    }

    this.refreshTokenPromise = this._performRefresh(refreshToken);
    const newToken = await this.refreshTokenPromise;
    this.refreshTokenPromise = null;

    return newToken;
  }

  /**
   * تنفيذ عملية refresh التوكن
   */
  private async _performRefresh(refreshToken: string): Promise<string | null> {
    try {
      const response = await fetch(
        getFullURL(API_CONFIG.ENDPOINTS.AUTH.REFRESH),
        {
          method: 'POST',
          headers: getDefaultHeaders(),
          body: JSON.stringify({ refresh_token: refreshToken }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        this.setToken(data.access_token);
        return data.access_token;
      }

      // إذا فشل refresh - حرّج المستخدم
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    } catch (error) {
      console.error('❌ Failed to refresh token:', error);
      return null;
    }
  }

  /**
   * الطلب الأساسي مع retry logic
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = API_CONFIG.RETRY.MAX_ATTEMPTS
  ): Promise<T> {
    const url = getFullURL(endpoint);
    const headers = new Headers(
      getDefaultHeaders(this.token || undefined, this.companyId || undefined)
    );

    // دمج headers الإضافية
    if (options.headers) {
      const additionalHeaders = new Headers(options.headers);
      additionalHeaders.forEach((value, key) => {
        headers.set(key, value);
      });
    }

    const requestOptions: RequestInit = {
      ...options,
      headers,
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUTS.DEFAULT),
    };

    try {
      const response = await fetch(url, requestOptions);

      // معالجة 401 - محاولة تحديث التوكن
      if (response.status === 401 && retries > 0) {
        const newToken = await this.refreshToken();
        if (newToken) {
          return this.request(endpoint, options, retries - 1);
        }
        // إذا فشل التحديث - إعادة محاولة مرة أخيرة
        if (retries > 1) {
          return this.request(endpoint, options, retries - 1);
        }
      }

      // معالجة الأخطاء
      if (!response.ok) {
        const error = await this._handleErrorResponse(response);
        throw error;
      }

      // معالجة الاستجابات الفارغة
      if (response.status === 204) {
        return { success: true } as T;
      }

      return await response.json();
    } catch (error) {
      // إعادة المحاولة في حالة أخطاء الشبكة
      if (retries > 0 && this._isRetryableError(error)) {
        const delay = API_CONFIG.RETRY.DELAY_MS * 
          Math.pow(API_CONFIG.RETRY.BACKOFF_MULTIPLIER, API_CONFIG.RETRY.MAX_ATTEMPTS - retries);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request(endpoint, options, retries - 1);
      }

      console.error(`❌ Request failed: ${url}`, error);
      
      // عرض toast notification للخطأ
      this._showErrorToast(error, endpoint);
      
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * معالجة استجابات الخطأ
   */
  private async _handleErrorResponse(response: Response): Promise<Error> {
    let errorData: APIError = {
      status: response.status,
    };

    try {
      errorData = await response.json();
    } catch {
      errorData.detail = response.statusText;
    }

    const message = errorData.detail || errorData.message || 'حدث خطأ غير متوقع';
    const error = new Error(message);
    (error as any).status = response.status;
    (error as any).data = errorData;

    return error;
  }

  /**
   * التحقق من أن الخطأ قابل للإعادة
   */
  private _isRetryableError(error: any): boolean {
    if (error instanceof TypeError) {
      // أخطاء الشبكة (Network errors)
      return error.message.includes('fetch') || error.message.includes('Failed to fetch');
    }
    // أخطاء timeout
    if (error.name === 'AbortError') {
      return true;
    }
    return false;
  }

  /**
   * عرض toast notification للخطأ
   */
  private _showErrorToast(error: any, endpoint: string): void {
    // تجاهل أخطاء المصادقة (401) - يتم التعامل معها بشكل خاص
    if (error?.status === 401) {
      return;
    }

    let errorMessage = 'حدث خطأ أثناء معالجة الطلب';
    let errorTitle = 'خطأ في الاتصال';

    // تحديد نوع الخطأ ورسالة مناسبة
    if (error?.status) {
      switch (error.status) {
        case 400:
          errorTitle = 'طلب غير صحيح';
          errorMessage = error?.data?.detail || error?.message || 'البيانات المرسلة غير صحيحة';
          break;
        case 403:
          errorTitle = 'غير مصرح';
          errorMessage = 'ليس لديك صلاحية للوصول إلى هذا المورد';
          break;
        case 404:
          errorTitle = 'غير موجود';
          errorMessage = 'المورد المطلوب غير موجود';
          break;
        case 408:
          errorTitle = 'انتهت مهلة الاتصال';
          errorMessage = 'انتهت مهلة الاتصال بالخادم. يرجى المحاولة مرة أخرى';
          break;
        case 409:
          errorTitle = 'تعارض';
          errorMessage = error?.data?.detail || error?.message || 'يوجد تعارض في البيانات';
          break;
        case 422:
          errorTitle = 'بيانات غير صحيحة';
          errorMessage = error?.data?.detail || error?.message || 'البيانات المرسلة غير صالحة';
          break;
        case 429:
          errorTitle = 'كثرة الطلبات';
          errorMessage = 'تم إرسال طلبات كثيرة جداً. يرجى الانتظار قليلاً';
          break;
        case 500:
          errorTitle = 'خطأ في الخادم';
          errorMessage = 'حدث خطأ داخلي في الخادم. يرجى المحاولة لاحقاً';
          break;
        case 502:
        case 503:
        case 504:
          errorTitle = 'الخادم غير متاح';
          errorMessage = 'الخادم غير متاح حالياً. يرجى المحاولة لاحقاً';
          break;
        default:
          errorTitle = `خطأ ${error.status}`;
          errorMessage = error?.data?.detail || error?.message || 'حدث خطأ غير متوقع';
      }
    } else if (error instanceof TypeError || error?.message?.includes('fetch') || error?.message?.includes('Failed to fetch')) {
      errorTitle = 'خطأ في الاتصال';
      errorMessage = 'لا يمكن الاتصال بالخادم. تأكد من اتصالك بالإنترنت';
    } else if (error?.name === 'AbortError') {
      errorTitle = 'انتهت مهلة الاتصال';
      errorMessage = 'انتهت مهلة الاتصال. يرجى المحاولة مرة أخرى';
    } else if (error?.message) {
      errorMessage = error.message;
    }

    // عرض toast notification
    toast.error(errorTitle, {
      description: errorMessage,
      duration: 5000,
    });
  }
}

// تصدير instance واحد من العميل (Singleton)
export const apiClient = new APIClient();
