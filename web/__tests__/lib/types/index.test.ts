import {
  User,
  Company,
  Product,
  Invoice,
  Sale,
  LoginResponse,
} from '@/lib/types'

describe('TypeScript Type Definitions', () => {
  describe('User Type', () => {
    it('should create valid User object', () => {
      const user: User = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        name: 'Test User',
        full_name: 'Test Full User',
        role: 'admin',
        avatar: null,
        is_active: true,
        loggedInAt: new Date().toISOString(),
      }

      expect(user.email).toBe('test@example.com')
      expect(user.role).toBe('admin')
    })

    it('should validate user roles', () => {
      const roles = ['admin', 'manager', 'user'] as const
      roles.forEach(role => {
        const user: User = {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          name: 'Test',
          full_name: 'Test User',
          role,
          avatar: null,
          is_active: true,
          loggedInAt: new Date().toISOString(),
        }
        expect(user.role).toBe(role)
      })
    })
  })

  describe('Company Type', () => {
    it('should create valid Company object', () => {
      const company: Company = {
        id: 1,
        name: 'Test Company',
        phone: '+966501234567',
        email: 'company@example.com',
        address: '123 Main St',
        is_active: true,
      }

      expect(company.name).toBe('Test Company')
      expect(company.id).toBe(1)
    })
  })

  describe('Product Type', () => {
    it('should create valid Product object', () => {
      const product: Product = {
        id: 1,
        name: 'Test Product',
        sku: 'SKU123',
        category_id: 1,
        price: 100,
        selling_price: 150,
        stock: 50,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(product.selling_price).toBeGreaterThan(0)
      expect(product.stock).toBeLessThanOrEqual(1000)
    })
  })

  describe('Invoice Type', () => {
    it('should create valid Invoice object', () => {
      const invoice: Invoice = {
        id: 'INV-1',
        invoiceNumber: 'INV-2025-001',
        customerName: 'Test Customer',
        customerPhone: '+966501234567',
        date: new Date().toISOString().split('T')[0],
        time: new Date().toISOString().split('T')[1],
        items: [],
        subtotal: 5000,
        tax: 750,
        discount: 0,
        total: 5750,
        status: 'paid',
        paymentMethod: 'cash',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      expect(invoice.status).toBe('paid')
      expect(invoice.total).toBeGreaterThan(0)
    })

    it('should validate invoice statuses', () => {
      const statuses = ['paid', 'pending', 'cancelled'] as const
      statuses.forEach(status => {
        const invoice: Invoice = {
          id: 'INV-1',
          invoiceNumber: 'INV001',
          customerName: 'Test',
          customerPhone: '0501234567',
          date: new Date().toISOString().split('T')[0],
          time: new Date().toISOString().split('T')[1],
          items: [],
          subtotal: 1000,
          tax: 150,
          discount: 0,
          total: 1150,
          status,
          paymentMethod: 'cash',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        expect(invoice.status).toBe(status)
      })
    })
  })

  describe('Sale Type', () => {
    it('should create valid Sale object', () => {
      const sale: Sale = {
        id: 1,
        invoice_number: 'INV-001',
        customer_name: 'John Doe',
        customer_phone: '+966501234567',
        sale_date: new Date().toISOString(),
        items: [
          {
            id: '1',
            productName: 'Test Product',
            quantity: 10,
            price: 150,
            total: 1500,
          },
        ],
        subtotal: 1500,
        tax_amount: 225,
        discount_amount: 0,
        total_amount: 1725,
        status: 'paid',
        payment_method: 'cash',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(sale.subtotal).toBeGreaterThan(0)
    })
  })

  describe('LoginResponse Type', () => {
    it('should create valid LoginResponse object', () => {
      const response: LoginResponse = {
        access_token: 'token123',
        refresh_token: 'refresh123',
        expires_in: 3600,
        user: {
          id: 1,
          email: 'test@example.com',
          username: 'testuser',
          name: 'Test User',
          full_name: 'Test User',
          role: 'admin',
          avatar: null,
          is_active: true,
          loggedInAt: new Date().toISOString(),
        },
      }

      expect(response.access_token).toBeDefined()
      expect(response.user.role).toBe('admin')
    })
  })

  describe('Type Safety', () => {
    it('should enforce required fields', () => {
      const user: User = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        name: 'Test',
        full_name: 'Test User',
        role: 'admin',
        avatar: null,
        is_active: true,
        loggedInAt: new Date().toISOString(),
      }

      expect(user.id).toBeDefined()
      expect(user.email).toBeDefined()
    })

    it('should support optional fields', () => {
      const product: Product = {
        id: 1,
        name: 'Test',
        sku: 'SKU001',
        category_id: 1,
        price: 100,
        selling_price: 100,
        stock: 50,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(product.id).toBe(1)
    })
  })
})
