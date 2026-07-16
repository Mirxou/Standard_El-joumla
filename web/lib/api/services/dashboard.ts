import { apiClient } from "../client";
import { API_CONFIG } from "@/lib/config/api";

export const dashboardService = {
    getStats: async () => {
        try {
            return await apiClient.get(API_CONFIG.ENDPOINTS.DASHBOARD.STATS);
        } catch (e) {
            console.error("Dashboard stats failed", e);
            return {
                total_revenue: 0,
                total_sales: 0,
                total_profit: 0,
                products_count: 0,
                low_stock_count: 0,
                profit_margin: 0,
                today_sales: 0,
                pending_orders: 0,
                top_products: []
            };
        }
    },
    
    getSalesChartData: async (days: number = 7) => {
        try {
            return await apiClient.get(`/api/v1/reports/charts/sales?days=${days}`);
        } catch (e) {
            console.error("Sales chart data failed", e);
            return [];
        }
    }
};
