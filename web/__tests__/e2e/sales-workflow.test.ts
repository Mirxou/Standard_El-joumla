/**
 * E2E Tests for Sales Workflow
 * اختبارات نهاية إلى نهاية لسير عمل المبيعات
 */

describe('Sales Workflow E2E', () => {
  beforeEach(() => {
    // Set up test environment
    cy.visit('/')
    // Login if needed
  })

  it('should complete full sales workflow', () => {
    // Navigate to sales
    cy.contains('المبيعات').click()

    // Create new invoice
    cy.contains('فاتورة جديدة').click()

    // Add products
    cy.get('[data-testid="product-select"]').click()
    cy.contains('منتج 1').click()

    // Set quantity
    cy.get('[data-testid="quantity-input"]').clear().type('2')

    // Add customer
    cy.get('[data-testid="customer-input"]').type('عميل تجريبي')

    // Save invoice
    cy.contains('حفظ').click()

    // Verify invoice created
    cy.contains('تم إنشاء الفاتورة بنجاح').should('be.visible')

    // Verify invoice in list
    cy.contains('عميل تجريبي').should('be.visible')
  })

  it('should print invoice', () => {
    // Navigate to sales
    cy.contains('المبيعات').click()

    // Find invoice
    cy.contains('عميل تجريبي').parent().within(() => {
      cy.contains('طباعة').click()
    })

    // Verify print dialog or PDF generation
    // This would require checking window.print or PDF download
  })

  it('should filter invoices', () => {
    cy.contains('المبيعات').click()

    // Use search
    cy.get('[placeholder*="بحث"]').type('عميل')

    // Verify filtered results
    cy.contains('عميل تجريبي').should('be.visible')
  })
})

