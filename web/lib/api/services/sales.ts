import { apiClient } from "../client";
import { API_CONFIG } from "@/lib/config/api";

export interface SaleItemDto {
    product_id: number;
    quantity: number;
    unit_price: number;
    discount_amount?: number;
    tax_amount?: number;
}

export interface CreateSaleDto {
    customer_id?: number | null;
    payment_method: string;
    items: SaleItemDto[];
    discount_amount?: number;
    tax_amount?: number;
    paid_amount?: number;
    notes?: string;
}

export const salesService = {
    create: async (data: CreateSaleDto) => {
        return apiClient.post(API_CONFIG.ENDPOINTS.SALES, data);
    },

    getAll: async (page = 1, limit = 50) => {
        return apiClient.get(`${API_CONFIG.ENDPOINTS.SALES}?page=${page}&page_size=${limit}`);
    },

    getById: async (id: number) => {
        return apiClient.get(`${API_CONFIG.ENDPOINTS.SALES}/${id}`);
    }
};
