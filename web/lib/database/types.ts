// Database type definitions
export interface User {
  id: string
  email: string
  full_name: string
  phone?: string
  role_id?: string
  is_active: boolean
  last_login?: string
  created_at: string
  updated_at: string
}

export interface Role {
  id: string
  name: string
  name_ar: string
  description?: string
  permissions: Record<string, boolean>
  created_at: string
  updated_at: string
}

export interface Product {
  id: number
  sku: string
  barcode?: string
  name: string
  name_ar?: string
  description?: string
  category_id?: number
  brand_id?: string
  cost_price: number
  selling_price: number
  wholesale_price?: number
  current_stock: number
  min_stock_level: number
  max_stock_level?: number
  reorder_point: number
  unit: string
  weight?: number
  dimensions?: Record<string, any>
  is_active: boolean
  is_featured: boolean
  image_url?: string
  images?: string[]
  tags?: string[]
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Category {
  id: string
  name: string
  name_ar: string
  description?: string
  parent_id?: string
  image_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Customer {
  id: string
  customer_code: string
  name: string
  email?: string
  phone?: string
  mobile?: string
  customer_type: 'retail' | 'wholesale' | 'vip'
  address?: string
  city?: string
  postal_code?: string
  country: string
  tax_number?: string
  commercial_registration?: string
  credit_limit: number
  current_balance: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface Supplier {
  id: string
  supplier_code: string
  name: string
  name_ar?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  country: string
  tax_number?: string
  commercial_registration?: string
  payment_terms?: string
  credit_limit: number
  current_balance: number
  contact_person?: string
  contact_phone?: string
  is_active: boolean
  rating?: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface SalesInvoice {
  id: string
  invoice_number: string
  customer_id?: string
  invoice_date: string
  due_date?: string
  subtotal: number
  discount_amount: number
  tax_amount: number
  total_amount: number
  paid_amount: number
  status: 'draft' | 'pending' | 'paid' | 'partial' | 'cancelled'
  payment_status: 'unpaid' | 'partial' | 'paid'
  notes?: string
  terms?: string
  created_by?: string
  created_at: string
  updated_at: string
}

export interface SalesInvoiceItem {
  id: string
  invoice_id: string
  product_id: string
  description?: string
  quantity: number
  unit_price: number
  discount_percent: number
  tax_percent: number
  line_total: number
  created_at: string
}

export interface Payment {
  id: string
  payment_number: string
  reference_type: 'sales_invoice' | 'purchase_order'
  reference_id: string
  party_type: 'customer' | 'supplier'
  party_id: string
  payment_date: string
  amount: number
  payment_method: 'cash' | 'card' | 'bank_transfer' | 'cheque' | 'other'
  bank_name?: string
  transaction_reference?: string
  status: 'pending' | 'completed' | 'cancelled'
  notes?: string
  created_by?: string
  created_at: string
}

export interface StockMovement {
  id: string
  product_id: string
  warehouse_id?: string
  movement_type: 'in' | 'out' | 'transfer' | 'adjustment'
  quantity: number
  reference_type?: string
  reference_id?: string
  notes?: string
  created_by?: string
  created_at: string
}
