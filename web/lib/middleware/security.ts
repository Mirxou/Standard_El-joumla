/**
 * Security Middleware
 * وسيط الأمان
 */

import { sanitizeInput, sanitizeUrl } from '@/lib/utils/security'

/**
 * Apply security headers
 * تطبيق رؤوس الأمان
 */
export function getSecurityHeaders(): HeadersInit {
  return {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Content-Security-Policy': [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000",
    ].join('; '),
  }
}

/**
 * Sanitize request body
 * تنظيف جسم الطلب
 */
export function sanitizeRequestBody(body: any): any {
  if (typeof body === 'string') {
    return sanitizeInput(body)
  }
  
  if (Array.isArray(body)) {
    return body.map(sanitizeRequestBody)
  }
  
  if (body && typeof body === 'object') {
    const sanitized: any = {}
    for (const [key, value] of Object.entries(body)) {
      if (typeof value === 'string') {
        sanitized[key] = sanitizeInput(value)
      } else if (typeof value === 'object') {
        sanitized[key] = sanitizeRequestBody(value)
      } else {
        sanitized[key] = value
      }
    }
    return sanitized
  }
  
  return body
}

