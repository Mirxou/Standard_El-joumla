import { apiClient } from "@/lib/api/client"
import { API_CONFIG } from "@/lib/config/api"

export interface Warehouse {
    id: number
    code: string
    name: string
    name_en?: string
    warehouse_type: string
    capacity: number
    current_utilization: number
    address?: string
    city?: string
    phone?: string
    manager_name?: string
    is_active: boolean
    status: string
}

export interface WarehouseListResponse {
    warehouses: Warehouse[]
}

export const warehousesService = {
    // Get all warehouses
    getAll: async (includeInactive = false) => {
        const response = await apiClient.get<WarehouseListResponse>(
            `${API_CONFIG.ENDPOINTS.WAREHOUSE}s?include_inactive=${includeInactive}`
        )
        return response.warehouses
    },

    // Create a new warehouse
    create: async (data: any) => {
        return apiClient.post(API_CONFIG.ENDPOINTS.WAREHOUSE + 's', data)
    },

    // Delete a warehouse
    delete: async (id: number) => {
        return apiClient.delete(`${API_CONFIG.ENDPOINTS.WAREHOUSE}s/${id}`)
    },

    // Get inventory for a specific warehouse
    getInventory: async (id: number) => {
        return apiClient.get(`${API_CONFIG.ENDPOINTS.WAREHOUSE}s/${id}/inventory`)
    }
}
