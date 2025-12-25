'use server'

// Server Actions for Customer Management
// إجراءات الخادم لإدارة العملاء

import { sql } from '@/lib/db/client'
import { Customer } from '@/lib/db/schema'
import { revalidatePath } from 'next/cache'

export async function getCustomers(): Promise<Customer[]> {
  try {
    const result = await sql`SELECT * FROM customers ORDER BY created_at DESC`
    return result as Customer[]
  } catch (error) {
    console.error('[v0] Error fetching customers:', error)
    throw new Error('فشل في جلب العملاء')
  }
}

export async function createCustomer(data: Partial<Customer>): Promise<Customer> {
  try {
    const result = await sql`
      INSERT INTO customers (
        name, customer_type, email, phone, mobile, address, city, country,
        tax_id, credit_limit, discount_percentage, notes, is_active
      ) VALUES (
        ${data.name}, ${data.customer_type || 'retail'}, ${data.email}, ${data.phone},
        ${data.mobile}, ${data.address}, ${data.city}, ${data.country || 'المغرب'},
        ${data.tax_id}, ${data.credit_limit || 0}, ${data.discount_percentage || 0},
        ${data.notes}, ${data.is_active ?? true}
      )
      RETURNING *
    `

    revalidatePath('/dashboard/customers')
    return result[0] as Customer
  } catch (error) {
    console.error('[v0] Error creating customer:', error)
    throw new Error('فشل في إضافة العميل')
  }
}
