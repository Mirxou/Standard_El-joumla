import { apiClient } from "../client";
import { API_CONFIG } from "@/lib/config/api";

export interface Product {
    id: number;
    name: string;
    sku: string;
    description?: string;
    price: number;
    selling_price: number;
    stock: number;
    category_name?: string;
    image_path?: string;
    is_active: boolean;
}

export const productsService = {
    getAll: async (activeOnly = true) => {
        const queryString = activeOnly ? '?active_only=true' : '';
        const response = await apiClient.get<any>(`${API_CONFIG.ENDPOINTS.PRODUCTS}${queryString}`);
        // Handle paginated response or array
        if (response.products) return response.products;
        if (Array.isArray(response)) return response;
        return response.data || [];
    },

    getById: async (id: number) => {
        return apiClient.get<Product>(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`);
    },

    create: async (data: any) => {
        return apiClient.post(API_CONFIG.ENDPOINTS.PRODUCTS, data);
    },

    update: async (id: number, data: any) => {
        return apiClient.put(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`, data);
    },

    delete: async (id: number) => {
        return apiClient.delete(`${API_CONFIG.ENDPOINTS.PRODUCTS}/${id}`);
    }
};
