/**
 * عميل API مركزي موحد
 * يتعامل مع:
 * - Token management
 * - Error handling
 * - Retry logic
 * - Request interceptors
 */

import { API_CONFIG, getDefaultHeaders, getFullURL } from '@/lib/config/api';
import { APIError } from '@/lib/types';

export class APIClient {
  private token: string | null = null;
  private companyId: string | null = null;
  private refreshTokenPromise: Promise<string | null> | null = null;

  constructor() {
    this.loadCredentials();
  }

  /**
   * تحميل بيانات الاعتماد من localStorage
   */
  private loadCredentials(): void {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
      this.companyId = localStorage.getItem('company_id');
    }
  }

  /**
   * تعيين التوكن (يُستدعى بعد تسجيل الدخول)
   */
  setToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
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
}

// تصدير instance واحد من العميل (Singleton)
export const apiClient = new APIClient();
