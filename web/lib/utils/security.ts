/**
 * Security Utilities
 * أدوات الأمان
 */

/**
 * Sanitize user input to prevent XSS
 * تنظيف إدخال المستخدم لمنع XSS
 */
export function sanitizeInput(input: string): string {
  if (typeof input !== 'string') return ''
  
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  }
  
  const reg = /[&<>"'/]/gi
  return input.replace(reg, (match) => map[match])
}

/**
 * Validate email format
 * التحقق من صيغة البريد الإلكتروني
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Generate CSRF token
 * توليد رمز CSRF
 */
export function generateCSRFToken(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Validate CSRF token
 * التحقق من رمز CSRF
 */
export function validateCSRFToken(token: string, storedToken: string): boolean {
  return token === storedToken && token.length === 64
}

/**
 * Escape HTML entities
 * إزالة كيانات HTML
 */
export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Sanitize URL to prevent XSS
 * تنظيف URL لمنع XSS
 */
export function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url)
    // Only allow http and https protocols
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return ''
    }
    return parsed.toString()
  } catch {
    return ''
  }
}

