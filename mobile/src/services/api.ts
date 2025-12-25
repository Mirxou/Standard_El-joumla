import axios, {AxiosInstance, AxiosError, AxiosRequestConfig} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {offlineStorage, OfflineAction} from './offlineStorage';
import { API_CONFIG } from '../config/api';

// إنشاء Axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor لإضافة Token
api.interceptors.request.use(
  async config => {
    const token = await AsyncStorage.getItem('@access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  },
);

// Response interceptor للتعامل مع الأخطاء
api.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token منتهي، محاولة تحديثه
      const refreshToken = await AsyncStorage.getItem('@refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AUTH.REFRESH}`, {
            refresh_token: refreshToken,
          });
          const newToken = response.data.access_token;
          await AsyncStorage.setItem('@access_token', newToken);
          // إعادة المحاولة
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${newToken}`;
            return api.request(error.config);
          }
        } catch (refreshError) {
          // فشل التحديث، تسجيل الخروج
          await AsyncStorage.multiRemove([
            '@access_token',
            '@refresh_token',
            '@user',
          ]);
        }
      }
    }
    return Promise.reject(error);
  },
);

// API Services
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await api.post(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {username, password});
    return response.data;
  },
  getMe: async () => {
    const response = await api.get(API_CONFIG.ENDPOINTS.AUTH.ME);
    return response.data;
  },
  refreshToken: async (refreshToken: string) => {
    const response = await api.post(API_CONFIG.ENDPOINTS.AUTH.REFRESH, {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};

export const productsApi = {
  getAll: async (params?: any) => {
    const response = await api.get(API_CONFIG.ENDPOINTS.PRODUCTS, {params});
    return response.data;
  },
  getById: async (id: number) => {
    const response = await api.get(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`);
    return response.data;
  },
  create: async (data: any) => {
    const response = await api.post(API_CONFIG.ENDPOINTS.PRODUCTS, data);
    return response.data;
  },
  update: async (id: number, data: any) => {
    const response = await api.put(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`);
  },
};

export const salesApi = {
  getAll: async (params?: any) => {
    const response = await api.get(API_CONFIG.ENDPOINTS.SALES, {params});
    return response.data;
  },
  getById: async (id: number) => {
    const response = await api.get(`${API_CONFIG.ENDPOINTS.SALES}/${id}`);
    return response.data;
  },
  create: async (data: any) => {
    const response = await api.post(API_CONFIG.ENDPOINTS.SALES, data);
    return response.data;
  },
  update: async (id: number, data: any) => {
    const response = await api.put(`${API_CONFIG.ENDPOINTS.SALES}/${id}`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`${API_CONFIG.ENDPOINTS.SALES}/${id}`);
  },
};

export const purchasesApi = {
  getAll: async (params?: any) => {
    const response = await api.get(API_CONFIG.ENDPOINTS.PURCHASES, {params});
    return response.data;
  },
  getById: async (id: number) => {
    const response = await api.get(`${API_CONFIG.ENDPOINTS.PURCHASES}/${id}`);
    return response.data;
  },
  create: async (data: any) => {
    const response = await api.post(API_CONFIG.ENDPOINTS.PURCHASES, data);
    return response.data;
  },
  update: async (id: number, data: any) => {
    const response = await api.put(`${API_CONFIG.ENDPOINTS.PURCHASES}/${id}`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`${API_CONFIG.ENDPOINTS.PURCHASES}/${id}`);
  },
};

export default api;

