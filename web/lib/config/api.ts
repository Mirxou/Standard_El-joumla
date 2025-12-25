/**
 * مركز التكوين الموحد للـ API
 * منع تكرار URLs وتوحيد جميع الإعدادات
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/api/v1/auth/login',
      LOGOUT: '/api/v1/auth/logout',
      REFRESH: '/api/v1/auth/refresh',
      COMPANIES: '/api/v1/auth/companies',
    },
    
    // Products
    PRODUCTS: '/api/v1/products',
    CATEGORIES: '/api/v1/categories',
    
    // Sales
    SALES: '/api/v1/sales',
    SALES_INVOICE: '/api/v1/sales/invoice',
    
    // Inventory
    INVENTORY: '/api/v1/inventory',
    
    // Warehouse
    WAREHOUSE: '/api/v1/warehouses',
    
    // Dashboard
    DASHBOARD: {
      STATS: '/api/v1/dashboard/stats',
      SALES: '/api/v1/dashboard/sales',
    },
    
    // Suppliers
    SUPPLIERS: '/api/v1/suppliers',
    
    // Users
    USERS: '/api/v1/users',
  },

  TIMEOUTS: {
    DEFAULT: 10000,        // 10 ثوان
    UPLOAD: 30000,         // 30 ثانية للـ uploads
    LONG_OPERATION: 60000, // دقيقة للعمليات الطويلة
  },

  RETRY: {
    MAX_ATTEMPTS: 3,
    DELAY_MS: 1000,
    BACKOFF_MULTIPLIER: 2,
  },

  HEADERS: {
    CONTENT_TYPE: 'Content-Type',
    COMPANY_ID: 'X-Company-ID',
    AUTHORIZATION: 'Authorization',
  },
};

/**
 * بناء رابط كامل من endpoint
 */
export const getFullURL = (endpoint: string): string => {
  if (endpoint.startsWith('http')) return endpoint;
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

/**
 * الحصول على headers الافتراضية
 */
export const getDefaultHeaders = (token?: string, companyId?: string): HeadersInit => {
  const headers: Record<string, string> = {
    [API_CONFIG.HEADERS.CONTENT_TYPE]: 'application/json',
  };

  if (token) {
    headers[API_CONFIG.HEADERS.AUTHORIZATION] = `Bearer ${token}`;
  }

  if (companyId) {
    headers[API_CONFIG.HEADERS.COMPANY_ID] = companyId;
  }

  return headers;
};
