import {
  User,
  Company,
  Product,
  Invoice,
  Sale,
  LoginRequest,
  LoginResponse,
} from '@/lib/types'

describe('Type Definitions - Corrected', () => {
  describe('User Type', () => {
    it('should create valid User object', () => {
      const user: User = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        username: 'testuser',
        full_name: 'Test User',
        role: 'admin',
        avatar: null,
        is_active: true,
        loggedInAt: new Date().toISOString(),
      }

      expect(user.email).toBe('test@example.com')
      expect(user.role).toBe('admin')
      expect(user.is_active).toBe(true)
    })

    it('should support different roles', () => {
      const roles = ['admin', 'manager', 'user', 'viewer']
      
      roles.forEach(role => {
        const user: User = {
          id: 1,
          email: `${role}@test.com`,
          name: role,
          username: role,
          full_name: role,
          role: role,
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
        email: 'company@example.com',
        phone: '+966501234567',
        address: '123 Main St',
        is_active: true,
      }

      expect(company.name).toBe('Test Company')
      expect(company.email).toContain('@')
      expect(company.is_active).toBe(true)
    })
  })

  describe('Product Type', () => {
    it('should create valid Product object', () => {
      const product: Product = {
        id: 1,
        name: 'Test Product',
        sku: 'SKU123',
        category_id: 1,
        price: 150,
        selling_price: 200,
        stock: 50,
        status: 'active',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(product.name).toBeDefined()
      expect(product.price).toBeGreaterThan(0)
    })

    it('should support optional properties', () => {
      const product: Product = {
        id: 1,
        name: 'Simple Product',
        sku: 'SKU-OPT',
        category_id: 1,
        price: 100,
        selling_price: 150,
        stock: 10,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(product.id).toBe(1)
      expect(product.name).toBeDefined()
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
        subtotal: 1000,
        tax: 150,
        discount: 0,
        total: 1150,
        status: 'pending',
        paymentMethod: 'cash',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      expect(invoice.invoiceNumber).toBeDefined()
      expect(['pending', 'مدفوعة', 'معلقة', 'ملغية', 'paid', 'cancelled']).toContain(invoice.status)
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
        items: [],
        subtotal: 1500,
        tax_amount: 225,
        discount_amount: 0,
        total_amount: 1725,
        status: 'pending',
        payment_method: 'cash',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      expect(sale.total_amount).toBeGreaterThan(0)
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
      expect(response.expires_in).toBeGreaterThan(0)
    })
  })

  describe('LoginRequest Type', () => {
    it('should create valid LoginRequest object', () => {
      const request: LoginRequest = {
        username: 'testuser',
        password: 'password123',
      }

      expect(request.username).toBeDefined()
      expect(request.password).toBeDefined()
    })
  })

  describe('Type Safety Checks', () => {
    it('should enforce required properties', () => {
      const user: User = {
        id: 1,
        email: 'test@test.com',
        username: 'test',
        full_name: 'Test',
        name: 'Test',
        role: 'user',
        avatar: null,
        is_active: true,
        loggedInAt: new Date().toISOString(),
      }

      expect(user).toHaveProperty('id')
      expect(user).toHaveProperty('email')
      expect(user).toHaveProperty('role')
    })
  })
})
