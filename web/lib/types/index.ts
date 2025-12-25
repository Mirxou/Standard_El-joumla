/**
 * تعريفات الأنواع الشاملة للتطبيق
 * بدل استخدام `any`
 */

// ============================================
// Authentication Types
// ============================================

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  name: string;
  role: string;
  avatar: string | null;
  is_active: boolean;
  loggedInAt: string;
}

export interface Company {
  id: number;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  logo?: string;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
  full_name?: string;
  role?: string;
}

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  companies: Company[];
  currentCompany: Company | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
  selectCompany: (company: Company) => void;
}

// ============================================
// Product & Inventory Types
// ============================================

export interface Category {
  id: number;
  name: string;
  name_ar: string;
  description?: string;
  parent_id?: number | null;
  icon?: string | null;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  name: string;
  name_ar?: string;
  sku: string;
  category_id: number;
  category?: Category;
  price: number;
  selling_price: number;
  cost?: number;
  stock: number;
  current_stock?: number;
  min_stock_level?: number;
  reorder_point?: number;
  status: 'active' | 'draft' | 'archived';
  is_active?: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface StockMovement {
  id: number;
  product_id: number;
  movement_type: 'in' | 'out' | 'adjustment';
  quantity: number;
  reference_type?: string;
  reference_id?: number;
  notes?: string;
  created_at: string;
  created_by?: string;
}

// ============================================
// Invoice & Sales Types
// ============================================

export interface InvoiceItem {
  id: string;
  product_id?: number;
  productName: string;
  quantity: number;
  price: number;
  total: number;
  unit_price?: number;
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  customerName: string;
  customerPhone: string;
  date: string;
  time: string;
  items: InvoiceItem[];
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  status: 'مدفوعة' | 'معلقة' | 'ملغية' | 'paid' | 'pending' | 'cancelled';
  paymentMethod: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Customer {
  id: number;
  name: string;
  name_en?: string;
  phone?: string;
  phone2?: string;
  email?: string;
  address?: string;
  city?: string;
  country: string;
  tax_number?: string;
  credit_limit: number;
  current_balance: number;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_purchase_date?: string;
  total_purchases: number;
  purchases_count: number;
  available_credit?: number;
  is_credit_exceeded?: boolean;
  full_address?: string;
}

export interface Sale {
  id: number;
  invoice_number: string;
  customer_name?: string;
  customer_phone?: string;
  sale_date: string;
  items: InvoiceItem[];
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  status: 'paid' | 'pending' | 'cancelled' | 'confirmed';
  payment_method: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// ============================================
// Warehouse Types
// ============================================

export interface Warehouse {
  id: number;
  name: string;
  name_ar?: string;
  location: string;
  address?: string;
  manager?: string;
  contact_phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================
// Supplier Types
// ============================================

export interface Supplier {
  id: number;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  city?: string;
  is_active: boolean;
  payment_terms?: string;
  created_at: string;
  updated_at: string;
}

// ============================================
// API Response Types
// ============================================

export interface APIResponse<T> {
  data: T;
  error?: string | null;
  success?: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface APIError {
  detail?: string;
  message?: string;
  status: number;
  timestamp?: string;
}

// ============================================
// Dashboard Types
// ============================================

export interface DashboardStats {
  totalRevenue: number;
  totalProducts: number;
  lowStockAlerts: number;
  profitMargin: number;
  todaySales: number;
  pendingOrders: number;
  expiringItems: number;
  activeSuppliers: number;
}

export interface CategoryStat {
  id: number;
  name_ar: string;
  productCount: number;
  totalStock: number;
  totalValue: number;
  percentage: number;
}

// ============================================
// Form Types
// ============================================

export interface FormErrors {
  [key: string]: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: FormErrors;
}
