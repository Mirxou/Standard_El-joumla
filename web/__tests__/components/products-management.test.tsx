/**
 * Unit Tests for Products Management Component
 * اختبارات وحدة لمكون إدارة المنتجات
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ProductsManagement from '@/components/products-management'
import { apiClient } from '@/lib/api/client'

jest.mock('@/lib/api/client')
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

describe('ProductsManagement', () => {
  const mockProducts = [
    {
      id: 1,
      name: 'منتج 1',
      sku: 'SKU001',
      price: 100,
      stock: 50,
      category: { name: 'فئة 1' },
    },
    {
      id: 2,
      name: 'منتج 2',
      sku: 'SKU002',
      price: 200,
      stock: 5,
      category: { name: 'فئة 2' },
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      products: mockProducts,
    })
  })

  it('should render products list', async () => {
    render(<ProductsManagement />)

    await waitFor(() => {
      expect(screen.getByText('منتج 1')).toBeInTheDocument()
      expect(screen.getByText('منتج 2')).toBeInTheDocument()
    })
  })

  it('should filter products by search term', async () => {
    render(<ProductsManagement />)

    await waitFor(() => {
      expect(screen.getByText('منتج 1')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText(/بحث باسم المنتج/)
    fireEvent.change(searchInput, { target: { value: 'منتج 1' } })

    await waitFor(() => {
      expect(screen.getByText('منتج 1')).toBeInTheDocument()
      expect(screen.queryByText('منتج 2')).not.toBeInTheDocument()
    })
  })

  it('should handle bulk selection', async () => {
    render(<ProductsManagement />)

    await waitFor(() => {
      expect(screen.getByText('منتج 1')).toBeInTheDocument()
    })

    const checkboxes = screen.getAllByRole('checkbox')
    fireEvent.click(checkboxes[1]) // Select first product

    await waitFor(() => {
      expect(screen.getByText(/حذف المحدد/)).toBeInTheDocument()
    })
  })

  it('should sort products', async () => {
    render(<ProductsManagement />)

    await waitFor(() => {
      expect(screen.getByText('منتج 1')).toBeInTheDocument()
    })

    const sortSelect = screen.getByText(/ترتيب/)
    fireEvent.click(sortSelect)

    // Test sorting functionality
    // This would require more specific implementation
  })
})

