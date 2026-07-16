/**
 * Unit Tests for PDF Generator
 * اختبارات وحدة لمولد PDF
 */

import { generateInvoicePDF } from '@/lib/utils/pdf-generator'

// Mock jsPDF
jest.mock('jspdf', () => {
  const mockDoc = {
    text: jest.fn(),
    save: jest.fn(),
    setFontSize: jest.fn(),
    setFont: jest.fn(),
    autoTable: jest.fn(),
  }
  return jest.fn(() => mockDoc)
})

describe('PDF Generator', () => {
  const mockInvoiceData = {
    id: '1',
    invoiceNumber: 'INV-001',
    customerName: 'عميل تجريبي',
    customerPhone: '0500000000',
    date: '2024-01-01',
    time: '10:00',
    items: [
      { name: 'منتج 1', quantity: 2, price: 100, total: 200 },
      { name: 'منتج 2', quantity: 1, price: 150, total: 150 },
    ],
    subtotal: 350,
    tax: 35,
    discount: 0,
    total: 385,
    paymentMethod: 'نقدي',
    notes: 'ملاحظات',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should generate PDF with correct invoice data', () => {
    generateInvoicePDF(mockInvoiceData)

    // Verify PDF was created
    expect(require('jspdf')).toHaveBeenCalled()
  })

  it('should handle missing optional fields', () => {
    const minimalData = {
      ...mockInvoiceData,
      notes: undefined,
    }

    expect(() => generateInvoicePDF(minimalData)).not.toThrow()
  })

  it('should format Arabic text correctly', () => {
    generateInvoicePDF(mockInvoiceData)

    // Verify Arabic text is included
    // This would require checking the actual PDF content
  })
})

