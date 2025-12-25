/**
 * مركز التكوين الموحد للـ API - Mobile App
 * منع تكرار URLs وتوحيد جميع الإعدادات
 * 
 * ملاحظة: React Native لا يدعم process.env مباشرة
 * يجب استخدام react-native-config أو Config من expo-constants
 * 
 * للاستخدام مع react-native-config:
 * 1. npm install react-native-config
 * 2. إنشاء ملف .env في مجلد mobile/
 * 3. إضافة API_BASE_URL=http://localhost:8000
 * 4. استخدام: import Config from 'react-native-config';
 *              const API_BASE_URL = Config.API_BASE_URL || 'http://localhost:8000';
 */

// حالياً نستخدم قيمة افتراضية
// TODO: إضافة دعم react-native-config أو expo-constants لاحقاً
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000'  // Development
  : 'https://your-api-domain.com';  // Production - يجب تحديثه

export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/api/v1/auth/login',
      LOGOUT: '/api/v1/auth/logout',
      REFRESH: '/api/v1/auth/refresh',
      COMPANIES: '/api/v1/auth/companies',
      ME: '/api/v1/auth/me',
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
    
    // Purchases
    PURCHASES: '/api/v1/purchases',
    
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

