// =====================================================
// TypeScript Types for Database Schema
// تعريفات النماذج بلغة TypeScript
// =====================================================

export interface Role {
  id: number
  name: string
  display_name: string
  permissions: Record<string, boolean>
  created_at: Date
  updated_at: Date
}

export interface User {
  id: number
  username: string
  email: string
  password_hash: string
  full_name: string
  role_id: number | null
  phone: string | null
  is_active: boolean
  last_login: Date | null
  created_at: Date
  updated_at: Date
}

export interface Category {
  id: number
  name: string
  name_ar: string
  description: string | null
  parent_id: number | null
  icon: string | null
  display_order: number
  is_active: boolean
  created_at: Date
  updated_at: Date
}

export interface Supplier {
  id: number
  name: string
  contact_person: string | null
  email: string | null
  phone: string | null
  mobile: string | null
  address: string | null
  city: string | null
  country: string
  tax_id: string | null
  payment_terms: string | null
  credit_limit: number
  current_balance: number
  rating: number | null
  notes: string | null
  is_active: boolean
  created_at: Date
  updated_at: Date
}

export interface Customer {
  id: number
  name: string
  customer_type: 'retail' | 'wholesale' | 'vip'
  email: string | null
  phone: string | null
  mobile: string | null
  address: string | null
  city: string | null
  country: string
  tax_id: string | null
  credit_limit: number
  current_balance: number
  loyalty_points: number
  discount_percentage: number
  notes: string | null
  is_active: boolean
  created_at: Date
  updated_at: Date
}

export interface Product {
  id: number
  sku: string
  barcode: string | null
  name: string
  name_ar: string
  description: string | null
  category_id: number | null
  supplier_id: number | null
  unit_cost: number
  selling_price: number
  wholesale_price: number | null
  vip_price: number | null
  tax_rate: number
  quantity_in_stock: number
  min_stock_level: number
  max_stock_level: number
  reorder_level: number
  reorder_quantity: number
  unit_of_measure: string
  weight: number | null
  weight_unit: string
  dimensions: string | null
  batch_tracking: boolean
  expiry_tracking: boolean
  serial_tracking: boolean
  manufacturer: string | null
  brand: string | null
  image_url: string | null
  notes: string | null
  is_active: boolean
  created_at: Date
  updated_at: Date
}

export interface ProductBatch {
  id: number
  product_id: number
  batch_number: string
  quantity: number
  manufacture_date: Date | null
  expiry_date: Date | null
  supplier_id: number | null
  unit_cost: number | null
  location: string | null
  notes: string | null
  created_at: Date
}

export interface PurchaseOrder {
  id: number
  order_number: string
  supplier_id: number | null
  order_date: Date
  expected_delivery_date: Date | null
  actual_delivery_date: Date | null
  status: 'pending' | 'confirmed' | 'delivered' | 'cancelled'
  subtotal: number
  tax_amount: number
  discount_amount: number
  shipping_cost: number
  total_amount: number
  payment_status: 'unpaid' | 'partial' | 'paid'
  payment_method: string | null
  notes: string | null
  created_by: number | null
  created_at: Date
  updated_at: Date
}

export interface PurchaseOrderItem {
  id: number
  purchase_order_id: number
  product_id: number
  quantity: number
  unit_cost: number
  tax_rate: number
  discount_percentage: number
  line_total: number
  batch_number: string | null
  expiry_date: Date | null
  notes: string | null
}

export interface SalesInvoice {
  id: number
  invoice_number: string
  customer_id: number | null
  invoice_date: Date
  due_date: Date | null
  status: 'draft' | 'confirmed' | 'paid' | 'cancelled' | 'refunded'
  subtotal: number
  tax_amount: number
  discount_amount: number
  total_amount: number
  payment_status: 'unpaid' | 'partial' | 'paid'
  payment_method: string | null
  notes: string | null
  created_by: number | null
  created_at: Date
  updated_at: Date
}

export interface SalesInvoiceItem {
  id: number
  sales_invoice_id: number
  product_id: number
  quantity: number
  unit_price: number
  tax_rate: number
  discount_percentage: number
  line_total: number
  batch_number: string | null
  notes: string | null
}

export interface Payment {
  id: number
  payment_type: 'purchase' | 'sales' | 'expense'
  reference_id: number | null
  payment_date: Date
  amount: number
  payment_method: 'cash' | 'card' | 'bank_transfer' | 'check'
  reference_number: string | null
  notes: string | null
  created_by: number | null
  created_at: Date
}

export interface InventoryMovement {
  id: number
  product_id: number
  movement_type: 'in' | 'out' | 'adjustment' | 'transfer' | 'return'
  quantity: number
  reference_type: string | null
  reference_id: number | null
  batch_number: string | null
  from_location: string | null
  to_location: string | null
  unit_cost: number | null
  notes: string | null
  created_by: number | null
  created_at: Date
}

export interface Alert {
  id: number
  alert_type: 'low_stock' | 'expiry_warning' | 'reorder_point'
  severity: 'info' | 'warning' | 'critical'
  product_id: number | null
  title: string
  message: string
  is_read: boolean
  is_resolved: boolean
  created_at: Date
  resolved_at: Date | null
}

export interface ActivityLog {
  id: number
  user_id: number | null
  action: string
  entity_type: string | null
  entity_id: number | null
  changes: Record<string, any> | null
  ip_address: string | null
  user_agent: string | null
  created_at: Date
}
