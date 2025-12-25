/**
 * @deprecated هذا الملف للتوافقية مع الكود القديم فقط
 * 
 * ⚠️ تحذير: هذا Supabase Shim مخصص للتوافقية فقط
 * يُنصح بشدة باستخدام apiClient من @/lib/api/client بدلاً من هذا الملف
 * 
 * This is a shim to replace the real Supabase client with one that talks to our Python API
 * This allows us to reuse the existing UI code without rewriting it all.
 * 
 * ملاحظة: تم استبدال جميع استخدامات supabase في API routes
 * هذا الملف موجود فقط للتوافقية مع الكود القديم
 */

import { API_CONFIG } from '@/lib/config/api'

const API_URL = API_CONFIG.BASE_URL;

class SupabaseShim {

  constructor() { }

  from(table: string) {
    return {
      select: (columns: string = '*') => {
        const promise = this._fetch(table);
        return new PostgrestFilterBuilder(promise);
      },

      insert: (payload: any) => {
        const promise = this._fetchWithMethod(table, 'POST', payload);
        return new PostgrestFilterBuilder(promise);
      },

      update: (payload: any) => {
        return new PostgrestFilterBuilder(null, 'update', table, payload, this);
      },

      delete: () => {
        return new PostgrestFilterBuilder(null, 'delete', table, null, this);
      }
    };
  }

  async _fetch(table: string) {
    return this._fetchWithMethod(table, 'GET');
  }

  async _fetchWithMethod(table: string, method: string, payload: any = null) {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      };

      if (payload && method !== 'GET') {
        options.body = JSON.stringify(payload);
      }

      // إضافة بادئة API_PREFIX (عادة /api/v1/)
      const endpoint = `${API_URL}/api/v1/${table}`;
      const res = await fetch(endpoint, options);

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${res.statusText}`);
      }

      let data = await res.json();

      // Supabase عادة ما يعيد مصفوفة عند الإدراج. 
      // الـ API الخاص بنا قد يعيد كائناً واحداً أو معرفاً.
      if (method === 'POST' && data && !Array.isArray(data)) {
        data = [data];
      }

      return { data: data, error: null };
    } catch (err: any) {
      console.error(`API Shim Error (${method} ${table}):`, err);
      // في حالة GET، نعيد مصفوفة فارغة لتجنب أخطاء .map() في الواجهة
      return { data: method === 'GET' ? [] : null, error: err.message || err };
    }
  }

  // يتم استدعاؤه من PostgrestFilterBuilder للعمليات التي تحتاج فلتر (update/delete)
  async _executeMutation(action: string, table: string, payload: any, filters: { column: string, value: any }[]) {
    console.log(`[Shim] Executing ${action} on ${table} with filters:`, filters);

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    let url = `${API_URL}/api/v1/${table}`;
    const idFilter = filters.find(f => f.column === 'id');

    if (idFilter) {
      url = `${API_URL}/api/v1/${table}/${idFilter.value}`;
    }

    const method = action === 'update' ? 'PUT' : 'DELETE';

    try {
      const options: RequestInit = {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
      };

      if (payload && method === 'PUT') {
        options.body = JSON.stringify(payload);
      }

      const res = await fetch(url, options);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${res.statusText}`);
      }

      // حذف: Supabase يعيد null أو البيانات المحذوفة. 
      // تحديث: يعيد البيانات المحدثة (عادة كمصفوفة في Supabase)
      let data = action === 'delete' ? null : await res.json();
      if (action === 'update' && data && !Array.isArray(data)) {
        data = [data];
      }

      return { data, error: null };
    } catch (err: any) {
      console.error(`API Mutation Error (${method} ${url}):`, err);
      return { data: null, error: err.message || err };
    }
  }

  async _mockAction(action: string, table: string, payload: any) {
    // تم استبدال المحاكاة بـ _fetchWithMethod و _executeMutation
    return this._fetchWithMethod(table, action === 'insert' ? 'POST' : 'GET', payload);
  }
}

class PostgrestFilterBuilder implements PromiseLike<{ data: any; error: any }> {
  private _promise: Promise<{ data: any; error: any }> | null;
  private _filters: { column: string, value: any }[] = [];

  constructor(
    promise: Promise<{ data: any; error: any }> | null,
    private _pendingAction?: string,
    private _table?: string,
    private _payload?: any,
    private _client?: SupabaseShim
  ) {
    this._promise = promise;
  }

  then<TResult1 = { data: any; error: any }, TResult2 = never>(
    onfulfilled?: ((value: { data: any; error: any }) => TResult1 | PromiseLike<TResult1>) | null,
    onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null
  ): PromiseLike<TResult1 | TResult2> {
    if (!this._promise) {
      if (this._pendingAction && this._client && this._table) {
        this._promise = this._client._executeMutation(this._pendingAction, this._table, this._payload, this._filters);
      } else {
        this._promise = Promise.resolve({ data: null, error: null });
      }
    }
    return this._promise.then(onfulfilled, onrejected);
  }

  select(columns?: string): this {
    return this;
  }

  single(): any {
    if (this._promise) {
      this._promise = this._promise.then((res: any) => {
        if (res.data && Array.isArray(res.data)) {
          return { ...res, data: res.data[0] || null };
        }
        return res;
      });
    }
    return this;
  }

  order(column: string, { ascending }: { ascending: boolean } = { ascending: true }): this {
    return this;
  }

  limit(count: number): this {
    return this;
  }

  eq(column: string, value: any): this {
    this._filters.push({ column, value });
    return this;
  }

  neq(column: string, value: any): this { return this; }
  gt(column: string, value: any): this { return this; }
  gte(column: string, value: any): this { return this; }
  lt(column: string, value: any): this { return this; }
  lte(column: string, value: any): this { return this; }
  is(column: string, value: any): this { return this; }
  in(column: string, value: any[]): this { return this; }
  like(column: string, pattern: string): this { return this; }
  ilike(column: string, pattern: string): this { return this; }
  contains(column: string, value: any): this { return this; }
  range(from: number, to: number): this { return this; }
}

export const supabase = new SupabaseShim();
